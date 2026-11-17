import Spec
import Tactics
import Algorithms.InsertionSort

/-!
# AxiomCode — Verified Bubble Sort

Promoted from `lean/drafts/bubblesort_correctness.lean` under the L2
promotion procedure (`lean/PROMOTION.md`). Authored and proved by Arjun
(Item 4B, own-hands track).

Statement-honesty record. The draft was a shell: a fieldless `Array`
structure, a body-less `bubbleSort`, and the statement
`∀ arr, bubbleSort arr = arr` — the claim that sorting returns its input
UNCHANGED. That statement is false of every real bubble sort (on
`[2, 1]` a bubble sort returns `[1, 2] ≠ [2, 1]`); it could only ever
have been "proved" of the undefined shell. The library form of a sorting
entry's correctness is Spec's `SortSpec` (output sorted, and a
permutation of the input), stated and proved here as
`bubbleSort_correct`. The algorithm is authored over `List Nat`, the
library's element shape: one pass (`bubblePass`) parks the maximum at
the end of the list; `bubbleSort` recurses on the rest.
-/

namespace AxiomCode

/-- One bubble pass, carried-element form: `bubblePassFrom x l` bubbles the
larger of the carried element and each head onward. -/
def bubblePassFrom (x : Nat) : List Nat → List Nat
  | [] => [x]
  | y :: ys => if x ≤ y then x :: bubblePassFrom y ys else y :: bubblePassFrom x ys

/-- One full bubble pass over a list. -/
def bubblePass : List Nat → List Nat
  | [] => []
  | x :: xs => bubblePassFrom x xs

theorem bubblePassFrom_ne_nil (x : Nat) (l : List Nat) : bubblePassFrom x l ≠ [] := by
  cases l with
  | nil => simp [bubblePassFrom]
  | cons y ys =>
    by_cases h : x ≤ y <;> simp [bubblePassFrom, h]

theorem bubblePass_ne_nil {x : Nat} {xs : List Nat} :
    bubblePass (x :: xs) ≠ [] :=
  bubblePassFrom_ne_nil x xs

/-- A pass only rearranges: the carried form is a permutation of `x :: l`. -/
theorem bubblePassFrom_perm (x : Nat) (l : List Nat) :
    List.Perm (bubblePassFrom x l) (x :: l) := by
  induction l generalizing x with
  | nil => simp [bubblePassFrom]
  | cons y ys ih =>
    by_cases h : x ≤ y
    · simp only [bubblePassFrom, h, ite_true]
      exact List.Perm.cons x (ih (x := y))
    · simp only [bubblePassFrom, h, ite_false]
      exact (List.Perm.cons y (ih (x := x))).trans (List.Perm.swap x y ys)

theorem bubblePass_perm (l : List Nat) : List.Perm (bubblePass l) l := by
  cases l with
  | nil => simp [bubblePass]
  | cons x xs => exact bubblePassFrom_perm x xs

theorem bubblePass_length (l : List Nat) : (bubblePass l).length = l.length := by
  exact (bubblePass_perm l).length_eq

/-- Every element of a pass is at most the pass's last element: one pass parks
the maximum at the end. Stated via `getLast?` (the dependent `getLast` form
fights the induction); converted back where needed. -/
theorem bubblePassFrom_le (x : Nat) (l : List Nat) :
    ∀ z ∈ bubblePassFrom x l, ∀ m, (bubblePassFrom x l).getLast? = some m → z ≤ m := by
  induction l generalizing x with
  | nil =>
    intro z hz m hm
    simp only [bubblePassFrom, List.mem_singleton] at hz
    simp only [bubblePassFrom, List.getLast?_singleton] at hm
    have hxm : x = m := Option.some.inj hm
    omega
  | cons y ys ih =>
    intro z hz m hm
    by_cases h : x ≤ y
    · obtain ⟨b, bs, hb⟩ := List.exists_cons_of_ne_nil (bubblePassFrom_ne_nil y ys)
      have hm' : (bubblePassFrom y ys).getLast? = some m := by
        have h1 : (x :: bubblePassFrom y ys).getLast? = some m := by
          simpa only [bubblePassFrom, h, ite_true] using hm
        rw [hb] at h1 ⊢
        rwa [List.getLast?_cons_cons] at h1
      have hym : y ≤ m :=
        ih (x := y) y ((bubblePassFrom_perm y ys).mem_iff.mpr (List.mem_cons_self)) m hm'
      simp only [bubblePassFrom, h, ite_true, List.mem_cons] at hz
      rcases hz with rfl | hz'
      · exact Nat.le_trans h hym
      · exact ih (x := y) z hz' m hm'
    · obtain ⟨b, bs, hb⟩ := List.exists_cons_of_ne_nil (bubblePassFrom_ne_nil x ys)
      have hm' : (bubblePassFrom x ys).getLast? = some m := by
        have h1 : (y :: bubblePassFrom x ys).getLast? = some m := by
          simpa only [bubblePassFrom, h, ite_false] using hm
        rw [hb] at h1 ⊢
        rwa [List.getLast?_cons_cons] at h1
      have hxm : x ≤ m :=
        ih (x := x) x ((bubblePassFrom_perm x ys).mem_iff.mpr (List.mem_cons_self)) m hm'
      simp only [bubblePassFrom, h, ite_false, List.mem_cons] at hz
      rcases hz with rfl | hz'
      · exact Nat.le_trans (Nat.le_of_lt (Nat.lt_of_not_le h)) hxm
      · exact ih (x := x) z hz' m hm'

theorem bubblePass_le_getLast (l : List Nat) (hl : l ≠ []) :
    ∀ z ∈ bubblePass l, z ≤ (bubblePass l).getLast (by
      cases l with
      | nil => simp at hl
      | cons x xs => exact bubblePass_ne_nil) := by
  cases l with
  | nil => simp at hl
  | cons x xs =>
    intro z hz
    have hm : (bubblePass (x :: xs)).getLast? =
        some ((bubblePass (x :: xs)).getLast bubblePass_ne_nil) :=
      List.getLast?_eq_some_getLast bubblePass_ne_nil
    exact bubblePassFrom_le x xs z hz _ hm

/-- Bubble sort: pass, park the maximum, recurse on the rest. -/
def bubbleSort : List Nat → List Nat
  | [] => []
  | x :: xs =>
    let p := bubblePass (x :: xs)
    bubbleSort p.dropLast ++ [p.getLast bubblePass_ne_nil]
  termination_by l => l.length
  decreasing_by
    have hlen : (bubblePass (x :: xs)).length = (x :: xs).length :=
      bubblePass_length _
    simp [List.length_dropLast, hlen]

/-- Bubble sort only rearranges its input. (Bounded strong induction on the
length — the house form, per Gcd: `Nat.strong_induction_on` does not exist in
this toolchain's core.) -/
theorem bubbleSort_perm (l : List Nat) : List.Perm l (bubbleSort l) := by
  have key : ∀ k, ∀ l, l.length < k → List.Perm l (bubbleSort l) := by
    intro k
    induction k with
    | zero => intro l hl; exact absurd hl (Nat.not_lt_zero _)
    | succ k ih =>
      intro l hl
      cases l with
      | nil =>
        have hnil : bubbleSort ([] : List Nat) = [] := by simp only [bubbleSort]
        rw [hnil]
      | cons x xs =>
        have hne : bubblePass (x :: xs) ≠ [] := bubblePass_ne_nil
        have hlt : (bubblePass (x :: xs)).dropLast.length < k := by
          have e1 : (bubblePass (x :: xs)).length = (x :: xs).length :=
            bubblePass_length _
          have e2 : (bubblePass (x :: xs)).dropLast.length =
              (bubblePass (x :: xs)).length - 1 := List.length_dropLast
          have e3 : (x :: xs).length = xs.length + 1 := rfl
          omega
        have ih' := ih _ hlt
        have hsplit : (bubblePass (x :: xs)).dropLast ++
            [(bubblePass (x :: xs)).getLast hne] = bubblePass (x :: xs) :=
          List.dropLast_concat_getLast hne
        have h1 : List.Perm (x :: xs) (bubblePass (x :: xs)) :=
          (bubblePass_perm _).symm
        have h2 : List.Perm (bubblePass (x :: xs))
            ((bubblePass (x :: xs)).dropLast ++
              [(bubblePass (x :: xs)).getLast hne]) := by
          rw [hsplit]
        have h3 : List.Perm ((bubblePass (x :: xs)).dropLast ++
              [(bubblePass (x :: xs)).getLast hne])
            (bubbleSort (bubblePass (x :: xs)).dropLast ++
              [(bubblePass (x :: xs)).getLast hne]) :=
          List.Perm.append ih' (List.Perm.refl _)
        have h4 : bubbleSort (x :: xs) =
            bubbleSort (bubblePass (x :: xs)).dropLast ++
              [(bubblePass (x :: xs)).getLast hne] := by
          simp only [bubbleSort]
        exact h4 ▸ (h1.trans (h2.trans h3))
  exact key (l.length + 1) l (Nat.lt_succ_self _)

/-- Bubble sort's output is pairwise sorted. Together with the bridge
(`pairwise_sorted`, already in the library via InsertionSort) this gives
`Sorted (bubbleSort l)`. -/
theorem bubbleSort_pairwise (l : List Nat) :
    List.Pairwise (· ≤ ·) (bubbleSort l) := by
  have key : ∀ k, ∀ l, l.length < k → List.Pairwise (· ≤ ·) (bubbleSort l) := by
    intro k
    induction k with
    | zero => intro l hl; exact absurd hl (Nat.not_lt_zero _)
    | succ k ih =>
      intro l hl
      cases l with
      | nil =>
        have hnil : bubbleSort ([] : List Nat) = [] := by simp only [bubbleSort]
        rw [hnil]; exact List.Pairwise.nil
      | cons x xs =>
        have hne : bubblePass (x :: xs) ≠ [] := bubblePass_ne_nil
        have hlt : (bubblePass (x :: xs)).dropLast.length < k := by
          have e1 : (bubblePass (x :: xs)).length = (x :: xs).length :=
            bubblePass_length _
          have e2 : (bubblePass (x :: xs)).dropLast.length =
              (bubblePass (x :: xs)).length - 1 := List.length_dropLast
          have e3 : (x :: xs).length = xs.length + 1 := rfl
          omega
        have ih' := ih _ hlt
        have h4 : bubbleSort (x :: xs) =
            bubbleSort (bubblePass (x :: xs)).dropLast ++
              [(bubblePass (x :: xs)).getLast hne] := by
          simp only [bubbleSort]
        rw [h4]
        apply List.pairwise_append.mpr
        refine ⟨ih', List.pairwise_singleton _ _, ?_⟩
        intro a ha b hb
        simp only [List.mem_singleton] at hb
        have ha1 : a ∈ (bubblePass (x :: xs)).dropLast :=
          (bubbleSort_perm (bubblePass (x :: xs)).dropLast).symm.mem_iff.mp ha
        have ha2 : a ∈ bubblePass (x :: xs) := List.dropLast_subset _ ha1
        have hle := bubblePass_le_getLast (x :: xs) (by simp) a ha2
        exact hb.symm ▸ hle
  exact key (l.length + 1) l (Nat.lt_succ_self _)

/-- Bubble sort meets Spec's sorting specification: the output is sorted
and a permutation of the input. (Sortedness rides the library's
`Sorted ↔ Pairwise` bridge from `Algorithms.InsertionSort`.) -/
theorem bubbleSort_correct : SortSpec bubbleSort := fun l =>
  ⟨pairwise_sorted (bubbleSort_pairwise l), bubbleSort_perm l⟩

end AxiomCode
