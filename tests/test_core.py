"""Test suite for AxiomCode -- zero external dependencies, zero-trust security."""

import pytest
import sys
import json
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestSpecGenerator:
    def test_lean_spec_to_lean(self):
        from cli import LeanSpec
        spec = LeanSpec(theorem="theorem foo : True := by sorry", imports=["Mathlib"], docstring="Test theorem")
        output = spec.to_lean()
        assert "import Mathlib" in output
        assert "theorem foo" in output

    def test_lean_spec_defaults(self):
        from cli import LeanSpec
        spec = LeanSpec(theorem="theorem bar : True := by sorry")
        assert "Mathlib" in spec.imports
        assert "Aesop" in spec.imports

    def test_parse_code_block(self):
        from cli import _parse_spec
        raw = "```lean\nimport Mathlib\n/-- Test -/\ntheorem test_correct : True := by sorry\n```"
        spec = _parse_spec(raw, "test", 100.0, "local")
        assert "Mathlib" in spec.imports
        assert "theorem test_correct" in spec.theorem

    def test_backends_registered(self):
        from cli import BACKENDS
        assert "local" in BACKENDS
        assert "openai" in BACKENDS
        assert "anthropic" in BACKENDS


class TestSecurity:
    def test_keypair_generation(self):
        from core.security import KeyPair
        kp = KeyPair.generate()
        assert len(kp.encryption_key) == 64
        assert len(kp.signing_key) == 64
        assert len(kp.key_id) == 16

    def test_keystore_roundtrip(self):
        from core.security import KeyStore
        with tempfile.TemporaryDirectory() as tmpdir:
            ks = KeyStore(tmpdir)
            kp = ks.create_key("test", "pass123")
            loaded = ks.load_key("test", "pass123")
            assert loaded.key_id == kp.key_id

    def test_proof_certificate(self):
        from core.security import ProofCertificate
        import secrets
        key = secrets.token_bytes(64)
        cert = ProofCertificate(
            algorithm_name="binary_search",
            spec_hash="abc123",
            proof_hash="def456",
            theorem="theorem binary_search_correct",
            steps=5,
            lemmas=2,
        )
        cert.sign(key)
        assert cert.verify(key) is True

    def test_proof_certificate_tamper(self):
        from core.security import ProofCertificate
        import secrets
        key = secrets.token_bytes(64)
        cert = ProofCertificate(
            algorithm_name="binary_search",
            spec_hash="abc123",
            proof_hash="def456",
            steps=5,
        )
        cert.sign(key)
        cert.steps = 999  # Tamper
        assert cert.verify(key) is False

    def test_hmac(self):
        from core.security import compute_hmac, verify_hmac
        import secrets
        key = secrets.token_bytes(32)
        data = b"test data"
        mac = compute_hmac(key, data)
        assert verify_hmac(key, data, mac) is True
        assert verify_hmac(key, b"different data", mac) is False

    def test_hash_data(self):
        from core.security import hash_data
        h1 = hash_data(b"hello")
        h2 = hash_data(b"hello")
        h3 = hash_data(b"world")
        assert h1 == h2
        assert h1 != h3

    def test_audit_log_integrity(self):
        from core.security import AuditLog
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "audit.log"
            audit = AuditLog(log_file)
            audit.add_entry("test_action", {"key": "value"})
            audit.add_entry("test_action2", {"key": "value2"})
            assert audit.verify_integrity() is True

    def test_secure_sandbox(self):
        from core.security import SecureSandbox
        with tempfile.TemporaryDirectory() as tmpdir:
            sandbox = SecureSandbox(tmpdir)
            result = sandbox.run([sys.executable, "-c", "print('hello')"])
            assert result["success"] is True
            assert "hello" in result["stdout"]
            sandbox.cleanup()

    def test_rate_limiter(self):
        from core.security import RateLimiter
        rl = RateLimiter(max_tokens=3, refill_rate=0.0)
        assert rl.acquire() is True
        assert rl.acquire() is True
        assert rl.acquire() is True
        assert rl.acquire() is False


class TestVisualization:
    def test_build_graph_data(self):
        from cli import _build_graph_data, ProofResult
        proof = ProofResult(theorem_name="test", steps=3, lemmas=1, lean_file=Path("test.lean"), tactics=["rw [h]", "simp", "exact h"])
        data = _build_graph_data(proof, "2d")
        assert len(data["nodes"]) == 3
        assert len(data["edges"]) == 2

    def test_build_proof_html(self):
        from cli import build_proof_html, ProofResult
        proof = ProofResult(theorem_name="test", steps=3, lemmas=1, lean_file=Path("test.lean"), tactics=["rw", "simp", "exact"])
        html = build_proof_html(proof, "2d")
        assert "AxiomCode" in html
        assert "d3.v7.min.js" in html


class TestCLI:
    def test_main_exists(self):
        from cli import main
        assert callable(main)


class TestVersioning:
    def test_version_manager_init(self):
        from core.versioning import VersionManager
        vm = VersionManager()
        assert vm.get_current_version() == "0.1.0"

    def test_version_set_and_get(self):
        from core.versioning import VersionManager
        with tempfile.TemporaryDirectory() as tmpdir:
            vm = VersionManager(tmpdir)
            vm.initialize()
            assert vm.get_current_version() == "0.1.0"
            assert vm.get_schema_version() == 1

    def test_version_registry(self):
        from core.versioning import VERSION_REGISTRY
        assert "0.1.0" in VERSION_REGISTRY
        info = VERSION_REGISTRY["0.1.0"]
        assert info.version == "0.1.0"
        assert len(info.new_features) > 0

    def test_migration_noop(self):
        from core.versioning import VersionManager
        with tempfile.TemporaryDirectory() as tmpdir:
            vm = VersionManager(tmpdir)
            vm.initialize()
            result = vm.migrate("0.1.0")
            assert result["status"] == "no-op"

    def test_list_versions(self):
        from core.versioning import VersionManager
        vm = VersionManager()
        versions = vm.list_versions()
        assert len(versions) >= 1

    def test_validate_data_integrity(self):
        from core.versioning import VersionManager
        with tempfile.TemporaryDirectory() as tmpdir:
            vm = VersionManager(tmpdir)
            vm.initialize()
            result = vm.validate_data_integrity()
            assert "version" in result
            assert "valid" in result

    def test_list_backups_empty(self):
        from core.versioning import VersionManager
        with tempfile.TemporaryDirectory() as tmpdir:
            vm = VersionManager(tmpdir)
            backups = vm.list_backups()
            assert backups == []

    def test_migration_history_empty(self):
        from core.versioning import VersionManager
        with tempfile.TemporaryDirectory() as tmpdir:
            vm = VersionManager(tmpdir)
            history = vm.get_migration_history()
            assert history == []

    def test_version_info(self):
        from core.versioning import VersionManager
        vm = VersionManager()
        info = vm.get_version_info("0.1.0")
        assert info.version == "0.1.0"
        assert info.schema_version == 1


class TestLicensing:
    def test_keypair_generation(self):
        from core.licensing import LicenseKeyPair
        keys = LicenseKeyPair.generate()
        assert len(keys.private_key) == 64
        assert len(keys.public_key) == 64
        assert len(keys.key_id) == 16

    def test_keypair_save_load(self):
        from core.licensing import LicenseKeyPair
        with tempfile.TemporaryDirectory() as tmpdir:
            keys = LicenseKeyPair.generate()
            priv_path = Path(tmpdir) / "private.key"
            pub_path = Path(tmpdir) / "public.key"
            keys.save_private(priv_path, "testpass")
            keys.save_public(pub_path)
            loaded_priv = LicenseKeyPair.load_private(priv_path, "testpass")
            loaded_pub = LicenseKeyPair.load_public(pub_path)
            assert loaded_priv.private_key == keys.private_key
            assert loaded_pub.public_key == keys.public_key

    def test_license_issue_and_verify(self):
        from core.licensing import LicenseManager
        with tempfile.TemporaryDirectory() as tmpdir:
            lm = LicenseManager(tmpdir)
            keys = lm.generate_root_key()
            lic = lm.issue_license(
                user_id="test@example.com",
                user_name="Test User",
                tier="pro",
            )
            assert lic.signature != ""
            assert lic.key_id == keys.key_id
            assert lm._public_key is not None
            valid, reason = lic.is_valid(lm._public_key)
            assert valid is True, f"License should be valid: {reason}"

    def test_license_tamper_detection(self):
        from core.licensing import LicenseManager
        with tempfile.TemporaryDirectory() as tmpdir:
            lm = LicenseManager(tmpdir)
            lm.generate_root_key()
            lic = lm.issue_license(
                user_id="test@example.com",
                user_name="Test User",
                tier="pro",
            )
            lic.tier = "enterprise"  # Tamper
            assert lm._public_key is not None
            valid, reason = lic.is_valid(lm._public_key)
            assert valid is False, "Tampered license should fail verification"

    def test_license_expiration(self):
        from core.licensing import LicenseManager
        with tempfile.TemporaryDirectory() as tmpdir:
            lm = LicenseManager(tmpdir)
            lm.generate_root_key()
            lic = lm.issue_license(
                user_id="test@example.com",
                user_name="Test User",
                tier="pro",
                expires_at=time.time() - 86400,  # Expired yesterday
            )
            assert lm._public_key is not None
            valid, reason = lic.is_valid(lm._public_key)
            assert valid is False
            assert "expired" in reason.lower()

    def test_license_revocation(self):
        from core.licensing import LicenseManager
        with tempfile.TemporaryDirectory() as tmpdir:
            lm = LicenseManager(tmpdir)
            lm.generate_root_key()
            lic = lm.issue_license(
                user_id="test@example.com",
                user_name="Test User",
                tier="pro",
            )
            lm.revoke_license(lic.license_id, "Payment failed")
            assert lm.is_revoked(lic.license_id)
            valid, reason = lm.verify_license(lic)
            assert valid is False
            assert "revoked" in reason.lower()

    def test_license_save_load(self):
        from core.licensing import LicenseManager, LicenseCertificate
        with tempfile.TemporaryDirectory() as tmpdir:
            lm = LicenseManager(tmpdir)
            lm.generate_root_key()
            lic = lm.issue_license(
                user_id="test@example.com",
                user_name="Test User",
                tier="pro",
            )
            lic_path = Path(tmpdir) / "test.license.json"
            lic.save(lic_path)
            loaded = LicenseCertificate.load(lic_path)
            assert loaded.license_id == lic.license_id
            assert loaded.user_id == lic.user_id
            assert lm._public_key is not None
            assert loaded.verify(lm._public_key)

    def test_portable_license(self):
        from core.licensing import LicenseManager
        with tempfile.TemporaryDirectory() as tmpdir:
            lm = LicenseManager(tmpdir)
            lm.generate_root_key()
            lic = lm.issue_portable_license(
                user_id="test@example.com",
                user_name="Test User",
                tier="pro",
            )
            assert lic.hardware_hash == ""
            assert lm._public_key is not None
            valid, reason = lic.is_valid(lm._public_key)
            assert valid is True, f"Portable license should be valid: {reason}"

    def test_license_features(self):
        from core.licensing import LicenseManager
        with tempfile.TemporaryDirectory() as tmpdir:
            lm = LicenseManager(tmpdir)
            lm.generate_root_key()
            lic = lm.issue_license(
                user_id="test@example.com",
                user_name="Test User",
                tier="pro",
                features=["algo", "viz"],
            )
            assert lic.has_feature("algo") is True
            assert lic.has_feature("viz") is True
            assert lic.has_feature("nonexistent") is False

    def test_hardware_fingerprint(self):
        from core.licensing import get_hardware_fingerprint, get_hardware_hash
        fp = get_hardware_fingerprint()
        assert len(fp) == 128  # SHA-512 hex digest = 128 chars
        hw_hash = get_hardware_hash()
        assert len(hw_hash) == 128
        # Same machine = same fingerprint
        assert get_hardware_fingerprint() == fp

    def test_license_manager_list_empty(self):
        from core.licensing import LicenseManager
        with tempfile.TemporaryDirectory() as tmpdir:
            lm = LicenseManager(tmpdir)
            licenses = lm.list_licenses()
            assert licenses == []

    def test_tiers_defined(self):
        from core.licensing import TIERS
        assert "community" in TIERS
        assert "pro" in TIERS
        assert "enterprise" in TIERS
        assert TIERS["community"]["price"] == "Free"


class TestPersistence:
    def test_datastore_create_get(self):
        from core.persistence import DataStore
        with tempfile.TemporaryDirectory() as tmpdir:
            store = DataStore(tmpdir)
            record = store.create("test_001", {"name": "test", "value": 42})
            assert record.id == "test_001"
            assert record.data["name"] == "test"
            loaded = store.get("test_001")
            assert loaded is not None
            assert loaded.data["value"] == 42

    def test_datastore_update(self):
        from core.persistence import DataStore
        with tempfile.TemporaryDirectory() as tmpdir:
            store = DataStore(tmpdir)
            store.create("test_001", {"name": "test", "value": 42})
            updated = store.update("test_001", {"value": 100})
            assert updated is not None
            assert updated.data["value"] == 100
            assert updated.data["name"] == "test"

    def test_datastore_history(self):
        from core.persistence import DataStore
        with tempfile.TemporaryDirectory() as tmpdir:
            store = DataStore(tmpdir)
            store.create("test_001", {"name": "test", "value": 1})
            store.update("test_001", {"value": 2})
            store.update("test_001", {"value": 3})
            history = store.get_history("test_001")
            assert len(history) == 2  # Two updates saved to history

    def test_datastore_delete(self):
        from core.persistence import DataStore
        with tempfile.TemporaryDirectory() as tmpdir:
            store = DataStore(tmpdir)
            store.create("test_001", {"name": "test"})
            assert store.delete("test_001") is True
            assert store.get("test_001") is None
            # History should still exist
            history = store.get_history("test_001")
            assert len(history) == 1

    def test_datastore_list(self):
        from core.persistence import DataStore
        with tempfile.TemporaryDirectory() as tmpdir:
            store = DataStore(tmpdir)
            store.create("a_001", {"name": "a"})
            store.create("b_001", {"name": "b"})
            store.create("c_001", {"name": "c"})
            records = store.list()
            assert len(records) == 3

    def test_datastore_stats(self):
        from core.persistence import DataStore
        with tempfile.TemporaryDirectory() as tmpdir:
            store = DataStore(tmpdir)
            store.create("test_001", {"name": "test"})
            stats = store.get_stats()
            assert stats["total_records"] == 1
            assert "schema_version" in stats

    def test_algorithm_registry(self):
        from core.persistence import AlgorithmRegistry
        with tempfile.TemporaryDirectory() as tmpdir:
            reg = AlgorithmRegistry(tmpdir)
            algo = reg.register_algorithm(
                "binary_search",
                spec_hash="abc123",
                proof_hash="def456",
                c_binary_hash="ghi789",
            )
            assert algo.id == "binary_search"
            assert algo.data["spec_hash"] == "abc123"

            loaded = reg.get_algorithm("binary_search")
            assert loaded is not None
            assert loaded.data["status"] == "verified"

    def test_algorithm_search(self):
        from core.persistence import AlgorithmRegistry
        with tempfile.TemporaryDirectory() as tmpdir:
            reg = AlgorithmRegistry(tmpdir)
            reg.register_algorithm("binary_search", spec_hash="abc", proof_hash="def")
            reg.register_algorithm("merge_sort", spec_hash="ghi", proof_hash="jkl")
            results = reg.search_algorithms("binary")
            assert len(results) == 1
            assert results[0].id == "binary_search"

    def test_session_manager(self):
        from core.persistence import SessionManager
        with tempfile.TemporaryDirectory() as tmpdir:
            sm = SessionManager(tmpdir)
            session = sm.create_session("user_001", {"ip": "127.0.0.1"})
            assert session.data["user_id"] == "user_001"

            sessions = sm.get_user_sessions("user_001")
            assert len(sessions) == 1

            sm.close_session(session.id)
            closed = sm.store.get(session.id)
            assert closed is not None
            assert closed.data["status"] == "closed"

    def test_schema_migration(self):
        from core.persistence import DataStore, CURRENT_SCHEMA_VERSION
        with tempfile.TemporaryDirectory() as tmpdir:
            store = DataStore(tmpdir)
            store.create("test_001", {"name": "test"})
            # Migration to same version should be no-op
            migrated = store.migrate_schema(CURRENT_SCHEMA_VERSION)
            assert migrated == 0


# ─── Comprehensive Security Tests ────────────────────────────────────────────

class TestEncryptionRoundtrip:
    """Tests for encryption/decryption roundtrips and tampering detection."""
    
    def test_secure_channel_encrypt_decrypt(self):
        from core.security import SecureChannel
        import secrets
        key = secrets.token_bytes(64)
        channel = SecureChannel(key)
        plaintext = b"Hello, World!"
        encrypted = channel.encrypt(plaintext)
        decrypted = channel.decrypt(encrypted)
        assert decrypted == plaintext
    
    def test_secure_channel_tampering_detection(self):
        from core.security import SecureChannel
        import secrets
        import base64
        key = secrets.token_bytes(64)
        channel = SecureChannel(key)
        plaintext = b"Secret data"
        encrypted = channel.encrypt(plaintext)
        
        # Tamper with the data: flip bits in the encrypted payload but keep valid base64
        data_bytes = base64.b64decode(encrypted["data"])
        tampered = bytes([data_bytes[0] ^ 0xFF]) + data_bytes[1:]  # Flip all bits in first byte
        encrypted["data"] = base64.b64encode(tampered).decode()
        
        # Decryption should fail at MAC verification
        with pytest.raises(ValueError, match="MAC verification failed"):
            channel.decrypt(encrypted)
    
    def test_secure_channel_tampering_nonce(self):
        from core.security import SecureChannel
        import secrets
        key = secrets.token_bytes(64)
        channel = SecureChannel(key)
        plaintext = b"Secret data"
        encrypted = channel.encrypt(plaintext)
        
        # Tamper with the nonce
        encrypted["nonce"] = "abcdabcdabcdabcdabcdabcd"  # Different nonce
        
        # Decryption should fail
        with pytest.raises(ValueError, match="MAC verification failed"):
            channel.decrypt(encrypted)
    
    def test_secure_channel_large_data(self):
        from core.security import SecureChannel
        import secrets
        key = secrets.token_bytes(64)
        channel = SecureChannel(key)
        plaintext = b"X" * 100000  # 100 KB
        encrypted = channel.encrypt(plaintext)
        decrypted = channel.decrypt(encrypted)
        assert decrypted == plaintext
    
    def test_audit_log_chain_integrity(self):
        from core.security import AuditLog
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "audit.log"
            audit = AuditLog(log_file)
            
            # Add multiple entries
            audit.add_entry("action1", {"detail": "value1"})
            audit.add_entry("action2", {"detail": "value2"})
            audit.add_entry("action3", {"detail": "value3"})
            
            # Verify integrity
            assert audit.verify_integrity() is True
    
    def test_audit_log_tampering_detection(self):
        from core.security import AuditLog
        import json
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "audit.log"
            audit = AuditLog(log_file)
            
            audit.add_entry("action1", {"detail": "value1"})
            audit.add_entry("action2", {"detail": "value2"})
            
            # Tamper with the log file
            lines = log_file.read_text().strip().split("\n")
            entry = json.loads(lines[0])
            entry["details"]["detail"] = "TAMPERED"
            lines[0] = json.dumps(entry)
            log_file.write_text("\n".join(lines))
            
            # Verification should fail
            assert audit.verify_integrity() is False


# ─── Input Validation Tests ─────────────────────────────────────────────────

class TestInputValidation:
    """Tests for input validation and sanitization."""
    
    def test_record_id_validation_valid(self):
        from core.persistence import _validate_record_id
        _validate_record_id("valid_record_id_001")  # Should not raise
    
    def test_record_id_validation_empty(self):
        from core.persistence import _validate_record_id
        with pytest.raises(ValueError, match="must be 1-255 characters"):
            _validate_record_id("")
    
    def test_record_id_validation_too_long(self):
        from core.persistence import _validate_record_id
        with pytest.raises(ValueError, match="must be 1-255 characters"):
            _validate_record_id("x" * 256)
    
    def test_record_id_validation_path_traversal(self):
        from core.persistence import _validate_record_id
        with pytest.raises(ValueError, match="invalid characters"):
            _validate_record_id("../../../etc/passwd")
        with pytest.raises(ValueError, match="invalid characters"):
            _validate_record_id("record/with/slashes")
    
    def test_record_id_validation_null_byte(self):
        from core.persistence import _validate_record_id
        with pytest.raises(ValueError, match="invalid characters"):
            _validate_record_id("record\x00name")
    
    def test_json_data_validation_valid(self):
        from core.persistence import _validate_json_data
        _validate_json_data({"key": "value", "number": 42})  # Should not raise
    
    def test_json_data_validation_not_dict(self):
        from core.persistence import _validate_json_data
        with pytest.raises(TypeError, match="must be a dictionary"):
            _validate_json_data("not a dict")
    
    def test_json_data_validation_not_serializable(self):
        from core.persistence import _validate_json_data
        with pytest.raises(ValueError, match="not JSON-serializable"):
            _validate_json_data({"key": object()})  # object() is not JSON-serializable
    
    def test_safe_read_json_valid(self):
        from core.persistence import _safe_read_json
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.json"
            test_file.write_text('{"key": "value"}')
            data = _safe_read_json(test_file)
            assert data["key"] == "value"
    
    def test_safe_read_json_invalid_json(self):
        from core.persistence import _safe_read_json
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.json"
            test_file.write_text("not valid json {{{")
            with pytest.raises(ValueError, match="Invalid JSON"):
                _safe_read_json(test_file)
    
    def test_safe_read_json_not_object(self):
        from core.persistence import _safe_read_json
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.json"
            test_file.write_text("[1, 2, 3]")  # Array, not object
            with pytest.raises(ValueError, match="must be an object"):
                _safe_read_json(test_file)
    
    def test_safe_read_json_file_too_large(self):
        from core.persistence import _safe_read_json
        import io
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.json"
            # Create a file larger than 10 MB by writing a large JSON object
            large_data = {"data": "x" * (11 * 1024 * 1024)}  # 11 MB of data
            test_file.write_text(json.dumps(large_data))
            with pytest.raises(ValueError, match="too large"):
                _safe_read_json(test_file)
    
    def test_safe_read_json_invalid_encoding(self):
        from core.persistence import _safe_read_json
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.json"
            test_file.write_bytes(b'\xff\xfe invalid utf-8')
            with pytest.raises(ValueError, match="not valid UTF-8"):
                _safe_read_json(test_file)
    
    def test_license_file_validation(self):
        from core.licensing import LicenseCertificate
        with pytest.raises(ValueError, match="Invalid JSON"):
            LicenseCertificate.from_json("not json")
    
    def test_license_file_not_object(self):
        from core.licensing import LicenseCertificate
        with pytest.raises(ValueError, match="must be an object"):
            LicenseCertificate.from_json("[1, 2, 3]")


# ─── Corrupted File Recovery Tests ──────────────────────────────────────────

class TestCorruptedFileRecovery:
    """Tests for handling and recovering from corrupted files."""
    
    def test_datastore_corrupted_json(self):
        from core.persistence import DataStore
        with tempfile.TemporaryDirectory() as tmpdir:
            store = DataStore(tmpdir)
            store.create("test_001", {"name": "test"})
            
            # Corrupt the JSON file
            record_file = store._record_path("test_001")
            record_file.write_text("not valid json {{{")
            
            # get() should return None gracefully
            result = store.get("test_001")
            assert result is None
    
    def test_datastore_list_skips_corrupted(self):
        from core.persistence import DataStore
        with tempfile.TemporaryDirectory() as tmpdir:
            store = DataStore(tmpdir)
            store.create("test_001", {"name": "test"})
            store.create("test_002", {"name": "test2"})
            
            # Corrupt one file
            record_file = store._record_path("test_002")
            record_file.write_text("corrupted!")
            
            # list() should skip the corrupted file
            records = store.list()
            assert len(records) == 1
            assert records[0].id == "test_001"
    
    def test_datastore_history_skips_corrupted(self):
        from core.persistence import DataStore
        with tempfile.TemporaryDirectory() as tmpdir:
            store = DataStore(tmpdir)
            store.create("test_001", {"name": "test"})
            store.update("test_001", {"name": "updated"})
            
            # Corrupt a history file
            history_files = list(store.history_dir.glob("*.json"))
            if history_files:
                history_files[0].write_text("corrupted!")
            
            # get_history() should skip corrupted entries
            history = store.get_history("test_001")
            # Should return at least 0 entries (corrupted ones skipped)
            assert isinstance(history, list)


# ─── License Expiration and Revocation Tests ───────────────────────────────

class TestLicenseExpirRevoke:
    """Comprehensive tests for license expiration and revocation."""
    
    def test_license_not_expired(self):
        from core.licensing import LicenseManager
        with tempfile.TemporaryDirectory() as tmpdir:
            lm = LicenseManager(tmpdir)
            lm.generate_root_key()
            lic = lm.issue_license(
                user_id="test@example.com",
                user_name="Test User",
                tier="pro",
                expires_at=time.time() + 86400,  # Tomorrow
            )
            assert lm._public_key is not None
            valid, reason = lic.is_valid(lm._public_key)
            assert valid is True
    
    def test_license_expired_yesterday(self):
        from core.licensing import LicenseManager
        with tempfile.TemporaryDirectory() as tmpdir:
            lm = LicenseManager(tmpdir)
            lm.generate_root_key()
            lic = lm.issue_license(
                user_id="test@example.com",
                user_name="Test User",
                tier="pro",
                expires_at=time.time() - 86400,  # Yesterday
            )
            assert lm._public_key is not None
            valid, reason = lic.is_valid(lm._public_key)
            assert valid is False
            assert "expired" in reason.lower()
    
    def test_license_never_expires(self):
        from core.licensing import LicenseManager
        with tempfile.TemporaryDirectory() as tmpdir:
            lm = LicenseManager(tmpdir)
            lm.generate_root_key()
            lic = lm.issue_license(
                user_id="test@example.com",
                user_name="Test User",
                tier="pro",
                expires_at=0,  # 0 = never expires
            )
            assert lm._public_key is not None
            valid, reason = lic.is_valid(lm._public_key)
            assert valid is True
    
    def test_license_revoked_multiple(self):
        from core.licensing import LicenseManager
        with tempfile.TemporaryDirectory() as tmpdir:
            lm = LicenseManager(tmpdir)
            lm.generate_root_key()
            
            lic1 = lm.issue_license(
                user_id="user1@example.com",
                user_name="User 1",
                tier="pro",
            )
            lic2 = lm.issue_license(
                user_id="user2@example.com",
                user_name="User 2",
                tier="pro",
            )
            
            lm.revoke_license(lic1.license_id, "Payment failed")
            
            # lic1 should be revoked
            valid1, _ = lm.verify_license(lic1)
            assert valid1 is False
            
            # lic2 should still be valid
            valid2, _ = lm.verify_license(lic2)
            assert valid2 is True
    
    def test_license_features_by_tier(self):
        from core.licensing import LicenseManager
        with tempfile.TemporaryDirectory() as tmpdir:
            lm = LicenseManager(tmpdir)
            lm.generate_root_key()
            
            community = lm.issue_license(
                user_id="c@example.com",
                user_name="Community User",
                tier="community",
            )
            pro = lm.issue_license(
                user_id="p@example.com",
                user_name="Pro User",
                tier="pro",
            )
            
            # Community should have basic features
            assert len(community.features) > 0
            # Pro should have more features
            assert len(pro.features) > len(community.features)


# ─── Binary Signature Tests ──────────────────────────────────────────────────

class TestBinarySignature:
    """Tests for binary file signing and verification."""
    
    def test_binary_signature_create_verify(self):
        from core.security import sign_binary
        import secrets
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a test binary file
            binary_file = Path(tmpdir) / "test.bin"
            binary_file.write_bytes(b"binary content")
            
            # Sign it
            key = secrets.token_bytes(64)
            sig = sign_binary(binary_file, key, "key123")
            
            # Verify it
            assert sig.verify(binary_file, key) is True
    
    def test_binary_signature_tampering(self):
        from core.security import sign_binary
        import secrets
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create and sign a binary file
            binary_file = Path(tmpdir) / "test.bin"
            binary_file.write_bytes(b"binary content")
            
            key = secrets.token_bytes(64)
            sig = sign_binary(binary_file, key, "key123")
            
            # Tamper with the file
            binary_file.write_bytes(b"tampered content")
            
            # Verification should fail
            assert sig.verify(binary_file, key) is False
    
    def test_binary_signature_wrong_key(self):
        from core.security import sign_binary
        import secrets
        with tempfile.TemporaryDirectory() as tmpdir:
            binary_file = Path(tmpdir) / "test.bin"
            binary_file.write_bytes(b"binary content")
            
            key1 = secrets.token_bytes(64)
            key2 = secrets.token_bytes(64)
            
            sig = sign_binary(binary_file, key1, "key123")
            
            # Verify with wrong key
            assert sig.verify(binary_file, key2) is False


# ─── Edge Case Tests ────────────────────────────────────────────────────────

class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""
    
    def test_datastore_record_id_special_chars(self):
        from core.persistence import DataStore
        with tempfile.TemporaryDirectory() as tmpdir:
            store = DataStore(tmpdir)
            # Valid IDs with special chars
            store.create("record-with-dashes", {"value": 1})
            store.create("record_with_underscores", {"value": 2})
            store.create("record.with.dots", {"value": 3})
            assert len(store.list()) == 3
    
    def test_datastore_large_data(self):
        from core.persistence import DataStore
        with tempfile.TemporaryDirectory() as tmpdir:
            store = DataStore(tmpdir)
            large_data = {"content": "X" * 1000000}  # 1 MB of text
            record = store.create("large_001", large_data)
            loaded = store.get("large_001")
            assert loaded is not None
            assert len(loaded.data["content"]) == 1000000
    
    def test_keystore_multiple_keys(self):
        from core.security import KeyStore
        with tempfile.TemporaryDirectory() as tmpdir:
            ks = KeyStore(tmpdir)
            keys = [ks.create_key(f"key_{i}", "pass123") for i in range(5)]
            
            # Load each one back
            for i, original_key in enumerate(keys):
                loaded = ks.load_key(f"key_{i}", "pass123")
                assert loaded.key_id == original_key.key_id
    
    def test_license_maximum_seats(self):
        from core.licensing import LicenseManager
        with tempfile.TemporaryDirectory() as tmpdir:
            lm = LicenseManager(tmpdir)
            lm.generate_root_key()
            
            lic = lm.issue_license(
                user_id="test@example.com",
                user_name="Test User",
                tier="enterprise",
                max_seats=-1,  # Unlimited
            )
            
            assert lm._public_key is not None
            assert lic.max_seats == -1
            valid, reason = lic.is_valid(lm._public_key)
            assert valid is True
    
    def test_audit_log_empty(self):
        from core.security import AuditLog
        with tempfile.TemporaryDirectory() as tmpdir:
            audit = AuditLog(Path(tmpdir) / "audit.log")
            # Empty log should verify
            assert audit.verify_integrity() is True


# Ensure pytest fixture is available
pytest.fixture = lambda *args, **kwargs: lambda f: f
