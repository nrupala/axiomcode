import Mathlib
import Aesop

structure SuffixArray where

/--  -/
theorem suffix_array_correctness (sa : SuffixArray) : sa.invariant := by sorry