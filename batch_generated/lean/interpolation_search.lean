import Mathlib
import Aesop



/-- implement interpolation search that probes positions based on value distribution, prove it finds the element in uniformly distributed sorted arrays -/
theorem interpolation_search_correct (l : List Nat) (x : Nat) :
  Sorted l → (interpolation_search l x = some i ↔ l[i]! = x) := by sorry