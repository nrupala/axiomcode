> Canonical: https://axiom-code.com/docs/reference/verdicts-and-errors/ · Type: Reference · Audience: Developers, users · Role packs: Developers · Users · Version: Docs set 2026-11-14 · Last verified: 2026-11-14 · Source: Certificate Policy §4.2; live API behaviour

# Verdicts & errors

Verdicts are boolean. Everything else is an error outcome with a name, a code, and a defined effect — so a refusal can never be mistaken for a result.

## Verdicts (200)

| Verdict | Meaning | Certificate |
| --- | --- | --- | --- |
| PASSED | The artefact compiled and every proof checked under the stated toolchain. | Issued on paid verifications. |
| FAILED | The artefact was checked and did not pass — proof failure, or rejection under the engine rules (sorry, admit, native-code shortcuts, vacuous builds). | Issued on paid verifications — a FAILED certificate records the verdict honestly. |

Trial runs (first 10 cases per key) return verdicts and usage records with **no certificate**, whichever verdict.

## NO VERDICT outcomes

| Code | Outcome | Effect |
| --- | --- | --- | --- |
| 202 | Queued — every proof slot busy. Not an error: poll the job. | Resolves to a verdict or a terminal NO VERDICT. |
| 401 | Missing or invalid API key. | No run; nothing consumed. |
| 402 | Payment required — trial exhausted and no credit balance. | No run; nothing consumed. |
| 413 | Artefact over the 256 KB limit. | No run; nothing consumed. |
| 429 | Rate or concurrency refusal. | No run; retry after slowing down. |
| 504 | Engine timeout — the run exceeded its time limit. | No charge; no trial case consumed. |
| — | Queued job failed before a verdict. | Reported on the job poll; nothing certified. |

## The rule

A certificate exists only where a verdict exists. NO VERDICT outcomes produce no certificate, ever — that asymmetry is the integrity of the system, stated in the [Certificate Policy](/paperwork/certificate-policy/) (§4.2) and repeated on the [practice page](/practice/).
