import Mathlib
import Aesop
import Mathlib.NumberTheory



/-- implement modular exponentiation using square-and-multiply, prove it correctly computes (base^exp) mod m -/
theorem modular_exponentiation_correct (a b : Nat) :
  modular_exponentiation a b = Nat.gcd a b := by sorry