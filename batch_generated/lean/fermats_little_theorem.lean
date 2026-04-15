import Mathlib
import Aesop
import Mathlib.NumberTheory



/-- implement a primality test based on Fermat's little theorem, prove that if a^(p-1) ≡ 1 (mod p) then p is probably prime -/
theorem fermats_little_theorem_correct (a b : Nat) :
  fermats_little_theorem a b = Nat.gcd a b := by sorry