"""AxiomCode CA — certificate issuance, verification, revocation.

Every verification verdict becomes an X.509-style certificate (JSON):
  serial, issuer, subject (code hash), verdict, toolchain,
  valid_from / valid_until, key_id.

Certificates EXPIRE (default 90 days, like Let's Encrypt) — correctness
is re-verified, which is also the renewal revenue model.
Revocation covers mis-issuance: if a toolchain bug invalidates past
verdicts, their serials go on the revocation list.
"""

import hashlib
import hmac
import json
import os
import time
import uuid
from pathlib import Path

_HERE = Path(__file__).parent
ISSUER = "AxiomCode CA"
SECRET = os.environ.get("AXIOMCODE_CERT_SECRET", "dev-secret-change-me").encode()
VALIDITY_DAYS = int(os.environ.get("AXIOMCODE_CERT_VALIDITY_DAYS", "90"))
REVOKED_FILE = os.environ.get("AXIOMCODE_REVOKED_FILE", str(_HERE / "revoked.txt"))


def issue(subject: dict) -> dict:
    """Issue a certificate. `subject` holds the verdict fields."""
    now = int(time.time())
    cert = {
        "serial": uuid.uuid4().hex[:16],
        "issuer": ISSUER,
        "valid_from": now,
        "valid_until": now + VALIDITY_DAYS * 86400,
        **subject,
    }
    body = json.dumps(cert, sort_keys=True).encode()
    sig = hmac.new(SECRET, body, hashlib.sha256).hexdigest()
    cert["signature"] = sig
    return cert


def _verify_sig(cert: dict) -> bool:
    sig = cert.get("signature", "")
    body = {k: v for k, v in cert.items() if k != "signature"}
    raw = json.dumps(body, sort_keys=True).encode()
    return hmac.compare_digest(sig, hmac.new(SECRET, raw, hashlib.sha256).hexdigest())


def revoked_serials() -> set:
    p = Path(REVOKED_FILE)
    if not p.exists():
        return set()
    return {line.strip() for line in p.read_text().splitlines() if line.strip()}


def revoke(serial: str) -> None:
    with open(REVOKED_FILE, "a") as f:
        f.write(serial.strip() + "\n")


def check(cert: dict) -> dict:
    """Validate a certificate. Returns status anyone can interpret."""
    if not isinstance(cert, dict) or not _verify_sig(cert):
        return {"valid": False, "reason": "bad_signature"}
    now = int(time.time())
    if now < cert.get("valid_from", 0):
        return {"valid": False, "reason": "not_yet_valid"}
    if now > cert.get("valid_until", 0):
        return {"valid": False, "reason": "expired", "payload": cert, "renew": True}
    if cert.get("serial") in revoked_serials():
        return {"valid": False, "reason": "revoked", "payload": cert}
    return {"valid": True, "payload": cert}


def encode(cert: dict) -> str:
    return json.dumps(cert, sort_keys=True)


def decode(raw: str) -> dict | None:
    try:
        c = json.loads(raw)
        return c if isinstance(c, dict) else None
    except Exception:
        return None
