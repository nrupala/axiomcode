import Mathlib
import Aesop



/-- implement a simplified timsort that merges sorted runs, prove the output is sorted and stable -/
theorem tim_sort_correct (l : List Nat) :
  Sorted (insertion_sort l) ∧ Permutation (insertion_sort l) l := by sorry