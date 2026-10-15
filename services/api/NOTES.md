# AxiomCode production build — W1 + W2, then W3 + W4 (code) + W5

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

## Left stubbed / out of scope after W1/W2 (status updated by W3–W5 below)

- Revocation is operator-side only (store.revoke) — no public revoke
  endpoint, same as the prototype; an authenticated admin path is
  still to be designed.
- ~~API-key enforcement on REST~~ — done in W3 (below).
- ~~Trial limits (10 cases), certificate withholding until payment,
  Stripe entitlement/webhooks, quotas, rate limits~~ — done in
  W3/W4/W5 (below). Idempotency: webhook grants are idempotent on
  Stripe ids; request-level idempotency keys are still open.
- restart_rest.sh / restart_mcp.sh were not copied from the prototype
  (they point at prototype paths/ports).
- Ruff: clean except deliberate fail-closed broad `except` catches
  (BLE001 in ca/certs/billing legacy path, S112 in the legacy JSONL
  reader) and import-order notes where sys.path setup must precede
  imports — all inherited patterns, left as-is intentionally.

## W3 — Access control + trial enforcement

- **API keys** (`store.py`): `Store.create_api_key(label)` returns a
  plaintext `axk_<token_urlsafe(32)>` exactly once; the store keeps
  ONLY its SHA-256 hash (`api_keys`: key_hash PK, label, created_at,
  revoked) plus an audit event carrying hash + label. Operator CLI:
  `python -m store create-key --label "Acme"` (prints the key once).
  `revoke_api_key(key_hash)` revokes by hash. Nothing anywhere logs
  or persists a plaintext key.
- **Identity = key hash.** Everywhere a caller identity is recorded
  (meter_events.key_id, certificate key_id, limits, grants) it is the
  key's SHA-256 hash — stable and joinable, not a secret. Request
  bodies carry no identity at all.
- **REST**: `/verify` and `/check` require a key (`X-Api-Key` header
  or `Authorization: Bearer`); missing / unknown / revoked → 401.
  The old `rest-anonymous` metering identity is gone. `/check` is a
  read: it consumes no trial case and no credits. Open endpoints:
  `/health`, `/.well-known/axiomcode-keys.json`, and `/revoked`
  (the public CRL — publishing it is the point, same as X.509).
- **MCP**: bearer auth now validates against the store, replacing
  keys.txt / `billing.load_keys` (the mutable-identity hole is
  closed: `_KEY` binds the authenticated key's hash per request, and
  no tool takes an identity parameter, so callers cannot meter or
  spend as another key). The server process's own key comes from
  `AXIOMCODE_API_KEY` and is provisioned at startup if unknown
  (`ensure_api_key`, label `AXIOMCODE_API_KEY_LABEL`, default
  "mcp-server"); a store revocation is never undone by a restart.
- **Trial** (shared flow, `verify_service.execute_verification` —
  both servers run the same code so the interfaces cannot drift):
  balance = sum(credit_grants) − metered credits used
  (`store.balance_for`). Balance > 0 → paid case (proof, meter,
  issue + record cert). Else, while trial cases used < 10 → free
  trial case: proof runs, a zero-credit meter event flagged
  `trial = 1` is recorded (that flag is how cases are counted), the
  response is `{verified, attempts, certificate: None, usage,
  trial: {cases_used, cases_left, certificates: "unlock with a
  credit pack"}}` and NO certificate is recorded. Trial exhausted
  and balance ≤ 0 → refused with 402 (REST) / a payment_required
  error object (MCP) BEFORE the prover is invoked — no free compute.
  Edge: a positive-but-tiny balance takes the paid path and may go
  slightly negative on that call (metering is post-hoc by design).
- **Limits** (`limits.py`, per-process state): sliding-window rate
  limit per key, default 60 req/min (`AXIOMCODE_RATE_LIMIT_PER_MIN`)
  → 429; per-key proof concurrency cap, default 2
  (`AXIOMCODE_MAX_CONCURRENT_PROOFS`), non-blocking → 429 /
  too_many_concurrent_proofs.
- **Store additions**: tables `api_keys`, `credit_grants`
  (external_id UNIQUE → grant idempotency), `meter_events.trial`
  column (added by an idempotent ALTER migration for W2 stores).
  `grant_credits` returns False on a duplicate external_id instead
  of raising, so webhook replays are naturally no-ops.
- **PR #21 hardening fixes**: (i) `ca.issue()` applies CA-fixed
  fields (version, alg, kid, serial, issuer, validity window) AFTER
  the subject spread — subjects can no longer override them, and a
  subject-supplied "signature" is always replaced; (ii)
  `verify_certificate` rejects a cert whose kid ≠ the verifying
  key's kid (reason `unknown_kid`) after the signature check, so a
  wrong key still reports `bad_signature` as before; (iii)
  `record_cert` / `revoke` write the state row AND their audit event
  in ONE transaction (rollback on error); (iv) **audit chain format
  v2**: hash = SHA-256(prev_hash | event_type | ts | canonical
  payload) — re-typing or re-dating a stored event now breaks the
  chain too. The store is pre-production, so no migration of W2
  chains is owed; a W2-created DB must not be mixed with v2 writers.

## W4 — Stripe billing (code layer only; no live calls anywhere)

- `stripe_billing.py`: pack catalogue starter 1,000cr/$10, growth
  5,000cr/$50, scale 20,000cr/$200 (doctrine unchanged); price IDs
  from `AXIOMCODE_STRIPE_PRICE_STARTER/_GROWTH/_SCALE`.
  `build_checkout_payload(pack, key_hash)` is pure; the session
  carries the key HASH as client_reference_id + metadata (never the
  plaintext key). The API call sits behind `StripeClient`
  (lazy SDK import) — tests inject a fake client.
- Webhook core `handle_webhook(store, payload, signature,
  verify_signature)`: the route wires verify_signature to
  `stripe.Webhook.construct_event`; tests pass a trivial callable.
  `checkout.session.completed` → grant the pack's credits with
  external_id = session id (replays grant nothing), plus a
  zero-credit link row keyed by the session's payment_intent id
  (source `stripe_pi_for:<session id>`) so refunds can find the
  grant. `charge.refunded` → negative grant reversing the original
  (external_id `<session>:refund:<charge id>`, replay-safe);
  refunds for unknown payments return handled=False for deploy-time
  monitoring to alert on.
- Route `POST /billing/webhook` in verify_api.py: without the
  `stripe` package or `STRIPE_WEBHOOK_SECRET` it answers 501 with a
  clear log line rather than accepting unverifiable events.
- **Still stubbed (deploy-time)**: creating the products/prices in
  the live Stripe account, setting the price-id env vars,
  `STRIPE_SECRET_KEY` / `STRIPE_WEBHOOK_SECRET`, and endpoint
  registration in the Stripe dashboard. No network call exists in
  any tested path.

## W5 — Job isolation

- Submission size cap: `AXIOMCODE_MAX_CODE_BYTES` (default 262144)
  → 413 / code_too_large, checked before proving on both interfaces.
- Proof timeout: `AXIOMCODE_PROOF_TIMEOUT_S` (default 600) enforced
  in `verify_service.run_proof` around the prover call → 504 /
  proof_timeout. Implemented with a worker thread (threads cannot be
  killed): on timeout the response goes out, the temp project is
  removed by the finally block, and the orphaned prover thread dies
  against the removed directory. Hard-kill process isolation is a
  possible future step if abuse shows up.
- Per-job temp projects stay unique (`mkdtemp` under
  `AXIOMCODE_WORK_ROOT`) and are always removed; shared mutable
  state between concurrent jobs is only the store (single
  connection + lock, WAL) and the limiter/gate (internally locked).

## Env vars (new in W3–W5)

- `AXIOMCODE_TRIAL_CASES` (10), `AXIOMCODE_RATE_LIMIT_PER_MIN` (60),
  `AXIOMCODE_MAX_CONCURRENT_PROOFS` (2), `AXIOMCODE_MAX_CODE_BYTES`
  (262144), `AXIOMCODE_PROOF_TIMEOUT_S` (600)
- `AXIOMCODE_API_KEY`, `AXIOMCODE_API_KEY_LABEL` (MCP server key)
- `AXIOMCODE_STRIPE_PRICE_STARTER/_GROWTH/_SCALE`,
  `AXIOMCODE_CHECKOUT_SUCCESS_URL`, `AXIOMCODE_CHECKOUT_CANCEL_URL`,
  `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET` (deploy-time)

## Tests — 40 passed, 0 failed (also clean under
## `-W error::DeprecationWarning`)

- test_access.py (9, new): 401 for missing/unknown key and for a
  caller-supplied body identity; X-Api-Key and Bearer both work;
  revoked key → 401; /health, keys payload, /revoked stay open;
  /check consumes no trial case and no credits; full trial flow —
  10 free cases with certificate=None and zero credits, no cert
  recorded, 11th refused 402 with the prover never invoked, grant →
  cert issued; rate limit 429; size cap 413; proof timeout 504 with
  the temp dir cleaned up.
- test_billing_flow.py (10, new): balance = grants − metered
  credits; trial meter events don't spend balance; grant idempotency
  on external_id; only key hashes are stored; checkout payload shape
  + error cases; fake-client session creation; webhook grants pack
  credits exactly once across replays; refund reverses exactly once;
  unknown refund / unhandled event types; bad signature propagates;
  webhook route answers 501 until Stripe is configured.
- test_hardening.py (7, new): subject cannot override issuer /
  serial / kid / alg / version / validity in issue(); cert signed by
  one key but naming another's kid is rejected (`unknown_kid`);
  chain detects event_type tamper (broken_seq 1) and ts tamper
  (broken_seq 2); concurrency gate unit behaviour; a second
  concurrent proof for the same key is rejected while one runs;
  MCP trial flow + tools expose no identity parameter.
- test_ca.py / test_store.py / test_wiring.py (14, updated):
  wiring tests now authenticate (provisioned key + fixture grant)
  and assert hash-keyed identity; all W1/W2 behaviour unchanged.
- Smoke (manual, not in suite): `python -m store create-key` issues
  a key whose plaintext appears nowhere in the DB file; MCP server
  with `AXIOMCODE_API_KEY` set provisions and authenticates it.
- Ruff: `ruff check` is clean for all service modules under the repo
  config (verified in a repo-shaped tree — sibling-module import
  order is first-party-sensitive, so it must be checked in-repo, not
  from this directory). New files are `ruff format`-clean; store.py
  and the older test files keep their W1/W2 formatting (ruff format
  is not the repo gate for this subtree, and restyling them would
  bury the functional diff). Pre-existing exceptions unchanged:
  E741 in legacy certs.py, test-file import grouping as merged.
