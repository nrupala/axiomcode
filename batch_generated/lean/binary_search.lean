import Mathlib
import Aesop



/-- implement binary search on a sorted array that returns the index of the target element or -1 if not found, prove it always returns the correct index when the element exists -/
theorem binary_search_correct (l : List Nat) (x : Nat) :
  Sorted l → (binary_search l x = some i ↔ l[i]! = x) := by sorry