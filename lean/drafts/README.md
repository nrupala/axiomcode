# Unverified drafts

Every `.lean` file here is an **unverified spec draft**: it was produced by the
spec generator (or a proof-search run that did not complete) and has NOT been
machine-checked. Files here typically end in `by sorry` or are incomplete.

Do not treat drafts as verified proofs. When a draft's proof is completed and
machine-checked by Lean 4 (zero `sorry`/`admit`), it graduates to
`../src/Algorithms/` — the verified library. CI enforces this: any
`sorry`/`admit` under `lean/src/` fails the build.
