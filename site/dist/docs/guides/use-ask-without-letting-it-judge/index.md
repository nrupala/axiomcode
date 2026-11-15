> Canonical: https://axiom-code.com/docs/guides/use-ask-without-letting-it-judge/ · Type: Guide · Audience: Users, evaluators · Role packs: Users · Guest · Version: Docs set 2026-11-14 · Last verified: 2026-11-14 · Source: Slice-2 shell design record; practice page

# Ask without letting it judge

Ask is a shell over the same verify calls, with a model that explains. The architecture keeps the model away from the verdict; this guide keeps your reading habits the same way.

## Who does what

- **The engine judges.** Verdicts come from the Lean kernel through the same callables the API uses.

- **Code renders the facts.** Verdict, artefact hash, usage, and certificate facts on the Ask page are rendered in code from the actual API payload — the model cannot alter a digit.

- **The model explains.** It puts the result into words, suggests next steps, and answers questions about the outcome. Its words are commentary, never evidence.

## Reading Ask well

- Trust the fact block; enjoy the explanation. If the two ever seem to differ, the fact block is the record — and the difference is worth an [error report](https://github.com/nrupala/axiomcode/issues).

- Explanations are **degraded-first**: if the model lane is slow or down, the facts still arrive, without an explanation. A missing explanation is a known residual of the current soak, not a failed verification.

- Ask keeps your key in page memory by default; nothing about your artefact is sent anywhere except the verification API.

## What Ask is not

Ask is not a second opinion and not an auditor. It will not certify intent, review your specification for meaning, or find the bug your proof forgot to state. For the bounds, read [Ask & AI boundaries](/docs/explanation/ask-and-ai-boundaries/).
