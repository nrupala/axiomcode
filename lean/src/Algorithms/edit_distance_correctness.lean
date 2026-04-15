import Mathlib
import Aesop

structure EditDistance (s t : String) where

def edit_distance (s t : String) : Nat :=

/--  -/
theorem edit_distance_correctness : ∀ s t : String, EditDistance s t :=
  by sorry