import Mathlib
import Aesop
import Mathlib.NumberTheory



/-- implement a function that checks if a number is perfect (sum of proper divisors equals the number), prove correctness for all inputs -/
theorem perfect_number_check_correct (a b : Nat) :
  perfect_number_check a b = Nat.gcd a b := by sorry