import Mathlib
import Aesop
import Mathlib.NumberTheory



/-- implement least common multiple computation using the relationship lcm(a,b) = |a*b|/gcd(a,b), prove the result is the smallest positive integer divisible by both -/
theorem lcm_computation_correct (a b : Nat) :
  lcm_computation a b = Nat.gcd a b := by sorry