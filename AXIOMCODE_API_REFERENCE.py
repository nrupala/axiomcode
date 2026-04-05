"""
AxiomCode API Reference — Python Style Learning Guide

This document serves as a Python-style help guide showing how to use
AxiomCode programmatically. Use this like Python's help() or pydoc.

Usage:
    python -c "from axiomcode_api_reference import *"
    help(KeyStore)
    help(ProofCertificate)
    help(DataStore)
"""

from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from pathlib import Path
import time


# ═══════════════════════════════════════════════════════════════════════════
# MODULE: core.security
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class KeyPair:
    """
    Cryptographic key pair for signing and encryption.
    
    A KeyPair contains both an encryption key and a signing key,
    allowing full zero-trust cryptographic operations.
    
    Attributes:
        encryption_key (bytes): 512-bit key for data encryption
        signing_key (bytes): 512-bit key for signing operations
        key_id (str): Unique identifier for this key pair
        created_at (float): Unix timestamp of creation
    
    Example:
        >>> from core.security import KeyPair
        >>> key = KeyPair.generate()
        >>> print(key.key_id)
        'a1b2c3d4e5f6g7h8'
        
        >>> # Serialize to JSON
        >>> data = key.to_dict()
        >>> loaded = KeyPair.from_dict(data)
        >>> assert loaded.key_id == key.key_id
    
    Methods:
        generate() -> KeyPair
            Create a new secure random key pair
        to_dict() -> dict
            Serialize to JSON-compatible dictionary
        from_dict(data: dict) -> KeyPair
            Deserialize from dictionary
    """
    
    encryption_key: bytes
    signing_key: bytes
    key_id: str
    created_at: float
    
    @classmethod
    def generate(cls) -> 'KeyPair':
        """Generate a cryptographically secure key pair."""
        pass
    
    def to_dict(self) -> dict:
        """Convert to JSON-serializable dictionary."""
        pass
    
    @classmethod
    def from_dict(cls, data: dict) -> 'KeyPair':
        """Restore from dictionary."""
        pass


class KeyStore:
    """
    Encrypted key storage with zero-knowledge design.
    
    Keys are encrypted with PBKDF2-derived master keys. Even if someone
    steals the key files, they cannot decrypt without the passphrase.
    
    The passphrase is ALWAYS validated on load — no caching bypass.
    
    Attributes:
        store_dir (Path): Directory where encrypted keys are stored
    
    Example:
        >>> from core.security import KeyStore
        >>> ks = KeyStore(".axiomcode/keys")
        >>> 
        >>> # Create a new key (encrypted at rest)
        >>> key = ks.create_key("my_key", "my_secure_passphrase")
        >>> print(key.key_id)
        >>> 
        >>> # Load the key (validates passphrase)
        >>> loaded = ks.load_key("my_key", "my_secure_passphrase")
        >>> 
        >>> # Wrong passphrase fails
        >>> try:
        ...     ks.load_key("my_key", "wrong_password")
        ... except ValueError:
        ...     print("Passphrase validation working!")
        >>> 
        >>> # Delete (overwrites then deletes)
        >>> ks.delete_key("my_key")
    
    Security Properties:
        - PBKDF2 with 600k iterations (OWASP 2024 compliant)
        - SHA-512 hash algorithm
        - XOR encryption with derived keystream
        - Passphrase always validated (no cache bypass)
        - Key files overwritten before deletion
    
    Methods:
        create_key(name: str, passphrase: str) -> KeyPair
            Create new key pair encrypted with passphrase
        load_key(name: str, passphrase: str) -> KeyPair
            Load and decrypt key (always validates passphrase)
        delete_key(name: str) -> None
            Securely delete key pair from storage
    """
    
    def __init__(self, store_dir: str | Path = ".axiomcode/keys"):
        """Initialize key store at given directory."""
        pass
    
    def create_key(self, name: str, passphrase: str) -> KeyPair:
        """
        Create and store a new encrypted key pair.
        
        Args:
            name: Identifier for this key (e.g., "root", "user1")
            passphrase: Encryption passphrase (never stored, only key derived)
        
        Returns:
            KeyPair: Generated and saved key pair
        
        Raises:
            FileExistsError: If key with same name already exists
            ValueError: If passphrase is too weak (< 8 chars recommended)
        
        Example:
            >>> ks = KeyStore()
            >>> key = ks.create_key("root", "super_secure_passphrase_123")
        """
        pass
    
    def load_key(self, name: str, passphrase: str) -> KeyPair:
        """
        Load and decrypt a key pair.
        
        SECURITY: Validates passphrase on every load. Does NOT return
        cached keys without verification. Failed decryption raises ValueError.
        
        Args:
            name: Key identifier
            passphrase: Decryption passphrase
        
        Returns:
            KeyPair: Decrypted key pair
        
        Raises:
            FileNotFoundError: If key doesn't exist
            ValueError: If passphrase is incorrect or file corrupted
        
        Example:
            >>> ks = KeyStore()
            >>> key = ks.load_key("root", "super_secure_passphrase_123")
            >>> 
            >>> # Wrong passphrase raises error
            >>> try:
            ...     ks.load_key("root", "wrong_passphrase")
            ... except ValueError as e:
            ...     print(f"Security: {e}")
        """
        pass
    
    def delete_key(self, name: str) -> None:
        """
        Securely delete a key pair.
        
        Overwrites key file with random data before deletion.
        This prevents key recovery via forensic disk analysis.
        
        Args:
            name: Key identifier to delete
        
        Raises:
            FileNotFoundError: If key doesn't exist
        
        Example:
            >>> ks = KeyStore()
            >>> ks.delete_key("obsolete_key")  # Securely wiped
        """
        pass


class ProofCertificate:
    """
    Cryptographic certificate attesting to algorithm correctness.
    
    This is the heart of AxiomCode's zero-trust model. Every generated
    algorithm comes with a signed certificate proving it was formally
    verified by Lean 4.
    
    Certificate contains:
        - Hashes of spec, proof, compile binary, Python package
        - Formal theorem statement
        - Proof tactics used
        - Model used for generation
        - HMAC-SHA512 signature
    
    Anyone can verify the certificate without trusting AxiomCode:
        1. Recompute hash of binary
        2. Compare with certificate.c_binary_hash
        3. Verify HMAC signature with public key
    
    Example:
        >>> from core.security import ProofCertificate, KeyStore
        >>> 
        >>> # Load certificate
        >>> cert = ProofCertificate.load("binary_search.cert")
        >>> print(cert.algorithm_name)
        'binary_search'
        >>> print(cert.steps)
        42  # Proof had 42 steps
        >>> 
        >>> # Verify the signature
        >>> ks = KeyStore()
        >>> key = ks.load_key("root", "passphrase")
        >>> 
        >>> is_valid = cert.verify_signature(key.signing_key)
        >>> print(f"Signed by root: {is_valid}")
    
    Attributes:
        algorithm_name (str): Name of the algorithm
        spec_hash (str): SHA-512 of Lean 4 specification
        proof_hash (str): SHA-512 of proof term
        c_binary_hash (str): SHA-512 of compiled C .so/.dll
        python_hash (str): SHA-512 of Python wheel
        theorem (str): Mathematical theorem statement
        tactics (list): Lean tactics used in proof
        steps (int): Number of proof steps
        lemmas (int): Number of lemmas used
        model_used (str): LLM model that generated spec
        generated_at (float): Unix timestamp of generation
        signature (str): HMAC-SHA512 signature
        key_id (str): ID of signing key
    
    Methods:
        sign(signing_key) -> ProofCertificate
            Sign certificate with key
        verify_signature(key) -> bool
            Verify HMAC signature using constant-time comparison
        save(path) -> None
            Save to JSON file
        load(path) -> ProofCertificate
            Load from JSON file
    """
    
    def sign(self, signing_key: bytes) -> 'ProofCertificate':
        """
        Sign the certificate with HMAC-SHA512.
        
        Args:
            signing_key: Key bytes from KeyPair.signing_key
        
        Returns:
            Self (for chaining)
        
        Example:
            >>> cert = ProofCertificate(algorithm_name="binary_search", ...)
            >>> key = keystore.load_key("root", "passphrase")
            >>> cert_signed = cert.sign(key.signing_key)
        """
        pass
    
    def verify_signature(self, key: bytes) -> bool:
        """
        Verify HMAC signature using constant-time comparison.
        
        Constant-time ensures timing attacks cannot succeed.
        
        Args:
            key: Key bytes to verify with
        
        Returns:
            bool: True if signature is valid
        
        Example:
            >>> if cert.verify_signature(key.signing_key):
            ...     print("Certificate authentic!")
            ... else:
            ...     raise ValueError("Certificate tampered with!")
        """
        pass
    
    def save(self, path: str) -> None:
        """Save certificate to JSON file."""
        pass
    
    @classmethod
    def load(cls, path: str) -> 'ProofCertificate':
        """Load certificate from JSON file."""
        pass


class AuditLog:
    """
    Tamper-evident audit log with hash chaining.
    
    Inspired by blockchain technology, uses hash chaining to ensure
    that any modification is detectable.
    
    Each log entry contains:
        - Event type (proof_verified, certificate_signed, etc.)
        - Details (JSON blob)
        - Timestamp
        - Hash of previous entry (chaining)
    
    Verification:
        Call verify_integrity() to detect tampering.
        If ANY entry is modified, the chain breaks.
    
    Example:
        >>> from core.security import AuditLog
        >>> 
        >>> audit = AuditLog(".axiomcode/audit.log")
        >>> 
        >>> # Log an event
        >>> audit.log_event(
        ...     event_type="proof_verified",
        ...     details={"algorithm": "binary_search", "valid": True}
        ... )
        >>> 
        >>> # Verify chain hasn't been tampered
        >>> if audit.verify_integrity():
        ...     print("Audit log is trustworthy")
        ... else:
        ...     print("WARNING: Audit log was modified!")
        >>> 
        >>> # Read full log
        >>> events = audit.read_log()
        >>> for entry in events:
        ...     print(f"[{entry['timestamp']}] {entry['event_type']}")
    
    Methods:
        log_event(event_type, details) -> None
            Add event to chain
        read_log() -> list
            Read all log entries
        verify_integrity() -> bool
            Check if chain has been tampered with
    """
    
    def log_event(self, event_type: str, details: Dict[str, Any]) -> None:
        """
        Log an event to the chain.
        
        Args:
            event_type: Category (e.g., "proof_verified", "certificate_signed")
            details: JSON-serializable event data
        """
        pass
    
    def read_log(self) -> List[Dict[str, Any]]:
        """Read all log entries."""
        pass
    
    def verify_integrity(self) -> bool:
        """
        Verify the hash chain hasn't been tampered.
        
        Returns:
            bool: True if chain is intact, False if modified
        """
        pass


def hash_data(data: bytes) -> str:
    """
    Compute SHA-512 hash of bytes.
    
    Example:
        >>> from core.security import hash_data
        >>> hash_val = hash_data(b"hello")
        >>> print(hash_val)
        '9b71d224bd62f3785d96f46e3d795c75...'
    """
    pass


def hash_file(path: Path) -> str:
    """
    Compute SHA-512 hash of file efficiently.
    
    Reads file in chunks to avoid memory issues.
    
    Example:
        >>> from core.security import hash_file
        >>> from pathlib import Path
        >>> 
        >>> binary_hash = hash_file(Path("binary_search.so"))
        >>> # Compare with certificate
        >>> assert binary_hash == cert.c_binary_hash
    """
    pass


def compute_hmac(key: bytes, data: bytes) -> str:
    """
    Compute HMAC-SHA512 for authentication.
    
    Example:
        >>> from core.security import compute_hmac, KeyStore
        >>> 
        >>> key = keystore.load_key("root", "pass")
        >>> signature = compute_hmac(key.signing_key, message)
    """
    pass


def verify_hmac(key: bytes, data: bytes, expected: str) -> bool:
    """
    Verify HMAC using constant-time comparison.
    
    Example:
        >>> if verify_hmac(key, message, signature):
        ...     print("Message authenticated!")
    """
    pass


# ═══════════════════════════════════════════════════════════════════════════
# MODULE: core.persistence
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class DataRecord:
    """
    A single data record with metadata.
    
    Attributes:
        id (str): Record identifier
        schema_version (int): Data schema version
        created_at (float): Creation timestamp
        updated_at (float): Last update timestamp
        data (dict): The actual data
        metadata (dict): Optional metadata
    """
    pass


class DataStore:
    """
    Persistent JSON data store with schema versioning.
    
    Features:
        - JSON files automatically versioned
        - Full history retained (data never deleted)
        - Automatic migration support
        - Input validation (safe from injection)
        - File size limits (prevent DoS)
        - UTF-8 encoding validation
    
    Example:
        >>> from core.persistence import DataStore
        >>> 
        >>> store = DataStore(".axiomcode/data")
        >>> 
        >>> # Create a record
        >>> record = store.create(
        ...     record_id="binary_search_v1",
        ...     data={"name": "binary_search", "version": 1}
        ... )
        >>> 
        >>> # Update (old version preserved)
        >>> store.update("binary_search_v1", {"version": 2})
        >>> 
        >>> # Get current
        >>> current = store.get("binary_search_v1")
        >>> print(current.data["version"])
        2
        >>> 
        >>> # See all versions
        >>> history = store.get_history("binary_search_v1")
        >>> print(f"Updated {len(history)} times")
        >>> 
        >>> # Delete (data retained in history)
        >>> store.delete("binary_search_v1")
    
    Methods:
        create(record_id, data, metadata=None) -> DataRecord
        get(record_id) -> DataRecord | None
        update(record_id, data, metadata=None) -> DataRecord | None
        delete(record_id) -> None
        list() -> List[DataRecord]
        get_history(record_id) -> List[DataRecord]
    """
    
    def create(
        self,
        record_id: str,
        data: Dict[str, Any],
        metadata: Dict[str, Any] | None = None
    ) -> DataRecord:
        """
        Create a new record.
        
        Args:
            record_id: Unique identifier (alphanumeric + underscore)
            data: JSON-serializable data dictionary
            metadata: Optional metadata
        
        Returns:
            DataRecord: Created record
        
        Raises:
            ValueError: If record_id invalid or data not JSON-serializable
        
        Example:
            >>> store.create("algo_1", {"name": "binary_search"})
        """
        pass
    
    def get(self, record_id: str) -> DataRecord | None:
        """
        Get current version of record.
        
        Args:
            record_id: Record identifier
        
        Returns:
            DataRecord or None if not found
        
        Example:
            >>> rec = store.get("algo_1")
            >>> if rec:
            ...     print(rec.data["name"])
        """
        pass
    
    def update(
        self,
        record_id: str,
        data: Dict[str, Any],
        metadata: Dict[str, Any] | None = None
    ) -> DataRecord | None:
        """
        Update a record.
        
        Old version automatically saved in history.
        
        Args:
            record_id: Record to update
            data: New data
            metadata: New metadata
        
        Returns:
            DataRecord or None if record doesn't exist
        
        Example:
            >>> store.update("algo_1", {"name": "binary_search_v2"})
        """
        pass
    
    def delete(self, record_id: str) -> None:
        """
        Delete a record.
        
        Data is retained in history for recovery.
        
        Args:
            record_id: Record to delete
        
        Example:
            >>> store.delete("algo_1")
        """
        pass
    
    def list(self) -> List[DataRecord]:
        """List all current records."""
        pass
    
    def get_history(self, record_id: str) -> List[DataRecord]:
        """Get all versions of a record (newest first)."""
        pass


# ═══════════════════════════════════════════════════════════════════════════
# MODULE: core.licensing
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class LicenseCertificate:
    """
    Hardware-bound license certificate.
    
    Properties:
        - Tied to specific hardware (CPU + MAC + disk serial)
        - Expiration date
        - Revocation support
        - Tier-based features
        - Multiple seats option
    
    Example:
        >>> from core.licensing import LicenseCertificate
        >>> 
        >>> cert = LicenseCertificate(
        ...     user="alice@example.com",
        ...     tier="pro",
        ...     hardware_fingerprint="abc123def456...",
        ...     expires_at=time.time() + 86400*365
        ... )
    """
    pass


class LicenseManager:
    """
    Hardware-bound license management system.
    
    Features:
        - Immutable hardware fingerprint per machine
        - Cannot copy license to another computer
        - Expiration and revocation support
        - Tier-based feature access
        - HMAC-signed certificates
    
    Example:
        >>> from core.licensing import LicenseManager, TIERS
        >>> 
        >>> lm = LicenseManager()
        >>> 
        >>> # Get immutable hardware fingerprint
        >>> fingerprint = lm.get_hardware_fingerprint()
        >>> 
        >>> # Issue a license
        >>> cert = lm.issue_license(
        ...     user="alice@example.com",
        ...     name="Alice Developer",
        ...     tier="pro",
        ...     hardware_fingerprint=fingerprint,
        ...     expires_days=365
        ... )
        >>> 
        >>> # Save and load
        >>> lm.save_license(cert, "alice.license")
        >>> loaded = lm.load_license("alice.license")
        >>> 
        >>> # Verify
        >>> if lm.verify_license(loaded):
        ...     if not lm.is_expired(loaded):
        ...         print("License valid!")
    
    Methods:
        get_hardware_fingerprint() -> str
            Get immutable hardware ID
        issue_license(...) -> LicenseCertificate
            Create new license
        load_license(path) -> LicenseCertificate
            Load license from file
        verify_license(cert) -> bool
            Verify signature and hardware binding
        is_expired(cert) -> bool
            Check if license expired
        is_revoked(cert) -> bool
            Check if license revoked
    """
    
    def get_hardware_fingerprint(self) -> str:
        """
        Get immutable hardware fingerprint.
        
        Computed from CPU serial, MAC address, disk serial.
        Same on every boot of the same machine.
        Different on every other machine.
        
        Returns:
            str: SHA-512 hardware fingerprint
        
        Example:
            >>> lm = LicenseManager()
            >>> fp = lm.get_hardware_fingerprint()
            >>> print(fp)
            'a3f2d8c9e1b5f7a2...'
        """
        pass
    
    def issue_license(
        self,
        user: str,
        tier: str,
        hardware_fingerprint: str,
        expires_days: int = 365,
        **kwargs
    ) -> LicenseCertificate:
        """
        Create and sign a new license.
        
        Args:
            user: Email address
            tier: "free", "pro", or "enterprise"
            hardware_fingerprint: From get_hardware_fingerprint()
            expires_days: Days until expiration
        
        Returns:
            LicenseCertificate: Signed license
        
        Example:
            >>> cert = lm.issue_license(
            ...     user="user@example.com",
            ...     tier="pro",
            ...     hardware_fingerprint=fp,
            ...     expires_days=365
            ... )
        """
        pass
    
    def load_license(self, path: str) -> LicenseCertificate:
        """Load license from file."""
        pass
    
    def verify_license(self, cert: LicenseCertificate) -> bool:
        """Verify license signature and hardware binding."""
        pass
    
    def is_expired(self, cert: LicenseCertificate) -> bool:
        """Check if license expired."""
        pass
    
    def is_revoked(self, cert: LicenseCertificate) -> bool:
        """Check if license revoked."""
        pass


TIERS = {
    "free": {
        "algorithms_per_day": 3,
        "max_proof_size": 50 * 1024,  # 50KB
        "features": ["basic_proofs", "local_visualization"]
    },
    "pro": {
        "algorithms_per_day": 50,
        "max_proof_size": 10 * 1024 * 1024,  # 10MB
        "features": ["advanced_tactics", "cloud_backends", "priority_support"]
    },
    "enterprise": {
        "algorithms_per_day": float('inf'),
        "max_proof_size": float('inf'),
        "features": ["custom_tactics", "dedicated_server", "sla"]
    }
}


# ═══════════════════════════════════════════════════════════════════════════
# USAGE PATTERNS
# ═══════════════════════════════════════════════════════════════════════════

"""
PATTERN 1: Complete Security Setup

    from core.security import KeyStore, ProofCertificate
    from core.persistence import DataStore
    from core.licensing import LicenseManager
    
    # 1. Initialize components
    keystore = KeyStore(".axiomcode/keys")
    datastore = DataStore(".axiomcode/data")
    license_mgr = LicenseManager()
    
    # 2. Create root key
    root_key = keystore.create_key("root", "secure_passphrase_123")
    
    # 3. Get hardware fingerprint
    hardware_fp = license_mgr.get_hardware_fingerprint()
    
    # 4. Issue license bound to hardware
    license_cert = license_mgr.issue_license(
        user="alice@example.com",
        tier="pro",
        hardware_fingerprint=hardware_fp
    )
    
    # 5. Save license
    license_mgr.save_license(license_cert, "alice.license")
    
    # 6. Store algorithm metadata
    datastore.create("binary_search_v1", {
        "algorithm": "binary_search",
        "proof_valid": True,
        "generated_at": "2026-04-01T09:00:00Z"
    })


PATTERN 2: Verify Proof Certificate

    from core.security import KeyStore, ProofCertificate, hash_file
    from pathlib import Path
    
    keystore = KeyStore()
    root_key = keystore.load_key("root", "passphrase")
    
    # Load certificate
    cert = ProofCertificate.load("binary_search.cert")
    
    # Verify signature
    if not cert.verify_signature(root_key.signing_key):
        raise ValueError("Certificate tampered with!")
    
    # Verify binary hash
    actual_hash = hash_file(Path("binary_search.so"))
    if actual_hash != cert.c_binary_hash:
        raise ValueError("Binary doesn't match proof!")
    
    print("✓ Proof verified and binary authentic")


PATTERN 3: License Checking

    from core.licensing import LicenseManager
    import time
    
    license_mgr = LicenseManager()
    
    def check_license_and_execute(feature_name):
        # Load current license
        license_cert = license_mgr.load_license("user.license")
        
        # Verify
        if not license_mgr.verify_license(license_cert):
            raise ValueError("Invalid license")
        
        # Check expiration
        if license_mgr.is_expired(license_cert):
            raise ValueError("License expired")
        
        # Check revocation
        if license_mgr.is_revoked(license_cert):
            raise ValueError("License revoked")
        
        # Check tier has this feature
        tier_features = TIERS[license_cert.tier]["features"]
        if feature_name not in tier_features:
            raise ValueError(f"{feature_name} not available in {license_cert.tier} tier")
        
        # Execute feature
        execute_feature(feature_name)


PATTERN 4: Data Versioning

    from core.persistence import DataStore
    
    store = DataStore()
    
    # Keep history across algorithm versions
    store.create("gcd", {"version": 1, "algorithm": "euclidean"})
    store.update("gcd", {"version": 2, "algorithm": "extended_euclidean"})
    store.update("gcd", {"version": 3, "algorithm": "binary_gcd"})
    
    # See all versions
    history = store.get_history("gcd")
    for i, record in enumerate(history):
        print(f"Version {i+1}: {record.data}")
    
    # Go back to version 2
    version_2 = history[1]
    store.update("gcd", version_2.data)


PATTERN 5: Secure Key Operations

    from core.security import KeyStore
    import tempfile
    
    with tempfile.TemporaryDirectory() as tmpdir:
        ks = KeyStore(tmpdir)
        
        # Create
        key1 = ks.create_key("user1", "password123")
        key2 = ks.create_key("user2", "password456")
        
        # Load (validates passphrase)
        loaded1 = ks.load_key("user1", "password123")
        
        # Wrong passphrase fails immediately
        try:
            ks.load_key("user1", "wrong_password")
        except ValueError:
            print("✓ Passphrase validation working")
        
        # Delete securely
        ks.delete_key("user1")
"""


# ═══════════════════════════════════════════════════════════════════════════
# REFERENCE TABLE
# ═══════════════════════════════════════════════════════════════════════════

REFERENCE_TABLE = """
┌─────────────────────────────────────────────────────────────────────────┐
│                    AxiomCode API Quick Reference                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  SECURITY                    │  PERSISTENCE              │  LICENSING   │
│  ───────────────────────────┼──────────────────────────┼──────────────│
│  KeyPair                    │  DataStore               │  LicenseMgr  │
│  ├─ generate()              │  ├─ create()             │  ├─ issue()  │
│  ├─ to_dict()               │  ├─ get()                │  ├─ verify() │
│  └─ from_dict()             │  ├─ update()             │  ├─ revoke() │
│                             │  ├─ delete()             │  └─ expired()│
│  KeyStore                   │  ├─ list()               │              │
│  ├─ create_key()            │  └─ get_history()        │  Certificate│
│  ├─ load_key() ★            │                          │  ├─ sign()   │
│  └─ delete_key()            │  DataRecord              │  ├─ verify() │
│                             │  ├─ id                   │  ├─ save()   │
│  ProofCertificate           │  ├─ data                 │  └─ load()   │
│  ├─ sign()                  │  ├─ metadata             │              │
│  ├─ verify_signature()      │  ├─ created_at           │  AuditLog    │
│  ├─ save()                  │  └─ updated_at           │  ├─ log()    │
│  └─ load()                  │                          │  ├─ read()   │
│                             │                          │  └─ verify() │
│  AuditLog                   │                          │              │
│  ├─ log_event()             │                          │              │
│  ├─ read_log()              │                          │              │
│  └─ verify_integrity()      │                          │              │
│                             │                          │              │
│  Functions:                 │                          │              │
│  ├─ hash_data()             │                          │              │
│  ├─ hash_file()             │                          │              │
│  ├─ compute_hmac()          │                          │              │
│  └─ verify_hmac()           │                          │              │
│                             │                          │              │
│  ★ = Always validates input (no unsafe caching)       │              │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
"""

if __name__ == "__main__":
    # Print reference
    print(REFERENCE_TABLE)
    print("\nFor full documentation, see AXIOMCODE_USER_GUIDE.md")
    print("For CLI commands, run: python cli.py help")
