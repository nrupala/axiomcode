"""W3/W4 — balance math, grant idempotency, Stripe checkout payload
and webhook core (grant once, replay safe, refund reversal)."""

import importlib.util

import billing
import pytest
import stripe_billing
import verify_api
from fastapi.testclient import TestClient
from store import Store, hash_api_key


@pytest.fixture()
def store(tmp_path):
    s = Store(tmp_path / "billing.db")
    yield s
    s.close()


@pytest.fixture()
def key(store):
    plaintext = store.create_api_key("billing-flow")
    return plaintext, hash_api_key(plaintext)


# ─── balance math ────────────────────────────────────────────────────


def test_balance_is_grants_minus_metered_credits(store, key):
    _plaintext, h = key
    assert store.balance_for(h) == 0
    store.grant_credits(h, 1000, source="test", external_id="cs_1")
    billing.meter(store, h, "aa" * 32, True, 2.0)  # 2.0s x 0.9 = 1.8 credits
    assert store.balance_for(h) == pytest.approx(1000 - 1.8)
    # Trial cases are free: they count as cases, never as spend.
    billing.meter(store, h, "bb" * 32, True, 5.0, trial=True)
    assert store.trial_cases_used(h) == 1
    assert store.balance_for(h) == pytest.approx(1000 - 1.8)
    assert store.credits_granted(h) == 1000


def test_grant_idempotent_on_external_id(store, key):
    _plaintext, h = key
    assert store.grant_credits(h, 500, source="stripe", external_id="cs_x") is True
    assert store.grant_credits(h, 500, source="stripe", external_id="cs_x") is False
    assert store.credits_granted(h) == 500
    # Grants without an external id are never deduplicated.
    assert store.grant_credits(h, 5, source="comp") is True
    assert store.grant_credits(h, 5, source="comp") is True
    assert store.credits_granted(h) == 510


def test_only_key_hashes_are_stored(store, key):
    plaintext, h = key
    row = store.lookup_api_key(plaintext)
    assert row["key_hash"] == h
    assert plaintext not in str(row)  # the secret itself is nowhere in the row
    assert store.authenticate_api_key(plaintext)["key_hash"] == h
    assert store.authenticate_api_key("axk_wrong") is None


# ─── checkout payload / client seam ──────────────────────────────────


def test_checkout_payload(monkeypatch):
    monkeypatch.setenv("AXIOMCODE_STRIPE_PRICE_STARTER", "price_starter_123")
    payload = stripe_billing.build_checkout_payload("starter", "cafe" * 16)
    assert payload["mode"] == "payment"
    assert payload["line_items"] == [{"price": "price_starter_123", "quantity": 1}]
    assert payload["client_reference_id"] == "cafe" * 16
    assert payload["metadata"] == {"pack": "starter", "key_hash": "cafe" * 16}
    with pytest.raises(ValueError):
        stripe_billing.build_checkout_payload("platinum", "cafe")
    monkeypatch.delenv("AXIOMCODE_STRIPE_PRICE_STARTER")
    with pytest.raises(ValueError):  # known pack, price not configured
        stripe_billing.build_checkout_payload("starter", "cafe")


def test_create_checkout_session_with_fake_client(monkeypatch):
    monkeypatch.setenv("AXIOMCODE_STRIPE_PRICE_GROWTH", "price_growth_9")
    seen = {}

    class FakeClient:
        def create_checkout_session(self, payload):
            seen.update(payload)
            return {"id": "cs_fake", "url": "https://checkout.stripe.test/cs_fake"}

    out = stripe_billing.create_checkout_session("growth", "beef" * 16, client=FakeClient())
    assert out["id"] == "cs_fake"
    assert seen["line_items"][0]["price"] == "price_growth_9"
    assert seen["metadata"]["pack"] == "growth"


# ─── webhook core ────────────────────────────────────────────────────


def _event(event_type, obj):
    return {"type": event_type, "data": {"object": obj}}


def _completed(key_hash, session="cs_1", pack="growth", pi="pi_1"):
    return _event(
        "checkout.session.completed",
        {
            "id": session,
            "client_reference_id": key_hash,
            "payment_intent": pi,
            "metadata": {"pack": pack, "key_hash": key_hash},
        },
    )


def _verify_with(event):
    return lambda _payload, _sig: event


def test_webhook_grants_pack_credits_once(store, key):
    _plaintext, h = key
    result = stripe_billing.handle_webhook(store, b"{}", "sig", _verify_with(_completed(h)))
    assert result["handled"] is True
    assert result["granted"] is True
    assert result["credits"] == 5000  # growth pack
    assert store.balance_for(h) == 5000

    replay = stripe_billing.handle_webhook(store, b"{}", "sig", _verify_with(_completed(h)))
    assert replay["handled"] is True
    assert replay["granted"] is False  # idempotent: redelivery grants nothing
    assert store.balance_for(h) == 5000


def test_webhook_refund_reverses_the_grant(store, key):
    _plaintext, h = key
    stripe_billing.handle_webhook(store, b"{}", "sig", _verify_with(_completed(h)))
    assert store.balance_for(h) == 5000

    refund = _event("charge.refunded", {"id": "ch_1", "payment_intent": "pi_1"})
    result = stripe_billing.handle_webhook(store, b"{}", "sig", _verify_with(refund))
    assert result["handled"] is True
    assert result["reversed"] is True
    assert store.balance_for(h) == 0

    replay = stripe_billing.handle_webhook(store, b"{}", "sig", _verify_with(refund))
    assert replay["reversed"] is False  # a refund also lands exactly once
    assert store.balance_for(h) == 0


def test_webhook_unknown_refund_and_event(store, key):
    _plaintext, _h = key
    refund = _event("charge.refunded", {"id": "ch_9", "payment_intent": "pi_nope"})
    result = stripe_billing.handle_webhook(store, b"{}", "sig", _verify_with(refund))
    assert result["handled"] is False
    other = _event("invoice.paid", {"id": "in_1"})
    assert stripe_billing.handle_webhook(store, b"{}", "sig", _verify_with(other))["handled"] is False


def test_webhook_bad_signature_propagates(store):
    def bad(_payload, _sig):
        raise ValueError("signature mismatch")

    with pytest.raises(ValueError):
        stripe_billing.handle_webhook(store, b"{}", "sig", bad)


def test_webhook_route_501_until_stripe_configured():
    if importlib.util.find_spec("stripe") is not None:
        pytest.skip("stripe installed here; the deploy-config path is covered at deploy")
    c = TestClient(verify_api.app, raise_server_exceptions=False)
    r = c.post("/billing/webhook", content=b"{}", headers={"Stripe-Signature": "t=1,v1=x"})
    assert r.status_code == 501
    assert r.json()["error"] == "stripe_not_configured"
