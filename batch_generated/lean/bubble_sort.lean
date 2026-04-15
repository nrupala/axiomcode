import Mathlib
import Aesop



/-- implement bubble sort that repeatedly swaps adjacent elements if they are in wrong order, prove it terminates and produces a sorted list -/
theorem bubble_sort_correct (l : List Nat) :
  Sorted (insertion_sort l) ∧ Permutation (insertion_sort l) l := by sorry