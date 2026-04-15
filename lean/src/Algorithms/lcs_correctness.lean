import Mathlib
import Aesop

structure LCSState where

def lcs (xs : List Char) (ys : List Char) : Nat :=

/-- The longest common subsequence algorithm is correct. -/
theorem lcs_correctness : ∀ xs ys, lcs xs ys = length (longestCommonSubseq xs ys) := by sorry