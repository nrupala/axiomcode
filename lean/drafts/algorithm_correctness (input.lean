import Mathlib
import Aesop

structure SubsetSumInput where

def isSubsetSum (input : SubsetSumInput) (subset : List ℕ) : Bool :=

/--  -/
theorem algorithm_correctness (input : SubsetSumInput) :
  ∃ subset : List ℕ, subset ⊆ input.numbers ∧ isSubsetSum input subset := by sorry