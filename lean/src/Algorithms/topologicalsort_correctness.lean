import Mathlib
import Aesop

structure Graph where

def isDAG (g : Graph) : Bool :=

def topologicalSort (g : Graph) : List g.vertices :=

/--  -/
theorem topologicalSort_correctness : ∀ g : Graph, isDAG g → topologicalSort g = some l ∧ l.length = #g.vertices ∧ (∀ v w ∈ l, (v, w) ∉ g.edges) :=
by sorry