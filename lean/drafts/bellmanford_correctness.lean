import Mathlib
import Aesop

structure Graph where

def initialDistances (g : Graph) (source : g.vertices) : List (g.vertices × Int) :=

def relaxEdge (dists : List (Graph.vertices × Int)) (edge : Graph.edges) : List (Graph.vertices × Int) :=

def bellmanFord (g : Graph) (source : g.vertices) (n : Nat) : List (Graph.vertices × Int) :=

/--  -/
theorem bellmanFord_correctness :
  ∀ (g : Graph) (source : g.vertices) (n : Nat),
  n ≥ g.vertices.size →
  bellmanFord g source n = shortestPaths g source :=
by sorry