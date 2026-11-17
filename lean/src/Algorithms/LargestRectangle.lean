import Spec
import Tactics

/-!
# AxiomCode — Verified Largest Rectangle in a Histogram

Promoted from `lean/drafts/largestrectanglearea_correctness.lean`
under the L2 promotion procedure (`lean/PROMOTION.md`). The draft's
shells are authored for real: `Histogram` gains its `heights` field,
and `largestRectangleArea` is the brute-force maximum over all
rectangles spanning a contiguous block of bars (the height of a block
is its shortest bar).

Statement honesty: the draft's theorem,
`∀ hist, largestRectangleArea hist ≥ 0`, is **vacuous as stated** —
every `Nat`-valued function whatsoever satisfies it — so it is proved
as stated (`Nat.zero_le`) and carries no information. The substantive
correctness statement is proved alongside it as
`largestRectangleArea_spec`: every genuine rectangle's area is at
most the result (upper bound), and the result is either `0` or is
attained by an actual rectangle (attainment). The draft's claim is
not silently replaced; the vacuity is recorded here and in the item
report, and the real content is named `_spec`.
-/

namespace AxiomCode

/-- A histogram: the heights of its bars. -/
structure Histogram where
  heights : List Nat
deriving DecidableEq, Repr

/-- The minimum of a list of heights (`0` on the empty list, which
arises only for empty spans, whose area is `0` anyway). -/
def minList : List Nat → Nat
  | [] => 0
  | x :: xs => xs.foldl Nat.min x

/-- The area of the rectangle spanning bars `i..j` inclusive: the
shortest bar in the span times the span's width. For `j < i` the
width `j + 1 - i` is `0` and so is the area. -/
def rectArea (h : List Nat) (i j : Nat) : Nat :=
  minList ((h.drop i).take (j + 1 - i)) * (j + 1 - i)

/-- The areas of all rectangles whose endpoints lie in range. -/
def allRectAreas (h : List Nat) : List Nat :=
  (List.range h.length).flatMap (fun i => (List.range h.length).map (rectArea h i))

/-- The largest rectangle area: the maximum over all rectangles. -/
def largestRectangleArea (hist : Histogram) : Nat :=
  (allRectAreas hist.heights).foldl max 0

/-- The initial value is at most the `foldl Nat.max` it seeds. -/
theorem le_foldl_max_init (l : List Nat) (init : Nat) :
    init ≤ l.foldl max init := by
  induction l generalizing init with
  | nil => exact Nat.le_refl _
  | cons a l ih =>
    exact Nat.le_trans (Nat.le_max_left _ _) (ih (init := max init a))

/-- Every element of a list is at most the list's `foldl Nat.max`,
from any initial value. -/
theorem le_foldl_max_of_mem_init {x : Nat} {l : List Nat} (hx : x ∈ l)
    (init : Nat) : x ≤ l.foldl max init := by
  induction l generalizing init with
  | nil => simp at hx
  | cons a l ih =>
    cases List.mem_cons.mp hx with
    | inl h =>
      subst h
      exact Nat.le_trans (Nat.le_max_right _ _) (le_foldl_max_init _ _)
    | inr h => exact ih h (max init a)

/-- Every element of a list is at most the list's `foldl Nat.max`. -/
theorem le_foldl_max_of_mem {x : Nat} {l : List Nat} (hx : x ∈ l) :
    x ≤ l.foldl max 0 :=
  le_foldl_max_of_mem_init hx 0

/-- The `foldl Nat.max` of a list is its initial value or one of the
list's elements. -/
theorem foldl_max_init_eq_or_mem (l : List Nat) (init : Nat) :
    l.foldl max init = init ∨ l.foldl max init ∈ l := by
  induction l generalizing init with
  | nil => exact Or.inl rfl
  | cons a l ih =>
    rw [List.foldl_cons]
    cases ih (init := max init a) with
    | inl h =>
      rw [h]
      cases Nat.le_total init a with
      | inl hle =>
        rw [Nat.max_eq_right hle]
        exact Or.inr (List.mem_cons_self)
      | inr hle =>
        rw [Nat.max_eq_left hle]
        exact Or.inl rfl
    | inr h => exact Or.inr (List.mem_cons_of_mem a h)

/-- The `foldl Nat.max` of a list is `0` or one of its elements. -/
theorem foldl_max_eq_zero_or_mem (l : List Nat) :
    l.foldl max 0 = 0 ∨ l.foldl max 0 ∈ l :=
  foldl_max_init_eq_or_mem l 0

/-- A rectangle area with both endpoints in range occurs in
`allRectAreas`. -/
theorem rectArea_mem_allRectAreas {h : List Nat} {i j : Nat}
    (hi : i < h.length) (hj : j < h.length) :
    rectArea h i j ∈ allRectAreas h := by
  apply List.mem_flatMap.mpr
  exact ⟨i, List.mem_range.mpr hi,
    List.mem_map.mpr ⟨j, List.mem_range.mpr hj, rfl⟩⟩

/-- The draft's theorem, as stated. It is vacuous for a `Nat`-valued
function; the content of this entry is `largestRectangleArea_spec`. -/
theorem largestRectangleArea_correctness :
    ∀ hist : Histogram, largestRectangleArea hist ≥ 0 :=
  fun _hist => Nat.zero_le _

/-- The substantive correctness of `largestRectangleArea`: an upper
bound on every genuine rectangle's area, and attainment — the value
is `0` or the area of an actual rectangle. -/
theorem largestRectangleArea_spec (hist : Histogram) :
    (∀ i j, i ≤ j → j < hist.heights.length →
      rectArea hist.heights i j ≤ largestRectangleArea hist) ∧
    (largestRectangleArea hist = 0 ∨
      ∃ i j, i ≤ j ∧ j < hist.heights.length ∧
        rectArea hist.heights i j = largestRectangleArea hist) := by
  constructor
  · intro i j hij hj
    exact le_foldl_max_of_mem
      (rectArea_mem_allRectAreas (Nat.lt_of_le_of_lt hij hj) hj)
  · by_cases hzero : largestRectangleArea hist = 0
    · exact Or.inl hzero
    · refine Or.inr ?_
      cases foldl_max_eq_zero_or_mem (allRectAreas hist.heights) with
      | inl h => exact absurd h hzero
      | inr h =>
        obtain ⟨i, hi, hmem⟩ := List.mem_flatMap.mp h
        obtain ⟨j, hj, harea⟩ := List.mem_map.mp hmem
        refine ⟨i, j, ?_, List.mem_range.mp hj, harea⟩
        rcases Nat.lt_or_ge j i with hji | hji
        · exfalso
          apply hzero
          have hwidth : j + 1 - i = 0 := by omega
          have harea0 : rectArea hist.heights i j = 0 := by
            show minList _ * (j + 1 - i) = 0
            rw [hwidth, Nat.mul_zero]
          exact harea.symm.trans harea0
        · exact hji

end AxiomCode
