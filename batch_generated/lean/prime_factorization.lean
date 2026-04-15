import Mathlib
import Aesop
import Mathlib.NumberTheory



/-- implement trial division prime factorization, prove the product of returned prime factors equals the original number -/
theorem prime_factorization_correct (a b : Nat) :
  prime_factorization a b = Nat.gcd a b := by sorry