import Mathlib
import Aesop

structure Graph where

def isArticulationPoint (G : Graph) (v : G.vertices) : Prop :=

/--  -/
theorem articulationPointsAlgorithmCorrectness (G : Graph) (articulationPoints : Set G.vertices) : 
  ∀ v ∈ articulationPoints, isArticulationPoint G v := by sorry