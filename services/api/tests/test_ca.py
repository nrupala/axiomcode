"""W1 — Ed25519 certification authority."""

import os
import stat

import ca
import certs as legacy_certs
import pytest

SUBJECT = {
    "code_sha256": "ab" * 32,
    "verified": True,
    "attempts": 1,
    "toolchain": "leanprover/lean4:v4.35.0-rc3",
    "key_id": "test-caller",
}


@pytest.fixture()
def authority(tmp_path):
    return ca.CA.load_or_create(tmp_path / "ca_key.pem")


def test_key_persistence_and_permissions(tmp_path):
    key_file = tmp_path / "ca_key.pem"
    first = ca.CA.load_or_create(key_file)
    assert key_file.exists()
    assert stat.S_IMODE(os.stat(key_file).st_mode) == 0o600
    second = ca.CA.load_or_create(key_file)
    assert second.kid == first.kid  # same key reloaded, not regenerated


def test_issue_verify_round_trip(authority):
    cert = authority.issue(dict(SUBJECT))
    assert cert["version"] == 2
    assert cert["alg"] == "Ed25519"
    assert cert["kid"] == authority.kid
    assert cert["issuer"] == "AxiomCode CA"
    assert cert["valid_until"] - cert["valid_from"] == 90 * 86400
    result = ca.verify_certificate(cert, ca=authority)
    assert result["valid"] is True
    assert result["payload"]["serial"] == cert["serial"]


def test_tampered_cert_fails(authority):
    cert = authority.issue(dict(SUBJECT))
    forged = dict(cert, verified=False)  # flip the verdict after signing
    assert ca.verify_certificate(forged, ca=authority)["valid"] is False
    mangled = dict(cert, signature="A" + cert["signature"][1:])
    result = ca.verify_certificate(mangled, ca=authority)
    assert result == {"valid": False, "reason": "bad_signature"}


def test_wrong_key_fails(authority, tmp_path):
    other = ca.CA.load_or_create(tmp_path / "other_key.pem")
    cert = authority.issue(dict(SUBJECT))
    result = ca.verify_certificate(cert, public_key=other.public_key)
    assert result["valid"] is False
    assert result["reason"] == "bad_signature"


def test_public_payload_verifies_issued_cert(authority):
    cert = authority.issue(dict(SUBJECT))
    payload = authority.public_keys_payload()
    assert payload["issuer"] == "AxiomCode CA"
    (entry,) = payload["keys"]
    assert entry["kid"] == cert["kid"]
    assert entry["alg"] == "Ed25519"
    # A third party with ONLY the published payload can verify:
    by_b64 = ca.verify_certificate(cert, public_key=entry["public_key"])
    assert by_b64["valid"] is True
    by_pem = ca.verify_certificate(cert, public_key=entry["public_key_pem"])
    assert by_pem["valid"] is True


def test_legacy_hmac_cert_rejected(authority):
    old = legacy_certs.issue(dict(SUBJECT))
    assert ca.verify_certificate(old, ca=authority)["valid"] is False
