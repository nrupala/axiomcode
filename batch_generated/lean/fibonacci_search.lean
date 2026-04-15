import Mathlib
import Aesop



/-- implement fibonacci search using fibonacci numbers to divide the search range, prove it correctly finds elements in sorted arrays -/
theorem fibonacci_search_correct (l : List Nat) (x : Nat) :
  Sorted l → (fibonacci_search l x = some i ↔ l[i]! = x) := by sorry