import Mathlib
import Aesop

structure Graph (V : Type) where

def isConnected (G : Graph V) : Prop :=

/--  -/
theorem algorithm_correctness {V : Type} (G : Graph V) (bridges : Set (V × V)) :
  ∀ e ∈ bridges, ¬isConnected (Graph.mk G.vertices (G.edges \ {e})) :=
by sorry