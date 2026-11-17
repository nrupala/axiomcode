import Spec
import Tactics

/-!
# AxiomCode — Verified Previous Permutation

Promoted from `lean/drafts/previous_correctness.lean` under the
L2 promotion procedure (`lean/PROMOTION.md`). The draft's shells
are authored for real: `Permutation` gains the `toList` field its
statement references, and `previous` computes the previous
permutation in lexicographic order — the standard algorithm,
structured as a tail-first recursion (`prevPermAux`): compute the
previous permutation of the tail; if the tail changed, keep the
head; if the tail is already minimal (ascending) and its head is
smaller than our head, the descent is here — swap the head with
the rightmost smaller element of the tail (`swapRightmostLt`) and
reverse the remainder, which makes it maximal. When no previous
permutation exists (the list is ascending), the list is returned
unchanged; that convention is part of the authored algorithm and
is stated here plainly.

Statement honesty: the draft's `IsPermutation` is an undefined
name, and as written it takes one argument — the output list —
which cannot express "a permutation of the input": a one-place
reading collapses (every list is a permutation of itself). It is
authored as the two-value relation it must mean,
`Permutation.IsPermutation p q := List.Perm p.toList q.toList`,
and the theorem is carried in the draft's shape with the relation
applied to the output and the input: `(previous p).IsPermutation p`.
(The draft file also ends with a stray unmatched
`end Permutation`; it has no counterpart here.) What the draft
claims is preservation — the output is a permutation of the input
— and that is exactly what is proved; that the output is the
*immediate* predecessor is the algorithm's design (described
above), not part of the draft's stated claim.
-/

namespace AxiomCode

/-- A permutation, represented by its list of elements. -/
structure Permutation (α : Type) where
  toList : List α
deriving DecidableEq, Repr

/-- `p` is a permutation of `q`: their lists are permutations of
each other. -/
def Permutation.IsPermutation (p q : Permutation Nat) : Prop :=
  List.Perm p.toList q.toList

/-- Find the rightmost element of `s` smaller than `v` and swap it
with `v`: returns the swapped-out element and `s` with that
position replaced by `v`, or `none` if no element is smaller. -/
def swapRightmostLt (v : Nat) : List Nat → Option (Nat × List Nat)
  | [] => none
  | x :: xs =>
    match swapRightmostLt v xs with
    | some (c, xs') => some (c, x :: xs')
    | none => if x < v then some (x, v :: xs) else none

/-- Swapping via `swapRightmostLt` preserves the permutation
relation between `v :: s` and the result. -/
theorem swapRightmostLt_perm {v : Nat} :
    ∀ {s : List Nat} {c : Nat} {s' : List Nat},
      swapRightmostLt v s = some (c, s') →
      List.Perm (v :: s) (c :: s') := by
  intro s
  induction s with
  | nil =>
    intro c s' h
    have h0 : swapRightmostLt v [] = none := rfl
    rw [h0] at h
    cases h
  | cons x xs ih =>
    intro c s' h
    cases hrec : swapRightmostLt v xs with
    | none =>
      simp only [swapRightmostLt, hrec] at h
      by_cases hxv : x < v
      · rw [ite_eq_left hxv] at h
        have h2 : (x, v :: xs) = (c, s') := Option.some.inj h
        cases h2
        exact List.Perm.swap x v xs
      · rw [ite_eq_right hxv] at h
        cases h
    | some p =>
      obtain ⟨c₀, xs₀⟩ := p
      simp only [swapRightmostLt, hrec] at h
      have h2 : (c₀, x :: xs₀) = (c, s') := Option.some.inj h
      cases h2
      exact ((List.Perm.swap x v xs).trans
        (List.Perm.cons x (ih hrec))).trans (List.Perm.swap c x xs₀)

/-- The previous-permutation recursion: returns the previous
permutation of the list together with a flag saying whether the
list was returned unchanged (no previous permutation exists
inside it — it is already ascending). -/
def prevPermAux : List Nat → List Nat × Bool
  | [] => ([], true)
  | [x] => ([x], true)
  | x :: y :: rest =>
    match prevPermAux (y :: rest) with
    | (_ys, true) =>
      if y < x then
        match swapRightmostLt x (y :: rest) with
        | some (c, s') => (c :: s'.reverse, false)
        | none => (x :: y :: rest, true)
      else (x :: y :: rest, true)
    | (ys, false) => (x :: ys, false)

/-- The recursion's output is a permutation of its input. -/
theorem prevPermAux_perm :
    ∀ l : List Nat, List.Perm (prevPermAux l).1 l := by
  intro l
  induction l with
  | nil => exact List.Perm.refl _
  | cons x xs ih =>
    cases xs with
    | nil => exact List.Perm.refl _
    | cons y rest =>
      have hunfold : prevPermAux (x :: y :: rest) =
          match prevPermAux (y :: rest) with
          | (ys, true) =>
            if y < x then
              match swapRightmostLt x (y :: rest) with
              | some (c, s') => (c :: s'.reverse, false)
              | none => (x :: y :: rest, true)
            else (x :: y :: rest, true)
          | (ys, false) => (x :: ys, false) := rfl
      cases htail : prevPermAux (y :: rest) with
      | mk ys flag =>
        cases flag with
        | false =>
          rw [hunfold, htail]
          rw [htail] at ih
          exact List.Perm.cons x ih
        | true =>
          by_cases hyx : y < x
          · cases hswap : swapRightmostLt x (y :: rest) with
            | none =>
              rw [hunfold, htail, ite_eq_left hyx, hswap]
            | some p =>
              obtain ⟨c, s'⟩ := p
              rw [hunfold, htail, ite_eq_left hyx, hswap]
              exact (List.Perm.cons c (List.reverse_perm s')).trans
                (swapRightmostLt_perm hswap).symm
          · rw [hunfold, htail, ite_eq_right hyx]

/-- The previous permutation of a list (the list itself when it
is already the smallest arrangement). -/
def prevPerm (l : List Nat) : List Nat := (prevPermAux l).1

/-- The previous permutation of a permutation. -/
def previous (p : Permutation Nat) : Permutation Nat :=
  ⟨prevPerm p.toList⟩

/-- The draft's correctness theorem, with `IsPermutation`
authored as the two-value relation (see the module doc): the
previous permutation is a permutation of the input. -/
theorem previous_correctness :
    ∀ p : Permutation Nat, (previous p).IsPermutation p := by
  intro p
  show List.Perm (previous p).toList p.toList
  exact prevPermAux_perm p.toList

end AxiomCode
