"""Wiring — verify_api (REST) and mcp_server issue/verify via Ed25519
and persist through the durable store. The Lean prover is stubbed:
these tests prove the CA/store wiring, not Lean itself."""

import os
from pathlib import Path

import ca
import mcp_server
import pytest
import verify_api
from fastapi.testclient import TestClient

CODE = "theorem t : True := trivial"


def _fake_search(writer, proj, code, *args, **kwargs):
    writer(code)
    return True, code, 1, "stubbed prover log"


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setattr(verify_api, "iterative_proof_search", _fake_search)
    monkeypatch.setattr(verify_api, "lean_version", lambda: "lean-test")
    return TestClient(verify_api.app)


def _work_root_leftovers(prefix):
    root = Path(os.environ["AXIOMCODE_WORK_ROOT"])
    return [p.name for p in root.iterdir() if p.name.startswith(prefix)]


def test_rest_end_to_end(client):
    r = client.post("/verify", json={"code": CODE})
    assert r.status_code == 200
    body = r.json()
    assert body["verified"] is True
    cert = body["certificate"]
    assert cert["alg"] == "Ed25519" and cert["version"] == 2

    # temp Lean project cleaned up by the finally block
    assert _work_root_leftovers("ax-api-") == []

    # cert persisted in the store
    assert verify_api.STORE.get_cert(cert["serial"]) == cert

    # published keys endpoint serves the payload for this CA
    keys = client.get("/.well-known/axiomcode-keys.json")
    assert keys.status_code == 200
    payload = keys.json()
    (entry,) = payload["keys"]
    assert entry["kid"] == cert["kid"]
    # a stranger with only the payload can verify the cert
    assert ca.verify_certificate(cert, public_key=entry["public_key"])["valid"] is True

    # check endpoint: valid, then revoked after operator revocation
    ok = client.post("/check", json={"certificate": cert})
    assert ok.json()["valid"] is True
    verify_api.STORE.revoke(cert["serial"], reason="test revocation")
    revoked = client.post("/check", json={"certificate": cert})
    assert revoked.json() == {"valid": False, "reason": "revoked", "payload": cert}
    listing = client.get("/revoked")
    assert cert["serial"] in listing.json()["revoked"]

    # metering + audit landed in the store; chain intact
    assert verify_api.STORE.usage_for("rest-anonymous")["calls"] >= 1
    chain = verify_api.STORE.verify_chain()
    assert chain["ok"] is True
    types = [e["event_type"] for e in verify_api.STORE.audit_events()]
    assert "issuance" in types and "verification" in types
    assert "revocation" in types


def _unwrap(tool):
    return getattr(tool, "fn", tool)


def test_mcp_tools_use_ed25519_and_store(monkeypatch):
    monkeypatch.setattr(mcp_server, "iterative_proof_search", _fake_search)
    mcp_server._KEY.id = "mcp-test-key"

    verify_fn = _unwrap(mcp_server.verify)
    out = verify_fn(code=CODE)
    cert = out["certificate"]
    assert out["verified"] is True
    assert cert["alg"] == "Ed25519"
    assert cert["key_id"] == "mcp-test-key"
    assert _work_root_leftovers("ax-mcp-") == []
    assert mcp_server.STORE.get_cert(cert["serial"]) == cert

    check_fn = _unwrap(mcp_server.check_certificate)
    assert check_fn(certificate=cert)["valid"] is True

    usage_fn = _unwrap(mcp_server.usage_report)
    report = usage_fn()
    assert report["key_id"] == "mcp-test-key"
    assert report["calls"] >= 1
    assert mcp_server.STORE.verify_chain()["ok"] is True


def test_legacy_hmac_module_still_importable():
    import certs  # legacy fixtures must keep working

    old = certs.issue({"code_sha256": "ee" * 32, "verified": True, "attempts": 1, "toolchain": "x", "key_id": "k"})
    assert certs.check(old)["valid"] is True  # HMAC path untouched
    # ...but the production CA refuses it (no Ed25519 alg)
    assert ca.verify_certificate(old)["valid"] is False
