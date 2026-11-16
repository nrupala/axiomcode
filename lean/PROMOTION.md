# Promotion procedure — drafts → verified library (L2)

A file in `lean/drafts/` is an unverified spec draft: it may not elaborate, its
statements may be false, vacuous, or ill-posed, and nothing in the build touches
it. A file in `lean/src/Algorithms/` is a verified library entry. This document
is the only route from the first state to the second (the Class A standard).

## What a promoted module must contain

1. **Place and name.** One algorithm per module at
   `lean/src/Algorithms/<Name>.lean` (module `Algorithms.<Name>`), registered by
   an `import Algorithms.<Name>` line in the root module `lean/src/Algorithms.lean`.
   Mangled draft filenames (spaces, braces, unicode) are renamed to clean module
   names on promotion. The module keeps `namespace AxiomCode`.
2. **Real definitions.** The algorithm — and every structure it uses — is fully
   defined: structure fields present, every `def` has a body. A draft's fieldless
   structure or body-less `def` is not a starting point to patch; author the real
   definitions (author-then-prove is the job).
3. **Elaborating, meaningful statements.** Every theorem statement elaborates
   against the real definitions and is stated against the `Spec` predicates
   (growing `Spec` in the same promotion when a new predicate is needed).
4. **Statement honesty.** Prove the draft's statement *as stated* if it is true.
   If a statement is false, vacuous, or ill-posed, STOP on that statement: record
   the counterexample/defect exactly in the item report and propose the repaired
   statement there. Never weaken, re-specify, or drop a statement silently.
   Retiring a draft is a ruling recorded in the triage, not a lane decision.
5. **Imports.** `import Spec` / `import Tactics` plus targeted imports only.
   Never `import Mathlib` wholesale (the drafts' habit), and never the stale
   `AxiomCode.Spec` / `AxiomCode.Tactics` module names — the lakefile's modules
   are `Spec` and `Tactics`. File layout: the `import` lines come first in the
   file and the `/-!` module doc follows them (a doc block before an `import`
   is a compile error) — the shape `Tactics.lean` already uses.
6. **No proof debt.** Zero `sorry`, `admit`, or `native_decide` in the module
   (CI's honesty gate fails the build on `sorry`/`admit` anywhere under
   `lean/src/`; `native_decide` is banned because it rests on
   `Lean.ofReduceBool`, outside the core three axioms).
7. **Axiom check.** Every theorem in the module appears in a check file
   (`checks/`, kept with the item's records) via `#print axioms`; the output
   must list only `propext`, `Classical.choice`, `Quot.sound` (or subsets) —
   never `sorryAx`.

## Exit checks (both, every promotion)

```bash
cd lean && lake build AxiomCode        # explicit target — bare `lake build` is
                                       # vacuous on this lakefile and proves nothing
grep -rEn '\b(sorry|admit)\b' lean/src/   # must be clean
lake env lean checks/<Name>Check.lean     # #print axioms: core three only
```

## Landing

Promotion lands as one PR: the lakefile roots amendment (first promotion only),
the root module registration, the new module, this procedure's first landing,
and the deletion of the promoted draft file from `lean/drafts/` in the same PR —
progress is counted as drafts remaining and sorries remaining (lifecycle plan
§L2), and the triage is updated to match.
