import Mathlib
import Aesop



/-- implement shell sort with diminishing gap sequence, prove the final array is sorted -/
theorem shell_sort_correct (l : List Nat) :
  Sorted (insertion_sort l) ∧ Permutation (insertion_sort l) l := by sorry