import Spec
import Tactics

/-!
# Manacher's algorithm — palindromic radii (naive form)

Manacher's algorithm computes, for every center of a string, the
radius of the longest palindrome around that center: the odd radii
`d₁[c]` (palindromes `s[c - r + 1 .. c + r - 1]` of length
`2 * r - 1` in the classical indexing) and the even radii `d₂[c]`
(palindromes `s[c - r .. c + r - 1]` of length `2 * r`). This entry
works over `List Nat` (symbols as naturals) and indexes radii by
*matched pairs*: `oddRadius s c` is the number of matching symbol
pairs around the odd center `c` — the longest palindrome centered
at `c` is `(s.drop (c - oddRadius s c)).take (2 * oddRadius s c + 1)`
— and `evenRadius s c` is the number of matching pairs around the
gap before `c`, with longest palindrome
`(s.drop (c - evenRadius s c)).take (2 * evenRadius s c)`.

Following the Z-function entry's precedent, the radii are computed
by the naive definition — direct expansion, here expressed as a
longest common prefix of the reversed left part and the right part
— and the entry certifies the computed radii against the
palindrome specification: the radius window is a palindrome
(`oddRadius_window`, `evenRadius_window`), and one pair more is
not (`oddRadius_window_succ`, `evenRadius_window_succ`), under the
stated in-bounds hypotheses. The linear-time algorithm, which
reuses previously computed radii instead of expanding each center
from scratch, is a named non-goal of this entry: the entry
certifies the naive computation against the specification any
optimized version must also meet.

## Draft defect record (promotion standard: defect + counterexample)

The draft (`lean/drafts/manachersalgorithm_correctness.lean`) did
not elaborate, in three independent ways. `ManachersResult` was a
fieldless structure, so the headline statement's projections
`result.center`, `result.right` and `result.lengths` name fields
that do not exist. `manachersAlgorithm` was written with `:=` and
no body. And the one concrete claim, `result.lengths[i] = 2 *
(result.center - i) + 1` for all `i < result.center`, is false as
a characterization of palindromic radii: radii depend on the
string's content, not on a center alone. Counterexample: for
`s = [0, 1]` every palindromic radius is `0` pairs (the two symbols
differ, and no longer window exists), so every correct radius
array has all entries `0`; the formula with `center = 1` forces
`lengths[0] = 2 * (1 - 0) + 1 = 3`, the length of a window that
cannot even fit in a string of length `2`. With `center = 0` the
quantified clause is vacuous and the statement says nothing about
any computed value at all.

## Repair (shape preserved)

The draft's function and theorem names are kept.
`manachersAlgorithm` returns the pair of radius arrays (odd,
even) — the actual output of Manacher's algorithm — as plain
`List Nat`s over `List Nat`. The headline
`manachersAlgorithm_correctness` is the pointwise characterization:
at every index `c`, the arrays hold exactly `oddRadius s c` and
`evenRadius s c`; the radius theorems then pin those values to the
palindrome specification from both sides (the radius window is a
palindrome, and the next window out is not).
-/

namespace AxiomCode

/-- The longest common prefix length of two symbol lists: how many
leading symbols they share. -/
def lcpN : List Nat → List Nat → Nat
  | [], _ => 0
  | _, [] => 0
  | a :: s, b :: t => if a = b then lcpN s t + 1 else 0

theorem lcpN_nil_left (t : List Nat) : lcpN [] t = 0 := rfl

theorem lcpN_nil_right (s : List Nat) : lcpN s [] = 0 := by
  cases s <;> rfl

theorem lcpN_cons_cons (a : Nat) (s : List Nat) (b : Nat) (t : List Nat) :
    lcpN (a :: s) (b :: t) = if a = b then lcpN s t + 1 else 0 := rfl

/-- A common prefix is no longer than the first list. -/
theorem lcpN_le_length_left : ∀ (s t : List Nat), lcpN s t ≤ s.length := by
  intro s
  induction s with
  | nil => intro t; exact Nat.zero_le _
  | cons a s ih =>
    intro t
    cases t with
    | nil => rw [lcpN_nil_right]; exact Nat.zero_le _
    | cons b t =>
      by_cases hab : a = b
      · rw [lcpN_cons_cons, if_pos hab]
        have ih' := ih t
        simp only [List.length_cons]
        omega
      · rw [lcpN_cons_cons, if_neg hab]
        exact Nat.zero_le _

/-- A common prefix is no longer than the second list. -/
theorem lcpN_le_length_right : ∀ (s t : List Nat), lcpN s t ≤ t.length := by
  intro s
  induction s with
  | nil => intro t; exact Nat.zero_le _
  | cons a s ih =>
    intro t
    cases t with
    | nil => rw [lcpN_nil_right]; exact Nat.zero_le _
    | cons b t =>
      by_cases hab : a = b
      · rw [lcpN_cons_cons, if_pos hab]
        have ih' := ih t
        simp only [List.length_cons]
        omega
      · rw [lcpN_cons_cons, if_neg hab]
        exact Nat.zero_le _

/-- The two lists agree on their first `lcpN` symbols. -/
theorem take_lcpN_eq : ∀ (a b : List Nat), a.take (lcpN a b) = b.take (lcpN a b) := by
  intro a
  induction a with
  | nil => intro b; rfl
  | cons a as ih =>
    intro b
    cases b with
    | nil => rfl
    | cons b bs =>
      by_cases hab : a = b
      · rw [lcpN_cons_cons, if_pos hab, List.take_succ_cons, List.take_succ_cons,
          ih bs, hab]
      · rw [lcpN_cons_cons, if_neg hab, List.take_zero, List.take_zero]

/-- Agreement on the first `r` symbols, with `r` in bounds on both
sides, bounds the longest common prefix from below. -/
theorem lcpN_max : ∀ (a b : List Nat) (r : Nat),
    a.take r = b.take r → r ≤ a.length → r ≤ b.length → r ≤ lcpN a b := by
  intro a
  induction a with
  | nil =>
    intro b r _ hr _
    simp only [List.length_nil] at hr
    omega
  | cons a as ih =>
    intro b r h hr hb
    cases b with
    | nil =>
      simp only [List.length_nil] at hb
      omega
    | cons b bs =>
      cases r with
      | zero => exact Nat.zero_le _
      | succ r =>
        rw [List.take_succ_cons, List.take_succ_cons] at h
        injection h with hab htake
        have hr' : r ≤ as.length := by
          simp only [List.length_cons] at hr
          omega
        have hb' : r ≤ bs.length := by
          simp only [List.length_cons] at hb
          omega
        have hle := ih bs r htake hr' hb'
        rw [lcpN_cons_cons, if_pos hab]
        omega

/-- The pair-matching condition for an odd center: the `r` symbols
to the left of `c`, read outward, equal the `r` symbols to the
right of `c`. -/
def OddPairs (s : List Nat) (c r : Nat) : Prop :=
  ((s.take c).reverse).take r = (s.drop (c + 1)).take r

/-- The pair-matching condition for an even center (the gap before
`c`): the `r` symbols to the left of the gap, read outward, equal
the `r` symbols to its right. -/
def EvenPairs (s : List Nat) (c r : Nat) : Prop :=
  ((s.take c).reverse).take r = (s.drop c).take r

/-- The odd radius at `c`: the number of matching pairs around the
center `c`, computed by direct expansion — the longest common
prefix of the reversed left part and the right part. -/
def oddRadius (s : List Nat) (c : Nat) : Nat :=
  lcpN (s.take c).reverse (s.drop (c + 1))

/-- The even radius at `c`: the number of matching pairs around
the gap before `c`. -/
def evenRadius (s : List Nat) (c : Nat) : Nat :=
  lcpN (s.take c).reverse (s.drop c)

/-- The odd radius never exceeds the number of symbols to the
left. -/
theorem oddRadius_le_center (s : List Nat) (c : Nat) : oddRadius s c ≤ c := by
  have h := lcpN_le_length_left (s.take c).reverse (s.drop (c + 1))
  rw [List.length_reverse, List.length_take] at h
  exact Nat.le_trans h (Nat.min_le_left _ _)

/-- The odd radius never exceeds the number of symbols to the
right. -/
theorem oddRadius_le_drop (s : List Nat) (c : Nat) :
    oddRadius s c ≤ (s.drop (c + 1)).length :=
  lcpN_le_length_right _ _

/-- The even radius never exceeds the number of symbols to the
left. -/
theorem evenRadius_le_center (s : List Nat) (c : Nat) : evenRadius s c ≤ c := by
  have h := lcpN_le_length_left (s.take c).reverse (s.drop c)
  rw [List.length_reverse, List.length_take] at h
  exact Nat.le_trans h (Nat.min_le_left _ _)

/-- The even radius never exceeds the number of symbols to the
right. -/
theorem evenRadius_le_drop (s : List Nat) (c : Nat) :
    evenRadius s c ≤ (s.drop c).length :=
  lcpN_le_length_right _ _

/-- The computed odd radius does match its pairs. -/
theorem oddRadius_pairs (s : List Nat) (c : Nat) : OddPairs s c (oddRadius s c) :=
  take_lcpN_eq _ _

/-- The computed even radius does match its pairs. -/
theorem evenRadius_pairs (s : List Nat) (c : Nat) : EvenPairs s c (evenRadius s c) :=
  take_lcpN_eq _ _

/-- Any in-bounds matching pair count is at most the computed odd
radius. -/
theorem oddRadius_max (s : List Nat) (c r : Nat) (hp : OddPairs s c r)
    (hr : r ≤ c) (hb : c + 1 + r ≤ s.length) : r ≤ oddRadius s c := by
  apply lcpN_max _ _ _ hp
  · rw [List.length_reverse, List.length_take]
    omega
  · rw [List.length_drop]
    omega

/-- Any in-bounds matching pair count is at most the computed even
radius. -/
theorem evenRadius_max (s : List Nat) (c r : Nat) (hp : EvenPairs s c r)
    (hr : r ≤ c) (hb : c + r ≤ s.length) : r ≤ evenRadius s c := by
  apply lcpN_max _ _ _ hp
  · rw [List.length_reverse, List.length_take]
    omega
  · rw [List.length_drop]
    omega

/-- The `r` symbols immediately left of `c`, reversed, are the
first `r` symbols of the reversed left part. -/
theorem take_left_window (s : List Nat) (c r : Nat) (hr : r ≤ c) (hc : c ≤ s.length) :
    ((s.drop (c - r)).take r).reverse = ((s.take c).reverse).take r := by
  have hA : ((s.drop (c - r)).take r).length = r := by
    rw [List.length_take, List.length_drop]
    omega
  have hsplit : s.take c = s.take (c - r) ++ (s.drop (c - r)).take r := by
    have h := List.take_append_drop (c - r) (s.take c)
    rw [List.take_take, List.drop_take] at h
    have e1 : min (c - r) c = c - r := by omega
    have e2 : c - (c - r) = r := by omega
    rw [e1, e2] at h
    exact h.symm
  rw [hsplit, List.reverse_append]
  exact (List.take_left' (by rw [List.length_reverse]; exact hA)).symm

/-- Decomposition of the odd radius window: the `r` symbols left
of the center, the center symbol, the `r` symbols right of it. -/
theorem odd_window_decomp (s : List Nat) (c r : Nat) (hr : r ≤ c) (hc : c < s.length) :
    (s.drop (c - r)).take (2 * r + 1) =
      (s.drop (c - r)).take r ++ s[c] :: (s.drop (c + 1)).take r := by
  have hA : ((s.drop (c - r)).take r).length = r := by
    rw [List.length_take, List.length_drop]
    omega
  have hdrop : s.drop (c - r) = (s.drop (c - r)).take r ++ s.drop c := by
    have h := List.take_append_drop r (s.drop (c - r))
    rw [List.drop_drop] at h
    have e : c - r + r = c := Nat.sub_add_cancel hr
    rw [e] at h
    exact h.symm
  have hmid : s.drop c = s[c] :: s.drop (c + 1) := (List.getElem_cons_drop hc).symm
  have hle : ((s.drop (c - r)).take r).length ≤ 2 * r + 1 := by omega
  have e2 : 2 * r + 1 - r = r + 1 := by omega
  have step1 : (s.drop (c - r)).take (2 * r + 1) =
      ((s.drop (c - r)).take r ++ s.drop c).take (2 * r + 1) :=
    congrArg (List.take (2 * r + 1)) hdrop
  have step2 : ((s.drop (c - r)).take r ++ s.drop c).take (2 * r + 1) =
      ((s.drop (c - r)).take r ++ s[c] :: s.drop (c + 1)).take (2 * r + 1) :=
    congrArg (List.take (2 * r + 1)) (congrArg ((s.drop (c - r)).take r ++ ·) hmid)
  have step3 : ((s.drop (c - r)).take r ++ s[c] :: s.drop (c + 1)).take (2 * r + 1) =
      (s.drop (c - r)).take r ++ s[c] :: (s.drop (c + 1)).take r := by
    rw [List.take_append, hA, List.take_of_length_le hle, e2, List.take_succ_cons]
  exact step1.trans (step2.trans step3)

/-- Decomposition of the even radius window: the `r` symbols left
of the gap, then the `r` symbols right of it. -/
theorem even_window_decomp (s : List Nat) (c r : Nat) (hr : r ≤ c) (hc : c ≤ s.length) :
    (s.drop (c - r)).take (2 * r) =
      (s.drop (c - r)).take r ++ (s.drop c).take r := by
  have hA : ((s.drop (c - r)).take r).length = r := by
    rw [List.length_take, List.length_drop]
    omega
  have hdrop : s.drop (c - r) = (s.drop (c - r)).take r ++ s.drop c := by
    have h := List.take_append_drop r (s.drop (c - r))
    rw [List.drop_drop] at h
    have e : c - r + r = c := Nat.sub_add_cancel hr
    rw [e] at h
    exact h.symm
  have hle : ((s.drop (c - r)).take r).length ≤ 2 * r := by omega
  have e2 : 2 * r - r = r := by omega
  have step1 : (s.drop (c - r)).take (2 * r) =
      ((s.drop (c - r)).take r ++ s.drop c).take (2 * r) :=
    congrArg (List.take (2 * r)) hdrop
  have step2 : ((s.drop (c - r)).take r ++ s.drop c).take (2 * r) =
      (s.drop (c - r)).take r ++ (s.drop c).take r := by
    rw [List.take_append, hA, List.take_of_length_le hle, e2]
  exact step1.trans step2

/-- Bridge, odd case: matching pairs make the radius window a
palindrome of the full length. -/
theorem odd_palindrome_of_pairs (s : List Nat) (c r : Nat) (hr : r ≤ c)
    (hc : c < s.length) (hlen : r ≤ (s.drop (c + 1)).length) (hp : OddPairs s c r) :
    (s.drop (c - r)).take (2 * r + 1) =
        ((s.drop (c - r)).take (2 * r + 1)).reverse ∧
      ((s.drop (c - r)).take (2 * r + 1)).length = 2 * r + 1 := by
  have hA : ((s.drop (c - r)).take r).length = r := by
    rw [List.length_take, List.length_drop]
    omega
  have hB : ((s.drop (c + 1)).take r).length = r := by
    rw [List.length_take]
    omega
  have hrevA : ((s.drop (c - r)).take r).reverse = (s.drop (c + 1)).take r := by
    rw [take_left_window s c r hr (Nat.le_of_lt hc)]
    exact hp
  have hrevB : ((s.drop (c + 1)).take r).reverse = (s.drop (c - r)).take r := by
    rw [← hrevA, List.reverse_reverse]
  constructor
  · rw [odd_window_decomp s c r hr hc, List.reverse_append, List.reverse_cons,
      hrevA, hrevB, List.append_assoc, List.singleton_append]
  · rw [odd_window_decomp s c r hr hc, List.length_append, hA, List.length_cons, hB]
    omega

/-- Bridge, odd case: a palindromic radius window means the pairs
match. -/
theorem odd_pairs_of_palindrome (s : List Nat) (c r : Nat) (hr : r ≤ c)
    (hc : c < s.length) (hlen : r ≤ (s.drop (c + 1)).length)
    (hpal : (s.drop (c - r)).take (2 * r + 1) =
      ((s.drop (c - r)).take (2 * r + 1)).reverse) :
    OddPairs s c r := by
  have hA : ((s.drop (c - r)).take r).length = r := by
    rw [List.length_take, List.length_drop]
    omega
  have hB : ((s.drop (c + 1)).take r).length = r := by
    rw [List.length_take]
    omega
  rw [odd_window_decomp s c r hr hc, List.reverse_append, List.reverse_cons] at hpal
  have htake : (s.drop (c - r)).take r = ((s.drop (c + 1)).take r).reverse := by
    have h := congrArg (List.take r) hpal
    rw [List.take_left' hA, List.append_assoc,
      List.take_left' (by rw [List.length_reverse]; exact hB)] at h
    exact h
  have hrevA : ((s.drop (c - r)).take r).reverse = (s.drop (c + 1)).take r := by
    rw [htake, List.reverse_reverse]
  show ((s.take c).reverse).take r = (s.drop (c + 1)).take r
  rw [← take_left_window s c r hr (Nat.le_of_lt hc)]
  exact hrevA

/-- Bridge, even case: matching pairs make the radius window a
palindrome of the full length. -/
theorem even_palindrome_of_pairs (s : List Nat) (c r : Nat) (hr : r ≤ c)
    (hc : c ≤ s.length) (hlen : r ≤ (s.drop c).length) (hp : EvenPairs s c r) :
    (s.drop (c - r)).take (2 * r) =
        ((s.drop (c - r)).take (2 * r)).reverse ∧
      ((s.drop (c - r)).take (2 * r)).length = 2 * r := by
  have hA : ((s.drop (c - r)).take r).length = r := by
    rw [List.length_take, List.length_drop]
    omega
  have hB : ((s.drop c).take r).length = r := by
    rw [List.length_take]
    omega
  have hrevA : ((s.drop (c - r)).take r).reverse = (s.drop c).take r := by
    rw [take_left_window s c r hr hc]
    exact hp
  have hrevB : ((s.drop c).take r).reverse = (s.drop (c - r)).take r := by
    rw [← hrevA, List.reverse_reverse]
  constructor
  · rw [even_window_decomp s c r hr hc, List.reverse_append, hrevA, hrevB]
  · rw [even_window_decomp s c r hr hc, List.length_append, hA, hB]
    omega

/-- Bridge, even case: a palindromic radius window means the
pairs match. -/
theorem even_pairs_of_palindrome (s : List Nat) (c r : Nat) (hr : r ≤ c)
    (hc : c ≤ s.length) (hlen : r ≤ (s.drop c).length)
    (hpal : (s.drop (c - r)).take (2 * r) =
      ((s.drop (c - r)).take (2 * r)).reverse) :
    EvenPairs s c r := by
  have hA : ((s.drop (c - r)).take r).length = r := by
    rw [List.length_take, List.length_drop]
    omega
  have hB : ((s.drop c).take r).length = r := by
    rw [List.length_take]
    omega
  rw [even_window_decomp s c r hr hc, List.reverse_append] at hpal
  have htake : (s.drop (c - r)).take r = ((s.drop c).take r).reverse := by
    have h := congrArg (List.take r) hpal
    rw [List.take_left' hA,
      List.take_left' (by rw [List.length_reverse]; exact hB)] at h
    exact h
  have hrevA : ((s.drop (c - r)).take r).reverse = (s.drop c).take r := by
    rw [htake, List.reverse_reverse]
  show ((s.take c).reverse).take r = (s.drop c).take r
  rw [← take_left_window s c r hr hc]
  exact hrevA

/-- The odd radius window is a palindrome of length
`2 * oddRadius s c + 1`. -/
theorem oddRadius_window (s : List Nat) (c : Nat) (hc : c < s.length) :
    (s.drop (c - oddRadius s c)).take (2 * oddRadius s c + 1) =
        ((s.drop (c - oddRadius s c)).take (2 * oddRadius s c + 1)).reverse ∧
      ((s.drop (c - oddRadius s c)).take (2 * oddRadius s c + 1)).length =
        2 * oddRadius s c + 1 :=
  odd_palindrome_of_pairs s c (oddRadius s c) (oddRadius_le_center s c) hc
    (oddRadius_le_drop s c) (oddRadius_pairs s c)

/-- The even radius window is a palindrome of length
`2 * evenRadius s c`. -/
theorem evenRadius_window (s : List Nat) (c : Nat) (hc : c ≤ s.length) :
    (s.drop (c - evenRadius s c)).take (2 * evenRadius s c) =
        ((s.drop (c - evenRadius s c)).take (2 * evenRadius s c)).reverse ∧
      ((s.drop (c - evenRadius s c)).take (2 * evenRadius s c)).length =
        2 * evenRadius s c :=
  even_palindrome_of_pairs s c (evenRadius s c) (evenRadius_le_center s c) hc
    (evenRadius_le_drop s c) (evenRadius_pairs s c)

/-- One pair beyond the odd radius, when that window is in
bounds, is not a palindrome: the computed radius is the longest
one. -/
theorem oddRadius_window_succ (s : List Nat) (c : Nat)
    (h1 : oddRadius s c + 1 ≤ c) (h2 : c + (oddRadius s c + 1) < s.length) :
    ¬ ((s.drop (c - (oddRadius s c + 1))).take (2 * (oddRadius s c + 1) + 1) =
        ((s.drop (c - (oddRadius s c + 1))).take (2 * (oddRadius s c + 1) + 1)).reverse) := by
  intro hpal
  have hp : OddPairs s c (oddRadius s c + 1) :=
    odd_pairs_of_palindrome s c (oddRadius s c + 1) h1 (by omega)
      (by rw [List.length_drop]; omega) hpal
  have hle := oddRadius_max s c (oddRadius s c + 1) hp h1 (by omega)
  omega

/-- One pair beyond the even radius, when that window is in
bounds, is not a palindrome: the computed radius is the longest
one. -/
theorem evenRadius_window_succ (s : List Nat) (c : Nat)
    (h1 : evenRadius s c + 1 ≤ c) (h2 : c + (evenRadius s c + 1) ≤ s.length) :
    ¬ ((s.drop (c - (evenRadius s c + 1))).take (2 * (evenRadius s c + 1)) =
        ((s.drop (c - (evenRadius s c + 1))).take (2 * (evenRadius s c + 1))).reverse) := by
  intro hpal
  have hp : EvenPairs s c (evenRadius s c + 1) :=
    even_pairs_of_palindrome s c (evenRadius s c + 1) h1 (by omega)
      (by rw [List.length_drop]; omega) hpal
  have hle := evenRadius_max s c (evenRadius s c + 1) hp h1 h2
  omega

/-- The odd radius array: `oddRadius` at every index. -/
def manacherOdd (s : List Nat) : List Nat :=
  (List.range s.length).map (oddRadius s)

/-- The even radius array: `evenRadius` at every index. -/
def manacherEven (s : List Nat) : List Nat :=
  (List.range s.length).map (evenRadius s)

/-- Manacher's algorithm: the pair of radius arrays (odd, even)
for the string. -/
def manachersAlgorithm (s : List Nat) : List Nat × List Nat :=
  (manacherOdd s, manacherEven s)

theorem manacherOdd_length (s : List Nat) : (manacherOdd s).length = s.length := by
  unfold manacherOdd
  rw [List.length_map, List.length_range]

theorem manacherEven_length (s : List Nat) : (manacherEven s).length = s.length := by
  unfold manacherEven
  rw [List.length_map, List.length_range]

/-- Correctness (the draft's headline, repaired): the computed
arrays agree with the radius definitions at every index. -/
theorem manachersAlgorithm_correctness (s : List Nat) (c : Nat) (hc : c < s.length) :
    (manachersAlgorithm s).1[c]? = some (oddRadius s c) ∧
      (manachersAlgorithm s).2[c]? = some (evenRadius s c) := by
  constructor
  · show (manacherOdd s)[c]? = some (oddRadius s c)
    unfold manacherOdd
    rw [List.getElem?_map, List.getElem?_range hc]
    rfl
  · show (manacherEven s)[c]? = some (evenRadius s c)
    unfold manacherEven
    rw [List.getElem?_map, List.getElem?_range hc]
    rfl

end AxiomCode
