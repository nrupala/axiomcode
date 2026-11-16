import Spec
import Tactics

/-!
# AxiomCode — Verified Insertion Sort

A formally verified insertion sort implementation with correctness proof.

Promoted from `lean/drafts/insertion_sort.lean` under the L2 promotion
procedure (`lean/PROMOTION.md`). The draft's three statements are proved
exactly as stated; the draft's stale imports (`AxiomCode.Spec`,
`AxiomCode.Tactics`) are corrected to the lakefile's module names.
-/

namespace AxiomCode

/-- Insert an element into a sorted list while maintaining sorted order. -/
def insert (x : Nat) : List Nat → List Nat
  | [] => [x]
  | y :: ys =>
    if x ≤ y then x :: y :: ys
    else y :: insert x ys

/-- Insertion sort: recursively sort the tail, then insert the head. -/
def insertionSort : List Nat → List Nat
  | [] => []
  | x :: xs => insert x (insertionSort xs)

-- Equation lemmas for `insert` (bulletproof unfolding via defeq `show`).
theorem insert_nil (x : Nat) : insert x [] = [x] := rfl

theorem insert_cons_le {x y : Nat} {ys : List Nat} (h : x ≤ y) :
    insert x (y :: ys) = x :: y :: ys := by
  show (if x ≤ y then x :: y :: ys else y :: insert x ys) = x :: y :: ys
  rw [ite_eq_left h]

theorem insert_cons_gt {x y : Nat} {ys : List Nat} (h : ¬ x ≤ y) :
    insert x (y :: ys) = y :: insert x ys := by
  show (if x ≤ y then x :: y :: ys else y :: insert x ys) = y :: insert x ys
  rw [ite_eq_right h]

theorem insertionSort_nil : insertionSort [] = [] := rfl

theorem insertionSort_cons (x : Nat) (xs : List Nat) :
    insertionSort (x :: xs) = insert x (insertionSort xs) := rfl

-- Bridge helpers: getI membership, both directions.
theorem getI_mem (l : List Nat) (i : Nat) (h : i < l.length) : l[i]! ∈ l := by
  induction l generalizing i with
  | nil => exact absurd h (Nat.not_lt_zero i)
  | cons a l ih =>
    cases i with
    | zero => exact List.Mem.head l
    | succ i =>
      have h' : i < l.length := by
        have hl : (a :: l).length = l.length + 1 := rfl
        omega
      exact List.Mem.tail a (ih i h')

theorem mem_getI (l : List Nat) (a : Nat) (h : a ∈ l) :
    ∃ i, i < l.length ∧ l[i]! = a := by
  induction l with
  | nil => exact absurd h (by simp)
  | cons b l ih =>
    cases h with
    | head l => exact ⟨0, by simp, rfl⟩
    | tail b hm =>
      obtain ⟨i, hi, hia⟩ := ih hm
      refine ⟨i + 1, ?_, hia⟩
      rw [List.length_cons]; omega

-- Bridge: Spec.Sorted ↔ List.Pairwise (· ≤ ·).
theorem sorted_pairwise {l : List Nat} (hS : Sorted l) : List.Pairwise (· ≤ ·) l := by
  induction l with
  | nil => exact List.Pairwise.nil
  | cons a l ih =>
    rw [List.pairwise_cons]
    constructor
    · intro a' ha'
      obtain ⟨i, hi, hia⟩ := mem_getI l a' ha'
      have h := hS 0 (i + 1) (by omega) (by rw [List.length_cons]; omega)
      have h2 : a ≤ l[i]! := h
      rw [hia] at h2
      exact h2
    · apply ih
      intro i j hij hj
      exact hS (i + 1) (j + 1) (by omega) (by rw [List.length_cons]; omega)

theorem pairwise_sorted {l : List Nat} (hP : List.Pairwise (· ≤ ·) l) : Sorted l := by
  induction l with
  | nil =>
    intro i j _ hj
    simp at hj
  | cons a l ih =>
    rw [List.pairwise_cons] at hP
    obtain ⟨hrel, htail⟩ := hP
    intro i j hij hj
    cases i with
    | zero =>
      cases j with
      | zero => exact absurd hij (by simp)
      | succ j =>
        have hj' : j < l.length := by
          have hl : (a :: l).length = l.length + 1 := rfl
          omega
        exact hrel _ (getI_mem l j hj')
    | succ i =>
      cases j with
      | zero => exact absurd hij (by simp)
      | succ j =>
        have hj' : j < l.length := by
          have hl : (a :: l).length = l.length + 1 := rfl
          omega
        exact ih htail i j (by omega) hj'

-- insert preserves permutation and pairwise-sortedness.
theorem insert_perm (x : Nat) (ys : List Nat) : List.Perm (insert x ys) (x :: ys) := by
  induction ys with
  | nil => rw [insert_nil]
  | cons y ys ih =>
    by_cases h : x ≤ y
    · rw [insert_cons_le h]
    · rw [insert_cons_gt h]
      exact (List.Perm.cons y ih).trans (List.Perm.swap x y ys)

theorem insert_pairwise {x : Nat} {ys : List Nat}
    (hP : List.Pairwise (· ≤ ·) ys) : List.Pairwise (· ≤ ·) (insert x ys) := by
  induction ys with
  | nil =>
    rw [insert_nil]
    exact List.Pairwise.cons (by simp) List.Pairwise.nil
  | cons y ys ih =>
    rw [List.pairwise_cons] at hP
    obtain ⟨hrel, htail⟩ := hP
    by_cases h : x ≤ y
    · rw [insert_cons_le h, List.pairwise_cons]
      constructor
      · intro a' ha'
        cases ha' with
        | head ys => exact h
        | tail y hm => exact Nat.le_trans h (hrel a' hm)
      · exact List.Pairwise.cons hrel htail
    · rw [insert_cons_gt h, List.pairwise_cons]
      constructor
      · intro a' ha'
        have ha'' : a' ∈ x :: ys := (insert_perm x ys).mem_iff.mp ha'
        cases ha'' with
        | head ys => omega
        | tail x hm => exact hrel a' hm
      · exact ih htail

/-- Theorem: insertion sort produces a sorted list. -/
theorem insertionSort_sorted (l : List Nat) :
    Sorted (insertionSort l) := by
  induction l with
  | nil =>
    rw [insertionSort_nil]
    intro i j _ hj
    simp at hj
  | cons x xs ih =>
    rw [insertionSort_cons]
    exact pairwise_sorted (insert_pairwise (sorted_pairwise ih))

/-- Theorem: insertion sort preserves elements (permutation). -/
theorem insertionSort_perm (l : List Nat) :
    List.Perm l (insertionSort l) := by
  induction l with
  | nil => rw [insertionSort_nil]
  | cons x xs ih =>
    rw [insertionSort_cons]
    exact ((List.Perm.cons x ih)).trans (insert_perm x (insertionSort xs)).symm

/-- Full correctness: insertion sort is a valid sorting function. -/
theorem insertionSort_correct (l : List Nat) :
    SortSpec insertionSort := by
  intro l'
  exact ⟨insertionSort_sorted l', insertionSort_perm l'⟩

/-- Export for C compilation. -/
@[export insertionSort_c]
def insertionSort_c (l : List Nat) : List Nat :=
  insertionSort l

end AxiomCode
