import Spec
import Tactics

/-!
# AxiomCode — Verified Kadane (maximum subarray sum)

Promoted from `lean/drafts/kadane_correctness.lean` under the L2
promotion procedure (`lean/PROMOTION.md`). Authored and proved by
Arjun (Item 5B, own-hands track).

Statement-honesty record. The draft was a shell: a fieldless
`KadaneInput` structure, a body-less `kadane`, and a statement in
generator dialect — `kadane input = List.max (List.scanl …).get?` —
whose `List.max`/`.get?` combination does not elaborate in this
toolchain. Its mathematical content is exact, and it is carried
verbatim in substance: with the draft's own step function
(`kadaneStep`) and its scan of ending values (`kadaneEndings`, the
draft's `List.scanl` expression), the maximum the draft names is
stated in the library's two-direction form — `kadane_correct`: the
algorithm's value occurs among the ending values and bounds them all.
The algorithm itself (`kadaneFrom`, `kadane`) is the genuine
single-pass state machine over `List Int`, not the scan: the scan is
the specification, and `kadaneFrom_spec` is the bridge, proved by
induction with the state invariant `cur ≤ best`.
-/

namespace AxiomCode

/-- The draft's step function, verbatim: best subarray sum ending at the
new element, restarted at the element or extended. -/
def kadaneStep (acc x : Int) : Int := max x (acc + x)

/-- The single-pass algorithm with explicit state: `cur` = best sum of a
subarray ending at the current position, `best` = best seen anywhere. -/
def kadaneFrom : Int → Int → List Int → Int
  | _, best, [] => best
  | cur, best, x :: xs =>
    kadaneFrom (kadaneStep cur x) (max best (kadaneStep cur x)) xs

/-- Kadane's algorithm: maximum subarray sum, empty subarray allowed. -/
def kadane (l : List Int) : Int := kadaneFrom 0 0 l

/-- The ending values: `scanl` of the step from the empty subarray. -/
def kadaneEndings (l : List Int) : List Int := List.scanl kadaneStep 0 l

/-- The maximum of the ending values, recursively: the largest value in
`List.scanl kadaneStep cur l`, whose head is `cur` itself. -/
def endingsMax : Int → List Int → Int
  | cur, [] => cur
  | cur, x :: xs => max cur (endingsMax (kadaneStep cur x) xs)

theorem endingsMax_mem (cur : Int) (l : List Int) :
    endingsMax cur l ∈ List.scanl kadaneStep cur l := by
  induction l generalizing cur with
  | nil => simp [endingsMax, List.scanl]
  | cons x xs ih =>
    have h1 : List.scanl kadaneStep cur (x :: xs) =
        cur :: List.scanl kadaneStep (kadaneStep cur x) xs := List.scanl_cons
    have h2 : endingsMax cur (x :: xs) =
        max cur (endingsMax (kadaneStep cur x) xs) := rfl
    rw [h1, h2]
    by_cases h : endingsMax (kadaneStep cur x) xs ≤ cur
    · have hm : max cur (endingsMax (kadaneStep cur x) xs) = cur := by omega
      rw [hm]; exact List.mem_cons_self
    · have hm : max cur (endingsMax (kadaneStep cur x) xs) =
          endingsMax (kadaneStep cur x) xs := by omega
      rw [hm]; exact List.mem_cons_of_mem _ (ih _)

theorem endingsMax_max (cur : Int) (l : List Int) :
    ∀ y ∈ List.scanl kadaneStep cur l, y ≤ endingsMax cur l := by
  induction l generalizing cur with
  | nil => intro y hy; simp [List.scanl] at hy; rw [hy]; simp [endingsMax]
  | cons x xs ih =>
    intro y hy
    have h1 : List.scanl kadaneStep cur (x :: xs) =
        cur :: List.scanl kadaneStep (kadaneStep cur x) xs := List.scanl_cons
    have h2 : endingsMax cur (x :: xs) =
        max cur (endingsMax (kadaneStep cur x) xs) := rfl
    rw [h1] at hy; rw [h2]
    rcases List.mem_cons.mp hy with rfl | hy
    · omega
    · have hy2 := ih _ y hy; omega

theorem endingsMax_ge (cur : Int) (l : List Int) : cur ≤ endingsMax cur l :=
  endingsMax_max cur l cur (by
    cases l with
    | nil => simp [List.scanl]
    | cons x xs => rw [List.scanl_cons]; exact List.mem_cons_self)

theorem kadaneFrom_spec (cur best : Int) (hcb : cur ≤ best) (l : List Int) :
    kadaneFrom cur best l = max best (endingsMax cur l) := by
  induction l generalizing cur best with
  | nil => simp only [kadaneFrom, endingsMax]; omega
  | cons x xs ih =>
    have h1 : kadaneFrom cur best (x :: xs) =
        kadaneFrom (kadaneStep cur x) (max best (kadaneStep cur x)) xs := rfl
    have h2 : endingsMax cur (x :: xs) =
        max cur (endingsMax (kadaneStep cur x) xs) := rfl
    have hcb' : kadaneStep cur x ≤ max best (kadaneStep cur x) := by omega
    rw [h1, ih _ _ hcb', h2]
    have hES : kadaneStep cur x ≤ endingsMax (kadaneStep cur x) xs :=
      endingsMax_ge _ _
    omega

/-- The draft's claim, in elaborable form: kadane's value is the maximum
of the ending values — it occurs among them, and bounds them all. -/
theorem kadane_correct (l : List Int) :
    kadane l ∈ kadaneEndings l ∧ ∀ y ∈ kadaneEndings l, y ≤ kadane l := by
  have h : kadane l = endingsMax 0 l := by
    have hge := endingsMax_ge (0 : Int) l
    rw [kadane, kadaneFrom_spec 0 0 (by omega) l]
    omega
  constructor
  · rw [h]; exact endingsMax_mem 0 l
  · intro y hy; rw [h]; exact endingsMax_max 0 l y hy


end AxiomCode
