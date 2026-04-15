import Mathlib
import Aesop



/-- implement quicksort with a pivot selection strategy, prove the output is sorted and contains exactly the same elements as the input -/
theorem quick_sort_correct (l : List Nat) :
  Sorted (insertion_sort l) ∧ Permutation (insertion_sort l) l := by sorry