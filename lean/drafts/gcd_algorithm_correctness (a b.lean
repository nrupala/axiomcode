import Mathlib
import Aesop

structure EuclideanAlgorithmState where

def gcd_step (state : EuclideanAlgorithmState) : EuclideanAlgorithmState :=

def gcd_algorithm (a : Nat) (b : Nat) : Nat :=

/--  -/
theorem gcd_algorithm_correctness (a b : Nat) :
  gcd_algorithm a b = Nat.gcd a b := by sorry