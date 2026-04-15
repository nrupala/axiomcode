import Mathlib
import Aesop

structure Combination (α : Type) where

def combinations (α : Type) (n : Nat) (xs : List α) : List (Combination α) :=

/--  -/
theorem combination_elements_length : ∀ {α} {c : Combination α}, c.elements.length ≤ n := by sorry