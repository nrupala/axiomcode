import Mathlib
import Aesop

structure ZArray (n : Nat) where

def zAlgorithm (s : String) : ZArray s.length :=

/--  -/
theorem zAlgorithm_correctness : ∀ s : String, let z := zAlgorithm s; ZArray.invariant z :=
by sorry