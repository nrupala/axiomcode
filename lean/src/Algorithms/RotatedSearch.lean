import Spec
import Tactics
import Algorithms.InsertionSort

/-!
# Search in a rotated sorted array

The draft (`drafts/searchinrotatedarray_correctness.lean`) did not
elaborate: `RotatedSortedArray` had no fields, `searchInRotatedArray`
had no body, it imported all of Mathlib (the library builds on core
plus the house `Tactics`), and its statement used the proof-carrying
`arr.arr[idx]`, which cannot even be stated for an `idx` produced by
the search without a bound proof in hand. Its claim was:

> `∀ arr target, match searchInRotatedArray arr target with
>   | some idx => arr.arr[idx] = target
>   | none => ¬∃ idx, arr.arr[idx] = target`

Defect on record: as stated, the claim is **false for the named
algorithm** — binary search in a rotated array is only correct on
rotated sorted input, a hypothesis the draft nowhere states.
Counterexample: `arr = [1, 3, 2]`, `target = 2`. The search takes
the middle element `3`; since the head `1 < 3`, the left part is
treated as sorted, and `1 ≤ 2 < 3` sends the search into `[1]`,
which returns `none` — but `2 ∈ [1, 3, 2]`, refuting the `none`
case. (A linear scan would satisfy the bare statement, but it is
not the named algorithm.)

Repair (the draft's proposition shape, the LRU precedent): the
structure gains its `arr` field; the theorem carries the hypothesis
`RotatedSorted arr.arr` — the invariant the type's name asserts —
stated here as two pairwise-sorted blocks with every element of the
second `≤` every element of the first; the `some` case is stated in
the total `arr.arr[idx]!` form with the bound `idx < arr.arr.length`
as an explicit conjunct, and the `none` case as `target ∉ arr.arr`
(the draft's `¬∃ idx` over the proof-carrying index, restated over
membership). The draft's `Int` target is specialised to `Nat`: the
library's `Spec` layer is `Nat`-typed throughout.
-/

namespace AxiomCode

/-- A rotated sorted list: two pairwise-sorted blocks, every element
of the second block `≤` every element of the first (so `b ++ a` is
the un-rotated sorted list). -/
def RotatedSorted (w : List Nat) : Prop :=
  ∃ a b, w = a ++ b ∧ List.Pairwise (· ≤ ·) a ∧ List.Pairwise (· ≤ ·) b ∧
    ∀ x ∈ b, ∀ y ∈ a, x ≤ y

/-- The draft's input type, given its field. -/
structure RotatedSortedArray where
  arr : List Nat
deriving DecidableEq, Repr

theorem pairwise_head_le {z : Nat} {zs : List Nat}
    (h : List.Pairwise (· ≤ ·) (z :: zs)) : ∀ y ∈ zs, z ≤ y :=
  fun y hy => (List.pairwise_cons.mp h).1 y hy

/-- Bounds from a three-way split of a pairwise list. -/
theorem pairwise_append_split {p sfx : List Nat} {z : Nat}
    (h : List.Pairwise (· ≤ ·) ((p ++ [z]) ++ sfx)) :
    (∀ y ∈ p, y ≤ z) ∧ (∀ y ∈ sfx, z ≤ y) := by
  obtain ⟨hpz, _, hcross⟩ := List.pairwise_append.mp h
  obtain ⟨_, _, hcross2⟩ := List.pairwise_append.mp hpz
  exact ⟨fun y hy => hcross2 y hy z (by simp),
    fun y hy => hcross z (by simp) y hy⟩

/-- Every element of a pairwise list is `≤` its last element. -/
theorem pairwise_le_getLast! : ∀ {l : List Nat}, List.Pairwise (· ≤ ·) l →
    ∀ {y : Nat}, y ∈ l → y ≤ l.getLast!
  | [], _, _, hy => absurd hy (by simp)
  | [z], _, y, hy => by
      have hyz : y = z := by simpa using hy
      rw [hyz]
      exact Nat.le_refl _
  | z :: z' :: zs', h, y, hy => by
      have hgl : (z :: z' :: zs').getLast! = (z' :: zs').getLast! := rfl
      rw [hgl]
      have htail : List.Pairwise (· ≤ ·) (z' :: zs') :=
        (List.pairwise_cons.mp h).2
      cases hy with
      | head =>
        exact Nat.le_trans (pairwise_head_le h z' (List.Mem.head _))
          (pairwise_le_getLast! htail (List.Mem.head _))
      | tail _ hym => exact pairwise_le_getLast! htail hym

/-- The last element of a nonempty list is a member. -/
theorem getLast!_mem : ∀ {l : List Nat}, l ≠ [] → l.getLast! ∈ l
  | [], h => absurd rfl h
  | [z], _ => List.Mem.head []
  | z :: z' :: zs', _ => by
      have hgl : (z :: z' :: zs').getLast! = (z' :: zs').getLast! := rfl
      rw [hgl]
      exact List.Mem.tail z (getLast!_mem (by simp))

/-- Dropping `n` elements exposes the `n`-th element at the head. -/
theorem drop_eq_cons_getElem! : ∀ (l : List Nat) (n : Nat), n < l.length →
    l.drop n = l[n]! :: l.drop (n + 1)
  | [], n, h => by simp at h
  | z :: zs, 0, _ => rfl
  | z :: zs, n + 1, h => by
      have h' : n < zs.length := by
        have h2 : (z :: zs).length = zs.length + 1 := rfl
        omega
      have ih := drop_eq_cons_getElem! zs n h'
      show zs.drop n = zs[n]! :: zs.drop (n + 1)
      exact ih

theorem head_mem_take {z : Nat} {zs : List Nat} {n : Nat} (hn : 0 < n) :
    z ∈ (z :: zs).take n := by
  cases n with
  | zero => omega
  | succ n' =>
    show z ∈ z :: zs.take n'
    exact List.Mem.head _

theorem mem_take_or_drop (y : Nat) (w : List Nat) (n : Nat) :
    (y ∈ w.take n ∨ y ∈ w.drop n) ↔ y ∈ w := by
  have h2 : w.take n ++ w.drop n = w := List.take_append_drop n w
  constructor
  · rintro (h | h)
    · exact List.take_subset n w h
    · exact List.drop_subset n w h
  · intro h
    rw [← h2] at h
    exact List.mem_append.mp h

/-- Slices of a rotated sorted list are rotated sorted. -/
theorem rotatedSorted_take (n : Nat) {w : List Nat} (h : RotatedSorted w) :
    RotatedSorted (w.take n) := by
  obtain ⟨a, b, hw, ha, hb, hba⟩ := h
  by_cases hn : n ≤ a.length
  · refine ⟨a.take n, [], ?_, ha.sublist (List.take_sublist n a), by simp, ?_⟩
    · rw [hw, List.take_append, Nat.sub_eq_zero_of_le hn]
      simp
    · intro x hx
      simp at hx
  · refine ⟨a, b.take (n - a.length), ?_, ha,
      hb.sublist (List.take_sublist _ b), ?_⟩
    · have hle : a.length ≤ n := by omega
      rw [hw, List.take_append, List.take_of_length_le hle]
    · intro x hx y hy
      exact hba x (List.take_subset _ b hx) y hy

theorem rotatedSorted_drop (n : Nat) {w : List Nat} (h : RotatedSorted w) :
    RotatedSorted (w.drop n) := by
  obtain ⟨a, b, hw, ha, hb, hba⟩ := h
  by_cases hn : n ≤ a.length
  · refine ⟨a.drop n, b, ?_, ha.sublist (List.drop_sublist n a), hb,
      fun x hx y hy => hba x hx y (List.drop_subset n a hy)⟩
    · rw [hw, List.drop_append, Nat.sub_eq_zero_of_le hn]
      simp
  · refine ⟨[], b.drop (n - a.length), ?_, by simp,
      hb.sublist (List.drop_sublist _ b), ?_⟩
    · have hle : a.length ≤ n := by omega
      rw [hw, List.drop_append, List.drop_of_length_le hle]
    · intro x _ y hy
      simp at hy

theorem getElem!_mem {l : List Nat} {i : Nat} (h : i < l.length) : l[i]! ∈ l := by
  have h1 : l.drop i = l[i]! :: l.drop (i + 1) := drop_eq_cons_getElem! l i h
  have h2 : l[i]! ∈ l.drop i := by
    rw [h1]
    exact List.Mem.head _
  exact List.drop_subset i l h2

theorem getElem!_append_left (l₁ l₂ : List Nat) (i : Nat) (h : i < l₁.length) :
    (l₁ ++ l₂)[i]! = l₁[i]! := by
  induction l₁ generalizing i with
  | nil => simp at h
  | cons z zs ih =>
    cases i with
    | zero => rfl
    | succ i' =>
      have h' : i' < zs.length := by
        have h2 : (z :: zs).length = zs.length + 1 := rfl
        omega
      show (z :: (zs ++ l₂))[i' + 1]! = (z :: zs)[i' + 1]!
      rw [List.getElem!_cons_succ, List.getElem!_cons_succ]
      exact ih i' h'

theorem getElem!_append_right (l₁ l₂ : List Nat) (i : Nat) (h : l₁.length ≤ i) :
    (l₁ ++ l₂)[i]! = l₂[i - l₁.length]! := by
  induction l₁ generalizing i with
  | nil => simp
  | cons z zs ih =>
    cases i with
    | zero => simp at h
    | succ i' =>
      have h' : zs.length ≤ i' := by
        have h2 : (z :: zs).length = zs.length + 1 := rfl
        omega
      have h3 : i' + 1 - (z :: zs).length = i' - zs.length := by
        have h2 : (z :: zs).length = zs.length + 1 := rfl
        omega
      show (z :: (zs ++ l₂))[i' + 1]! = l₂[i' + 1 - (z :: zs).length]!
      rw [List.getElem!_cons_succ, h3]
      exact ih i' h'

theorem getElem!_take (l : List Nat) (n i : Nat) (h : i < (l.take n).length) :
    (l.take n)[i]! = l[i]! := by
  have h2 := getElem!_append_left (l.take n) (l.drop n) i h
  rw [List.take_append_drop] at h2
  exact h2.symm

theorem getElem!_drop (l : List Nat) (n i : Nat) (h : n ≤ l.length) :
    (l.drop n)[i]! = l[i + n]! := by
  have hlen : (l.take n).length = n := by
    rw [List.length_take]
    omega
  have h2 := getElem!_append_right (l.take n) (l.drop n) (i + n)
    (by rw [List.length_take]; omega)
  rw [List.take_append_drop, hlen, Nat.add_sub_cancel] at h2
  exact h2.symm

/-- Bounds around the `j`-th element of a pairwise list: everything
in the prefix is `≤` it, everything after it is `≥` it. -/
theorem split_bounds {l : List Nat} (hl : List.Pairwise (· ≤ ·) l) (j : Nat)
    (hj : j < l.length) :
    (∀ y ∈ l.take j, y ≤ l[j]!) ∧ (∀ y ∈ l.drop (j + 1), l[j]! ≤ y) := by
  have hsplit : l = (l.take j ++ [l[j]!]) ++ l.drop (j + 1) := by
    calc l = l.take j ++ l.drop j := (List.take_append_drop j l).symm
      _ = l.take j ++ (l[j]! :: l.drop (j + 1)) := by
          rw [drop_eq_cons_getElem! l j hj]
      _ = (l.take j ++ [l[j]!]) ++ l.drop (j + 1) := by
          rw [List.append_assoc, List.singleton_append]
  rw [hsplit] at hl
  exact pairwise_append_split hl

/-- Binary search in a rotated sorted list, with an explicit fuel
bound (the list's length always suffices) and a base offset for the
window's position in the original list. In the cons case, `mid` is
`(h :: t).length / 2` and the pivot is `m = (h :: t)[mid]!`: if the
head is below the pivot, the left part is sorted and the search
continues on the side the target's range dictates; if the pivot is
below the head, symmetrically; if head and pivot agree (duplicates),
the head is dropped and the search continues on the tail. -/
def rotatedSearchBounded : Nat → List Nat → Nat → Nat → Option Nat
  | 0, _, _, _ => none
  | _ + 1, [], _, _ => none
  | fuel + 1, (h :: t), target, base =>
      if (h :: t)[(h :: t).length / 2]! = target then
        some (base + (h :: t).length / 2)
      else if h < (h :: t)[(h :: t).length / 2]! then
        if h ≤ target ∧ target < (h :: t)[(h :: t).length / 2]! then
          rotatedSearchBounded fuel ((h :: t).take ((h :: t).length / 2)) target base
        else
          rotatedSearchBounded fuel ((h :: t).drop ((h :: t).length / 2 + 1)) target
            (base + (h :: t).length / 2 + 1)
      else if (h :: t)[(h :: t).length / 2]! < h then
        if (h :: t)[(h :: t).length / 2]! < target ∧
            target ≤ ((h :: t).drop ((h :: t).length / 2)).getLast! then
          rotatedSearchBounded fuel ((h :: t).drop ((h :: t).length / 2 + 1)) target
            (base + (h :: t).length / 2 + 1)
        else
          rotatedSearchBounded fuel ((h :: t).take ((h :: t).length / 2)) target base
      else
        rotatedSearchBounded fuel t target (base + 1)

theorem rotatedSearchBounded_succ_cons (fuel h target base : Nat) (t : List Nat) :
    rotatedSearchBounded (fuel + 1) (h :: t) target base =
      if (h :: t)[(h :: t).length / 2]! = target then
        some (base + (h :: t).length / 2)
      else if h < (h :: t)[(h :: t).length / 2]! then
        if h ≤ target ∧ target < (h :: t)[(h :: t).length / 2]! then
          rotatedSearchBounded fuel ((h :: t).take ((h :: t).length / 2)) target base
        else
          rotatedSearchBounded fuel ((h :: t).drop ((h :: t).length / 2 + 1)) target
            (base + (h :: t).length / 2 + 1)
      else if (h :: t)[(h :: t).length / 2]! < h then
        if (h :: t)[(h :: t).length / 2]! < target ∧
            target ≤ ((h :: t).drop ((h :: t).length / 2)).getLast! then
          rotatedSearchBounded fuel ((h :: t).drop ((h :: t).length / 2 + 1)) target
            (base + (h :: t).length / 2 + 1)
        else
          rotatedSearchBounded fuel ((h :: t).take ((h :: t).length / 2)) target base
      else
        rotatedSearchBounded fuel t target (base + 1) := by
  rw [rotatedSearchBounded]

/-- Search a rotated sorted array for `target` (the draft's
signature, at `Nat`). -/
def searchInRotatedArray (arr : RotatedSortedArray) (target : Nat) : Option Nat :=
  rotatedSearchBounded arr.arr.length arr.arr target 0

theorem rotatedSearchBounded_spec (fuel : Nat) (w : List Nat) (target base : Nat)
    (hfuel : w.length ≤ fuel) (hrot : RotatedSorted w) :
    (∀ idx, rotatedSearchBounded fuel w target base = some idx →
      w[idx - base]! = target ∧ base ≤ idx ∧ idx - base < w.length) ∧
    (rotatedSearchBounded fuel w target base = none → target ∉ w) := by
  induction fuel generalizing w base with
  | zero =>
    have hw0 : w = [] := by
      cases w with
      | nil => rfl
      | cons z zs =>
        have h2 : (z :: zs).length = zs.length + 1 := rfl
        omega
    refine ⟨fun idx hidx => ?_, fun _ => ?_⟩
    · have h0 : rotatedSearchBounded 0 w target base = none := by
        rw [rotatedSearchBounded]
      rw [h0] at hidx
      simp at hidx
    · rw [hw0]
      simp
  | succ fuel ih =>
    cases w with
    | nil =>
      refine ⟨fun idx hidx => ?_, fun _ => by simp⟩
      · have h0 : rotatedSearchBounded (fuel + 1) [] target base = none := by
          rw [rotatedSearchBounded]
        rw [h0] at hidx
        simp at hidx
    | cons h t =>
      have key : ∀ (mid m : Nat), mid = (h :: t).length / 2 →
          m = (h :: t)[mid]! →
          (∀ idx, rotatedSearchBounded (fuel + 1) (h :: t) target base = some idx →
            (h :: t)[idx - base]! = target ∧ base ≤ idx ∧
              idx - base < (h :: t).length) ∧
          (rotatedSearchBounded (fuel + 1) (h :: t) target base = none →
            target ∉ h :: t) := by
        intro mid m hmid_def hm_def
        rw [rotatedSearchBounded_succ_cons, ← hmid_def, ← hm_def]
        have hlen_eq : (h :: t).length = t.length + 1 := rfl
        have hmid_lt : mid < (h :: t).length := by
          rw [hmid_def]
          exact Nat.div_lt_self (by omega) (by decide)
        have hdrop : (h :: t).drop mid = m :: (h :: t).drop (mid + 1) := by
          have h1 := drop_eq_cons_getElem! (h :: t) mid hmid_lt
          rwa [← hm_def] at h1
        have hrot_take : RotatedSorted ((h :: t).take mid) :=
          rotatedSorted_take mid hrot
        have hrot_drop : RotatedSorted ((h :: t).drop (mid + 1)) :=
          rotatedSorted_drop (mid + 1) hrot
        have hrot_tail : RotatedSorted t := rotatedSorted_drop 1 hrot
        obtain ⟨a, b, hw, ha, hb, hba⟩ := hrot
        have hlen_w : (h :: t).length = a.length + b.length := by
          rw [hw, List.length_append]
        have hhead : (∃ as, a = h :: as) ∨ a = [] := by
          cases a with
          | nil => exact Or.inr rfl
          | cons a₀ as =>
            have h2 : h :: t = a₀ :: (as ++ b) := hw
            injection h2 with h4 h5
            exact Or.inl ⟨as, by rw [h4]⟩
        have hh_mem_a : h ∈ a ∨ a = [] := by
          cases hhead with
          | inl hh =>
            obtain ⟨as, has⟩ := hh
            exact Or.inl (by rw [has]; exact List.Mem.head _)
          | inr hh => exact Or.inr hh
        by_cases hmt : m = target
        · rw [ite_eq_left hmt]
          refine ⟨fun idx hidx => ?_, fun hn => by simp at hn⟩
          · have hidx2 : base + mid = idx := Option.some.inj hidx
            refine ⟨?_, by omega, ?_⟩
            · rw [← hidx2, Nat.add_sub_cancel_left, ← hm_def]
              exact hmt
            · rw [← hidx2, Nat.add_sub_cancel_left]
              exact hmid_lt
        · rw [ite_eq_right hmt]
          by_cases hhm : h < m
          · rw [ite_eq_left hhm]
            have hB2case : a.length > mid ∨ a = [] := by
              by_contra hcon
              have hsm : a.length ≤ mid := by
                by_contra hc
                exact hcon (Or.inl (by omega))
              have ha_ne : a ≠ [] := fun hh => hcon (Or.inr hh)
              have hmb : m ∈ b := by
                have h1 : m = b[mid - a.length]! := by
                  rw [hm_def, hw]
                  exact getElem!_append_right a b mid hsm
                rw [h1]
                exact getElem!_mem (by omega)
              have hle : m ≤ h := by
                cases hh_mem_a with
                | inl hh => exact hba m hmb h hh
                | inr hh => exact absurd hh ha_ne
              omega
            by_cases hcond : h ≤ target ∧ target < m
            · rw [ite_eq_left hcond]
              have hfuel_take : ((h :: t).take mid).length ≤ fuel := by
                rw [List.length_take]
                omega
              obtain ⟨ih_some, ih_none⟩ := ih ((h :: t).take mid) base hfuel_take
                hrot_take
              have b2a_excl : target ∈ (h :: t).drop (mid + 1) →
                  target ∈ (h :: t).take mid := by
                intro hmem
                rw [hw, List.drop_append] at hmem
                cases List.mem_append.mp hmem with
                | inl hy =>
                  cases hB2case with
                  | inl hgt =>
                    have hsb := (split_bounds ha mid hgt).2 target hy
                    have hm_a : m = a[mid]! := by
                      rw [hm_def, hw]
                      exact getElem!_append_left a b mid hgt
                    exfalso
                    omega
                  | inr ha0 =>
                    rw [ha0] at hy
                    simp at hy
                | inr hy =>
                  cases hB2case with
                  | inl hgt =>
                    have htb : target ∈ b := List.drop_subset _ b hy
                    have hha : h ∈ a := by
                      cases hh_mem_a with
                      | inl hh => exact hh
                      | inr hh =>
                        exfalso
                        have h6 : a.length = 0 := by simp [hh]
                        omega
                    have hle : target ≤ h := hba target htb h hha
                    have hmid_pos : 0 < mid := by
                      by_contra hc
                      have hm0 : mid = 0 := by omega
                      rw [hm0] at hdrop
                      simp only [List.drop_zero, List.cons.injEq] at hdrop
                      obtain ⟨h45, -⟩ := hdrop
                      omega
                    rw [show target = h by omega]
                    exact head_mem_take hmid_pos
                  | inr ha0 =>
                    have hm_b : m = b[mid]! := by
                      rw [hm_def, hw, ha0]
                      exact getElem!_append_right [] b mid (by simp)
                    have hlen_b : mid < b.length := by
                      rw [ha0] at hlen_w
                      simp at hlen_w
                      omega
                    have hsb := (split_bounds hb mid hlen_b).2 target (by
                      simpa [ha0] using hy)
                    exfalso
                    omega
              refine ⟨fun idx hidx => ?_, fun hn => ?_⟩
              · obtain ⟨h1, h2, h3⟩ := ih_some idx hidx
                refine ⟨?_, h2, ?_⟩
                · rwa [getElem!_take (h :: t) mid (idx - base) h3] at h1
                · have h4 : ((h :: t).take mid).length ≤ (h :: t).length := by
                    rw [List.length_take]
                    omega
                  omega
              · intro hmem
                have htd := (mem_take_or_drop target (h :: t) mid).mpr hmem
                cases htd with
                | inl hh => exact ih_none hn hh
                | inr hh =>
                  rw [hdrop] at hh
                  cases List.mem_cons.mp hh with
                  | inl hh2 => exact hmt hh2.symm
                  | inr hh2 => exact ih_none hn (b2a_excl hh2)
            · rw [ite_eq_right hcond]
              have hfuel_drop : ((h :: t).drop (mid + 1)).length ≤ fuel := by
                rw [List.length_drop]
                omega
              obtain ⟨ih_some, ih_none⟩ := ih ((h :: t).drop (mid + 1))
                (base + mid + 1) hfuel_drop hrot_drop
              have b2b_excl : target ∈ (h :: t).take mid → False := by
                intro hh
                have hbounds : h ≤ target ∧ target ≤ m := by
                  cases hB2case with
                  | inl hgt =>
                    have htake : (h :: t).take mid = a.take mid := by
                      rw [hw, List.take_append,
                        Nat.sub_eq_zero_of_le (by omega : mid ≤ a.length),
                        List.take_zero, List.append_nil]
                    rw [htake] at hh
                    refine ⟨?_, ?_⟩
                    · have hta : target ∈ a := List.take_subset _ a hh
                      cases hhead with
                      | inl hh2 =>
                        obtain ⟨as, has⟩ := hh2
                        have ha' : List.Pairwise (· ≤ ·) (h :: as) := by
                          rwa [has] at ha
                        rw [has] at hta
                        cases List.mem_cons.mp hta with
                        | inl hh3 => omega
                        | inr hh3 => exact pairwise_head_le ha' target hh3
                      | inr hh2 =>
                        rw [hh2] at hta
                        simp at hta
                    · have hsb := (split_bounds ha mid hgt).1 target hh
                      have hm_a : m = a[mid]! := by
                        rw [hm_def, hw]
                        exact getElem!_append_left a b mid hgt
                      rwa [← hm_a] at hsb
                  | inr ha0 =>
                    have hw_b : h :: t = b := by simp [hw, ha0]
                    have htake : (h :: t).take mid = b.take mid := by
                      simp [hw, ha0]
                    rw [htake] at hh
                    refine ⟨?_, ?_⟩
                    · have htb : target ∈ b := List.take_subset _ b hh
                      rw [← hw_b] at htb
                      cases List.mem_cons.mp htb with
                      | inl hh3 => omega
                      | inr hh3 =>
                        have hb' : List.Pairwise (· ≤ ·) (h :: t) := by
                          rwa [← hw_b] at hb
                        exact pairwise_head_le hb' target hh3
                    · have hlen_b : mid < b.length := by
                        rw [ha0] at hlen_w
                        simp at hlen_w
                        omega
                      have hsb := (split_bounds hb mid hlen_b).1 target hh
                      have hm_b : m = b[mid]! := by
                        rw [hm_def, hw, ha0]
                        exact getElem!_append_right [] b mid (by simp)
                      rwa [← hm_b] at hsb
                obtain ⟨hle1, hle2⟩ := hbounds
                have hdisj : target < h ∨ m ≤ target := by
                  by_contra hc
                  have e1 : h ≤ target := by
                    by_contra hc1
                    exact hc (Or.inl (by omega))
                  have e2 : target < m := by
                    by_contra hc2
                    exact hc (Or.inr (by omega))
                  exact hcond ⟨e1, e2⟩
                cases hdisj with
                | inl hh3 => omega
                | inr hh3 => exact hmt (show m = target by omega)
              refine ⟨fun idx hidx => ?_, fun hn => ?_⟩
              · obtain ⟨h1, h2, h3⟩ := ih_some idx hidx
                refine ⟨?_, by omega, ?_⟩
                · have h4 : idx - base = (idx - (base + mid + 1)) + (mid + 1) := by
                    omega
                  rw [h4, ← getElem!_drop (h :: t) (mid + 1)
                    (idx - (base + mid + 1)) (by omega)]
                  exact h1
                · have h5 : ((h :: t).drop (mid + 1)).length =
                      (h :: t).length - (mid + 1) := List.length_drop
                  omega
              · intro hmem
                have htd := (mem_take_or_drop target (h :: t) mid).mpr hmem
                cases htd with
                | inl hh => exact b2b_excl hh
                | inr hh =>
                  rw [hdrop] at hh
                  cases List.mem_cons.mp hh with
                  | inl hh2 => exact hmt hh2.symm
                  | inr hh2 => exact ih_none hn hh2
          · rw [ite_eq_right hhm]
            by_cases hmh : m < h
            · rw [ite_eq_left hmh]
              have hB3case : a.length ≤ mid := by
                by_contra hcon
                have hgt : mid < a.length := by omega
                have hm_a : m = a[mid]! := by
                  rw [hm_def, hw]
                  exact getElem!_append_left a b mid hgt
                have hma : m ∈ a := by
                  rw [hm_a]
                  exact getElem!_mem hgt
                have hle : h ≤ m := by
                  cases hhead with
                  | inl hh2 =>
                    obtain ⟨as, has⟩ := hh2
                    have ha' : List.Pairwise (· ≤ ·) (h :: as) := by
                      rwa [has] at ha
                    rw [has] at hma
                    cases List.mem_cons.mp hma with
                    | inl hh3 => omega
                    | inr hh3 => exact pairwise_head_le ha' m hh3
                  | inr hh2 =>
                    exfalso
                    have h6 : a.length = 0 := by simp [hh2]
                    omega
                omega
              have hm_b : m = b[mid - a.length]! := by
                rw [hm_def, hw]
                exact getElem!_append_right a b mid hB3case
              have hj_lt : mid - a.length < b.length := by omega
              by_cases hcond : m < target ∧ target ≤ ((h :: t).drop mid).getLast!
              · rw [ite_eq_left hcond]
                have hfuel_drop : ((h :: t).drop (mid + 1)).length ≤ fuel := by
                  rw [List.length_drop]
                  omega
                obtain ⟨ih_some, ih_none⟩ := ih ((h :: t).drop (mid + 1))
                  (base + mid + 1) hfuel_drop hrot_drop
                have b3a_excl : target ∈ (h :: t).take mid →
                    target ∈ (h :: t).drop (mid + 1) := by
                  intro hmem
                  have htake : (h :: t).take mid = a ++ b.take (mid - a.length) := by
                    rw [hw, List.take_append, List.take_of_length_le hB3case]
                  rw [htake] at hmem
                  cases List.mem_append.mp hmem with
                  | inl hy =>
                    have hle_h : h ≤ target := by
                      cases hhead with
                      | inl hh2 =>
                        obtain ⟨as, has⟩ := hh2
                        have ha' : List.Pairwise (· ≤ ·) (h :: as) := by
                          rwa [has] at ha
                        rw [has] at hy
                        cases List.mem_cons.mp hy with
                        | inl hh3 => omega
                        | inr hh3 => exact pairwise_head_le ha' target hh3
                      | inr hh2 =>
                        rw [hh2] at hy
                        simp at hy
                    have hdm : (h :: t).drop mid = b.drop (mid - a.length) := by
                      simp [hw, List.drop_append, List.drop_of_length_le hB3case]
                    have hlast_mem : ((h :: t).drop mid).getLast! ∈ b := by
                      have hne : b.drop (mid - a.length) ≠ [] := by
                        rw [← hdm]
                        intro hcon2
                        have hl : ((h :: t).drop mid).length =
                            (h :: t).length - mid := List.length_drop
                        have hl2 : ((h :: t).drop mid).length = 0 := by
                          simp [hcon2]
                        omega
                      rw [hdm]
                      exact List.drop_subset _ b (getLast!_mem hne)
                    have hlast_le : ((h :: t).drop mid).getLast! ≤ h := by
                      cases hh_mem_a with
                      | inl hh => exact hba _ hlast_mem h hh
                      | inr hh =>
                        rw [hh] at hy
                        simp at hy
                    have hteq : target = ((h :: t).drop mid).getLast! := by omega
                    rw [hteq]
                    by_cases hrest : (h :: t).drop (mid + 1) = []
                    · exfalso
                      have hlast_m : ((h :: t).drop mid).getLast! = m := by
                        rw [hdrop, hrest]
                        rfl
                      omega
                    · have hgl : ((h :: t).drop mid).getLast! =
                          ((h :: t).drop (mid + 1)).getLast! := by
                        rw [hdrop]
                        cases hrest' : (h :: t).drop (mid + 1) with
                        | nil => exact absurd hrest' hrest
                        | cons z zs => rfl
                      rw [hgl]
                      exact getLast!_mem hrest
                  | inr hy =>
                    have hsb := (split_bounds hb (mid - a.length) hj_lt).1 target hy
                    exfalso
                    omega
                refine ⟨fun idx hidx => ?_, fun hn => ?_⟩
                · obtain ⟨h1, h2, h3⟩ := ih_some idx hidx
                  refine ⟨?_, by omega, ?_⟩
                  · have h4 : idx - base = (idx - (base + mid + 1)) + (mid + 1) := by
                      omega
                    rw [h4, ← getElem!_drop (h :: t) (mid + 1)
                      (idx - (base + mid + 1)) (by omega)]
                    exact h1
                  · have h5 : ((h :: t).drop (mid + 1)).length =
                        (h :: t).length - (mid + 1) := List.length_drop
                    omega
                · intro hmem
                  have htd := (mem_take_or_drop target (h :: t) mid).mpr hmem
                  cases htd with
                  | inl hh => exact ih_none hn (b3a_excl hh)
                  | inr hh =>
                    rw [hdrop] at hh
                    cases List.mem_cons.mp hh with
                    | inl hh2 => exact hmt hh2.symm
                    | inr hh2 => exact ih_none hn hh2
              · rw [ite_eq_right hcond]
                have hfuel_take : ((h :: t).take mid).length ≤ fuel := by
                  rw [List.length_take]
                  omega
                obtain ⟨ih_some, ih_none⟩ := ih ((h :: t).take mid) base hfuel_take
                  hrot_take
                have b3b_excl : target ∈ (h :: t).drop (mid + 1) → False := by
                  intro hmem
                  have hge : m ≤ target := by
                    have hdm1 : (h :: t).drop (mid + 1) =
                        b.drop (mid + 1 - a.length) := by
                      simp [hw, List.drop_append,
                        List.drop_of_length_le (show a.length ≤ mid + 1 by omega)]
                    rw [hdm1] at hmem
                    have h2 : mid + 1 - a.length = (mid - a.length) + 1 := by omega
                    rw [h2] at hmem
                    have hsb := (split_bounds hb (mid - a.length) hj_lt).2 target hmem
                    rwa [← hm_b] at hsb
                  have hle : target ≤ ((h :: t).drop mid).getLast! := by
                    have hp : List.Pairwise (· ≤ ·) ((h :: t).drop mid) := by
                      have hdm : (h :: t).drop mid = b.drop (mid - a.length) := by
                        simp [hw, List.drop_append, List.drop_of_length_le hB3case]
                      rw [hdm]
                      exact hb.sublist (List.drop_sublist _ b)
                    have hmem2 : target ∈ (h :: t).drop mid := by
                      rw [hdrop]
                      exact List.Mem.tail m hmem
                    exact pairwise_le_getLast! hp hmem2
                  have hdisj : target ≤ m ∨
                      ((h :: t).drop mid).getLast! < target := by
                    by_contra hc
                    have e1 : m < target := by
                      by_contra hc1
                      exact hc (Or.inl (by omega))
                    have e2 : target ≤ ((h :: t).drop mid).getLast! := by
                      by_contra hc2
                      exact hc (Or.inr (by omega))
                    exact hcond ⟨e1, e2⟩
                  cases hdisj with
                  | inl hh3 => exact hmt (show m = target by omega)
                  | inr hh3 => omega
                refine ⟨fun idx hidx => ?_, fun hn => ?_⟩
                · obtain ⟨h1, h2, h3⟩ := ih_some idx hidx
                  refine ⟨?_, h2, ?_⟩
                  · rwa [getElem!_take (h :: t) mid (idx - base) h3] at h1
                  · have h4 : ((h :: t).take mid).length ≤ (h :: t).length := by
                      rw [List.length_take]
                      omega
                    omega
                · intro hmem
                  have htd := (mem_take_or_drop target (h :: t) mid).mpr hmem
                  cases htd with
                  | inl hh => exact ih_none hn hh
                  | inr hh =>
                    rw [hdrop] at hh
                    cases List.mem_cons.mp hh with
                    | inl hh2 => exact hmt hh2.symm
                    | inr hh2 => exact b3b_excl hh2
            · rw [ite_eq_right hmh]
              have hhm_eq : h = m := by omega
              have hfuel_t : t.length ≤ fuel := by omega
              obtain ⟨ih_some, ih_none⟩ := ih t (base + 1) hfuel_t hrot_tail
              refine ⟨fun idx hidx => ?_, fun hn => ?_⟩
              · obtain ⟨h1, h2, h3⟩ := ih_some idx hidx
                refine ⟨?_, by omega, by omega⟩
                · have h4 : idx - base = (idx - (base + 1)) + 1 := by omega
                  rw [h4, List.getElem!_cons_succ]
                  exact h1
              · intro hmem
                cases List.mem_cons.mp hmem with
                | inl hh2 => exact hmt (hh2.trans hhm_eq).symm
                | inr hh2 => exact ih_none hn hh2
      exact key _ _ rfl rfl

/-- The specification at the entry point (base offset `0`). -/
theorem searchInRotatedArray_spec (arr : RotatedSortedArray) (target : Nat)
    (hrot : RotatedSorted arr.arr) :
    (∀ idx, searchInRotatedArray arr target = some idx →
      arr.arr[idx]! = target ∧ idx < arr.arr.length) ∧
    (searchInRotatedArray arr target = none → target ∉ arr.arr) := by
  obtain ⟨h1, h2⟩ := rotatedSearchBounded_spec arr.arr.length arr.arr target 0
    (Nat.le_refl _) hrot
  refine ⟨fun idx hidx => ?_, fun hn => h2 hn⟩
  obtain ⟨h3, -, h4⟩ := h1 idx hidx
  exact ⟨by rwa [Nat.sub_zero] at h3, by rwa [Nat.sub_zero] at h4⟩

/-- The draft's statement, repaired as recorded in the module doc. -/
theorem searchInRotatedArray_correctness (arr : RotatedSortedArray)
    (target : Nat) (hrot : RotatedSorted arr.arr) :
    match searchInRotatedArray arr target with
    | some idx => arr.arr[idx]! = target ∧ idx < arr.arr.length
    | none => target ∉ arr.arr := by
  obtain ⟨h1, h2⟩ := searchInRotatedArray_spec arr target hrot
  cases hr : searchInRotatedArray arr target with
  | some idx => exact h1 idx hr
  | none => exact h2 hr

end AxiomCode
