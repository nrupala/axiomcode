"""AxiomCode CA — signed revocation snapshots (Slice 4, step S1).

The offline verifier design (slice4-offline-verifier-design.md §2.3)
adds one new CA-published document beside the unsigned `/revoked`
list: a **revocation snapshot** — the same revoked-serial set, but
CA-signed, monotonically sequenced, and timestamped, so it can be
carried across an air gap and trusted on arrival:

    {
      "issuer": "AxiomCode CA",
      "kid": "<CA key id>",
      "sequence": 1042,
      "issued_at": 1763000000,
      "next_update_by": 1763604800,
      "revoked": ["<serial>", "…"],
      "signature": "<base64 Ed25519 over the canonical JSON of the above>"
    }

The signature is produced by `ca.CA.sign_body` over `ca.canonical` —
the production signing path, reused verbatim; this module implements
no cryptography of its own. Verification likewise runs through the
production helpers (`ca.canonical`, `ca.coerce_public_key`,
`ca.kid_for`) — the same public-key math `ca.verify_certificate`
uses, so a snapshot verified here is verified the way S2's checker
will verify it.

Sequence discipline (§2.3, §4.2): sequences come from a state file on
disk (`snapshot-sequence.json` in the snapshot directory), allocated
under an exclusive file lock with an atomic replace — never from
process memory — so monotonicity survives restarts, and a floor taken
from the currently published snapshot means a lost state file can
never re-issue an old sequence. Consumers refuse any sequence <= the
highest they have imported (anti-rollback).

Reissue duty (§4.1): a fresh snapshot is published on every revocation
event (the store CLI's revoke path calls `reissue_from_env`) and at
least weekly by schedule (systemd timer → `snapshot.py reissue`); a
no-change reissue still advances the sequence, so freshness is
provable rather than assumed. `next_update_by` = issued_at + 7 days.

Keys-document snapshot form (§4.3): `build_keys_snapshot` wraps the
`ca.public_keys_payload` key set in a signed, sequenced document,
signed by the OUTGOING CA key at rotation time and carrying every
key's full SHA-256 fingerprint, so an offline site can authenticate
an incoming key against a key it already trusts.
"""

import base64
import fcntl
import hashlib
import json
import os
import time
from pathlib import Path

import ca
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

ISSUER = ca.ISSUER
KEYS_SNAPSHOT_KIND = "axiomcode-keys-snapshot"

# §4.1 cadence: reissue at least weekly; next_update_by advertises it.
REISSUE_INTERVAL_S = 7 * 86400
# §2.3 freshness bands (Director's ruling, 2026-11-14: 7/30 as proposed).
FRESH_CURRENT_S = 7 * 86400
FRESH_STALE_S = 30 * 86400

SNAPSHOT_FILENAME = "revocation-snapshot.json"
KEYS_SNAPSHOT_FILENAME = "keys-snapshot.json"
SEQUENCE_FILENAME = "snapshot-sequence.json"


# ─── sequence allocation ─────────────────────────────────────────────


class SequenceAllocator:
    """Monotonic sequence numbers with on-disk state only.

    The counter lives in `<dir>/snapshot-sequence.json`; allocation
    takes an exclusive flock, reads, increments, and atomically
    replaces the file (tmp + fsync + os.replace + dir fsync) before
    releasing the lock. A new process — a restarted service, a timer
    firing, an operator CLI — always continues from the on-disk
    value, never from 0 and never from memory.
    """

    def __init__(self, state_dir: str | Path):
        self.dir = Path(state_dir)
        self.path = self.dir / SEQUENCE_FILENAME

    def _read_locked(self) -> int:
        try:
            data = json.loads(self.path.read_text())
            return int(data["sequence"])
        except Exception:
            return 0

    def allocate(self, floor: int = 0) -> int:
        """The next sequence: max(on-disk value, `floor`) + 1, persisted
        before it is returned. `floor` is the sequence of the currently
        published snapshot, so a damaged or deleted state file cannot
        take publication backwards."""
        self.dir.mkdir(parents=True, exist_ok=True)
        lock_path = self.dir / (SEQUENCE_FILENAME + ".lock")
        with open(lock_path, "a+") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)  # type: ignore[attr-defined]  # flock is Unix-only; the duty runs on the Linux service host
            try:
                nxt = max(self._read_locked(), int(floor)) + 1
                tmp = self.dir / (SEQUENCE_FILENAME + ".tmp")
                tmp.write_text(json.dumps({"sequence": nxt, "updated_at": int(time.time())}))
                with open(tmp) as fh:
                    os.fsync(fh.fileno())
                os.replace(tmp, self.path)
                dir_fd = os.open(self.dir, os.O_RDONLY)
                try:
                    os.fsync(dir_fd)
                finally:
                    os.close(dir_fd)
                return nxt
            finally:
                fcntl.flock(lock, fcntl.LOCK_UN)  # type: ignore[attr-defined]  # as above


# ─── document builders ───────────────────────────────────────────────


def build_revocation_snapshot(
    ca_obj: ca.CA,
    revoked_serials,
    sequence: int,
    now: int | None = None,
) -> dict:
    """The §2.3 snapshot document, signed by the CA key. The signature
    covers the canonical JSON of the unsigned document — exactly the
    shape §2.3 specifies, produced by production's `sign_body`."""
    issued = int(time.time()) if now is None else int(now)
    body = {
        "issuer": ISSUER,
        "kid": ca_obj.kid,
        "sequence": int(sequence),
        "issued_at": issued,
        "next_update_by": issued + REISSUE_INTERVAL_S,
        "revoked": sorted(revoked_serials),
    }
    doc = dict(body)
    doc["signature"] = ca_obj.sign_body(body)
    return doc


def key_fingerprint(pub: Ed25519PublicKey) -> str:
    """Full SHA-256 fingerprint of a public key (the kid is its first
    16 hex chars — ca.kid_for; the fingerprint is the whole digest,
    the form §4.3 publishes for bootstrap comparison)."""
    raw = pub.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    return hashlib.sha256(raw).hexdigest()


def build_keys_snapshot(
    ca_obj: ca.CA,
    sequence: int,
    now: int | None = None,
    signing_ca: ca.CA | None = None,
) -> dict:
    """The §4.3 keys-document snapshot form: the public_keys_payload
    key set (current + retired) in a signed, sequenced document.

    Signed by `signing_ca` — at rotation time the OUTGOING CA, whose
    key the receiving site already trusts (§4.3); defaults to ca_obj
    itself. Carries each key's full fingerprint so the incoming key
    can be checked against the signed document, not just transported
    by it."""
    signer = signing_ca or ca_obj
    issued = int(time.time()) if now is None else int(now)
    payload = ca_obj.public_keys_payload()
    fingerprints = {}
    for entry in payload["keys"]:
        pub = ca.coerce_public_key(entry["public_key"])
        fingerprints[entry["kid"]] = key_fingerprint(pub)
    body = {
        "kind": KEYS_SNAPSHOT_KIND,
        "issuer": ISSUER,
        "kid": signer.kid,
        "sequence": int(sequence),
        "issued_at": issued,
        "keys": payload["keys"],
        "fingerprints": fingerprints,
    }
    doc = dict(body)
    doc["signature"] = signer.sign_body(body)
    return doc


# ─── verification (production public-key math) ───────────────────────


def _resolve_key(doc: dict, keys) -> Ed25519PublicKey | None:
    """The public key a signed document names. `keys` is either a
    public_keys_payload dict (kid lookup across current + retired
    entries), a single public-key value ca.coerce_public_key accepts,
    or a ca.CA (its public_key_for_kid, rotation-aware)."""
    kid = doc.get("kid")
    if isinstance(keys, ca.CA):
        return keys.public_key_for_kid(kid) if kid else None
    if isinstance(keys, dict) and "keys" in keys:
        for entry in keys["keys"]:
            if entry.get("kid") == kid:
                return ca.coerce_public_key(entry["public_key"])
        return None
    pub = ca.coerce_public_key(keys)
    return pub if ca.kid_for(pub) == kid else None


def _verify_signed(doc, keys) -> dict:
    """Signature leg shared by both snapshot forms — the same helpers
    ca.verify_certificate uses: canonical body, coerced public key,
    kid agreement."""
    if not isinstance(doc, dict):
        return {"valid": False, "reason": "malformed"}
    sig_b64 = doc.get("signature")
    if not sig_b64:
        return {"valid": False, "reason": "bad_signature"}
    pub = _resolve_key(doc, keys)
    if pub is None:
        return {"valid": False, "reason": "unknown_kid"}
    body = {k: v for k, v in doc.items() if k != "signature"}
    try:
        pub.verify(base64.b64decode(sig_b64), ca.canonical(body))
    except Exception:  # InvalidSignature, malformed base64, wrong key type
        return {"valid": False, "reason": "bad_signature"}
    return {"valid": True}


def verify_revocation_snapshot(doc, keys) -> dict:
    """Verify a revocation snapshot against trusted keys: shape first
    (the §2.3 fields, typed), then the signature leg. Returns
    {valid, reason?} in the ca.verify_certificate style."""
    if not isinstance(doc, dict):
        return {"valid": False, "reason": "malformed"}
    if doc.get("issuer") != ISSUER:
        return {"valid": False, "reason": "bad_issuer"}
    for field in ("kid", "sequence", "issued_at", "next_update_by", "revoked"):
        if field not in doc:
            return {"valid": False, "reason": "malformed"}
    if not isinstance(doc["revoked"], list) or not all(isinstance(s, str) for s in doc["revoked"]):
        return {"valid": False, "reason": "malformed"}
    if not isinstance(doc["sequence"], int) or doc["sequence"] < 1:
        return {"valid": False, "reason": "malformed"}
    return _verify_signed(doc, keys)


def verify_keys_snapshot(doc, keys) -> dict:
    """Verify a keys snapshot: shape, signature, and the internal
    consistency §4.3 depends on — every listed key's fingerprint must
    match the key itself, so a signed document cannot smuggle a
    fingerprint that belongs to a different key."""
    if not isinstance(doc, dict) or doc.get("kind") != KEYS_SNAPSHOT_KIND:
        return {"valid": False, "reason": "malformed"}
    if doc.get("issuer") != ISSUER:
        return {"valid": False, "reason": "bad_issuer"}
    if not isinstance(doc.get("keys"), list) or not isinstance(doc.get("fingerprints"), dict):
        return {"valid": False, "reason": "malformed"}
    result = _verify_signed(doc, keys)
    if not result["valid"]:
        return result
    for entry in doc["keys"]:
        try:
            pub = ca.coerce_public_key(entry["public_key"])
        except Exception:
            return {"valid": False, "reason": "malformed"}
        if ca.kid_for(pub) != entry.get("kid"):
            return {"valid": False, "reason": "kid_mismatch"}
        if doc["fingerprints"].get(entry["kid"]) != key_fingerprint(pub):
            return {"valid": False, "reason": "fingerprint_mismatch"}
    return {"valid": True}


# ─── publication ─────────────────────────────────────────────────────


def _atomic_write_json(path: Path, doc: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(doc, sort_keys=True))
    with open(tmp) as fh:
        os.fsync(fh.fileno())
    os.replace(tmp, path)


def read_published(state_dir: str | Path, filename: str = SNAPSHOT_FILENAME) -> dict | None:
    path = Path(state_dir) / filename
    try:
        doc = json.loads(path.read_text())
        return doc if isinstance(doc, dict) else None
    except Exception:
        return None


def publish_revocation_snapshot(
    ca_obj: ca.CA,
    revoked_serials,
    state_dir: str | Path,
    now: int | None = None,
    reason: str = "",
) -> dict:
    """Allocate the next sequence (floored at the currently published
    snapshot's), build, sign, and atomically publish the snapshot.
    `reason` (revoke | scheduled | bootstrap | manual) is recorded in
    the publication audit sidecar, never in the signed document — the
    §2.3 shape carries no such field."""
    state_dir = Path(state_dir)
    current = read_published(state_dir)
    floor = int(current["sequence"]) if current and isinstance(current.get("sequence"), int) else 0
    sequence = SequenceAllocator(state_dir).allocate(floor=floor)
    doc = build_revocation_snapshot(ca_obj, revoked_serials, sequence, now=now)
    _atomic_write_json(state_dir / SNAPSHOT_FILENAME, doc)
    _append_publication_log(state_dir, "revocation", doc, reason)
    return doc


def publish_keys_snapshot(
    ca_obj: ca.CA,
    state_dir: str | Path,
    now: int | None = None,
    signing_ca: ca.CA | None = None,
    reason: str = "",
) -> dict:
    """Publish the keys snapshot (rotation events; §4.1's trust/keys
    update kind). Shares the one sequence allocator with revocation
    snapshots — one monotonic trust sequence per CA — while consumers
    track the highest sequence per document kind."""
    state_dir = Path(state_dir)
    current = read_published(state_dir, KEYS_SNAPSHOT_FILENAME)
    floor = int(current["sequence"]) if current and isinstance(current.get("sequence"), int) else 0
    sequence = SequenceAllocator(state_dir).allocate(floor=floor)
    doc = build_keys_snapshot(ca_obj, sequence, now=now, signing_ca=signing_ca)
    _atomic_write_json(state_dir / KEYS_SNAPSHOT_FILENAME, doc)
    _append_publication_log(state_dir, "keys", doc, reason)
    return doc


def _append_publication_log(state_dir: Path, kind: str, doc: dict, reason: str) -> None:
    entry = {
        "kind": kind,
        "sequence": doc["sequence"],
        "kid": doc["kid"],
        "issued_at": doc["issued_at"],
        "reason": reason,
        "published_at": int(time.time()),
    }
    with open(state_dir / "snapshot-publications.jsonl", "a") as fh:
        fh.write(json.dumps(entry, sort_keys=True) + "\n")


def reissue_from_env(store, ca_obj: ca.CA | None = None) -> dict | None:
    """The revocation-event trigger (§4.1): called by the store CLI's
    revoke path after a revocation commits. Publication is configured
    by AXIOMCODE_SNAPSHOT_DIR; unset means the snapshot duty is not
    armed in this deployment and the call is a no-op (the weekly timer
    and the on-read bootstrap in verify_api are the other two legs).
    A publication failure is raised to the caller, which reports it
    loudly — it never un-commits the revocation itself."""
    state_dir = os.environ.get("AXIOMCODE_SNAPSHOT_DIR")
    if not state_dir:
        return None
    ca_obj = ca_obj or ca.CA.load_or_create()
    return publish_revocation_snapshot(ca_obj, store.revoked_serials(), state_dir, reason="revoke")


# ─── reference consumer (the import side S2 builds on) ───────────────


def freshness_band(doc: dict | None, now: int | None = None) -> str:
    """§2.3's bands, on the snapshot's own issued_at against local
    time: current (<= 7d), stale (<= 30d), hard-stale (> 30d), or
    none (no snapshot). A future-dated snapshot reports hard-stale
    here and is refused at import (see SnapshotImporter)."""
    if not doc:
        return "none"
    age = (int(time.time()) if now is None else int(now)) - int(doc["issued_at"])
    if age < 0:
        return "hard-stale"
    if age <= FRESH_CURRENT_S:
        return "current"
    if age <= FRESH_STALE_S:
        return "stale"
    return "hard-stale"


class SnapshotImporter:
    """The consumer side of §2.3/§4.2, in reference form: verify the
    signature against trusted keys, refuse a future-dated snapshot
    (mis-signed-or-mis-clocked, §2.3), refuse any sequence <= the
    highest already imported for that kind (anti-rollback), and only
    then replace the stored document. A refused import changes
    nothing. State is a JSON file on disk — highest sequences survive
    restarts exactly as the allocator's do."""

    def __init__(self, state_path: str | Path):
        self.path = Path(state_path)
        self.state = self._load()

    def _load(self) -> dict:
        try:
            data = json.loads(self.path.read_text())
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def _save(self) -> None:
        _atomic_write_json(self.path, self.state)

    def highest(self, kind: str) -> int:
        return int(self.state.get("highest", {}).get(kind, 0))

    def _import(self, kind: str, doc, verify_fn, keys, now: int | None = None) -> dict:
        result = verify_fn(doc, keys)
        if not result["valid"]:
            return {"imported": False, "reason": result["reason"]}
        now = int(time.time()) if now is None else int(now)
        if int(doc["issued_at"]) > now:
            return {"imported": False, "reason": "issued_in_future"}
        if int(doc["sequence"]) <= self.highest(kind):
            return {"imported": False, "reason": "rollback"}
        self.state.setdefault("highest", {})[kind] = int(doc["sequence"])
        self.state.setdefault("documents", {})[kind] = doc
        self._save()
        return {"imported": True, "sequence": int(doc["sequence"])}

    def import_revocation_snapshot(self, doc, keys, now: int | None = None) -> dict:
        return self._import("revocation", doc, verify_revocation_snapshot, keys, now=now)

    def import_keys_snapshot(self, doc, keys, now: int | None = None) -> dict:
        return self._import("keys", doc, verify_keys_snapshot, keys, now=now)

    def document(self, kind: str) -> dict | None:
        doc = self.state.get("documents", {}).get(kind)
        return doc if isinstance(doc, dict) else None


# ─── CLI ─────────────────────────────────────────────────────────────


def _main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(prog="snapshot", description="AxiomCode CA snapshot duty (Slice 4 S1)")
    sub = parser.add_subparsers(dest="cmd", required=True)

    reissue = sub.add_parser("reissue", help="publish a fresh revocation snapshot over the store's current revoked set")
    reissue.add_argument("--reason", default="scheduled", help="publication-log reason (scheduled | manual | …)")
    reissue.add_argument("--state-dir", default=None, help="snapshot dir (default: AXIOMCODE_SNAPSHOT_DIR)")
    reissue.add_argument("--db", default=None, help="store path (default: AXIOMCODE_DB)")

    keys_cmd = sub.add_parser("keys-snapshot", help="publish a keys snapshot (§4.3 form) signed by the current CA key")
    keys_cmd.add_argument("--state-dir", default=None, help="snapshot dir (default: AXIOMCODE_SNAPSHOT_DIR)")

    verify = sub.add_parser("verify", help="verify a snapshot file against a keys payload file (generic tooling)")
    verify.add_argument("snapshot_file")
    verify.add_argument("keys_file")

    args = parser.parse_args(argv)
    state_dir: str | None = getattr(args, "state_dir", None) or os.environ.get("AXIOMCODE_SNAPSHOT_DIR")
    if args.cmd in ("reissue", "keys-snapshot") and not state_dir:
        print("error: no snapshot dir (--state-dir or AXIOMCODE_SNAPSHOT_DIR)", flush=True)
        return 2
    # Past the guard, the two commands that use a snapshot dir have
    # one; "verify" never reads it.
    snapshot_dir = state_dir or ""
    if args.cmd == "reissue":
        from store import Store

        store = Store(args.db)
        try:
            doc = publish_revocation_snapshot(
                ca.CA.load_or_create(), store.revoked_serials(), snapshot_dir, reason=args.reason
            )
        finally:
            store.close()
        print(json.dumps({"sequence": doc["sequence"], "kid": doc["kid"], "revoked": len(doc["revoked"])}))
        return 0
    if args.cmd == "keys-snapshot":
        doc = publish_keys_snapshot(ca.CA.load_or_create(), snapshot_dir, reason="manual")
        print(json.dumps({"sequence": doc["sequence"], "kid": doc["kid"], "keys": len(doc["keys"])}))
        return 0
    if args.cmd == "verify":
        doc = json.loads(Path(args.snapshot_file).read_text())
        keys = json.loads(Path(args.keys_file).read_text())
        fn = verify_keys_snapshot if doc.get("kind") == KEYS_SNAPSHOT_KIND else verify_revocation_snapshot
        result = fn(doc, keys)
        print(json.dumps(result))
        return 0 if result["valid"] else 1
    return 2


if __name__ == "__main__":
    raise SystemExit(_main())
