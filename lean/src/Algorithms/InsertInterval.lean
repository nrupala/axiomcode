import Spec
import Tactics

/-!
# AxiomCode — Verified Interval Insertion

Promoted from `lean/drafts/insertinterval_correctness.lean` under
the L2 promotion procedure (`lean/PROMOTION.md`). The draft's shells
are authored for real: `Interval` gains the fields its statements
reference (`start`, and `«end»` — `end` is a Lean keyword and cannot
be a bare field name, so the field is spelled with guillemets; its
projection still prints as `.end`), the `.invariant` its first
conjunct names becomes the def `Interval.invariant`
(`start ≤ «end»`), and `insertInterval` is insertion into a list
ordered by `start`, without merging.

Statement honesty, two records:

1. **The draft's first conjunct is FALSE as stated.** It claims every
   interval of the output satisfies `.invariant`, with no hypothesis
   on the input: but take `intervals = [⟨5, 3⟩]` — the output
   contains `⟨5, 3⟩`, whose invariant `5 ≤ 3` fails; likewise a
   malformed `newInterval` alone falsifies it on `intervals = []`.
   The theorem is carried with the two hypotheses the claim needs —
   every input interval satisfies the invariant, and so does the new
   interval — added in front of the draft's `let`, the rest of the
   statement in the draft's exact shape (LRU/quickselect precedent:
   the missing hypothesis is named, not silently assumed).

2. **The authored algorithm does not merge.** The draft's second and
   third conjuncts pin the output's `(start, «end»)` pairs to be
   exactly the input's pairs plus the new interval's pair; a merging
   insertion falsifies both (inserting `[2, 5]` into `[[1, 2]]`
   would merge to `[[1, 5]]`, whose pair occurs in neither the input
   nor the singleton). So the algorithm the draft's statement
   describes is insertion without merging, and that is what is
   authored and proved.
-/

namespace AxiomCode

/-- An interval of naturals, `start` to `«end»`. -/
structure Interval where
  start : Nat
  «end» : Nat
deriving DecidableEq, Repr

/-- The interval invariant: the start does not exceed the end. -/
def Interval.invariant (i : Interval) : Prop :=
  i.start ≤ i.«end»

/-- Insert `newInterval` into a list of intervals, keeping the list
ordered by `start` (before the first interval whose start is not
smaller). No merging: every input interval survives unchanged. -/
def insertInterval : List Interval → Interval → List Interval
  | [], n => [n]
  | i :: is, n =>
    if n.start ≤ i.start then n :: i :: is else i :: insertInterval is n

/-- Consing an element onto a list permutes to appending it. -/
theorem perm_cons_append (n : Interval) (is : List Interval) :
    (n :: is).Perm (is ++ [n]) := by
  induction is with
  | nil => exact List.Perm.refl _
  | cons x xs ih =>
    exact (List.Perm.swap x n xs).trans (List.Perm.cons x ih)

/-- Insertion permutes the input with the new interval appended. -/
theorem insertInterval_perm (is : List Interval) (n : Interval) :
    (insertInterval is n).Perm (is ++ [n]) := by
  induction is with
  | nil => exact List.Perm.refl _
  | cons i is ih =>
    by_cases h : n.start ≤ i.start
    · have hunfold : insertInterval (i :: is) n = n :: i :: is := by
        simp only [insertInterval, h, ite_true]
      rw [hunfold]
      exact perm_cons_append n (i :: is)
    · have hunfold : insertInterval (i :: is) n =
          i :: insertInterval is n := by
        simp only [insertInterval, h, ite_false]
      rw [hunfold]
      exact List.Perm.cons i ih

/-- The draft's correctness theorem, in its exact shape, with the
two invariant hypotheses its first conjunct needs (see the module
doc): every output interval satisfies the invariant; every input
interval's pair survives into the output; every output interval's
pair comes from the input or is the new interval's. -/
theorem insertInterval_correctness :
    ∀ (intervals : List Interval) (newInterval : Interval),
      (∀ i ∈ intervals, i.invariant) → newInterval.invariant →
      let inserted := insertInterval intervals newInterval
      (∀ i ∈ inserted, i.invariant) ∧
      (∀ i ∈ intervals, ∃ j ∈ inserted,
        i.start = j.start ∧ i.«end» = j.«end») ∧
      (∀ i ∈ inserted, ∃ j ∈ intervals ++ [newInterval],
        i.start = j.start ∧ i.«end» = j.«end») := by
  intro intervals newInterval hinv hnew
  have hperm := insertInterval_perm intervals newInterval
  refine ⟨?_, ?_, ?_⟩
  · intro i hi
    have hi' : i ∈ intervals ++ [newInterval] := hperm.mem_iff.mp hi
    cases List.mem_append.mp hi' with
    | inl h => exact hinv i h
    | inr h =>
      have hi2 : i = newInterval := List.mem_singleton.mp h
      subst hi2
      exact hnew
  · intro i hi
    exact ⟨i, hperm.mem_iff.mpr (List.mem_append_left _ hi), rfl, rfl⟩
  · intro i hi
    exact ⟨i, hperm.mem_iff.mp hi, rfl, rfl⟩

end AxiomCode
