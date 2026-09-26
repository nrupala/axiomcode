import Mathlib
import Aesop

structure Array (α : Type) where

def bubbleSort (arr : Array Nat) : Array Nat :=

/--  -/
theorem bubbleSort_correctness : ∀ arr : Array Nat, bubbleSort arr = arr :=
by sorry