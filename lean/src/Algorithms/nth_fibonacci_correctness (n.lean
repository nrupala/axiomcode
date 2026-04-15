import Mathlib
import Aesop

structure Fibonacci (n : Nat) where

def fib (n : Nat) : Nat :=

/--  -/
theorem nth_fibonacci_correctness (n : Nat) :
  ∃ f : Fibonacci n, f.value = fib n := by sorry