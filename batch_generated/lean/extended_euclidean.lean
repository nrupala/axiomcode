import Mathlib
import Aesop
import Mathlib.NumberTheory



/-- implement the extended Euclidean algorithm that finds GCD and Bézout coefficients, prove that a*x + b*y = gcd(a,b) -/
theorem extended_euclidean_correct (a b : Nat) :
  extended_euclidean a b = Nat.gcd a b := by sorry