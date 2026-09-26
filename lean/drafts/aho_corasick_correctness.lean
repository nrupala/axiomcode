import Mathlib
import Aesop

structure TrieNode where

def transition (state : AutomatonState) (char : Char) : AutomatonState :=

def build_automaton (patterns : List String) : AutomatonState :=

/--  -/
theorem aho_corasick_correctness :
  ∀ patterns : List String, ∀ input : String,
    ∃ matches : List (String × Nat),
      (∀ (match_str, pos) ∈ matches, match_str ∈ patterns ∧ input.drop pos = match_str) :=
by sorry