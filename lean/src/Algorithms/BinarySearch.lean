import Spec
import Tactics

/-!
# AxiomCode — Verified Binary Search

Promoted from `lean/drafts/binarysearch_correctness {α.lean` under the
L2 promotion procedure (`lean/PROMOTION.md`). Authored and proved by
Arjun (Item 4B, own-hands track).

Statement-honesty record. The draft was a shell: a fieldless
`SortedArray` structure, a body-less `binarySearch`, and a statement
quantifying over a field (`sa.arr`) that does not exist in the shell —
ill-posed as written. The recon's intended target was Spec's
`BinarySearchSpec`; that specification is itself unsatisfiable as
written — `binarySearchSpec_unsat` below proves that NO function
satisfies it (on `[1, 1]` with target `1`, the iff forces
`f l x = some 0` and `f l x = some 1` at once: the iff silently assumes
the target occurs at most once). This entry therefore proves the
standard two-direction form — soundness (`binarySearch_sound`) and
completeness (`binarySearch_complete`), packaged as
`binarySearch_correct`. Repairing `BinarySearchSpec` in Spec.lean is a
specification decision above this entry; it is flagged here, not
silently routed around.
-/

namespace AxiomCode

/-- FINDING (for the Director's ruling): `BinarySearchSpec` as written in
Spec.lean is unsatisfiable — NO function satisfies it. On a list with a
duplicated value ([1, 1], x = 1), the iff forces `f l x = some 0` and
`f l x = some 1` simultaneously. The provable, standard form is the
two-direction pair (soundness + completeness) proved below; the Spec's iff
form additionally needs a uniqueness hypothesis it does not state. -/
theorem binarySearchSpec_unsat (f : List Nat → Nat → Option Nat) :
    ¬ BinarySearchSpec f := by
  intro hf
  have hS : Sorted [1, 1] := by
    intro i j hij hj
    have hlen : ([1, 1] : List Nat).length = 2 := rfl
    have hj1 : j = 1 := by omega
    have hi0 : i = 0 := by omega
    subst hj1; subst hi0
    exact Nat.le_refl 1
  have h0 : f [1, 1] 1 = some 0 :=
    (hf [1, 1] 1 hS 0).mpr ⟨rfl, by decide⟩
  have h1 : f [1, 1] 1 = some 1 :=
    (hf [1, 1] 1 hS 1).mpr ⟨rfl, by decide⟩
  rw [h0] at h1
  exact absurd (Option.some.inj h1) (by omega)

/-- Binary search over a sorted list: split at the midpoint, recurse into the
half that can contain the target. -/
def binarySearch : List Nat → Nat → Option Nat
  | [], _ => none
  | a :: as, x =>
    let l := a :: as
    let mid := l.length / 2
    let pivot := l[mid]!
    if x = pivot then some mid
    else if x < pivot then binarySearch (l.take mid) x
    else (binarySearch (l.drop (mid + 1)) x).map (· + (mid + 1))
  termination_by l _ => l.length
  decreasing_by
    · simp only [List.length_take, List.length_cons]
      omega
    · simp only [List.length_drop, List.length_cons]
      omega

/-- `getI` at an in-range index is the index itself. -/
theorem binarySearch_getI_eq_get (l : List Nat) (i : Nat) (h : i < l.length) :
    l[i]! = l[i]'h := by
  have h1 : l[i]? = some (l[i]'h) := List.getElem?_eq_some_iff.mpr ⟨h, rfl⟩
  rw [List.getElem!_eq_getElem?_getD, h1]
  rfl

/-- `getI` commutes with `take` below the cut. -/
theorem binarySearch_getI_take (l : List Nat) {n i : Nat} (h : i < n) :
    (l.take n)[i]! = l[i]! := by
  rw [List.getElem!_eq_getElem?_getD, List.getElem!_eq_getElem?_getD,
    List.getElem?_take_of_lt h]

/-- `getI` commutes with `drop`, shifting the index. -/
theorem binarySearch_getI_drop (l : List Nat) (n i : Nat) :
    (l.drop n)[i]! = l[n + i]! := by
  rw [List.getElem!_eq_getElem?_getD, List.getElem!_eq_getElem?_getD,
    List.getElem?_drop]

theorem binarySearch_sorted_take (l : List Nat) (hS : Sorted l) (n : Nat) :
    Sorted (l.take n) := by
  intro i j hij hj
  have hlen : (l.take n).length = min n l.length := List.length_take
  have hi : i < n := by omega
  have hjl : j < l.length := by omega
  rw [binarySearch_getI_take l hi, binarySearch_getI_take l (by omega : j < n)]
  exact hS i j hij hjl

theorem binarySearch_sorted_drop (l : List Nat) (hS : Sorted l) (n : Nat) :
    Sorted (l.drop n) := by
  intro i j hij hj
  have hlen : (l.drop n).length = l.length - n := List.length_drop
  rw [binarySearch_getI_drop, binarySearch_getI_drop]
  exact hS (n + i) (n + j) (by omega) (by omega)

/-- Soundness: an index returned by `binarySearch` really holds the target. -/
theorem binarySearch_sound (l : List Nat) (x : Nat) (hS : Sorted l) :
    ∀ i, binarySearch l x = some i → l[i]! = x ∧ i < l.length := by
  have key : ∀ k, ∀ l, l.length < k → ∀ (x : Nat), Sorted l →
      ∀ i, binarySearch l x = some i → l[i]! = x ∧ i < l.length := by
    intro k
    induction k with
    | zero => intro l hl; exact absurd hl (Nat.not_lt_zero _)
    | succ k ih =>
      intro l hl x hS i hfound
      cases l with
      | nil => simp [binarySearch] at hfound
      | cons a as =>
        have hlen : 0 < (a :: as).length := by simp
        have hmid : (a :: as).length / 2 < (a :: as).length :=
          Nat.div_lt_self hlen (by omega)
        have htake : (List.take ((a :: as).length / 2) (a :: as)).length <
            (a :: as).length := by
          rw [List.length_take]; omega
        have hdrop : (List.drop ((a :: as).length / 2 + 1) (a :: as)).length <
            (a :: as).length := by
          rw [List.length_drop]; omega
        simp only [binarySearch] at hfound
        by_cases hx : x = (a :: as)[(a :: as).length / 2]!
        · rw [ite_eq_left hx] at hfound
          have hmi : (a :: as).length / 2 = i := Option.some.inj hfound
          exact ⟨by rw [← hmi]; exact hx.symm, by rw [← hmi]; exact hmid⟩
        · rw [ite_eq_right hx] at hfound
          by_cases hlt : x < (a :: as)[(a :: as).length / 2]!
          · rw [ite_eq_left hlt] at hfound
            obtain ⟨h1, h2⟩ := ih _ (by omega : ((a :: as).take ((a :: as).length / 2)).length < k)
              x (binarySearch_sorted_take _ hS _) i hfound
            have hilen : i < (a :: as).length / 2 := by
              have : i < ((a :: as).take ((a :: as).length / 2)).length := h2
              rw [List.length_take] at this; omega
            exact ⟨by rwa [binarySearch_getI_take _ hilen] at h1, by omega⟩
          · rw [ite_eq_right hlt] at hfound
            obtain ⟨j, hj, hji⟩ := Option.map_eq_some_iff.mp hfound
            obtain ⟨h1, h2⟩ := ih _ (by omega : ((a :: as).drop ((a :: as).length / 2 + 1)).length < k)
              x (binarySearch_sorted_drop _ hS _) j hj
            have hidx : ((a :: as).length / 2 + 1) + j = i := by omega
            constructor
            · rw [← hidx]; rwa [binarySearch_getI_drop] at h1
            · have : j < (a :: as).length - ((a :: as).length / 2 + 1) := by
                have h2' : j < ((a :: as).drop ((a :: as).length / 2 + 1)).length := h2
                rwa [List.length_drop] at h2'
              omega
  intro i hfound
  exact key (l.length + 1) l (Nat.lt_succ_self _) x hS i hfound

/-- Completeness: a target present in a sorted list is found. -/
theorem binarySearch_complete (l : List Nat) (x : Nat) (hS : Sorted l)
    (hmem : x ∈ l) :
    ∃ i, binarySearch l x = some i ∧ l[i]! = x ∧ i < l.length := by
  have key : ∀ k, ∀ l, l.length < k → ∀ (x : Nat), Sorted l → x ∈ l →
      ∃ i, binarySearch l x = some i ∧ l[i]! = x ∧ i < l.length := by
    intro k
    induction k with
    | zero => intro l hl; exact absurd hl (Nat.not_lt_zero _)
    | succ k ih =>
      intro l hl x hS hmem
      cases l with
      | nil => simp at hmem
      | cons a as =>
        have hlen : 0 < (a :: as).length := by simp
        have hmid : (a :: as).length / 2 < (a :: as).length :=
          Nat.div_lt_self hlen (by omega)
        obtain ⟨j, hjlen, hj⟩ := List.mem_iff_getElem.mp hmem
        have hjx : (a :: as)[j]! = x := by
          rw [binarySearch_getI_eq_get _ j hjlen]; exact hj
        by_cases hx : x = (a :: as)[(a :: as).length / 2]!
        · refine ⟨(a :: as).length / 2, ?_, hx.symm, hmid⟩
          simp only [binarySearch]
          rw [ite_eq_left hx]
        · by_cases hlt : x < (a :: as)[(a :: as).length / 2]!
          · have hjm : j < (a :: as).length / 2 := by
              rcases Nat.lt_or_ge j ((a :: as).length / 2) with h | h
              · exact h
              · exfalso
                rcases Nat.eq_or_lt_of_le h with heq | hgt
                · have hp : (a :: as)[(a :: as).length / 2]! = x := by
                    rw [heq]; exact hjx
                  omega
                · have := hS ((a :: as).length / 2) j hgt hjlen
                  omega
            have hmemt : x ∈ (a :: as).take ((a :: as).length / 2) := by
              rw [List.mem_iff_getElem?]
              refine ⟨j, ?_⟩
              rw [List.getElem?_take_of_lt hjm, List.getElem?_eq_some_iff]
              exact ⟨hjlen, hj⟩
            obtain ⟨i, hfound, h1, h2⟩ := ih _
              (by rw [List.length_take]; omega :
                ((a :: as).take ((a :: as).length / 2)).length < k)
              x (binarySearch_sorted_take _ hS _) hmemt
            have hilen : i < (a :: as).length / 2 := by
              have : i < ((a :: as).take ((a :: as).length / 2)).length := h2
              rw [List.length_take] at this; omega
            refine ⟨i, ?_, ?_, by omega⟩
            · simp only [binarySearch]
              rw [ite_eq_right hx, ite_eq_left hlt]
              exact hfound
            · rwa [binarySearch_getI_take _ hilen] at h1
          · have hmj : (a :: as).length / 2 < j := by
              rcases Nat.lt_or_ge ((a :: as).length / 2) j with h | h
              · exact h
              · exfalso
                rcases Nat.eq_or_lt_of_le h with heq | hgt
                · have hp : (a :: as)[j]! = (a :: as)[(a :: as).length / 2]! := by
                    rw [heq]
                  omega
                · have := hS j ((a :: as).length / 2) hgt hmid
                  omega
            have hmemd : x ∈ (a :: as).drop ((a :: as).length / 2 + 1) := by
              rw [List.mem_iff_getElem?]
              refine ⟨j - ((a :: as).length / 2 + 1), ?_⟩
              rw [List.getElem?_drop]
              have hsum : (a :: as).length / 2 + 1 +
                    (j - ((a :: as).length / 2 + 1)) = j :=
                  Nat.add_sub_cancel' hmj
              rw [hsum]
              exact List.getElem?_eq_some_iff.mpr ⟨hjlen, hj⟩
            obtain ⟨i, hfound, h1, h2⟩ := ih _
              (by rw [List.length_drop]; omega :
                ((a :: as).drop ((a :: as).length / 2 + 1)).length < k)
              x (binarySearch_sorted_drop _ hS _) hmemd
            refine ⟨i + ((a :: as).length / 2 + 1), ?_, ?_, ?_⟩
            · simp only [binarySearch]
              rw [ite_eq_right hx, ite_eq_right hlt, hfound]
              rfl
            · have hidx : (a :: as).length / 2 + 1 + i =
                  i + ((a :: as).length / 2 + 1) := by omega
              rw [← hidx]; rwa [binarySearch_getI_drop] at h1
            · have : i < (a :: as).length - ((a :: as).length / 2 + 1) := by
                have h2' : i < ((a :: as).drop ((a :: as).length / 2 + 1)).length := h2
                rwa [List.length_drop] at h2'
              omega
  exact key (l.length + 1) l (Nat.lt_succ_self _) x hS hmem

/-- The honest binary-search specification: the two-direction pair that
`BinarySearchSpec`'s iff form overstates (see `binarySearchSpec_unsat`). -/
theorem binarySearch_correct (l : List Nat) (x : Nat) (hS : Sorted l) :
    (∀ i, binarySearch l x = some i → l[i]! = x ∧ i < l.length) ∧
    (x ∈ l → ∃ i, binarySearch l x = some i ∧ l[i]! = x ∧ i < l.length) :=
  ⟨binarySearch_sound l x hS, binarySearch_complete l x hS⟩


end AxiomCode
