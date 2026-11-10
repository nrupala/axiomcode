"""Hosted MCP (the agent gate) — the /mcp mount in verify_api must
behave exactly like the REST surface it shares a store, CA, limiter
and proof queue with: API-key auth with hash identity, trial verdicts
without certificates, the 402 refusal shape, FIFO queueing with
owner-only job status, and revocation-aware certificate checks.

The Lean prover is stubbed like the wiring/queue tests. The client
is used as a context manager so the app lifespan runs — that is
what starts the proof queue and the MCP session manager in
production (uvicorn lifespan), and it must work here too.
"""

import json
import time

import billing
import ca
import pytest
import verify_api
from fastapi.testclient import TestClient
from store import hash_api_key

CODE = "theorem t : True := trivial"


def _fast_search(writer, proj, code, *args, **kwargs):
    writer(code)
    return True, code, 1, "stubbed prover log"


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setattr(verify_api, "iterative_proof_search", _fast_search)
    monkeypatch.setattr(verify_api, "lean_version", lambda: "lean-test")
    verify_api.QUEUE.start()
    # base_url host "localhost": the MCP transport's DNS-rebinding
    # protection validates the Host header, and TestClient's default
    # "testserver" host is (correctly) not on the allowlist.
    with TestClient(verify_api.app, base_url="http://localhost") as c:
        yield c


def _rpc(client, method, params, key=None, rpc_id=1):
    headers = {"Accept": "application/json, text/event-stream"}
    if key:
        headers["Authorization"] = f"Bearer {key}"
    return client.post(
        "/mcp",
        json={"jsonrpc": "2.0", "id": rpc_id, "method": method, "params": params},
        headers=headers,
    )


def _tool(client, name, arguments=None, key=None):
    r = _rpc(client, "tools/call", {"name": name, "arguments": arguments or {}}, key=key)
    assert r.status_code == 200, r.text
    result = r.json()["result"]
    assert not result.get("isError"), result
    if "structuredContent" in result:
        return result["structuredContent"]
    return json.loads(result["content"][0]["text"])


def _new_key(label, credits=0):
    plaintext = verify_api.STORE.create_api_key(label)
    if credits:
        verify_api.STORE.grant_credits(
            hash_api_key(plaintext),
            credits,
            source="test-fixture",
            external_id=f"fixture-{hash_api_key(plaintext)[:12]}",
        )
    return plaintext


# ─── auth ────────────────────────────────────────────────────────────


def test_mcp_requires_a_valid_key(client):
    # No key at all: the middleware refuses before any tool runs.
    r = _rpc(client, "tools/call", {"name": "health", "arguments": {}})
    assert r.status_code == 401
    assert r.json() == {"error": "invalid or missing API key"}
    # An unknown key is refused identically.
    r = _rpc(client, "tools/call", {"name": "health", "arguments": {}}, key="axk_not-a-real-key")
    assert r.status_code == 401


def test_mcp_accepts_bearer_and_x_api_key(client):
    key = _new_key("mcp-auth-forms")
    assert _tool(client, "health", key=key) == {"status": "ok"}
    r = client.post(
        "/mcp",
        json={"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "health", "arguments": {}}},
        headers={"Accept": "application/json, text/event-stream", "X-Api-Key": key},
    )
    assert r.status_code == 200


# ─── discovery + public-shape tools ──────────────────────────────────


def test_mcp_tool_table(client):
    key = _new_key("mcp-tools")
    r = _rpc(client, "tools/list", {}, key=key)
    assert r.status_code == 200
    names = {t["name"] for t in r.json()["result"]["tools"]}
    assert {"verify", "job_status", "check_certificate", "revoked", "health", "usage_report", "pricing"} <= names


def test_mcp_revoked_and_pricing_shapes(client):
    key = _new_key("mcp-shapes")
    body = _tool(client, "revoked", key=key)
    assert body["issuer"] == ca.ISSUER
    assert isinstance(body["revoked"], list)
    body = _tool(client, "pricing", key=key)
    assert body["credit_usd"] == 0.01
    assert body["rate_credits_per_s"] > 0


# ─── verify: trial, eligibility, timeout ─────────────────────────────


def test_mcp_trial_verdict_has_no_certificate(client):
    key = _new_key("mcp-trial")
    body = _tool(client, "verify", {"code": CODE}, key=key)
    assert body["verified"] is True
    assert body["certificate"] is None  # trial: verdict only, exactly as REST
    assert body["trial"]["cases_used"] == 1
    assert body["trial"]["cases_left"] == verify_api.TRIAL_CASES - 1


def test_mcp_payment_required_after_trial_and_never_queues(client):
    key = _new_key("mcp-broke")
    key_hash = hash_api_key(key)
    for _ in range(verify_api.TRIAL_CASES):
        billing.meter(verify_api.STORE, key_hash, "0" * 64, True, 0.1, trial=True)
    body = _tool(client, "verify", {"code": CODE}, key=key)
    assert body["error"] == "payment_required"
    assert body["trial"]["cases_left"] == 0
    assert verify_api.JOBS.count_jobs("queued") == 0


def test_mcp_proof_timeout_maps_to_rest_error(client, monkeypatch):
    def slow(writer, proj, code, *args, **kwargs):
        time.sleep(1.0)
        return True, code, 1, "slow stub"

    monkeypatch.setattr(verify_api, "iterative_proof_search", slow)
    monkeypatch.setattr(verify_api, "PROOF_TIMEOUT_S", 0.2)
    key = _new_key("mcp-slow")
    body = _tool(client, "verify", {"code": CODE}, key=key)
    assert body["error"] == "proof_timeout"


# ─── verify: the queue (F-AX-5 parity) ───────────────────────────────


def _wait_for_job(client, job_id, key, want, timeout=10.0):
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        last = _tool(client, "job_status", {"job_id": job_id}, key=key)
        if last.get("status") == want:
            return last
        time.sleep(0.05)
    raise AssertionError(f"job {job_id} never reached {want}: last={last}")


def test_mcp_queued_submit_poll_and_owner_only_status(client, monkeypatch):
    monkeypatch.setattr(verify_api.QUEUE, "global_slots", 1)
    key1 = _new_key("mcp-queue-first")
    key2 = _new_key("mcp-queue-second")

    # Hold the only proof slot: the host is busy, as in the REST test.
    assert verify_api.QUEUE.acquire_immediate("filler-key-hash") is True
    try:
        body = _tool(client, "verify", {"code": CODE}, key=key1)
        assert body["status"] == "queued"
        assert body["position"] == 1
        job_id = body["job_id"]

        # The owner can read the position…
        view = _tool(client, "job_status", {"job_id": job_id}, key=key1)
        assert view["status"] == "queued"
        assert view["position"] == 1

        # …another key cannot — indistinguishable from an unknown id.
        assert _tool(client, "job_status", {"job_id": job_id}, key=key2)["error"] == "not_found"
        assert _tool(client, "job_status", {"job_id": "job_nonexistent"}, key=key1)["error"] == "not_found"
    finally:
        verify_api.QUEUE.release("filler-key-hash")

    done = _wait_for_job(client, job_id, key1, "done")
    assert done["result"]["verified"] is True
    assert done["result"]["certificate"] is None  # trial job: no certificate

    # The submitted code is not retained after completion (as REST).
    job = verify_api.JOBS.get_job(job_id)
    assert job["code"] == ""
    assert job["code_sha256"]


# ─── check_certificate ───────────────────────────────────────────────


def test_mcp_check_certificate_valid_revoked_unknown(client):
    paid = _new_key("mcp-paid", credits=100)
    body = _tool(client, "verify", {"code": CODE}, key=paid)
    cert = body["certificate"]
    assert cert and cert["serial"]
    assert isinstance(_tool(client, "usage_report", key=paid), dict)

    checker = _new_key("mcp-checker")
    result = _tool(client, "check_certificate", {"certificate": cert}, key=checker)
    assert result["valid"] is True

    verify_api.STORE.revoke(cert["serial"], reason="test-revocation")
    result = _tool(client, "check_certificate", {"certificate": cert}, key=checker)
    assert result["valid"] is False
    assert result["reason"] == "revoked"

    result = _tool(client, "check_certificate", {"certificate": {"serial": "axc_unknown"}}, key=checker)
    assert result["valid"] is False
