import Mathlib
import Aesop

structure CountingSortInput where

def countingSort (input : CountingSortInput) : List Nat :=

/--  -/
theorem countingSort_correctness : ∀ input, countingSort input = input.arr.sort :=
by sorry