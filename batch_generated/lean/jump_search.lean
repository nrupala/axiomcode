import Mathlib
import Aesop



/-- implement jump search that checks elements at fixed intervals then does linear search in the identified block, prove it finds the element if present -/
theorem jump_search_correct (l : List Nat) (x : Nat) :
  Sorted l → (jump_search l x = some i ↔ l[i]! = x) := by sorry