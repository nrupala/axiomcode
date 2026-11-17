import Spec
import Tactics

/-!
# AxiomCode — Verified Range-Sum Query

A formally verified range-sum query structure: queries are answered in
O(1) from precomputed prefix sums.

Promoted from `lean/drafts/algorithm_correctness (q.lean` under the L2
promotion procedure (`lean/PROMOTION.md`). The draft's shells are
authored for real: the structure gains its `data` field (the draft's
explicit `RangeSumQuery.mk` definition is the structure's constructor
once the field exists), and `query` is the prefix-sum algorithm.

One defect in the draft is recorded, not silently repaired: the draft
states the theorem with the slice notation `q.data[left:right+1]`, which
cannot elaborate over `List` in this toolchain — the `[a:b]` notation
resolves to `Array.toSubarray` and demands an `Array`. The theorem is
therefore carried in the slice's List form,
`List.sum ((q.data.drop left).take (right + 1 - left))` — the sum of the
elements from index `left` to index `right` inclusive, with the
clamping that form and the prefix-sum definition share. The theorem is
named `RangeSumQuery.algorithm_correctness`: the draft's bare name
`algorithm_correctness` is also the LRU draft's theorem name, and the
two cannot both live at `AxiomCode.algorithm_correctness`.
-/

namespace AxiomCode

/-- A range-sum query structure over a list of naturals: the data, queried
by index range. Queries are answered from precomputed prefix sums. -/
structure RangeSumQuery where
  data : List Nat
deriving DecidableEq, Repr

/-- Prefix sums with a running accumulator: `prefixFrom acc l` is the list
of partial sums of `l` starting from `acc`, including `acc` itself as the
head — so it has `l.length + 1` entries and entry `i` is
`acc + (l.take i).sum`. -/
def prefixFrom (acc : Nat) : List Nat → List Nat
  | [] => [acc]
  | x :: xs => acc :: prefixFrom (acc + x) xs

/-- The prefix sums of a list, starting from `0`. -/
def prefixes (l : List Nat) : List Nat :=
  prefixFrom 0 l

theorem prefixFrom_length (acc : Nat) (l : List Nat) :
    (prefixFrom acc l).length = l.length + 1 := by
  induction l generalizing acc with
  | nil => rfl
  | cons x xs ih =>
    show (prefixFrom (acc + x) xs).length + 1 = xs.length + 1 + 1
    rw [ih]

/-- The characterising property of `prefixFrom`: entry `i` (for `i` in
range) is the accumulator plus the sum of the first `i` elements. -/
theorem prefixFrom_getI (acc : Nat) (l : List Nat) (i : Nat) (hi : i ≤ l.length) :
    (prefixFrom acc l)[i]! = acc + (l.take i).sum := by
  induction l generalizing acc i with
  | nil =>
    have hi0 : i = 0 := Nat.eq_zero_of_le_zero (by simpa using hi)
    subst hi0
    rfl
  | cons x xs ih =>
    cases i with
    | zero => rfl
    | succ j =>
      have hj : j ≤ xs.length := by
        have hl : (x :: xs).length = xs.length + 1 := rfl
        omega
      show (prefixFrom (acc + x) xs)[j]! = acc + ((x :: xs).take (j + 1)).sum
      rw [ih (acc + x) j hj]
      show acc + x + (xs.take j).sum = acc + (x + (xs.take j).sum)
      omega

/-- Entry `i` of the prefix sums is the sum of the first `i` elements. -/
theorem prefixes_getI (l : List Nat) (i : Nat) (hi : i ≤ l.length) :
    (prefixes l)[i]! = (l.take i).sum := by
  have h := prefixFrom_getI 0 l i hi
  rw [Nat.zero_add] at h
  exact h

/-- The sum of a segment, from the sums of two prefixes: for `a ≤ b`, the
sum of the first `b` elements is the sum of the first `a` plus the sum of
the next `b - a` elements after position `a`. -/
theorem sum_take_segment (l : List Nat) (a b : Nat) (h : a ≤ b) :
    (l.take b).sum = (l.take a).sum + ((l.drop a).take (b - a)).sum := by
  induction l generalizing a b with
  | nil => simp
  | cons x xs ih =>
    cases a with
    | zero =>
      simp
    | succ a =>
      cases b with
      | zero => exact absurd h (by omega)
      | succ b =>
        have hab : a ≤ b := by omega
        have hsub : b + 1 - (a + 1) = b - a := by omega
        have h1 : ((x :: xs).take (b + 1)).sum = x + (xs.take b).sum := rfl
        have h2 : ((x :: xs).take (a + 1)).sum = x + (xs.take a).sum := rfl
        have h3 : (x :: xs).drop (a + 1) = xs.drop a := rfl
        rw [h1, h2, h3, hsub, ih a b hab]
        omega

/-- Range-sum query: the sum of the elements at indices `left … right`
(inclusive), answered in O(1) from the prefix sums as
`prefix[right + 1] − prefix[left]`. The indices are clamped to the data
length, matching the clamping of the slice on the right-hand side of the
correctness theorem. -/
def RangeSumQuery.query (q : RangeSumQuery) (left right : Nat) : Nat :=
  (prefixes q.data)[min (right + 1) q.data.length]!
    - (prefixes q.data)[min left q.data.length]!

/-- The draft's statement, in its List form (see the module doc for the
slice-notation defect): the query returns the sum of the elements from
index `left` to index `right` inclusive. -/
theorem RangeSumQuery.algorithm_correctness (q : RangeSumQuery) (left right : Nat) :
    RangeSumQuery.query q left right
      = List.sum ((q.data.drop left).take (right + 1 - left)) := by
  have hmin1 : min (right + 1) q.data.length ≤ q.data.length :=
    Nat.min_le_right _ _
  have hmin2 : min left q.data.length ≤ q.data.length :=
    Nat.min_le_right _ _
  have hq : RangeSumQuery.query q left right =
      (prefixes q.data)[min (right + 1) q.data.length]!
        - (prefixes q.data)[min left q.data.length]! := rfl
  rw [hq, prefixes_getI _ _ hmin1, prefixes_getI _ _ hmin2]
  by_cases hcase : left ≤ right + 1
  · -- In-order range: segment identity between the two prefix sums.
    have hseg := sum_take_segment q.data (min left q.data.length)
      (min (right + 1) q.data.length) (by omega)
    have hdrop : (q.data.drop (min left q.data.length)).take
        (min (right + 1) q.data.length - min left q.data.length)
        = (q.data.drop left).take (right + 1 - left) := by
      by_cases hl : left ≤ q.data.length
      · have hminl : min left q.data.length = left := Nat.min_eq_left hl
        rw [hminl]
        by_cases hr : right + 1 ≤ q.data.length
        · have hminr : min (right + 1) q.data.length = right + 1 :=
            Nat.min_eq_left hr
          rw [hminr]
        · have hminr : min (right + 1) q.data.length = q.data.length :=
            Nat.min_eq_right (by omega)
          rw [hminr]
          have hlen : (q.data.drop left).length = q.data.length - left := by
            rw [List.length_drop]
          have e1 : (q.data.drop left).take (q.data.length - left)
              = q.data.drop left := by
            apply List.take_of_length_le
            omega
          have e2 : (q.data.drop left).take (right + 1 - left)
              = q.data.drop left := by
            apply List.take_of_length_le
            omega
          rw [e1, e2]
      · have hminl : min left q.data.length = q.data.length :=
          Nat.min_eq_right (by omega)
        have hminr : min (right + 1) q.data.length = q.data.length :=
          Nat.min_eq_right (by omega)
        have e1 : q.data.drop q.data.length = [] :=
          List.drop_of_length_le (Nat.le_refl _)
        have e2 : q.data.drop left = [] :=
          List.drop_of_length_le (by omega)
        rw [hminl, hminr, e1, e2, List.take_nil, List.take_nil]
    rw [hdrop] at hseg
    omega
  · -- Out-of-order range (`right + 1 < left`): both sides are `0` — the
    -- prefix difference vanishes by monotonicity, the slice is empty.
    have hseg := sum_take_segment q.data (min (right + 1) q.data.length)
      (min left q.data.length) (by omega)
    have hR : ((q.data.drop left).take (right + 1 - left)).sum = 0 := by
      have hz : right + 1 - left = 0 := by omega
      rw [hz, List.take_zero, List.sum_nil]
    rw [hR]
    omega

end AxiomCode
