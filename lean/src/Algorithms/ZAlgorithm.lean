import Spec
import Tactics

/-!
# The Z-function

The Z-function of a string: at each position `k`, the length of the
longest common prefix of the string and its suffix at `k`. This
entry computes it by the naive quadratic definition — `zAlgorithm s`
at index `k` is `lcp s (s.drop k)`, where `lcp` is the longest
common prefix length — and the headline theorem
`zAlgorithm_correctness` states that the computed array agrees with
that definition at every index, with the classical consequences
`zAlgorithm_head` (`Z[0]` is the whole string's length) and
`zAlgorithm_le` (`Z[k] + k` never exceeds the length).

The linear-time Z-box algorithm is a named non-goal of this entry:
the entry certifies the naive computation against the
longest-common-prefix definition, which is the specification any
optimized version must also meet.

## Draft defect record (promotion standard: defect + counterexample)

The draft (`lean/drafts/zalgorithm_correctness.lean`) did not
elaborate: `zAlgorithm` was written with `:=` and no body, and the
headline statement `let z := zAlgorithm s; ZArray.invariant z`
references `ZArray.invariant`, which does not exist — `ZArray
(n : Nat)` was a fieldless structure, whose only projection is its
constructor; there is no `invariant` field or definition anywhere
in the draft or the tree. In shape, too, an unnamed "invariant" of
an opaque wrapper type states nothing checkable about the computed
values: it names no property of any entry of the array.

## Repair (shape preserved)

The draft's function and theorem names are kept. The array is a
plain `List Nat` over `List Char` (the library's string substrate),
and the placeholder "invariant" is made concrete as the pointwise
characterization: at every index `k` below the length, the computed
value is exactly the longest common prefix of the string and its
suffix at `k`.
-/

namespace AxiomCode

/-- The longest common prefix length of two lists: how many
leading chars they share. -/
def lcp : List Char → List Char → Nat
  | [], _ => 0
  | _, [] => 0
  | a :: s, b :: t => if a = b then lcp s t + 1 else 0

theorem lcp_nil_left (t : List Char) : lcp [] t = 0 := rfl

theorem lcp_nil_right (s : List Char) : lcp s [] = 0 := by
  cases s <;> rfl

theorem lcp_cons_cons (a : Char) (s : List Char) (b : Char) (t : List Char) :
    lcp (a :: s) (b :: t) = if a = b then lcp s t + 1 else 0 := rfl

/-- A common prefix is no longer than the first list. -/
theorem lcp_le_length_left : ∀ (s t : List Char), lcp s t ≤ s.length := by
  intro s
  induction s with
  | nil => intro t; exact Nat.zero_le _
  | cons a s ih =>
    intro t
    cases t with
    | nil => rw [lcp_nil_right]; exact Nat.zero_le _
    | cons b t =>
      by_cases hab : a = b
      · rw [lcp_cons_cons, if_pos hab]
        have ih' := ih t
        simp only [List.length_cons]
        omega
      · rw [lcp_cons_cons, if_neg hab]
        exact Nat.zero_le _

/-- A common prefix is no longer than the second list. -/
theorem lcp_le_length_right : ∀ (s t : List Char), lcp s t ≤ t.length := by
  intro s
  induction s with
  | nil => intro t; exact Nat.zero_le _
  | cons a s ih =>
    intro t
    cases t with
    | nil => rw [lcp_nil_right]; exact Nat.zero_le _
    | cons b t =>
      by_cases hab : a = b
      · rw [lcp_cons_cons, if_pos hab]
        have ih' := ih t
        simp only [List.length_cons]
        omega
      · rw [lcp_cons_cons, if_neg hab]
        exact Nat.zero_le _

/-- The longest common prefix of a list with itself is its whole
length. -/
theorem lcp_self (s : List Char) : lcp s s = s.length := by
  induction s with
  | nil => rfl
  | cons a s ih =>
    rw [lcp_cons_cons, if_pos rfl, ih]
    simp only [List.length_cons]

/-- The Z-function, computed by the naive definition: at index `k`,
the longest common prefix of the string and its suffix at `k`. -/
def zAlgorithm (s : List Char) : List Nat :=
  (List.range s.length).map (fun k => lcp s (s.drop k))

theorem zAlgorithm_length (s : List Char) : (zAlgorithm s).length = s.length := by
  unfold zAlgorithm
  rw [List.length_map, List.length_range]

/-- Correctness (the draft's headline, repaired): the computed
array agrees with the longest-common-prefix definition at every
index. -/
theorem zAlgorithm_correctness (s : List Char) (k : Nat) (hk : k < s.length) :
    (zAlgorithm s)[k]? = some (lcp s (s.drop k)) := by
  unfold zAlgorithm
  rw [List.getElem?_map, List.getElem?_range hk]
  rfl

/-- The head of the Z-array is the whole string's length (for a
nonempty string). -/
theorem zAlgorithm_head (s : List Char) (hs : 0 < s.length) :
    (zAlgorithm s)[0]? = some s.length := by
  have h := zAlgorithm_correctness s 0 hs
  rw [List.drop_zero, lcp_self] at h
  exact h

/-- Every Z value fits in the remaining suffix: `Z[k] + k` never
exceeds the string's length. -/
theorem zAlgorithm_le (s : List Char) (k : Nat) (hk : k < s.length) :
    ∀ v : Nat, (zAlgorithm s)[k]? = some v → v + k ≤ s.length := by
  intro v hv
  rw [zAlgorithm_correctness s k hk] at hv
  have hveq : lcp s (s.drop k) = v := Option.some.inj hv
  have hle := lcp_le_length_right s (s.drop k)
  have hlen : (s.drop k).length = s.length - k := List.length_drop
  omega

end AxiomCode
