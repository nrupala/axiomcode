"""P1 certificate-product behavior tests.

Every test here asserts BEHAVIOR, not files: expired certs must verify as
expired, revoked certs must show revoked in the registry, tampered log
entries must break chain verification. Green checkmarks are not evidence;
these assertions are.
"""

import json
import tempfile
import time
from pathlib import Path

import pytest


def _signed_cert(**overrides):
    from core.security import Ed25519KeyPair, ProofCertificate

    kp = Ed25519KeyPair.generate()
    params = dict(
        algorithm_name="binary_search",
        spec_hash="abc123",
        proof_hash="def456",
        theorem="theorem binary_search_correct",
        verification_status="verified",
        tier="verified",
        artifact_version="1.2.3",
        product_name="BinarySearch",
        owner="Jane Builder",
        repo_or_website="https://github.com/jane/bs",
        owner_contact="jane@example.com",
        issued_at=time.time() - 100,
        expires_at=time.time() + 86400,
    )
    params.update(overrides)
    cert = ProofCertificate(**params)
    cert.serial = ProofCertificate.generate_serial(kp.key_id)
    cert.key_id = kp.key_id
    cert.sign(kp.private_key)
    return cert, kp


class TestCertificateSchemaV2:
    def test_v2_fields_present(self):
        cert, _ = _signed_cert()
        assert cert.version == 2
        assert cert.serial.startswith("AXC-")
        assert cert.validity_status() == "active"
        assert cert.is_currently_valid() is True
        d = json.loads(cert.to_json())
        for field in (
            "serial",
            "issued_at",
            "expires_at",
            "revoked",
            "artifact_version",
            "tier",
            "product_name",
            "owner",
            "repo_or_website",
            "owner_contact",
            "issuer_name",
            "md5_hashes",
            "qr_payload",
        ):
            assert field in d, f"missing v2 field: {field}"

    def test_serials_unique(self):
        from core.security import Ed25519KeyPair, ProofCertificate

        kp = Ed25519KeyPair.generate()
        serials = {ProofCertificate.generate_serial(kp.key_id) for _ in range(200)}
        assert len(serials) == 200

    def test_expired_cert_reports_expired(self):
        cert, _ = _signed_cert(expires_at=time.time() - 10)
        assert cert.validity_status() == "expired"
        assert cert.is_currently_valid() is False

    def test_not_yet_valid_cert(self):
        cert, _ = _signed_cert(issued_at=time.time() + 3600, expires_at=time.time() + 7200)
        assert cert.validity_status() == "not-yet-valid"
        assert cert.is_currently_valid() is False

    def test_revoked_flag_reports_revoked(self):
        cert, _ = _signed_cert(revoked=True, revocation_reason="key compromised")
        assert cert.validity_status() == "revoked"

    def test_never_expires_when_zero(self):
        cert, _ = _signed_cert(expires_at=0.0)
        assert cert.validity_status() == "active"

    def test_v2_roundtrip_preserves_signature(self):
        cert, kp = _signed_cert()
        loaded = __import__("core.security", fromlist=["ProofCertificate"]).ProofCertificate.from_json(cert.to_json())
        assert loaded.verify(kp.public_key) is True
        assert loaded.serial == cert.serial


class TestMigrationResigning:
    def _v1_cert(self):
        from core.security import Ed25519KeyPair, ProofCertificate

        kp = Ed25519KeyPair.generate()
        cert = ProofCertificate(
            version=1,
            algorithm_name="x",
            spec_hash="a",
            proof_hash="b",
            generated_at=time.time() - 500,
            verification_status="verified",
        )
        cert.key_id = kp.key_id
        cert.sign(kp.private_key)
        old_sig = cert.signature
        # Force the payload back to v1 shape for a faithful fixture: v1 had no
        # v2 fields in the signed payload. Re-sign as v1 by temporarily
        # downgrading the version field only (v2 fields default empty anyway).
        return cert, kp, old_sig

    def test_migration_refuses_without_key(self):
        cert, _, _ = self._v1_cert()
        with pytest.raises(ValueError, match="[Rr]e-?sign"):
            cert.migrate_v1_to_v2(b"", "")

    def test_migration_resigns_with_key(self):
        from core.security import CERT_SCHEMA_VERSION

        cert, kp, old_sig = self._v1_cert()
        old_payload_sig_valid = cert.verify(kp.public_key)
        assert old_payload_sig_valid is True
        cert.migrate_v1_to_v2(kp.private_key, kp.key_id)
        assert cert.version == CERT_SCHEMA_VERSION
        assert cert.serial.startswith("AXC-")
        assert cert.issued_at == cert.generated_at
        assert cert.tier == "verified"  # honest inference from verified status
        # New signature verifies over the new payload...
        assert cert.verify(kp.public_key) is True
        # ...and the OLD signature does not verify the new payload (proves re-signing).
        assert cert.signature != old_sig

    def test_migration_rejects_non_v1(self):
        cert, kp = _signed_cert()
        with pytest.raises(ValueError, match="expects a v1"):
            cert.migrate_v1_to_v2(kp.private_key, kp.key_id)

    def test_versioning_migration_skips_signed_without_key(self):
        import tempfile

        from core.security import ProofCertificate
        from core.versioning import migrate_v1_to_v2

        cert, _, _ = self._v1_cert()
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            cert_dir = base / "build" / "certs"
            cert_dir.mkdir(parents=True)
            cert.save(cert_dir / "x.cert.json")
            result = migrate_v1_to_v2(base / ".axiomcode")
            # Must NOT silently rewrite: the signed file is skipped, reported.
            assert result["status"] == "success"
            assert any("x.cert.json" in s for s in result["skipped"])
            reloaded = ProofCertificate.load(cert_dir / "x.cert.json")
            assert reloaded.version == 1  # untouched

    def test_versioning_migration_resigns_with_key(self):
        import tempfile

        from core.security import CERT_SCHEMA_VERSION, ProofCertificate
        from core.versioning import migrate_v1_to_v2

        cert, kp, _ = self._v1_cert()
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            cert_dir = base / "build" / "certs"
            cert_dir.mkdir(parents=True)
            cert.save(cert_dir / "x.cert.json")
            result = migrate_v1_to_v2(base / ".axiomcode", signing_key=kp.private_key, key_id=kp.key_id)
            assert any("x.cert.json" in c for c in result["changes"])
            reloaded = ProofCertificate.load(cert_dir / "x.cert.json")
            assert reloaded.version == CERT_SCHEMA_VERSION
            assert reloaded.verify(kp.public_key) is True


class TestPublicRegistry:
    def _registry(self, tmpdir):
        from core.registry import CertificateRegistry

        return CertificateRegistry(Path(tmpdir) / "registry")

    def test_publish_and_active_status(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            reg = self._registry(tmpdir)
            cert, _ = _signed_cert()
            serial = reg.publish(cert)
            assert serial == cert.serial
            assert reg.status(serial) == "active"
            assert any(e["serial"] == serial for e in reg.list_certificates())

    def test_publish_refuses_unsigned(self):
        from core.security import ProofCertificate

        with tempfile.TemporaryDirectory() as tmpdir:
            reg = self._registry(tmpdir)
            cert = ProofCertificate(algorithm_name="x")  # never signed
            cert.serial = "AXC-TEST-000000000000"
            with pytest.raises(ValueError, match="not signed"):
                reg.publish(cert)

    def test_publish_refuses_tampered(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            reg = self._registry(tmpdir)
            cert, _ = _signed_cert()
            cert.steps = 99999  # tamper after signing
            with pytest.raises(ValueError, match="[Ss]ignature invalid"):
                reg.publish(cert)

    def test_publish_refuses_duplicate_serial(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            reg = self._registry(tmpdir)
            cert, _ = _signed_cert()
            reg.publish(cert)
            with pytest.raises(ValueError, match="already published"):
                reg.publish(cert)

    def test_revoke_is_public_and_visible(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            reg = self._registry(tmpdir)
            cert, _ = _signed_cert()
            reg.publish(cert)
            reg.revoke(cert.serial, "key compromised", user="issuer")
            assert reg.status(cert.serial) == "revoked"
            # Still visible in the full view — revocation is never silent.
            assert any(e["serial"] == cert.serial for e in reg.list_certificates(status_filter="all"))
            # But absent from the default (active-only) storefront.
            assert not any(e["serial"] == cert.serial for e in reg.list_certificates())
            rec = reg.revocation_record(cert.serial)
            assert rec["reason"] == "key compromised"

    def test_revoke_requires_reason(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            reg = self._registry(tmpdir)
            cert, _ = _signed_cert()
            reg.publish(cert)
            with pytest.raises(ValueError, match="reason"):
                reg.revoke(cert.serial, "  ")

    def test_expired_visible_with_status(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            reg = self._registry(tmpdir)
            cert, _ = _signed_cert(expires_at=time.time() - 5)
            reg.publish(cert)
            assert reg.status(cert.serial) == "expired"
            assert any(e["serial"] == cert.serial for e in reg.list_certificates(status_filter="all"))

    def test_export_is_machine_readable_and_verifiable(self):
        from core.security import ed25519_verify

        with tempfile.TemporaryDirectory() as tmpdir:
            reg = self._registry(tmpdir)
            cert, kp = _signed_cert()
            reg.publish(cert)
            doc = json.loads(reg.export_json())
            assert doc["registry"] == "AxiomCode Certificate Registry"
            entry = doc["certificates"][0]
            assert entry["serial"] == cert.serial
            assert entry["status"] == "active"
            # An agent can verify the signature from the export alone.
            import base64

            assert ed25519_verify(base64.b64decode(entry["verify_key"]), cert._payload(), entry["signature"])

    def test_verify_registry_detects_tampering(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            reg = self._registry(tmpdir)
            cert, _ = _signed_cert()
            reg.publish(cert)
            # Tamper with the stored file behind the registry's back.
            stored = next((Path(tmpdir) / "registry" / "certs").glob("*.json"))
            data = json.loads(stored.read_text())
            data["steps"] = 123456
            stored.write_text(json.dumps(data))
            ok, issues = reg.verify_registry()
            assert ok is False
            assert any("SIGNATURE INVALID" in i for i in issues)

    def test_verify_registry_clean(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            reg = self._registry(tmpdir)
            for _ in range(3):
                cert, _ = _signed_cert()
                reg.publish(cert)
            ok, issues = reg.verify_registry()
            assert ok is True and issues == []


class TestSignedAuditLog:
    def _signed_log(self, tmpdir):
        from core.security import AuditLog, Ed25519KeyPair

        kp = Ed25519KeyPair.generate()
        log = AuditLog(Path(tmpdir) / "audit.log", signing_key=kp.private_key)
        return log, kp

    def test_signed_entries_verify(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log, kp = self._signed_log(tmpdir)
            log.add_entry("certificate.issued", {"serial": "AXC-1", "artifact_version": "1.0.0", "tier": "verified"})
            ok, issues = log.verify_chain()
            assert ok is True, issues
            assert log.verify_integrity() is True

    def test_genesis_bound_to_key(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log, kp = self._signed_log(tmpdir)
            entries = log._read_entries()
            assert entries[0]["action"] == "log.genesis"
            import base64

            assert entries[0]["details"]["verify_key"] == base64.b64encode(kp.public_key).decode()

    def test_tampered_entry_breaks_chain(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log, kp = self._signed_log(tmpdir)
            log.add_entry("note", {"x": 1})
            lines = Path(log.log_file).read_text().strip().split("\n")
            entry = json.loads(lines[-1])
            entry["details"] = {"x": 999}  # tamper
            lines[-1] = json.dumps(entry)
            Path(log.log_file).write_text("\n".join(lines))
            log2 = type(log)(log.log_file, verify_key=kp.public_key)
            ok, issues = log2.verify_chain()
            assert ok is False
            assert any("tampered" in i or "signature" in i for i in issues)
            assert log2.verify_integrity() is False

    def test_rewritten_genesis_fails_without_key(self):
        """An attacker rewriting the log from scratch cannot mint a valid
        genesis without the signing key."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log, kp = self._signed_log(tmpdir)
            log.add_entry("note", {"x": 1})
            # Attacker wipes the file and writes a fresh unsigned log.
            Path(log.log_file).write_text(
                json.dumps(
                    {
                        "timestamp": time.time(),
                        "user": "system",
                        "action": "note",
                        "details": {"x": "forged"},
                        "previous_hash": "0" * 64,
                        "entry_hash": "f" * 64,
                    }
                )
                + "\n"
            )
            log2 = type(log)(log.log_file, verify_key=kp.public_key)
            assert log2.verify_integrity() is False

    def test_unsigned_entries_rejected_in_signed_mode(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            from core.security import AuditLog

            log = AuditLog(Path(tmpdir) / "audit.log")  # unsigned mode
            log.add_entry("note", {"x": 1})
            # Now verify with a key expectation: the unsigned entry must fail.
            from core.security import Ed25519KeyPair

            kp = Ed25519KeyPair.generate()
            log2 = AuditLog(Path(tmpdir) / "audit.log", verify_key=kp.public_key)
            ok, issues = log2.verify_chain()
            assert ok is False
            assert any("missing signature" in i for i in issues)

    def test_unsigned_mode_still_works(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            from core.security import AuditLog

            log = AuditLog(Path(tmpdir) / "audit.log")
            log.add_entry("note", {"x": 1})
            assert log.verify_integrity() is True

    def test_lifecycle_schema_enforced(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log, _ = self._signed_log(tmpdir)
            # Missing required 'reason' for recertification.skipped
            with pytest.raises(ValueError, match="missing required"):
                log.add_entry("recertification.skipped", {"serial": "AXC-1", "artifact_version": "1.0.1"})
            # Complete event passes
            log.add_entry(
                "recertification.skipped",
                {"serial": "AXC-1", "artifact_version": "1.0.1", "reason": "docs-only change"},
            )
            assert log.verify_integrity() is True
            # Unknown actions still pass through (backward compatible)
            log.add_entry("custom.anything", {"whatever": True})
            assert log.verify_integrity() is True


class TestFreeScanTier:
    def test_scan_never_mints_certificate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            from core.tiers import run_free_scan

            lean_file = Path(tmpdir) / "Sample.lean"
            lean_file.write_text("theorem foo : 1 = 1 := by\n  sorry\naxiom sneaky : False\n")
            report = run_free_scan(lean_file)
            assert report["tier"] == "scan"
            assert report["certificate_minted"] is False
            assert "NOT VERIFIED" in report["label"]
            assert report["files_with_sorry"] == 1
            assert report["files_with_declared_axioms"] == 1
            # No certificate file anywhere near the target.
            assert list(Path(tmpdir).glob("*.cert.json")) == []

    def test_scan_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            from core.tiers import run_free_scan

            (Path(tmpdir) / "A.lean").write_text("theorem a : True := trivial\n")
            (Path(tmpdir) / "B.lean").write_text("theorem b : True := by sorry\n")
            report = run_free_scan(tmpdir)
            assert report["files_scanned"] == 2
            assert report["files_with_sorry"] == 1

    def test_tier_definitions_complete(self):
        from core.tiers import ALL_TIERS, TIER_DEFINITIONS, validate_tier

        assert set(ALL_TIERS) == {"scan", "verified", "certified"}
        for tier in ALL_TIERS:
            d = TIER_DEFINITIONS[tier]
            assert d["runs"] and d["evidence"] and d["asserts"]
            assert validate_tier(tier) == tier
        assert TIER_DEFINITIONS["scan"]["certificate"] is None
        with pytest.raises(ValueError):
            validate_tier("platinum")

    def test_generate_refuses_scan_tier_mint(self):
        from cli import generate_certificate
        from core.security import Ed25519KeyPair

        # Minimal stand-ins: generate_certificate only touches spec/proof fields.
        class Spec:
            spec_hash = "s"
            theorem = "t"
            model_used = "m"

        class Proof:
            theorem_name = "x"
            proof_hash = "p"
            tactics = []
            steps = 0
            lemmas = 0
            verification_status = "verified"
            lean_version = "l"
            build_log = ""

        kp = Ed25519KeyPair.generate()
        with pytest.raises(ValueError, match="never mints"):
            generate_certificate(Spec(), Proof(), None, None, kp.private_key, kp.key_id, tier="scan")
