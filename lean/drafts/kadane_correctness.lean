import Mathlib
import Aesop

structure KadaneInput where

def kadane (input : KadaneInput) : Int :=

/--  -/
theorem kadane_correctness : ∀ (input : KadaneInput), kadane input = List.max (List.scanl (fun acc x => max x (acc + x)) 0 input.arr).get? := by sorry