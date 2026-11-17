import Spec
import Tactics

namespace AxiomCode

/-!
# KMP search — the verified automaton

## Statement-honesty record

The draft (`kmp_search_correctness.lean`) was a shell: a
fieldless `KMPTable`, body-less `kmp_table` / `kmp_search`, and
a headline whose variables `pos` and `m` are unbound — it does
not elaborate as written, and nothing in it was carried
literally. The classical claim is authored here in full.

## What is proved

The KMP state after consuming a text is the length of the
longest pattern prefix that is a suffix of the text
(`kmpState`, by bounded search, with `kmpState_spec` /
`kmpState_max` pinning it as exactly that longest length). The
correctness core is the **step lemma** (`kmpState_step`): the
next state after appending one symbol depends only on the
current state — the text and the representative
`p.take (state)` give the same next state — proved through the
suffix chain (a prefix-suffix of `s ++ [a]` of length `j ≥ 1`
drops to one of `s` of length `j - 1`, and prefix-suffixes of
`s` are suffixes of its longest). The automaton (`kmpStep`,
`kmpRun`) therefore computes the state function exactly
(`foldl_from_state`, `kmpRun_eq_state`), and the search
(`kmpSearch`) is characterized exactly: it returns `some pos`
iff an occurrence starts at `pos` and none starts earlier
(`kmpSearch_eq_some`), and `none` iff no occurrence exists
(`kmpSearch_eq_none`).

Scope, stated plainly: this verifies the automaton's
correctness. The failure-function *table* construction and the
linear-time bound are not part of the claim — `kmpStep`
recomputes the state by bounded search; what the step lemma
proves is that the current state is all a step needs, which is
exactly the fact a table exploits.
-/

/-- `k` is a prefix-suffix length of pattern `p` for text `s`:
the length-`k` prefix of `p` is exactly the length-`k` suffix
of `s`. -/
def prefSuf (p s : List Nat) (k : Nat) : Prop :=
  k ≤ p.length ∧ p.take k = s.drop (s.length - k)

instance (p s : List Nat) (k : Nat) : Decidable (prefSuf p s k) := by
  unfold prefSuf
  infer_instance

theorem prefSuf_zero (p s : List Nat) : prefSuf p s 0 := by
  refine ⟨Nat.zero_le _, ?_⟩
  simp [List.drop_length]

theorem le_foldl_max : ∀ (l : List Nat) (a : Nat), a ≤ l.foldl max a := by
  intro l
  induction l with
  | nil => intro a; simp only [List.foldl_nil]; exact Nat.le_refl a
  | cons x l ih =>
    intro a
    simp only [List.foldl_cons]
    exact Nat.le_trans (Nat.le_max_left a x) (ih (max a x))

theorem mem_le_foldl_max : ∀ (l : List Nat) (a k : Nat),
    k ∈ l → k ≤ l.foldl max a := by
  intro l
  induction l with
  | nil => intro a k h; simp at h
  | cons x l ih =>
    intro a k h
    simp only [List.foldl_cons]
    rcases List.mem_cons.mp h with h1 | h'
    · have e : max a x = max a k := by rw [← h1]
      rw [e]
      exact Nat.le_trans (Nat.le_max_right a k) (le_foldl_max l (max a k))
    · exact ih (max a x) k h'

theorem foldl_max_mem : ∀ (l : List Nat) (a : Nat),
    l ≠ [] → l.foldl max a ∈ l ∨ l.foldl max a = a := by
  intro l
  induction l with
  | nil => intro a h; exact absurd rfl h
  | cons x l ih =>
    intro a _
    simp only [List.foldl_cons]
    by_cases hl : l = []
    · subst hl
      simp only [List.foldl_nil]
      rcases Nat.le_total a x with h | h
      · rw [Nat.max_eq_right h]; exact Or.inl (List.mem_cons_self)
      · rw [Nat.max_eq_left h]; exact Or.inr rfl
    · rcases ih (max a x) hl with h | h
      · exact Or.inl (List.mem_cons_of_mem x h)
      · rw [h]
        rcases Nat.le_total a x with h2 | h2
        · rw [Nat.max_eq_right h2]; exact Or.inl (List.mem_cons_self)
        · rw [Nat.max_eq_left h2]; exact Or.inr rfl

/-- The KMP state: the longest prefix-suffix length of `p`
for the consumed text `s`, by bounded search. -/
def kmpState (p s : List Nat) : Nat :=
  ((List.range (p.length + 1)).filter
    (fun k => decide (prefSuf p s k))).foldl max 0

theorem kmpState_spec (p s : List Nat) : prefSuf p s (kmpState p s) := by
  unfold kmpState
  have h0 : 0 ∈ (List.range (p.length + 1)).filter
      (fun k => decide (prefSuf p s k)) := by
    rw [List.mem_filter]
    exact ⟨List.mem_range.mpr (Nat.succ_pos _),
      decide_eq_true (prefSuf_zero p s)⟩
  have hne : ((List.range (p.length + 1)).filter
      (fun k => decide (prefSuf p s k))) ≠ [] := by
    intro h
    rw [h] at h0
    simp at h0
  rcases foldl_max_mem _ 0 hne with h | h
  · have := List.mem_filter.mp h
    exact (decide_eq_true_iff.mp this.2)
  · rw [h]; exact prefSuf_zero p s

theorem kmpState_le_length (p s : List Nat) : kmpState p s ≤ p.length := by
  exact (kmpState_spec p s).1

theorem kmpState_max (p s : List Nat) {k : Nat} (h : prefSuf p s k) :
    k ≤ kmpState p s := by
  unfold kmpState
  apply mem_le_foldl_max
  rw [List.mem_filter]
  exact ⟨List.mem_range.mpr (Nat.succ_le_of_lt (Nat.lt_succ_of_le h.1)),
    decide_eq_true h⟩

theorem prefSuf_le_right {p s : List Nat} {k : Nat} (h : prefSuf p s k) :
    k ≤ s.length := by
  obtain ⟨h1, h2⟩ := h
  have h3 := congrArg List.length h2
  rw [List.length_take, List.length_drop] at h3
  omega

/-- The step lemma — the correctness core of KMP. The next state
after appending one symbol depends only on the current state:
the text `s` and the representative `p.take (state)` give the
same next state. Both directions go through the suffix chain:
a prefix-suffix of `s ++ [a]` of length `j ≥ 1` drops to a
prefix-suffix of `s` of length `j - 1`, and prefix-suffixes of
`s` are suffixes of its longest one. -/
theorem kmpState_step (p s : List Nat) (a : Nat) :
    kmpState p (s ++ [a]) = kmpState p (p.take (kmpState p s) ++ [a]) := by
  generalize hk_def : kmpState p s = k
  have hk := kmpState_spec p s
  rw [hk_def] at hk
  have hklen : k ≤ s.length := prefSuf_le_right hk
  have htk : (p.take k).length = k := by
    rw [List.length_take]; exact Nat.min_eq_left hk.1
  apply Nat.le_antisymm
  · -- the state after `s ++ [a]` is a prefix-suffix of the representative
    generalize hk'_def : kmpState p (s ++ [a]) = k'
    have hk' := kmpState_spec p (s ++ [a])
    rw [hk'_def] at hk'
    apply kmpState_max
    by_cases h0 : k' = 0
    · subst h0
      refine ⟨Nat.zero_le _, ?_⟩
      simp only [List.take_zero]
      symm
      refine List.drop_eq_nil_of_le ?_
      omega
    · have hk'1 : 1 ≤ k' := by omega
      have hk'len : k' ≤ s.length + 1 := by
        have h := prefSuf_le_right hk'
        simp only [List.length_append, List.length_singleton] at h
        exact h
      have htake' : p.take k' = s.drop (s.length + 1 - k') ++ [a] := by
        have h2 := hk'.2
        rw [List.length_append, List.length_singleton] at h2
        rw [h2, List.drop_append_of_le_length (by omega : s.length + 1 - k' ≤ s.length)]
      -- `k' - 1` is a prefix-suffix of `s`
      have hps : prefSuf p s (k' - 1) := by
        refine ⟨by have h1 := hk'.1; omega, ?_⟩
        have e1 : p.take (k' - 1) = (p.take k').take (k' - 1) := by
          rw [List.take_take, Nat.min_eq_left (by omega : k' - 1 ≤ k')]
        have e2 : (s.drop (s.length + 1 - k')).length = k' - 1 := by
          rw [List.length_drop]; omega
        rw [e1, htake', List.take_append, e2]
        simp only [Nat.sub_self, List.take_zero, List.append_nil]
        rw [List.take_of_length_le (by omega : (s.drop (s.length + 1 - k')).length ≤ k' - 1)]
        congr 1
        omega
      have hkm : k' - 1 ≤ k := hk_def ▸ kmpState_max p s hps
      refine ⟨hk'.1, ?_⟩
      rw [htake']
      have hlen2 : (p.take k ++ [a]).length = k + 1 := by
        rw [List.length_append, htk, List.length_singleton]
      rw [hlen2, List.drop_append_of_le_length
        (show k + 1 - k' ≤ (p.take k).length by rw [htk]; omega)]
      congr 1
      rw [hk.2, List.drop_drop]
      congr 1
      omega
  · -- and conversely
    generalize hj_def : kmpState p (p.take k ++ [a]) = j
    have hj := kmpState_spec p (p.take k ++ [a])
    rw [hj_def] at hj
    apply kmpState_max
    by_cases h0 : j = 0
    · subst h0
      refine ⟨Nat.zero_le _, ?_⟩
      simp only [List.take_zero]
      symm
      refine List.drop_eq_nil_of_le ?_
      omega
    · have hj1 : 1 ≤ j := by omega
      have hjlen : j ≤ k + 1 := by
        have h := prefSuf_le_right hj
        rwa [List.length_append, htk, List.length_singleton] at h
      refine ⟨hj.1, ?_⟩
      have hlen2 : (p.take k ++ [a]).length = k + 1 := by
        rw [List.length_append, htk, List.length_singleton]
      have htakej : p.take j = s.drop (s.length + 1 - j) ++ [a] := by
        have h2 := hj.2
        rw [hlen2, List.drop_append_of_le_length
          (show k + 1 - j ≤ (p.take k).length by rw [htk]; omega)] at h2
        rw [h2, hk.2, List.drop_drop]
        congr 1
        congr 1
        omega
      rw [htakej, List.length_append, List.length_singleton,
        List.drop_append_of_le_length (by omega : s.length + 1 - j ≤ s.length)]

/-- One automaton step from state `k` on symbol `a`: the state
of the representative string. -/
def kmpStep (p : List Nat) (k a : Nat) : Nat :=
  kmpState p (p.take k ++ [a])

/-- The automaton run: fold the step over the text from state 0. -/
def kmpRun (p t : List Nat) : Nat :=
  t.foldl (kmpStep p) 0

theorem kmpState_nil (p : List Nat) : kmpState p [] = 0 :=
  Nat.le_antisymm (prefSuf_le_right (kmpState_spec p [])) (Nat.zero_le _)

/-- The run invariant, generalized over the consumed prefix:
running the automaton over `t` starting from the state of `s`
ends in the state of `s ++ t`. Induction on `t`; the cons step
is exactly the step lemma. -/
theorem foldl_from_state (p : List Nat) : ∀ (t s : List Nat),
    t.foldl (kmpStep p) (kmpState p s) = kmpState p (s ++ t) := by
  intro t
  induction t with
  | nil => intro s; simp
  | cons a t ih =>
    intro s
    simp only [List.foldl_cons]
    have hstep : kmpStep p (kmpState p s) a = kmpState p (s ++ [a]) :=
      (kmpState_step p s a).symm
    rw [hstep, ih (s ++ [a]), List.append_assoc]
    rfl

/-- The automaton computes the state: the run over `t` from 0
is `kmpState p t`. -/
theorem kmpRun_eq_state (p t : List Nat) : kmpRun p t = kmpState p t := by
  have h := foldl_from_state p t []
  rw [kmpState_nil, List.nil_append] at h
  exact h

/-- The full-match bridge: the state of a text prefix is the
pattern length exactly when the window ending at that prefix
is the pattern itself. -/
theorem state_eq_length_iff (p t : List Nat) (i : Nat) (hi : i ≤ t.length) :
    kmpState p (t.take i) = p.length ↔
      p.length ≤ i ∧ (t.drop (i - p.length)).take p.length = p := by
  constructor
  · intro h
    have hspec := kmpState_spec p (t.take i)
    rw [h] at hspec
    have hlen := prefSuf_le_right hspec
    rw [List.length_take, Nat.min_eq_left hi] at hlen
    refine ⟨hlen, ?_⟩
    have h2 := hspec.2
    rw [List.length_take, Nat.min_eq_left hi] at h2
    have hple : p.take p.length = p :=
      List.take_of_length_le (Nat.le_refl _)
    rw [hple] at h2
    have h3 : (t.take i).drop (i - p.length) =
        (t.drop (i - p.length)).take p.length := by
      rw [List.drop_take]
      congr 1
      omega
    rw [h3] at h2
    exact h2.symm
  · intro h
    apply Nat.le_antisymm
    · exact kmpState_le_length p _
    · apply kmpState_max
      refine ⟨Nat.le_refl _, ?_⟩
      rw [List.length_take, Nat.min_eq_left hi,
        List.take_of_length_le (Nat.le_refl _),
        List.drop_take]
      have e : i - (i - p.length) = p.length := by omega
      rw [e]
      exact h.2.symm

theorem find?_range_some_spec (q : Nat → Bool) : ∀ (n a : Nat),
    (List.range n).find? q = some a →
      a < n ∧ q a = true ∧ ∀ b, b < a → q b = false := by
  intro n
  induction n with
  | zero => intro a h; simp at h
  | succ n ih =>
    intro a h
    rw [List.range_succ, List.find?_append] at h
    cases h1 : (List.range n).find? q with
    | some a' =>
      rw [h1] at h
      have haa : a' = a := Option.some.inj h
      subst haa
      obtain ⟨h1', h2', h3'⟩ := ih a' h1
      exact ⟨by omega, h2', h3'⟩
    | none =>
      rw [h1] at h
      have h2 : ([n] : List Nat).find? q = some a := h
      rw [List.find?_cons, List.find?_nil] at h2
      cases hq : q n
      · simp [hq] at h2
      · simp only [hq] at h2
        have han : a = n := (Option.some.inj h2).symm
        subst han
        refine ⟨Nat.lt_succ_self a, hq, ?_⟩
        intro b hb
        have hnb : ¬ q b = true :=
          List.find?_eq_none.mp h1 b (List.mem_range.mpr (by omega))
        cases hqb : q b
        · rfl
        · exact absurd hqb hnb

theorem find?_range_eq_some (q : Nat → Bool) {n a : Nat} (ha : a < n)
    (hqa : q a = true) (hmin : ∀ b, b < a → q b = false) :
    (List.range n).find? q = some a := by
  induction n with
  | zero => omega
  | succ n ih =>
    rw [List.range_succ, List.find?_append]
    by_cases han : a < n
    · rw [ih han]
      rfl
    · have han2 : a = n := by omega
      subst han2
      have hnone : (List.range a).find? q = none := by
        rw [List.find?_eq_none]
        intro b hb
        rw [List.mem_range] at hb
        have hfb := hmin b (by omega)
        rw [hfb]
        exact (by decide : ¬ (false = true))
      rw [hnone]
      simp [hqa]

/-- KMP search: the first end position whose state is the full
pattern length, reported as the occurrence's start. -/
def kmpSearch (p t : List Nat) : Option Nat :=
  match (List.range (t.length + 1)).find?
      (fun i => decide (kmpState p (t.take i) = p.length)) with
  | some i => some (i - p.length)
  | none => none

/-- An occurrence of `p` in `t` starting at `pos`: the window
there is `p`, in bounds. -/
def Occurs (p t : List Nat) (pos : Nat) : Prop :=
  (t.drop pos).take p.length = p ∧ pos + p.length ≤ t.length

theorem kmpSearch_eq_some {p t : List Nat} {pos : Nat} :
    kmpSearch p t = some pos ↔
      Occurs p t pos ∧ ∀ pos', pos' < pos → ¬ Occurs p t pos' := by
  unfold kmpSearch
  constructor
  · intro h
    cases h1 : (List.range (t.length + 1)).find?
        (fun i => decide (kmpState p (t.take i) = p.length)) with
    | none => simp [h1] at h
    | some i =>
      simp only [h1] at h
      have hpos : i - p.length = pos := Option.some.inj h
      obtain ⟨hi1, hi2, hi3⟩ := find?_range_some_spec _ _ _ h1
      have hi2' : kmpState p (t.take i) = p.length :=
        of_decide_eq_true hi2
      have hi_le : i ≤ t.length := by omega
      obtain ⟨hmle, hwin⟩ := (state_eq_length_iff p t i hi_le).mp hi2'
      have hpos_eq : pos + p.length = i := by omega
      subst hpos
      constructor
      · exact ⟨hwin, by omega⟩
      · intro pos' hpos' hocc
        have hi' : pos' + p.length < i := by
          have h4 : pos' + p.length ≤ t.length := hocc.2
          omega
        have hstate : kmpState p (t.take (pos' + p.length)) = p.length := by
          apply (state_eq_length_iff p t (pos' + p.length) (by omega)).mpr
          exact ⟨by omega, by
            have e : pos' + p.length - p.length = pos' := by omega
            rw [e]
            exact hocc.1⟩
        have hq : (fun i => decide (kmpState p (t.take i) = p.length))
            (pos' + p.length) = false :=
          hi3 _ hi'
        have hq' : decide (kmpState p (t.take (pos' + p.length)) =
            p.length) = false := hq
        exact of_decide_eq_false hq' hstate
  · intro h
    obtain ⟨hocc, hmin⟩ := h
    have hocc2 : pos + p.length ≤ t.length := hocc.2
    have hfind : (List.range (t.length + 1)).find?
        (fun i => decide (kmpState p (t.take i) = p.length)) =
        some (pos + p.length) := by
      apply find?_range_eq_some
      · omega
      · rw [decide_eq_true_eq]
        apply (state_eq_length_iff p t (pos + p.length) (by omega)).mpr
        refine ⟨by omega, ?_⟩
        have e : pos + p.length - p.length = pos := by omega
        rw [e]
        exact hocc.1
      · intro b hb
        by_cases hb1 : p.length ≤ b
        · have hstate : kmpState p (t.take b) ≠ p.length := by
            intro hst
            by_cases hb_le : b ≤ t.length
            · obtain ⟨-, hwin⟩ := (state_eq_length_iff p t b hb_le).mp hst
              exact hmin _ (by omega) ⟨hwin, by omega⟩
            · have htake : t.take b = t := List.take_of_length_le (by omega)
              rw [htake] at hst
              have hst2 : kmpState p (t.take t.length) = p.length := by
                have e : t.take t.length = t :=
                  List.take_of_length_le (Nat.le_refl _)
                rw [e]
                exact hst
              obtain ⟨hmle, hwin⟩ :=
                (state_eq_length_iff p t t.length (Nat.le_refl _)).mp hst2
              exact hmin _ (by omega) ⟨hwin, by omega⟩
          rw [Bool.eq_iff_iff]
          simp [hstate]
        · have hstate : kmpState p (t.take b) ≠ p.length := by
            intro hst
            have hle := prefSuf_le_right
              (hst ▸ kmpState_spec p (t.take b))
            rw [List.length_take] at hle
            omega
          rw [Bool.eq_iff_iff]
          simp [hstate]
    rw [hfind]
    show some (pos + p.length - p.length) = some pos
    congr 1
    omega

theorem kmpSearch_eq_none {p t : List Nat} :
    kmpSearch p t = none ↔ ∀ pos, ¬ Occurs p t pos := by
  constructor
  · intro h pos hocc
    have hocc2 : pos + p.length ≤ t.length := hocc.2
    have hstate : kmpState p (t.take (pos + p.length)) = p.length := by
      apply (state_eq_length_iff p t (pos + p.length) (by omega)).mpr
      refine ⟨by omega, ?_⟩
      have e : pos + p.length - p.length = pos := by omega
      rw [e]
      exact hocc.1
    unfold kmpSearch at h
    cases h1 : (List.range (t.length + 1)).find?
        (fun i => decide (kmpState p (t.take i) = p.length)) with
    | some i => simp [h1] at h
    | none =>
      have hnone := List.find?_eq_none.mp h1 (pos + p.length)
        (List.mem_range.mpr (by omega))
      exact hnone (decide_eq_true hstate)
  · intro h
    unfold kmpSearch
    cases h1 : (List.range (t.length + 1)).find?
        (fun i => decide (kmpState p (t.take i) = p.length)) with
    | none => rfl
    | some i =>
      obtain ⟨hi1, hi2, -⟩ := find?_range_some_spec _ _ _ h1
      have hi2' : kmpState p (t.take i) = p.length :=
        of_decide_eq_true hi2
      have hi_le : i ≤ t.length := by omega
      by_cases hm : p.length ≤ i
      · obtain ⟨hmle, hwin⟩ := (state_eq_length_iff p t i hi_le).mp hi2'
        exact False.elim (h (i - p.length) ⟨hwin, by omega⟩)
      · have hle := prefSuf_le_right (hi2' ▸ kmpState_spec p (t.take i))
        rw [List.length_take] at hle
        omega

end AxiomCode
