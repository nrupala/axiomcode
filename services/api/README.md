# AxiomCode API & CA prototype

**Status: prototype — not production.** Built 2026-09-26 to prove the product loop
(real Lean compile → verdict → certificate → independent check → revocation).
It is version-controlled here as a checkpoint before the production rebuild.

## What it does

- `verify_api.py` — FastAPI REST: `POST /verify`, `POST /check`, `GET /revoked`
- `mcp_server.py` — MCP server: `verify`, `check_certificate`, `pricing`, `usage_report`
- `certs.py` — CA prototype: serials, `AxiomCode CA` issuer, 90-day validity, revocation list
- `billing.py` — compute-time metering, full-cost component model, 2.25× loaded-cost multiple

## Known gaps (must be fixed before launch)

- Certificates use HMAC with a symmetric secret — **not publicly independently
  verifiable**. Production needs Ed25519 signing with published verification keys.
- No API-key authentication (REST meters under `rest-anonymous`).
- MCP request identity uses mutable global state (unsafe under concurrency).
- Metering is plain JSONL, not the promised hash-chained tamper-evident log.
- Revocation is a local text file, not durable storage.
- Temp Lean projects are not cleaned up.
- Trial count, certificate withholding, payment entitlement, rate limits, quotas,
  idempotency, abuse controls, and refunds are not implemented.
- Pricing component values are placeholders (the 2.25× doctrine is locked).

## Running it (local dev only)

```bash
python verify_api.py   # 127.0.0.1:8091
python mcp_server.py   # 127.0.0.1:8092
```

Never expose these ports publicly; there is no authentication.
