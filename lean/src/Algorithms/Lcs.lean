import Spec
import Tactics

/-!
# Longest common subsequence

The length of the longest common subsequence of two lists, computed
by the classical dynamic-programming recurrence (`lcs`), together
with the extracting algorithm `longestCommonSubseq`, which produces
an actual longest common subsequence. The specification is the
inductive `Subseq` relation (subsequencehood), and the headline
theorem `lcs_correctness` states the draft's equation — the computed
length is the length of the produced sequence — plus the two facts
that make it a correctness statement: the produced sequence is a
common subsequence of both inputs, and no common subsequence is
longer.

Both recursions are fuelled (`lcsAux`, `lcsSeqAux`) because their
recursive calls shrink different arguments; fuel irrelevance lemmas
show the values are independent of the fuel once it exceeds the
combined length, so the public functions satisfy the unfuelled
recurrences. The extractor chooses its branch by comparing the two
candidate lengths through `lcsAux` at the same fuel, which at
adequate fuel are the true `lcs` values.

## Draft defect record (promotion standard: defect + counterexample)

The draft (`lean/drafts/lcs_correctness.lean`) did not elaborate:
`lcs` was written with `:=` and no body; the headline statement
`lcs xs ys = length (longestCommonSubseq xs ys)` references
`longestCommonSubseq`, a function defined nowhere in the draft or
the tree, and a bare `length` that resolves to nothing in scope;
`LCSState` was a fieldless structure the statement never used.

Even read charitably, the shape certifies nothing until a
sequence-producing function exists and is proved to produce a common
subsequence of maximum length: an equation against an unspecified
function's length constrains neither side.

## Repair (shape preserved)

The draft's equation is kept as the headline's first conjunct, with
the draft's own function name `longestCommonSubseq` now denoting the
authored extracting algorithm, and the two facts that give the
equation its content proved alongside: the produced sequence is a
common subsequence (`Subseq` of both inputs), and every common
subsequence has length at most `lcs xs ys`.
-/

namespace AxiomCode

/-- Fuelled worker for `lcs`. A fuel of zero on nonempty input
returns `0`, a value the adequacy lemma `lcsAux_irrel` shows is
never seen at adequate fuel. -/
def lcsAux : Nat → List Char → List Char → Nat
  | 0, _, _ => 0
  | _ + 1, [], _ => 0
  | _ + 1, _, [] => 0
  | f + 1, a :: xs, b :: ys =>
      if a = b then lcsAux f xs ys + 1
      else max (lcsAux f xs (b :: ys)) (lcsAux f (a :: xs) ys)

/-- The length of the longest common subsequence of `xs` and `ys`. -/
def lcs (xs ys : List Char) : Nat :=
  lcsAux (xs.length + ys.length + 1) xs ys

theorem lcsAux_succ_nil_left (f : Nat) (ys : List Char) :
    lcsAux (f + 1) [] ys = 0 := rfl

theorem lcsAux_succ_nil_right (f : Nat) (xs : List Char) :
    lcsAux (f + 1) xs [] = 0 := by cases xs <;> rfl

theorem lcsAux_succ_cons_cons (f : Nat) (a : Char) (xs : List Char)
    (b : Char) (ys : List Char) :
    lcsAux (f + 1) (a :: xs) (b :: ys) =
      if a = b then lcsAux f xs ys + 1
      else max (lcsAux f xs (b :: ys)) (lcsAux f (a :: xs) ys) := rfl

/-- Fuel irrelevance for the length worker. -/
theorem lcsAux_irrel : ∀ (f₁ f₂ : Nat) (xs ys : List Char),
    xs.length + ys.length < f₁ → xs.length + ys.length < f₂ →
    lcsAux f₁ xs ys = lcsAux f₂ xs ys := by
  intro f₁
  induction f₁ with
  | zero => intro f₂ xs ys h₁ h₂; exact (Nat.not_lt_zero _ h₁).elim
  | succ f ih =>
    intro f₂ xs ys h₁ h₂
    cases f₂ with
    | zero => exact (Nat.not_lt_zero _ h₂).elim
    | succ g =>
      cases xs with
      | nil =>
        rw [lcsAux_succ_nil_left, lcsAux_succ_nil_left]
      | cons a xs =>
        cases ys with
        | nil =>
          rw [lcsAux_succ_nil_right, lcsAux_succ_nil_right]
        | cons b ys =>
          simp only [List.length_cons] at h₁ h₂
          by_cases hab : a = b
          · rw [lcsAux_succ_cons_cons, lcsAux_succ_cons_cons, if_pos hab, if_pos hab]
            rw [ih g xs ys (by omega) (by omega)]
          · rw [lcsAux_succ_cons_cons, lcsAux_succ_cons_cons, if_neg hab, if_neg hab]
            rw [ih g xs (b :: ys) (by simp only [List.length_cons]; omega)
                (by simp only [List.length_cons]; omega),
              ih g (a :: xs) ys (by simp only [List.length_cons]; omega)
                (by simp only [List.length_cons]; omega)]

/-- At any adequate fuel the worker computes `lcs`. -/
theorem lcsAux_eq_lcs (f : Nat) (xs ys : List Char)
    (hf : xs.length + ys.length < f) :
    lcsAux f xs ys = lcs xs ys :=
  lcsAux_irrel f (xs.length + ys.length + 1) xs ys hf (by omega)

theorem lcs_nil_left (ys : List Char) : lcs [] ys = 0 := rfl

theorem lcs_nil_right (xs : List Char) : lcs xs [] = 0 := by
  cases xs <;> rfl

/-- The unfuelled recurrence: matching heads extend a longest common
subsequence of the tails; differing heads drop one side's head,
whichever keeps more. -/
theorem lcs_cons_cons (a : Char) (xs : List Char) (b : Char) (ys : List Char) :
    lcs (a :: xs) (b :: ys) =
      if a = b then lcs xs ys + 1
      else max (lcs xs (b :: ys)) (lcs (a :: xs) ys) := by
  have e : (a :: xs).length + (b :: ys).length + 1 = (xs.length + ys.length + 2) + 1 := by
    simp only [List.length_cons]; omega
  have h1 : lcs (a :: xs) (b :: ys) =
      if a = b then lcsAux (xs.length + ys.length + 2) xs ys + 1
      else max (lcsAux (xs.length + ys.length + 2) xs (b :: ys))
        (lcsAux (xs.length + ys.length + 2) (a :: xs) ys) := by
    show lcsAux ((a :: xs).length + (b :: ys).length + 1) (a :: xs) (b :: ys) = _
    rw [e]
    exact lcsAux_succ_cons_cons _ _ _ _ _
  rw [h1,
    lcsAux_eq_lcs _ xs ys (by omega),
    lcsAux_eq_lcs _ xs (b :: ys) (by simp only [List.length_cons]; omega),
    lcsAux_eq_lcs _ (a :: xs) ys (by simp only [List.length_cons]; omega)]

/-- Subsequencehood: `Subseq s l` says `s` arises from `l` by
deleting chars — built by keeping a head (`cons`) or dropping it
(`skip`). -/
inductive Subseq : List Char → List Char → Prop
  | nil : Subseq [] l
  | cons (a : Char) : Subseq s l → Subseq (a :: s) (a :: l)
  | skip (a : Char) : Subseq s l → Subseq s (a :: l)

theorem subseq_nil_right {s : List Char} : Subseq s [] → s = [] := by
  intro h
  cases h with
  | nil => rfl

/-- Inversion at a cons target: a cons-headed subsequence either
keeps the head (and continues in the tail) or drops it. -/
theorem subseq_cons_cons_inv {c : Char} {s : List Char} {a : Char} {l : List Char} :
    Subseq (c :: s) (a :: l) → (c = a ∧ Subseq s l) ∨ Subseq (c :: s) l := by
  intro h
  cases h with
  | cons a' h' => exact Or.inl ⟨rfl, h'⟩
  | skip a' h' => exact Or.inr h'

/-- Dropping the head of a subsequence: if `c :: s` embeds in `l`,
so does `s`. -/
theorem subseq_cons_left_tail (c : Char) (s : List Char) :
    ∀ (l : List Char), Subseq (c :: s) l → Subseq s l := by
  intro l
  induction l with
  | nil => intro h; cases h
  | cons a l ih =>
    intro h
    cases subseq_cons_cons_inv h with
    | inl h' => exact Subseq.skip a h'.2
    | inr h' => exact Subseq.skip a (ih h')

/-- The computed length is at most the first list's length, in
bounded form. -/
theorem lcs_le_length_left_aux : ∀ (k : Nat) (xs ys : List Char),
    xs.length + ys.length ≤ k → lcs xs ys ≤ xs.length := by
  intro k
  induction k with
  | zero =>
    intro xs ys h
    cases xs with
    | nil =>
      cases ys with
      | nil => rw [lcs_nil_left]; exact Nat.zero_le _
      | cons b ys => simp [List.length_cons] at h
    | cons a xs => simp [List.length_cons] at h
  | succ k ih =>
    intro xs ys h
    cases xs with
    | nil => rw [lcs_nil_left]; exact Nat.zero_le _
    | cons a xs =>
      cases ys with
      | nil => rw [lcs_nil_right]; exact Nat.zero_le _
      | cons b ys =>
        simp only [List.length_cons] at h
        by_cases hab : a = b
        · rw [lcs_cons_cons, if_pos hab]
          have ih' := ih xs ys (by omega)
          simp only [List.length_cons]
          omega
        · rw [lcs_cons_cons, if_neg hab]
          have ih1 := ih xs (b :: ys) (by simp only [List.length_cons]; omega)
          have ih2 := ih (a :: xs) ys (by simp only [List.length_cons]; omega)
          simp only [List.length_cons] at ih2 ⊢
          omega

/-- The computed length is at most the first list's length. -/
theorem lcs_le_length_left (xs ys : List Char) : lcs xs ys ≤ xs.length :=
  lcs_le_length_left_aux (xs.length + ys.length) xs ys (by omega)

/-- The computed length is at most the second list's length, in
bounded form. -/
theorem lcs_le_length_right_aux : ∀ (k : Nat) (xs ys : List Char),
    xs.length + ys.length ≤ k → lcs xs ys ≤ ys.length := by
  intro k
  induction k with
  | zero =>
    intro xs ys h
    cases xs with
    | nil =>
      cases ys with
      | nil => rw [lcs_nil_left]; exact Nat.zero_le _
      | cons b ys => simp [List.length_cons] at h
    | cons a xs => simp [List.length_cons] at h
  | succ k ih =>
    intro xs ys h
    cases xs with
    | nil => rw [lcs_nil_left]; exact Nat.zero_le _
    | cons a xs =>
      cases ys with
      | nil => rw [lcs_nil_right]; exact Nat.zero_le _
      | cons b ys =>
        simp only [List.length_cons] at h
        by_cases hab : a = b
        · rw [lcs_cons_cons, if_pos hab]
          have ih' := ih xs ys (by omega)
          simp only [List.length_cons]
          omega
        · rw [lcs_cons_cons, if_neg hab]
          have ih1 := ih xs (b :: ys) (by simp only [List.length_cons]; omega)
          have ih2 := ih (a :: xs) ys (by simp only [List.length_cons]; omega)
          simp only [List.length_cons] at ih1 ⊢
          omega

/-- The computed length is at most the second list's length. -/
theorem lcs_le_length_right (xs ys : List Char) : lcs xs ys ≤ ys.length :=
  lcs_le_length_right_aux (xs.length + ys.length) xs ys (by omega)

/-- Monotonicity in the second list, in bounded form: prepending a
char to the target cannot shrink the longest common subsequence. -/
theorem lcs_mono_cons_right_aux : ∀ (k : Nat) (xs ys : List Char),
    xs.length + ys.length ≤ k → ∀ b : Char, lcs xs ys ≤ lcs xs (b :: ys) := by
  intro k
  induction k with
  | zero =>
    intro xs ys h b
    cases xs with
    | nil =>
      cases ys with
      | nil => rw [lcs_nil_left, lcs_nil_left]; exact Nat.zero_le 0
      | cons c ys => simp [List.length_cons] at h
    | cons a xs => simp [List.length_cons] at h
  | succ k ih =>
    intro xs ys h b
    cases xs with
    | nil => rw [lcs_nil_left]; exact Nat.zero_le _
    | cons a xs =>
      cases ys with
      | nil => rw [lcs_nil_right]; exact Nat.zero_le _
      | cons c ys =>
        simp only [List.length_cons] at h
        by_cases hac : a = c
        · have hrL : lcs (a :: xs) (c :: ys) = lcs xs ys + 1 := by
            rw [lcs_cons_cons, if_pos hac]
          by_cases hab : a = b
          · have hrR : lcs (a :: xs) (b :: c :: ys) = lcs xs (c :: ys) + 1 := by
              rw [lcs_cons_cons, if_pos hab]
            rw [hrL, hrR]
            have ih' := ih xs ys (by omega) c
            omega
          · have hrR : lcs (a :: xs) (b :: c :: ys) =
                max (lcs xs (b :: c :: ys)) (lcs (a :: xs) (c :: ys)) := by
              rw [lcs_cons_cons, if_neg hab]
            rw [hrL, hrR, hrL]
            omega
        · have hrL : lcs (a :: xs) (c :: ys) =
              max (lcs xs (c :: ys)) (lcs (a :: xs) ys) := by
            rw [lcs_cons_cons, if_neg hac]
          by_cases hab : a = b
          · have hrR : lcs (a :: xs) (b :: c :: ys) = lcs xs (c :: ys) + 1 := by
              rw [lcs_cons_cons, if_pos hab]
            rw [hrL, hrR]
            have ih1 := ih (a :: xs) ys (by simp only [List.length_cons]; omega) b
            have hrB : lcs (a :: xs) (b :: ys) = lcs xs ys + 1 := by
              rw [lcs_cons_cons, if_pos hab]
            have ih2 := ih xs ys (by omega) c
            omega
          · have hrR : lcs (a :: xs) (b :: c :: ys) =
                max (lcs xs (b :: c :: ys)) (lcs (a :: xs) (c :: ys)) := by
              rw [lcs_cons_cons, if_neg hab]
            rw [hrL, hrR, hrL]
            omega

/-- Monotonicity in the second list: prepending a char to the
target cannot shrink the longest common subsequence. -/
theorem lcs_mono_cons_right (xs ys : List Char) (b : Char) :
    lcs xs ys ≤ lcs xs (b :: ys) :=
  lcs_mono_cons_right_aux (xs.length + ys.length) xs ys (by omega) b

/-- Optimality, in bounded form: every common subsequence has
length at most the computed value. The proof inverts both
subsequence derivations at the heads; the match/drop case analysis
is the classical one, with `lcs_mono_cons_right` closing the
drop/drop differing-heads case. -/
theorem lcs_length_le_aux : ∀ (k : Nat) (xs ys : List Char),
    xs.length + ys.length ≤ k →
    ∀ s : List Char, Subseq s xs → Subseq s ys → s.length ≤ lcs xs ys := by
  intro k
  induction k with
  | zero =>
    intro xs ys h s h1 h2
    cases xs with
    | nil =>
      cases ys with
      | nil =>
        obtain rfl := subseq_nil_right h1
        rw [lcs_nil_left]
        exact Nat.zero_le 0
      | cons b ys => simp [List.length_cons] at h
    | cons a xs => simp [List.length_cons] at h
  | succ k ih =>
    intro xs ys h s h1 h2
    cases xs with
    | nil =>
      obtain rfl := subseq_nil_right h1
      rw [lcs_nil_left]
      exact Nat.zero_le 0
    | cons a xs =>
      cases ys with
      | nil =>
        obtain rfl := subseq_nil_right h2
        rw [lcs_nil_right]
        exact Nat.zero_le 0
      | cons b ys =>
        simp only [List.length_cons] at h
        cases s with
        | nil => exact Nat.zero_le _
        | cons c s =>
          have linv := subseq_cons_cons_inv h1
          have rinv := subseq_cons_cons_inv h2
          by_cases hab : a = b
          · have hr : lcs (a :: xs) (b :: ys) = lcs xs ys + 1 := by
              rw [lcs_cons_cons, if_pos hab]
            rw [hr]
            cases linv with
            | inl hl =>
              obtain ⟨rfl, hl2⟩ := hl
              cases rinv with
              | inl hr' =>
                obtain ⟨rfl, hr2⟩ := hr'
                have hle := ih xs ys (by omega) s hl2 hr2
                simp only [List.length_cons]
                omega
              | inr hr' =>
                have hle := ih xs ys (by omega) s hl2 (subseq_cons_left_tail c s ys hr')
                simp only [List.length_cons]
                omega
            | inr hl =>
              cases rinv with
              | inl hr' =>
                obtain ⟨rfl, hr2⟩ := hr'
                have hle := ih xs ys (by omega) s (subseq_cons_left_tail c s xs hl) hr2
                simp only [List.length_cons]
                omega
              | inr hr' =>
                have hle := ih xs ys (by omega) (c :: s) hl hr'
                omega
          · have hr : lcs (a :: xs) (b :: ys) =
                max (lcs xs (b :: ys)) (lcs (a :: xs) ys) := by
              rw [lcs_cons_cons, if_neg hab]
            rw [hr]
            cases linv with
            | inl hl =>
              obtain ⟨rfl, hl2⟩ := hl
              cases rinv with
              | inl hr' =>
                obtain ⟨rfl, hr2⟩ := hr'
                exact (hab rfl).elim
              | inr hr' =>
                have hle := ih (c :: xs) ys (by simp only [List.length_cons]; omega)
                  (c :: s) (Subseq.cons c hl2) hr'
                omega
            | inr hl =>
              cases rinv with
              | inl hr' =>
                obtain ⟨rfl, hr2⟩ := hr'
                have hle := ih xs (c :: ys) (by simp only [List.length_cons]; omega)
                  (c :: s) hl (Subseq.cons c hr2)
                omega
              | inr hr' =>
                have hle := ih xs ys (by omega) (c :: s) hl hr'
                have hmono := lcs_mono_cons_right xs ys b
                omega

/-- Optimality: every common subsequence has length at most the
computed value. -/
theorem lcs_length_le (xs ys : List Char) (s : List Char) :
    Subseq s xs → Subseq s ys → s.length ≤ lcs xs ys :=
  lcs_length_le_aux (xs.length + ys.length) xs ys (by omega) s

/-- Fuelled worker for `longestCommonSubseq`. At differing heads it
follows whichever side keeps the larger `lcsAux` value at the same
fuel — at adequate fuel those are the true `lcs` values, so the
chosen branch attains the maximum in `lcs`'s recurrence. -/
def lcsSeqAux : Nat → List Char → List Char → List Char
  | 0, _, _ => []
  | _ + 1, [], _ => []
  | _ + 1, _, [] => []
  | f + 1, a :: xs, b :: ys =>
      if a = b then a :: lcsSeqAux f xs ys
      else if lcsAux f (a :: xs) ys ≤ lcsAux f xs (b :: ys)
        then lcsSeqAux f xs (b :: ys)
        else lcsSeqAux f (a :: xs) ys

/-- A longest common subsequence of `xs` and `ys`, produced by the
dynamic program (its length is `lcs xs ys`; see `lcs_correctness`). -/
def longestCommonSubseq (xs ys : List Char) : List Char :=
  lcsSeqAux (xs.length + ys.length + 1) xs ys

theorem lcsSeqAux_succ_nil_left (f : Nat) (ys : List Char) :
    lcsSeqAux (f + 1) [] ys = [] := rfl

theorem lcsSeqAux_succ_nil_right (f : Nat) (xs : List Char) :
    lcsSeqAux (f + 1) xs [] = [] := by cases xs <;> rfl

theorem lcsSeqAux_succ_cons_cons (f : Nat) (a : Char) (xs : List Char)
    (b : Char) (ys : List Char) :
    lcsSeqAux (f + 1) (a :: xs) (b :: ys) =
      if a = b then a :: lcsSeqAux f xs ys
      else if lcsAux f (a :: xs) ys ≤ lcsAux f xs (b :: ys)
        then lcsSeqAux f xs (b :: ys)
        else lcsSeqAux f (a :: xs) ys := rfl

/-- Fuel irrelevance for the extractor. The branch condition is
rewritten through `lcsAux_irrel` first, so both fuels face the same
comparison. -/
theorem lcsSeqAux_irrel : ∀ (f₁ f₂ : Nat) (xs ys : List Char),
    xs.length + ys.length < f₁ → xs.length + ys.length < f₂ →
    lcsSeqAux f₁ xs ys = lcsSeqAux f₂ xs ys := by
  intro f₁
  induction f₁ with
  | zero => intro f₂ xs ys h₁ h₂; exact (Nat.not_lt_zero _ h₁).elim
  | succ f ih =>
    intro f₂ xs ys h₁ h₂
    cases f₂ with
    | zero => exact (Nat.not_lt_zero _ h₂).elim
    | succ g =>
      cases xs with
      | nil =>
        rw [lcsSeqAux_succ_nil_left, lcsSeqAux_succ_nil_left]
      | cons a xs =>
        cases ys with
        | nil =>
          rw [lcsSeqAux_succ_nil_right, lcsSeqAux_succ_nil_right]
        | cons b ys =>
          simp only [List.length_cons] at h₁ h₂
          by_cases hab : a = b
          · rw [lcsSeqAux_succ_cons_cons, lcsSeqAux_succ_cons_cons, if_pos hab, if_pos hab]
            rw [ih g xs ys (by omega) (by omega)]
          · rw [lcsSeqAux_succ_cons_cons, lcsSeqAux_succ_cons_cons, if_neg hab, if_neg hab,
              lcsAux_irrel f g (a :: xs) ys (by simp only [List.length_cons]; omega)
                (by simp only [List.length_cons]; omega),
              lcsAux_irrel f g xs (b :: ys) (by simp only [List.length_cons]; omega)
                (by simp only [List.length_cons]; omega)]
            by_cases hc : lcsAux g (a :: xs) ys ≤ lcsAux g xs (b :: ys)
            · rw [if_pos hc, if_pos hc]
              exact ih g xs (b :: ys) (by simp only [List.length_cons]; omega)
                (by simp only [List.length_cons]; omega)
            · rw [if_neg hc, if_neg hc]
              exact ih g (a :: xs) ys (by simp only [List.length_cons]; omega)
                (by simp only [List.length_cons]; omega)

/-- At any adequate fuel the extractor computes
`longestCommonSubseq`. -/
theorem lcsSeqAux_eq_longestCommonSubseq (f : Nat) (xs ys : List Char)
    (hf : xs.length + ys.length < f) :
    lcsSeqAux f xs ys = longestCommonSubseq xs ys :=
  lcsSeqAux_irrel f (xs.length + ys.length + 1) xs ys hf (by omega)

/-- The extractor's unfuelled recurrence: matching heads are kept;
differing heads follow the side whose `lcs` value attains the
maximum. -/
theorem longestCommonSubseq_cons_cons (a : Char) (xs : List Char)
    (b : Char) (ys : List Char) :
    longestCommonSubseq (a :: xs) (b :: ys) =
      if a = b then a :: longestCommonSubseq xs ys
      else if lcs (a :: xs) ys ≤ lcs xs (b :: ys)
        then longestCommonSubseq xs (b :: ys)
        else longestCommonSubseq (a :: xs) ys := by
  have e : (a :: xs).length + (b :: ys).length + 1 = (xs.length + ys.length + 2) + 1 := by
    simp only [List.length_cons]; omega
  have h1 : longestCommonSubseq (a :: xs) (b :: ys) =
      if a = b then a :: lcsSeqAux (xs.length + ys.length + 2) xs ys
      else if lcsAux (xs.length + ys.length + 2) (a :: xs) ys
          ≤ lcsAux (xs.length + ys.length + 2) xs (b :: ys)
        then lcsSeqAux (xs.length + ys.length + 2) xs (b :: ys)
        else lcsSeqAux (xs.length + ys.length + 2) (a :: xs) ys := by
    show lcsSeqAux ((a :: xs).length + (b :: ys).length + 1) (a :: xs) (b :: ys) = _
    rw [e]
    exact lcsSeqAux_succ_cons_cons _ _ _ _ _
  rw [h1,
    lcsAux_eq_lcs _ (a :: xs) ys (by simp only [List.length_cons]; omega),
    lcsAux_eq_lcs _ xs (b :: ys) (by simp only [List.length_cons]; omega),
    lcsSeqAux_eq_longestCommonSubseq _ xs ys (by omega),
    lcsSeqAux_eq_longestCommonSubseq _ xs (b :: ys) (by simp only [List.length_cons]; omega),
    lcsSeqAux_eq_longestCommonSubseq _ (a :: xs) ys (by simp only [List.length_cons]; omega)]

/-- Achievability, in bounded form: the produced sequence is a
common subsequence of both inputs, of length exactly `lcs xs ys`. -/
theorem lcsSeq_spec_aux : ∀ (k : Nat) (xs ys : List Char),
    xs.length + ys.length ≤ k →
    (longestCommonSubseq xs ys).length = lcs xs ys ∧
    Subseq (longestCommonSubseq xs ys) xs ∧
    Subseq (longestCommonSubseq xs ys) ys := by
  intro k
  induction k with
  | zero =>
    intro xs ys h
    cases xs with
    | nil =>
      cases ys with
      | nil => exact ⟨rfl, Subseq.nil, Subseq.nil⟩
      | cons b ys => simp [List.length_cons] at h
    | cons a xs => simp [List.length_cons] at h
  | succ k ih =>
    intro xs ys h
    cases xs with
    | nil =>
      have hv : longestCommonSubseq [] ys = [] := rfl
      rw [hv, lcs_nil_left]
      exact ⟨rfl, Subseq.nil, Subseq.nil⟩
    | cons a xs =>
      cases ys with
      | nil =>
        have hv : longestCommonSubseq (a :: xs) [] = [] := rfl
        rw [hv, lcs_nil_right]
        exact ⟨rfl, Subseq.nil, Subseq.nil⟩
      | cons b ys =>
        simp only [List.length_cons] at h
        by_cases hab : a = b
        · subst hab
          have hv : longestCommonSubseq (a :: xs) (a :: ys)
              = a :: longestCommonSubseq xs ys := by
            rw [longestCommonSubseq_cons_cons, if_pos rfl]
          have hl : lcs (a :: xs) (a :: ys) = lcs xs ys + 1 := by
            rw [lcs_cons_cons, if_pos rfl]
          rw [hv, hl]
          obtain ⟨h1, h2, h3⟩ := ih xs ys (by omega)
          refine ⟨?_, Subseq.cons a h2, Subseq.cons a h3⟩
          simp only [List.length_cons]
          omega
        · by_cases hc : lcs (a :: xs) ys ≤ lcs xs (b :: ys)
          · have hv : longestCommonSubseq (a :: xs) (b :: ys)
                = longestCommonSubseq xs (b :: ys) := by
              rw [longestCommonSubseq_cons_cons, if_neg hab, if_pos hc]
            have hl : lcs (a :: xs) (b :: ys)
                = max (lcs xs (b :: ys)) (lcs (a :: xs) ys) := by
              rw [lcs_cons_cons, if_neg hab]
            rw [hv, hl]
            obtain ⟨h1, h2, h3⟩ := ih xs (b :: ys) (by simp only [List.length_cons]; omega)
            exact ⟨by omega, Subseq.skip a h2, h3⟩
          · have hv : longestCommonSubseq (a :: xs) (b :: ys)
                = longestCommonSubseq (a :: xs) ys := by
              rw [longestCommonSubseq_cons_cons, if_neg hab, if_neg hc]
            have hl : lcs (a :: xs) (b :: ys)
                = max (lcs xs (b :: ys)) (lcs (a :: xs) ys) := by
              rw [lcs_cons_cons, if_neg hab]
            rw [hv, hl]
            obtain ⟨h1, h2, h3⟩ := ih (a :: xs) ys (by simp only [List.length_cons]; omega)
            exact ⟨by omega, h2, Subseq.skip b h3⟩

/-- Achievability: the produced sequence is a common subsequence of
both inputs, of length exactly `lcs xs ys`. -/
theorem lcsSeq_spec (xs ys : List Char) :
    (longestCommonSubseq xs ys).length = lcs xs ys ∧
    Subseq (longestCommonSubseq xs ys) xs ∧
    Subseq (longestCommonSubseq xs ys) ys :=
  lcsSeq_spec_aux (xs.length + ys.length) xs ys (by omega)

/-- Correctness (the draft's headline, repaired): the computed
length is the length of the produced sequence — the draft's own
equation — and the produced sequence is a common subsequence of
both inputs, with no common subsequence longer. -/
theorem lcs_correctness (xs ys : List Char) :
    lcs xs ys = (longestCommonSubseq xs ys).length ∧
    Subseq (longestCommonSubseq xs ys) xs ∧
    Subseq (longestCommonSubseq xs ys) ys ∧
    ∀ s : List Char, Subseq s xs → Subseq s ys → s.length ≤ lcs xs ys := by
  obtain ⟨h1, h2, h3⟩ := lcsSeq_spec xs ys
  exact ⟨h1.symm, h2, h3, fun s hs ht => lcs_length_le xs ys s hs ht⟩

end AxiomCode
