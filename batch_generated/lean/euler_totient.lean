import Mathlib
import Aesop
import Mathlib.NumberTheory



/-- implement Euler's totient function that counts integers coprime to n, prove the result equals the count of numbers less than n that are coprime to n -/
theorem euler_totient_correct (a b : Nat) :
  euler_totient a b = Nat.gcd a b := by sorry