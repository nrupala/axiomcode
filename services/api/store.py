"""AxiomCode durable store (production, W2 + W3) — sqlite3, stdlib only.

Replaces the prototype's revoked.txt + meter.jsonl flat files with one
durable database:

  certificates  (serial PK, cert_json, status, issued_at)
  revocations   (serial PK, reason, ts)
  meter_events  (id, ts, key_id, code_sha256, verified, credits, usd,
                 trial, entry_json) — the billing record; trial rows
                 are free verification cases (credits = 0, trial = 1)
  audit_log     (seq, ts, event_type, payload_json, prev_hash, hash)
  api_keys      (key_hash PK, label, created_at, revoked) — only the
                 SHA-256 hash of a key is ever stored, never plaintext
  credit_grants (id, key_hash, credits, source, external_id UNIQUE, ts)
                 — purchased / comped credits; external_id (e.g. a
                 Stripe checkout session id) makes grants idempotent

The audit log is hash-chained: every row's hash is
SHA-256(prev_hash | event_type | ts | canonical payload_json), where
the payload is stored as its canonical JSON string (json.dumps,
sort_keys=True), so any later edit to a stored payload, event type or
timestamp — even one byte — breaks the chain at that seq, and
verify_chain() reports the first broken seq. (Chain format v2, W3:
the W2 format bound only the payload. The store is pre-production,
so no migration of W2 chains is owed.)

A key's balance is sum(credit_grants) - sum(meter_events.credits);
trial cases are counted from meter_events rows with trial = 1.
Everywhere a caller identity is recorded (meter_events.key_id,
certificate key_id) it is the key's SHA-256 hash — stable, joinable,
and not a secret.

Issuance and revocation append their audit events by construction
(record_cert / revoke do it themselves, in the same transaction as
the state change); verification events are appended by the API layer
via append_audit().
"""

import hashlib
import json
import os
import secrets
import sqlite3
import threading
import time
from pathlib import Path

_HERE = Path(__file__).parent
DEFAULT_DB = os.environ.get("AXIOMCODE_DB", str(_HERE / "axiomcode.db"))
GENESIS_HASH = "0" * 64

_SCHEMA = """
CREATE TABLE IF NOT EXISTS certificates (
    serial TEXT PRIMARY KEY,
    cert_json TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'issued',
    issued_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS revocations (
    serial TEXT PRIMARY KEY,
    reason TEXT NOT NULL DEFAULT '',
    ts INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS meter_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts INTEGER NOT NULL,
    key_id TEXT NOT NULL,
    code_sha256 TEXT NOT NULL,
    verified INTEGER NOT NULL,
    credits REAL NOT NULL DEFAULT 0,
    usd REAL NOT NULL DEFAULT 0,
    entry_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS audit_log (
    seq INTEGER PRIMARY KEY AUTOINCREMENT,
    ts INTEGER NOT NULL,
    event_type TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    prev_hash TEXT NOT NULL,
    hash TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS api_keys (
    key_hash TEXT PRIMARY KEY,
    label TEXT NOT NULL DEFAULT '',
    created_at INTEGER NOT NULL,
    revoked INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS credit_grants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key_hash TEXT NOT NULL,
    credits REAL NOT NULL,
    source TEXT NOT NULL DEFAULT '',
    external_id TEXT UNIQUE,
    ts INTEGER NOT NULL
);
"""

KEY_PREFIX = "axk_"


def hash_api_key(plaintext: str) -> str:
    """The only representation of an API key that is ever stored."""
    return hashlib.sha256(plaintext.encode()).hexdigest()


def _canonical(payload: dict) -> str:
    return json.dumps(payload, sort_keys=True)


def _chain_hash(prev_hash: str, event_type: str, ts: int, payload_json: str) -> str:
    """Chain format v2 (W3): binds event type and timestamp as well as
    the payload, so re-typing or re-dating a stored event also breaks
    the chain."""
    material = "|".join((prev_hash, event_type, str(ts), payload_json))
    return hashlib.sha256(material.encode()).hexdigest()


class Store:
    """One durable AxiomCode store. Safe for the threadpool-style
    concurrency of the API servers (single connection + lock, WAL)."""

    def __init__(self, db_path: str | Path | None = None):
        self.path = Path(db_path or DEFAULT_DB)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._db = sqlite3.connect(self.path, check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        self._db.execute("PRAGMA journal_mode=WAL")
        self._db.executescript(_SCHEMA)
        # Migration for stores created by W2: meter_events.trial marks
        # free trial cases (zero-credit) — added in W3.
        cols = {r["name"] for r in self._db.execute("PRAGMA table_info(meter_events)")}
        if "trial" not in cols:
            self._db.execute("ALTER TABLE meter_events ADD COLUMN trial INTEGER NOT NULL DEFAULT 0")
        self._db.commit()

    def close(self) -> None:
        with self._lock:
            self._db.close()

    # ─── audit log ───────────────────────────────────────────────────
    def _insert_audit_locked(self, event_type: str, payload: dict, ts: int) -> dict:
        """Insert one hash-chained audit row. Caller must hold the lock
        and owns the transaction (commit / rollback)."""
        payload_json = _canonical(payload)
        row = self._db.execute("SELECT hash FROM audit_log ORDER BY seq DESC LIMIT 1").fetchone()
        prev_hash = row["hash"] if row else GENESIS_HASH
        h = _chain_hash(prev_hash, event_type, ts, payload_json)
        cur = self._db.execute(
            "INSERT INTO audit_log (ts, event_type, payload_json, prev_hash, hash) VALUES (?, ?, ?, ?, ?)",
            (ts, event_type, payload_json, prev_hash, h),
        )
        return {
            "seq": cur.lastrowid,
            "ts": ts,
            "event_type": event_type,
            "payload": payload,
            "prev_hash": prev_hash,
            "hash": h,
        }

    def append_audit(self, event_type: str, payload: dict) -> dict:
        """Append one hash-chained audit event. Returns the stored row."""
        ts = int(time.time())
        with self._lock:
            out = self._insert_audit_locked(event_type, payload, ts)
            self._db.commit()
            return out

    def verify_chain(self) -> dict:
        """Recompute the whole chain. {"ok": True, "events": n} or
        {"ok": False, "broken_seq": <first seq that fails>}."""
        with self._lock:
            rows = self._db.execute(
                "SELECT seq, ts, event_type, payload_json, prev_hash, hash FROM audit_log ORDER BY seq"
            ).fetchall()
        prev = GENESIS_HASH
        for r in rows:
            if r["prev_hash"] != prev:
                return {"ok": False, "broken_seq": r["seq"]}
            expect = _chain_hash(r["prev_hash"], r["event_type"], r["ts"], r["payload_json"])
            if expect != r["hash"]:
                return {"ok": False, "broken_seq": r["seq"]}
            prev = r["hash"]
        return {"ok": True, "events": len(rows)}

    def audit_events(self, event_type: str | None = None) -> list[dict]:
        with self._lock:
            if event_type:
                rows = self._db.execute(
                    "SELECT * FROM audit_log WHERE event_type = ? ORDER BY seq", (event_type,)
                ).fetchall()
            else:
                rows = self._db.execute("SELECT * FROM audit_log ORDER BY seq").fetchall()
        return [{**dict(r), "payload": json.loads(r["payload_json"])} for r in rows]

    # ─── certificates & revocation ───────────────────────────────────
    def record_cert(self, cert: dict) -> dict:
        """Persist an issued certificate + its issuance audit event,
        in ONE transaction (W3 hardening: the two used to commit
        separately, so a crash could leave a cert with no audit row)."""
        with self._lock:
            try:
                self._db.execute(
                    "INSERT OR REPLACE INTO certificates (serial, cert_json, status, issued_at) VALUES (?, ?, ?, ?)",
                    (cert["serial"], _canonical(cert), "issued", int(cert.get("valid_from", time.time()))),
                )
                self._insert_audit_locked(
                    "issuance",
                    {
                        "serial": cert["serial"],
                        "kid": cert.get("kid"),
                        "code_sha256": cert.get("code_sha256"),
                        "verified": cert.get("verified"),
                    },
                    int(time.time()),
                )
                self._db.commit()
            except Exception:
                self._db.rollback()
                raise
        return cert

    def get_cert(self, serial: str) -> dict | None:
        with self._lock:
            row = self._db.execute("SELECT cert_json FROM certificates WHERE serial = ?", (serial,)).fetchone()
        return json.loads(row["cert_json"]) if row else None

    def revoke(self, serial: str, reason: str = "") -> None:
        """Revoke a certificate + append the revocation audit event,
        in ONE transaction (same W3 hardening as record_cert)."""
        ts = int(time.time())
        with self._lock:
            try:
                self._db.execute(
                    "INSERT OR REPLACE INTO revocations (serial, reason, ts) VALUES (?, ?, ?)", (serial, reason, ts)
                )
                self._db.execute("UPDATE certificates SET status = 'revoked' WHERE serial = ?", (serial,))
                self._insert_audit_locked("revocation", {"serial": serial, "reason": reason}, ts)
                self._db.commit()
            except Exception:
                self._db.rollback()
                raise

    def is_revoked(self, serial: str) -> bool:
        with self._lock:
            row = self._db.execute("SELECT 1 FROM revocations WHERE serial = ?", (serial,)).fetchone()
        return row is not None

    def revoked_serials(self) -> set:
        with self._lock:
            rows = self._db.execute("SELECT serial FROM revocations").fetchall()
        return {r["serial"] for r in rows}

    # ─── metering ────────────────────────────────────────────────────
    def record_meter(self, entry: dict) -> dict:
        """Persist one metered call (the full billing entry is kept).
        Trial cases arrive with credits = 0 and entry["trial"] set;
        the flag is indexed so trial usage is countable per key."""
        with self._lock:
            self._db.execute(
                "INSERT INTO meter_events (ts, key_id, code_sha256,"
                " verified, credits, usd, trial, entry_json)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    int(entry.get("ts", time.time())),
                    entry.get("key_id", ""),
                    entry.get("code_sha256", ""),
                    1 if entry.get("verified") else 0,
                    float(entry.get("credits", 0)),
                    float(entry.get("usd", 0)),
                    1 if entry.get("trial") else 0,
                    _canonical(entry),
                ),
            )
            self._db.commit()
        return entry

    def trial_cases_used(self, key_id: str) -> int:
        """Free trial verification cases consumed by a key (W3)."""
        with self._lock:
            row = self._db.execute(
                "SELECT COUNT(*) AS n FROM meter_events WHERE key_id = ? AND trial = 1", (key_id,)
            ).fetchone()
        return int(row["n"])

    def usage_for(self, key_id: str) -> dict:
        """Aggregate metered spend — same shape as billing.usage_for."""
        with self._lock:
            row = self._db.execute(
                "SELECT COUNT(*) AS calls, COALESCE(SUM(credits), 0) AS c,"
                " COALESCE(SUM(usd), 0) AS u FROM meter_events"
                " WHERE key_id = ?",
                (key_id,),
            ).fetchone()
        return {
            "key_id": key_id,
            "calls": row["calls"],
            "credits_used": round(row["c"], 4),
            "usd_used": round(row["u"], 4),
        }

    def meter_events(self, key_id: str | None = None) -> list[dict]:
        with self._lock:
            if key_id:
                rows = self._db.execute(
                    "SELECT entry_json FROM meter_events WHERE key_id = ? ORDER BY id", (key_id,)
                ).fetchall()
            else:
                rows = self._db.execute("SELECT entry_json FROM meter_events ORDER BY id").fetchall()
        return [json.loads(r["entry_json"]) for r in rows]

    # ─── API keys (W3) ───────────────────────────────────────────────
    def create_api_key(self, label: str = "") -> str:
        """Create a key and return its PLAINTEXT — shown once, never
        stored. Only the SHA-256 hash lands in the store (plus an
        audit event carrying the hash and label, never the secret)."""
        plaintext = KEY_PREFIX + secrets.token_urlsafe(32)
        key_hash = hash_api_key(plaintext)
        ts = int(time.time())
        with self._lock:
            try:
                self._db.execute(
                    "INSERT INTO api_keys (key_hash, label, created_at, revoked) VALUES (?, ?, ?, 0)",
                    (key_hash, label, ts),
                )
                self._insert_audit_locked("api_key_created", {"key_hash": key_hash, "label": label}, ts)
                self._db.commit()
            except Exception:
                self._db.rollback()
                raise
        return plaintext

    def ensure_api_key(self, plaintext: str, label: str = "") -> str:
        """Provision a specific key (e.g. from AXIOMCODE_API_KEY at
        server start) if its hash is not already known. Returns the
        key_hash. An existing row is left untouched — in particular a
        revocation is never silently undone by a restart."""
        key_hash = hash_api_key(plaintext)
        ts = int(time.time())
        with self._lock:
            row = self._db.execute("SELECT 1 FROM api_keys WHERE key_hash = ?", (key_hash,)).fetchone()
            if row is None:
                try:
                    self._db.execute(
                        "INSERT INTO api_keys (key_hash, label, created_at, revoked) VALUES (?, ?, ?, 0)",
                        (key_hash, label, ts),
                    )
                    self._insert_audit_locked("api_key_created", {"key_hash": key_hash, "label": label}, ts)
                    self._db.commit()
                except Exception:
                    self._db.rollback()
                    raise
        return key_hash

    def lookup_api_key(self, plaintext: str) -> dict | None:
        """Store row for a presented key (any state), or None."""
        key_hash = hash_api_key(plaintext)
        with self._lock:
            row = self._db.execute(
                "SELECT key_hash, label, created_at, revoked FROM api_keys WHERE key_hash = ?", (key_hash,)
            ).fetchone()
        return dict(row) if row else None

    def authenticate_api_key(self, plaintext: str) -> dict | None:
        """Store row for a presented key iff it exists and is not
        revoked — the only check the servers rely on."""
        row = self.lookup_api_key(plaintext)
        if row is None or row["revoked"]:
            return None
        return row

    def revoke_api_key(self, key_hash: str) -> bool:
        """Revoke by hash (never by plaintext). True if a key changed."""
        ts = int(time.time())
        with self._lock:
            try:
                cur = self._db.execute(
                    "UPDATE api_keys SET revoked = 1 WHERE key_hash = ? AND revoked = 0", (key_hash,)
                )
                if cur.rowcount:
                    self._insert_audit_locked("api_key_revoked", {"key_hash": key_hash}, ts)
                self._db.commit()
            except Exception:
                self._db.rollback()
                raise
        return bool(cur.rowcount)

    # ─── credit grants & balance (W3) ────────────────────────────────
    def grant_credits(self, key_hash: str, credits: float, source: str = "", external_id: str | None = None) -> bool:
        """Record a credit grant (purchase, comp, or a negative entry
        for a refund reversal). Idempotent on external_id: returns
        False when a grant with that external_id already exists, so a
        replayed webhook grants nothing twice."""
        ts = int(time.time())
        with self._lock:
            try:
                self._db.execute(
                    "INSERT INTO credit_grants (key_hash, credits, source, external_id, ts) VALUES (?, ?, ?, ?, ?)",
                    (key_hash, float(credits), source, external_id, ts),
                )
                self._insert_audit_locked(
                    "credit_grant",
                    {
                        "key_hash": key_hash,
                        "credits": float(credits),
                        "source": source,
                        "external_id": external_id,
                    },
                    ts,
                )
                self._db.commit()
            except sqlite3.IntegrityError:
                self._db.rollback()
                return False
            except Exception:
                self._db.rollback()
                raise
        return True

    def find_grant(self, external_id: str) -> dict | None:
        """The grant recorded under an external id, if any."""
        with self._lock:
            row = self._db.execute(
                "SELECT key_hash, credits, source, external_id, ts FROM credit_grants WHERE external_id = ?",
                (external_id,),
            ).fetchone()
        return dict(row) if row else None

    def credits_granted(self, key_hash: str) -> float:
        """Total credits ever granted to a key (net of reversals)."""
        with self._lock:
            row = self._db.execute(
                "SELECT COALESCE(SUM(credits), 0) AS g FROM credit_grants WHERE key_hash = ?", (key_hash,)
            ).fetchone()
        return round(float(row["g"]), 4)

    def balance_for(self, key_hash: str) -> float:
        """Spendable balance: grants minus metered credit usage."""
        used = float(self.usage_for(key_hash)["credits_used"])
        return round(self.credits_granted(key_hash) - used, 4)


_DEFAULT_STORE: Store | None = None


def default_store() -> Store:
    """Process-wide store, opened at AXIOMCODE_DB."""
    global _DEFAULT_STORE
    if _DEFAULT_STORE is None:
        _DEFAULT_STORE = Store()
    return _DEFAULT_STORE


def issue_api_key(store: Store, label: str) -> str:
    """Operator helper: create a key in `store`, return the plaintext
    (to be handed to the customer once — it cannot be recovered)."""
    return store.create_api_key(label)


def _main(argv: list[str] | None = None) -> int:
    """CLI: python -m store create-key --label "Acme" [--db PATH]
    Prints the new plaintext key exactly once."""
    import argparse

    parser = argparse.ArgumentParser(prog="store", description="AxiomCode store operator tools")
    sub = parser.add_subparsers(dest="cmd", required=True)
    create = sub.add_parser("create-key", help="create an API key (plaintext printed once)")
    create.add_argument("--label", default="", help="human label for the key")
    create.add_argument("--db", default=None, help="store path (default: AXIOMCODE_DB)")
    args = parser.parse_args(argv)
    if args.cmd == "create-key":
        store = Store(args.db)
        try:
            print(issue_api_key(store, args.label))
        finally:
            store.close()
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(_main())
