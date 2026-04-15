import Mathlib
import Aesop

structure MaximalSquare where

def is_square (matrix : List (List Bool)) (size : Nat) (top_left : (Nat × Nat)) : Bool :=

def maximal_square_size (matrix : List (List Bool)) : Nat :=

/--  -/
theorem maximal_square_correctness : ∀ matrix : List (List Bool), maximal_square_size matrix = MaximalSquare.size :=
by sorry