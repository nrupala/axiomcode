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


# ─── operator CLI (revoke / list-revoked) ─────────────────────────────
# F0 staging finding (2026-10-20): Store.revoke() had no operator
# surface — no CLI, route, or tool called it. These tests drive the
# CLI entry point itself.


def test_cli_revoke_happy_path(tmp_path, cert, capsys):
    import store as store_module

    db = tmp_path / "cli.db"
    s = Store(db)
    s.record_cert(cert)
    s.close()
    rc = store_module._main(["revoke", cert["serial"], "--reason", "operator test", "--db", str(db)])
    assert rc == 0
    assert f"revoked: {cert['serial']}" in capsys.readouterr().out
    s2 = Store(db)
    assert s2.is_revoked(cert["serial"])
    assert "revocation" in [e["event_type"] for e in s2.audit_events()]
    s2.close()


def test_cli_revoke_unknown_serial_refused(tmp_path, capsys):
    import store as store_module

    db = tmp_path / "cli.db"
    Store(db).close()
    rc = store_module._main(["revoke", "deadbeefcafe", "--db", str(db)])
    assert rc == 2
    assert "no certificate with serial" in capsys.readouterr().err


def test_cli_revoke_already_revoked_reports_without_duplicate_audit(tmp_path, cert, capsys):
    import store as store_module

    db = tmp_path / "cli.db"
    s = Store(db)
    s.record_cert(cert)
    s.revoke(cert["serial"])
    s.close()
    rc = store_module._main(["revoke", cert["serial"], "--db", str(db)])
    assert rc == 0
    assert "already revoked" in capsys.readouterr().out
    s2 = Store(db)
    assert [e["event_type"] for e in s2.audit_events()].count("revocation") == 1
    s2.close()


def test_cli_list_revoked(tmp_path, cert, capsys):
    import store as store_module

    db = tmp_path / "cli.db"
    s = Store(db)
    s.record_cert(cert)
    s.revoke(cert["serial"])
    s.close()
    rc = store_module._main(["list-revoked", "--db", str(db)])
    assert rc == 0
    assert cert["serial"] in capsys.readouterr().out


# ─── renewal machinery: expiring report + audit lineage ───────────
# Lifecycle plan L1 item 2 (2026-10-20): certificates expire at 90
# days and tiers.py prices re-verification on expiry, but nothing
# could list what is expiring or link a renewal to its predecessor.


def _bare_cert(serial, key_id="k1", code="aa" * 32, valid_from=1_000, valid_until=2_000):
    return {
        "serial": serial,
        "key_id": key_id,
        "code_sha256": code,
        "verified": True,
        "valid_from": valid_from,
        "valid_until": valid_until,
    }


def test_certs_expiring_window_and_revoked_exclusion(store):
    now = 1_700_000_000
    store.record_cert(_bare_cert("soon", valid_until=now + 3 * 86400))
    store.record_cert(_bare_cert("later", valid_until=now + 30 * 86400))
    store.record_cert(_bare_cert("gone", valid_until=now - 86400))
    store.record_cert(_bare_cert("rev", valid_until=now + 86400))
    store.revoke("rev")
    out = store.certs_expiring(14 * 86400, now=now)
    assert [c["serial"] for c in out] == ["gone", "soon"]
    assert out[0]["expired"] is True and out[1]["expired"] is False


def test_find_prior_cert(store):
    store.record_cert(_bare_cert("first", valid_from=100))
    store.record_cert(_bare_cert("second", valid_from=200))
    store.record_cert(_bare_cert("other-code", code="bb" * 32, valid_from=300))
    assert store.find_prior_cert("k1", "aa" * 32) == "second"
    assert store.find_prior_cert("k1", "aa" * 32, exclude_serial="second") == "first"
    assert store.find_prior_cert("k1", "cc" * 32) is None
    assert store.find_prior_cert("nobody", "aa" * 32) is None


def test_record_cert_renews_in_audit_payload(store):
    store.record_cert(_bare_cert("s1"))
    store.record_cert(_bare_cert("s2"), renews="s1")
    issuance = {e["payload"]["serial"]: e["payload"] for e in store.audit_events("issuance")}
    assert "renews" not in issuance["s1"]
    assert issuance["s2"]["renews"] == "s1"


def test_cli_expiring(tmp_path, capsys):
    import time

    import store as store_module

    db = tmp_path / "cli.db"
    s = Store(db)
    now = int(time.time())
    s.record_cert(_bare_cert("expiring1", valid_until=now + 2 * 86400))
    s.record_cert(_bare_cert("far", valid_until=now + 90 * 86400))
    s.close()
    rc = store_module._main(["expiring", "--days", "14", "--db", str(db)])
    out = capsys.readouterr().out
    assert rc == 0 and "expiring1" in out and "far" not in out
