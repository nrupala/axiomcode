import Mathlib
import Aesop

structure Window where

def isValidWindow (s : String) (t : String) (window : Window) : Bool :=

def minWindowSubstring (s : String) (t : String) : Option Window :=

/--  -/
theorem minWindowSubstring_correctness : ∀ s t : String,
  minWindowSubstring s t = some w → isValidWindow s t w ∧ (∀ w', isValidWindow s t w' → w.length ≤ w'.length) :=
by sorry