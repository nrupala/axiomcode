import Mathlib
import Aesop
import Mathlib.NumberTheory



/-- implement integer square root using Newton's method, prove the result is the largest integer whose square is at most n -/
theorem integer_square_root_correct (a b : Nat) :
  integer_square_root a b = Nat.gcd a b := by sorry