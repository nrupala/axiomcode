import Spec
import Tactics

/-!
# AxiomCode — Verified Greatest Common Divisor (Euclid's Algorithm)

A formally verified Euclidean algorithm with correctness proof.

Promoted from `lean/drafts/gcd_algorithm_correctness (a b.lean` under the
L2 promotion procedure (`lean/PROMOTION.md`). The draft's single statement
is proved exactly as stated. The draft's shells are authored for real: the
state structure gains its two fields, `gcd_step` gains its body, and
`gcd_algorithm` is the state run the draft's design sketches. The draft's
wholesale imports (`Mathlib`, `Aesop`) are corrected to the Class A form;
the proof needs only Lean core's `Nat.gcd` API.
-/

namespace AxiomCode

/-- State of Euclid's algorithm: the current pair `(a, b)`. -/
structure EuclideanAlgorithmState where
  a : Nat
  b : Nat
deriving DecidableEq, Repr

/-- One step of Euclid's algorithm: `(a, b) ↦ (b, a % b)`. -/
def gcd_step (state : EuclideanAlgorithmState) : EuclideanAlgorithmState :=
  ⟨state.b, state.a % state.b⟩

/-- Run Euclid's algorithm from a state: step until the second component
is `0`, then read off the first. Termination: a step replaces `b` by
`a % b`, which is strictly smaller whenever `b > 0`. -/
def gcdRun : EuclideanAlgorithmState → Nat
  | ⟨a, 0⟩ => a
  | ⟨a, b + 1⟩ => gcdRun (gcd_step ⟨a, b + 1⟩)
termination_by s => s.b
decreasing_by exact Nat.mod_lt _ (Nat.succ_pos _)

/-- The gcd algorithm on a pair of natural numbers: Euclid's algorithm
run from the initial state `⟨a, b⟩`. -/
def gcd_algorithm (a b : Nat) : Nat :=
  gcdRun ⟨a, b⟩

theorem gcdRun_zero (a : Nat) : gcdRun ⟨a, 0⟩ = a := by
  rw [gcdRun]

theorem gcdRun_succ (a b : Nat) :
    gcdRun ⟨a, b + 1⟩ = gcdRun (gcd_step ⟨a, b + 1⟩) := by
  rw [gcdRun]

/-- One step does not change the run's result (for a non-terminal state):
the run is an iteration of `gcd_step`. -/
theorem gcdRun_step (s : EuclideanAlgorithmState) (h : s.b ≠ 0) :
    gcdRun (gcd_step s) = gcdRun s := by
  obtain ⟨a, b⟩ := s
  cases b with
  | zero => exact absurd rfl h
  | succ b => exact (gcdRun_succ a b).symm

/-- Correctness of the state run: it computes `Nat.gcd` of the state's
components. Proof by induction on a bound for the second component
(strong induction in bounded form), using `Nat.gcd_rec` and
commutativity at each step. -/
theorem gcdRun_correct (s : EuclideanAlgorithmState) :
    gcdRun s = Nat.gcd s.a s.b := by
  have key : ∀ k (s : EuclideanAlgorithmState), s.b < k →
      gcdRun s = Nat.gcd s.a s.b := by
    intro k
    induction k with
    | zero => intro s hs; exact absurd hs (Nat.not_lt_zero _)
    | succ k ih =>
      intro s hs
      obtain ⟨a, b⟩ := s
      have hb : b < k + 1 := hs
      cases b with
      | zero =>
        rw [gcdRun_zero]
        exact (Nat.gcd_zero_right a).symm
      | succ b =>
        rw [gcdRun_succ]
        show gcdRun ⟨b + 1, a % (b + 1)⟩ = Nat.gcd a (b + 1)
        have hlt : a % (b + 1) < k := by
          have h1 : a % (b + 1) < b + 1 := Nat.mod_lt a (Nat.succ_pos b)
          omega
        rw [ih ⟨b + 1, a % (b + 1)⟩ hlt]
        calc Nat.gcd (b + 1) (a % (b + 1))
            = Nat.gcd (a % (b + 1)) (b + 1) := Nat.gcd_comm _ _
          _ = Nat.gcd (b + 1) a := (Nat.gcd_rec (b + 1) a).symm
          _ = Nat.gcd a (b + 1) := Nat.gcd_comm _ _
  exact key (s.b + 1) s (Nat.lt_succ_self _)

/-- The draft's statement, exactly as stated: the algorithm computes
`Nat.gcd`. -/
theorem gcd_algorithm_correctness (a b : Nat) :
    gcd_algorithm a b = Nat.gcd a b :=
  gcdRun_correct ⟨a, b⟩

/-- The result divides the first argument. -/
theorem gcd_algorithm_dvd_left (a b : Nat) : gcd_algorithm a b ∣ a := by
  rw [gcd_algorithm_correctness]
  exact Nat.gcd_dvd_left a b

/-- The result divides the second argument. -/
theorem gcd_algorithm_dvd_right (a b : Nat) : gcd_algorithm a b ∣ b := by
  rw [gcd_algorithm_correctness]
  exact Nat.gcd_dvd_right a b

/-- Any common divisor of `a` and `b` divides the result — with
`gcd_algorithm_dvd_left`/`gcd_algorithm_dvd_right`, the result is the
greatest common divisor. -/
theorem dvd_gcd_algorithm {d a b : Nat} (ha : d ∣ a) (hb : d ∣ b) :
    d ∣ gcd_algorithm a b := by
  rw [gcd_algorithm_correctness]
  exact Nat.dvd_gcd ha hb

/-- The algorithm is commutative in its arguments. -/
theorem gcd_algorithm_comm (a b : Nat) :
    gcd_algorithm a b = gcd_algorithm b a := by
  rw [gcd_algorithm_correctness, gcd_algorithm_correctness, Nat.gcd_comm]

end AxiomCode
