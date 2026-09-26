import Mathlib
import Aesop

structure ManachersResult where

def manachersAlgorithm (s : String) : ManachersResult :=

/--  -/
theorem manachersAlgorithm_correctness :
  ∀ s : String, let result := manachersAlgorithm s in
    result.center ≤ s.length ∧ result.right ≤ s.length ∧
    (∀ i, i < result.center → result.lengths[i] = 2 * (result.center - i) + 1) :=
by sorry