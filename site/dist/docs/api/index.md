> Canonical: https://axiom-code.com/docs/api/ · Type: Reference · Audience: Developers, agents · Role packs: Developers · Version: Docs set 2026-11-14 · Last verified: 2026-11-14 · Source: Live OpenAPI (canonical) + service behaviour

# API — machine-first docs

Base: `https://api.axiom-code.com` · Auth: `X-Api-Key` header on every call except the public endpoints.

**Contract of record:** the live OpenAPI document at [https://api.axiom-code.com/openapi.json](https://api.axiom-code.com/openapi.json) (OpenAPI 3.1, served by the API itself) is canonical. This page is the human-readable rendering of the same contract; the summary JSON kept on this site for offline reading is labelled a summary and never overrides the live document.

| Endpoint | What |
| --- | --- | --- |
| POST /verify | Submit a Lean artefact {"code": "..."}. 200 → verdict + usage (+ certificate when paid). 202 → queued, poll the job. |
| GET /verify/jobs/{job_id} | Poll a queued job (same key). 202 while queued/running; 200 with the result; a failed job reports a NO VERDICT outcome. |
| POST /check | Validate a certificate {"certificate": {...}} — signature, validity window, revocation. |
| GET /revoked | Public revocation list. No auth. |
| GET /.well-known/axiomcode-keys.json | CA public keys. No auth. |
| GET /health | Service health. No auth. |
| POST /shell/turn · GET /shell/jobs/{job_id} | The Ask shell's backend — orchestrates the same verify/check callables; the shell's facts are rendered in code from these payloads. |

Billing endpoints (`POST /billing/checkout`, `POST /billing/webhook`) exist in the route table and answer 501 while billing is paused.

## Rules of the road

- **Verdicts are boolean** — PASSED or FAILED. Errors are [NO VERDICT outcomes](/docs/reference/verdicts-and-errors/) (401/402/413/429/504, failed jobs) and never carry certificates.

- **Trial:** the first 10 cases per key return verdicts + usage, never certificates. Certificates ride paid verifications (packs not yet on sale — [pricing](/pricing/)).

- **Queue:** bounded proof slots; saturation answers 202 with a position. See [use the queue](/docs/guides/use-the-queue/).

- **Metering:** 0.9 credits per engine second; timeouts and refusals are free. See [reconcile metering](/docs/guides/reconcile-metering/).

- **Limits:** 256 KB artefacts; keys stored as hashes only. See [keys & limits](/docs/reference/keys-and-limits/).

- **MCP instead?** The same service is exposed as seven tools at `https://api.axiom-code.com/mcp/` — see the [MCP reference](/docs/mcp/).

```
curl -X POST https://api.axiom-code.com/verify \
  -H "X-Api-Key: $AXIOMCODE_KEY" -H "Content-Type: application/json" \
  -d '{"code": "theorem t (a b : Nat) : a + b = b + a := Nat.add_comm a b"}'

→ {"verified": true, "job_id": null, "artifact_hash": "sha256:…",
    "attempts": […], "usage": {…},
    "trial": {"used": 1, "limit": 10}, "certificate": null}
```
