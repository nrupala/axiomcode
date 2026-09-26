import Mathlib
import Aesop

structure Edge (V : Type) where

def isSpanningTree {V : Type} (g : Graph V) (vertices : Set V) : Prop :=

/--  -/
theorem prim_algorithm_correctness {V : Type} (graph : Graph V) (start_vertex : V) :
  ∃ mst : List (Edge V), isSpanningTree (Graph.mk mst) ({start_vertex}) := by sorry