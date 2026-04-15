import Mathlib
import Aesop
import Mathlib.NumberTheory



/-- implement the Miller-Rabin primality test with k witnesses, prove it correctly identifies composites and has bounded error probability -/
theorem miller_rabin_primality_correct (a b : Nat) :
  miller_rabin_primality a b = Nat.gcd a b := by sorry