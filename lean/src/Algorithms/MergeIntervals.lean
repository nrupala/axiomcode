import Spec
import Tactics
import Algorithms.InsertInterval

/-!
# AxiomCode — Verified Interval Merging

Promoted from `lean/drafts/mergeintervals_correctness.lean` under
the L2 promotion procedure (`lean/PROMOTION.md`). The draft's
`Interval` is the structure authored for insert-interval (Entry 4
of this part) — same name, same intended fields — so this module
imports and reuses it rather than defining a rival. The draft's
body-less `mergeIntervals` is authored as: sort by start
(insertion sort, `sortByStart`), then sweep left to right merging
each interval into the current one while it overlaps or touches
(`mergeInto`). The two symbols the draft's statement uses without
definition are authored with their natural meanings: `i ≤ j` is
the pointwise order on `(start, «end»)` (an `LE Interval`
instance), and `disjoint i j` is strict separation — one interval
ends strictly before the other starts. (Touching intervals are
therefore not disjoint, and the sweep merges them, matching the
usual convention.) With those authorings, **the draft's statement
is true and is carried exactly as stated**, in its `let` shape.

The proof is one invariant bundle for the sweep
(`mergeInto_spec`): the output is pairwise strictly separated;
every output start is the current interval's start or a swept
interval's start; and every output interval's end is the end of
some interval among the current one and the swept ones, whose
start is at least the output's start. The first conjunct of the
draft follows from the third component plus the sort's
permutation; the second from the first component by a pairwise
extraction lemma.
-/

namespace AxiomCode

/-- The pointwise order on intervals: `i ≤ j` when both `i.start`
and `i.«end»` are at most `j`'s. -/
instance : LE Interval where
  le a b := a.start ≤ b.start ∧ a.«end» ≤ b.«end»

/-- Strict separation: one interval ends strictly before the
other starts. -/
def disjoint (a b : Interval) : Prop :=
  a.«end» < b.start ∨ b.«end» < a.start

/-- Insert into a list by start order. -/
def insertByStart (n : Interval) : List Interval → List Interval
  | [] => [n]
  | i :: is =>
    if n.start ≤ i.start then n :: i :: is else i :: insertByStart n is

/-- Insertion sort by start. -/
def sortByStart : List Interval → List Interval
  | [] => []
  | i :: is => insertByStart i (sortByStart is)

/-- Sweep: merge `next` into `cur` while it overlaps or touches
(`next.start ≤ cur.«end»`), extending the current end; otherwise
emit `cur` and restart with `next`. -/
def mergeInto (cur : Interval) : List Interval → List Interval
  | [] => [cur]
  | next :: rest =>
    if next.start ≤ cur.«end» then
      mergeInto ⟨cur.start, max cur.«end» next.«end»⟩ rest
    else
      cur :: mergeInto next rest

/-- Merge a start-sorted list. -/
def mergeSorted : List Interval → List Interval
  | [] => []
  | i :: is => mergeInto i is

/-- Merge all overlapping or touching intervals of the list. -/
def mergeIntervals (intervals : List Interval) : List Interval :=
  mergeSorted (sortByStart intervals)

/-- Insertion by start permutes the cons. -/
theorem insertByStart_perm {n : Interval} :
    ∀ l : List Interval, (insertByStart n l).Perm (n :: l) := by
  intro l
  induction l with
  | nil => exact List.Perm.refl _
  | cons i is ih =>
    by_cases h : n.start ≤ i.start
    · have hunfold : insertByStart n (i :: is) = n :: i :: is := by
        simp only [insertByStart, h, ite_true]
      rw [hunfold]
    · have hunfold : insertByStart n (i :: is) =
          i :: insertByStart n is := by
        simp only [insertByStart, h, ite_false]
      rw [hunfold]
      exact (List.Perm.cons i ih).trans (List.Perm.swap n i is)

/-- Sorting by start is a permutation. -/
theorem sortByStart_perm :
    ∀ l : List Interval, (sortByStart l).Perm l := by
  intro l
  induction l with
  | nil => exact List.Perm.refl _
  | cons i is ih =>
    exact (insertByStart_perm _).trans (List.Perm.cons i ih)

/-- Insertion by start preserves pairwise start order (elements
passed over have smaller starts; elements at and after the
insertion point have starts at least the inserted one, by the
pairwise hypothesis). -/
theorem pairwise_insertByStart {n : Interval} :
    ∀ {l : List Interval}, l.Pairwise (fun a b => a.start ≤ b.start) →
      (insertByStart n l).Pairwise (fun a b => a.start ≤ b.start) := by
  intro l hp
  induction l with
  | nil =>
    simp only [insertByStart]
    exact List.Pairwise.cons (fun y hy => by simp at hy) List.Pairwise.nil
  | cons i is ih =>
    have hp' := List.pairwise_cons.mp hp
    by_cases h : n.start ≤ i.start
    · have hunfold : insertByStart n (i :: is) = n :: i :: is := by
        simp only [insertByStart, h, ite_true]
      rw [hunfold]
      refine List.pairwise_cons.mpr ⟨?_, hp⟩
      intro y hy
      cases List.mem_cons.mp hy with
      | inl hyi => rw [hyi]; exact h
      | inr hyi => exact Nat.le_trans h (hp'.1 y hyi)
    · have hunfold : insertByStart n (i :: is) =
          i :: insertByStart n is := by
        simp only [insertByStart, h, ite_false]
      rw [hunfold]
      refine List.pairwise_cons.mpr ⟨?_, ih hp'.2⟩
      intro y hy
      have hym : y ∈ n :: is := (insertByStart_perm is).mem_iff.mp hy
      cases List.mem_cons.mp hym with
      | inl hyn => rw [hyn]; omega
      | inr hyi => exact hp'.1 y hyi

/-- The sorted list is pairwise start-ordered. -/
theorem sortByStart_pairwise (l : List Interval) :
    (sortByStart l).Pairwise (fun a b => a.start ≤ b.start) := by
  induction l with
  | nil => exact List.Pairwise.nil
  | cons i is ih => exact pairwise_insertByStart ih

/-- Pairwise extraction: two distinct members of a pairwise list
are related one way or the other. -/
theorem pairwise_disjoint {R : Interval → Interval → Prop}
    {l : List Interval} (hp : l.Pairwise R) {a b : Interval}
    (ha : a ∈ l) (hb : b ∈ l) (hne : a ≠ b) : R a b ∨ R b a := by
  induction l with
  | nil => simp at ha
  | cons x xs ih =>
    have hp' := List.pairwise_cons.mp hp
    cases List.mem_cons.mp ha with
    | inl hax =>
      subst hax
      cases List.mem_cons.mp hb with
      | inl hbx => exact absurd hbx.symm hne
      | inr hbx => exact Or.inl (hp'.1 b hbx)
    | inr hax =>
      cases List.mem_cons.mp hb with
      | inl hbx =>
        subst hbx
        exact Or.inr (hp'.1 a hax)
      | inr hbx => exact ih hp'.2 hax hbx

/-- The sweep's invariant bundle (see the module doc). -/
theorem mergeInto_spec :
    ∀ (rest : List Interval) (cur : Interval),
      rest.Pairwise (fun a b => a.start ≤ b.start) →
      (∀ y ∈ rest, cur.start ≤ y.start) →
      (mergeInto cur rest).Pairwise (fun a b => a.«end» < b.start) ∧
      (∀ m ∈ mergeInto cur rest, m.start = cur.start ∨
        ∃ y ∈ rest, m.start = y.start) ∧
      (∀ m ∈ mergeInto cur rest, ∃ y ∈ cur :: rest,
        y.«end» = m.«end» ∧ m.start ≤ y.start) := by
  intro rest
  induction rest with
  | nil =>
    intro cur _ _
    refine ⟨?_, ?_, ?_⟩
    · exact List.Pairwise.cons (fun y hy => by simp at hy)
        List.Pairwise.nil
    · intro m hm
      have hmc : m = cur := List.mem_singleton.mp hm
      exact Or.inl (by rw [hmc])
    · intro m hm
      have hmc : m = cur := List.mem_singleton.mp hm
      exact ⟨cur, List.mem_cons_self, by rw [hmc],
        by rw [hmc]; exact Nat.le_refl _⟩
  | cons next rest ih =>
    intro cur hp hcur
    have hp' := List.pairwise_cons.mp hp
    have hcur_next : cur.start ≤ next.start :=
      hcur next (List.mem_cons_self)
    have hcur_rest : ∀ y ∈ rest, cur.start ≤ y.start :=
      fun y hy => hcur y (List.mem_cons_of_mem next hy)
    by_cases hmerge : next.start ≤ cur.«end»
    · have hunfold : mergeInto cur (next :: rest) =
          mergeInto ⟨cur.start, max cur.«end» next.«end»⟩ rest := by
        simp only [mergeInto, hmerge, ite_true]
      rw [hunfold]
      have hcur' : ∀ y ∈ rest,
          (⟨cur.start, max cur.«end» next.«end»⟩ : Interval).start ≤
            y.start :=
        fun y hy => hcur_rest y hy
      obtain ⟨hA, hB, hC⟩ :=
        ih ⟨cur.start, max cur.«end» next.«end»⟩ hp'.2 hcur'
      refine ⟨hA, ?_, ?_⟩
      · intro m hm
        cases hB m hm with
        | inl h1 => exact Or.inl h1
        | inr h2 =>
          obtain ⟨y, hy, hys⟩ := h2
          exact Or.inr ⟨y, List.mem_cons_of_mem next hy, hys⟩
      · intro m hm
        obtain ⟨y, hy, hye, hms⟩ := hC m hm
        cases List.mem_cons.mp hy with
        | inr hyr =>
          exact ⟨y, List.mem_cons_of_mem cur
            (List.mem_cons_of_mem next hyr), hye, hms⟩
        | inl hyc =>
          subst hyc
          cases Nat.le_total cur.«end» next.«end» with
          | inl hle =>
            have hmax : max cur.«end» next.«end» = next.«end» :=
              Nat.max_eq_right hle
            refine ⟨next, List.mem_cons_of_mem cur
              (List.mem_cons_self), by rw [hmax] at hye; exact hye, ?_⟩
            have hms' : m.start ≤ cur.start := hms
            omega
          | inr hle =>
            have hmax : max cur.«end» next.«end» = cur.«end» :=
              Nat.max_eq_left hle
            refine ⟨cur, List.mem_cons_self,
              by rw [hmax] at hye; exact hye, ?_⟩
            have hms' : m.start ≤ cur.start := hms
            exact hms'
    · have hunfold : mergeInto cur (next :: rest) =
          cur :: mergeInto next rest := by
        simp only [mergeInto, hmerge, ite_false]
      rw [hunfold]
      obtain ⟨hA, hB, hC⟩ := ih next hp'.2 hp'.1
      refine ⟨?_, ?_, ?_⟩
      · refine List.pairwise_cons.mpr ⟨?_, hA⟩
        intro m hm
        cases hB m hm with
        | inl h1 => omega
        | inr h2 =>
          obtain ⟨y, hy, hys⟩ := h2
          have hle := hp'.1 y hy
          omega
      · intro m hm
        cases List.mem_cons.mp hm with
        | inl hmc => exact Or.inl (by rw [hmc])
        | inr hm' =>
          cases hB m hm' with
          | inl h1 => exact Or.inr ⟨next, List.mem_cons_self, h1⟩
          | inr h2 =>
            obtain ⟨y, hy, hys⟩ := h2
            exact Or.inr ⟨y, List.mem_cons_of_mem next hy, hys⟩
      · intro m hm
        cases List.mem_cons.mp hm with
        | inl hmc =>
          exact ⟨cur, List.mem_cons_self, by rw [hmc],
            by rw [hmc]; exact Nat.le_refl _⟩
        | inr hm' =>
          obtain ⟨y, hy, hye, hms⟩ := hC m hm'
          exact ⟨y, List.mem_cons_of_mem cur hy, hye, hms⟩

/-- The draft's correctness theorem, carried exactly as stated
(with `≤` and `disjoint` authored as in the module doc): every
merged interval is pointwise below some input interval, and any
two distinct merged intervals are disjoint. -/
theorem mergeIntervals_correctness : ∀ intervals : List Interval,
    let merged := mergeIntervals intervals
    (∀ i ∈ merged, ∃ j ∈ intervals, i ≤ j) ∧
    (∀ i ∈ merged, ∀ j ∈ merged, i ≠ j → disjoint i j) := by
  intro intervals
  show (∀ i ∈ mergeIntervals intervals, ∃ j ∈ intervals, i ≤ j) ∧
    (∀ i ∈ mergeIntervals intervals,
      ∀ j ∈ mergeIntervals intervals, i ≠ j → disjoint i j)
  cases hsort : sortByStart intervals with
  | nil =>
    have hm : mergeIntervals intervals = [] := by
      simp only [mergeIntervals, hsort, mergeSorted]
    rw [hm]
    constructor
    · intro i hi
      simp at hi
    · intro i hi
      simp at hi
  | cons i is =>
    have hm : mergeIntervals intervals = mergeInto i is := by
      simp only [mergeIntervals, hsort, mergeSorted]
    have hp : (i :: is).Pairwise (fun a b => a.start ≤ b.start) := by
      rw [← hsort]
      exact sortByStart_pairwise intervals
    have hp' := List.pairwise_cons.mp hp
    obtain ⟨hA, _, hC⟩ := mergeInto_spec is i hp'.2 hp'.1
    rw [hm]
    constructor
    · intro m hm'
      obtain ⟨y, hy, hye, hms⟩ := hC m hm'
      have hy2 : y ∈ sortByStart intervals := by
        rw [hsort]
        exact hy
      have hyI : y ∈ intervals :=
        (sortByStart_perm intervals).mem_iff.mp hy2
      refine ⟨y, hyI, ⟨hms, ?_⟩⟩
      rw [hye]
      exact Nat.le_refl _
    · intro a ha b hb hne
      exact pairwise_disjoint hA ha hb hne

end AxiomCode
