import Mathlib
import Aesop

structure Interval where

def mergeIntervals (intervals : List Interval) : List Interval :=

/--  -/
theorem mergeIntervals_correctness : ∀ intervals : List Interval,
  let merged := mergeIntervals intervals in
    (∀ i ∈ merged, ∃ j ∈ intervals, i ≤ j) ∧
    (∀ i j ∈ merged, i ≠ j → disjoint i j) :=
by sorry