"""PR #21 hardening regressions + W3 service-level behaviour:
CA-fixed fields win in issue(); kid must match the verifying key;
the audit chain binds event_type and ts; per-key proof concurrency;
MCP trial flow + credential-bound identity."""

import inspect
import sqlite3
import threading

import ca
import limits
import mcp_server
import pytest
import verify_service
from store import Store, hash_api_key

SUBJECT = {
    "code_sha256": "ab" * 32,
    "verified": True,
    "attempts": 1,
    "toolchain": "leanprover/lean4:v4.35.0-rc3",
    "key_id": "test-caller",
}
CODE = "theorem t : True := trivial"


@pytest.fixture()
def authority(tmp_path):
    return ca.CA.load_or_create(tmp_path / "ca_key.pem")


# ─── CA hardening ────────────────────────────────────────────────────


def test_issue_fixed_fields_win_over_subject(authority):
    forged = dict(
        SUBJECT, issuer="Mallory CA", serial="forged-serial", kid="0" * 16, alg="none", version=99, valid_until=1
    )
    cert = authority.issue(forged)
    assert cert["issuer"] == "AxiomCode CA"
    assert cert["serial"] != "forged-serial"
    assert cert["kid"] == authority.kid
    assert cert["alg"] == "Ed25519"
    assert cert["version"] == 2
    assert cert["valid_until"] - cert["valid_from"] == 90 * 86400
    # ...and the resulting cert still verifies cleanly.
    assert ca.verify_certificate(cert, ca=authority)["valid"] is True


def test_cert_naming_another_kid_is_rejected(tmp_path):
    ca_a = ca.CA.load_or_create(tmp_path / "a.pem")
    ca_b = ca.CA.load_or_create(tmp_path / "b.pem")
    # B signs a body that claims A's kid: signature is genuinely B's.
    body = {k: v for k, v in ca_b.issue(dict(SUBJECT)).items() if k != "signature"}
    body["kid"] = ca_a.kid
    forged = {**body, "signature": ca_b.sign_body(body)}
    result = ca.verify_certificate(forged, public_key=ca_b.public_key)
    assert result == {"valid": False, "reason": "unknown_kid"}
    # Against A's key the same cert fails the signature outright.
    assert ca.verify_certificate(forged, public_key=ca_a.public_key)["valid"] is False


# ─── audit chain binds event_type + ts (format v2) ───────────────────


def test_chain_detects_event_type_tamper(tmp_path):
    db = tmp_path / "tamper-type.db"
    s = Store(db)
    s.append_audit("verification", {"serial": "s1", "valid": True})
    s.append_audit("verification", {"serial": "s2", "valid": True})
    assert s.verify_chain()["ok"] is True
    s.close()

    raw = sqlite3.connect(db)
    raw.execute("UPDATE audit_log SET event_type = 'issuance' WHERE seq = 1")
    raw.commit()
    raw.close()

    reopened = Store(db)
    result = reopened.verify_chain()
    assert result == {"ok": False, "broken_seq": 1}
    reopened.close()


def test_chain_detects_timestamp_tamper(tmp_path):
    db = tmp_path / "tamper-ts.db"
    s = Store(db)
    s.append_audit("verification", {"serial": "s1", "valid": True})
    s.append_audit("verification", {"serial": "s2", "valid": True})
    s.close()

    raw = sqlite3.connect(db)
    raw.execute("UPDATE audit_log SET ts = ts + 3600 WHERE seq = 2")
    raw.commit()
    raw.close()

    reopened = Store(db)
    assert reopened.verify_chain() == {"ok": False, "broken_seq": 2}
    reopened.close()


# ─── concurrency gate ────────────────────────────────────────────────


def test_concurrency_gate_unit():
    gate = limits.ConcurrencyGate(2)
    assert gate.acquire("k") is True
    assert gate.acquire("k") is True
    assert gate.acquire("k") is False  # at cap for this key
    assert gate.acquire("other") is True  # ...but not for others
    gate.release("k")
    assert gate.acquire("k") is True


def test_service_rejects_second_concurrent_proof(tmp_path):
    store = Store(tmp_path / "conc.db")
    authority = ca.CA.load_or_create(tmp_path / "ca.pem")
    plaintext = store.create_api_key("conc")
    key_hash = hash_api_key(plaintext)
    store.grant_credits(key_hash, 1000, source="test")

    started = threading.Event()
    release = threading.Event()

    def blocking_search(writer, proj, code, *args, **kwargs):
        writer(code)
        started.set()
        release.wait(10)
        return True, code, 1, "blocked stub"

    gate = limits.ConcurrencyGate(1)
    kwargs = dict(
        store=store,
        authority=authority,
        key_hash=key_hash,
        code=CODE,
        max_attempts=1,
        work_root=str(tmp_path),
        prefix="ax-test-",
        toolchain="tc",
        search=blocking_search,
        gate=gate,
    )
    results = []
    t = threading.Thread(target=lambda: results.append(verify_service.execute_verification(**kwargs)))
    t.start()
    try:
        assert started.wait(5)
        with pytest.raises(verify_service.TooManyConcurrentError):
            verify_service.execute_verification(**kwargs)
    finally:
        release.set()
        t.join(10)
    assert results[0]["certificate"] is not None
    store.close()


# ─── MCP: trial flow + identity cannot be supplied ──────────────────


def _unwrap(tool):
    return getattr(tool, "fn", tool)


def test_mcp_trial_flow(monkeypatch):
    def fake_search(writer, proj, code, *args, **kwargs):
        writer(code)
        return True, code, 1, "stubbed prover log"

    monkeypatch.setattr(mcp_server, "iterative_proof_search", fake_search)
    plaintext = mcp_server.STORE.create_api_key("mcp-trial")
    key_hash = hash_api_key(plaintext)
    mcp_server._KEY.key_hash = key_hash

    verify_fn = _unwrap(mcp_server.verify)
    out = verify_fn(code=CODE)
    assert out["verified"] is True
    assert out["certificate"] is None  # trial: verdict, no certificate
    assert out["trial"]["cases_used"] == 1
    assert mcp_server.STORE.trial_cases_used(key_hash) == 1

    # The tools take identity from the credential context only: no
    # parameter lets a caller name another key.
    params = inspect.signature(verify_fn).parameters
    assert "key_id" not in params and "key_hash" not in params

    # Grant credits -> the same tool now issues certificates.
    mcp_server.STORE.grant_credits(key_hash, 1000, source="test")
    out = verify_fn(code=CODE)
    assert out["certificate"] is not None
    assert out["certificate"]["key_id"] == key_hash
