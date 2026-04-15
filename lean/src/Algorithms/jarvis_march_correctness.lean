import Mathlib
import Aesop

structure Point where

def orientation (o p q : Point) : Int :=

def next_to_hull (points : List Point) (hull : List Point) (p : Point) : Bool :=

def jarvis_march (points : List Point) : List Point :=

/--  -/
theorem jarvis_march_correctness : ∀ points : List Point, convex_hull points = jarvis_march points := by sorry