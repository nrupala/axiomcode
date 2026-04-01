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
