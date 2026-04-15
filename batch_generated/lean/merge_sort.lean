import Mathlib
import Aesop



/-- implement merge sort using divide and conquer, prove it produces a sorted list that is a permutation of the input, prove O(n log n) time complexity bound -/
theorem merge_sort_correct (l : List Nat) :
  Sorted (insertion_sort l) ∧ Permutation (insertion_sort l) l := by sorry