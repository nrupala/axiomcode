import Mathlib
import Aesop

structure CatalanNumber where

def catalan_number (n : Nat) : Nat :=

/--  -/
theorem catalan_number_correct : ∀ n : Nat, catalan_number n = (2 * n + 1) / (n + 2) * ∑ i in Finset.range n, catalan_number i * catalan_number (n - i - 1) := by sorry