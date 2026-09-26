import Mathlib
import Aesop

structure RadixSortInput where

def radixSort (input : RadixSortInput) : List Nat :=

/--  -/
theorem radixSort_correctness : ∀ (input : RadixSortInput), radixSort input = List.sort (≤) input.arr := by sorry