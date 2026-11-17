import Spec
import Tactics
import Algorithms.InsertionSort

/-!
# AxiomCode — Verified Quicksort

A formally verified quicksort: permutation and sortedness, the draft's
statement, and the library-standard `SortSpec`.

Promoted from `lean/drafts/quicksort_correctness.lean` under the L2
promotion procedure (`lean/PROMOTION.md`). The draft is a shell: a
fieldless `Array` structure, body-less `get`/`set`/`quicksort`, and a
statement over an undefined `sorted`. Authored for real here: quicksort
on lists (pivot on the head, recurse on the two filter partitions of the
tail), with `sorted` read as the library's `Spec.Sorted`.

Two authoring decisions the shells force, recorded not silent:

* **Element type.** The draft works over `List Int`; the library's `Spec`
  predicates are `Nat`-typed, so the entry is authored over `List Nat`
  (the same specialisation the counting/radix drafts already have).
* **The draft's membership half is one direction of `Perm`.** The
  draft's statement — sorted, and every input element occurs in the
  output — is proved exactly in that shape (`quicksort_correctness`);
  the full permutation (`quicksort_perm`) and the library-standard
  `SortSpec` statement (`quicksort_correct`) are proved alongside it.

The `Sorted` ↔ `Pairwise` bridge is the one proved in
`Algorithms.InsertionSort` (`sorted_pairwise`, `pairwise_sorted`),
imported and reused — the bridge constants already live in this
namespace and are not duplicated.
-/

namespace AxiomCode

/-- Quicksort: pivot on the head, recurse on the strictly-smaller and the
not-smaller elements of the tail. -/
def quicksort : List Nat → List Nat
  | [] => []
  | x :: xs => quicksort (xs.filter (· < x)) ++ [x] ++
      quicksort (xs.filter (fun y => ¬ y < x))
termination_by l => l.length
decreasing_by
  all_goals
    simp only [List.length_cons, List.length_unattach]
    refine Nat.lt_succ_of_le ?_
    calc (List.filter _ xs.attach).length
        ≤ xs.attach.length := List.length_filter_le _ _
      _ = xs.length := List.length_attach

theorem quicksort_nil : quicksort [] = [] := by
  rw [quicksort]

theorem quicksort_cons (x : Nat) (xs : List Nat) :
    quicksort (x :: xs) = quicksort (xs.filter (· < x)) ++ [x] ++
      quicksort (xs.filter (fun y => ¬ y < x)) := by
  rw [quicksort]

-- The two filters partition the list (as a permutation).
theorem append_cons_perm (x : Nat) (a b : List Nat) :
    List.Perm (a ++ x :: b) (x :: (a ++ b)) := by
  induction a with
  | nil => exact List.Perm.refl _
  | cons y ys ih =>
    simp only [List.cons_append]
    exact (List.Perm.cons y ih).trans (List.Perm.swap x y (ys ++ b))

theorem filter_partition_perm (p : Nat → Bool) (l : List Nat) :
    List.Perm (l.filter p ++ l.filter (fun a => !p a)) l := by
  induction l with
  | nil => simp
  | cons x xs ih =>
    rw [List.filter_cons, List.filter_cons]
    by_cases h : p x = true
    · have h2 : (fun a => !p a) x = false := by simp [h]
      rw [ite_eq_left h, ite_eq_right (by simp [h2] : ¬ (fun a => !p a) x = true)]
      simp only [List.cons_append]
      exact List.Perm.cons x ih
    · have hf : p x = false := by
        cases hpx : p x with
        | true => exact absurd hpx h
        | false => rfl
      have h2 : (fun a => !p a) x = true := by simp [hf]
      rw [ite_eq_right h, ite_eq_left h2]
      exact (append_cons_perm x _ _).trans (List.Perm.cons x ih)

theorem quicksort_perm (l : List Nat) : List.Perm (quicksort l) l := by
  have key : ∀ n (l : List Nat), l.length < n → List.Perm (quicksort l) l := by
    intro n
    induction n with
    | zero => intro l hl; simp at hl
    | succ n ih =>
      intro l hl
      cases l with
      | nil => rw [quicksort_nil]
      | cons x xs =>
        rw [quicksort_cons]
        have hlen : xs.length < n := by
          simp only [List.length_cons] at hl; omega
        have h1 : (xs.filter (· < x)).length < n :=
          Nat.lt_of_le_of_lt (List.length_filter_le _ xs) hlen
        have h2 : (xs.filter (fun y => ¬ y < x)).length < n :=
          Nat.lt_of_le_of_lt (List.length_filter_le _ xs) hlen
        have step1 : List.Perm
            (quicksort (xs.filter (· < x)) ++ [x] ++
              quicksort (xs.filter (fun y => ¬ y < x)))
            ((xs.filter (· < x)) ++ [x] ++ (xs.filter (fun y => ¬ y < x))) :=
          List.Perm.append (List.Perm.append (ih _ h1) (List.Perm.refl [x])) (ih _ h2)
        have step2 : List.Perm
            ((xs.filter (· < x)) ++ [x] ++ (xs.filter (fun y => ¬ y < x)))
            (x :: (xs.filter (· < x) ++ xs.filter (fun y => ¬ y < x))) := by
          rw [List.append_assoc]
          exact append_cons_perm x _ _
        have step3 : List.Perm
            (x :: (xs.filter (· < x) ++ xs.filter (fun y => ¬ y < x)))
            (x :: xs) :=
          List.Perm.cons x (filter_partition_perm _ xs)
        exact step1.trans (step2.trans step3)
  exact key (l.length + 1) l (Nat.lt_succ_self _)

theorem quicksort_pairwise (l : List Nat) : List.Pairwise (· ≤ ·) (quicksort l) := by
  have key : ∀ n (l : List Nat), l.length < n →
      List.Pairwise (· ≤ ·) (quicksort l) := by
    intro n
    induction n with
    | zero => intro l hl; simp at hl
    | succ n ih =>
      intro l hl
      cases l with
      | nil => rw [quicksort_nil]; exact List.Pairwise.nil
      | cons x xs =>
        rw [quicksort_cons]
        have hlen : xs.length < n := by
          simp only [List.length_cons] at hl; omega
        have h1 : (xs.filter (· < x)).length < n :=
          Nat.lt_of_le_of_lt (List.length_filter_le _ xs) hlen
        have h2 : (xs.filter (fun y => ¬ y < x)).length < n :=
          Nat.lt_of_le_of_lt (List.length_filter_le _ xs) hlen
        have ih1 := ih _ h1
        have ih2 := ih _ h2
        rw [List.pairwise_append]
        refine ⟨?_, ih2, ?_⟩
        · rw [List.pairwise_append]
          refine ⟨ih1, List.pairwise_singleton _ _, ?_⟩
          intro a ha _ hb
          have ha2 : a ∈ xs.filter (· < x) := (quicksort_perm _).mem_iff.mp ha
          have hax : a < x := by
            have h3 := (List.mem_filter.mp ha2).2
            simpa using h3
          have hbx : _ = x := List.mem_singleton.mp hb
          rw [hbx]
          exact Nat.le_of_lt hax
        · intro a ha b hb
          have hb2 : b ∈ xs.filter (fun y => ¬ y < x) :=
            (quicksort_perm _).mem_iff.mp hb
          have hxb : x ≤ b := by
            have h3 := (List.mem_filter.mp hb2).2
            simpa using h3
          rw [List.mem_append] at ha
          cases ha with
          | inl ha =>
            have ha2 : a ∈ xs.filter (· < x) := (quicksort_perm _).mem_iff.mp ha
            have hax : a < x := by
              have h3 := (List.mem_filter.mp ha2).2
              simpa using h3
            exact Nat.le_trans (Nat.le_of_lt hax) hxb
          | inr ha =>
            have hax : a = x := List.mem_singleton.mp ha
            rw [hax]
            exact hxb
  exact key (l.length + 1) l (Nat.lt_succ_self _)

theorem quicksort_sorted (l : List Nat) : Sorted (quicksort l) :=
  pairwise_sorted (quicksort_pairwise l)

/-- The draft's statement (with `sorted` read as `Spec.Sorted`, over the
library's `Nat` element type). -/
theorem quicksort_correctness (arr : List Nat) :
    Sorted (quicksort arr) ∧ (∀ x ∈ arr, x ∈ quicksort arr) :=
  ⟨quicksort_sorted arr,
   fun x hx => (quicksort_perm arr).mem_iff.mpr hx⟩

/-- Full library-standard correctness: quicksort meets `SortSpec`. -/
theorem quicksort_correct (l : List Nat) : SortSpec quicksort :=
  fun l => ⟨quicksort_sorted l, (quicksort_perm l).symm⟩

end AxiomCode
