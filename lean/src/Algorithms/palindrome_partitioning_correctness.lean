import Mathlib
import Aesop

structure PalindromePartition where

/--  -/
theorem palindrome_partitioning_correctness :
  ∀ (input : List Char), ∃ (partition : PalindromePartition), partition.input = input := by sorry