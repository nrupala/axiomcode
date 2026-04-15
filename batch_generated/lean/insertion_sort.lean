import Mathlib
import Aesop



/-- implement insertion sort that sorts a list of natural numbers, prove the output is sorted and is a permutation of the input -/
theorem insertion_sort_correct (l : List Nat) :
  Sorted (insertion_sort l) ∧ Permutation (insertion_sort l) l := by sorry