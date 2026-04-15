import Mathlib
import Aesop

structure Permutation (α : Type) where

def previous (p : Permutation ℕ) : Permutation ℕ :=

/--  -/
theorem previous_correctness : ∀ p : Permutation ℕ, IsPermutation (previous p).toList := by sorry

end Permutation