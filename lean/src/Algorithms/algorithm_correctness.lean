import Mathlib
import Aesop

structure ArrayProductExceptSelf (α : Type) where

def product_except_self (arr : List Int) : ArrayProductExceptSelf Int :=

/--  -/
theorem algorithm_correctness : ∀ arr : List Int, product_except_self arr = ArrayProductExceptSelf.mk arr (product_except_self arr).product_except_self := by sorry