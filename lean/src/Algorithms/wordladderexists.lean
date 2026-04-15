import Mathlib
import Aesop

structure WordLadderConfig where

def isTransformation (config : WordLadderConfig) (word1 word2 : String) : Bool :=

def isValidStep (config : WordLadderConfig) (ladder : List String) : Bool :=

def isWordLadder (config : WordLadderConfig) (ladder : List String) : Bool :=

/--  -/
theorem wordLadderExists : ∀ config : WordLadderConfig, ∃ ladder : List String, isWordLadder config ladder := by sorry