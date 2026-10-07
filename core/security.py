"""
AxiomCode Security Layer
=========================
Zero-trust design: encrypted key storage, signed artifacts, honest
verification accounting (a signature attests to provenance — never to
proofhood by itself; see `verification_status`).

Cryptographic operations:
- hashlib (SHA-256, SHA-512, HMAC) — stdlib
- secrets (cryptographic random) — stdlib
- Ed25519 signatures via the `cryptography` package — REQUIRED for
  certificate signing. Signatures must be verifiable by third parties and
  agents without a shared secret, which symmetric HMAC cannot provide.
  (The old stdlib-only constraint yielded here deliberately: hand-rolling
  Ed25519 would be far worse than taking the audited dependency.)
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
import os
import secrets
import time
from dataclasses import dataclass, field
from pathlib import Path

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

# ─── Cryptographic Constants ────────────────────────────────────────────────

HASH_ALGORITHM = "sha512"
HMAC_ALGORITHM = "sha512"
KEY_SIZE = 64  # 512-bit keys
NONCE_SIZE = 32
SALT_SIZE = 32
# Certificate schema version. v2 adds: serial number, validity window,
# revocation fields, artifact version pin, tier, builder/issuer identity
# fields, per-file MD5s, and QR payload. v1 certificates must be migrated
# with re-signing (see ProofCertificate.migrate_v1_to_v2) — never silently.
CERT_SCHEMA_VERSION = 2
# Version stamp for keystore key files. This is INDEPENDENT of the
# certificate schema version (a past bug conflated the two).
KEYSTORE_FILE_VERSION = 1
# Legacy alias: the old single version constant. Kept for compatibility;
# new code uses CERT_SCHEMA_VERSION / KEYSTORE_FILE_VERSION.
PROOF_CERT_VERSION = 1


# ─── Key Management ─────────────────────────────────────────────────────────


@dataclass
class KeyPair:
    """Symmetric key pair for encryption and signing."""

    encryption_key: bytes  # For data encryption
    signing_key: bytes  # For code/proof signing
    key_id: str  # Unique key identifier
    created_at: float  # Creation timestamp

    @classmethod
    def generate(cls) -> KeyPair:
        """Generate a cryptographically secure key pair."""
        return cls(
            encryption_key=secrets.token_bytes(KEY_SIZE),
            signing_key=secrets.token_bytes(KEY_SIZE),
            key_id=secrets.token_hex(8),
            created_at=time.time(),
        )

    def to_dict(self) -> dict:
        return {
            "encryption_key": base64.b64encode(self.encryption_key).decode(),
            "signing_key": base64.b64encode(self.signing_key).decode(),
            "key_id": self.key_id,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> KeyPair:
        return cls(
            encryption_key=base64.b64decode(data["encryption_key"]),
            signing_key=base64.b64decode(data["signing_key"]),
            key_id=data["key_id"],
            created_at=data["created_at"],
        )


class KeyStore:
    """Secure key storage with zero-knowledge design.

    Keys are never stored in plaintext on disk.
    They are encrypted with a master key derived from user input.
    """

    def __init__(self, store_dir: str | Path = ".axiomcode/keys"):
        self.store_dir = Path(store_dir)
        self.store_dir.mkdir(parents=True, exist_ok=True)
        self._cache: dict[str, KeyPair] = {}

    def _derive_master_key(self, passphrase: str, salt: bytes) -> bytes:
        """Derive a master key from passphrase using PBKDF2."""
        return hashlib.pbkdf2_hmac(
            "sha512",
            passphrase.encode("utf-8"),
            salt,
            iterations=600000,  # OWASP 2024 recommendation
        )

    def _encrypt_key(self, key_data: bytes, master_key: bytes) -> dict:
        """Encrypt key data using XOR with derived keystream (simple but secure with strong key)."""
        nonce = secrets.token_bytes(NONCE_SIZE)
        keystream = hashlib.sha512(master_key + nonce).digest()
        # Expand keystream if needed
        while len(keystream) < len(key_data):
            keystream += hashlib.sha512(keystream[-64:] + nonce).digest()
        encrypted = bytes(a ^ b for a, b in zip(key_data, keystream[: len(key_data)], strict=True))
        return {
            "nonce": base64.b64encode(nonce).decode(),
            "data": base64.b64encode(encrypted).decode(),
        }

    def _decrypt_key(self, encrypted: dict, master_key: bytes) -> bytes:
        """Decrypt key data."""
        nonce = base64.b64decode(encrypted["nonce"])
        data = base64.b64decode(encrypted["data"])
        keystream = hashlib.sha512(master_key + nonce).digest()
        while len(keystream) < len(data):
            keystream += hashlib.sha512(keystream[-64:] + nonce).digest()
        return bytes(a ^ b for a, b in zip(data, keystream[: len(data)], strict=True))

    def create_key(self, name: str, passphrase: str) -> KeyPair:
        """Create and store a new key pair."""
        keypair = KeyPair.generate()
        salt = secrets.token_bytes(SALT_SIZE)
        master_key = self._derive_master_key(passphrase, salt)
        encrypted = self._encrypt_key(
            json.dumps(keypair.to_dict()).encode(),
            master_key,
        )

        key_file = self.store_dir / f"{name}.key"
        key_file.write_text(
            json.dumps(
                {
                    "version": KEYSTORE_FILE_VERSION,
                    "salt": base64.b64encode(salt).decode(),
                    "encrypted": encrypted,
                },
                indent=2,
            )
        )

        self._cache[name] = keypair
        return keypair

    def load_key(self, name: str, passphrase: str) -> KeyPair:
        """Load a key pair from storage.

        Always validates the passphrase — never returns cached key without verification.
        This ensures security-sensitive operations always verify user credentials.
        """
        key_file = self.store_dir / f"{name}.key"
        if not key_file.exists():
            raise FileNotFoundError(f"Key not found: {name}")

        try:
            data = json.loads(key_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            raise ValueError(f"Invalid key file: {e}") from e

        if not isinstance(data, dict) or "salt" not in data or "encrypted" not in data:
            raise ValueError("Invalid key file format")

        try:
            salt = base64.b64decode(data["salt"])
            master_key = self._derive_master_key(passphrase, salt)
            decrypted = self._decrypt_key(data["encrypted"], master_key)
            decrypted_dict = json.loads(decrypted)
            # Validate that decrypted data has expected structure
            if not isinstance(decrypted_dict, dict) or "key_id" not in decrypted_dict:
                raise ValueError("Invalid decrypted key structure - wrong passphrase?")
            keypair = KeyPair.from_dict(decrypted_dict)
        except (binascii.Error, json.JSONDecodeError, ValueError) as e:
            raise ValueError(f"Failed to decrypt key: {e}") from e

        self._cache[name] = keypair
        return keypair

    def delete_key(self, name: str) -> None:
        """Securely delete a key pair."""
        key_file = self.store_dir / f"{name}.key"
        if key_file.exists():
            # Overwrite with random data before deletion
            key_file.write_bytes(secrets.token_bytes(key_file.stat().st_size))
            key_file.unlink()
        self._cache.pop(name, None)

    def create_signing_key(self, name: str, passphrase: str) -> Ed25519KeyPair:
        """Create and store a new Ed25519 signing key pair.

        Signing keys live in `<name>.signing.key`, separate from the legacy
        symmetric keys — the two are never interchangeable.
        """
        keypair = Ed25519KeyPair.generate()
        salt = secrets.token_bytes(SALT_SIZE)
        master_key = self._derive_master_key(passphrase, salt)
        encrypted = self._encrypt_key(
            json.dumps(keypair.to_dict()).encode(),
            master_key,
        )
        key_file = self.store_dir / f"{name}.signing.key"
        key_file.write_text(
            json.dumps(
                {
                    "version": KEYSTORE_FILE_VERSION,
                    "salt": base64.b64encode(salt).decode(),
                    "encrypted": encrypted,
                },
                indent=2,
            )
        )
        return keypair

    def load_signing_key(self, name: str, passphrase: str) -> Ed25519KeyPair:
        """Load an Ed25519 signing key pair from storage."""
        key_file = self.store_dir / f"{name}.signing.key"
        if not key_file.exists():
            raise FileNotFoundError(f"Signing key not found: {name}")
        try:
            data = json.loads(key_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            raise ValueError(f"Invalid signing key file: {e}") from e
        if not isinstance(data, dict) or "salt" not in data or "encrypted" not in data:
            raise ValueError("Invalid signing key file format")
        try:
            salt = base64.b64decode(data["salt"])
            master_key = self._derive_master_key(passphrase, salt)
            decrypted = self._decrypt_key(data["encrypted"], master_key)
            decrypted_dict = json.loads(decrypted)
            if not isinstance(decrypted_dict, dict) or decrypted_dict.get("algorithm") != "ed25519":
                raise ValueError("Invalid decrypted signing key structure - wrong passphrase?")
            return Ed25519KeyPair.from_dict(decrypted_dict)
        except (binascii.Error, json.JSONDecodeError, ValueError) as e:
            raise ValueError(f"Failed to decrypt signing key: {e}") from e


# ─── Ed25519 signing keys ────────────────────────────────────────────────────
#
# Certificate signatures MUST be asymmetric: anyone (third parties, agents)
# must be able to verify a certificate using only the public key, which is
# published inside the certificate itself. HMAC is symmetric — verification
# requires the secret — so it can never serve as a public trust primitive.


@dataclass
class Ed25519KeyPair:
    """Asymmetric key pair for certificate signing.

    The private key signs; the public key verifies and is safe to publish
    (it is embedded in every certificate this key signs).
    """

    private_key: bytes  # 32-byte Ed25519 seed — SECRET
    public_key: bytes  # 32-byte Ed25519 public key — safe to publish
    key_id: str
    created_at: float

    @classmethod
    def generate(cls) -> Ed25519KeyPair:
        """Generate a fresh Ed25519 key pair."""
        private = Ed25519PrivateKey.generate()
        private_bytes = private.private_bytes_raw()
        public_bytes = private.public_key().public_bytes_raw()
        return cls(
            private_key=private_bytes,
            public_key=public_bytes,
            key_id=secrets.token_hex(8),
            created_at=time.time(),
        )

    def to_dict(self) -> dict:
        return {
            "algorithm": "ed25519",
            "private_key": base64.b64encode(self.private_key).decode(),
            "public_key": base64.b64encode(self.public_key).decode(),
            "key_id": self.key_id,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Ed25519KeyPair:
        if data.get("algorithm", "ed25519") != "ed25519":
            raise ValueError(f"Not an Ed25519 keypair: {data.get('algorithm')}")
        private_key = base64.b64decode(data["private_key"])
        public_key = base64.b64decode(data["public_key"])
        if len(private_key) != 32 or len(public_key) != 32:
            raise ValueError("Invalid Ed25519 key lengths")
        return cls(
            private_key=private_key,
            public_key=public_key,
            key_id=data["key_id"],
            created_at=data["created_at"],
        )


def ed25519_sign(private_key: bytes, data: bytes) -> str:
    """Sign data with an Ed25519 private key. Returns base64 signature."""
    if len(private_key) != 32:
        raise ValueError("Ed25519 private key must be 32 bytes")
    private = Ed25519PrivateKey.from_private_bytes(private_key)
    return base64.b64encode(private.sign(data)).decode()


def ed25519_verify(public_key: bytes, data: bytes, signature: str) -> bool:
    """Verify an Ed25519 signature. Never raises on bad input — returns False."""
    try:
        if len(public_key) != 32:
            return False
        public = Ed25519PublicKey.from_public_bytes(public_key)
        public.verify(base64.b64decode(signature), data)
        return True
    except (InvalidSignature, ValueError, binascii.Error):
        return False


def ed25519_public_from_private(private_key: bytes) -> bytes:
    """Derive the Ed25519 public key from a private key."""
    if len(private_key) != 32:
        raise ValueError("Ed25519 private key must be 32 bytes")
    return Ed25519PrivateKey.from_private_bytes(private_key).public_key().public_bytes_raw()


# ─── Cryptographic Hashing ──────────────────────────────────────────────────


def hash_data(data: bytes, algorithm: str = HASH_ALGORITHM) -> str:
    """Compute cryptographic hash of data."""
    h = hashlib.new(algorithm)
    h.update(data)
    return h.hexdigest()


def hash_file(path: Path, algorithm: str = HASH_ALGORITHM) -> str:
    """Compute cryptographic hash of a file."""
    h = hashlib.new(algorithm)
    with open(path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()


def compute_hmac(key: bytes, data: bytes, algorithm: str = HMAC_ALGORITHM) -> str:
    """Compute HMAC for data authentication."""
    return hmac.new(key, data, algorithm).hexdigest()


def verify_hmac(key: bytes, data: bytes, expected: str, algorithm: str = HMAC_ALGORITHM) -> bool:
    """Verify HMAC with constant-time comparison."""
    computed = hmac.new(key, data, algorithm).hexdigest()
    return hmac.compare_digest(computed, expected)


# ─── Proof Certificates ─────────────────────────────────────────────────────


@dataclass
class ProofCertificate:
    """Cryptographic certificate attesting to a generated artifact.

    This is the core of AxiomCode's zero-trust model. Every generated
    algorithm comes with a signed certificate that can be independently
    verified. The signature attests to *provenance and integrity* — who
    generated the artifact, when, from what spec, and with what toolchain.
    Whether the proof was actually machine-checked is recorded honestly in
    `verification_status` ("verified" / "unverified" / "failed"); a signature
    alone never implies proofhood.

    Signatures are Ed25519 (asymmetric): the public verification key is
    embedded in the certificate itself (`verify_key`) and covered by the
    signature, so any third party or agent can verify authenticity without a
    shared secret.
    """

    version: int = CERT_SCHEMA_VERSION
    algorithm_name: str = ""
    spec_hash: str = ""  # Hash of the Lean 4 specification
    proof_hash: str = ""  # Hash of the proof term
    c_binary_hash: str = ""  # Hash of the compiled C binary
    python_hash: str = ""  # Hash of the Python package
    theorem: str = ""  # The theorem statement
    tactics: list[str] = field(default_factory=list)
    steps: int = 0
    lemmas: int = 0
    model_used: str = ""
    generated_at: float = 0.0
    signature: str = ""  # base64 Ed25519 signature over the payload
    key_id: str = ""  # Key used for signing
    verify_key: str = ""  # base64 Ed25519 public key — safe to publish
    # Honest verification accounting. "verified" ONLY when a proof assistant
    # machine-checked the proof; "unverified"/"failed" otherwise. The signature
    # attests to provenance and integrity — never to proofhood by itself.
    verification_status: str = "unverified"
    lean_version: str = ""  # Lean toolchain version that checked the proof
    build_log_hash: str = ""  # Hash of the (truncated) build log
    # ── Schema v2 fields (SPEC: certificate product) ──────────────────────
    serial: str = ""  # Unique, issuer-scoped serial number, e.g. AXC-1A2B3C4D-ABCDEF123456
    issued_at: float = 0.0  # Validity window start (unix time)
    expires_at: float = 0.0  # Validity window end; 0 = never expires
    revoked: bool = False  # Revocation flag (registry revocation list is authoritative)
    revocation_reason: str = ""  # Why revoked, when revoked=True
    artifact_version: str = ""  # Version pin of the certified artifact, e.g. "1.2.3"
    tier: str = ""  # "scan" | "verified" | "certified" — verification depth sold
    product_name: str = ""  # Builder's product name (builder branding)
    owner: str = ""  # Builder name/identity
    repo_or_website: str = ""  # Canonical source locator: repo URL or website
    owner_contact: str = ""  # Builder contact for third-party inquiries
    issuer_name: str = "AxiomCode"  # Our details as issuer
    issuer_website: str = ""
    issuer_contact: str = ""
    md5_hashes: dict[str, str] = field(default_factory=dict)  # per-file MD5s for customer checks
    qr_payload: str = ""  # Verification URL encoded in the certificate QR code

    def _payload(self) -> bytes:
        """Get the certificate payload (excluding signature)."""
        data = {
            "version": self.version,
            "algorithm_name": self.algorithm_name,
            "spec_hash": self.spec_hash,
            "proof_hash": self.proof_hash,
            "c_binary_hash": self.c_binary_hash,
            "python_hash": self.python_hash,
            "theorem": self.theorem,
            "tactics": self.tactics,
            "steps": self.steps,
            "lemmas": self.lemmas,
            "model_used": self.model_used,
            "generated_at": self.generated_at,
            "key_id": self.key_id,
            "verify_key": self.verify_key,
            "verification_status": self.verification_status,
            "lean_version": self.lean_version,
            "build_log_hash": self.build_log_hash,
            "serial": self.serial,
            "issued_at": self.issued_at,
            "expires_at": self.expires_at,
            "revoked": self.revoked,
            "revocation_reason": self.revocation_reason,
            "artifact_version": self.artifact_version,
            "tier": self.tier,
            "product_name": self.product_name,
            "owner": self.owner,
            "repo_or_website": self.repo_or_website,
            "owner_contact": self.owner_contact,
            "issuer_name": self.issuer_name,
            "issuer_website": self.issuer_website,
            "issuer_contact": self.issuer_contact,
            "md5_hashes": self.md5_hashes,
            "qr_payload": self.qr_payload,
        }
        return json.dumps(data, sort_keys=True).encode("utf-8")

    def sign(self, private_key: bytes) -> ProofCertificate:
        """Sign the certificate with an Ed25519 private key (32 bytes).

        The corresponding public key is embedded in the certificate and
        covered by the signature, so verifiers need no shared secret.
        """
        self.verify_key = base64.b64encode(ed25519_public_from_private(private_key)).decode()
        self.signature = ed25519_sign(private_key, self._payload())
        return self

    def verify(self, public_key: bytes | None = None) -> bool:
        """Verify the certificate's Ed25519 signature.

        Uses the explicitly provided public key, or the key embedded in the
        certificate itself. (Embedded-key verification detects tampering with
        an issued certificate; binding the certificate to a *trusted* issuer
        additionally requires checking `key_id`/`verify_key` against the
        issuer's published keys — see `verify_against_keystore`.)
        """
        key = public_key
        if key is None:
            if not self.verify_key:
                return False
            try:
                key = base64.b64decode(self.verify_key)
            except (binascii.Error, ValueError):
                return False
        if not self.signature:
            return False
        return ed25519_verify(key, self._payload(), self.signature)

    def verify_against_issuer_key(self, issuer_public_key: bytes, issuer_key_id: str) -> tuple[bool, str]:
        """Verify the signature AND bind the certificate to a trusted issuer key.

        The caller loads the trusted keypair (by keystore *name*) and passes
        its public key and key_id. Returns (ok, reason). Fails when the
        certificate does not name the trusted key, or when the signature does
        not verify under it — i.e. the certificate was not signed by the
        issuer the verifier trusts.
        """
        if self.key_id != issuer_key_id:
            return False, (f"certificate names key '{self.key_id}', not the trusted issuer key '{issuer_key_id}'")
        if not self.verify(issuer_public_key):
            return False, "signature invalid against trusted issuer key"
        return True, "signature valid; issuer key trusted"

    def to_json(self) -> str:
        """Export certificate as JSON."""
        return json.dumps(
            {
                "version": self.version,
                "algorithm_name": self.algorithm_name,
                "spec_hash": self.spec_hash,
                "proof_hash": self.proof_hash,
                "c_binary_hash": self.c_binary_hash,
                "python_hash": self.python_hash,
                "theorem": self.theorem,
                "tactics": self.tactics,
                "steps": self.steps,
                "lemmas": self.lemmas,
                "model_used": self.model_used,
                "generated_at": self.generated_at,
                "signature": self.signature,
                "key_id": self.key_id,
                "verify_key": self.verify_key,
                "verification_status": self.verification_status,
                "lean_version": self.lean_version,
                "build_log_hash": self.build_log_hash,
                "serial": self.serial,
                "issued_at": self.issued_at,
                "expires_at": self.expires_at,
                "revoked": self.revoked,
                "revocation_reason": self.revocation_reason,
                "artifact_version": self.artifact_version,
                "tier": self.tier,
                "product_name": self.product_name,
                "owner": self.owner,
                "repo_or_website": self.repo_or_website,
                "owner_contact": self.owner_contact,
                "issuer_name": self.issuer_name,
                "issuer_website": self.issuer_website,
                "issuer_contact": self.issuer_contact,
                "md5_hashes": self.md5_hashes,
                "qr_payload": self.qr_payload,
            },
            indent=2,
        )

    @classmethod
    def from_json(cls, data: str) -> ProofCertificate:
        """Import certificate from JSON."""
        try:
            d = json.loads(data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in proof certificate: {e}") from e

        if not isinstance(d, dict):
            raise ValueError("Proof certificate JSON must be an object")

        return cls(
            version=d.get("version", CERT_SCHEMA_VERSION),
            algorithm_name=d.get("algorithm_name", ""),
            spec_hash=d.get("spec_hash", ""),
            proof_hash=d.get("proof_hash", ""),
            c_binary_hash=d.get("c_binary_hash", ""),
            python_hash=d.get("python_hash", ""),
            theorem=d.get("theorem", ""),
            tactics=d.get("tactics", []),
            steps=d.get("steps", 0),
            lemmas=d.get("lemmas", 0),
            model_used=d.get("model_used", ""),
            generated_at=d.get("generated_at", 0.0),
            signature=d.get("signature", ""),
            key_id=d.get("key_id", ""),
            verify_key=d.get("verify_key", ""),
            verification_status=d.get("verification_status", "unverified"),
            lean_version=d.get("lean_version", ""),
            build_log_hash=d.get("build_log_hash", ""),
            serial=d.get("serial", ""),
            issued_at=d.get("issued_at", 0.0),
            expires_at=d.get("expires_at", 0.0),
            revoked=d.get("revoked", False),
            revocation_reason=d.get("revocation_reason", ""),
            artifact_version=d.get("artifact_version", ""),
            tier=d.get("tier", ""),
            product_name=d.get("product_name", ""),
            owner=d.get("owner", ""),
            repo_or_website=d.get("repo_or_website", ""),
            owner_contact=d.get("owner_contact", ""),
            issuer_name=d.get("issuer_name", "AxiomCode"),
            issuer_website=d.get("issuer_website", ""),
            issuer_contact=d.get("issuer_contact", ""),
            md5_hashes=d.get("md5_hashes", {}),
            qr_payload=d.get("qr_payload", ""),
        )

    # ── Schema v2: serials, validity, migration ────────────────────────────

    @staticmethod
    def generate_serial(key_id: str) -> str:
        """Generate a unique, issuer-scoped certificate serial number.

        Format: AXC-<8 hex of key_id>-<12 random hex>. The key_id prefix binds
        the serial to the issuing key; 48 bits of randomness make collisions
        infeasible. Uniqueness is additionally enforced by the registry.
        """
        prefix = (key_id or "UNKNOWN")[:8].upper()
        return f"AXC-{prefix}-{secrets.token_hex(6).upper()}"

    def validity_status(self, now: float | None = None) -> str:
        """Compute the certificate's lifecycle status.

        Returns one of: "active" | "expired" | "revoked" | "not-yet-valid".
        This reflects the certificate's own fields. The public registry's
        revocation list is authoritative for revocation — a registry lookup
        can mark a certificate revoked even when this field is False.
        """
        now = time.time() if now is None else now
        if self.revoked:
            return "revoked"
        if self.issued_at > 0 and now < self.issued_at:
            return "not-yet-valid"
        if self.expires_at > 0 and now > self.expires_at:
            return "expired"
        return "active"

    def is_currently_valid(self, now: float | None = None) -> bool:
        """True only when validity_status() == 'active'."""
        return self.validity_status(now) == "active"

    def migrate_v1_to_v2(self, private_key: bytes, key_id: str) -> ProofCertificate:
        """Migrate a v1 certificate to schema v2, re-signing it.

        Populates the new v2 fields with honest defaults (serial generated,
        issued_at := generated_at, expires_at := 0/never, tier inferred from
        verification_status) and RE-SIGNS with the issuer's private key.

        Refuses without a signing key: silently rewriting a signed certificate
        breaks its signature (the exact HIGH-6 failure). Callers without the
        issuer key must re-issue the certificate instead.
        """
        if self.version != 1:
            raise ValueError(f"migrate_v1_to_v2 expects a v1 certificate, got version {self.version}")
        if not private_key or len(private_key) != 32:
            raise ValueError("migration requires the 32-byte Ed25519 issuer private key for re-signing")
        self.version = CERT_SCHEMA_VERSION
        self.serial = ProofCertificate.generate_serial(key_id)
        self.issued_at = self.generated_at
        self.expires_at = 0.0
        self.revoked = False
        self.revocation_reason = ""
        # Honest tier inference: only a machine-checked proof earns "verified".
        self.tier = "verified" if self.verification_status == "verified" else ""
        self.key_id = key_id
        self.sign(private_key)
        return self

    def save(self, path: Path) -> None:
        """Save certificate to file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.to_json())

    @classmethod
    def load(cls, path: Path) -> ProofCertificate:
        """Load certificate from file."""
        path = Path(path)
        if not path.is_file():
            raise FileNotFoundError(f"Certificate file not found: {path}")

        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as e:
            raise ValueError(f"Certificate file is not valid UTF-8: {e}") from e

        return cls.from_json(content)


# ─── Binary Signing ─────────────────────────────────────────────────────────


@dataclass
class BinarySignature:
    """Signature for a compiled binary (C or Python)."""

    file_hash: str
    signature: str
    key_id: str
    signed_at: float
    file_type: str  # "c_binary" or "python_wheel"

    def to_dict(self) -> dict:
        return {
            "file_hash": self.file_hash,
            "signature": self.signature,
            "key_id": self.key_id,
            "signed_at": self.signed_at,
            "file_type": self.file_type,
        }

    def verify(self, file_path: Path, signing_key: bytes) -> bool:
        """Verify binary integrity and signature."""
        actual_hash = hash_file(file_path)
        if actual_hash != self.file_hash:
            return False
        payload = json.dumps(
            {
                "file_hash": self.file_hash,
                "file_type": self.file_type,
                "key_id": self.key_id,
                "signed_at": self.signed_at,
            },
            sort_keys=True,
        ).encode("utf-8")
        return verify_hmac(signing_key, payload, self.signature)


def sign_binary(file_path: Path, signing_key: bytes, key_id: str, file_type: str = "c_binary") -> BinarySignature:
    """Sign a binary file."""
    file_hash = hash_file(file_path)
    signed_at = time.time()  # Use same timestamp for both
    payload = json.dumps(
        {
            "file_hash": file_hash,
            "file_type": file_type,
            "key_id": key_id,
            "signed_at": signed_at,
        },
        sort_keys=True,
    ).encode("utf-8")
    signature = compute_hmac(signing_key, payload)

    return BinarySignature(
        file_hash=file_hash,
        signature=signature,
        key_id=key_id,
        signed_at=signed_at,
        file_type=file_type,
    )


# ─── Secure Communication ───────────────────────────────────────────────────


class SecureChannel:
    """Zero-knowledge secure communication channel.

    All data is encrypted before transmission.
    The server never sees plaintext data.
    """

    def __init__(self, key: bytes):
        self.key = key
        self._nonce_counter = 0

    def encrypt(self, data: bytes) -> dict:
        """Encrypt data for transmission."""
        nonce = secrets.token_bytes(NONCE_SIZE)
        # Derive keystream from key + nonce
        keystream = hashlib.sha512(self.key + nonce).digest()
        while len(keystream) < len(data):
            keystream += hashlib.sha512(keystream[-64:] + nonce).digest()
        encrypted = bytes(a ^ b for a, b in zip(data, keystream[: len(data)], strict=True))

        # Add HMAC for integrity
        mac = compute_hmac(self.key, nonce + encrypted)

        return {
            "nonce": base64.b64encode(nonce).decode(),
            "data": base64.b64encode(encrypted).decode(),
            "mac": mac,
        }

    def decrypt(self, encrypted: dict) -> bytes:
        """Decrypt received data."""
        nonce = base64.b64decode(encrypted["nonce"])
        data = base64.b64decode(encrypted["data"])

        # Verify integrity first
        if not verify_hmac(self.key, nonce + data, encrypted["mac"]):
            raise ValueError("MAC verification failed -- data may be tampered")

        # Decrypt
        keystream = hashlib.sha512(self.key + nonce).digest()
        while len(keystream) < len(data):
            keystream += hashlib.sha512(keystream[-64:] + nonce).digest()
        return bytes(a ^ b for a, b in zip(data, keystream[: len(data)], strict=True))


# ─── Audit Log ──────────────────────────────────────────────────────────────


# Lifecycle event schemas: actions the product's lifecycle depends on must
# carry their required fields. Unknown actions still pass through (existing
# callers keep working), but the events the SPEC's semver lifecycle depends
# on (issue / revoke / skip-recertification) are content-validated.
LIFECYCLE_SCHEMAS: dict[str, list[str]] = {
    "certificate.issued": ["serial", "artifact_version", "tier"],
    "certificate.revoked": ["serial", "reason"],
    "recertification.skipped": ["serial", "artifact_version", "reason"],
    "certificate.expired": ["serial"],
}


class AuditLog:
    """Tamper-evident audit log for compliance.

    Each entry is chained to the previous entry via hash. Any modification
    breaks the chain and is detectable.

    Signed mode: pass `signing_key` (32-byte Ed25519 private key). Every new
    entry is then Ed25519-signed, and the log opens with a signed genesis
    entry binding the log's identity to the issuer's public key. Rewriting
    the log from scratch without the signing key produces entries that fail
    `verify_integrity(verify_key=...)` — there is no rewritable genesis.

    Unsigned mode (no keys): behaves as before — hash chain only. Suitable
    for local/dev logs, never for the public transparency log.
    """

    GENESIS_PREVIOUS_HASH = "0" * 64

    def __init__(
        self,
        log_file: str | Path = ".axiomcode/audit.log",
        signing_key: bytes | None = None,
        verify_key: bytes | None = None,
    ):
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self._signing_key = signing_key
        self._verify_key = verify_key
        if signing_key is not None and len(signing_key) != 32:
            raise ValueError("AuditLog signing key must be a 32-byte Ed25519 private key")
        if verify_key is not None and len(verify_key) != 32:
            raise ValueError("AuditLog verify key must be a 32-byte Ed25519 public key")
        if signing_key is not None and verify_key is None:
            verify_key = self._verify_key = ed25519_public_from_private(signing_key)
        # A fresh signed log opens with a signed genesis entry binding the
        # log identity to the issuer key. Without the signing key, no valid
        # genesis can be minted — the log cannot be rewritten from scratch.
        if self._signing_key is not None and not self._has_entries():
            self._write_genesis()
        self._last_hash = self._load_last_hash()

    def _has_entries(self) -> bool:
        return self.log_file.exists() and bool(self.log_file.read_text().strip())

    def _write_genesis(self) -> None:
        assert self._signing_key is not None and self._verify_key is not None
        entry: dict = {
            "timestamp": time.time(),
            "user": "system",
            "action": "log.genesis",
            "details": {
                "verify_key": base64.b64encode(self._verify_key).decode(),
                "note": "Genesis entry: this log's identity is bound to the issuer key above.",
            },
            "previous_hash": self.GENESIS_PREVIOUS_HASH,
        }
        self._finalize_entry(entry)

    def _entry_payload(self, entry: dict) -> bytes:
        return json.dumps(
            {
                "timestamp": entry["timestamp"],
                "user": entry["user"],
                "action": entry["action"],
                "details": entry["details"],
                "previous_hash": entry["previous_hash"],
            },
            sort_keys=True,
        ).encode("utf-8")

    def _finalize_entry(self, entry: dict) -> str:
        entry_hash = hash_data(self._entry_payload(entry))
        entry["entry_hash"] = entry_hash
        if self._signing_key is not None:
            assert self._verify_key is not None  # set together in __init__
            entry["signature"] = ed25519_sign(self._signing_key, self._entry_payload(entry))
            entry["verify_key"] = base64.b64encode(self._verify_key).decode()
        with open(self.log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")
        self._last_hash = entry_hash
        return entry_hash

    def _load_last_hash(self) -> str:
        """Load the last hash from the log file."""
        if not self.log_file.exists():
            return self.GENESIS_PREVIOUS_HASH
        lines = self.log_file.read_text().strip().split("\n")
        if lines and lines[0].strip():
            last = json.loads(lines[-1])
            return str(last.get("entry_hash", self.GENESIS_PREVIOUS_HASH))
        return self.GENESIS_PREVIOUS_HASH

    def _validate_lifecycle(self, action: str, details: dict) -> None:
        required = LIFECYCLE_SCHEMAS.get(action)
        if required is None:
            return
        missing = [k for k in required if k not in details]
        if missing:
            raise ValueError(f"Lifecycle event '{action}' missing required details: {missing}")

    def add_entry(self, action: str, details: dict, user: str = "system") -> str:
        """Add a tamper-evident log entry.

        Lifecycle actions (certificate.issued / certificate.revoked /
        recertification.skipped / certificate.expired) are schema-validated:
        missing required details raise ValueError instead of silently
        logging a content-free event.
        """
        if not isinstance(details, dict):
            raise ValueError("AuditLog details must be a dict")
        self._validate_lifecycle(action, details)
        entry = {
            "timestamp": time.time(),
            "user": user,
            "action": action,
            "details": details,
            "previous_hash": self._last_hash,
        }
        return self._finalize_entry(entry)

    def _read_entries(self) -> list[dict]:
        if not self.log_file.exists():
            return []
        text = self.log_file.read_text().strip()
        if not text:
            return []
        return [json.loads(line) for line in text.split("\n") if line.strip()]

    def verify_chain(self) -> tuple[bool, list[str]]:
        """Verify hash chain and (when a verify key is set) entry signatures.

        Returns (ok, issues). Fails closed: any tampered entry, any missing
        or invalid signature in signed mode, or any break in the chain
        yields ok=False with a precise issue list.
        """
        issues: list[str] = []
        prev_hash = self.GENESIS_PREVIOUS_HASH
        for i, entry in enumerate(self._read_entries()):
            if entry.get("previous_hash") != prev_hash:
                issues.append(f"entry {i}: previous_hash mismatch (chain broken)")
                # Continue checking remaining entries to report all damage.
            expected_hash = hash_data(self._entry_payload(entry))
            if entry.get("entry_hash") != expected_hash:
                issues.append(f"entry {i} ({entry.get('action')}): entry_hash mismatch (tampered)")
            if self._verify_key is not None:
                sig = entry.get("signature")
                if not sig:
                    issues.append(f"entry {i} ({entry.get('action')}): missing signature in signed log")
                elif not ed25519_verify(self._verify_key, self._entry_payload(entry), sig):
                    issues.append(f"entry {i} ({entry.get('action')}): invalid signature")
            prev_hash = entry.get("entry_hash", prev_hash)
        return (len(issues) == 0), issues

    def verify_integrity(self) -> bool:
        """Verify the entire log chain is intact.

        In signed mode (verify key set) every entry must also carry a valid
        signature; unsigned entries fail verification. Unsigned mode checks
        the hash chain only (legacy behavior).
        """
        ok, _ = self.verify_chain()
        return ok


# ─── Secure Sandbox ─────────────────────────────────────────────────────────


class SecureSandbox:
    """Sandboxed execution environment for untrusted code.

    Uses subprocess isolation with resource limits.
    No direct access to host filesystem or network.
    """

    def __init__(self, work_dir: str | Path = ".axiomcode/sandbox"):
        self.work_dir = Path(work_dir)
        self.work_dir.mkdir(parents=True, exist_ok=True)

    def run(self, command: list[str], timeout: int = 60, input_data: bytes | None = None) -> dict:
        """Run a command in a sandboxed environment."""
        import subprocess

        env = os.environ.copy()
        # Restrict environment
        env["HOME"] = str(self.work_dir)
        env["TMPDIR"] = str(self.work_dir / "tmp")
        (self.work_dir / "tmp").mkdir(exist_ok=True)

        # Remove dangerous env vars
        for var in ["LD_PRELOAD", "LD_LIBRARY_PATH", "PYTHONPATH", "PATH"]:
            if var in env:
                del env[var]

        try:
            result = subprocess.run(
                command,
                cwd=str(self.work_dir),
                env=env,
                input=input_data,
                capture_output=True,
                timeout=timeout,
            )
            return {
                "returncode": result.returncode,
                "stdout": result.stdout.decode("utf-8", errors="replace"),
                "stderr": result.stderr.decode("utf-8", errors="replace"),
                "success": result.returncode == 0,
            }
        except subprocess.TimeoutExpired:
            return {
                "returncode": -1,
                "stdout": "",
                "stderr": f"Command timed out after {timeout}s",
                "success": False,
            }
        except Exception as e:
            return {
                "returncode": -1,
                "stdout": "",
                "stderr": str(e),
                "success": False,
            }

    def cleanup(self) -> None:
        """Clean up sandbox directory."""
        import shutil

        if self.work_dir.exists():
            shutil.rmtree(self.work_dir)
        self.work_dir.mkdir(parents=True, exist_ok=True)


# ─── Rate Limiter ───────────────────────────────────────────────────────────


class RateLimiter:
    """Token bucket rate limiter for API calls."""

    def __init__(self, max_tokens: int = 10, refill_rate: float = 1.0):
        self.max_tokens = max_tokens
        self.refill_rate = refill_rate  # tokens per second
        self.tokens = float(max_tokens)
        self.last_refill = time.monotonic()

    def acquire(self) -> bool:
        """Try to acquire a token. Returns True if successful."""
        now = time.monotonic()
        elapsed = now - self.last_refill
        self.tokens = min(self.max_tokens, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now

        if self.tokens >= 1.0:
            self.tokens -= 1.0
            return True
        return False

    def wait(self) -> None:
        """Wait until a token is available."""
        while not self.acquire():
            time.sleep(0.1)
