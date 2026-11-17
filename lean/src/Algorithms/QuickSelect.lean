import Spec
import Tactics
import Algorithms.InsertionSort
import Algorithms.QuickSort

/-!
# Quickselect — the `k`-th order statistic

The draft (`drafts/quickselect_correctness (input.lean`) did not
elaborate: `QuickselectInput` had no fields, `quickselect` had no
body, and the statement quantified over undefined `left`/`right`
sublists and a nonexistent `input.arr`. The draft's claim was:

> `quickselect input ∈ input.arr ∧
>   left.all (· ≤ quickselect input) ∧ right.all (· ≥ quickselect input)`

with `left`/`right` evidently the elements on either side of position
`k` in the sorted order — i.e. the result is the element that would
sit at index `k` of the sorted list.

Defect on record: the claim needs the hypothesis `k < arr.length`,
which the draft omits. Without it the claim is false for any
implementation: with `arr = [1]` and `k = 5` there is no 5th order
statistic; the junk value `0` this implementation returns satisfies
`0 ∉ [1]`, refuting the membership conjunct.

Repair (the draft's proposition shape, the LRU precedent): the
structure gains `arr` and `k`; the undefined `left`/`right` conjuncts
become the two counting facts that pin the result to position `k` —
at most `k` elements are strictly smaller (they occupy the positions
left of `k`), and more than `k` elements are `≤` the result (so
everything strictly larger sits to its right) — under the hypothesis
`input.k < input.arr.length`.

The definition recurses on an explicit fuel bound (the list's length
always suffices: each step drops the pivot and recurses on a filter),
in the house style of `Gcd.gcdRun`.
-/

namespace AxiomCode

/-- Input for quickselect: a list and an index `k` (0-based) into its
sorted order. -/
structure QuickselectInput where
  arr : List Nat
  k : Nat
deriving DecidableEq, Repr

/-- Quickselect with an explicit fuel bound. Returns the element that
would sit at index `k` in the sorted list, for `k` in range; `0`
(junk) out of range. -/
def quickselectBounded : Nat → List Nat → Nat → Nat
  | 0, _, _ => 0
  | _ + 1, [], _ => 0
  | n + 1, x :: xs, k =>
      if k < (xs.filter (· < x)).length then
        quickselectBounded n (xs.filter (· < x)) k
      else if k = (xs.filter (· < x)).length then x
      else
        quickselectBounded n (xs.filter (fun y => !(y < x)))
          (k - (xs.filter (· < x)).length - 1)

theorem quickselectBounded_succ_cons (n x : Nat) (xs : List Nat) (k : Nat) :
    quickselectBounded (n + 1) (x :: xs) k =
      if k < (xs.filter (· < x)).length then
        quickselectBounded n (xs.filter (· < x)) k
      else if k = (xs.filter (· < x)).length then x
      else
        quickselectBounded n (xs.filter (fun y => !(y < x)))
          (k - (xs.filter (· < x)).length - 1) := by
  rw [quickselectBounded]

/-- Quickselect on a list: fuel = the list's length. -/
def quickselectList (l : List Nat) (k : Nat) : Nat :=
  quickselectBounded l.length l k

/-- Quickselect on the input structure (the draft's signature). -/
def quickselect (input : QuickselectInput) : Nat :=
  quickselectList input.arr input.k

/-- The order-statistic specification, by induction on the fuel. The
pivot splits the tail into the elements below it (`filter_partition_perm`)
and both counting conjuncts are transported across the split. -/
theorem quickselectBounded_spec (n : Nat) (l : List Nat) (k : Nat)
    (hn : l.length ≤ n) (hk : k < l.length) :
    quickselectBounded n l k ∈ l ∧
    (l.filter (· < quickselectBounded n l k)).length ≤ k ∧
    k < (l.filter (· ≤ quickselectBounded n l k)).length := by
  induction n generalizing l k with
  | zero => omega
  | succ n ih =>
    cases l with
    | nil => exact (Nat.not_lt_zero k hk).elim
    | cons x xs =>
      rw [quickselectBounded_succ_cons]
      have hpart : List.Perm
          ((xs.filter (· < x)) ++ (xs.filter (fun y => !(y < x)))) xs :=
        filter_partition_perm _ xs
      have hlen_xs : xs.length =
          (xs.filter (· < x)).length + (xs.filter (fun y => !(y < x))).length := by
        have h2 := hpart.length_eq
        rw [List.length_append] at h2
        exact h2.symm
      have hxs_le : xs.length ≤ n := by
        have h3 : (x :: xs).length = xs.length + 1 := rfl
        omega
      have filter_length_split : ∀ q : Nat → Bool,
          (xs.filter q).length =
            ((xs.filter (· < x)).filter q).length +
              ((xs.filter (fun y => !(y < x))).filter q).length := by
        intro q
        have hp2 := (hpart.symm.filter q).length_eq
        rw [List.filter_append, List.length_append] at hp2
        exact hp2
      have mem_lo : ∀ y ∈ xs.filter (· < x), y < x :=
        fun y hy => of_decide_eq_true (List.mem_filter.mp hy).2
      have mem_hi : ∀ y ∈ xs.filter (fun y => !(y < x)), x ≤ y := by
        intro y hy
        have h2 := (List.mem_filter.mp hy).2
        have h3 : ¬ y < x := by simpa using h2
        omega
      have lo_filter_self : ∀ q : Nat → Bool,
          (∀ y ∈ xs.filter (· < x), q y = true) →
          ((xs.filter (· < x)).filter q) = xs.filter (· < x) :=
        fun q hq => List.filter_eq_self.mpr hq
      by_cases h1 : k < (xs.filter (· < x)).length
      · rw [ite_eq_left h1]
        have hlen_lo : (xs.filter (· < x)).length ≤ n :=
          Nat.le_trans (List.length_filter_le _ xs) hxs_le
        obtain ⟨hr_mem, hr_lo, hr_hi⟩ := ih _ _ hlen_lo h1
        refine ⟨List.Mem.tail x (List.mem_filter.mp hr_mem).1, ?_, ?_⟩
        · -- elements of (x :: xs) below r: x is not one (r < x)
          have hrx : (quickselectBounded n (xs.filter (· < x)) k) < x :=
            mem_lo _ hr_mem
          have e1 : ((x :: xs).filter (· < quickselectBounded n (xs.filter (· < x)) k))
              = xs.filter (· < quickselectBounded n (xs.filter (· < x)) k) := by
            rw [List.filter_cons,
              ite_eq_right (by simp only [decide_eq_true_eq]; omega :
                ¬ decide (x < quickselectBounded n (xs.filter (· < x)) k) = true)]
          rw [e1, filter_length_split]
          have e2 : ((xs.filter (fun y => !(y < x))).filter
              (· < quickselectBounded n (xs.filter (· < x)) k)) = [] := by
            rw [List.filter_eq_nil_iff]
            intro y hy
            have hyx : x ≤ y := mem_hi y hy
            simp only [decide_eq_true_eq]
            omega
          rw [e2, List.length_nil, Nat.add_zero]
          exact hr_lo
        · have hrx : quickselectBounded n (xs.filter (· < x)) k < x :=
            mem_lo _ hr_mem
          have e1 : ((x :: xs).filter (· ≤ quickselectBounded n (xs.filter (· < x)) k))
              = xs.filter (· ≤ quickselectBounded n (xs.filter (· < x)) k) := by
            rw [List.filter_cons,
              ite_eq_right (by simp only [decide_eq_true_eq]; omega :
                ¬ decide (x ≤ quickselectBounded n (xs.filter (· < x)) k) = true)]
          rw [e1, filter_length_split]
          omega
      · by_cases h2 : k = (xs.filter (· < x)).length
        · rw [ite_eq_right h1, ite_eq_left h2]
          refine ⟨List.Mem.head xs, ?_, ?_⟩
          · have e1 : ((x :: xs).filter (· < x)) = xs.filter (· < x) := by
              rw [List.filter_cons,
                ite_eq_right (by simp only [decide_eq_true_eq]; omega :
                  ¬ decide (x < x) = true)]
            rw [e1, filter_length_split]
            have e2 : ((xs.filter (· < x)).filter (· < x)) = xs.filter (· < x) :=
              lo_filter_self _ (fun y hy => (List.mem_filter.mp hy).2)
            have e3 : ((xs.filter (fun y => !(y < x))).filter (· < x)) = [] := by
              rw [List.filter_eq_nil_iff]
              intro y hy
              have hyx : x ≤ y := mem_hi y hy
              simp only [decide_eq_true_eq]
              omega
            rw [e2, e3, List.length_nil, Nat.add_zero]
            omega
          · have e1 : ((x :: xs).filter (· ≤ x)) =
                x :: xs.filter (· ≤ x) := by
              rw [List.filter_cons,
                ite_eq_left (by simp only [decide_eq_true_eq]; omega :
                  decide (x ≤ x) = true)]
            rw [e1, List.length_cons, filter_length_split]
            have e2 : ((xs.filter (· < x)).filter (· ≤ x)) = xs.filter (· < x) :=
              lo_filter_self _ (fun y hy => by
                have := mem_lo y hy
                simp only [decide_eq_true_eq]
                omega)
            rw [e2]
            omega
        · rw [ite_eq_right h1, ite_eq_right h2]
          have hlen_hi : (xs.filter (fun y => !(y < x))).length ≤ n :=
            Nat.le_trans (List.length_filter_le _ xs) hxs_le
          have hk' : k - (xs.filter (· < x)).length - 1 <
              (xs.filter (fun y => !(y < x))).length := by
            have h3 : (x :: xs).length = xs.length + 1 := rfl
            omega
          obtain ⟨hr_mem, hr_lo, hr_hi⟩ :=
            ih _ _ hlen_hi hk'
          have hrx : x ≤ quickselectBounded n (xs.filter (fun y => !(y < x)))
              (k - (xs.filter (· < x)).length - 1) := mem_hi _ hr_mem
          refine ⟨List.Mem.tail x (List.mem_filter.mp hr_mem).1, ?_, ?_⟩
          · have e1 : ((x :: xs).filter
                (· < quickselectBounded n (xs.filter (fun y => !(y < x)))
                  (k - (xs.filter (· < x)).length - 1))).length ≤
                (xs.filter
                  (· < quickselectBounded n (xs.filter (fun y => !(y < x)))
                    (k - (xs.filter (· < x)).length - 1))).length + 1 := by
              rw [List.filter_cons]
              by_cases hxr : x < quickselectBounded n
                  (xs.filter (fun y => !(y < x)))
                  (k - (xs.filter (· < x)).length - 1)
              · rw [ite_eq_left (by simp only [decide_eq_true_eq]; exact hxr :
                    decide (x < quickselectBounded n
                      (xs.filter (fun y => !(y < x)))
                      (k - (xs.filter (· < x)).length - 1)) = true),
                  List.length_cons]
                exact Nat.le_refl _
              · rw [ite_eq_right (by simp only [decide_eq_true_eq]; exact hxr :
                    ¬ decide (x < quickselectBounded n
                      (xs.filter (fun y => !(y < x)))
                      (k - (xs.filter (· < x)).length - 1)) = true)]
                omega
            refine Nat.le_trans e1 ?_
            rw [filter_length_split]
            have e2 : ((xs.filter (· < x)).filter
                (· < quickselectBounded n (xs.filter (fun y => !(y < x)))
                  (k - (xs.filter (· < x)).length - 1))) =
                xs.filter (· < x) :=
              lo_filter_self _ (fun y hy => by
                have hyx := mem_lo y hy
                simp only [decide_eq_true_eq]
                omega)
            rw [e2]
            omega
          · have e1 : ((x :: xs).filter
                (· ≤ quickselectBounded n (xs.filter (fun y => !(y < x)))
                  (k - (xs.filter (· < x)).length - 1))) =
                x :: xs.filter
                  (· ≤ quickselectBounded n (xs.filter (fun y => !(y < x)))
                    (k - (xs.filter (· < x)).length - 1)) := by
              rw [List.filter_cons,
                ite_eq_left (by simp only [decide_eq_true_eq]; exact hrx :
                  decide (x ≤ quickselectBounded n
                    (xs.filter (fun y => !(y < x)))
                    (k - (xs.filter (· < x)).length - 1)) = true)]
            rw [e1, List.length_cons, filter_length_split]
            have e2 : ((xs.filter (· < x)).filter
                (· ≤ quickselectBounded n (xs.filter (fun y => !(y < x)))
                  (k - (xs.filter (· < x)).length - 1))) =
                xs.filter (· < x) :=
              lo_filter_self _ (fun y hy => by
                have hyx := mem_lo y hy
                simp only [decide_eq_true_eq]
                omega)
            rw [e2]
            omega

/-- The order-statistic specification at the entry point. -/
theorem quickselectList_spec (l : List Nat) (k : Nat) (hk : k < l.length) :
    quickselectList l k ∈ l ∧
    (l.filter (· < quickselectList l k)).length ≤ k ∧
    k < (l.filter (· ≤ quickselectList l k)).length :=
  quickselectBounded_spec l.length l k (Nat.le_refl _) hk

/-- The draft's statement, repaired as recorded in the module doc:
the result is the `k`-th order statistic of the input. -/
theorem quickselect_correctness (input : QuickselectInput)
    (hk : input.k < input.arr.length) :
    quickselect input ∈ input.arr ∧
    (input.arr.filter (· < quickselect input)).length ≤ input.k ∧
    input.k < (input.arr.filter (· ≤ quickselect input)).length :=
  quickselectList_spec input.arr input.k hk

end AxiomCode
