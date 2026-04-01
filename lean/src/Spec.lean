/-!
# AxiomCode — Specification Definitions

Core types and predicates for specifying algorithm correctness.
-/

import Mathlib.Data.List.Sort
import Mathlib.Order.WellFounded

namespace AxiomCode

/-- A list is sorted in non-decreasing order. -/
def Sorted (l : List Nat) : Prop :=
  ∀ i j, i < j → j < l.length → l[i]! ≤ l[j]!

/-- Two lists are permutations of each other. -/
def Perm (l₁ l₂ : List Nat) : Prop :=
  List.Perm l₁ l₂

/-- Specification for a sorting algorithm: output is sorted and a permutation of input. -/
def SortSpec (f : List Nat → List Nat) : Prop :=
  ∀ l, Sorted (f l) ∧ Perm l (f l)

/-- Specification for binary search: returns index if element exists, none otherwise. -/
def BinarySearchSpec (f : List Nat → Nat → Option Nat) : Prop :=
  ∀ l x, Sorted l →
    (f l x = some i ↔ l[i]! = x ∧ i < l.length)

/-- Specification for merge operation: merges two sorted lists into one sorted list. -/
def MergeSpec (f : List Nat → List Nat → List Nat) : Prop :=
  ∀ l₁ l₂, Sorted l₁ → Sorted l₂ →
    Sorted (f l₁ l₂) ∧ Perm (l₁ ++ l₂) (f l₁ l₂)

end AxiomCode
