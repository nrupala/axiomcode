import Spec
import Tactics
import Algorithms.LargestRectangle
import Algorithms.RainWater

/-!
# AxiomCode — Verified Maximal Square

Promoted from `lean/drafts/maximal_square_correctness.lean` under
the L2 promotion procedure (`lean/PROMOTION.md`). The draft's
shells are authored for real: `is_square` checks, by `List.all`
over the square's cells, that every cell of the `size × size`
square at `top_left` is `true` (out-of-range cells read the default
`false`, so a square poking outside the matrix is not a square);
`maximal_square_size` searches downward from the matrix's height
for the largest size for which a square exists somewhere.

Statement honesty: **the draft's theorem has no referent.** It
reads `∀ matrix, maximal_square_size matrix = MaximalSquare.size`,
but `MaximalSquare` is a fieldless structure — there is no `size`
field for the projection to denote, and any constant reading is
false anyway, since the maximal size varies with the matrix (`[]`
gives `0`, `[[true]]` gives `1`). The structure is authored as the
problem record holding the `matrix` the claim is about, and the
theorem is carried in the draft's shape — a statement about
`maximal_square_size matrix` for every `matrix` — with the
meaningless right-hand side repaired to the property that defines
the maximal size: it is **attained** (some square of that size is
all-`true`) and it is an **upper bound** (no larger all-`true`
square exists anywhere).
-/

namespace AxiomCode

/-- A maximal-square problem: the matrix being searched. -/
structure MaximalSquare where
  matrix : List (List Bool)
deriving DecidableEq, Repr

/-- The number of columns of a matrix: the longest row. -/
def maxRowLength (matrix : List (List Bool)) : Nat :=
  (matrix.map List.length).foldl max 0

/-- Whether the `size × size` square with top-left corner
`top_left` consists entirely of `true` cells. -/
def is_square (matrix : List (List Bool)) (size : Nat)
    (top_left : Nat × Nat) : Bool :=
  (List.range size).all (fun di =>
    (List.range size).all (fun dj =>
      matrix[top_left.1 + di]![top_left.2 + dj]!))

/-- Whether an all-`true` square of size `s` exists anywhere in
the matrix. -/
def existsSquare (matrix : List (List Bool)) (s : Nat) : Bool :=
  (List.range (matrix.length + 1)).any (fun i =>
    (List.range (maxRowLength matrix + 1)).any (fun j =>
      is_square matrix s (i, j)))

/-- The largest existing square size not exceeding `bound`:
try `bound` first, then descend. -/
def maximalUpTo (matrix : List (List Bool)) : Nat → Nat
  | 0 => 0
  | s + 1 =>
    if existsSquare matrix (s + 1) then s + 1 else maximalUpTo matrix s

/-- The size of the largest all-`true` square in the matrix. -/
def maximal_square_size (matrix : List (List Bool)) : Nat :=
  maximalUpTo matrix matrix.length

/-- `!`-indexing at or beyond the length reads the default. -/
theorem getElem!_eq_default_of_le {α : Type} [Inhabited α] {l : List α}
    {i : Nat} (h : l.length ≤ i) : l[i]! = default := by
  rw [List.getElem!_eq_getElem?_getD, (List.getElem?_eq_none_iff).mpr h]
  rfl

/-- Every cell of an all-`true` square is `true`. -/
theorem is_square_cell {matrix : List (List Bool)} {s i j di dj : Nat}
    (hsq : is_square matrix s (i, j) = true) (hdi : di < s) (hdj : dj < s) :
    matrix[i + di]![j + dj]! = true := by
  have h1 := List.all_eq_true.mp hsq di (List.mem_range.mpr hdi)
  exact List.all_eq_true.mp h1 dj (List.mem_range.mpr hdj)

/-- An all-`true` square of positive size fits in the matrix's
height: its bottom row is a genuine row. -/
theorem is_square_length_le {matrix : List (List Bool)} {s i j : Nat}
    (hsq : is_square matrix s (i, j) = true) (hs : 1 ≤ s) :
    s ≤ matrix.length := by
  have hcell := is_square_cell hsq (show s - 1 < s by omega)
    (show 0 < s by omega)
  by_cases hlt : i + (s - 1) < matrix.length
  · omega
  · exfalso
    have e1 : matrix[i + (s - 1)]! = [] :=
      getElem!_eq_default_of_le (show matrix.length ≤ i + (s - 1) by omega)
    rw [e1, Nat.add_zero] at hcell
    have e2 : ([] : List Bool)[j]! = false :=
      getElem!_eq_default_of_le (by simp)
    rw [e2] at hcell
    exact Bool.false_ne_true hcell

/-- The top row index of an all-`true` square of positive size is
a genuine row index (same cell argument as `is_square_length_le`,
keeping the row bound itself). -/
theorem is_square_row_lt {matrix : List (List Bool)} {s i j : Nat}
    (hsq : is_square matrix s (i, j) = true) (hs : 1 ≤ s) :
    i < matrix.length := by
  have hcell := is_square_cell hsq (show s - 1 < s by omega)
    (show 0 < s by omega)
  by_cases hlt : i + (s - 1) < matrix.length
  · omega
  · exfalso
    have e1 : matrix[i + (s - 1)]! = [] :=
      getElem!_eq_default_of_le (show matrix.length ≤ i + (s - 1) by omega)
    rw [e1, Nat.add_zero] at hcell
    have e2 : ([] : List Bool)[j]! = false :=
      getElem!_eq_default_of_le (by simp)
    rw [e2] at hcell
    exact Bool.false_ne_true hcell

/-- The right edge of an all-`true` square of positive size fits
in its top row's length. -/
theorem is_square_col_lt {matrix : List (List Bool)} {s i j : Nat}
    (hsq : is_square matrix s (i, j) = true) (hs : 1 ≤ s) :
    j + (s - 1) < (matrix[i]!).length := by
  have hcell := is_square_cell hsq (show 0 < s by omega)
    (show s - 1 < s by omega)
  by_cases hlt : j + (s - 1) < (matrix[i]!).length
  · exact hlt
  · exfalso
    have e2 : (matrix[i]!)[j + (s - 1)]! = false :=
      getElem!_eq_default_of_le (show (matrix[i]!).length ≤ j + (s - 1)
        by omega)
    rw [Nat.add_zero, e2] at hcell
    exact Bool.false_ne_true hcell

/-- A genuine row's length is at most the matrix's `maxRowLength`
(the banked fold-max membership bound from `LargestRectangle`). -/
theorem row_length_le_maxRowLength (matrix : List (List Bool)) (i : Nat)
    (hi : i < matrix.length) :
    (matrix[i]!).length ≤ maxRowLength matrix := by
  rw [getElem!_eq_getElem_of_lt hi]
  exact le_foldl_max_of_mem
    (List.mem_map.mpr ⟨matrix[i]'hi, List.getElem_mem hi, rfl⟩)

/-- An all-`true` square somewhere makes `existsSquare` true, when
its position is inside the searched ranges. -/
theorem existsSquare_of_is_square {matrix : List (List Bool)} {s i j : Nat}
    (hsq : is_square matrix s (i, j) = true)
    (hi : i ≤ matrix.length) (hj : j ≤ maxRowLength matrix) :
    existsSquare matrix s = true := by
  show (List.range (matrix.length + 1)).any (fun i =>
    (List.range (maxRowLength matrix + 1)).any (fun j =>
      is_square matrix s (i, j))) = true
  rw [List.any_eq_true]
  exact ⟨i, List.mem_range.mpr (by omega), by
    rw [List.any_eq_true]
    exact ⟨j, List.mem_range.mpr (by omega), hsq⟩⟩

/-- `maximalUpTo` never exceeds its bound. -/
theorem maximalUpTo_le (matrix : List (List Bool)) (b : Nat) :
    maximalUpTo matrix b ≤ b := by
  induction b with
  | zero => exact Nat.le_refl 0
  | succ b ih =>
    by_cases h : existsSquare matrix (b + 1) = true
    · have hunfold : maximalUpTo matrix (b + 1) = b + 1 := by
        simp only [maximalUpTo, h, ite_true]
      omega
    · have hunfold : maximalUpTo matrix (b + 1) = maximalUpTo matrix b := by
        simp only [maximalUpTo, h, Bool.false_eq_true, ite_false]
      omega

/-- Any existing square size under the bound is at most
`maximalUpTo`. -/
theorem existsSquare_le_maximalUpTo {matrix : List (List Bool)}
    {s b : Nat} (hsq : existsSquare matrix s = true) (hsb : s ≤ b) :
    s ≤ maximalUpTo matrix b := by
  induction b with
  | zero => exact hsb
  | succ b ih =>
    by_cases h : existsSquare matrix (b + 1) = true
    · have hunfold : maximalUpTo matrix (b + 1) = b + 1 := by
        simp only [maximalUpTo, h, ite_true]
      rw [hunfold]
      exact hsb
    · have hunfold : maximalUpTo matrix (b + 1) = maximalUpTo matrix b := by
        simp only [maximalUpTo, h, Bool.false_eq_true, ite_false]
      rw [hunfold]
      by_cases hs2 : s = b + 1
      · rw [hs2] at hsq
        exact absurd hsq h
      · exact ih (by omega)

/-- `maximalUpTo` is attained: it is `0` (the empty square always
exists) or a size for which a square exists. -/
theorem maximalUpTo_attained (matrix : List (List Bool)) (b : Nat) :
    maximalUpTo matrix b = 0 ∨
      existsSquare matrix (maximalUpTo matrix b) = true := by
  induction b with
  | zero => exact Or.inl rfl
  | succ b ih =>
    by_cases h : existsSquare matrix (b + 1) = true
    · have hunfold : maximalUpTo matrix (b + 1) = b + 1 := by
        simp only [maximalUpTo, h, ite_true]
      rw [hunfold]
      exact Or.inr h
    · have hunfold : maximalUpTo matrix (b + 1) = maximalUpTo matrix b := by
        simp only [maximalUpTo, h, Bool.false_eq_true, ite_false]
      rw [hunfold]
      exact ih

/-- The draft's theorem with its referent-less right-hand side
repaired to the defining property of the maximal size (see the
module doc): the returned size is attained by an all-`true`
square, and no all-`true` square anywhere is larger. -/
theorem maximal_square_correctness :
    ∀ matrix : List (List Bool),
      (∃ i j, is_square matrix (maximal_square_size matrix) (i, j) = true) ∧
      (∀ s i j, is_square matrix s (i, j) = true →
        s ≤ maximal_square_size matrix) := by
  intro matrix
  constructor
  · cases maximalUpTo_attained matrix matrix.length with
    | inl h0 =>
      refine ⟨0, 0, ?_⟩
      show is_square matrix (maximalUpTo matrix matrix.length) (0, 0) = true
      rw [h0]
      rfl
    | inr hsq =>
      show ∃ i j, is_square matrix (maximalUpTo matrix matrix.length)
        (i, j) = true
      have h1 : ∃ i ∈ List.range (matrix.length + 1),
          (List.range (maxRowLength matrix + 1)).any (fun j =>
            is_square matrix (maximalUpTo matrix matrix.length)
              (i, j)) = true :=
        List.any_eq_true.mp hsq
      obtain ⟨i, _, h2⟩ := h1
      obtain ⟨j, _, h3⟩ := List.any_eq_true.mp h2
      exact ⟨i, j, h3⟩
  · intro s i j hsq
    show s ≤ maximalUpTo matrix matrix.length
    cases Nat.eq_zero_or_pos s with
    | inl h0 => omega
    | inr hs =>
      have hs1 : 1 ≤ s := hs
      have hlen : s ≤ matrix.length := is_square_length_le hsq hs1
      have hi : i ≤ matrix.length :=
        Nat.le_of_lt (is_square_row_lt hsq hs1)
      have hj : j ≤ maxRowLength matrix := by
        have hcol := is_square_col_lt hsq hs1
        have hrow := row_length_le_maxRowLength matrix i
          (is_square_row_lt hsq hs1)
        omega
      exact existsSquare_le_maximalUpTo
        (existsSquare_of_is_square hsq hi hj) hlen

end AxiomCode
