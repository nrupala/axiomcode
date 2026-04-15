import Mathlib
import Aesop



/-- implement ternary search on a sorted array that divides the search space into three parts, prove correctness and termination -/
theorem ternary_search_correct (l : List Nat) (x : Nat) :
  Sorted l → (ternary_search l x = some i ↔ l[i]! = x) := by sorry