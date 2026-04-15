import Mathlib
import Aesop



/-- implement exponential search that finds the range where element may be present by doubling indices then binary search, prove correctness -/
theorem exponential_search_correct (l : List Nat) (x : Nat) :
  Sorted l → (exponential_search l x = some i ↔ l[i]! = x) := by sorry