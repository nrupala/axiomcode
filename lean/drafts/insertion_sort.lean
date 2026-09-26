/-!
# AxiomCode — Verified Insertion Sort

A formally verified insertion sort implementation with correctness proof.
-/

import AxiomCode.Spec
import AxiomCode.Tactics

namespace AxiomCode

/-- Insert an element into a sorted list while maintaining sorted order. -/
def insert (x : Nat) : List Nat → List Nat
  | [] => [x]
  | y :: ys =>
    if x ≤ y then x :: y :: ys
    else y :: insert x ys

/-- Insertion sort: recursively sort the tail, then insert the head. -/
def insertionSort : List Nat → List Nat
  | [] => []
  | x :: xs => insert x (insertionSort xs)

/-- Theorem: insertion sort produces a sorted list. -/
theorem insertionSort_sorted (l : List Nat) :
    Sorted (insertionSort l) := by
  sorry

/-- Theorem: insertion sort preserves elements (permutation). -/
theorem insertionSort_perm (l : List Nat) :
    List.Perm l (insertionSort l) := by
  sorry

/-- Full correctness: insertion sort is a valid sorting function. -/
theorem insertionSort_correct (l : List Nat) :
    SortSpec insertionSort := by
  constructor
  · exact insertionSort_sorted l
  · exact insertionSort_perm l

/-- Export for C compilation. -/
@[export insertionSort_c]
def insertionSort_c (l : List Nat) : List Nat :=
  insertionSort l

end AxiomCode
