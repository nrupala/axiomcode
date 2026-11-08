# What AxiomCode rejects, and why

Policy version: see `core/proof_policy.py` → `POLICY_VERSION` (also recorded on every certificate as `policy_version`).

AxiomCode checks proofs written by people and by AI models. A proof that "passes" by cheating is worse than no proof. Every submission goes through three layers, in order:

1. **Policy screen** (`core/proof_policy.py`), before Lean runs. A BLOCK finding rejects the submission unproved, with the rule and the line number.
2. **Sandboxed elaboration** (`core/sandbox.py`). Lean runs under bubblewrap with no network, a read-only root and the project directory as the only writable path, plus memory, process, file-size and CPU limits. The hosted API runs in `required` mode: no sandbox means no run.
3. **Axiom audit** (`core/prover.py: audit_axioms`). `#print axioms` runs on every theorem, including those carrying attributes or modifiers. Anything outside `propext`, `Classical.choice`, `Quot.sound` and `funext` fails.

| Rule | Severity | What it stops |
|---|---|---|
| exec.eval / exec.run_cmd / exec.initialize / exec.io / exec.extern / exec.unsafe | BLOCK | Code running on the verifier host at elaboration time |
| exec.exit | BLOCK | `#exit` truncating the file so later theorems are never checked |
| meta.syntax | BLOCK | Custom syntax, macros and elaborators that disguise what a declaration proves |
| import.disallowed | BLOCK | Imports outside AxiomCode, Mathlib, Std, Batteries, Init, Aesop, Qq and Plausible (notably `Lean.*`, which unlocks metaprogramming and IO) |
| cheat.skip_kernel / cheat.debug_option | BLOCK | Options that switch off or alter the kernel check |
| cheat.native_decide | BLOCK | Trusting the compiler instead of the kernel (`Lean.ofReduceBool`) |
| cheat.sorry_ax | BLOCK | Direct `sorryAx` |
| cheat.axiom_decl | BLOCK | User-declared axioms |
| audit.private_theorem | BLOCK | Theorems whose mangled names the axiom audit cannot address |
| cheat.opaque / cheat.implemented_by / audit.example | WARN | Reported; does not block |

The hostile corpus that proves each rule fires lives in `tests/test_proof_policy.py`. It needs no Lean toolchain and runs in CI.

**Limits, stated plainly.** The screen is pattern-based. It is a first line, not a proof of safety, which is why the sandbox exists. Blocking custom syntax also rejects some honest files that define their own notation. That trade is deliberate for an untrusted-input service.
