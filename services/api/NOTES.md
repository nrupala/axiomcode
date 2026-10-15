# AxiomCode production build — W1 + W2

Local working copy built from `api-prototype/` (state/secret files —
keys.txt, meter.jsonl, revoked.txt — deliberately excluded). Nothing
pushed anywhere; this tree is for review/checkpoint.

## W1 — Ed25519 certification authority (`ca.py`, new)

- `CA` class: Ed25519 keypair generation; `CA.load_or_create(path)`
  persists the private key as PEM (PKCS8, no passphrase) with mode
  0600 and reloads it afterwards. Key file path from
  `AXIOMCODE_CA_KEY_FILE` (default: `ca_key.pem` beside the module).
- Certificate format v2: the prototype fields — serial, issuer
  "AxiomCode CA", valid_from / valid_until (90-day window),
  code_sha256 (the artifact hash), verified (the verdict), toolchain,
  attempts, key_id (the caller) — plus `version: 2`, `alg: "Ed25519"`,
  `kid` (CA key id = first 16 hex of SHA-256 over the raw public key),
  and `signature` (base64). Signature covers the canonical JSON of the
  cert body — `json.dumps(..., sort_keys=True)`, the same
  canonicalization certs.py used.
- `verify_certificate(cert, public_key=...)` checks the signature with
  a PUBLIC key only (accepts a key object, base64 raw key, or PEM —
  i.e. exactly what the published payload carries) plus the validity
  window; returns the prototype's `{valid, reason, payload}` shape.
  Revocation is layered on top by the servers via the store, the same
  split as X.509 vs CRL.
- `public_keys_payload()` returns the document for
  /.well-known/axiomcode-keys.json: issuer, keys[] with kid / alg /
  use / public_key (base64) / public_key_pem, published_at.
  verify_api serves it at `GET /.well-known/axiomcode-keys.json`.
- verify_api.py and mcp_server.py issue + check via Ed25519 by
  default. certs.py (HMAC) is unchanged and importable for legacy
  fixtures; v2 verification rejects HMAC certs (no Ed25519 alg).

## W2 — Durable store + hash-chained audit log (`store.py`, new)

- sqlite3 (stdlib), one DB (`AXIOMCODE_DB`, default `axiomcode.db`
  beside the module), WAL mode, lock-guarded single connection.
- Tables: certificates (serial PK, cert_json, status, issued_at),
  revocations (serial PK, reason, ts), meter_events (full billing
  entry kept as JSON + indexed columns), audit_log (seq, ts,
  event_type, payload_json, prev_hash, hash) with
  hash = SHA-256(prev_hash + canonical payload_json); genesis
  prev_hash is 64 zeros.
- record_cert / revoke append their issuance / revocation audit
  events by construction; the servers append "verification" events on
  every /check and check_certificate call.
- `verify_chain()` recomputes linkage + hashes and reports the first
  broken seq.
- billing.py: pricing math untouched (2.25× loaded-cost doctrine);
  meter() / usage_for() now route through the store. A plain path
  argument still uses the legacy JSONL code path for old fixtures.
- revoked.txt and meter.jsonl are gone from both servers.
- Temp Lean projects: created under `AXIOMCODE_WORK_ROOT` (default
  system temp) and removed in a `finally` block in both servers.

## Tests — 14 passed, 0 failed (`~/ax-venv/bin/python -m pytest tests/ -q`)

- test_ca.py (6): key persistence + 0600 perms; issue→verify
  round-trip (v2 fields, 90-day window); tampered verdict and mangled
  signature fail; wrong key fails (bad_signature); published payload
  verifies a real cert via both base64 and PEM; legacy HMAC cert
  rejected.
- test_store.py (5): record/get round-trip; revocation persists
  across store close/reopen; audit chain verifies (issuance +
  verification + revocation); one flipped byte in a stored payload is
  detected with broken_seq = 2; meter events recorded and aggregated
  (billing routes to the same numbers).
- test_wiring.py (3): REST end-to-end with a stubbed prover —
  /verify issues an Ed25519 cert, persists it, serves keys payload
  that verifies it, /check valid → revoked after operator revocation,
  /revoked lists it, temp dir cleaned, audit chain intact; MCP tools
  (verify / check_certificate / usage_report) run on the same CA +
  store; legacy HMAC module still works standalone.
- The Lean prover is stubbed in wiring tests on purpose: they prove
  CA/store wiring, not Lean. Real-Lean behaviour was proven by the
  prototype demo (2026-09-26) and the engine suite.

## Left stubbed / out of scope (later workstreams)

- Revocation is operator-side only (store.revoke) — no public revoke
  endpoint, same as the prototype; an authenticated admin path is
  still to be designed.
- API-key enforcement on REST (prototype had none; MCP bearer auth
  unchanged, including its known mutable-identity issue — W3 scope).
- Trial limits (10 cases), certificate withholding until payment,
  Stripe entitlement/webhooks, quotas, rate limits, idempotency —
  not in W1/W2 scope.
- restart_rest.sh / restart_mcp.sh were not copied from the prototype
  (they point at prototype paths/ports).
- Ruff: clean except deliberate fail-closed broad `except` catches
  (BLE001 in ca/certs/billing legacy path, S112 in the legacy JSONL
  reader) and import-order notes where sys.path setup must precede
  imports — all inherited patterns, left as-is intentionally.
