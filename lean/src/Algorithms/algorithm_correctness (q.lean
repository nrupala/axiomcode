import Mathlib
import Aesop

structure RangeSumQuery where

def RangeSumQuery.mk (data : List Nat) : RangeSumQuery :=

def RangeSumQuery.query (q : RangeSumQuery) (left right : Nat) : Nat :=

/-- The range sum query algorithm is correct. -/
theorem algorithm_correctness (q : RangeSumQuery) (left right : Nat) :
    RangeSumQuery.query q left right = List.sum q.data[left:right+1] := by sorry