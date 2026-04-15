import Mathlib
import Aesop

structure QuickselectInput where

def quickselect (input : QuickselectInput) : Nat :=

/--  -/
theorem quickselect_correctness (input : QuickselectInput) :
  let result := quickselect input in
  result ∈ input.arr ∧
  (∀ x ∈ input.arr, x < result → x ∈ left) ∧
  (∀ x ∈ input.arr, result < x → x ∈ right) :=
by sorry