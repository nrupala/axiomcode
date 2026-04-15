import Mathlib
import Aesop



/-- implement heap sort using a max-heap data structure, prove it correctly sorts any list of natural numbers -/
theorem heap_sort_correct (l : List Nat) :
  Sorted (insertion_sort l) ∧ Permutation (insertion_sort l) l := by sorry