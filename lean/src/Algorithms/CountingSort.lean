import Spec
import Tactics
import Algorithms.InsertionSort
import Algorithms.QuickSort

/-!
# AxiomCode — Verified Counting Sort

A formally verified counting sort: the output is the input grouped by
value, proved a permutation of the input and pairwise sorted, and
proved equal to the core sort.

Promoted from `lean/drafts/countingsort_correctness.lean` under the L2
promotion procedure (`lean/PROMOTION.md`). The draft is a shell: a
fieldless `CountingSortInput`, a body-less `countingSort`, and the
statement `countingSort input = input.arr.sort` over a `.sort` that
does not exist in Lean core. Authored for real here: the input gains
its `arr` field, and counting sort is the bounded grouping
`countingSortUpTo` — for each value `v` below the bound, `List.count v l`
copies of `v` — run at bound `max + 1`.

The draft's claim is carried in repaired notation, recorded not silent:
core's sort is `List.mergeSort`, applied list-first, so the statement
reads `countingSort input = input.arr.mergeSort (· ≤ ·)`. It is proved
through the two halves separately (`SortSpec`: sorted and a
permutation) plus the uniqueness of sorted permutations
(`pairwise_perm_eq`). The `Sorted` ↔ `Pairwise` bridge is imported from
`Algorithms.InsertionSort`; the append/cons permutation step is
`Algorithms.QuickSort`'s `append_cons_perm` — both reused, not
duplicated, as the constants already live in this namespace.
-/

namespace AxiomCode

/-- Input for counting sort: a list of natural numbers. -/
structure CountingSortInput where
  arr : List Nat
deriving DecidableEq, Repr

/-- Counting sort bounded by `b`: the elements of `l` that are `< b`,
grouped by value — for each `v < b`, `List.count v l` copies of `v`,
in increasing order of `v`. -/
def countingSortUpTo : Nat → List Nat → List Nat
  | 0, _ => []
  | b + 1, l => countingSortUpTo b l ++ List.replicate (List.count b l) b

theorem countingSortUpTo_zero (l : List Nat) : countingSortUpTo 0 l = [] := rfl

theorem countingSortUpTo_succ (b : Nat) (l : List Nat) :
    countingSortUpTo (b + 1) l =
      countingSortUpTo b l ++ List.replicate (List.count b l) b := rfl

/-- Counting sort: group every element of `l` by value, using
`max + 1` as the bound (every element is `≤ max`). -/
def countingSortList (l : List Nat) : List Nat :=
  countingSortUpTo (l.foldr max 0 + 1) l

/-- Counting sort on the input structure (the draft's signature). -/
def countingSort (input : CountingSortInput) : List Nat :=
  countingSortList input.arr

-- The elements `≥ b` of `l` split off exactly the elements `= b`:
-- filter (b ≤ ·) l is, as a permutation, the `b`-block followed by
-- the elements `≥ b + 1`.
theorem filter_split_perm (b : Nat) (l : List Nat) :
    List.Perm (List.replicate (List.count b l) b ++ l.filter (fun x => b + 1 ≤ x))
      (l.filter (fun x => b ≤ x)) := by
  induction l with
  | nil => simp
  | cons x xs ih =>
    by_cases hxb : x = b
    · rw [hxb]
      have hc : List.count b (b :: xs) = List.count b xs + 1 := by
        rw [List.count_cons, ite_eq_left (by simp : (b == b) = true)]
      have hf1 : (b :: xs).filter (fun x => b + 1 ≤ x) =
          xs.filter (fun x => b + 1 ≤ x) := by
        rw [List.filter_cons,
          ite_eq_right (by simp only [decide_eq_true_eq]; omega :
            ¬ decide (b + 1 ≤ b) = true)]
      have hf2 : (b :: xs).filter (fun x => b ≤ x) =
          b :: xs.filter (fun x => b ≤ x) := by
        rw [List.filter_cons,
          ite_eq_left (by simp only [decide_eq_true_eq]; omega :
            decide (b ≤ b) = true)]
      rw [hc, List.replicate_succ, hf1, hf2, List.cons_append]
      exact List.Perm.cons b ih
    · have hc : List.count b (x :: xs) = List.count b xs := by
        rw [List.count_cons,
          ite_eq_right (by simpa [beq_iff_eq] using hxb : ¬ (x == b) = true),
          Nat.add_zero]
      by_cases hlt : x < b
      · have hf1 : (x :: xs).filter (fun x => b + 1 ≤ x) =
            xs.filter (fun x => b + 1 ≤ x) := by
          rw [List.filter_cons,
            ite_eq_right (by simp only [decide_eq_true_eq]; omega :
              ¬ decide (b + 1 ≤ x) = true)]
        have hf2 : (x :: xs).filter (fun x => b ≤ x) =
            xs.filter (fun x => b ≤ x) := by
          rw [List.filter_cons,
            ite_eq_right (by simp only [decide_eq_true_eq]; omega :
              ¬ decide (b ≤ x) = true)]
        rw [hc, hf1, hf2]
        exact ih
      · have hf1 : (x :: xs).filter (fun x => b + 1 ≤ x) =
            x :: xs.filter (fun x => b + 1 ≤ x) := by
          rw [List.filter_cons,
            ite_eq_left (by simp only [decide_eq_true_eq]; omega :
              decide (b + 1 ≤ x) = true)]
        have hf2 : (x :: xs).filter (fun x => b ≤ x) =
            x :: xs.filter (fun x => b ≤ x) := by
          rw [List.filter_cons,
            ite_eq_left (by simp only [decide_eq_true_eq]; omega :
              decide (b ≤ x) = true)]
        rw [hc, hf1, hf2]
        exact (append_cons_perm x _ _).trans (List.Perm.cons x ih)

theorem countingSortUpTo_perm (b : Nat) (l : List Nat) :
    List.Perm (countingSortUpTo b l ++ l.filter (fun x => b ≤ x)) l := by
  induction b generalizing l with
  | zero =>
    have hf : l.filter (fun x => 0 ≤ x) = l :=
      List.filter_eq_self.mpr (fun a _ => by
        simp only [decide_eq_true_eq]; exact Nat.zero_le a)
    rw [countingSortUpTo_zero, List.nil_append, hf]
  | succ b ih =>
    rw [countingSortUpTo_succ, List.append_assoc]
    exact (List.Perm.append_left _ (filter_split_perm b l)).trans (ih l)

theorem mem_le_foldr_max (l : List Nat) (x : Nat) (hx : x ∈ l) :
    x ≤ l.foldr max 0 := by
  induction l with
  | nil => simp at hx
  | cons a as ih =>
    simp only [List.foldr_cons]
    cases List.mem_cons.mp hx with
    | inl h => rw [h]; exact Nat.le_max_left a _
    | inr h => exact Nat.le_trans (ih h) (Nat.le_max_right a _)

theorem countingSortList_perm (l : List Nat) :
    List.Perm (countingSortList l) l := by
  have hf : l.filter (fun x => l.foldr max 0 + 1 ≤ x) = [] := by
    rw [List.filter_eq_nil_iff]
    intro a ha
    have h2 := mem_le_foldr_max l a ha
    simp only [decide_eq_true_eq]
    omega
  have h := countingSortUpTo_perm (l.foldr max 0 + 1) l
  rw [hf, List.append_nil] at h
  exact h

theorem countingSortUpTo_pairwise (b : Nat) (l : List Nat) :
    List.Pairwise (· ≤ ·) (countingSortUpTo b l) ∧
    ∀ x ∈ countingSortUpTo b l, x < b := by
  induction b generalizing l with
  | zero =>
    rw [countingSortUpTo_zero]
    exact ⟨List.Pairwise.nil, fun x hx => by simp at hx⟩
  | succ b ih =>
    obtain ⟨ihp, ihb⟩ := ih l
    rw [countingSortUpTo_succ, List.pairwise_append]
    refine ⟨⟨ihp, ?_, ?_⟩, ?_⟩
    · rw [List.pairwise_replicate]
      exact Or.inr (Nat.le_refl b)
    · intro x hx y hy
      have hxb : x < b := ihb x hx
      have hyb : y = b := (List.mem_replicate.mp hy).2
      omega
    · intro x hx
      rw [List.mem_append] at hx
      cases hx with
      | inl hx => have h3 := ihb x hx; omega
      | inr hx => have h3 : x = b := (List.mem_replicate.mp hx).2; omega

theorem countingSortList_sorted (l : List Nat) : Sorted (countingSortList l) :=
  pairwise_sorted (countingSortUpTo_pairwise _ l).1

/-- Two pairwise-sorted permutations of each other are equal
(sorted permutations are unique). -/
theorem pairwise_perm_eq {a b : List Nat}
    (ha : List.Pairwise (· ≤ ·) a) (hb : List.Pairwise (· ≤ ·) b)
    (hp : List.Perm a b) : a = b := by
  induction a generalizing b with
  | nil => exact (List.perm_nil.mp hp.symm).symm
  | cons x xs ih =>
    cases b with
    | nil => cases List.perm_nil.mp hp
    | cons y ys =>
      rw [List.pairwise_cons] at ha hb
      obtain ⟨hax, haxs⟩ := ha
      obtain ⟨hby, hbys⟩ := hb
      have hxmem : x ∈ y :: ys := hp.mem_iff.mp (List.Mem.head xs)
      have hymem : y ∈ x :: xs := hp.mem_iff.mpr (List.Mem.head ys)
      have hxy : x = y := by
        cases List.mem_cons.mp hxmem with
        | inl h => exact h
        | inr hx' =>
          cases List.mem_cons.mp hymem with
          | inl h => exact h.symm
          | inr hy' => exact Nat.le_antisymm (hax y hy') (hby x hx')
      subst hxy
      have hperm : List.Perm xs ys := List.Perm.cons_inv hp
      rw [ih haxs hbys hperm]

theorem mergeSort_pairwise (l : List Nat) :
    List.Pairwise (· ≤ ·) (l.mergeSort (· ≤ ·)) := by
  have h := List.pairwise_mergeSort (le := fun a b => decide (a ≤ b))
    (by
      intro a b c hab hbc
      simp only [decide_eq_true_eq] at hab hbc ⊢
      omega)
    (by
      intro a b
      simp only [Bool.or_eq_true, decide_eq_true_eq]
      exact Nat.le_total a b)
    l
  exact List.Pairwise.imp (fun h => of_decide_eq_true h) h

/-- Library-standard correctness: counting sort meets `SortSpec`. -/
theorem countingSortList_correct (l : List Nat) : SortSpec countingSortList :=
  fun l => ⟨countingSortList_sorted l, (countingSortList_perm l).symm⟩

/-- The draft's statement, with `.sort` repaired to the core sort
`List.mergeSort (· ≤ ·)` (Lean core has no `List.sort`): counting sort
computes the sorted list. -/
theorem countingSort_correctness (input : CountingSortInput) :
    countingSort input = input.arr.mergeSort (· ≤ ·) :=
  pairwise_perm_eq (countingSortUpTo_pairwise _ _).1 (mergeSort_pairwise _)
    ((countingSortList_perm _).trans (List.mergeSort_perm _ _).symm)

end AxiomCode
