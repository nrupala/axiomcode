import Mathlib
import Aesop

structure Interval (α : Type) where

def insertInterval (intervals : List (Interval α)) (newInterval : Interval α) : List (Interval α) :=

/--  -/
theorem insertInterval_correctness :
  ∀ (intervals : List (Interval α)) (newInterval : Interval α),
    let inserted := insertInterval intervals newInterval
    in (∀ i ∈ inserted, i.invariant) ∧
       (∀ i ∈ intervals, ∃ j ∈ inserted, i.start = j.start ∧ i.end = j.end) ∧
       (∀ i ∈ inserted, ∃ j ∈ intervals ++ [newInterval], i.start = j.start ∧ i.end = j.end) :=
by sorry