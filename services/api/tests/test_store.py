"""W2 — durable store with hash-chained audit log."""

import sqlite3

import billing
import ca
import pytest
from store import Store


@pytest.fixture()
def store(tmp_path):
    s = Store(tmp_path / "test.db")
    yield s
    s.close()


@pytest.fixture()
def cert(authority_keyfile):
    return authority_keyfile.issue(
        {
            "code_sha256": "cd" * 32,
            "verified": True,
            "attempts": 1,
            "toolchain": "leanprover/lean4:v4.35.0-rc3",
            "key_id": "caller-1",
        }
    )


@pytest.fixture()
def authority_keyfile(tmp_path):
    return ca.CA.load_or_create(tmp_path / "k.pem")


def test_record_and_get_cert(store, cert):
    store.record_cert(cert)
    assert store.get_cert(cert["serial"]) == cert
    assert store.get_cert("no-such-serial") is None


def test_revocation_persists_across_reopen(tmp_path, cert):
    db = tmp_path / "durable.db"
    first = Store(db)
    first.record_cert(cert)
    first.revoke(cert["serial"], reason="toolchain defect")
    assert first.is_revoked(cert["serial"])
    first.close()

    second = Store(db)  # reopen — revocation must survive
    assert second.is_revoked(cert["serial"])
    assert cert["serial"] in second.revoked_serials()
    assert second.get_cert(cert["serial"])["serial"] == cert["serial"]
    second.close()


def test_audit_chain_verifies(store, cert):
    store.record_cert(cert)  # issuance event
    store.append_audit("verification", {"serial": cert["serial"], "valid": True, "via": "test"})
    store.revoke(cert["serial"], reason="test")  # revocation event
    result = store.verify_chain()
    assert result == {"ok": True, "events": 3}
    types = [e["event_type"] for e in store.audit_events()]
    assert types == ["issuance", "verification", "revocation"]


def test_audit_chain_detects_flipped_byte(tmp_path, cert):
    db = tmp_path / "tamper.db"
    s = Store(db)
    s.record_cert(cert)
    s.append_audit("verification", {"serial": cert["serial"], "valid": True})
    s.revoke(cert["serial"], reason="test")
    assert s.verify_chain()["ok"] is True
    s.close()

    raw = sqlite3.connect(db)
    seq, payload = raw.execute("SELECT seq, payload_json FROM audit_log WHERE seq = 2").fetchone()
    flipped = payload[:6] + ("X" if payload[6] != "X" else "Y") + payload[7:]
    raw.execute("UPDATE audit_log SET payload_json = ? WHERE seq = ?", (flipped, seq))
    raw.commit()
    raw.close()

    reopened = Store(db)
    result = reopened.verify_chain()
    assert result["ok"] is False
    assert result["broken_seq"] == 2
    reopened.close()


def test_meter_events_recorded(store):
    e1 = billing.meter(store, "key-1", "aa" * 32, True, 2.0)
    billing.meter(store, "key-1", "bb" * 32, False, 2.0)
    billing.meter(store, "key-2", "cc" * 32, True, 1.0)

    events = store.meter_events("key-1")
    assert len(events) == 2
    assert events[0]["code_sha256"] == "aa" * 32
    assert e1["credits"] == pytest.approx(1.8)  # 2.0s x 0.9 credits/s

    usage = store.usage_for("key-1")
    assert usage["calls"] == 2
    assert usage["credits_used"] == pytest.approx(3.6)
    assert usage["usd_used"] == pytest.approx(0.036)
    # billing.usage_for routes to the same store numbers
    assert billing.usage_for(store, "key-1") == usage
    assert store.usage_for("key-2")["calls"] == 1
