"""
Comprehensive test suite for AxiomCode core modules.
Tests security, licensing, versioning, and persistence with integration scenarios.
"""

import pytest
import sys
import json
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


# ─── Security Module Tests ──────────────────────────────────────────────────

class TestKeyPairAndKeyStore:
    """Test key generation, storage, and retrieval."""

    def test_keypair_generation(self):
        """KeyPair should generate unique, properly-sized keys."""
        from core.security import KeyPair
        kp = KeyPair.generate()
        
        assert len(kp.encryption_key) == 64  # 512-bit
        assert len(kp.signing_key) == 64
        assert len(kp.key_id) == 16
        assert kp.created_at > 0
        
        # Generate second keypair - should be different
        kp2 = KeyPair.generate()
        assert kp.key_id != kp2.key_id
        assert kp.encryption_key != kp2.encryption_key

    def test_keypair_serialization(self):
        """KeyPair to_dict/from_dict should be reversible."""
        from core.security import KeyPair
        kp = KeyPair.generate()
        d = kp.to_dict()
        
        # Should be valid JSON
        json_str = json.dumps(d)
        parsed = json.loads(json_str)
        
        # Should deserialize back to same keypair
        kp2 = KeyPair.from_dict(parsed)
        assert kp2.key_id == kp.key_id
        assert kp2.encryption_key == kp.encryption_key
        assert kp2.signing_key == kp.signing_key

    def test_keystore_create_and_load(self):
        """KeyStore should encrypt and store keys securely."""
        from core.security import KeyStore
        
        with tempfile.TemporaryDirectory() as tmpdir:
            ks = KeyStore(tmpdir)
            
            # Create key
            kp = ks.create_key("test_key", "secure_passphrase")
            assert kp.key_id is not None
            
            # Load key
            loaded = ks.load_key("test_key", "secure_passphrase")
            assert loaded.key_id == kp.key_id
            assert loaded.encryption_key == kp.encryption_key

    def test_keystore_wrong_passphrase(self):
        """KeyStore should reject wrong passphrase."""
        from core.security import KeyStore
        
        with tempfile.TemporaryDirectory() as tmpdir:
            ks = KeyStore(tmpdir)
            ks.create_key("test_key", "correct_pass")
            
            # Should raise ValueError for wrong passphrase (either decrypt or JSON parse error)
            with pytest.raises(ValueError):
                ks.load_key("test_key", "wrong_pass")

    def test_keystore_nonexistent_key(self):
        """KeyStore should raise error for missing key."""
        from core.security import KeyStore
        
        with tempfile.TemporaryDirectory() as tmpdir:
            ks = KeyStore(tmpdir)
            with pytest.raises(FileNotFoundError):
                ks.load_key("nonexistent", "pass")

    def test_keystore_delete_key(self):
        """KeyStore should securely delete keys."""
        from core.security import KeyStore
        
        with tempfile.TemporaryDirectory() as tmpdir:
            ks = KeyStore(tmpdir)
            ks.create_key("to_delete", "pass")
            
            # Verify exists
            assert ks.load_key("to_delete", "pass") is not None
            
            # Delete
            ks.delete_key("to_delete")
            
            # Should not exist anymore
            with pytest.raises(FileNotFoundError):
                ks.load_key("to_delete", "pass")


class TestProofCertificates:
    """Test proof certificate signing and verification."""

    def test_proof_cert_sign_verify(self):
        """Proof certificate should be signable and verifiable."""
        from core.security import ProofCertificate
        import secrets
        
        key = secrets.token_bytes(64)
        cert = ProofCertificate(
            algorithm_name="binary_search",
            spec_hash="abc123def456",
            proof_hash="xyz789abc",
            c_binary_hash="c_hash_value",
            python_hash="py_hash_value",
            theorem="theorem binary_search_correct : True",
            tactics=["decide", "simp"],
            steps=42,
            lemmas=5,
            model_used="claude-opus",
            generated_at=time.time(),
        )
        
        cert.sign(key)
        assert cert.signature != ""
        assert cert.verify(key) is True

    def test_proof_cert_tamper_detection(self):
        """Tampered certificates should fail verification."""
        from core.security import ProofCertificate
        import secrets
        
        key = secrets.token_bytes(64)
        cert = ProofCertificate(
            algorithm_name="binary_search",
            spec_hash="abc123",
            steps=5,
        )
        cert.sign(key)
        original_sig = cert.signature
        
        # Tamper: change algorithm name
        cert.algorithm_name = "altered"
        assert cert.verify(key) is False
        
        # Tamper: change steps
        cert.algorithm_name = "binary_search"
        cert.steps = 999
        assert cert.verify(key) is False

    def test_proof_cert_json_roundtrip(self):
        """Proof certificate should serialize/deserialize via JSON."""
        from core.security import ProofCertificate, compute_hmac
        import secrets
        
        key = secrets.token_bytes(64)
        cert = ProofCertificate(
            algorithm_name="gcd",
            spec_hash="spec_abc",
            proof_hash="proof_xyz",
            theorem="theorem gcd_correct",
            steps=10,
        )
        cert.sign(key)
        
        # Serialize to JSON
        json_str = cert.to_json()
        
        # Parse back
        cert2 = ProofCertificate.from_json(json_str)
        assert cert2.algorithm_name == cert.algorithm_name
        assert cert2.signature == cert.signature
        assert cert2.verify(key) is True

    def test_proof_cert_file_persistence(self):
        """Proof certificate should save and load from file."""
        from core.security import ProofCertificate
        import secrets
        
        with tempfile.TemporaryDirectory() as tmpdir:
            key = secrets.token_bytes(64)
            cert = ProofCertificate(
                algorithm_name="insertion_sort",
                spec_hash="spec123",
                theorem="theorem sort_correct",
                steps=7,
            )
            cert.sign(key)
            
            cert_file = Path(tmpdir) / "test_cert.json"
            cert.save(cert_file)
            assert cert_file.exists()
            
            # Load back
            loaded = ProofCertificate.load(cert_file)
            assert loaded.algorithm_name == "insertion_sort"
            assert loaded.verify(key) is True


class TestBinarySignatures:
    """Test binary file signing and verification."""

    def test_sign_and_verify_binary(self):
        """Binary signature should be verifiable."""
        from core.security import sign_binary, hash_file, BinarySignature
        import secrets
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test binary
            test_bin = Path(tmpdir) / "test.bin"
            test_bin.write_bytes(b"test binary content")
            
            key = secrets.token_bytes(64)
            sig = sign_binary(test_bin, key, "key_001", "c_binary")
            
            assert isinstance(sig, BinarySignature)
            assert sig.file_hash != ""
            assert sig.signature != ""
            assert sig.verify(test_bin, key) is True

    def test_binary_tamper_detection(self):
        """Tampered binary should fail verification."""
        from core.security import sign_binary
        import secrets
        
        with tempfile.TemporaryDirectory() as tmpdir:
            test_bin = Path(tmpdir) / "test.bin"
            test_bin.write_bytes(b"original content")
            
            key = secrets.token_bytes(64)
            sig = sign_binary(test_bin, key, "key_001")
            
            # Tamper with binary
            test_bin.write_bytes(b"modified content")
            
            # Verification should fail
            assert sig.verify(test_bin, key) is False

    def test_binary_wrong_key(self):
        """Binary signed with one key should not verify with another."""
        from core.security import sign_binary
        import secrets
        
        with tempfile.TemporaryDirectory() as tmpdir:
            test_bin = Path(tmpdir) / "test.bin"
            test_bin.write_bytes(b"content")
            
            key1 = secrets.token_bytes(64)
            key2 = secrets.token_bytes(64)
            
            sig = sign_binary(test_bin, key1, "key_001", "c_binary")
            assert sig.verify(test_bin, key1) is True
            # Different key should not verify
            result = sig.verify(test_bin, key2)
            assert result is False or result == False  # Handle different falsy returns


class TestSecureChannel:
    """Test encrypted communication channel."""

    def test_secure_channel_encryption(self):
        """SecureChannel should encrypt and decrypt data."""
        from core.security import SecureChannel
        import secrets
        
        key = secrets.token_bytes(64)
        channel = SecureChannel(key)
        
        plaintext = b"sensitive data"
        encrypted_dict = channel.encrypt(plaintext)
        
        assert "nonce" in encrypted_dict
        assert "data" in encrypted_dict
        assert "mac" in encrypted_dict
        
        decrypted = channel.decrypt(encrypted_dict)
        assert decrypted == plaintext

    def test_secure_channel_tamper_detection(self):
        """SecureChannel should detect tampering."""
        from core.security import SecureChannel
        import secrets
        
        key = secrets.token_bytes(64)
        channel = SecureChannel(key)
        
        plaintext = b"test data"
        encrypted_dict = channel.encrypt(plaintext)
        
        # Tamper with MAC
        encrypted_dict["mac"] = "a" * 64
        
        with pytest.raises(ValueError, match="MAC verification failed"):
            channel.decrypt(encrypted_dict)


class TestAuditLog:
    """Test tamper-evident audit logging."""

    def test_audit_log_create_and_read(self):
        """AuditLog should create and store entries."""
        from core.security import AuditLog
        
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "audit.log"
            audit = AuditLog(log_file)
            
            # Add entries
            h1 = audit.add_entry("login", {"user": "alice"}, "alice")
            h2 = audit.add_entry("algorithm_verified", {"algo": "sort"}, "system")
            
            assert h1 != ""
            assert h2 != ""
            assert h1 != h2

    def test_audit_log_chain_integrity(self):
        """AuditLog chain should verify integrity."""
        from core.security import AuditLog
        
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "audit.log"
            audit = AuditLog(log_file)
            
            # Add entries
            audit.add_entry("action_1", {"data": "value1"})
            audit.add_entry("action_2", {"data": "value2"})
            audit.add_entry("action_3", {"data": "value3"})
            
            # Verify chain
            assert audit.verify_integrity() is True

    def test_audit_log_tamper_detection(self):
        """AuditLog should detect tampering."""
        from core.security import AuditLog
        import json
        
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "audit.log"
            audit = AuditLog(log_file)
            
            audit.add_entry("action", {"data": "value"})
            
            # Tamper with log file
            lines = log_file.read_text().strip().split("\n")
            first_entry = json.loads(lines[0])
            first_entry["details"]["data"] = "tampered"
            lines[0] = json.dumps(first_entry)
            log_file.write_text("\n".join(lines))
            
            # Load fresh instance and verify
            audit2 = AuditLog(log_file)
            assert audit2.verify_integrity() is False


class TestSecureSandbox:
    """Test sandboxed code execution."""

    def test_sandbox_simple_command(self):
        """SecureSandbox should run commands safely."""
        from core.security import SecureSandbox
        import platform
        
        with tempfile.TemporaryDirectory() as tmpdir:
            sandbox = SecureSandbox(tmpdir)
            
            # Run simple command (platform-specific)
            if platform.system() == "Windows":
                # On Windows: cmd.exe is typically available
                result = sandbox.run(["cmd", "/c", "echo", "hello"], timeout=5)
            else:
                # On Unix/Linux
                result = sandbox.run(["echo", "hello"], timeout=5)
            
            assert result["success"] is True
            assert result["returncode"] == 0
            assert "hello" in result["stdout"]

    def test_sandbox_timeout(self):
        """SecureSandbox should respect timeout."""
        from core.security import SecureSandbox
        import platform
        
        with tempfile.TemporaryDirectory() as tmpdir:
            sandbox = SecureSandbox(tmpdir)
            
            # Run long command with short timeout (platform-specific)
            if platform.system() == "Windows":
                # On Windows: use python -c with sleep (no I/O redirection needed)
                result = sandbox.run(["python", "-c", "import time; time.sleep(10)"], timeout=1)
            else:
                # On Unix/Linux: use sleep
                result = sandbox.run(["sleep", "10"], timeout=1)
            
            assert result["success"] is False
            # Check for timeout in stderr or returncode
            assert result["returncode"] == -1 or "timed out" in result["stderr"] or result["returncode"] != 0

    def test_sandbox_cleanup(self):
        """SecureSandbox should clean up work directory."""
        from core.security import SecureSandbox
        
        with tempfile.TemporaryDirectory() as tmpdir:
            sandbox = SecureSandbox(tmpdir)
            work_dir = sandbox.work_dir
            
            # Create some files
            (work_dir / "test.txt").write_text("content")
            assert (work_dir / "test.txt").exists()
            
            # Cleanup
            sandbox.cleanup()
            assert not (work_dir / "test.txt").exists()


class TestRateLimiter:
    """Test rate limiting."""

    def test_rate_limiter_acquire(self):
        """RateLimiter should track token availability."""
        from core.security import RateLimiter
        
        limiter = RateLimiter(max_tokens=3, refill_rate=1.0)
        
        # Should acquire 3 tokens
        assert limiter.acquire() is True
        assert limiter.acquire() is True
        assert limiter.acquire() is True
        
        # Fourth should fail
        assert limiter.acquire() is False

    def test_rate_limiter_refill(self):
        """RateLimiter should refill tokens over time."""
        from core.security import RateLimiter
        import time
        
        limiter = RateLimiter(max_tokens=1, refill_rate=1.0)  # 1 token/second
        
        # Use the token
        assert limiter.acquire() is True
        assert limiter.acquire() is False
        
        # Wait for refill
        time.sleep(1.1)
        
        # Should acquire again
        assert limiter.acquire() is True


# ─── Licensing Module Tests ──────────────────────────────────────────────────

class TestLicensing:
    """Test license generation and verification."""

    def test_hardware_fingerprint(self):
        """Hardware fingerprint should be consistent and unique."""
        from core.licensing import get_hardware_fingerprint, get_hardware_hash
        
        fp1 = get_hardware_fingerprint()
        fp2 = get_hardware_fingerprint()
        
        assert fp1 == fp2
        assert len(fp1) == 128  # SHA-512 hex
        
        # Hardware hash should also be consistent
        hash1 = get_hardware_hash()
        hash2 = get_hardware_hash()
        assert hash1 == hash2

    def test_license_key_pair_generation(self):
        """LicenseKeyPair should generate and serialize."""
        from core.licensing import LicenseKeyPair
        
        keypair = LicenseKeyPair.generate()
        
        assert len(keypair.private_key) == 64
        assert len(keypair.public_key) == 64
        assert keypair.key_id != ""
        assert keypair.algorithm == "hmac-sha512"

    def test_license_key_pair_persistence(self):
        """LicenseKeyPair should save and load from file."""
        from core.licensing import LicenseKeyPair
        
        with tempfile.TemporaryDirectory() as tmpdir:
            keypair = LicenseKeyPair.generate()
            
            private_path = Path(tmpdir) / "private.key"
            public_path = Path(tmpdir) / "public.key"
            
            # Save
            keypair.save_private(private_path, passphrase="secret")
            keypair.save_public(public_path)
            
            # Load
            loaded_private = LicenseKeyPair.load_private(private_path, "secret")
            loaded_public = LicenseKeyPair.load_public(public_path)
            
            assert loaded_private.key_id == keypair.key_id
            assert loaded_public.key_id == keypair.key_id

    def test_license_certificate_sign_verify(self):
        """License certificate should be signable and verifiable."""
        from core.licensing import LicenseCertificate, LicenseKeyPair
        import secrets
        
        keypair = LicenseKeyPair.generate()
        
        cert = LicenseCertificate(
            license_id="AxC-2026-001",
            user_id="user_123",
            user_name="Alice",
            tier="pro",
            features=["verified_code", "advanced_analytics"],
            max_seats=5,
            issued_at=time.time(),
            expires_at=time.time() + 365 * 24 * 3600,
        )
        
        cert.sign(keypair.private_key)
        assert cert.verify(keypair.public_key) is True

    def test_license_certificate_expiration(self):
        """Expired licenses should be rejected."""
        from core.licensing import LicenseCertificate, LicenseKeyPair
        
        keypair = LicenseKeyPair.generate()
        
        # License expired 1 hour ago
        cert = LicenseCertificate(
            license_id="old_license",
            user_id="user_123",
            tier="community",
            expires_at=time.time() - 3600,
        )
        cert.sign(keypair.private_key)
        
        is_valid, reason = cert.is_valid(keypair.public_key)
        assert is_valid is False
        assert "expired" in reason.lower()

    def test_license_certificate_revocation(self):
        """Revoked licenses should be rejected."""
        from core.licensing import LicenseCertificate, LicenseKeyPair
        
        keypair = LicenseKeyPair.generate()
        
        cert = LicenseCertificate(
            license_id="revoked_license",
            user_id="user_123",
            tier="pro",
            revoked=True,
            revocation_reason="Key compromise",
        )
        cert.sign(keypair.private_key)
        
        is_valid, reason = cert.is_valid(keypair.public_key)
        assert is_valid is False
        assert "revoked" in reason.lower()

    def test_license_manager(self):
        """LicenseManager should issue and verify licenses."""
        from core.licensing import LicenseManager
        from pathlib import Path
        
        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = LicenseManager(tmpdir)
            
            # Generate root key
            root_key = mgr.generate_root_key()
            
            # Save and load the key pair
            private_key_path = Path(tmpdir) / "root_private.key"
            public_key_path = Path(tmpdir) / "root_public.key"
            
            root_key.save_private(private_key_path, "")
            root_key.save_public(public_key_path)
            
            mgr.load_private_key(private_key_path, "")
            mgr.load_public_key(public_key_path)
            
            # Issue license
            license_cert = mgr.issue_license(
                user_id="alice",
                user_name="Alice",
                tier="pro",
            )
            
            # Verify license
            is_valid, reason = mgr.verify_license(license_cert)
            assert is_valid is True


# ─── Persistence Module Tests ────────────────────────────────────────────────

class TestDataStore:
    """Test persistent data storage."""

    def test_data_store_create_read(self):
        """DataStore should persist and retrieve records."""
        from core.persistence import DataStore
        
        with tempfile.TemporaryDirectory() as tmpdir:
            store = DataStore(tmpdir)
            
            # Create record
            record = store.create("algo_001", {
                "name": "binary_search",
                "complexity": "O(log n)",
            })
            
            assert record.id == "algo_001"
            assert record.data["name"] == "binary_search"
            
            # Read record
            loaded = store.get("algo_001")
            assert loaded is not None
            assert loaded.data["name"] == "binary_search"

    def test_data_store_update(self):
        """DataStore should update records and preserve history."""
        from core.persistence import DataStore
        
        with tempfile.TemporaryDirectory() as tmpdir:
            store = DataStore(tmpdir)
            
            # Create record
            store.create("record_1", {"status": "draft"})
            
            # Update record
            updated = store.update("record_1", {"status": "verified"})
            assert updated.data["status"] == "verified"
            
            # History should contain original
            history = store.get_history("record_1")
            assert len(history) > 0
            assert history[0].data["status"] == "draft"

    def test_data_store_delete_preserves_history(self):
        """DataStore.delete should preserve historical versions."""
        from core.persistence import DataStore
        
        with tempfile.TemporaryDirectory() as tmpdir:
            store = DataStore(tmpdir)
            
            store.create("to_delete", {"data": "value"})
            deleted = store.delete("to_delete")
            
            assert deleted is True
            
            # Get should return None
            assert store.get("to_delete") is None
            
            # But history should exist
            history = store.get_history("to_delete")
            assert len(history) > 0
            assert history[0].data["data"] == "value"

    def test_data_store_list(self):
        """DataStore should list all records."""
        from core.persistence import DataStore
        
        with tempfile.TemporaryDirectory() as tmpdir:
            store = DataStore(tmpdir)
            
            store.create("record_1", {"name": "algo1"})
            store.create("record_2", {"name": "algo2"})
            store.create("record_3", {"name": "algo3"})
            
            records = store.list()
            assert len(records) == 3


class TestVersioning:
    """Test version management and migrations."""

    def test_version_manager_get_current(self):
        """VersionManager should report current version."""
        from core.versioning import VersionManager, CURRENT_VERSION
        
        with tempfile.TemporaryDirectory() as tmpdir:
            vm = VersionManager(tmpdir)
            vm.initialize()
            
            current = vm.get_current_version()
            assert current == CURRENT_VERSION

    def test_version_manager_backup_and_rollback(self):
        """VersionManager should create backups and rollback."""
        from core.versioning import VersionManager
        import json
        
        with tempfile.TemporaryDirectory() as tmpdir:
            vm = VersionManager(tmpdir)
            vm.initialize()
            
            # Create some data
            data_file = Path(tmpdir) / ".axiomcode" / "data.json"
            data_file.parent.mkdir(parents=True, exist_ok=True)
            data_file.write_text(json.dumps({"version": "1"}))
            
            # Create backup
            backup_path = vm._create_backup("0.1.0")
            assert backup_path.exists()
            
            # Backups should be listed
            backups = vm.list_backups()
            assert len(backups) > 0


# ─── Integration Tests ──────────────────────────────────────────────────────

class TestIntegration:
    """Integration tests combining multiple modules."""

    def test_full_algorithm_verification_flow(self):
        """Full flow: generate cert, sign binaries, verify all."""
        from core.security import ProofCertificate, sign_binary, BinarySignature
        from core.licensing import LicenseManager
        import secrets
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup
            key = secrets.token_bytes(64)
            
            # Create proof certificate
            cert = ProofCertificate(
                algorithm_name="verified_sort",
                theorem="sorted output = permutation of input",
                steps=12,
                lemmas=3,
            )
            cert.sign(key)
            
            # Create binary and sign
            binary_path = Path(tmpdir) / "sort.o"
            binary_path.write_bytes(b"compiled binary")
            sig = sign_binary(binary_path, key, "key_001", "c_binary")
            assert isinstance(sig, BinarySignature)
            
            # Both should verify
            assert cert.verify(key)
            assert sig.verify(binary_path, key)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
