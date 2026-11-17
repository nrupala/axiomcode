import Spec
import Tactics
import Algorithms.ProductExceptSelf

/-!
# AxiomCode — Verified Trapping Rain Water

Promoted from `lean/drafts/algorithm_correctness (problem.lean`
under the L2 promotion procedure (`lean/PROMOTION.md`). The draft's
shells are authored for real: `RainWaterProblem` gains the
`heights` field its statement references, and the draft's four
body-less definitions (`maxLeft`, `maxRight`, `trappedWaterAt`,
`totalTrappedWater`) are authored with their natural meanings — the
strict maxima to the left and to the right of a position, the water
standing at a position, and the total over all positions.

Statement honesty: the draft's theorem reads
`totalTrappedWater problem.heights = ...` — its right-hand side is a
literal hole in the draft, so there is no stated claim to carry
verbatim. The claim authored in its place, in the draft's shape
(definition-by-definition equality with the efficient algorithm), is
that the per-position definition equals the standard linear
algorithm: precompute at each position the inclusive prefix maximum
(`leftMaxes`) and the inclusive suffix maximum (`rightMaxes`), then
the water at `i` is `min leftMax[i] rightMax[i] - heights[i]`. The
equality is proved position by position: `maxLeft` folded with the
bar itself is the inclusive prefix maximum, and `maxRight` folded
with the bar itself is the inclusive suffix maximum.
-/

namespace AxiomCode

/-- A trapping-rain-water problem: a list of bar heights. -/
structure RainWaterProblem where
  heights : List Nat
deriving DecidableEq, Repr

/-- The tallest bar strictly to the left of position `i`. -/
def maxLeft (heights : List Nat) (i : Nat) : Nat :=
  (heights.take i).foldl max 0

/-- The tallest bar strictly to the right of position `i`. -/
def maxRight (heights : List Nat) (i : Nat) : Nat :=
  (heights.drop (i + 1)).foldl max 0

/-- The water standing at position `i`: the lower of the two side
maxima (each taken with the bar itself), minus the bar. -/
def trappedWaterAt (heights : List Nat) (i : Nat) : Nat :=
  min (max (maxLeft heights i) heights[i]!) (max (maxRight heights i) heights[i]!)
    - heights[i]!

/-- The total trapped water: `trappedWaterAt` summed over all
positions. -/
def totalTrappedWater (heights : List Nat) : Nat :=
  ((List.range heights.length).map (trappedWaterAt heights)).sum

/-- Inclusive prefix maxima: entry `i` is the tallest bar in
`heights[0..i]`. -/
def leftMaxes : List Nat → List Nat
  | [] => []
  | x :: xs => x :: (leftMaxes xs).map (max x)

/-- Inclusive suffix maxima: entry `i` is the tallest bar in
`heights[i..]`, built by a right fold that carries the running
maximum in the head of the accumulator. -/
def rightMaxes (heights : List Nat) : List Nat :=
  heights.foldr (fun x acc => (max x (acc.head?.getD 0)) :: acc) []

/-- The linear algorithm: water at `i` is
`min leftMax[i] rightMax[i] - heights[i]`, summed over all
positions. -/
def trap (heights : List Nat) : Nat :=
  ((List.range heights.length).map
    (fun i => min (leftMaxes heights)[i]! (rightMaxes heights)[i]!
      - heights[i]!)).sum

/-- `!`-indexing a cons at `0`. -/
theorem getElem!_cons_zero {α : Type} [Inhabited α] (a : α) (l : List α) :
    (a :: l)[0]! = a := by
  rw [List.getElem!_eq_getElem?_getD, List.getElem?_cons_zero]
  rfl

/-- `!`-indexing a cons at a successor. -/
theorem getElem!_cons_succ {α : Type} [Inhabited α] (a : α) (l : List α)
    (i : Nat) : (a :: l)[i + 1]! = l[i]! := by
  rw [List.getElem!_eq_getElem?_getD, List.getElem!_eq_getElem?_getD,
    List.getElem?_cons_succ]

/-- `!`-indexing at a valid index is the proof-carrying index. -/
theorem getElem!_eq_getElem_of_lt {α : Type} [Inhabited α] {l : List α}
    {i : Nat} (h : i < l.length) : l[i]! = l[i]'h := by
  rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem h]
  rfl

/-- Folding `max` from any starting value: the start joins the fold. -/
theorem foldl_max_init_eq (l : List Nat) (init : Nat) :
    l.foldl max init = max init (l.foldl max 0) := by
  induction l generalizing init with
  | nil => exact (Nat.max_zero init).symm
  | cons a l ih =>
    rw [List.foldl_cons, List.foldl_cons, Nat.zero_max,
      ih (init := max init a), ih (init := a)]
    exact Nat.max_assoc init a (l.foldl max 0)

/-- One more bar joins the left maximum: folding `max` over
`take (i + 1)` is the left maximum at `i` joined with bar `i`. -/
theorem foldl_max_take_succ {h : List Nat} {i : Nat} (hi : i < h.length) :
    (h.take (i + 1)).foldl max 0 = max ((h.take i).foldl max 0) h[i]! := by
  rw [List.take_add_one, List.getElem?_eq_getElem hi, List.foldl_append,
    getElem!_eq_getElem_of_lt hi]
  rfl

/-- `leftMaxes` preserves length. -/
theorem length_leftMaxes (h : List Nat) : (leftMaxes h).length = h.length := by
  induction h with
  | nil => rfl
  | cons x xs ih => simp [leftMaxes, ih]

/-- Entry `i` of `leftMaxes` is the fold of `max` over
`take (i + 1)`. -/
theorem getElem!_leftMaxes (h : List Nat) (i : Nat) (hi : i < h.length) :
    (leftMaxes h)[i]! = (h.take (i + 1)).foldl max 0 := by
  induction h generalizing i with
  | nil => exact absurd hi (by simp)
  | cons x xs ih =>
    have hlm : leftMaxes (x :: xs) = x :: (leftMaxes xs).map (max x) := rfl
    cases i with
    | zero =>
      rw [hlm, getElem!_cons_zero, List.take_succ_cons]
      rfl
    | succ i =>
      have hi' : i < xs.length := by
        have := hi
        simp at this ⊢
        omega
      have hlen : i < (leftMaxes xs).length := by
        rw [length_leftMaxes]
        exact hi'
      rw [hlm, getElem!_cons_succ, getElem!_map_of_lt hlen, ih i hi',
        List.take_succ_cons, List.foldl_cons, Nat.zero_max,
        ← foldl_max_init_eq]

/-- The head of `rightMaxes` (with default `0`) is the fold of `max`
over the whole list. -/
theorem rightMaxes_head (h : List Nat) :
    (rightMaxes h).head?.getD 0 = h.foldl max 0 := by
  induction h with
  | nil => rfl
  | cons x xs ih =>
    show max x ((rightMaxes xs).head?.getD 0) = (x :: xs).foldl max 0
    rw [ih, List.foldl_cons, Nat.zero_max, foldl_max_init_eq xs x]

/-- Entry `i` of `rightMaxes` is the fold of `max` over `drop i`. -/
theorem getElem!_rightMaxes (h : List Nat) (i : Nat) (hi : i < h.length) :
    (rightMaxes h)[i]! = (h.drop i).foldl max 0 := by
  induction h generalizing i with
  | nil => exact absurd hi (by simp)
  | cons x xs ih =>
    have hrm : rightMaxes (x :: xs) =
        (max x ((rightMaxes xs).head?.getD 0)) :: rightMaxes xs := rfl
    cases i with
    | zero =>
      rw [hrm, getElem!_cons_zero, rightMaxes_head]
      show max x (xs.foldl max 0) = (x :: xs).foldl max 0
      rw [List.foldl_cons, Nat.zero_max, foldl_max_init_eq xs x]
    | succ i =>
      have hi' : i < xs.length := by
        have := hi
        simp at this ⊢
        omega
      rw [hrm, getElem!_cons_succ, ih i hi']
      rfl

/-- The pointwise equality behind the main theorem: the
per-position definition at a valid index `i` is the linear
algorithm's per-position value. -/
theorem trappedWaterAt_eq (h : List Nat) (i : Nat) (hi : i < h.length) :
    trappedWaterAt h i =
      min (leftMaxes h)[i]! (rightMaxes h)[i]! - h[i]! := by
  have hleft : max (maxLeft h i) h[i]! = (leftMaxes h)[i]! := by
    show max ((h.take i).foldl max 0) h[i]! = (leftMaxes h)[i]!
    rw [getElem!_leftMaxes h i hi, foldl_max_take_succ hi]
  have hright : max (maxRight h i) h[i]! = (rightMaxes h)[i]! := by
    rw [getElem!_rightMaxes h i hi]
    show max ((h.drop (i + 1)).foldl max 0) h[i]! = (h.drop i).foldl max 0
    rw [← List.getElem_cons_drop hi]
    rw [List.foldl_cons, Nat.zero_max, getElem!_eq_getElem_of_lt hi,
      foldl_max_init_eq (h.drop (i + 1)) (h[i]'hi), Nat.max_comm]
  show min (max (maxLeft h i) h[i]!) (max (maxRight h i) h[i]!) - h[i]! = _
  rw [hleft, hright]

/-- Summing pointwise-equal functions over the same list. -/
theorem sum_map_congr {f g : Nat → Nat} {l : List Nat}
    (h : ∀ x ∈ l, f x = g x) : (l.map f).sum = (l.map g).sum := by
  induction l with
  | nil => rfl
  | cons a l ih =>
    rw [List.map_cons, List.map_cons, List.sum_cons, List.sum_cons,
      h a (by simp), ih (fun x hx => h x (List.mem_cons_of_mem a hx))]

/-- The draft's theorem with its holed right-hand side authored as
the linear algorithm: the per-position definition of trapped water
equals the prefix/suffix-maxima algorithm. -/
theorem RainWaterProblem.algorithm_correctness (problem : RainWaterProblem) :
    totalTrappedWater problem.heights = trap problem.heights := by
  show ((List.range problem.heights.length).map
      (trappedWaterAt problem.heights)).sum =
    ((List.range problem.heights.length).map
      (fun i => min (leftMaxes problem.heights)[i]!
        (rightMaxes problem.heights)[i]! - problem.heights[i]!)).sum
  exact sum_map_congr (fun i hi =>
    trappedWaterAt_eq problem.heights i (List.mem_range.mp hi))

end AxiomCode
