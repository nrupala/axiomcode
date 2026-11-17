import Spec
import Tactics

/-!
# Edit distance (Levenshtein)

The Levenshtein edit distance between two strings, computed by the
classical three-way dynamic-programming recurrence (delete the head
of the source, insert the head of the target, or substitute/match the
two heads), and proved equal to the least cost of an edit script:
`EditScript` is the inductive specification of transformability at a
given cost, and the headline theorem `edit_distance_correctness`
states that the computed value is achievable by a script and that no
script does better — the algorithm computes the minimum script cost.

The library works on `List Char` (a string's `String.data`), the
substrate the other string entries use. The recursion is fuelled
(`editDistAux`) because the three recursive calls shrink different
arguments; `editDistAux_irrel` shows the value is independent of the
fuel once the fuel exceeds the combined length, so `editDist` — the
worker at the canonical fuel `s.length + t.length + 1` — satisfies
the unfuelled recurrence (`editDist_cons_cons`).

## Draft defect record (promotion standard: defect + counterexample)

The draft (`lean/drafts/edit_distance_correctness.lean`) did not
elaborate: `edit_distance` was written with `:=` and no body, and it
imported Mathlib and Aesop, which this working copy does not build.

Its statement was also vacuous. `EditDistance (s t : String)` was a
fieldless structure, and the theorem was
`∀ s t : String, EditDistance s t` — a claim about that structure
only. A fieldless structure is inhabited by its constructor for
every `s` and `t`, and the statement never mentions `edit_distance`
at all: it stays true if `edit_distance` is replaced by any function
whatsoever (the constant zero function, say), so as stated it
certifies nothing about the algorithm.

## Repair (shape preserved)

The draft's theorem name is kept for the headline. The vacuous
structure is replaced by the real specification, the inductive
`EditScript` relation (a script of keeps, substitutions, deletions
and insertions transforming one list into the other at a stated
cost), and the headline states of the authored algorithm exactly
what the draft gestured at: its value is the cost of an actual
script, and every script costs at least that much.
-/

namespace AxiomCode

/-- Fuelled worker for `editDist`. The fuel bounds the recursion:
each step consumes one unit and recurses on strictly shorter
combined input. A fuel of zero on nonempty input returns `0`, a
value the adequacy lemma `editDistAux_irrel` shows is never seen at
adequate fuel. -/
def editDistAux : Nat → List Char → List Char → Nat
  | 0, _, _ => 0
  | _ + 1, [], t => t.length
  | _ + 1, s, [] => s.length
  | f + 1, a :: s, b :: t =>
      if a = b then editDistAux f s t
      else 1 + min (editDistAux f s (b :: t)) (min (editDistAux f (a :: s) t) (editDistAux f s t))

/-- The Levenshtein edit distance: the least number of single-char
insertions, deletions and substitutions turning `s` into `t`. -/
def editDist (s t : List Char) : Nat :=
  editDistAux (s.length + t.length + 1) s t

theorem editDistAux_succ_nil_left (f : Nat) (t : List Char) :
    editDistAux (f + 1) [] t = t.length := rfl

theorem editDistAux_succ_nil_right (f : Nat) (s : List Char) :
    editDistAux (f + 1) s [] = s.length := by cases s <;> rfl

theorem editDistAux_succ_cons_cons (f : Nat) (a : Char) (s : List Char)
    (b : Char) (t : List Char) :
    editDistAux (f + 1) (a :: s) (b :: t) =
      if a = b then editDistAux f s t
      else 1 + min (editDistAux f s (b :: t))
        (min (editDistAux f (a :: s) t) (editDistAux f s t)) := rfl

/-- Fuel irrelevance: once both fuels exceed the combined length,
the worker's value no longer depends on the fuel. -/
theorem editDistAux_irrel : ∀ (f₁ f₂ : Nat) (s t : List Char),
    s.length + t.length < f₁ → s.length + t.length < f₂ →
    editDistAux f₁ s t = editDistAux f₂ s t := by
  intro f₁
  induction f₁ with
  | zero => intro f₂ s t h₁ h₂; exact (Nat.not_lt_zero _ h₁).elim
  | succ f ih =>
    intro f₂ s t h₁ h₂
    cases f₂ with
    | zero => exact (Nat.not_lt_zero _ h₂).elim
    | succ g =>
      cases s with
      | nil =>
        rw [editDistAux_succ_nil_left, editDistAux_succ_nil_left]
      | cons a s =>
        cases t with
        | nil =>
          rw [editDistAux_succ_nil_right, editDistAux_succ_nil_right]
        | cons b t =>
          simp only [List.length_cons] at h₁ h₂
          by_cases hab : a = b
          · rw [editDistAux_succ_cons_cons, editDistAux_succ_cons_cons,
              if_pos hab, if_pos hab]
            exact ih g s t (by omega) (by omega)
          · rw [editDistAux_succ_cons_cons, editDistAux_succ_cons_cons,
              if_neg hab, if_neg hab]
            rw [ih g s (b :: t) (by simp only [List.length_cons]; omega)
                (by simp only [List.length_cons]; omega),
              ih g (a :: s) t (by simp only [List.length_cons]; omega)
                (by simp only [List.length_cons]; omega),
              ih g s t (by omega) (by omega)]

/-- At any adequate fuel the worker computes `editDist`. -/
theorem editDistAux_eq_editDist (f : Nat) (s t : List Char)
    (hf : s.length + t.length < f) :
    editDistAux f s t = editDist s t :=
  editDistAux_irrel f (s.length + t.length + 1) s t hf (by omega)

theorem editDist_nil_left (t : List Char) : editDist [] t = t.length := rfl

theorem editDist_nil_right (s : List Char) : editDist s [] = s.length := by
  cases s <;> rfl

/-- The unfuelled recurrence: matching heads cost the diagonal;
differing heads cost one plus the cheapest of delete, insert and
substitute. -/
theorem editDist_cons_cons (a : Char) (s : List Char) (b : Char) (t : List Char) :
    editDist (a :: s) (b :: t) =
      if a = b then editDist s t
      else 1 + min (editDist s (b :: t)) (min (editDist (a :: s) t) (editDist s t)) := by
  have e : (a :: s).length + (b :: t).length + 1 = (s.length + t.length + 2) + 1 := by
    simp only [List.length_cons]; omega
  have h1 : editDist (a :: s) (b :: t) =
      if a = b then editDistAux (s.length + t.length + 2) s t
      else 1 + min (editDistAux (s.length + t.length + 2) s (b :: t))
        (min (editDistAux (s.length + t.length + 2) (a :: s) t)
          (editDistAux (s.length + t.length + 2) s t)) := by
    show editDistAux ((a :: s).length + (b :: t).length + 1) (a :: s) (b :: t) = _
    rw [e]
    exact editDistAux_succ_cons_cons _ _ _ _ _
  rw [h1,
    editDistAux_eq_editDist _ s t (by omega),
    editDistAux_eq_editDist _ s (b :: t) (by simp only [List.length_cons]; omega),
    editDistAux_eq_editDist _ (a :: s) t (by simp only [List.length_cons]; omega)]

/-- Symmetry of the distance, in bounded form (the induction is on a
bound for the combined length). -/
theorem editDist_symm_aux : ∀ (k : Nat) (s t : List Char),
    s.length + t.length ≤ k → editDist s t = editDist t s := by
  intro k
  induction k with
  | zero =>
    intro s t h
    cases s with
    | nil =>
      cases t with
      | nil => rfl
      | cons b t => simp [List.length_cons] at h
    | cons a s => simp [List.length_cons] at h
  | succ k ih =>
    intro s t h
    cases s with
    | nil => rw [editDist_nil_left, editDist_nil_right]
    | cons a s =>
      cases t with
      | nil => rw [editDist_nil_right, editDist_nil_left]
      | cons b t =>
        simp only [List.length_cons] at h
        by_cases hab : a = b
        · rw [editDist_cons_cons, editDist_cons_cons, if_pos hab, if_pos hab.symm]
          exact ih s t (by omega)
        · rw [editDist_cons_cons, editDist_cons_cons, if_neg hab,
            if_neg (fun hba => hab hba.symm)]
          have h1 := ih s (b :: t) (by simp only [List.length_cons]; omega)
          have h2 := ih (a :: s) t (by simp only [List.length_cons]; omega)
          have h3 := ih s t (by omega)
          omega

/-- The edit distance is symmetric. -/
theorem editDist_symm (s t : List Char) : editDist s t = editDist t s :=
  editDist_symm_aux (s.length + t.length) s t (by omega)

/-- The length bounds, in bounded form: the distance is at least the
length difference, in both orientations. -/
theorem editDist_length_bounds_aux : ∀ (k : Nat) (s t : List Char),
    s.length + t.length ≤ k →
    t.length ≤ s.length + editDist s t ∧ s.length ≤ t.length + editDist s t := by
  intro k
  induction k with
  | zero =>
    intro s t h
    cases s with
    | nil =>
      cases t with
      | nil =>
        rw [editDist_nil_left]
        exact ⟨by omega, by omega⟩
      | cons b t => simp [List.length_cons] at h
    | cons a s => simp [List.length_cons] at h
  | succ k ih =>
    intro s t h
    cases s with
    | nil =>
      rw [editDist_nil_left]
      show t.length ≤ 0 + t.length ∧ 0 ≤ t.length + t.length
      constructor <;> omega
    | cons a s =>
      cases t with
      | nil =>
        rw [editDist_nil_right]
        show 0 ≤ (a :: s).length + (a :: s).length ∧
          (a :: s).length ≤ 0 + (a :: s).length
        constructor <;> omega
      | cons b t =>
        simp only [List.length_cons] at h
        by_cases hab : a = b
        · have hrec : editDist (a :: s) (b :: t) = editDist s t := by
            rw [editDist_cons_cons, if_pos hab]
          have ih' := ih s t (by omega)
          obtain ⟨h1, h2⟩ := ih'
          rw [hrec]
          constructor <;> simp only [List.length_cons] <;> omega
        · have hrec : editDist (a :: s) (b :: t) =
              1 + min (editDist s (b :: t)) (min (editDist (a :: s) t) (editDist s t)) := by
            rw [editDist_cons_cons, if_neg hab]
          have ih1 := ih s (b :: t) (by simp only [List.length_cons]; omega)
          have ih2 := ih (a :: s) t (by simp only [List.length_cons]; omega)
          have ih3 := ih s t (by omega)
          obtain ⟨h1a, h1b⟩ := ih1
          obtain ⟨h2a, h2b⟩ := ih2
          obtain ⟨h3a, h3b⟩ := ih3
          rw [hrec]
          constructor <;>
            simp only [List.length_cons] at h1a h1b h2a h2b h3a h3b ⊢ <;> omega

/-- The distance is at least the length difference, in both
orientations: at least `t.length - s.length` insertions are needed,
and at least `s.length - t.length` deletions. -/
theorem editDist_length_le_add (s t : List Char) :
    t.length ≤ s.length + editDist s t ∧ s.length ≤ t.length + editDist s t :=
  editDist_length_bounds_aux (s.length + t.length) s t (by omega)

/-- The one-char Lipschitz package, in bounded form: prepending one
char to either side changes the distance by at most one, in the
three forms the script arguments need. (The fourth form,
`editDist_le_cons_left`, is the third read through `editDist_symm`.) -/
theorem editDist_lipschitz_aux : ∀ (k : Nat) (s t : List Char),
    s.length + t.length ≤ k →
    (∀ a : Char, editDist (a :: s) t ≤ editDist s t + 1) ∧
    (∀ b : Char, editDist s (b :: t) ≤ editDist s t + 1) ∧
    (∀ b : Char, editDist s t ≤ editDist s (b :: t) + 1) := by
  intro k
  induction k with
  | zero =>
    intro s t h
    cases s with
    | nil =>
      cases t with
      | nil =>
        refine ⟨?_, ?_, ?_⟩
        · intro a₁; simp [editDist_nil_right, editDist_nil_left]
        · intro b₁; simp [editDist_nil_left]
        · intro b₁; simp [editDist_nil_left]
      | cons b t => simp [List.length_cons] at h
    | cons a s => simp [List.length_cons] at h
  | succ k ih =>
    intro s t h
    cases s with
    | nil =>
      refine ⟨?_, ?_, ?_⟩
      · intro a₁
        cases t with
        | nil => simp [editDist_nil_right, editDist_nil_left]
        | cons b t =>
          by_cases h1 : a₁ = b
          · rw [editDist_cons_cons, if_pos h1, editDist_nil_left, editDist_nil_left]
            simp only [List.length_cons]; omega
          · rw [editDist_cons_cons, if_neg h1, editDist_nil_left, editDist_nil_left]
            omega
      · intro b₁
        rw [editDist_nil_left, editDist_nil_left]
        simp only [List.length_cons]; omega
      · intro b₁
        rw [editDist_nil_left, editDist_nil_left]
        simp only [List.length_cons]; omega
    | cons a s =>
      cases t with
      | nil =>
        refine ⟨?_, ?_, ?_⟩
        · intro a₁
          rw [editDist_nil_right, editDist_nil_right]
          simp only [List.length_cons]; omega
        · intro b₁
          by_cases h1 : a = b₁
          · rw [editDist_cons_cons, if_pos h1, editDist_nil_right, editDist_nil_right]
            simp only [List.length_cons]; omega
          · rw [editDist_cons_cons, if_neg h1, editDist_nil_right, editDist_nil_right]
            omega
        · intro b₁
          have hLB := (editDist_length_le_add (a :: s) [b₁]).2
          have hB : ([b₁] : List Char).length = 1 := rfl
          rw [editDist_nil_right]
          omega
      | cons b t =>
        simp only [List.length_cons] at h
        have ih_st := ih s t (by omega)
        have ih_sbt := ih s (b :: t) (by simp only [List.length_cons]; omega)
        have ih_ast := ih (a :: s) t (by simp only [List.length_cons]; omega)
        have ih_ts := ih t s (by omega)
        refine ⟨?_, ?_, ?_⟩
        · -- L1: prepend to the source.
          intro a₁
          by_cases h1 : a₁ = b
          · have hr : editDist (a₁ :: a :: s) (b :: t) = editDist (a :: s) t := by
              rw [editDist_cons_cons, if_pos h1]
            rw [hr]
            exact ih_ast.2.2 b
          · have hr : editDist (a₁ :: a :: s) (b :: t) =
                1 + min (editDist (a :: s) (b :: t))
                  (min (editDist (a₁ :: a :: s) t) (editDist (a :: s) t)) := by
              rw [editDist_cons_cons, if_neg h1]
            rw [hr]; omega
        · -- L3: prepend to the target.
          intro b₁
          by_cases h1 : a = b₁
          · have hr : editDist (a :: s) (b₁ :: b :: t) = editDist s (b :: t) := by
              rw [editDist_cons_cons, if_pos h1]
            rw [hr]
            by_cases h2 : a = b
            · have hr2 : editDist (a :: s) (b :: t) = editDist s t := by
                rw [editDist_cons_cons, if_pos h2]
              rw [hr2]
              exact ih_st.2.1 b
            · have hr2 : editDist (a :: s) (b :: t) =
                  1 + min (editDist s (b :: t)) (min (editDist (a :: s) t) (editDist s t)) := by
                rw [editDist_cons_cons, if_neg h2]
              rw [hr2]
              have hA : editDist s (b :: t) ≤ editDist s t + 1 := ih_st.2.1 b
              have hB : editDist s t ≤ editDist (a :: s) t + 1 := by
                have key := ih_ts.2.2 a
                rwa [editDist_symm t s, editDist_symm t (a :: s)] at key
              omega
          · have hr : editDist (a :: s) (b₁ :: b :: t) =
                1 + min (editDist s (b₁ :: b :: t))
                  (min (editDist (a :: s) (b :: t)) (editDist s (b :: t))) := by
              rw [editDist_cons_cons, if_neg h1]
            rw [hr]; omega
        · -- L4: the target grows by one char.
          intro c
          by_cases h1 : a = b
          · by_cases h2 : a = c
            · have hrL : editDist (a :: s) (b :: t) = editDist s t := by
                rw [editDist_cons_cons, if_pos h1]
              have hrR : editDist (a :: s) (c :: b :: t) = editDist s (b :: t) := by
                rw [editDist_cons_cons, if_pos h2]
              rw [hrL, hrR]
              exact ih_st.2.2 b
            · have hrL : editDist (a :: s) (b :: t) = editDist s t := by
                rw [editDist_cons_cons, if_pos h1]
              have hrR : editDist (a :: s) (c :: b :: t) =
                  1 + min (editDist s (c :: b :: t))
                    (min (editDist (a :: s) (b :: t)) (editDist s (b :: t))) := by
                rw [editDist_cons_cons, if_neg h2]
              rw [hrR, hrL]
              have hA : editDist s t ≤ editDist s (b :: t) + 1 := ih_st.2.2 b
              have hB : editDist s (b :: t) ≤ editDist s (c :: b :: t) + 1 := ih_sbt.2.2 c
              omega
          · by_cases h2 : a = c
            · have hrL : editDist (a :: s) (b :: t) =
                  1 + min (editDist s (b :: t)) (min (editDist (a :: s) t) (editDist s t)) := by
                rw [editDist_cons_cons, if_neg h1]
              have hrR : editDist (a :: s) (c :: b :: t) = editDist s (b :: t) := by
                rw [editDist_cons_cons, if_pos h2]
              rw [hrL, hrR]; omega
            · have hrL : editDist (a :: s) (b :: t) =
                  1 + min (editDist s (b :: t)) (min (editDist (a :: s) t) (editDist s t)) := by
                rw [editDist_cons_cons, if_neg h1]
              have hrR : editDist (a :: s) (c :: b :: t) =
                  1 + min (editDist s (c :: b :: t))
                    (min (editDist (a :: s) (b :: t)) (editDist s (b :: t))) := by
                rw [editDist_cons_cons, if_neg h2]
              rw [hrR, hrL]
              have hA : editDist s (b :: t) ≤ editDist s (c :: b :: t) + 1 := ih_sbt.2.2 c
              have hB : editDist s t ≤ editDist s (b :: t) + 1 := ih_st.2.2 b
              have hC : editDist s t ≤ editDist (a :: s) t + 1 := by
                have key := ih_ts.2.2 a
                rwa [editDist_symm t s, editDist_symm t (a :: s)] at key
              omega

/-- Prepending a char to the source raises the distance by at most
one (the extra char can always be deleted). -/
theorem editDist_cons_left_le (a : Char) (s t : List Char) :
    editDist (a :: s) t ≤ editDist s t + 1 :=
  (editDist_lipschitz_aux (s.length + t.length) s t (by omega)).1 a

/-- Prepending a char to the target raises the distance by at most
one (the extra char can always be inserted). -/
theorem editDist_cons_right_le (b : Char) (s t : List Char) :
    editDist s (b :: t) ≤ editDist s t + 1 :=
  (editDist_lipschitz_aux (s.length + t.length) s t (by omega)).2.1 b

/-- Prepending a char to the target lowers the distance by at most
one. -/
theorem editDist_le_cons_right (b : Char) (s t : List Char) :
    editDist s t ≤ editDist s (b :: t) + 1 :=
  (editDist_lipschitz_aux (s.length + t.length) s t (by omega)).2.2 b

/-- Prepending a char to the source lowers the distance by at most
one (the third Lipschitz form read through `editDist_symm`). -/
theorem editDist_le_cons_left (a : Char) (s t : List Char) :
    editDist s t ≤ editDist (a :: s) t + 1 := by
  have key := editDist_le_cons_right a t s
  rwa [editDist_symm t s, editDist_symm t (a :: s)] at key

/-- Edit scripts: `EditScript s t n` says `s` can be transformed
into `t` by a sequence of single-char operations of total cost `n` —
keep a matching head for free, substitute a differing head, delete a
source head, or insert a target head, each paid operation costing
one. This is the specification `editDist` computes the minimum of. -/
inductive EditScript : List Char → List Char → Nat → Prop
  | nil : EditScript [] [] 0
  | keep (a : Char) : EditScript s t n → EditScript (a :: s) (a :: t) n
  | sub (a b : Char) : a ≠ b → EditScript s t n → EditScript (a :: s) (b :: t) (n + 1)
  | del (a : Char) : EditScript s t n → EditScript (a :: s) t (n + 1)
  | ins (b : Char) : EditScript s t n → EditScript s (b :: t) (n + 1)

/-- Optimality: no script beats the computed distance. -/
theorem editDist_le_of_script : ∀ {s t : List Char} {n : Nat},
    EditScript s t n → editDist s t ≤ n := by
  intro s t n h
  induction h with
  | nil => exact Nat.zero_le 0
  | keep a h ih =>
    rw [editDist_cons_cons, if_pos rfl]
    exact ih
  | sub a b hne h ih =>
    rw [editDist_cons_cons, if_neg hne]
    omega
  | del a h ih =>
    refine Nat.le_trans (editDist_cons_left_le a _ _) ?_
    omega
  | ins b h ih =>
    refine Nat.le_trans (editDist_cons_right_le b _ _) ?_
    omega

/-- Building a target from nothing costs one insertion per char. -/
theorem editScript_nil_left (t : List Char) : EditScript [] t t.length := by
  induction t with
  | nil => exact EditScript.nil
  | cons b t ih => exact EditScript.ins b ih

/-- Deleting a whole source costs one deletion per char. -/
theorem editScript_nil_right (s : List Char) : EditScript s [] s.length := by
  induction s with
  | nil => exact EditScript.nil
  | cons a s ih => exact EditScript.del a ih

/-- Achievability, in bounded form: the computed distance is the
cost of an actual script. At differing heads the script follows
whichever of delete, insert or substitute attains the minimum. -/
theorem editScript_of_editDist_aux : ∀ (k : Nat) (s t : List Char),
    s.length + t.length ≤ k → EditScript s t (editDist s t) := by
  intro k
  induction k with
  | zero =>
    intro s t h
    cases s with
    | nil =>
      cases t with
      | nil => exact EditScript.nil
      | cons b t => simp [List.length_cons] at h
    | cons a s => simp [List.length_cons] at h
  | succ k ih =>
    intro s t h
    cases s with
    | nil =>
      rw [editDist_nil_left]
      exact editScript_nil_left t
    | cons a s =>
      cases t with
      | nil =>
        rw [editDist_nil_right]
        exact editScript_nil_right _
      | cons b t =>
        simp only [List.length_cons] at h
        by_cases hab : a = b
        · subst hab
          have hr : editDist (a :: s) (a :: t) = editDist s t := by
            rw [editDist_cons_cons, if_pos rfl]
          rw [hr]
          exact EditScript.keep a (ih s t (by omega))
        · have hr : editDist (a :: s) (b :: t) =
              1 + min (editDist s (b :: t)) (min (editDist (a :: s) t) (editDist s t)) := by
            rw [editDist_cons_cons, if_neg hab]
          rw [hr]
          have hA := ih s (b :: t) (by simp only [List.length_cons]; omega)
          have hB := ih (a :: s) t (by simp only [List.length_cons]; omega)
          have hC := ih s t (by omega)
          by_cases hmin : editDist s (b :: t) ≤ min (editDist (a :: s) t) (editDist s t)
          · have hm : min (editDist s (b :: t)) (min (editDist (a :: s) t) (editDist s t))
                = editDist s (b :: t) := by omega
            rw [hm, Nat.add_comm]
            exact EditScript.del a hA
          · by_cases hmin2 : editDist (a :: s) t ≤ editDist s t
            · have hm : min (editDist s (b :: t)) (min (editDist (a :: s) t) (editDist s t))
                  = editDist (a :: s) t := by omega
              rw [hm, Nat.add_comm]
              exact EditScript.ins b hB
            · have hm : min (editDist s (b :: t)) (min (editDist (a :: s) t) (editDist s t))
                  = editDist s t := by omega
              rw [hm, Nat.add_comm]
              exact EditScript.sub a b hab hC

/-- Achievability: the computed distance is the cost of an actual
edit script. -/
theorem editScript_editDist (s t : List Char) : EditScript s t (editDist s t) :=
  editScript_of_editDist_aux (s.length + t.length) s t (by omega)

/-- Correctness (the draft's headline, repaired): the computed
distance is the least script cost — a script of exactly that cost
exists, and every script costs at least that much. -/
theorem edit_distance_correctness (s t : List Char) :
    EditScript s t (editDist s t) ∧ ∀ n : Nat, EditScript s t n → editDist s t ≤ n :=
  ⟨editScript_editDist s t, fun n h => editDist_le_of_script h⟩

/-- The distance from a string to itself is zero. -/
theorem editDist_self (s : List Char) : editDist s s = 0 := by
  have h1 : EditScript s s 0 := by
    induction s with
    | nil => exact EditScript.nil
    | cons a s ih => exact EditScript.keep a ih
  have h2 := editDist_le_of_script h1
  omega

end AxiomCode
