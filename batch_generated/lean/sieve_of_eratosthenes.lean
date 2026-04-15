import Mathlib
import Aesop
import Mathlib.NumberTheory



/-- implement the Sieve of Eratosthenes to find all primes up to n, prove every number marked as prime is actually prime and all composites are marked -/
theorem sieve_of_eratosthenes_correct (a b : Nat) :
  sieve_of_eratosthenes a b = Nat.gcd a b := by sorry