import Mathlib
import Aesop

structure AVLTree (α : Type) where

def height (t : AVLTree α) : Nat :=

def balanceFactor (n : AVLNode α) : Int :=

/--  -/
theorem avl_tree_correctness : ∀ t : AVLTree α, (∀ n : AVLNode α, n ∈ t.root → |balanceFactor n| ≤ 1) ∧ (∀ n : AVLNode α, n ∈ t.root → height (AVLTree.mk (some n)) = max (height n.left) (height n.right) + 1) := by sorry