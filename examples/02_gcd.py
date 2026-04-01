"""
Example 2: GCD — Euclidean algorithm with termination proof.

Run: axiomcode "implement the Euclidean algorithm for greatest common divisor, prove it always terminates and returns the correct GCD"
"""

# What AxiomCode generates internally:
#
# import Mathlib
# import Aesop
#
# /-- Euclidean algorithm for GCD. -/
# def gcd (a b : Nat) : Nat :=
#   if b = 0 then a else gcd b (a % b)
#
# /-- GCD always terminates and returns the correct result. -/
# theorem gcd_correct (a b : Nat) :
#     gcd a b ∣ a ∧ gcd a b ∣ b ∧
#     ∀ d, d ∣ a → d ∣ b → d ∣ gcd a b := by sorry
#
# /-- GCD always terminates (well-founded recursion). -/
# theorem gcd_terminates (a b : Nat) :
#     ∃ n, gcd a b terminates in n steps := by sorry
