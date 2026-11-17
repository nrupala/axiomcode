import Spec
import Tactics
import Algorithms.InsertionSort
import Algorithms.QuickSort
import Algorithms.CountingSort

/-!
# AxiomCode — Verified Radix Sort (LSD, base 10)

A formally verified LSD radix sort: each pass stably redistributes by
one decimal digit; after enough passes the list is sorted, and the
output is a permutation of the input.

Promoted from `lean/drafts/radixsort_correctness.lean` under the L2
promotion procedure (`lean/PROMOTION.md`). The draft is a shell: a
fieldless `RadixSortInput`, a body-less `radixSort`, and the statement
`radixSort input = List.sort (≤) input.arr` over a `List.sort` that
does not exist in Lean core. Authored for real here: the input gains
its `arr` field; a pass is the ten digit-buckets of the list (each a
filter, hence stable), and `radixSortP p` runs passes for digit
positions `0..p - 1`. The draft's claim is carried in repaired
notation — core's sort, list-first: `radixSort input =
input.arr.mergeSort (· ≤ ·)` — the proposition (radix sort computes
the sorted list) unchanged; the repair is recorded here, not silent.

Correctness shape: the invariant after `p` passes is pairwise
sortedness by the truncated key `x % 10 ^ p` (the digit decomposition
is core's `Nat.mod_mul`), plus permutation at every stage (bucketing
by a bounded key is a permutation — `flatMap_filter_perm_of_lt`). At
`passes = max + 1`, `10 ^ passes` exceeds every element
(`Nat.lt_pow_self`), the truncated key is the element itself, and the
invariant is sortedness. Reused from the sibling entries of this item:
the `Sorted` ↔ `Pairwise` bridge (`Algorithms.InsertionSort`),
`filter_partition_perm` (`Algorithms.QuickSort`), and
`pairwise_perm_eq` / `mergeSort_pairwise` (`Algorithms.CountingSort`)
— reused, not duplicated, as the constants live in this namespace.
-/

namespace AxiomCode

/-- Input for radix sort: a list of natural numbers. -/
structure RadixSortInput where
  arr : List Nat
deriving DecidableEq, Repr

/-- The `k`-th decimal digit of `x` (0 = units). -/
def radixDigit (k x : Nat) : Nat := (x / 10 ^ k) % 10

theorem radixDigit_eq (k x : Nat) : radixDigit k x = (x / 10 ^ k) % 10 := rfl

/-- One LSD radix pass: stably redistribute `l` by digit `k` —
the buckets for digits `0..9`, each a filter of `l` (hence in
original relative order), concatenated in digit order. -/
def radixPass (k : Nat) (l : List Nat) : List Nat :=
  (List.range 10).flatMap (fun d => l.filter (fun x => radixDigit k x = d))

theorem radixPass_eq (k : Nat) (l : List Nat) :
    radixPass k l =
      (List.range 10).flatMap (fun d => l.filter (fun x => radixDigit k x = d)) :=
  rfl

/-- `p` LSD passes, digit positions `0, 1, …, p - 1` in that order. -/
def radixSortP : Nat → List Nat → List Nat
  | 0, l => l
  | p + 1, l => radixPass p (radixSortP p l)

theorem radixSortP_zero (l : List Nat) : radixSortP 0 l = l := rfl

theorem radixSortP_succ (p : Nat) (l : List Nat) :
    radixSortP (p + 1) l = radixPass p (radixSortP p l) := rfl

/-- Radix sort: enough passes that `10 ^ passes` exceeds every element
(`passes = max + 1` suffices, since `n < 10 ^ n`). -/
def radixSortList (l : List Nat) : List Nat :=
  radixSortP (l.foldr max 0 + 1) l

/-- Radix sort on the input structure (the draft's signature). -/
def radixSort (input : RadixSortInput) : List Nat :=
  radixSortList input.arr

-- Filters with pointwise-equal predicates (on the list's elements) agree.
theorem filter_congr_mem (p q : Nat → Bool) (l : List Nat)
    (h : ∀ x ∈ l, p x = q x) : l.filter p = l.filter q := by
  induction l with
  | nil => rfl
  | cons x xs ih =>
    rw [List.filter_cons, List.filter_cons, h x (List.Mem.head xs),
      ih (fun y hy => h y (List.Mem.tail x hy))]

theorem flatMap_filter_congr (f : Nat → Nat) (l l' : List Nat) (ds : List Nat)
    (h : ∀ d ∈ ds, l'.filter (fun x => f x = d) = l.filter (fun x => f x = d)) :
    ds.flatMap (fun d => l'.filter (fun x => f x = d)) =
      ds.flatMap (fun d => l.filter (fun x => f x = d)) := by
  induction ds with
  | nil => rfl
  | cons d ds ih =>
    rw [List.flatMap_cons, List.flatMap_cons, h d (List.Mem.head ds),
      ih (fun e he => h e (List.Mem.tail d he))]

-- Bucketing a list by a bounded key is a permutation of the list.
theorem flatMap_filter_perm_of_lt (f : Nat → Nat) :
    ∀ (n : Nat) (l : List Nat), (∀ x ∈ l, f x < n) →
      List.Perm ((List.range n).flatMap (fun d => l.filter (fun x => f x = d)))
        l := by
  intro n
  induction n with
  | zero =>
    intro l hf
    cases l with
    | nil => simp
    | cons x xs => exact absurd (hf x (List.Mem.head xs)) (Nat.not_lt_zero _)
  | succ n ih =>
    intro l hf
    have hf' : ∀ x ∈ l.filter (fun x => f x < n), f x < n :=
      fun x hx => of_decide_eq_true (List.mem_filter.mp hx).2
    have ih' := ih (l.filter (fun x => f x < n)) hf'
    have hcongr : (List.range n).flatMap
          (fun d => (l.filter (fun x => f x < n)).filter (fun x => f x = d))
        = (List.range n).flatMap (fun d => l.filter (fun x => f x = d)) := by
      apply flatMap_filter_congr
      intro d hd
      have hdn : d < n := List.mem_range.mp hd
      rw [List.filter_filter]
      apply filter_congr_mem
      intro x _
      by_cases h : f x = d
      · have hd : decide (f x = d) = true := by
          simp only [decide_eq_true_eq]; exact h
        have h2 : decide (f x < n) = true := by
          simp only [decide_eq_true_eq]; omega
        simp [hd, h2]
      · have hd : decide (f x = d) = false := by
          simp only [decide_eq_false_iff_not]; exact h
        simp [hd]
    have hcong2 : l.filter (fun x => f x = n) =
        l.filter (fun x => !decide (f x < n)) := by
      apply filter_congr_mem
      intro x hx
      have hfx := hf x hx
      by_cases h : f x < n
      · have hd1 : decide (f x < n) = true := by
          simp only [decide_eq_true_eq]; exact h
        have hd2 : decide (f x = n) = false := by
          simp only [decide_eq_false_iff_not]; omega
        simp [hd1, hd2]
      · have hd1 : decide (f x < n) = false := by
          simp only [decide_eq_false_iff_not]; exact h
        have hd2 : decide (f x = n) = true := by
          simp only [decide_eq_true_eq]; omega
        simp [hd1, hd2]
    have hsplit : List.Perm
        (l.filter (fun x => f x < n) ++ l.filter (fun x => f x = n)) l := by
      rw [hcong2]
      exact filter_partition_perm _ l
    have hflat : (List.range (n + 1)).flatMap (fun d => l.filter (fun x => f x = d))
        = (List.range n).flatMap (fun d => l.filter (fun x => f x = d)) ++
          l.filter (fun x => f x = n) := by
      rw [List.range_succ, List.flatMap_append]
      congr 1
      simp [List.flatMap_cons]
    rw [hflat, ← hcongr]
    exact (List.Perm.append_right _ ih').trans hsplit

theorem radixPass_perm (k : Nat) (l : List Nat) :
    List.Perm (radixPass k l) l :=
  flatMap_filter_perm_of_lt (radixDigit k) 10 l
    (fun x _ => Nat.mod_lt _ (by decide))

-- Relation conversion for `Pairwise` with membership side conditions.
theorem pairwise_imp_mem {R S : Nat → Nat → Prop} {l : List Nat}
    (h : ∀ x ∈ l, ∀ y ∈ l, R x y → S x y) (hp : List.Pairwise R l) :
    List.Pairwise S l := by
  induction l with
  | nil => exact List.Pairwise.nil
  | cons a l ih =>
    rw [List.pairwise_cons] at hp ⊢
    obtain ⟨hrel, htail⟩ := hp
    exact ⟨fun a' ha' => h a (List.Mem.head l) a' (List.Mem.tail a ha') (hrel a' ha'),
      ih (fun x hx y hy hxy => h x (List.Mem.tail a hx) y (List.Mem.tail a hy) hxy)
        htail⟩

-- Pairwise over a range-flatMap of buckets: within-bucket pairwise plus
-- a strict cross-bucket relation gives pairwise of the concatenation.
theorem pairwise_flatMap_range (R : Nat → Nat → Prop) (g : Nat → List Nat)
    (n : Nat)
    (hpair : ∀ d, List.Pairwise R (g d))
    (hcross : ∀ d₁ d₂, d₁ < d₂ → ∀ x ∈ g d₁, ∀ y ∈ g d₂, R x y) :
    List.Pairwise R ((List.range n).flatMap g) := by
  induction n with
  | zero => simp
  | succ n ih =>
    have hsing : ([n] : List Nat).flatMap g = g n := by
      simp [List.flatMap_cons]
    rw [List.range_succ, List.flatMap_append, List.pairwise_append]
    refine ⟨ih, ?_, ?_⟩
    · rw [hsing]
      exact hpair n
    · intro x hx y hy
      obtain ⟨d₁, hd₁, hx1⟩ := List.mem_flatMap.mp hx
      have hd1n : d₁ < n := List.mem_range.mp hd₁
      rw [hsing] at hy
      exact hcross d₁ n hd1n x hx1 y hy

theorem radixPass_pairwise_key (k : Nat) (l : List Nat)
    (h : List.Pairwise (fun x y => x % 10 ^ k ≤ y % 10 ^ k) l) :
    List.Pairwise (fun x y => x % 10 ^ (k + 1) ≤ y % 10 ^ (k + 1))
      (radixPass k l) := by
  rw [radixPass_eq]
  apply pairwise_flatMap_range _ _ 10
  · intro d
    have hsub : List.Pairwise (fun x y => x % 10 ^ k ≤ y % 10 ^ k)
        (l.filter (fun x => radixDigit k x = d)) :=
      h.sublist (List.filter_sublist)
    apply pairwise_imp_mem _ hsub
    intro x hx y hy hxy
    have hdx : radixDigit k x = d := of_decide_eq_true (List.mem_filter.mp hx).2
    have hdy : radixDigit k y = d := of_decide_eq_true (List.mem_filter.mp hy).2
    have ex : x % 10 ^ (k + 1) = x % 10 ^ k + 10 ^ k * d := by
      rw [show (10 : Nat) ^ (k + 1) = 10 ^ k * 10 from Nat.pow_succ 10 k,
        Nat.mod_mul, ← radixDigit_eq, hdx]
    have ey : y % 10 ^ (k + 1) = y % 10 ^ k + 10 ^ k * d := by
      rw [show (10 : Nat) ^ (k + 1) = 10 ^ k * 10 from Nat.pow_succ 10 k,
        Nat.mod_mul, ← radixDigit_eq, hdy]
    omega
  · intro d₁ d₂ hd12 x hx y hy
    have hdx : radixDigit k x = d₁ := of_decide_eq_true (List.mem_filter.mp hx).2
    have hdy : radixDigit k y = d₂ := of_decide_eq_true (List.mem_filter.mp hy).2
    have ex : x % 10 ^ (k + 1) = x % 10 ^ k + 10 ^ k * d₁ := by
      rw [show (10 : Nat) ^ (k + 1) = 10 ^ k * 10 from Nat.pow_succ 10 k,
        Nat.mod_mul, ← radixDigit_eq, hdx]
    have ey : y % 10 ^ (k + 1) = y % 10 ^ k + 10 ^ k * d₂ := by
      rw [show (10 : Nat) ^ (k + 1) = 10 ^ k * 10 from Nat.pow_succ 10 k,
        Nat.mod_mul, ← radixDigit_eq, hdy]
    have hmod : x % 10 ^ k < 10 ^ k :=
      Nat.mod_lt _ (Nat.pow_pos (a := 10) (n := k) (by decide))
    have hmul : 10 ^ k * d₁ + 10 ^ k ≤ 10 ^ k * d₂ := by
      have h1 : 10 ^ k * (d₁ + 1) ≤ 10 ^ k * d₂ :=
        Nat.mul_le_mul_left _ (by omega : d₁ + 1 ≤ d₂)
      rwa [Nat.mul_add, Nat.mul_one] at h1
    omega

theorem radixSortP_pairwise (p : Nat) (l : List Nat) :
    List.Pairwise (fun x y => x % 10 ^ p ≤ y % 10 ^ p) (radixSortP p l) ∧
    List.Perm (radixSortP p l) l := by
  induction p generalizing l with
  | zero =>
    rw [radixSortP_zero]
    refine ⟨?_, List.Perm.refl _⟩
    induction l with
    | nil => exact List.Pairwise.nil
    | cons a l ih =>
      rw [List.pairwise_cons]
      exact ⟨fun a' _ => by
        have h1 : a % 10 ^ 0 = 0 := by simp only [Nat.pow_zero, Nat.mod_one]
        have h2 : a' % 10 ^ 0 = 0 := by simp only [Nat.pow_zero, Nat.mod_one]
        omega, ih⟩
  | succ p ih =>
    obtain ⟨ihp, ihperm⟩ := ih l
    rw [radixSortP_succ]
    exact ⟨radixPass_pairwise_key p _ ihp, (radixPass_perm p _).trans ihperm⟩

theorem radixSortList_perm (l : List Nat) : List.Perm (radixSortList l) l :=
  (radixSortP_pairwise _ l).2

theorem radixSortList_sorted (l : List Nat) : Sorted (radixSortList l) := by
  have h := (radixSortP_pairwise (l.foldr max 0 + 1) l).1
  apply pairwise_sorted
  apply pairwise_imp_mem _ h
  intro x hx y hy hxy
  have hxM : x ≤ l.foldr max 0 :=
    mem_le_foldr_max l x ((radixSortList_perm l).mem_iff.mp hx)
  have hyM : y ≤ l.foldr max 0 :=
    mem_le_foldr_max l y ((radixSortList_perm l).mem_iff.mp hy)
  have h10 : l.foldr max 0 + 1 < 10 ^ (l.foldr max 0 + 1) :=
    Nat.lt_pow_self (by decide)
  have hlt : x < 10 ^ (l.foldr max 0 + 1) :=
    Nat.lt_trans (Nat.lt_succ_of_le hxM) h10
  have hylt : y < 10 ^ (l.foldr max 0 + 1) :=
    Nat.lt_trans (Nat.lt_succ_of_le hyM) h10
  rwa [Nat.mod_eq_of_lt hlt, Nat.mod_eq_of_lt hylt] at hxy

/-- Library-standard correctness: radix sort meets `SortSpec`. -/
theorem radixSortList_correct (l : List Nat) : SortSpec radixSortList :=
  fun l => ⟨radixSortList_sorted l, (radixSortList_perm l).symm⟩

/-- The draft's statement, with `List.sort (≤)` repaired to the core
sort `List.mergeSort (· ≤ ·)` (Lean core has no `List.sort`): radix
sort computes the sorted list. -/
theorem radixSort_correctness (input : RadixSortInput) :
    radixSort input = input.arr.mergeSort (· ≤ ·) :=
  pairwise_perm_eq (sorted_pairwise (radixSortList_sorted _)) (mergeSort_pairwise _)
    ((radixSortList_perm _).trans (List.mergeSort_perm _ _).symm)

end AxiomCode
