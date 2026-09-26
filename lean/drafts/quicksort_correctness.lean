import Mathlib
import Aesop

structure Array (α : Type) where

def get (self : Array α) (i : Nat) : Option α :=

def set (self : Array α) (i : Nat) (v : α) : Option (Array α) :=

def quicksort (arr : List Int) : List Int :=

/--  -/
theorem quicksort_correctness : ∀ arr : List Int, sorted (quicksort arr) ∧ (∀ x ∈ arr, x ∈ quicksort arr) :=
  by sorry