import Mathlib
import Aesop

structure Edge (V : Type) where

structure Graph (V : Type) where

def isSpanningTree {V : Type} [Fintype V] (g : Graph V) (mst : Graph V) :

def kruskal {V : Type} [Fintype V] (g : Graph V) :

/--  -/
theorem kruskal_correctness {V : Type} [Fintype V] (g : Graph V) :
    isSpanningTree g (kruskal g) :=
by sorry