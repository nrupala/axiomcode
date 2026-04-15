import Mathlib
import Aesop



/-- implement radix sort using counting sort as a subroutine for each digit, prove it correctly sorts non-negative integers -/
theorem radix_sort_correct (l : List Nat) :
  Sorted (insertion_sort l) ∧ Permutation (insertion_sort l) l := by sorry