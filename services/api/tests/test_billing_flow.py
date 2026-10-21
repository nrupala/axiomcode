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


def test_webhook_route_with_real_stripe_verifier(monkeypatch):
    """Regression — F0 staging on the Dell G3 (2026-10-20): the
    /billing/webhook route converted the verified Stripe event with
    json.dumps(event). Real stripe-python events are attribute-access
    objects, not dicts, so that raised TypeError on EVERY genuine
    delivery and the route answered 400 — no real payment could ever
    grant credits. The other webhook tests stub the verifier with
    plain dicts, which is why this shipped. This test runs the route's
    real stripe.Webhook.construct_event end to end. Skips where the
    stripe package is not installed."""
    pytest.importorskip("stripe")
    import hashlib
    import hmac
    import json as jsonlib
    import time

    secret = "whsec_route_test_secret"
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", secret)
    store = verify_api.STORE
    plaintext = store.create_api_key("billing-route-real")
    key_hash = hash_api_key(plaintext)
    session = {
        "id": "cs_route_test_1",
        "object": "checkout.session",
        "client_reference_id": key_hash,
        "metadata": {"pack": "starter", "key_hash": key_hash},
        "payment_intent": "pi_route_test_1",
        "status": "complete",
        "payment_status": "paid",
    }
    event = {
        "id": "evt_route_test_1",
        "object": "event",
        "type": "checkout.session.completed",
        "data": {"object": session},
    }
    payload = jsonlib.dumps(event, separators=(",", ":")).encode()
    ts = int(time.time())
    sig = hmac.new(secret.encode(), f"{ts}.".encode() + payload, hashlib.sha256).hexdigest()
    client = TestClient(verify_api.app, raise_server_exceptions=False)
    r = client.post(
        "/billing/webhook",
        content=payload,
        headers={"Stripe-Signature": f"t={ts},v1={sig}", "Content-Type": "application/json"},
    )
    assert r.status_code == 200
    assert r.json()["handled"] is True
    assert store.balance_for(key_hash) == 1000


# ─── checkout route ─────────────────────────────────────────────────
# The landing build item: create_checkout_session existed with no
# caller. POST /billing/checkout wires it, key-bound, 501-honest
# when Stripe is not configured (same posture as the webhook).


class _FakeStripeClient:
    def __init__(self):
        self.payloads = []

    def create_checkout_session(self, payload):
        self.payloads.append(payload)
        return {"id": "cs_test_fake", "url": "https://checkout.stripe.com/c/cs_test_fake"}


@pytest.fixture()
def checkout_env(monkeypatch):
    import sys
    import types

    monkeypatch.setitem(sys.modules, "stripe", types.ModuleType("stripe"))
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_fake")
    monkeypatch.setenv("AXIOMCODE_STRIPE_PRICE_STARTER", "price_fake_starter")
    fake = _FakeStripeClient()
    monkeypatch.setattr(stripe_billing, "StripeClient", lambda *a, **k: fake)
    return fake


def _route_key(label):
    plaintext = verify_api.STORE.create_api_key(label)
    return plaintext, hash_api_key(plaintext)


def test_checkout_route_creates_bound_session(checkout_env):
    plaintext, h = _route_key("checkout-route")
    client = TestClient(verify_api.app, raise_server_exceptions=False)
    r = client.post("/billing/checkout", json={"pack": "starter"}, headers={"X-Api-Key": plaintext})
    assert r.status_code == 200
    body = r.json()
    assert body["checkout_url"] == "https://checkout.stripe.com/c/cs_test_fake"
    assert body["session_id"] == "cs_test_fake" and body["pack"] == "starter"
    payload = checkout_env.payloads[0]
    assert payload["client_reference_id"] == h
    assert payload["metadata"] == {"pack": "starter", "key_hash": h}
    assert payload["line_items"] == [{"price": "price_fake_starter", "quantity": 1}]


def test_checkout_route_unknown_pack_400(checkout_env):
    plaintext, _h = _route_key("checkout-route-badpack")
    client = TestClient(verify_api.app, raise_server_exceptions=False)
    r = client.post("/billing/checkout", json={"pack": "platinum"}, headers={"X-Api-Key": plaintext})
    assert r.status_code == 400 and "unknown pack" in r.json()["error"]


def test_checkout_route_requires_auth(checkout_env):
    client = TestClient(verify_api.app, raise_server_exceptions=False)
    r = client.post("/billing/checkout", json={"pack": "starter"})
    assert r.status_code == 401


def test_checkout_route_501_without_secret_key(monkeypatch):
    import sys
    import types

    monkeypatch.setitem(sys.modules, "stripe", types.ModuleType("stripe"))
    monkeypatch.delenv("STRIPE_SECRET_KEY", raising=False)
    plaintext, _h = _route_key("checkout-route-nosecret")
    client = TestClient(verify_api.app, raise_server_exceptions=False)
    r = client.post("/billing/checkout", json={"pack": "starter"}, headers={"X-Api-Key": plaintext})
    assert r.status_code == 501
