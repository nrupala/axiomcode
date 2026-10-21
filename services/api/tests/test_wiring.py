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
from store import hash_api_key

CODE = "theorem t : True := trivial"


def _fake_search(writer, proj, code, *args, **kwargs):
    writer(code)
    return True, code, 1, "stubbed prover log"


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setattr(verify_api, "iterative_proof_search", _fake_search)
    monkeypatch.setattr(verify_api, "lean_version", lambda: "lean-test")
    return TestClient(verify_api.app)


def _paid_key(store, label):
    """A provisioned key holding credits (the paid path: certs issue)."""
    plaintext = store.create_api_key(label)
    key_hash = hash_api_key(plaintext)
    store.grant_credits(key_hash, 1000, source="test-fixture")
    return plaintext, key_hash


def _work_root_leftovers(prefix):
    root = Path(os.environ["AXIOMCODE_WORK_ROOT"])
    return [p.name for p in root.iterdir() if p.name.startswith(prefix)]


def test_rest_end_to_end(client):
    plaintext, key_hash = _paid_key(verify_api.STORE, "wiring-rest")
    auth = {"X-Api-Key": plaintext}
    r = client.post("/verify", json={"code": CODE}, headers=auth)
    assert r.status_code == 200
    body = r.json()
    assert body["verified"] is True
    cert = body["certificate"]
    assert cert["alg"] == "Ed25519" and cert["version"] == 2
    assert cert["key_id"] == key_hash

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
    ok = client.post("/check", json={"certificate": cert}, headers=auth)
    assert ok.json()["valid"] is True
    verify_api.STORE.revoke(cert["serial"], reason="test revocation")
    revoked = client.post("/check", json={"certificate": cert}, headers=auth)
    assert revoked.json() == {"valid": False, "reason": "revoked", "payload": cert}
    listing = client.get("/revoked")
    assert cert["serial"] in listing.json()["revoked"]

    # metering + audit landed in the store; chain intact
    assert verify_api.STORE.usage_for(key_hash)["calls"] >= 1
    chain = verify_api.STORE.verify_chain()
    assert chain["ok"] is True
    types = [e["event_type"] for e in verify_api.STORE.audit_events()]
    assert "issuance" in types and "verification" in types
    assert "revocation" in types


def _unwrap(tool):
    return getattr(tool, "fn", tool)


def test_mcp_tools_use_ed25519_and_store(monkeypatch):
    monkeypatch.setattr(mcp_server, "iterative_proof_search", _fake_search)
    _plaintext, key_hash = _paid_key(mcp_server.STORE, "wiring-mcp")
    mcp_server._KEY.key_hash = key_hash

    verify_fn = _unwrap(mcp_server.verify)
    out = verify_fn(code=CODE)
    cert = out["certificate"]
    assert out["verified"] is True
    assert cert["alg"] == "Ed25519"
    assert cert["key_id"] == key_hash
    assert _work_root_leftovers("ax-mcp-") == []
    assert mcp_server.STORE.get_cert(cert["serial"]) == cert

    check_fn = _unwrap(mcp_server.check_certificate)
    assert check_fn(certificate=cert)["valid"] is True

    usage_fn = _unwrap(mcp_server.usage_report)
    report = usage_fn()
    assert report["key_id"] == key_hash
    assert report["calls"] >= 1
    assert mcp_server.STORE.verify_chain()["ok"] is True


def test_legacy_hmac_module_still_importable():
    import certs  # legacy fixtures must keep working

    old = certs.issue({"code_sha256": "ee" * 32, "verified": True, "attempts": 1, "toolchain": "x", "key_id": "k"})
    assert certs.check(old)["valid"] is True  # HMAC path untouched
    # ...but the production CA refuses it (no Ed25519 alg)
    assert ca.verify_certificate(old)["valid"] is False


def test_verify_unicode_code_survives_locale_default_encoding(monkeypatch):
    """Regression — F0 staging on the Dell G3 (2026-10-20): on a
    Windows-locale host the process default encoding is cp1252, and
    verify_service's proof writer used Path.write_text with no encoding,
    so Lean code containing ∀ (U+2200) crashed /verify with a 500.
    Simulate that host at the pathlib seam: an implicit encoding must
    behave as cp1252. The writer pins UTF-8, so the case must verify
    and the file the prover receives must round-trip exactly."""
    seen = {}

    def capturing_search(writer, proj, code, *args, **kwargs):
        path = writer(code)
        seen["content"] = Path(path).read_bytes().decode("utf-8")
        return True, code, 1, "stubbed prover log"

    real_write_text = Path.write_text

    def locale_write_text(self, data, encoding=None, errors=None, newline=None):
        # A Windows-locale process resolves a missing encoding to cp1252.
        return real_write_text(self, data, encoding=encoding or "cp1252", errors=errors, newline=newline)

    monkeypatch.setattr(Path, "write_text", locale_write_text)
    monkeypatch.setattr(verify_api, "iterative_proof_search", capturing_search)
    monkeypatch.setattr(verify_api, "lean_version", lambda: "lean-test")
    client = TestClient(verify_api.app, raise_server_exceptions=False)
    plaintext, _key_hash = _paid_key(verify_api.STORE, "wiring-unicode")
    code = "theorem ac_u : ∀ n : Nat, n + 0 = n := by omega"
    r = client.post("/verify", json={"code": code}, headers={"X-Api-Key": plaintext})
    assert r.status_code == 200
    assert r.json()["verified"] is True
    assert seen["content"] == code


def test_second_issuance_records_renewal_lineage(client):
    """Re-verifying the same code with the same key (the renewal shape)
    links the successor to its predecessor in the audit chain — the
    first issuance carries no lineage, the second names the first."""
    plaintext, _key_hash = _paid_key(verify_api.STORE, "wiring-renewal")
    auth = {"X-Api-Key": plaintext}
    c1 = client.post("/verify", json={"code": CODE}, headers=auth).json()["certificate"]
    c2 = client.post("/verify", json={"code": CODE}, headers=auth).json()["certificate"]
    assert c1["serial"] != c2["serial"]
    issuance = {e["payload"]["serial"]: e["payload"] for e in verify_api.STORE.audit_events("issuance")}
    assert "renews" not in issuance[c1["serial"]]
    assert issuance[c2["serial"]]["renews"] == c1["serial"]
