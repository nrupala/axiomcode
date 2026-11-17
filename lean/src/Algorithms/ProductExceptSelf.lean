import Spec
import Tactics

/-!
# AxiomCode — Verified Product of Array Except Self

Promoted from `lean/drafts/algorithm_correctness.lean` under the L2
promotion procedure (`lean/PROMOTION.md`). The draft's shells are
authored for real: the structure gains the two fields its theorem's
right-hand side names (the input `arr` and the output field
`product_except_self`), and the algorithm is the prefix/suffix
product construction: entry `i` of the output is
`(product of all entries before i) * (product of all entries after i)`.

Statement honesty: the draft's theorem,
`∀ arr, product_except_self arr = ⟨arr, (product_except_self arr).product_except_self⟩`,
is carried in its exact shape as
`ArrayProductExceptSelf.algorithm_correctness` (the bare name is
shared by several drafts and is namespaced under the structure, per
the LRU precedent). Once the fields exist, that statement is the
record-keeping claim — the result records its input and is determined
by its fields — and it is proved by `rfl`. The substantive
correctness is proved alongside it as `productExceptSelf_spec`:
entry `i` of the output is the product of all entries of the input
except entry `i` (`listProd (arr.eraseIdx i)`).
-/

namespace AxiomCode

/-- The product-except-self record: the input array and the computed
output array. -/
structure ArrayProductExceptSelf (α : Type) where
  arr : List α
  product_except_self : List α
deriving DecidableEq, Repr

/-- The product of a list of integers (`1` on the empty list). -/
def listProd (l : List Int) : Int := l.foldl (· * ·) 1

/-- `foldl (· * ·)` with an initial value is that value times the
product of the list. -/
theorem foldl_mul_init (l : List Int) (init : Int) :
    l.foldl (· * ·) init = init * listProd l := by
  induction l generalizing init with
  | nil => exact (Int.mul_one init).symm
  | cons x xs ih =>
    show (x :: xs).foldl (· * ·) init = init * (x :: xs).foldl (· * ·) 1
    rw [List.foldl_cons, List.foldl_cons, ih (init := init * x),
      ih (init := 1 * x), Int.one_mul, Int.mul_assoc]

/-- The product of a cons. -/
theorem listProd_cons (x : Int) (xs : List Int) :
    listProd (x :: xs) = x * listProd xs := by
  show (x :: xs).foldl (· * ·) 1 = x * listProd xs
  rw [List.foldl_cons, foldl_mul_init, Int.one_mul]

/-- The product of an append is the product of the products. -/
theorem listProd_append (a b : List Int) :
    listProd (a ++ b) = listProd a * listProd b := by
  have happ : (a ++ b).foldl (· * ·) 1 = b.foldl (· * ·) (listProd a) :=
    List.foldl_append
  exact happ.trans (foldl_mul_init b (listProd a))

/-- Reversing a list does not change its product. -/
theorem listProd_reverse (l : List Int) : listProd l.reverse = listProd l := by
  induction l with
  | nil => rfl
  | cons x xs ih =>
    rw [List.reverse_cons, listProd_append, ih]
    have hx : listProd [x] = x := by
      rw [listProd_cons]
      exact Int.mul_one x
    rw [hx, listProd_cons]
    exact Int.mul_comm _ _

/-- Prefix products: entry `i` is the product of all entries before
`i`. -/
def prefixProd : List Int → List Int
  | [] => []
  | x :: xs => 1 :: (prefixProd xs).map (x * ·)

theorem length_prefixProd (l : List Int) :
    (prefixProd l).length = l.length := by
  induction l with
  | nil => rfl
  | cons x xs ih =>
    show (1 :: (prefixProd xs).map (x * ·)).length = (x :: xs).length
    rw [List.length_cons, List.length_map, ih, List.length_cons]

theorem getElem?_prefixProd (l : List Int) (i : Nat) (h : i < l.length) :
    (prefixProd l)[i]? = some (listProd (l.take i)) := by
  induction l generalizing i with
  | nil => exact absurd h (Nat.not_lt_zero i)
  | cons x xs ih =>
    cases i with
    | zero =>
      show (1 :: (prefixProd xs).map (x * ·))[0]? =
        some (listProd ((x :: xs).take 0))
      rw [List.getElem?_cons_zero]
      rfl
    | succ i =>
      have hi : i < xs.length := by
        have hh := h
        simp only [List.length_cons] at hh
        omega
      show (1 :: (prefixProd xs).map (x * ·))[i + 1]? =
        some (listProd ((x :: xs).take (i + 1)))
      rw [List.getElem?_cons_succ, List.getElem?_map, ih i hi]
      show some (x * listProd (xs.take i)) =
        some (listProd ((x :: xs).take (i + 1)))
      have htake : (x :: xs).take (i + 1) = x :: xs.take i := rfl
      rw [htake, listProd_cons]

/-- Suffix products: entry `i` is the product of all entries after
`i`, computed as prefix products over the reversed list, reversed
back. -/
def suffixProd (arr : List Int) : List Int := (prefixProd arr.reverse).reverse

/-- Indexing into a mapped list, at an in-range index. -/
theorem getElem!_map_of_lt {α β : Type} [Inhabited α] [Inhabited β]
    {f : α → β} {l : List α} {i : Nat} (h : i < l.length) :
    (l.map f)[i]! = f (l[i]!) := by
  rw [List.getElem!_eq_getElem?_getD, List.getElem?_map,
    List.getElem!_eq_getElem?_getD]
  cases hl : l[i]? with
  | none =>
    have hle : l.length ≤ i := List.getElem?_eq_none_iff.mp hl
    omega
  | some a => rfl

/-- Indexing into a reversed list, at an in-range index. -/
theorem getElem!_reverse_of_lt {α : Type} [Inhabited α] {l : List α}
    {i : Nat} (h : i < l.length) :
    l.reverse[i]! = l[l.length - 1 - i]! := by
  rw [List.getElem!_eq_getElem?_getD, List.getElem!_eq_getElem?_getD,
    List.getElem?_reverse h]

theorem getElem!_prefixProd (l : List Int) (i : Nat) (h : i < l.length) :
    (prefixProd l)[i]! = listProd (l.take i) := by
  rw [List.getElem!_eq_getElem?_getD, getElem?_prefixProd l i h]
  rfl

theorem getElem!_suffixProd (l : List Int) (i : Nat) (h : i < l.length) :
    (suffixProd l)[i]! = listProd (l.drop (i + 1)) := by
  have hlen : (prefixProd l.reverse).length = l.length := by
    rw [length_prefixProd, List.length_reverse]
  have step1 : (suffixProd l)[i]! =
      (prefixProd l.reverse)[l.length - 1 - i]! := by
    show ((prefixProd l.reverse).reverse)[i]! = _
    have hrev := getElem!_reverse_of_lt (l := prefixProd l.reverse)
      (by rw [hlen]; exact h)
    rw [hlen] at hrev
    exact hrev
  rw [step1, getElem!_prefixProd _ _ (by rw [List.length_reverse]; omega),
    List.take_reverse, listProd_reverse]
  have hidx : l.length - (l.length - 1 - i) = i + 1 := by omega
  rw [hidx]

/-- Product except self: entry `i` is the product of the prefix
before `i` times the product of the suffix after `i`. -/
def productExceptSelf (arr : List Int) : List Int :=
  (List.range arr.length).map
    (fun i => (prefixProd arr)[i]! * (suffixProd arr)[i]!)

/-- The draft's function: the record of the input and its
product-except-self output. -/
def product_except_self (arr : List Int) : ArrayProductExceptSelf Int :=
  ⟨arr, productExceptSelf arr⟩

/-- The draft's theorem, in its exact shape: the result records its
input and is determined by its fields. -/
theorem ArrayProductExceptSelf.algorithm_correctness :
    ∀ arr : List Int, AxiomCode.product_except_self arr =
      ArrayProductExceptSelf.mk arr
        (AxiomCode.product_except_self arr).product_except_self :=
  fun _arr => rfl

/-- The substantive correctness: entry `i` of the output is the
product of all entries of the input except entry `i`. -/
theorem productExceptSelf_spec (arr : List Int) (i : Nat)
    (h : i < arr.length) :
    (product_except_self arr).product_except_self[i]! =
      listProd (arr.eraseIdx i) := by
  show (productExceptSelf arr)[i]! = listProd (arr.eraseIdx i)
  show ((List.range arr.length).map
    (fun k => (prefixProd arr)[k]! * (suffixProd arr)[k]!))[i]! =
      listProd (arr.eraseIdx i)
  have hrange : (List.range arr.length)[i]! = i := by
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_range h]
    rfl
  rw [getElem!_map_of_lt (by rwa [List.length_range]), hrange,
    getElem!_prefixProd _ _ h, getElem!_suffixProd _ _ h,
    List.eraseIdx_eq_take_drop_succ, listProd_append]

end AxiomCode
