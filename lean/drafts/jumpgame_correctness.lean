import Mathlib
import Aesop

structure JumpGameInput where

def canJump (input : JumpGameInput) : Bool :=

/--  -/
theorem jumpGame_correctness : ∀ (input : JumpGameInput), canJump input = true ↔ ∃ path, List.sum path ≤ input.target :=
by sorry