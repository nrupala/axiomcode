import Spec
import Tactics

/-!
# AxiomCode — Verified Fibonacci

Promoted from `lean/drafts/nth_fibonacci_correctness (n.lean` under the
L2 promotion procedure (`lean/PROMOTION.md`). Authored and proved by
Arjun (Item 5B, own-hands track).

Statement-honesty record. The draft was a shell: a fieldless
`Fibonacci (n)` structure, a body-less `fib`, and the statement
`∃ f : Fibonacci n, f.value = fib n` quantifying over a field (`value`)
that does not exist in the shell — ill-posed as written. The library
form is the standard spec/algorithm pair: the defining recurrence as
the specification (`fibSpec`), an iterative pair loop as the algorithm
(`fibPair`, `fib`), and the correctness theorem that the loop computes
the recurrence for every `n`.
-/

namespace AxiomCode

/-- The defining recurrence (specification). -/
def fibSpec : Nat → Nat
  | 0 => 0
  | 1 => 1
  | n + 2 => fibSpec (n + 1) + fibSpec n

/-- One step of the iterative pair loop: (F n, F (n+1)) ↦ (F (n+1), F (n+2)). -/
def fibPair : Nat → Nat × Nat
  | 0 => (0, 1)
  | n + 1 => let p := fibPair n; (p.2, p.1 + p.2)

/-- The algorithm: first component of the pair loop. -/
def fib (n : Nat) : Nat := (fibPair n).1

theorem fibPair_spec (n : Nat) : fibPair n = (fibSpec n, fibSpec (n + 1)) := by
  induction n with
  | zero => rfl
  | succ n ih =>
    cases n with
    | zero => rfl
    | succ m =>
      have h2 : fibSpec (m + 3) = fibSpec (m + 2) + fibSpec (m + 1) := rfl
      have step : fibPair (m + 2) =
          ((fibPair (m + 1)).2, (fibPair (m + 1)).1 + (fibPair (m + 1)).2) := rfl
      rw [step, ih]
      show (fibSpec (m + 1 + 1), fibSpec (m + 1) + fibSpec (m + 1 + 1)) =
        (fibSpec (m + 2), fibSpec (m + 3))
      refine Prod.ext rfl ?_
      show fibSpec (m + 1) + fibSpec (m + 2) = fibSpec (m + 3)
      rw [Nat.add_comm (fibSpec (m + 1)) (fibSpec (m + 2))]
      exact h2.symm

/-- Correctness: the iterative algorithm computes the defining recurrence. -/
theorem fib_correct (n : Nat) : fib n = fibSpec n := by
  rw [fib, fibPair_spec]

theorem fibSpec_succ_succ (n : Nat) :
    fibSpec (n + 2) = fibSpec (n + 1) + fibSpec n := rfl


end AxiomCode
