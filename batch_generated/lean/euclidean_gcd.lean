import Mathlib
import Aesop
import Mathlib.NumberTheory



/-- implement the Euclidean algorithm for greatest common divisor, prove it always terminates and returns the correct GCD of two natural numbers -/
theorem euclidean_gcd_correct (a b : Nat) :
  euclidean_gcd a b = Nat.gcd a b := by sorry