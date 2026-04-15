import Mathlib
import Aesop

structure RotatedSortedArray where

def searchInRotatedArray (arr : RotatedSortedArray) (target : Int) : Option Nat :=

/--  -/
theorem searchInRotatedArray_correctness :
  ∀ arr : RotatedSortedArray, ∀ target : Int,
    match searchInRotatedArray arr target with
    | some idx => arr.arr[idx] = target
    | none => ¬∃ idx, arr.arr[idx] = target := by sorry