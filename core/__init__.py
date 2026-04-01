# Core module -- security, versioning, licensing, persistence
from core.security import (
    KeyStore, KeyPair,
    ProofCertificate, BinarySignature, sign_binary,
    SecureChannel, AuditLog, SecureSandbox, RateLimiter,
    hash_data, hash_file, compute_hmac, verify_hmac,
)
from core.versioning import VersionManager, CURRENT_VERSION
from core.licensing import (
    LicenseManager, LicenseCertificate, LicenseKeyPair,
    get_hardware_fingerprint, get_hardware_hash, TIERS,
)
from core.persistence import DataStore, SessionManager, AlgorithmRegistry

__all__ = [
    "KeyStore", "KeyPair",
    "ProofCertificate", "BinarySignature", "sign_binary",
    "SecureChannel", "AuditLog", "SecureSandbox", "RateLimiter",
    "hash_data", "hash_file", "compute_hmac", "verify_hmac",
    "VersionManager", "CURRENT_VERSION",
    "LicenseManager", "LicenseCertificate", "LicenseKeyPair",
    "get_hardware_fingerprint", "get_hardware_hash", "TIERS",
    "DataStore", "SessionManager", "AlgorithmRegistry",
]
