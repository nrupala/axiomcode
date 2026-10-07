"""Product-finishing behavior tests: badge embed, QR rendering, registry HTTP.

Every test here asserts BEHAVIOR, not files: a revoked certificate's badge
must render revoked, a tampered certificate's badge must not claim
certified, QR output must be a real QR encoding the verification URL, and
the HTTP surface must be read-only.
"""

import json
import threading
import time
import urllib.request
from pathlib import Path
from wsgiref.simple_server import make_server

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
        tier="certified",
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


@pytest.fixture()
def registry_dir(tmp_path):
    from core.registry import CertificateRegistry

    reg = CertificateRegistry(tmp_path / "registry")
    cert, _ = _signed_cert()
    reg.publish(cert)
    revoked_cert, _ = _signed_cert(product_name="OldWidget", artifact_version="0.9.0")
    reg.publish(revoked_cert)
    reg.revoke(revoked_cert.serial, "superseded by 1.0.0")
    expired_cert, _ = _signed_cert(
        product_name="AncientLib",
        artifact_version="0.1.0",
        expires_at=time.time() - 10,
    )
    reg.publish(expired_cert)
    return tmp_path / "registry", cert, revoked_cert, expired_cert


BASE = "https://registry.example.com"


class TestQR:
    def test_png_is_real_png(self):
        from core.qr import render_qr_png

        png = render_qr_png("https://registry.example.com/cert/AXC-1")
        assert png[:8] == b"\x89PNG\r\n\x1a\n"
        assert len(png) > 200

    def test_svg_is_well_formed(self):
        import xml.etree.ElementTree as ET

        from core.qr import render_qr_svg

        svg = render_qr_svg("https://registry.example.com/cert/AXC-1")
        root = ET.fromstring(svg)
        assert root.tag.endswith("svg")

    def test_empty_payload_refused(self):
        from core.qr import render_qr_png, render_qr_svg

        with pytest.raises(ValueError):
            render_qr_png("")
        with pytest.raises(ValueError):
            render_qr_svg("   ")

    def test_different_payloads_different_codes(self):
        from core.qr import render_qr_png

        a = render_qr_png("https://registry.example.com/cert/AXC-1")
        b = render_qr_png("https://registry.example.com/cert/AXC-2")
        assert a != b

    def test_verification_url(self):
        from core.qr import verification_url

        assert verification_url("AXC-1", "https://r.example.com/") == "https://r.example.com/cert/AXC-1"
        with pytest.raises(ValueError):
            verification_url("", "https://r.example.com")
        with pytest.raises(ValueError):
            verification_url("AXC-1", "")

    def test_qr_for_certificate_prefers_signed_payload(self):
        from core.qr import qr_for_certificate

        cert, _ = _signed_cert(qr_payload="https://registry.example.com/cert/AXC-SPECIAL")
        png = qr_for_certificate(cert, "https://other.example.com")
        assert png[:8] == b"\x89PNG\r\n\x1a\n"
        # The signed payload wins over the base URL — it is covered by the signature.
        from core.qr import render_qr_png

        assert png == render_qr_png("https://registry.example.com/cert/AXC-SPECIAL")

    def test_qr_for_certificate_falls_back_to_serial_url(self):
        from core.qr import qr_for_certificate, render_qr_png, verification_url

        cert, _ = _signed_cert()
        png = qr_for_certificate(cert, BASE)
        assert png == render_qr_png(verification_url(cert.serial, BASE))


class TestBadge:
    def test_active_certified_badge_is_version_pinned(self, registry_dir):
        from core.badge import badge_data, render_badge_svg

        reg_dir, cert, _, _ = registry_dir
        from core.registry import CertificateRegistry

        data = badge_data(cert.serial, CertificateRegistry(reg_dir), BASE)
        assert data["status"] == "certified"
        assert data["message"] == "Certified v1.2.3"
        assert "1.2.3" in data["message"]  # never a bare "Certified"
        svg = render_badge_svg(data)
        assert "Certified v1.2.3" in svg
        assert svg.startswith("<svg")

    def test_revoked_badge_shows_revoked(self, registry_dir):
        from core.badge import badge_data, render_badge_svg
        from core.registry import CertificateRegistry

        reg_dir, _, revoked_cert, _ = registry_dir
        data = badge_data(revoked_cert.serial, CertificateRegistry(reg_dir), BASE)
        assert data["status"] == "revoked"
        assert data["message"] == "Revoked"
        svg = render_badge_svg(data)
        assert "Revoked" in svg
        assert "Certified" not in svg

    def test_expired_badge_shows_expired(self, registry_dir):
        from core.badge import badge_data
        from core.registry import CertificateRegistry

        reg_dir, _, _, expired_cert = registry_dir
        data = badge_data(expired_cert.serial, CertificateRegistry(reg_dir), BASE)
        assert data["status"] == "expired"
        assert data["message"] == "Expired"

    def test_unknown_serial_badge(self, registry_dir):
        from core.badge import badge_data, render_badge_svg
        from core.registry import CertificateRegistry

        reg_dir, _, _, _ = registry_dir
        data = badge_data("AXC-NOPE-000000000000", CertificateRegistry(reg_dir), BASE)
        assert data["status"] == "unknown"
        svg = render_badge_svg(data)
        assert "Unknown" in svg

    def test_tampered_cert_badge_does_not_claim_certified(self, registry_dir):
        from core.badge import badge_data
        from core.registry import CertificateRegistry

        reg_dir, cert, _, _ = registry_dir
        # Tamper with the stored file (keep JSON valid, break the signature).
        path = reg_dir / "certs" / f"{cert.serial}.json"
        doc = json.loads(path.read_text())
        doc["product_name"] = "EvilWidget"
        path.write_text(json.dumps(doc))
        data = badge_data(cert.serial, CertificateRegistry(reg_dir), BASE)
        assert data["status"] == "invalid"
        assert "Certified" not in data["message"]

    def test_snippet_points_at_live_badge_and_cert_page(self):
        from core.badge import badge_snippet

        snip = badge_snippet("AXC-1", BASE)
        assert f"{BASE}/badge/AXC-1.svg" in snip["markdown"]
        assert f"{BASE}/cert/AXC-1" in snip["markdown"]
        assert f"{BASE}/badge/AXC-1.svg" in snip["html"]
        assert f"{BASE}/cert/AXC-1" in snip["html"]


@pytest.fixture()
def http_server(registry_dir):
    import sys

    sys.path.insert(0, str(Path(__file__).parent.parent / "services"))
    from registry_app import create_app

    reg_dir, cert, revoked_cert, expired_cert = registry_dir
    app = create_app(str(reg_dir), BASE)
    httpd = make_server("127.0.0.1", 0, app)
    port = httpd.server_address[1]
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    base = f"http://127.0.0.1:{port}"
    yield base, cert, revoked_cert, expired_cert
    httpd.shutdown()


def _get(base, path, method="GET"):
    req = urllib.request.Request(base + path, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, r.headers.get("Content-Type", ""), r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get("Content-Type", ""), e.read()


class TestRegistryHTTP:
    def test_health(self, http_server):
        base, *_ = http_server
        status, ctype, body = _get(base, "/health")
        assert status == 200
        assert json.loads(body)["ok"] is True

    def test_active_list_excludes_revoked_and_expired(self, http_server):
        base, cert, revoked_cert, expired_cert = http_server
        status, _, body = _get(base, "/api/registry")
        assert status == 200
        serials = [c["serial"] for c in json.loads(body)["certificates"]]
        assert cert.serial in serials
        assert revoked_cert.serial not in serials
        assert expired_cert.serial not in serials

    def test_full_log_includes_revoked(self, http_server):
        base, cert, revoked_cert, _ = http_server
        status, _, body = _get(base, "/api/registry?status=all")
        assert status == 200
        by_serial = {c["serial"]: c for c in json.loads(body)["certificates"]}
        assert by_serial[revoked_cert.serial]["status"] == "revoked"
        assert by_serial[cert.serial]["status"] == "active"

    def test_cert_lookup_is_agent_verifiable(self, http_server):
        base, cert, *_ = http_server
        status, _, body = _get(base, f"/api/cert/{cert.serial}")
        assert status == 200
        doc = json.loads(body)
        assert doc["status"] == "active"
        assert doc["signature"]  # Ed25519 signature present
        assert doc["verify_key"]  # public key present — verify without shared secret
        assert doc["artifact_version"] == "1.2.3"

    def test_cert_lookup_unknown_serial_404(self, http_server):
        base, *_ = http_server
        status, _, _ = _get(base, "/api/cert/AXC-NOPE-000000000000")
        assert status == 404

    def test_cert_lookup_rejects_path_traversal(self, http_server):
        base, *_ = http_server
        status, _, _ = _get(base, "/api/cert/..%2F..%2Fetc")
        assert status in (400, 404)

    def test_badge_endpoint_live_status(self, http_server):
        base, cert, revoked_cert, _ = http_server
        status, ctype, body = _get(base, f"/badge/{cert.serial}.svg")
        assert status == 200
        assert "image/svg+xml" in ctype
        assert b"Certified v1.2.3" in body
        status, _, body = _get(base, f"/badge/{revoked_cert.serial}.svg")
        assert status == 200
        assert b"Revoked" in body
        assert b"Certified" not in body

    def test_qr_endpoint(self, http_server):
        base, cert, *_ = http_server
        status, ctype, body = _get(base, f"/qr/{cert.serial}.png")
        assert status == 200
        assert "image/png" in ctype
        assert body[:8] == b"\x89PNG\r\n\x1a\n"

    def test_human_cert_page(self, http_server):
        base, cert, *_ = http_server
        status, ctype, body = _get(base, f"/cert/{cert.serial}")
        assert status == 200
        assert "text/html" in ctype
        assert cert.serial.encode() in body
        assert b"ACTIVE" in body

    def test_read_only_post_rejected(self, http_server):
        base, *_ = http_server
        status, _, _ = _get(base, "/api/registry", method="POST")
        assert status == 405
        status, _, _ = _get(base, "/api/cert/whatever", method="DELETE")
        assert status == 405

    def test_storefront_lists_active(self, http_server):
        base, cert, *_ = http_server
        status, _, body = _get(base, "/")
        assert status == 200
        assert cert.serial.encode() in body
