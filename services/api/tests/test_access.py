"""W3/W5 — REST access control: API-key auth, trial enforcement,
rate limiting, submission size cap, proof timeout."""

import os
import sqlite3
import time
from pathlib import Path

import limits
import pytest
import verify_api
from fastapi.testclient import TestClient
from store import hash_api_key

CODE = "theorem t : True := trivial"


def _counting_search(calls):
    def search(writer, proj, code, *args, **kwargs):
        calls.append(code)
        writer(code)
        return True, code, 1, "stubbed prover log"

    return search


@pytest.fixture()
def client(monkeypatch):
    calls: list = []
    monkeypatch.setattr(verify_api, "iterative_proof_search", _counting_search(calls))
    monkeypatch.setattr(verify_api, "lean_version", lambda: "lean-test")
    return TestClient(verify_api.app), calls


@pytest.fixture()
def slow_client(monkeypatch):
    def slow(writer, proj, code, *args, **kwargs):
        time.sleep(1.0)
        return True, code, 1, "slow stub"

    monkeypatch.setattr(verify_api, "iterative_proof_search", slow)
    monkeypatch.setattr(verify_api, "lean_version", lambda: "lean-test")
    monkeypatch.setattr(verify_api, "PROOF_TIMEOUT_S", 0.2)
    return TestClient(verify_api.app)


def _new_key(label, credits=0):
    store = verify_api.STORE
    plaintext = store.create_api_key(label)
    key_hash = hash_api_key(plaintext)
    if credits:
        store.grant_credits(key_hash, credits, source="test-fixture", external_id=f"fixture-{key_hash[:12]}")
    return plaintext, key_hash


def _cert_count_for(key_hash):
    raw = sqlite3.connect(os.environ["AXIOMCODE_DB"])
    try:
        (n,) = raw.execute(
            "SELECT COUNT(*) FROM certificates WHERE cert_json LIKE ?",
            (f"%{key_hash}%",),
        ).fetchone()
        return n
    finally:
        raw.close()


# ─── auth ────────────────────────────────────────────────────────────


def test_missing_and_unknown_keys_get_401(client):
    c, _calls = client
    assert c.post("/verify", json={"code": CODE}).status_code == 401
    assert c.post("/verify", json={"code": CODE}, headers={"X-Api-Key": "axk_not-a-real-key"}).status_code == 401
    assert c.post("/check", json={"certificate": {}}).status_code == 401
    # A caller-supplied identity field buys nothing: still no key, still 401.
    assert c.post("/verify", json={"code": CODE, "key_id": "victim"}).status_code == 401


def test_bearer_and_x_api_key_both_authenticate(client):
    c, _calls = client
    plaintext, _h = _new_key("auth-shapes", credits=100)
    body = {"certificate": {"serial": "nope"}}
    assert c.post("/check", json=body, headers={"X-Api-Key": plaintext}).status_code == 200
    assert c.post("/check", json=body, headers={"Authorization": f"Bearer {plaintext}"}).status_code == 200


def test_revoked_key_gets_401(client):
    c, _calls = client
    plaintext, key_hash = _new_key("auth-revoked", credits=100)
    auth = {"X-Api-Key": plaintext}
    assert c.post("/check", json={"certificate": {}}, headers=auth).status_code == 200
    verify_api.STORE.revoke_api_key(key_hash)
    assert c.post("/check", json={"certificate": {}}, headers=auth).status_code == 401
    assert c.post("/verify", json={"code": CODE}, headers=auth).status_code == 401


def test_open_endpoints_need_no_key(client):
    c, _calls = client
    assert c.get("/health").json() == {"status": "ok"}
    assert c.get("/.well-known/axiomcode-keys.json").status_code == 200
    assert c.get("/revoked").status_code == 200


def test_check_consumes_no_trial_or_credits(client):
    c, _calls = client
    plaintext, key_hash = _new_key("check-is-free")
    auth = {"X-Api-Key": plaintext}
    for _ in range(3):
        r = c.post("/check", json={"certificate": {"serial": "x"}}, headers=auth)
        assert r.status_code == 200
    store = verify_api.STORE
    assert store.trial_cases_used(key_hash) == 0
    assert store.usage_for(key_hash)["calls"] == 0


# ─── trial flow ──────────────────────────────────────────────────────


def test_trial_flow_then_unlock(client):
    c, calls = client
    store = verify_api.STORE
    plaintext, key_hash = _new_key("trial-flow")
    auth = {"X-Api-Key": plaintext}

    for i in range(10):
        r = c.post("/verify", json={"code": CODE}, headers=auth)
        assert r.status_code == 200
        body = r.json()
        assert body["verified"] is True
        assert body["certificate"] is None  # the whole point of the trial
        assert body["usage"]["credits"] == 0  # ...and it is free
        assert body["trial"]["cases_used"] == i + 1
        assert body["trial"]["cases_left"] == 10 - (i + 1)
        assert body["trial"]["certificates"] == "unlock with a credit pack"
    assert len(calls) == 10
    assert store.trial_cases_used(key_hash) == 10
    assert store.usage_for(key_hash)["credits_used"] == 0
    assert _cert_count_for(key_hash) == 0  # no cert was ever recorded

    # 11th case: refused BEFORE the proof runs.
    r = c.post("/verify", json={"code": CODE}, headers=auth)
    assert r.status_code == 402
    assert r.json()["error"] == "payment_required"
    assert len(calls) == 10  # prover never invoked

    # Credits land (what the Stripe webhook does) -> certificates unlock.
    store.grant_credits(key_hash, 1000, source="test", external_id="cs_trial_unlock")
    r = c.post("/verify", json={"code": CODE}, headers=auth)
    assert r.status_code == 200
    body = r.json()
    assert body["certificate"] is not None
    assert body["certificate"]["key_id"] == key_hash
    assert store.get_cert(body["certificate"]["serial"]) is not None
    assert _cert_count_for(key_hash) == 1


# ─── limits & isolation (W5) ─────────────────────────────────────────


def test_rate_limit_returns_429(client, monkeypatch):
    c, _calls = client
    monkeypatch.setattr(verify_api, "LIMITER", limits.RateLimiter(3, 60))
    plaintext, _h = _new_key("rate-limited", credits=100)
    auth = {"X-Api-Key": plaintext}
    for _ in range(3):
        r = c.post("/check", json={"certificate": {}}, headers=auth)
        assert r.status_code == 200
    r = c.post("/check", json={"certificate": {}}, headers=auth)
    assert r.status_code == 429
    assert r.json()["error"] == "rate_limited"


def test_size_cap_returns_413(client, monkeypatch):
    c, calls = client
    monkeypatch.setattr(verify_api, "MAX_CODE_BYTES", 8)
    plaintext, _h = _new_key("size-cap", credits=100)
    r = c.post("/verify", json={"code": CODE}, headers={"X-Api-Key": plaintext})
    assert r.status_code == 413
    assert r.json()["error"] == "code_too_large"
    assert calls == []  # refused before proving


def test_proof_timeout_returns_504_and_cleans_up(slow_client):
    plaintext, _h = _new_key("timeout", credits=100)
    r = slow_client.post("/verify", json={"code": CODE}, headers={"X-Api-Key": plaintext})
    assert r.status_code == 504
    assert r.json()["error"] == "proof_timeout"
    root = Path(os.environ["AXIOMCODE_WORK_ROOT"])
    assert [p.name for p in root.iterdir() if p.name.startswith("ax-api-")] == []
