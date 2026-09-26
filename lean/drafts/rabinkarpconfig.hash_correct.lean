import Mathlib
import Aesop

structure RabinKarpConfig where

def RabinKarpConfig.hash (s : String) (prime : Nat) (d : Nat) : Nat :=

def RabinKarpConfig.rollHash (oldHash : Nat) (oldChar : Char) (newChar : Char) (patternLen : Nat) (prime : Nat) (d : Nat) : Nat :=

/--  -/
theorem RabinKarpConfig.hash_correct : ∀ s : String, RabinKarpConfig.hash s prime d = RabinKarpConfig.hash s prime d :=
by sorry

theorem RabinKarpConfig.rollHash_correct : ∀ oldHash oldChar newChar patternLen,
  RabinKarpConfig.rollHash oldHash oldChar newChar patternLen prime d = RabinKarpConfig.rollHash oldHash oldChar newChar patternLen prime d :=
by sorry

structure RabinKarpResult where
  indices : List Nat

theorem rabin_karp_correctness (config : RabinKarpConfig) (result : RabinKarpResult) :
  ∀ idx ∈ result.indices, config.text.toSubstring idx config.pattern.length = config.pattern :=
by sorry