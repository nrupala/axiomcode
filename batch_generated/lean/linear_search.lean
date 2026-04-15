import Mathlib
import Aesop



/-- implement linear search that finds the first occurrence of an element in a list, prove it returns the correct index or indicates absence -/
theorem linear_search_correct (l : List Nat) (x : Nat) :
  Sorted l → (linear_search l x = some i ↔ l[i]! = x) := by sorry