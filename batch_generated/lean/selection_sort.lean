import Mathlib
import Aesop



/-- implement selection sort that repeatedly finds the minimum element and places it at the beginning, prove the result is sorted and preserves all elements -/
theorem selection_sort_correct (l : List Nat) :
  Sorted (insertion_sort l) ∧ Permutation (insertion_sort l) l := by sorry