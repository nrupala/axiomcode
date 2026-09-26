import Mathlib
import Aesop

structure StackWithMax (α : Type) where

def empty {α : Type} : StackWithMax α :=

def push {α : Type} (s : StackWithMax α) (x : α) : StackWithMax α :=

def pop {α : Type} (s : StackWithMax α) : Option (StackWithMax α) :=

def max {α : Type} (s : StackWithMax α) : Option α :=

/--  -/
theorem stack_with_max_invariant :
  ∀ {α : Type} (s : StackWithMax α), s.invariant := by