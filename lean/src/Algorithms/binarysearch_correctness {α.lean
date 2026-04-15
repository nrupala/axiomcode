import Mathlib
import Aesop

structure SortedArray (α : Type) where

def binarySearch {α : Type} [LinearOrder α] (sa : SortedArray α) (target : α) : Option Nat :=

/--  -/
theorem binarySearch_correctness {α : Type} [LinearOrder α] (sa : SortedArray α) (target : α) :
    match binarySearch sa target with
    | none => ∀ i, sa.arr[i] ≠ target
    | some idx => sa.arr[idx] = target :=
  by sorry