import Mathlib
import Aesop

structure RainWaterProblem where

def maxLeft (heights : List Nat) (i : Nat) : Nat :=

def maxRight (heights : List Nat) (i : Nat) : Nat :=

def trappedWaterAt (heights : List Nat) (i : Nat) : Nat :=

def totalTrappedWater (heights : List Nat) : Nat :=

/-- The correctness theorem for the trapping rain water algorithm. -/
theorem algorithm_correctness (problem : RainWaterProblem) :
  totalTrappedWater problem.heights = ... := by sorry