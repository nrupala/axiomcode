import Mathlib
import Aesop

structure Point where

def orientation (o p q : Point) : Int :=

def onSegment (o p q : Point) : Bool :=

def grahamScan (points : List Point) : List Point :=

/--  -/
theorem grahamScan_correctness : ∀ (points : List Point), convexHull points = grahamScan points := by sorry