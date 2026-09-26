import Mathlib
import Aesop

structure LRU_Cache (Key : Type) (Value : Type) where

def LRU_Cache.empty {Key Value} (capacity : Nat) : LRU_Cache Key Value :=

def LRU_Cache.insert {Key Value} (cache : LRU_Cache Key Value) (k : Key) (v : Value) : LRU_Cache Key Value :=

/--  -/
theorem LRU_Cache.invariant_preserved_insert {Key Value} (cache : LRU_Cache Key Value) (k : Key) (v : Value) :
  (∀ k' v', (k', v') ∈ cache.cache → k ≠ k' ∨ v = v') :=
sorry

theorem algorithm_correctness {Key Value} (capacity : Nat) (keys : List Key) (values : List Value) :
  ∀ i, i < length keys →
    let cache := List.foldl (fun acc j => LRU_Cache.insert acc keys[j] values[j]) (LRU_Cache.empty capacity) (range i)
    in (∀ k v, (k, v) ∈ cache.cache → length cache.cache ≤ capacity ∧ (∀ k' v', (k', v') ∈ cache.cache → k ≠ k' ∨ v = v')) :=
sorry