> Canonical: https://axiom-code.com/docs/explanation/ask-and-ai-boundaries/ · Type: Explanation · Audience: Users, evaluators, regulators · Role packs: Users · Guest · Regulators · Version: Docs set 2026-11-14 · Last verified: 2026-11-14 · Source: Slice-2 shell design record

# Ask & AI boundaries

Ask puts a language model next to a certification engine. The boundary between them is architectural, not promissory — this page describes where the walls are built.

## The walls

- **Judgment wall.** Verdicts are produced by the Lean kernel through the same service callables as the REST API. The model is not in that path and cannot influence it.

- **Fact wall.** Every fact on the Ask page — verdict, hash, usage, certificate fields — is rendered in code from the actual API payload. The model receives the result to explain it; it cannot edit the numbers it explains.

- **Degraded-first delivery.** If the model lane is slow or unavailable, the facts ship anyway, without an explanation. The system's failure mode is silence from the commentator, never invention by it.

- **Data wall.** Your key stays in page memory by default; your artefact goes to the verification API and nowhere else. Ask adds no telemetry and no third-party calls with your content.

## Why build it this way

"Don't trust our AI — verify our proof" is the product's founding sentence. A shell that let the model judge would contradict it in the place users are most likely to believe. So the model is given the one job it is good at — explanation — and structurally denied the job it must never hold. If you catch the explanation and the fact block disagreeing, the fact block is right and the disagreement is a reportable defect ([GitHub Issues](https://github.com/nrupala/axiomcode/issues)).

## The open residual

Explanation latency is a named residual of the shell's current soak: under load, explanations can lag or be skipped while facts arrive on time. It is recorded on the [status page](/status/) rather than smoothed over here.
