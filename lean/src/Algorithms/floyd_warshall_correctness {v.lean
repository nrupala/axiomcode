import Mathlib
import Aesop

structure Graph (V : Type) where

def shortestPaths (G : Graph V) : List (V × V × Nat) :=

/-- Floyd-Warshall algorithm correctness theorem -/
theorem floyd_warshall_correctness {V : Type} (G : Graph V) :
  ∀ u v, shortestPaths G[u, v] = min (List.map (fun (w, _, d) => d + shortestPaths G[w, v]) G.edges ++ [Nat.maxRec 0]) :=
by sorry