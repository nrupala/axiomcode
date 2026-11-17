import Spec
import Tactics

/-!
# AxiomCode — Verified Jump Game

Promoted from `lean/drafts/jumpgame_correctness.lean` under the L2
promotion procedure (`lean/PROMOTION.md`). Authored and proved by
Arjun (Item 5B, own-hands track).

Statement-honesty record. The draft was a shell: a fieldless
`JumpGameInput` structure, a body-less `canJump`, and the statement
`canJump input = true ↔ ∃ path, List.sum path ≤ input.target` over
fields (`target`) and a path notion that exist nowhere in the shell —
ill-posed as written. The intended claim is the classic one, carried
here in full: over `List Nat` (jump lengths), the greedy
furthest-reach decision (`canJump`, via the reach function
`jumpReach`) is true exactly when the last index is reachable by
jumps, reachability being the inductive `JumpReachable`. Soundness
(`jump_sound`) and completeness (`jump_complete`) are proved
separately; the completeness invariant is the no-gap property of the
greedy reach along any reachable index.
-/

namespace AxiomCode

/-- Reachability by jumps: from a reachable index `i` you may land on any
`j` with `i < j ≤ i + l[i]!` inside the list. (For `i ≥ l.length`,
`l[i]! = 0`, so the step is self-guarding.) -/
inductive JumpReachable (l : List Nat) : Nat → Prop
  | start : JumpReachable l 0
  | step {i j : Nat} (h : JumpReachable l i) (hij : i < j)
      (hj : j ≤ i + l[i]!) (hjl : j < l.length) : JumpReachable l j

/-- The greedy reach: `jumpReach l i` = the furthest index reachable
after processing positions `0 … i-1`; processing stops growing the
reach at the first position it cannot stand on. -/
def jumpReach (l : List Nat) : Nat → Nat
  | 0 => 0
  | i + 1 => if i > jumpReach l i then jumpReach l i
             else max (jumpReach l i) (i + l[i]!)

/-- The greedy decision: the last index is within the final reach. -/
def canJump (l : List Nat) : Bool := decide (l.length - 1 ≤ jumpReach l l.length)

theorem jumpReach_succ (l : List Nat) (i : Nat) :
    jumpReach l (i + 1) = if i > jumpReach l i then jumpReach l i
      else max (jumpReach l i) (i + l[i]!) := rfl

theorem jumpReach_mono_step (l : List Nat) (i : Nat) :
    jumpReach l i ≤ jumpReach l (i + 1) := by
  rw [jumpReach_succ]
  by_cases h : i > jumpReach l i
  · rw [ite_eq_left h]; exact Nat.le.refl
  · rw [ite_eq_right h]; exact Nat.le_max_left _ _

theorem jumpReach_mono (l : List Nat) {i k : Nat} (h : i ≤ k) :
    jumpReach l i ≤ jumpReach l k := by
  induction k with
  | zero =>
    have hi0 : i = 0 := by omega
    subst hi0
    exact Nat.le.refl
  | succ k ih =>
    rcases Nat.eq_or_lt_of_le h with heq | hlt
    · have hik : i = k + 1 := by omega
      subst hik
      exact Nat.le.refl
    · exact Nat.le_trans (ih (by omega)) (jumpReach_mono_step l k)

theorem jumpReach_zero (l : List Nat) : jumpReach l 0 = 0 := rfl

/-- Soundness invariant: every index within the reach after `i` steps,
and inside the list, is genuinely reachable. -/
theorem jump_sound (l : List Nat) :
    ∀ i, i ≤ l.length → ∀ m, m ≤ jumpReach l i → m < l.length →
      JumpReachable l m := by
  intro i
  induction i with
  | zero =>
    intro _ m hm _
    have : m = 0 := by rw [jumpReach_zero] at hm; omega
    rw [this]; exact JumpReachable.start
  | succ i ih =>
    intro hi m hm hml
    have hi' : i < l.length := by omega
    rw [jumpReach_succ] at hm
    by_cases hgap : i > jumpReach l i
    · rw [ite_eq_left hgap] at hm
      exact ih (by omega) m hm hml
    · rw [ite_eq_right hgap] at hm
      have hiR : i ≤ jumpReach l i := by omega
      rcases Nat.lt_or_ge m (jumpReach l i + 1) with hmR | hmR
      · exact ih (by omega) m (by omega) hml
      · -- m is in the new part: reached by jumping from i
        have hstep : m ≤ i + l[i]! := by
          have hmax : max (jumpReach l i) (i + l[i]!) = jumpReach l i ∨
              max (jumpReach l i) (i + l[i]!) = i + l[i]! := by omega
          rcases hmax with h2 | h2
          · omega
          · omega
        exact JumpReachable.step (ih (by omega) i hiR hi') (by omega) hstep hml

/-- Completeness invariant: a reachable index `j` has no gap before it —
every `i ≤ j` is within the reach after `i` steps. -/
theorem jump_complete (l : List Nat) {j : Nat} (h : JumpReachable l j) :
    ∀ i, i ≤ j → i ≤ jumpReach l i := by
  induction h with
  | start =>
    intro i hi
    have : i = 0 := by omega
    subst this
    rw [jumpReach_zero]
    exact Nat.le.refl
  | step hrec hij hj hjl ih =>
    rename_i i j
    intro k hk
    rcases Nat.lt_or_ge k (i + 1) with hk1 | hk1
    · exact ih k (by omega)
    · -- i + 1 ≤ k ≤ j: the reach at k is at least the jump from i
      have hRi : i ≤ jumpReach l i := ih i (by omega)
      have hR1 : jumpReach l (i + 1) = max (jumpReach l i) (i + l[i]!) := by
        rw [jumpReach_succ, ite_eq_right (by omega : ¬ i > jumpReach l i)]
      have hjR : j ≤ jumpReach l (i + 1) := by
        rw [hR1]; exact Nat.le_trans hj (Nat.le_max_right _ _)
      exact Nat.le_trans (Nat.le_trans hk hjR) (jumpReach_mono l hk1)

/-- The draft's claim, in elaborable form: the greedy decision is true
exactly when the last index is reachable by jumps. -/
theorem canJump_correct (l : List Nat) :
    canJump l = true ↔ JumpReachable l (l.length - 1) := by
  constructor
  · intro h
    have hle : l.length - 1 ≤ jumpReach l l.length := of_decide_eq_true h
    cases l with
    | nil => exact JumpReachable.start
    | cons a as =>
      have hlen : (a :: as).length - 1 < (a :: as).length := by
        simp [List.length_cons]
      exact jump_sound (a :: as) (a :: as).length (by omega) _ hle hlen
  · intro h
    have h1 : l.length - 1 ≤ jumpReach l (l.length - 1) :=
      jump_complete l h (l.length - 1) (by omega)
    have h2 : jumpReach l (l.length - 1) ≤ jumpReach l l.length :=
      jumpReach_mono l (by omega)
    exact decide_eq_true_eq.mpr (by omega)


end AxiomCode
