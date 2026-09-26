import Mathlib
import Aesop

structure ListState where

def isSorted (l : List Nat) : Prop :=

/--  -/
theorem insertionSort_correctness :
  ∀ (xs : List Nat), ∃ ys, isSorted ys ∧ ys.length = xs.length := by sorry