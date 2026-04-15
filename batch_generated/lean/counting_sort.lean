import Mathlib
import Aesop



/-- implement counting sort for integers in a known range, prove it produces a stable sorted output -/
theorem counting_sort_correct (l : List Nat) :
  Sorted (insertion_sort l) ∧ Permutation (insertion_sort l) l := by sorry