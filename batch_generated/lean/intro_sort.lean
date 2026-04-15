import Mathlib
import Aesop



/-- implement introsort that switches from quicksort to heapsort when recursion depth exceeds a limit, prove it always terminates with a sorted array -/
theorem intro_sort_correct (l : List Nat) :
  Sorted (insertion_sort l) ∧ Permutation (insertion_sort l) l := by sorry