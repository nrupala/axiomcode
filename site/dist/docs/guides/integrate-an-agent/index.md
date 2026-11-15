> Canonical: https://axiom-code.com/docs/guides/integrate-an-agent/ · Type: Guide · Audience: Agent builders, developers · Role packs: Developers · Version: Docs set 2026-11-14 · Last verified: 2026-11-14 · Source: REST + hosted MCP service records

# Integrate an agent

AxiomCode is built to be called by agents: one key, two doors, boolean verdicts, and error outcomes an agent can act on without guessing.

## Choose the door

- **MCP** ([reference](/docs/mcp/)) when the caller is an agent client that already speaks tools: seven tools, same semantics.

- **REST** ([reference](/docs/api/)) for everything else — scripts, backends, CI. Same key, same queue, same trial.

## Key handling

- One key per integration; keys are issued by email and shown once — store the key in your secret manager, never in prompts, artefacts, or logs.

- The service stores only a hash of your key. A lost key is replaced, not recovered.

## Outcome mapping

| Outcome | Agent behaviour |
| --- | --- | --- |
| 200 + PASSED | Proceed; record the artefact hash and (paid) the certificate serial. |
| 200 + FAILED | Stop the line: the artefact did not pass. Surface the usage record; do not retry the same bytes expecting a different verdict. |
| 202 queued | Poll job_status / the job URL with the same key until 200 or a terminal error. |
| 402 | Trial exhausted and no balance: a commercial state, not a fault. Escalate to the key's owner. |
| 429 / 413 / 401 | Slow down / shrink the artefact / fix the key. All three are NO VERDICT. |
| 504 / failed job | NO VERDICT: nothing was decided. A retry is legitimate; a conclusion is not. |

## Discipline

- Never let the agent paraphrase a verdict into a stronger claim: PASSED binds the submitted bytes under the named toolchain, nothing more ([what verification proves](/docs/explanation/what-verification-proves/)).

- Record `artifact_hash` with every outcome — it is the join key between your logs, our usage records, and any certificate.
