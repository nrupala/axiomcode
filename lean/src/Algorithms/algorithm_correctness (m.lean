import Mathlib
import Aesop

structure SpiralMatrix where

def isSpiralMatrix (m : SpiralMatrix) : Bool :=

/-- A spiral matrix of size `rows x cols` is correctly generated if all elements are visited in a spiral order. -/
theorem algorithm_correctness (m : SpiralMatrix) : isSpiralMatrix m ↔ List.flatten m.matrix = List.range (m.rows * m.cols) := by sorry