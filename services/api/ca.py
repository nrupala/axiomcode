"""AxiomCode CA — Ed25519 certification authority (production, W1).

Replaces the prototype's HMAC-SHA256 signing (certs.py, kept for legacy
fixtures) with asymmetric Ed25519 signatures: certificates can be
verified by ANYONE holding only the public key, which is published at
/.well-known/axiomcode-keys.json. The private key never leaves the CA
key file (PEM, mode 0600).

Certificate format v2: the prototype fields (serial, issuer,
valid_from / valid_until — a 90-day window, code_sha256 [artifact hash],
verified [verdict], toolchain, attempts, key_id [caller]) plus:
  "version": 2, "alg": "Ed25519", "kid": <CA key id>,
  "signature": base64 Ed25519 signature over the canonical JSON of the
  certificate body (every field except "signature", json.dumps with
  sort_keys=True — the same canonicalization as certs.py).
"""

import base64
import hashlib
import json
import os
import time
import uuid
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

_HERE = Path(__file__).parent
ISSUER = "AxiomCode CA"
ALG = "Ed25519"
VALIDITY_DAYS = int(os.environ.get("AXIOMCODE_CERT_VALIDITY_DAYS", "90"))
DEFAULT_KEY_FILE = os.environ.get("AXIOMCODE_CA_KEY_FILE", str(_HERE / "ca_key.pem"))


def canonical(body: dict) -> bytes:
    """Canonical bytes of a certificate body — same approach as certs.py."""
    return json.dumps(body, sort_keys=True).encode()


def kid_for(public_key: Ed25519PublicKey) -> str:
    """Stable key id: first 16 hex of SHA-256 over the raw public key."""
    raw = public_key.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    return hashlib.sha256(raw).hexdigest()[:16]


def _pem_private(key: Ed25519PrivateKey) -> bytes:
    return key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )


def _pem_public(key: Ed25519PublicKey) -> str:
    return key.public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()


def coerce_public_key(key) -> Ed25519PublicKey:
    """Accept an Ed25519PublicKey, a base64 raw-key string, raw bytes,
    or a PEM string — so a key taken straight out of the published
    /.well-known/axiomcode-keys.json payload can verify certificates."""
    if isinstance(key, Ed25519PublicKey):
        return key
    if isinstance(key, str) and "BEGIN PUBLIC KEY" in key:
        loaded = serialization.load_pem_public_key(key.encode())
        if not isinstance(loaded, Ed25519PublicKey):
            raise ValueError("PEM does not hold an Ed25519 public key")
        return loaded
    raw = base64.b64decode(key) if isinstance(key, str) else bytes(key)
    return Ed25519PublicKey.from_public_bytes(raw)


def _retired_registry_path(key_file: Path) -> Path:
    """Retired public keys live beside the signing key:
    ca_key.pem -> ca_key.retired.json."""
    return key_file.with_name(key_file.stem + ".retired.json")


def _load_retired(key_file: Path) -> dict[str, Ed25519PublicKey]:
    path = _retired_registry_path(key_file)
    if not path.exists():
        return {}
    out: dict[str, Ed25519PublicKey] = {}
    for entry in json.loads(path.read_text()).get("retired", []):
        pub = Ed25519PublicKey.from_public_bytes(base64.b64decode(entry["public_key"]))
        out[entry["kid"]] = pub
    return out


def _save_retired(key_file: Path, retired: dict[str, Ed25519PublicKey]) -> None:
    entries = [
        {
            "kid": kid,
            "public_key": base64.b64encode(
                pub.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
            ).decode(),
        }
        for kid, pub in sorted(retired.items())
    ]
    path = _retired_registry_path(key_file)
    path.write_text(json.dumps({"retired": entries}, indent=2))
    os.chmod(path, 0o600)


class CA:
    """An Ed25519 certification authority: one current signing key
    plus the retired public keys it still stands behind for
    verification (key rotation, L1 item 3)."""

    def __init__(
        self,
        private_key: Ed25519PrivateKey,
        retired: dict[str, Ed25519PublicKey] | None = None,
    ):
        self._private = private_key
        self.public_key = private_key.public_key()
        self.kid = kid_for(self.public_key)
        self._retired = dict(retired or {})

    def public_key_for_kid(self, kid: str) -> Ed25519PublicKey | None:
        """The published key a certificate names: the current key, a
        retired key, or None (unknown kid — not ours to vouch for)."""
        if kid == self.kid:
            return self.public_key
        return self._retired.get(kid)

    # ─── key management ──────────────────────────────────────────────
    @classmethod
    def generate(cls) -> "CA":
        return cls(Ed25519PrivateKey.generate())

    @classmethod
    def load_or_create(cls, key_file: str | Path | None = None) -> "CA":
        """Load the CA key from `key_file`, generating and persisting a
        new one (PEM, mode 0600) if it does not exist yet."""
        path = Path(key_file or DEFAULT_KEY_FILE)
        retired = _load_retired(path)
        if path.exists():
            key = serialization.load_pem_private_key(path.read_bytes(), password=None)
            if not isinstance(key, Ed25519PrivateKey):
                raise ValueError(f"{path} does not hold an Ed25519 key")
            return cls(key, retired=retired)
        ca = cls.generate()
        ca._retired = retired
        path.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            os.write(fd, _pem_private(ca._private))
        finally:
            os.close(fd)
        os.chmod(path, 0o600)
        return ca

    @classmethod
    def rotate(cls, key_file: str | Path | None = None) -> "CA":
        """Rotate the signing key: the current public key moves to
        the retired registry (existing certificates keep verifying
        against it), and a fresh key becomes current. The registry is
        written BEFORE the key file is replaced, so an interruption
        never leaves the old key unpublished. Returns the new CA —
        a running service must restart to serve it."""
        path = Path(key_file or DEFAULT_KEY_FILE)
        if not path.exists():
            raise FileNotFoundError(f"no CA key at {path} to rotate")
        current = cls.load_or_create(path)
        retired = {**current._retired, current.kid: current.public_key}
        _save_retired(path, retired)
        new_key = Ed25519PrivateKey.generate()
        tmp = path.with_name(path.name + ".tmp")
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        try:
            os.write(fd, _pem_private(new_key))
        finally:
            os.close(fd)
        os.replace(tmp, path)
        os.chmod(path, 0o600)
        return cls(new_key, retired=retired)

    # ─── issuance ────────────────────────────────────────────────────
    def sign_body(self, body: dict) -> str:
        sig = self._private.sign(canonical(body))
        return base64.b64encode(sig).decode()

    def issue(self, subject: dict) -> dict:
        """Issue a v2 certificate. `subject` holds the verdict fields
        (code_sha256, verified, attempts, toolchain, key_id, ...).
        The CA-fixed fields (version, alg, kid, serial, issuer,
        validity window) are applied AFTER the subject spread, so a
        subject can never override them (PR #21 review hardening)."""
        now = int(time.time())
        cert = {
            **subject,
            "version": 2,
            "alg": ALG,
            "kid": self.kid,
            "serial": uuid.uuid4().hex[:16],
            "issuer": ISSUER,
            "valid_from": now,
            "valid_until": now + VALIDITY_DAYS * 86400,
        }
        cert["signature"] = self.sign_body(cert)
        return cert

    # ─── publication ─────────────────────────────────────────────────
    @staticmethod
    def _key_entry(pub: Ed25519PublicKey, status: str) -> dict:
        raw = pub.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
        return {
            "kid": kid_for(pub),
            "alg": ALG,
            "use": "cert-signing",
            "status": status,
            "public_key": base64.b64encode(raw).decode(),
            "public_key_pem": _pem_public(pub),
        }

    def public_keys_payload(self) -> dict:
        """The document served at /.well-known/axiomcode-keys.json:
        the current signing key plus every retired key whose
        certificates may still be in their validity window."""
        keys = [self._key_entry(self.public_key, "current")]
        keys += [self._key_entry(self._retired[kid], "retired") for kid in sorted(self._retired)]
        return {"issuer": ISSUER, "keys": keys, "published_at": int(time.time())}


def verify_certificate(cert: dict, public_key=None, ca: CA | None = None) -> dict:
    """Validate a v2 certificate's signature and validity window using
    ONLY a public key (the CA's own by default, or one supplied — e.g.
    taken from the published keys payload). Revocation is layered on
    top by the caller via store.is_revoked — a public key alone cannot
    know the revocation list, same split as X.509 vs CRL.

    Returns the certs.check shape: {valid, reason?, payload?}."""
    if not isinstance(cert, dict) or cert.get("alg") != ALG:
        return {"valid": False, "reason": "bad_signature"}
    sig_b64 = cert.get("signature")
    if not sig_b64:
        return {"valid": False, "reason": "bad_signature"}
    if public_key is not None:
        pub = coerce_public_key(public_key)
    elif ca is not None:
        resolved = ca.public_key_for_kid(cert.get("kid", ""))
        if resolved is None:
            return {"valid": False, "reason": "unknown_kid"}
        pub = resolved
    else:
        pub = coerce_public_key(default_ca().public_key)
    body = {k: v for k, v in cert.items() if k != "signature"}
    try:
        pub.verify(base64.b64decode(sig_b64), canonical(body))
    except Exception:  # InvalidSignature, malformed base64, wrong key type
        return {"valid": False, "reason": "bad_signature"}
    if cert.get("kid") != kid_for(pub):
        # The signature verifies under this key but the cert names a
        # different one — not a cert this key stands behind.
        return {"valid": False, "reason": "unknown_kid"}
    now = int(time.time())
    if now < cert.get("valid_from", 0):
        return {"valid": False, "reason": "not_yet_valid"}
    if now > cert.get("valid_until", 0):
        return {"valid": False, "reason": "expired", "payload": cert, "renew": True}
    return {"valid": True, "payload": cert}


_DEFAULT_CA: CA | None = None


def default_ca() -> CA:
    """Process-wide CA, loaded/created from AXIOMCODE_CA_KEY_FILE."""
    global _DEFAULT_CA
    if _DEFAULT_CA is None:
        _DEFAULT_CA = CA.load_or_create()
    return _DEFAULT_CA


def encode(cert: dict) -> str:
    return json.dumps(cert, sort_keys=True)


def decode(raw: str) -> dict | None:
    try:
        c = json.loads(raw)
        return c if isinstance(c, dict) else None
    except Exception:
        return None


def _main(argv: list[str] | None = None) -> int:
    """Operator CLI: python -m ca rotate [--key-file PATH]
    Rotates the CA signing key (see CA.rotate). Prints the old and
    new kids; the API must be restarted to serve the new key."""
    import argparse

    parser = argparse.ArgumentParser(prog="ca", description="AxiomCode CA operator tools")
    sub = parser.add_subparsers(dest="cmd", required=True)
    rotate = sub.add_parser("rotate", help="rotate the CA signing key")
    rotate.add_argument("--key-file", default=None, help="key path (default: AXIOMCODE_CA_KEY_FILE)")
    args = parser.parse_args(argv)
    if args.cmd == "rotate":
        key_file = args.key_file or DEFAULT_KEY_FILE
        before = CA.load_or_create(key_file)
        after = CA.rotate(key_file)
        print(f"rotated: {before.kid} -> {after.kid}")
        print(f"retired keys published: {len(after._retired)}")
        print("restart the API to serve the new key")
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(_main())
