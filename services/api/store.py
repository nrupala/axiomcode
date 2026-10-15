"""AxiomCode durable store (production, W2) — sqlite3, stdlib only.

Replaces the prototype's revoked.txt + meter.jsonl flat files with one
durable database:

  certificates  (serial PK, cert_json, status, issued_at)
  revocations   (serial PK, reason, ts)
  meter_events  (id, ts, key_id, code_sha256, verified, credits, usd,
                 entry_json) — the billing record
  audit_log     (seq, ts, event_type, payload_json, prev_hash, hash)

The audit log is hash-chained: every row's hash is
SHA-256(prev_hash + canonical payload_json), where the payload is
stored as its canonical JSON string (json.dumps, sort_keys=True), so
any later edit to a stored payload — even one byte — breaks the chain
at that seq, and verify_chain() reports the first broken seq.

Issuance and revocation append their audit events by construction
(record_cert / revoke do it themselves); verification events are
appended by the API layer via append_audit().
"""

import hashlib
import json
import os
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
"""


def _canonical(payload: dict) -> str:
    return json.dumps(payload, sort_keys=True)


def _chain_hash(prev_hash: str, payload_json: str) -> str:
    return hashlib.sha256((prev_hash + payload_json).encode()).hexdigest()


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
        self._db.commit()

    def close(self) -> None:
        with self._lock:
            self._db.close()

    # ─── audit log ───────────────────────────────────────────────────
    def append_audit(self, event_type: str, payload: dict) -> dict:
        """Append one hash-chained audit event. Returns the stored row."""
        payload_json = _canonical(payload)
        ts = int(time.time())
        with self._lock:
            row = self._db.execute("SELECT hash FROM audit_log ORDER BY seq DESC LIMIT 1").fetchone()
            prev_hash = row["hash"] if row else GENESIS_HASH
            h = _chain_hash(prev_hash, payload_json)
            cur = self._db.execute(
                "INSERT INTO audit_log (ts, event_type, payload_json, prev_hash, hash) VALUES (?, ?, ?, ?, ?)",
                (ts, event_type, payload_json, prev_hash, h),
            )
            self._db.commit()
            return {
                "seq": cur.lastrowid,
                "ts": ts,
                "event_type": event_type,
                "payload": payload,
                "prev_hash": prev_hash,
                "hash": h,
            }

    def verify_chain(self) -> dict:
        """Recompute the whole chain. {"ok": True, "events": n} or
        {"ok": False, "broken_seq": <first seq that fails>}."""
        with self._lock:
            rows = self._db.execute("SELECT seq, payload_json, prev_hash, hash FROM audit_log ORDER BY seq").fetchall()
        prev = GENESIS_HASH
        for r in rows:
            if r["prev_hash"] != prev:
                return {"ok": False, "broken_seq": r["seq"]}
            if _chain_hash(r["prev_hash"], r["payload_json"]) != r["hash"]:
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
        """Persist an issued certificate + its issuance audit event."""
        with self._lock:
            self._db.execute(
                "INSERT OR REPLACE INTO certificates (serial, cert_json, status, issued_at) VALUES (?, ?, ?, ?)",
                (cert["serial"], _canonical(cert), "issued", int(cert.get("valid_from", time.time()))),
            )
            self._db.commit()
        self.append_audit(
            "issuance",
            {
                "serial": cert["serial"],
                "kid": cert.get("kid"),
                "code_sha256": cert.get("code_sha256"),
                "verified": cert.get("verified"),
            },
        )
        return cert

    def get_cert(self, serial: str) -> dict | None:
        with self._lock:
            row = self._db.execute("SELECT cert_json FROM certificates WHERE serial = ?", (serial,)).fetchone()
        return json.loads(row["cert_json"]) if row else None

    def revoke(self, serial: str, reason: str = "") -> None:
        ts = int(time.time())
        with self._lock:
            self._db.execute(
                "INSERT OR REPLACE INTO revocations (serial, reason, ts) VALUES (?, ?, ?)", (serial, reason, ts)
            )
            self._db.execute("UPDATE certificates SET status = 'revoked' WHERE serial = ?", (serial,))
            self._db.commit()
        self.append_audit("revocation", {"serial": serial, "reason": reason})

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
        """Persist one metered call (the full billing entry is kept)."""
        with self._lock:
            self._db.execute(
                "INSERT INTO meter_events (ts, key_id, code_sha256,"
                " verified, credits, usd, entry_json)"
                " VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    int(entry.get("ts", time.time())),
                    entry.get("key_id", ""),
                    entry.get("code_sha256", ""),
                    1 if entry.get("verified") else 0,
                    float(entry.get("credits", 0)),
                    float(entry.get("usd", 0)),
                    _canonical(entry),
                ),
            )
            self._db.commit()
        return entry

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


_DEFAULT_STORE: Store | None = None


def default_store() -> Store:
    """Process-wide store, opened at AXIOMCODE_DB."""
    global _DEFAULT_STORE
    if _DEFAULT_STORE is None:
        _DEFAULT_STORE = Store()
    return _DEFAULT_STORE
