import Mathlib
import Aesop

structure Reservoir where

def reservoirSampling (stream : List α) (k : Nat) : Reservoir :=

/--  -/
theorem reservoirSampling_correctness : ∀ (stream : List α) (k : Nat), Reservoir.size (reservoirSampling stream k) ≤ k :=
by sorry