# AxiomCode API & CA service

**Status: production build, staging-proven.** The product loop (real Lean
compile → verdict → Ed25519 certificate → independent check → revocation)
passed its full acceptance sequence on staging, 2026-10-20. Production
landing follows the F0 landing pack. This directory began as a 2026-09-26
prototype; PRs #21/#22 rebuilt it into the service described here, and the
prototype's `certs.py` HMAC module survives only as the legacy local format
(see `core/` and the migration path in `core/security.py`).

## What it does

- `verify_api.py` — FastAPI REST: `POST /verify`, `POST /check`,
  `GET /revoked`, `GET /.well-known/axiomcode-keys.json`,
  `POST /billing/webhook`. (Checkout session creation lives in
  `stripe_billing.create_checkout_session`; wiring it to a route is a
  production-landing build item.)
- `mcp_server.py` — MCP server over the same verify service:
  `verify`, `check_certificate`, `pricing`, `usage_report`
- `ca.py` — Ed25519 certification authority: v2 certificates, 90-day
  validity, published keys, **key rotation** with retired-key publication
  (`python -m ca rotate`)
- `store.py` — durable SQLite store: API keys (hash-only), credit grants,
  metering, certificates, revocations, and a hash-chained audit log.
  Operator CLI: `python -m store create-key | revoke | list-revoked |
  expiring`
- `stripe_billing.py` — Stripe checkout + webhook core: pack grants
  idempotent on Stripe ids, refund reversal via the payment-intent link
- `billing.py` — compute-time metering, 0.90 credits/sec
  (0.40 × 2.25 loaded-cost multiple)
- `verify_service.py` — the shared verification path for REST and MCP:
  trial policy (10 cases, verdict + transcript, certificate withheld,
  payment demanded before proving), rate limit 60/min per key,
  concurrency gate 2 per key, 256 KB code cap, 600 s proof timeout

## Running it

```bash
# host environment: AXIOMCODE_DB, AXIOMCODE_CA_KEY_FILE,
# AXIOMCODE_WORK_ROOT, STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET,
# AXIOMCODE_STRIPE_PRICE_STARTER/_GROWTH/_SCALE
uvicorn verify_api:app --host 127.0.0.1 --port 8890
python mcp_server.py
```

Certificates are Ed25519-signed and **publicly independently verifiable**
against the published keys payload — no trust in this service required.
