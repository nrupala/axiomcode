"""AxiomCode Stripe billing (W4 code layer) — credit packs over
Stripe Checkout, credits granted by webhook.

NO live Stripe calls live in this module's tested paths: building a
checkout payload is pure, the API call sits behind a thin client
(create_checkout_session(client=...)), and the webhook core takes a
signature-verification callable. Product/price creation in the live
account and the webhook secret arrive at deploy time.

Packs (pricing doctrine — 1 credit = $0.01, metered at 0.9 credits
per compute-second; see billing.py):
  starter  1,000 credits  $10
  growth   5,000 credits  $50
  scale   20,000 credits  $200
Price IDs come from env: AXIOMCODE_STRIPE_PRICE_STARTER / _GROWTH /
_SCALE. The checkout session carries the buyer's key HASH (never the
plaintext key) as client_reference_id + metadata, so the webhook can
grant credits to exactly that key.

Webhook behaviour:
  checkout.session.completed -> grant the pack's credits with
      external_id = the checkout session id. Replays are no-ops:
      store.grant_credits is idempotent on external_id. A zero-credit
      link row (external_id = the session's payment_intent id,
      source = "stripe_pi_for:<session id>") is recorded alongside so
      a later refund can find the grant — charges know the payment
      intent, not the checkout session.
  charge.refunded -> if the charge's payment_intent resolves to a
      link row, append a negative grant reversing the original
      credits (external_id = "<session id>:refund:<charge id>", so
      replayed refund events are no-ops too) and the key's balance
      drops accordingly. Unknown payments are reported unhandled;
      deploy-time monitoring owns alerting on those.
"""

import os

PACKS = {
    "starter": {"credits": 1000, "usd": 10, "price_env": "AXIOMCODE_STRIPE_PRICE_STARTER"},
    "growth": {"credits": 5000, "usd": 50, "price_env": "AXIOMCODE_STRIPE_PRICE_GROWTH"},
    "scale": {"credits": 20000, "usd": 200, "price_env": "AXIOMCODE_STRIPE_PRICE_SCALE"},
}

DEFAULT_SUCCESS_URL = os.environ.get("AXIOMCODE_CHECKOUT_SUCCESS_URL", "https://axiom-code.com/billing/success")
DEFAULT_CANCEL_URL = os.environ.get("AXIOMCODE_CHECKOUT_CANCEL_URL", "https://axiom-code.com/pricing/")


def price_id_for(pack: str) -> str | None:
    """The configured Stripe price id for a pack, or None."""
    spec = PACKS.get(pack)
    if spec is None:
        return None
    return os.environ.get(str(spec["price_env"])) or None


def pack_catalogue() -> dict:
    """Pack list with live price-id wiring status (no secrets)."""
    return {
        name: {
            "credits": spec["credits"],
            "usd": spec["usd"],
            "price_id": price_id_for(name),
            "price_env": spec["price_env"],
        }
        for name, spec in PACKS.items()
    }


def build_checkout_payload(
    pack: str, key_hash: str, *, success_url: str = DEFAULT_SUCCESS_URL, cancel_url: str = DEFAULT_CANCEL_URL
) -> dict:
    """The exact Checkout Session create payload for a pack + key.
    Pure function — the network call is create_checkout_session's."""
    spec = PACKS.get(pack)
    if spec is None:
        raise ValueError(f"unknown pack: {pack!r}")
    price_id = price_id_for(pack)
    if price_id is None:
        raise ValueError(f"no Stripe price configured for pack {pack!r} (set {spec['price_env']})")
    return {
        "mode": "payment",
        "line_items": [{"price": price_id, "quantity": 1}],
        "client_reference_id": key_hash,
        "metadata": {"pack": pack, "key_hash": key_hash},
        "success_url": success_url,
        "cancel_url": cancel_url,
    }


class StripeClient:
    """Thin wrapper over the stripe SDK so tests can substitute a
    fake with the same create_checkout_session(payload) shape. The
    SDK is imported lazily — this module never requires it."""

    def __init__(self, secret_key: str | None = None):
        import stripe

        stripe.api_key = secret_key or os.environ.get("STRIPE_SECRET_KEY", "")
        self._stripe = stripe

    def create_checkout_session(self, payload: dict) -> dict:
        session = self._stripe.checkout.Session.create(**payload)
        return session.to_dict() if hasattr(session, "to_dict") else dict(session)


def create_checkout_session(
    pack: str,
    key_hash: str,
    *,
    client=None,
    success_url: str = DEFAULT_SUCCESS_URL,
    cancel_url: str = DEFAULT_CANCEL_URL,
) -> dict:
    """Create a Checkout Session for a pack. `client` defaults to the
    real StripeClient; tests pass a fake."""
    payload = build_checkout_payload(pack, key_hash, success_url=success_url, cancel_url=cancel_url)
    client = client or StripeClient()
    session: dict = client.create_checkout_session(payload)
    return session


def handle_webhook(store, raw_payload, signature, verify_signature) -> dict:
    """Webhook core. `verify_signature(raw_payload, signature)` must
    return the event dict or raise (bad signature / malformed event)
    — the route wires it to stripe.Webhook.construct_event; tests
    pass a trivial callable. Signature failure propagates.

    Returns a result dict describing what happened; grants are
    idempotent on Stripe ids, so redelivery is always safe."""
    event = verify_signature(raw_payload, signature)
    if not isinstance(event, dict):
        event = dict(event)
    event_type = event.get("type", "")
    obj = (event.get("data") or {}).get("object") or {}

    if event_type == "checkout.session.completed":
        return _on_checkout_completed(store, obj)
    if event_type == "charge.refunded":
        return _on_charge_refunded(store, obj)
    return {"handled": False, "reason": f"unhandled event type: {event_type}"}


def _on_checkout_completed(store, session: dict) -> dict:
    key_hash = session.get("client_reference_id") or (session.get("metadata") or {}).get("key_hash")
    pack = (session.get("metadata") or {}).get("pack")
    spec = PACKS.get(pack or "")
    if not key_hash or spec is None:
        return {"handled": False, "reason": "session missing key_hash or known pack metadata"}
    session_id = session.get("id", "")
    granted = store.grant_credits(
        key_hash, spec["credits"], source="stripe:checkout.session.completed", external_id=session_id
    )
    payment_intent = session.get("payment_intent")
    if payment_intent:
        # Zero-credit link row: lets charge.refunded (which knows the
        # payment intent, not the session) find this grant later.
        store.grant_credits(key_hash, 0, source=f"stripe_pi_for:{session_id}", external_id=payment_intent)
    return {
        "handled": True,
        "event": "checkout.session.completed",
        "granted": granted,
        "credits": spec["credits"] if granted else 0,
        "key_hash": key_hash,
        "pack": pack,
        "session": session_id,
    }


def _on_charge_refunded(store, charge: dict) -> dict:
    payment_intent = charge.get("payment_intent")
    link = store.find_grant(payment_intent) if payment_intent else None
    if link is None or not str(link["source"]).startswith("stripe_pi_for:"):
        return {"handled": False, "reason": "refund for an unknown payment"}
    session_id = link["source"].split(":", 1)[1]
    original = store.find_grant(session_id)
    if original is None or original["credits"] <= 0:
        return {"handled": False, "reason": "no grant found for refunded session"}
    reversal_id = f"{session_id}:refund:{charge.get('id', '')}"
    reversed_now = store.grant_credits(
        original["key_hash"], -original["credits"], source="stripe:charge.refunded", external_id=reversal_id
    )
    return {
        "handled": True,
        "event": "charge.refunded",
        "reversed": reversed_now,
        "credits": -original["credits"] if reversed_now else 0,
        "key_hash": original["key_hash"],
        "session": session_id,
    }
