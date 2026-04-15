import Mathlib
import Aesop

structure KMPTable where

def kmp_table (pattern : String) : KMPTable :=

def kmp_search (text : String) (pattern : String) : Option Nat :=

/--  -/
theorem kmp_search_correctness : ∀ text pattern,
  kmp_search text pattern = some pos ↔ ∃ i, text[i] = pattern[0] ∧ ∀ j < m, text[i + j] = pattern[j]
:= by sorry