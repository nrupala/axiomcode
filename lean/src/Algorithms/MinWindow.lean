import Spec
import Tactics

/-!
# Minimum window substring (brute-force form)

The minimum window substring problem: given a text and a pattern,
find the shortest contiguous window of the text whose multiset of
symbols covers the pattern's multiset — every symbol occurs in the
window at least as often as in the pattern. This entry works over
`List Nat` (symbols as naturals), a window is a pair `(start,
length)`, and cover is stated with `List.count`:
`Covers pat win := ∀ x ∈ pat, List.count x pat ≤ List.count x win`
(equivalently for all symbols whatsoever, `covers_iff`).

The search is the brute-force verified form: `windowList`
enumerates every in-bounds window, the covering ones are kept,
and `bestOf` selects a shortest one. The headline theorems
characterize the result exactly: `minWindowSubstring_eq_some` (a
returned window is valid — in bounds and covering — and no valid
window is shorter; this is the draft's direction, proved) and
`minWindowSubstring_eq_none` (nothing is returned if and only if
no covering window exists — the direction the draft omitted), with
completeness `minWindowSubstring_complete` as a corollary. The
classical two-pointer sliding-window algorithm is a named
non-goal of this entry: the entry certifies the brute-force search
against the specification any optimized version must also meet.

## Draft defect record (promotion standard: defect + counterexample)

The draft (`lean/drafts/minwindowsubstring_correctness.lean`) did
not elaborate and, read as charitably as possible, certifies
nothing. `Window` was a fieldless structure, so the statement's
`w.length` names a projection that does not exist; `isValidWindow`
and `minWindowSubstring` were written with `:=` and no body; and
the theorem's `w` is unbound in the source. Even repaired
mechanically, the statement covers only one direction — *if* the
function returns `some w`, then `w` is valid and shortest — and
says nothing about the `none` case. That direction alone is
vacuously satisfiable by a function that never returns anything:
for text `= [0]` and pattern `= [0]` the window `(0, 1)` covers,
so a correct search must return a window, yet the draft's
statement is consistent with `minWindowSubstring` returning
`none` on every input. And `isValidWindow`, an uninterpreted
`Bool`, is given no stated relation to covering the pattern at
all.

## Repair (shape preserved)

The draft's function name is kept, and its validity notion is
kept as `IsValidWindow` — a window is a concrete pair
`(start, length)`, valid when it is in bounds and its contents
cover the pattern. The draft's direction is proved as
`minWindowSubstring_eq_some`, and the missing direction is
supplied: `minWindowSubstring_eq_none` and
`minWindowSubstring_complete`.
-/

namespace AxiomCode

/-- Multiset cover: every symbol of the pattern occurs in the
window at least as often as in the pattern. -/
abbrev Covers (pat win : List Nat) : Prop :=
  ∀ x ∈ pat, List.count x pat ≤ List.count x win

/-- Cover, stated over all symbols rather than the pattern's
members only: the two forms agree because a symbol outside the
pattern has count `0` there. -/
theorem covers_iff (pat win : List Nat) :
    Covers pat win ↔ ∀ x, List.count x pat ≤ List.count x win := by
  constructor
  · intro h x
    by_cases hx : x ∈ pat
    · exact h x hx
    · rw [List.count_eq_zero_of_not_mem hx]
      exact Nat.zero_le _
  · intro h x _
    exact h x

/-- A window of the text is valid when it lies inside the text
and its contents cover the pattern. -/
def IsValidWindow (text pat : List Nat) (w : Nat × Nat) : Prop :=
  w.1 + w.2 ≤ text.length ∧ Covers pat ((text.drop w.1).take w.2)

/-- Every in-bounds window `(start, length)` of the text. -/
def windowList (text : List Nat) : List (Nat × Nat) :=
  (List.range (text.length + 1)).flatMap (fun i =>
    (List.range (text.length + 1 - i)).map (fun len => (i, len)))

/-- The windows enumerated are exactly the in-bounds ones. -/
theorem mem_windowList {text : List Nat} {w : Nat × Nat} :
    w ∈ windowList text ↔ w.1 + w.2 ≤ text.length := by
  unfold windowList
  rw [List.mem_flatMap]
  constructor
  · rintro ⟨i, hi, hmem⟩
    rw [List.mem_range] at hi
    rw [List.mem_map] at hmem
    obtain ⟨len, hlen, hpair⟩ := hmem
    rw [List.mem_range] at hlen
    have h1 : w.1 = i := (congrArg Prod.fst hpair).symm
    have h2 : w.2 = len := (congrArg Prod.snd hpair).symm
    omega
  · intro h
    refine ⟨w.1, List.mem_range.mpr (by omega), ?_⟩
    exact List.mem_map.mpr ⟨w.2, List.mem_range.mpr (by omega), rfl⟩

/-- Keep the better of the running best and each new window:
strictly shorter wins, ties keep the incumbent. -/
def bestFrom (b : Nat × Nat) : List (Nat × Nat) → Nat × Nat
  | [] => b
  | w :: ws => bestFrom (if w.2 < b.2 then w else b) ws

/-- The selected window is always one of the candidates. -/
theorem bestFrom_mem : ∀ (b : Nat × Nat) (ws : List (Nat × Nat)),
    bestFrom b ws ∈ b :: ws := by
  intro b ws
  induction ws generalizing b with
  | nil => exact List.mem_cons_self
  | cons w ws ih =>
    by_cases h : w.2 < b.2
    · have e : bestFrom b (w :: ws) = bestFrom w ws := by
        simp only [bestFrom, if_pos h]
      rw [e]
      exact List.mem_cons_of_mem b (ih w)
    · have e : bestFrom b (w :: ws) = bestFrom b ws := by
        simp only [bestFrom, if_neg h]
      rw [e]
      have ihb := ih b
      rcases List.mem_cons.mp ihb with heq | hmem
      · rw [heq]
        exact List.mem_cons_self
      · exact List.mem_cons_of_mem b (List.mem_cons_of_mem w hmem)

/-- The selected window is no longer than any candidate. -/
theorem bestFrom_min : ∀ (b : Nat × Nat) (ws : List (Nat × Nat)) (y : Nat × Nat),
    y ∈ b :: ws → (bestFrom b ws).2 ≤ y.2 := by
  intro b ws
  induction ws generalizing b with
  | nil =>
    intro y hy
    rcases List.mem_cons.mp hy with rfl | hmem
    · exact Nat.le_refl _
    · cases hmem
  | cons w ws ih =>
    intro y hy
    by_cases h : w.2 < b.2
    · have e : bestFrom b (w :: ws) = bestFrom w ws := by
        simp only [bestFrom, if_pos h]
      rw [e]
      have hwb : (bestFrom w ws).2 ≤ w.2 := ih w w (List.mem_cons_self)
      have hww : (bestFrom w ws).2 ≤ b.2 := Nat.le_trans hwb (Nat.le_of_lt h)
      rcases List.mem_cons.mp hy with rfl | hy'
      · exact hww
      · rcases List.mem_cons.mp hy' with rfl | hy''
        · exact hwb
        · exact ih w y (List.mem_cons_of_mem w hy'')
    · have e : bestFrom b (w :: ws) = bestFrom b ws := by
        simp only [bestFrom, if_neg h]
      rw [e]
      have hbb : (bestFrom b ws).2 ≤ b.2 := ih b b (List.mem_cons_self)
      have hbw : (bestFrom b ws).2 ≤ w.2 := by
        have hwb : (bestFrom b ws).2 ≤ b.2 := hbb
        have hle : b.2 ≤ w.2 := by omega
        exact Nat.le_trans hwb hle
      rcases List.mem_cons.mp hy with rfl | hy'
      · exact hbb
      · rcases List.mem_cons.mp hy' with rfl | hy''
        · exact hbw
        · exact ih b y (List.mem_cons_of_mem b hy'')

/-- A shortest window of the list, if the list is nonempty. -/
def bestOf (l : List (Nat × Nat)) : Option (Nat × Nat) :=
  match l with
  | [] => none
  | w :: ws => some (bestFrom w ws)

theorem bestOf_eq_none {l : List (Nat × Nat)} : bestOf l = none ↔ l = [] := by
  cases l with
  | nil => exact ⟨fun _ => rfl, fun _ => rfl⟩
  | cons w ws =>
    constructor
    · intro h
      have e : bestOf (w :: ws) = some (bestFrom w ws) := rfl
      rw [e] at h
      cases h
    · intro h
      cases h

theorem bestOf_mem {l : List (Nat × Nat)} {b : Nat × Nat} :
    bestOf l = some b → b ∈ l := by
  cases l with
  | nil =>
    intro h
    have e : bestOf ([] : List (Nat × Nat)) = none := rfl
    rw [e] at h
    cases h
  | cons w ws =>
    intro h
    have e : bestOf (w :: ws) = some (bestFrom w ws) := rfl
    rw [e] at h
    have hb : bestFrom w ws = b := Option.some.inj h
    rw [← hb]
    exact bestFrom_mem w ws

theorem bestOf_min {l : List (Nat × Nat)} {b : Nat × Nat} (h : bestOf l = some b)
    (y : Nat × Nat) (hy : y ∈ l) : b.2 ≤ y.2 := by
  cases l with
  | nil => cases hy
  | cons w ws =>
    have e : bestOf (w :: ws) = some (bestFrom w ws) := rfl
    rw [e] at h
    have hb : bestFrom w ws = b := Option.some.inj h
    rw [← hb]
    exact bestFrom_min w ws y hy

/-- The minimum window substring: a shortest window of the text
covering the pattern, or `none` when no window covers it. -/
def minWindowSubstring (text pat : List Nat) : Option (Nat × Nat) :=
  bestOf ((windowList text).filter (fun w =>
    decide (Covers pat ((text.drop w.1).take w.2))))

/-- The draft's direction, proved: a returned window is valid,
and no valid window is shorter. -/
theorem minWindowSubstring_eq_some {text pat : List Nat} {w : Nat × Nat}
    (h : minWindowSubstring text pat = some w) :
    IsValidWindow text pat w ∧ ∀ w', IsValidWindow text pat w' → w.2 ≤ w'.2 := by
  have hmem := bestOf_mem h
  rw [List.mem_filter] at hmem
  obtain ⟨hwlist, hcov⟩ := hmem
  have hcov' : Covers pat ((text.drop w.1).take w.2) := of_decide_eq_true hcov
  have hw : IsValidWindow text pat w := ⟨mem_windowList.mp hwlist, hcov'⟩
  refine ⟨hw, ?_⟩
  intro w' hw'
  have hmem' : w' ∈ (windowList text).filter (fun w =>
      decide (Covers pat ((text.drop w.1).take w.2))) := by
    rw [List.mem_filter]
    refine ⟨mem_windowList.mpr hw'.1, ?_⟩
    rw [decide_eq_true_eq]
    exact hw'.2
  exact bestOf_min h w' hmem'

/-- The direction the draft omitted: nothing is returned if and
only if no covering window exists. -/
theorem minWindowSubstring_eq_none {text pat : List Nat} :
    minWindowSubstring text pat = none ↔ ¬ ∃ w, IsValidWindow text pat w := by
  constructor
  · intro h ⟨w, hw⟩
    have hmem : w ∈ (windowList text).filter (fun w =>
        decide (Covers pat ((text.drop w.1).take w.2))) := by
      rw [List.mem_filter]
      refine ⟨mem_windowList.mpr hw.1, ?_⟩
      rw [decide_eq_true_eq]
      exact hw.2
    have hnil : (windowList text).filter (fun w =>
        decide (Covers pat ((text.drop w.1).take w.2))) = [] :=
      bestOf_eq_none.mp h
    rw [hnil] at hmem
    cases hmem
  · intro h
    unfold minWindowSubstring
    rw [bestOf_eq_none, List.eq_nil_iff_forall_not_mem]
    intro w hwmem
    rw [List.mem_filter] at hwmem
    obtain ⟨hwlist, hcov⟩ := hwmem
    have hcov' : Covers pat ((text.drop w.1).take w.2) := of_decide_eq_true hcov
    exact h ⟨w, mem_windowList.mp hwlist, hcov'⟩

/-- Completeness: when a covering window exists, one is
returned. -/
theorem minWindowSubstring_complete {text pat : List Nat}
    (h : ∃ w, IsValidWindow text pat w) :
    ∃ w, minWindowSubstring text pat = some w := by
  by_cases hnone : minWindowSubstring text pat = none
  · rw [minWindowSubstring_eq_none] at hnone
    exact absurd h hnone
  · exact match h2 : minWindowSubstring text pat with
      | none => absurd h2 hnone
      | some w => ⟨w, rfl⟩

/-- Sanity: with an empty pattern a window is always returned,
and it has length `0`. -/
theorem minWindowSubstring_empty_pat (text : List Nat) :
    ∃ w, minWindowSubstring text [] = some w ∧ w.2 = 0 := by
  have hvalid : IsValidWindow text [] (0, 0) := by
    refine ⟨Nat.zero_le _, ?_⟩
    intro x hx
    cases hx
  obtain ⟨w, hw⟩ := minWindowSubstring_complete ⟨(0, 0), hvalid⟩
  refine ⟨w, hw, ?_⟩
  have hmin := (minWindowSubstring_eq_some hw).2 (0, 0) hvalid
  have h2 : (0, 0).2 = (0 : Nat) := rfl
  omega

end AxiomCode
