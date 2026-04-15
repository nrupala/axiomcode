import Mathlib
import Aesop

structure Histogram where

def largestRectangleArea (hist : Histogram) : Nat :=

/--  -/
theorem largestRectangleArea_correctness : ∀ hist : Histogram, largestRectangleArea hist ≥ 0 :=
by sorry