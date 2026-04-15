import Mathlib
import Aesop

structure Trie (α : Type) where

def insert (trie : Trie α) (path : Path trie.root) (value : α) : Trie α :=

def lookup (trie : Trie α) (path : Path trie.root) : Option α :=

/--  -/
theorem insert_lookup_correctness (trie : Trie α) (path : Path trie.root) (value : α) :
  lookup (insert trie path value) path = some value :=
by sorry