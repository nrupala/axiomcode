# AxiomCode — Threat Model

Filed for gate finding F-AX-4 (2026-10-23 full gate). Repo-grounded:
every claim below names the code or the deployment fact it rests on.
Updated at the public flip, 2026-11-09; the hosted MCP transport
(T8) was added with the 0.3.0 package, 2026-11-09.

## What this service is

A certification authority for software correctness. Customers submit
Lean 4 artifacts over an authenticated API; the engine compiles them
with the real Lean toolchain (pinned `leanprover/lean4:v4.35.0-rc3`);
paid verdicts are sealed into Ed25519-signed certificates that anyone
can verify against the CA's published public keys. The product's one
existential risk is **mis-issuance** — saying "verified" when it
isn't — and this model is organised around it.

## Assets, in order of value

1. **The CA private key** (`state/ca_key.pem` on the host). Whoever
   holds it can mint certificates indistinguishable from ours.
2. **The integrity of the verdict path** — the code that decides
   verified / not verified (`verify_service.py`, `core/prover`).
3. **The durable store** (`state/axiomcode.db`) — certificates,
   revocations, meter events, credit grants, the hash-chained audit
   log, and (transiently) queued jobs' submitted code.
4. **Credit balances** — grants are money. A forged grant is theft.
5. **The Stripe webhook secret** — the only credential that can turn
   an HTTP request into a credit grant.
6. **Customer API keys** — stored only as SHA-256 hashes.

## Deployment facts the model rests on

- Single host (Aetheris), one uvicorn process, loopback :8890,
  reached publicly only through a Cloudflare tunnel
  (`api.axiom-code.com`). systemd unit `axiomcode-prod`.
- All runtime state lives in `state/` inside the deployment clone:
  directory mode 700, key / env / DB files 600, and `state/` is
  git-ignored (gate F-AX-1, closed 2026-10-23) so the crown jewels
  can never be swept into a commit.
- Signing happens in the API process: the CA key is loaded at
  startup and certificates are signed only inside
  `verify_service.execute_verification`, after the proof run.
  There is no other signing path and no other host signs.
- Billing is **paused** (owner's readiness-arming rule, 2026-11-06):
  the Stripe webhook endpoint and all Payment Links are deactivated
  in Stripe, and no Stripe secret key is configured on the host —
  `/billing/checkout` answers an honest 501 in this state.

## Actors

- **Customer** — holds an API key; may submit code, check its own
  jobs and certificates, buy credits (when billing is armed).
- **Relying party** — anyone verifying a certificate offline against
  the published keys, or reading `/revoked`. Needs no account.
- **Attacker, unauthenticated** — sees only the public reads, the
  webhook route, and 401s.
- **Attacker with a stolen customer key** — bounded by that key's
  trial/balance, rate limit, and concurrency; cannot read other
  keys' jobs (404), cannot mint grants, cannot sign.
- **Operator** — provisions/revokes keys and revokes certificates
  through the store on the host; the operator key never leaves the
  owner's custody.
- **Stripe** — the only external party whose messages move money,
  and only through the signature-verified webhook.

## Threats and the controls that answer them

### T1 — Mis-issuance: a false artifact certified
- `sorry` / `admit` / axiom smuggling: the prover's axiom audit
  fails closed; the gate's judgment differential (true / false /
  sorry / axiom-smuggle / ∀ corpus) re-proves this at every gate.
- Vacuous builds: rejected by the proof runner (a target that
  compiles nothing is not a proof).
- Trial keys can never receive certificates — enforced in
  `execute_verification` before issuance, proven in acceptance.
- A wrong verdict discovered later is answered by **public
  revocation**: serial on `/revoked`, `/check` reports revoked.

### T2 — CA key theft
- File 600 in a 700 directory, git-ignored, on a host whose only
  public path in is the tunnel to the loopback API.
- Residual risk, stated plainly: the key is on the same host and in
  the same process as the public API (isolation tier
  *in-process-exception*, accepted in `gate.yaml`). A full host
  compromise is a CA compromise. The scale-up step — a separated
  signing service the API can ask but not read — is owed before
  this product carries volume that justifies it, and the public
  security page does not claim it exists yet.

### T3 — Forged or replayed payment events
- Webhook signatures verified (Stripe HMAC) before the event body
  is read; bad signatures answer 400 and grant nothing (gate-probed
  2026-10-23).
- Grants are idempotent on the Stripe session id — a replayed
  `checkout.session.completed` grants zero the second time
  (acceptance-proven). Refunds reverse the original grant.
- Checkout sessions are bound to the caller's key hash via
  `client_reference_id`; a session paid by one person cannot credit
  another key.

### T4 — Free compute / denial of service
- Payment is checked **before** proving: trial exhausted + no
  balance answers 402 and no proof runs.
- Per-key rate limit (60/min), per-key concurrency (2), global
  proof slots (4), code size cap (256 KB), proof wall-clock cap
  (600 s), each proof in a fresh temporary project removed in a
  `finally` block.
- Excess demand joins the durable FIFO queue with a checkable
  position (F-AX-5) rather than piling onto the host.

### T5 — Cross-customer exposure
- Caller identity is the key's hash, taken only from the
  credential; request bodies carry no identity at all.
- Queued jobs are readable only by the submitting key; other keys
  get 404. Job code is cleared from the store at completion.
- Certificates are public-by-design documents (that is what makes
  them independently verifiable); they bind a code **hash**, never
  the code.

### T6 — Tampering with the record
- The audit log is hash-chained (v2 format binds event type and
  timestamp as well as payload); `verify_chain()` reports the first
  broken link. Meter events and grants are append-only rows the
  balance derives from — there is no balance field to edit.

### T7 — Malicious submissions
- Submitted Lean code is compiled, not trusted: size and time caps,
  single-use project directory. Residual risk, stated plainly:
  proofs run as the service user on the host, not inside a separate
  sandbox — a toolchain-level escape is a host-level event. The
  caps and the fresh-directory discipline bound the ordinary cases;
  sandboxing the prover (the burst-worker design runs prover-only
  workers off-host) is the named next step, gated separately.

### T8 — The hosted MCP transport (agent callers)
- The hosted MCP leg (`mcp_hosted.py`, mounted at `/mcp` in this
  same process) is a second transport onto the same store, CA and
  queue. It is declared as its own pathway (PW-MCP in `gate.yaml`,
  gate record axiomcode-mcp-slice1-2026-11-09, Ruling 2): a new
  transport with its own auth middleware is a distinct gate, even
  though every tool calls the same `verify_api` callables the REST
  routes call, so admission, eligibility, metering and revocation
  cannot drift between legs.
- Authentication runs in a pure-ASGI middleware
  (`KeyAuthMiddleware`) BEFORE the MCP app sees the request: the
  same API keys, resolved by the same `authenticate_key`; a
  missing, unknown or revoked key gets one identical 401 body (no
  validity oracle). The caller's identity travels in a
  request-scoped ContextVar — never a module global — and tools
  take no identity parameter, so no caller can act under another
  key.
- The transport is stateless (no server-side sessions to pin or
  hijack; queued jobs are durable in the store, not in a session),
  answers JSON, and runs with DNS-rebinding protection ON: a Host
  allowlist (loopback + `api.axiom-code.com`, extensible via
  `AXIOMCODE_MCP_ALLOWED_HOSTS`); other Hosts are refused 421
  before auth.
- Admission is queue-shared with REST: eligibility (trial/balance)
  is decided before admission on this leg too, so an agent can
  neither run nor queue a proof it could not pay for, and its jobs
  are readable only by the submitting key (other keys and unknown
  ids answer the same not_found body).
- Declared difference (gate-accepted, Ruling 3): on auth failure
  this leg's 401 body uses the MCP `{"error": ...}` envelope where
  REST uses FastAPI's `{"detail": ...}`; every post-auth body is
  the REST body verbatim.
- The legacy standalone server (`mcp_server.py`) is NOT this leg:
  recorded named drift (pre-queue admission, module-global
  identity), deployed nowhere, and it must never be deployed
  as-is; hosting it would be a new gate declaration.

### T9 — The interactive shell (conversational layer)
- The Ask shell (`services/api/shell.py`; routes `/shell/turn` and
  `/shell/jobs/{job_id}`; site page `/ask/`) puts a language model in
  front of the service for human callers. It is declared as its own
  pathway (PW-SHELL in `gate.yaml`, gate package 0.4.0): a new face
  is a distinct gate, even though every action behind it calls the
  same `verify_api` callables as REST and MCP, so admission, trial
  counting, metering and revocation cannot drift between legs.
- The named threat is judgment corruption by conversation: a user —
  or text injected through submitted code, a pasted certificate, or
  a smuggled conversation turn — steering the model into misstating,
  softening, or inventing a verdict. The control is structural, not
  a prompt: verdicts, account numbers, prices and revocation state
  enter a turn ONLY as fact blocks rendered in code from API
  payloads (two registers built from the same values), the model's
  text returns on a separate channel that nothing parses for facts,
  and the page renders facts and explanation in separate regions.
  History is sanitized in code (only user/assistant roles survive;
  a smuggled 'system' turn is dropped). The model holds no tools and
  no store access, and there is no action that re-judges a verdict:
  resubmission is a new verification with its own verdict.
- Trial semantics are pinned by the renderer, not the model: a
  verdict body carrying a trial block or a null certificate renders
  "no certificate was issued", and a certificate's serial and
  validity dates enter text only from the payload.
- The caller's key is authenticated by the same dependency as REST
  before any turn runs; it is never stored, logged, echoed, or
  placed in the model context (behaviour-tested, including a scan
  of the state DB after turns). Conversation content goes only to
  the model endpoint on the same host (loopback); the model is
  stateless between turns.
- Browser access rides the CORS posture of the 0.4.0 package: the
  site's origin only, on the browser-facing paths only
  (`/verify`, `/check`, `/revoked`, `/shell`). Before this package
  the API had no CORS leg at all and the site's own pages were
  blocked by browsers — the absence was the larger risk; the scoped
  middleware is the control, and it changes no authentication rule.
- Residual, stated plainly: the model's explanations can still be
  clumsy or, within a true fact set, badly worded. The user-leg
  walk (a first-time customer talking to the shell) is the control
  for explanation quality; it is owed before this face is called
  proven, and it cannot affect verdicts either way.

## Out of scope / not claimed

- No protection is claimed against a compromised host OS (see T2).
- The legacy standalone MCP server (`mcp_server.py`) is not
  deployed and is recorded named drift (see T8); it is not part of
  this model's attack surface. The hosted MCP leg IS in scope —
  T8 above and pathway PW-MCP in `gate.yaml`.
- Burst proving workers do not exist yet in production. Their
  design invariant — a worker's wrong verdict cannot mint a
  certificate, because issuance stays behind this host's own
  checks — must be behaviour-proven at their own gate before they
  carry a single job.
