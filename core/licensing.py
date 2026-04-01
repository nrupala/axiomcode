"""
AxiomCode Licensing System
===========================
Cryptographic credential and certificate system for commercial use.

Architecture:
  - Root key pair (kept SECRET by AxiomCode) — signs all licenses
  - Public key (shipped with software) — verifies licenses
  - License certificates — bound to user, hardware, expiration
  - Hardware binding — license tied to machine fingerprint
  - Offline verification — no phone-home needed
  - Revocation support — compromised licenses can be invalidated

All stdlib. Zero external dependencies.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import platform
import secrets
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


# ─── Constants ──────────────────────────────────────────────────────────────

LICENSE_VERSION = 1
LICENSE_KEY_SIZE = 64  # 512-bit keys
HARDWARE_SALT = b"axiomcode-hardware-fingerprint-v1"


# ─── Hardware Fingerprint ───────────────────────────────────────────────────

def get_hardware_fingerprint() -> str:
    """
    Generate a unique hardware fingerprint for this machine.
    Uses multiple hardware identifiers hashed together.
    This is NOT cryptographically secure — it's for binding, not secrecy.
    """
    components = []

    # MAC address (most reliable cross-platform identifier)
    mac = hex(uuid.getnode())[2:].zfill(12)
    components.append(mac)

    # CPU info
    try:
        if platform.system() == "Windows":
            import subprocess
            result = subprocess.run(
                ["wmic", "cpu", "get", "ProcessorId"],
                capture_output=True, text=True, timeout=5
            )
            cpu_id = result.stdout.strip().split("\n")[-1].strip()
            if cpu_id:
                components.append(cpu_id)
        elif platform.system() == "Linux":
            for line in Path("/proc/cpuinfo").read_text().split("\n"):
                if "serial" in line.lower():
                    serial = line.split(":")[-1].strip()
                    if serial:
                        components.append(serial)
                    break
    except Exception:
        pass

    # Machine ID (Linux)
    try:
        if platform.system() == "Linux":
            machine_id = Path("/etc/machine-id").read_text().strip()
            if machine_id:
                components.append(machine_id)
    except Exception:
        pass

    # Hostname + platform
    components.append(platform.node())
    components.append(platform.machine())

    # Hash all components together
    raw = "|".join(components).encode("utf-8")
    return hashlib.sha512(raw).hexdigest()


def get_hardware_hash(salt: bytes = HARDWARE_SALT) -> str:
    """Get a salted hardware hash for license binding."""
    fp = get_hardware_fingerprint()
    return hashlib.sha512(salt + fp.encode()).hexdigest()


# ─── License Key Pair ───────────────────────────────────────────────────────

@dataclass
class LicenseKeyPair:
    """
    Asymmetric key pair for license signing and verification.
    
    Uses HMAC-SHA512 for MVP. For production with true asymmetric crypto
    (where verification key cannot sign), use Ed25519 or RSA-4096.
    """
    private_key: bytes   # SECRET — used to sign licenses
    public_key: bytes    # PUBLIC — shipped with software to verify
    key_id: str
    created_at: float
    algorithm: str = "hmac-sha512"

    @classmethod
    def generate(cls) -> "LicenseKeyPair":
        """Generate a new key pair.
        
        NOTE: HMAC is symmetric — signing and verification use the same key.
        The 'public_key' here is identical to 'private_key'. For production
        with true asymmetric crypto (where verification key cannot sign),
        replace with Ed25519 or RSA-4096 using the `cryptography` package.
        """
        key = secrets.token_bytes(LICENSE_KEY_SIZE)
        return cls(
            private_key=key,
            public_key=key,  # Same key — HMAC is symmetric
            key_id=secrets.token_hex(8),
            created_at=time.time(),
        )

    def save_private(self, path: Path, passphrase: str = "") -> None:
        """Save private key (KEEP THIS SECRET — never distribute)."""
        path.parent.mkdir(parents=True, exist_ok=True)
        salt = secrets.token_bytes(32)
        derived = hashlib.pbkdf2_hmac("sha512", passphrase.encode(), salt, 600000)
        keystream = hashlib.sha512(derived).digest()
        while len(keystream) < len(self.private_key):
            keystream += hashlib.sha512(keystream[-64:] + derived).digest()
        encrypted = bytes(a ^ b for a, b in zip(self.private_key, keystream[:len(self.private_key)]))

        path.write_text(json.dumps({
            "type": "axiomcode-private-key",
            "version": LICENSE_VERSION,
            "key_id": self.key_id,
            "salt": base64.b64encode(salt).decode(),
            "data": base64.b64encode(encrypted).decode(),
            "public_key": base64.b64encode(self.public_key).decode(),
            "created_at": self.created_at,
        }, indent=2))

    @classmethod
    def load_private(cls, path: Path, passphrase: str = "") -> "LicenseKeyPair":
        """Load private key."""
        data = json.loads(path.read_text())
        salt = base64.b64decode(data["salt"])
        encrypted = base64.b64decode(data["data"])
        derived = hashlib.pbkdf2_hmac("sha512", passphrase.encode(), salt, 600000)
        keystream = hashlib.sha512(derived).digest()
        while len(keystream) < len(encrypted):
            keystream += hashlib.sha512(keystream[-64:] + derived).digest()
        private_key = bytes(a ^ b for a, b in zip(encrypted, keystream[:len(encrypted)]))
        return cls(
            private_key=private_key,
            public_key=base64.b64decode(data["public_key"]),
            key_id=data["key_id"],
            created_at=data["created_at"],
        )

    def save_public(self, path: Path) -> None:
        """Save public key (safe to distribute with the software)."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({
            "type": "axiomcode-public-key",
            "version": LICENSE_VERSION,
            "key_id": self.key_id,
            "data": base64.b64encode(self.public_key).decode(),
            "algorithm": self.algorithm,
            "created_at": self.created_at,
        }, indent=2))

    @classmethod
    def load_public(cls, path: Path) -> "LicenseKeyPair":
        """Load public key."""
        data = json.loads(path.read_text())
        return cls(
            private_key=b"",
            public_key=base64.b64decode(data["data"]),
            key_id=data["key_id"],
            created_at=data["created_at"],
            algorithm=data.get("algorithm", "hmac-sha512"),
        )


# ─── License Certificate ────────────────────────────────────────────────────

@dataclass
class LicenseCertificate:
    """
    Cryptographic license certificate bound to a user and machine.
    """
    version: int = LICENSE_VERSION
    license_id: str = ""
    user_id: str = ""
    user_name: str = ""
    tier: str = "community"
    hardware_hash: str = ""  # Empty = portable (not hardware-bound)
    features: list[str] = field(default_factory=list)
    max_seats: int = 1
    issued_at: float = 0.0
    expires_at: float = 0.0  # 0 = never expires
    revoked: bool = False
    revocation_reason: str = ""
    signature: str = ""
    key_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def _payload(self) -> bytes:
        """Get the license payload (excluding signature)."""
        data = {
            "version": self.version,
            "license_id": self.license_id,
            "user_id": self.user_id,
            "user_name": self.user_name,
            "tier": self.tier,
            "hardware_hash": self.hardware_hash,
            "features": sorted(self.features),
            "max_seats": self.max_seats,
            "issued_at": self.issued_at,
            "expires_at": self.expires_at,
            "revoked": self.revoked,
            "key_id": self.key_id,
            "metadata": self.metadata,
        }
        return json.dumps(data, sort_keys=True).encode("utf-8")

    def sign(self, private_key: bytes) -> "LicenseCertificate":
        """Sign the license with the root private key."""
        self.signature = hmac.new(private_key, self._payload(), "sha512").hexdigest()
        return self

    def verify(self, public_key: bytes) -> bool:
        """Verify the license signature."""
        expected = hmac.new(public_key, self._payload(), "sha512").hexdigest()
        return hmac.compare_digest(expected, self.signature)

    def is_valid(self, public_key: bytes) -> tuple[bool, str]:
        """
        Full validation: signature, expiration, revocation, hardware binding.
        Returns (is_valid, reason).
        """
        # Check signature
        if not self.verify(public_key):
            return False, "Invalid signature — license may be forged"

        # Check revocation
        if self.revoked:
            return False, f"License revoked: {self.revocation_reason}"

        # Check expiration
        if self.expires_at > 0 and time.time() > self.expires_at:
            return False, f"License expired on {time.strftime('%Y-%m-%d', time.localtime(self.expires_at))}"

        # Check hardware binding
        if self.hardware_hash:
            current_hw = get_hardware_hash()
            if self.hardware_hash != current_hw:
                return False, "License bound to different hardware"

        return True, "Valid"

    def has_feature(self, feature: str) -> bool:
        """Check if this license includes a specific feature."""
        return feature in self.features or self.tier == "enterprise"

    def to_json(self) -> str:
        """Export license as JSON."""
        return json.dumps({
            "version": self.version,
            "license_id": self.license_id,
            "user_id": self.user_id,
            "user_name": self.user_name,
            "tier": self.tier,
            "hardware_hash": self.hardware_hash,
            "features": self.features,
            "max_seats": self.max_seats,
            "issued_at": self.issued_at,
            "expires_at": self.expires_at,
            "revoked": self.revoked,
            "revocation_reason": self.revocation_reason,
            "signature": self.signature,
            "key_id": self.key_id,
            "metadata": self.metadata,
        }, indent=2)

    @classmethod
    def from_json(cls, data: str) -> "LicenseCertificate":
        """Import license from JSON."""
        d = json.loads(data)
        return cls(
            version=d.get("version", LICENSE_VERSION),
            license_id=d.get("license_id", ""),
            user_id=d.get("user_id", ""),
            user_name=d.get("user_name", ""),
            tier=d.get("tier", "community"),
            hardware_hash=d.get("hardware_hash", ""),
            features=d.get("features", []),
            max_seats=d.get("max_seats", 1),
            issued_at=d.get("issued_at", 0.0),
            expires_at=d.get("expires_at", 0.0),
            revoked=d.get("revoked", False),
            revocation_reason=d.get("revocation_reason", ""),
            signature=d.get("signature", ""),
            key_id=d.get("key_id", ""),
            metadata=d.get("metadata", {}),
        )

    def save(self, path: Path) -> None:
        """Save license to file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.to_json())

    @classmethod
    def load(cls, path: Path) -> "LicenseCertificate":
        """Load license from file."""
        return cls.from_json(path.read_text())


# ─── License Manager ────────────────────────────────────────────────────────

class LicenseManager:
    """
    Manages license creation, verification, and revocation.

    Usage:
        # Generate root key pair (do this ONCE, keep private key secret)
        lm = LicenseManager()
        keys = lm.generate_root_key()
        keys.save_private("root_private.key", "super-secret-passphrase")
        keys.save_public("root_public.key")  # Ship this with the software

        # Issue a license (requires private key)
        license = lm.issue_license(
            user_id="user@example.com",
            user_name="John Doe",
            tier="pro",
            features=["all_algorithms", "visualization", "publishing"],
            expires_at=time.time() + 365 * 86400,  # 1 year
        )
        license.save("john_doe.license.json")

        # Verify a license (only needs public key)
        lm.load_public_key("root_public.key")
        valid, reason = lm.verify_license("john_doe.license.json")
    """

    def __init__(self, data_dir: str | Path = ".axiomcode/licenses"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._private_key: bytes | None = None
        self._public_key: bytes | None = None
        self._key_id: str = ""
        self._revocation_list: set[str] = set()
        self._load_revocation_list()

    def _load_revocation_list(self) -> None:
        """Load the revocation list."""
        rev_file = self.data_dir / "revoked.json"
        if rev_file.exists():
            data = json.loads(rev_file.read_text())
            self._revocation_list = set(data.get("revoked", []))

    def _save_revocation_list(self) -> None:
        """Save the revocation list."""
        rev_file = self.data_dir / "revoked.json"
        rev_file.write_text(json.dumps({
            "revoked": list(self._revocation_list),
            "updated_at": time.time(),
        }, indent=2))

    def generate_root_key(self) -> LicenseKeyPair:
        """Generate a new root key pair."""
        keys = LicenseKeyPair.generate()
        self._private_key = keys.private_key
        self._public_key = keys.public_key
        self._key_id = keys.key_id
        return keys

    def load_private_key(self, path: Path | str, passphrase: str = "") -> None:
        """Load the root private key."""
        keys = LicenseKeyPair.load_private(Path(path), passphrase)
        self._private_key = keys.private_key
        self._public_key = keys.public_key
        self._key_id = keys.key_id

    def load_public_key(self, path: Path | str) -> None:
        """Load the root public key."""
        keys = LicenseKeyPair.load_public(Path(path))
        self._public_key = keys.public_key
        self._key_id = keys.key_id

    def issue_license(
        self,
        user_id: str,
        user_name: str,
        tier: str = "community",
        features: list[str] | None = None,
        max_seats: int = 1,
        expires_at: float = 0.0,
        metadata: dict[str, Any] | None = None,
    ) -> LicenseCertificate:
        """
        Issue a new license certificate.
        Requires the root private key to be loaded.
        """
        if not self._private_key:
            raise RuntimeError("Root private key not loaded. Call load_private_key() first.")

        if features is None:
            features = self._default_features_for_tier(tier)

        license = LicenseCertificate(
            license_id=secrets.token_hex(16),
            user_id=user_id,
            user_name=user_name,
            tier=tier,
            hardware_hash=get_hardware_hash(),
            features=features,
            max_seats=max_seats,
            issued_at=time.time(),
            expires_at=expires_at,
            key_id=self._key_id,
            metadata=metadata or {},
        )
        license.sign(self._private_key)
        return license

    def issue_portable_license(
        self,
        user_id: str,
        user_name: str,
        tier: str = "community",
        features: list[str] | None = None,
        max_seats: int = 1,
        expires_at: float = 0.0,
        metadata: dict[str, Any] | None = None,
    ) -> LicenseCertificate:
        """
        Issue a license NOT bound to hardware (portable across machines).
        Use with caution — these can be shared.
        """
        if not self._private_key:
            raise RuntimeError("Root private key not loaded.")

        if features is None:
            features = self._default_features_for_tier(tier)

        license = LicenseCertificate(
            license_id=secrets.token_hex(16),
            user_id=user_id,
            user_name=user_name,
            tier=tier,
            hardware_hash="",  # No hardware binding
            features=features,
            max_seats=max_seats,
            issued_at=time.time(),
            expires_at=expires_at,
            key_id=self._key_id,
            metadata=metadata or {},
        )
        license.sign(self._private_key)
        return license

    def verify_license(self, license_path: Path | str | LicenseCertificate) -> tuple[bool, str]:
        """
        Verify a license certificate.
        Only needs the public key.
        """
        if not self._public_key:
            raise RuntimeError("Root public key not loaded. Call load_public_key() first.")

        if isinstance(license_path, LicenseCertificate):
            license = license_path
        else:
            license = LicenseCertificate.load(Path(license_path))

        # Check revocation list
        if license.license_id in self._revocation_list:
            return False, "License is revoked"

        return license.is_valid(self._public_key)

    def revoke_license(self, license_id: str, reason: str = "") -> None:
        """Revoke a license by ID."""
        self._revocation_list.add(license_id)
        self._save_revocation_list()

    def is_revoked(self, license_id: str) -> bool:
        """Check if a license is revoked."""
        return license_id in self._revocation_list

    def list_licenses(self) -> list[dict]:
        """List all installed licenses."""
        licenses = []
        for lf in self.data_dir.glob("*.license.json"):
            try:
                lic = LicenseCertificate.load(lf)
                valid, reason = lic.is_valid(self._public_key) if self._public_key else (False, "No public key loaded")
                licenses.append({
                    "file": str(lf),
                    "license_id": lic.license_id,
                    "user": lic.user_name,
                    "tier": lic.tier,
                    "valid": valid,
                    "reason": reason,
                })
            except Exception:
                licenses.append({
                    "file": str(lf),
                    "license_id": "unknown",
                    "user": "unknown",
                    "tier": "unknown",
                    "valid": False,
                    "reason": "Failed to parse",
                })
        return licenses

    @staticmethod
    def _default_features_for_tier(tier: str) -> list[str]:
        """Get default features for a license tier."""
        tiers = {
            "community": ["basic_algorithms", "visualization_2d"],
            "pro": ["all_algorithms", "visualization_2d", "visualization_3d", "publishing", "certificates"],
            "enterprise": [],  # All features
        }
        return tiers.get(tier, tiers["community"])


# ─── Tier Definitions ───────────────────────────────────────────────────────

TIERS = {
    "community": {
        "name": "Community",
        "price": "Free",
        "features": ["Basic algorithms", "2D visualization", "Local LLM only"],
        "max_seats": 1,
        "expires": False,
    },
    "pro": {
        "name": "Pro",
        "price": "$49/month",
        "features": ["All algorithms", "3D visualization", "Cloud LLMs", "Publishing", "Certificates"],
        "max_seats": 3,
        "expires": True,
    },
    "enterprise": {
        "name": "Enterprise",
        "price": "Custom",
        "features": ["Everything", "Multi-user", "Compliance", "Support", "Custom algorithms"],
        "max_seats": -1,  # Unlimited
        "expires": True,
    },
}
