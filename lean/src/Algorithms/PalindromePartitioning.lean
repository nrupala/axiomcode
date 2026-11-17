import Spec
import Tactics

/-!
# Palindrome partitioning (minimum pieces)

The least number of palindromic pieces a string can be cut into,
computed by a fuelled dynamic program over first-piece choices:
`prefMin` ranges over the palindromic prefixes of the string and
takes the cheapest split `1 + minPal (rest)`, defaulting to the
string's length (the all-singletons cut, always available since
every singleton is a palindrome). The headline theorem
`palindrome_partitioning_correctness` states that the computed
value is the minimum piece count in both directions: a partition
into `minPal s` palindromic pieces exists, and every palindromic
partition of `s` has at least `minPal s` pieces.

The specification is the inductive `PalPartition` relation: a list
of pieces, each nonempty and a palindrome, whose concatenation is
the string.

The library works on `List Nat` (symbols as naturals), the
substrate the recent string/DP entries use (Rabin–Karp precedent);
the draft's `List Char` is ported.

## Draft defect record (promotion standard: defect + counterexample)

The draft (`lean/drafts/palindrome_partitioning_correctness.lean`)
did not elaborate: `PalindromePartition` was a fieldless structure,
so the headline's `partition.input` names a projection that does
not exist, and it imported Mathlib and Aesop, which this working
copy does not build.

Its statement was also vacuous. The theorem was
`∀ (input : List Char), ∃ (partition : PalindromePartition),
partition.input = input` — an ∃-form whose only constraint ties
the (nonexistent) `input` field to the input. It says nothing
about palindromes, nothing about pieces joining to the input, and
nothing about minimality: any structure with an `input` field
satisfies it by taking that field to be the input, so as stated it
certifies nothing about partitioning. The rulings package classed
the entry "∃-form, weak — re-spec at promotion".

## Repair (shape preserved)

The draft's theorem name is kept for the headline. The fieldless
structure is replaced by the real specification, the inductive
`PalPartition` relation, and the headline states of the authored
algorithm exactly what the draft gestured at: its value is the
piece count of an actual palindromic partition, and every
palindromic partition has at least that many pieces.
-/

namespace AxiomCode

/-- A list is a palindrome when it reads the same backwards. -/
def IsPalindrome (l : List Nat) : Prop := l = l.reverse

instance (l : List Nat) : Decidable (IsPalindrome l) :=
  inferInstanceAs (Decidable (l = l.reverse))

/-- Palindromic partitions: `PalPartition s ps` says the pieces
`ps` concatenate to `s`, each piece nonempty and a palindrome. -/
inductive PalPartition : List Nat → List (List Nat) → Prop
  | nil : PalPartition [] []
  | cons (p s : List Nat) (ps : List (List Nat)) :
      p ≠ [] → IsPalindrome p → PalPartition s ps →
      PalPartition (p ++ s) (p :: ps)

/-- The cheapest first-piece split among prefix lengths `1 … n`:
the minimum of `1 + g (s.drop k)` over palindromic prefixes
`s.take k` with `1 ≤ k ≤ n`, defaulting to `s.length` (the
all-singletons count) when no prefix qualifies or `n = 0`. -/
def prefMin (g : List Nat → Nat) (s : List Nat) : Nat → Nat
  | 0 => s.length
  | n + 1 => min (prefMin g s n)
      (if IsPalindrome (s.take (n + 1)) then 1 + g (s.drop (n + 1))
       else s.length)

theorem prefMin_zero (g : List Nat → Nat) (s : List Nat) :
    prefMin g s 0 = s.length := rfl

theorem prefMin_succ (g : List Nat → Nat) (s : List Nat) (n : Nat) :
    prefMin g s (n + 1) = min (prefMin g s n)
      (if IsPalindrome (s.take (n + 1)) then 1 + g (s.drop (n + 1))
       else s.length) := rfl

/-- `prefMin` depends on its cost function only at the split
points `s.drop (k + 1)` for `k ≤ n`. -/
theorem prefMin_congr (g₁ g₂ : List Nat → Nat) (s : List Nat) :
    ∀ n, (∀ k, k ≤ n → g₁ (s.drop (k + 1)) = g₂ (s.drop (k + 1))) →
      prefMin g₁ s n = prefMin g₂ s n := by
  intro n
  induction n with
  | zero => intro _; rfl
  | succ n ih =>
    intro h
    rw [prefMin_succ g₁, prefMin_succ g₂,
      ih (fun k hk => h k (by omega)), h n (by omega)]

/-- The default is an upper bound: considering more prefixes can
only lower (or keep) the cheapest split. -/
theorem prefMin_le_default (g : List Nat → Nat) (s : List Nat) :
    ∀ n, prefMin g s n ≤ s.length := by
  intro n
  induction n with
  | zero => exact Nat.le_refl _
  | succ n ih => rw [prefMin_succ]; omega

/-- Split bound: a palindromic prefix of length `k ≤ n` bounds the
cheapest split by its own cost. -/
theorem prefMin_le (g : List Nat → Nat) (s : List Nat) :
    ∀ n k, 1 ≤ k → k ≤ n → IsPalindrome (s.take k) →
      prefMin g s n ≤ 1 + g (s.drop k) := by
  intro n
  induction n with
  | zero => intro k h1 h2 _; omega
  | succ n ih =>
    intro k h1 h2 hpal
    rw [prefMin_succ]
    by_cases hk : k = n + 1
    · subst hk
      rw [ite_eq_left hpal]
      omega
    · have hle := ih k h1 (by omega) hpal
      omega

/-- Attainment: the cheapest split is either the default or is
attained at a specific palindromic prefix. -/
theorem prefMin_attained (g : List Nat → Nat) (s : List Nat) :
    ∀ n, prefMin g s n = s.length ∨
      ∃ k, 1 ≤ k ∧ k ≤ n ∧ IsPalindrome (s.take k) ∧
        prefMin g s n = 1 + g (s.drop k) := by
  intro n
  induction n with
  | zero => rw [prefMin_zero]; exact Or.inl rfl
  | succ n ih =>
    rw [prefMin_succ]
    by_cases hpal : IsPalindrome (s.take (n + 1))
    · rw [ite_eq_left hpal]
      by_cases hle : prefMin g s n ≤ 1 + g (s.drop (n + 1))
      · have hm : min (prefMin g s n) (1 + g (s.drop (n + 1)))
            = prefMin g s n := by omega
        rw [hm]
        rcases ih with h | ⟨k, h1, h2, h3, h4⟩
        · exact Or.inl h
        · exact Or.inr ⟨k, h1, by omega, h3, h4⟩
      · have hm : min (prefMin g s n) (1 + g (s.drop (n + 1)))
            = 1 + g (s.drop (n + 1)) := by omega
        rw [hm]
        exact Or.inr ⟨n + 1, by omega, by omega, hpal, rfl⟩
    · rw [ite_eq_right hpal]
      have hm : min (prefMin g s n) s.length = prefMin g s n := by
        have hd := prefMin_le_default g s n
        omega
      rw [hm]
      rcases ih with h | ⟨k, h1, h2, h3, h4⟩
      · exact Or.inl h
      · exact Or.inr ⟨k, h1, by omega, h3, h4⟩

/-- Fuelled worker for `minPal`. The fuel bounds the recursion:
each step consumes one unit and recurses on strictly shorter
suffixes. A fuel of zero returns `s.length`, a value the adequacy
lemma `minPalAux_irrel` shows is never seen at adequate fuel. -/
def minPalAux : Nat → List Nat → Nat
  | 0, s => s.length
  | _ + 1, [] => 0
  | f + 1, s => prefMin (minPalAux f) s s.length

theorem minPalAux_zero (s : List Nat) : minPalAux 0 s = s.length := rfl

theorem minPalAux_succ_nil (f : Nat) : minPalAux (f + 1) [] = 0 := rfl

theorem minPalAux_succ_cons (f : Nat) (a : Nat) (s : List Nat) :
    minPalAux (f + 1) (a :: s) =
      prefMin (minPalAux f) (a :: s) (a :: s).length := rfl

/-- Fuel irrelevance: once both fuels exceed the string length,
the worker's value no longer depends on the fuel. -/
theorem minPalAux_irrel : ∀ (f₁ f₂ : Nat) (s : List Nat),
    s.length < f₁ → s.length < f₂ → minPalAux f₁ s = minPalAux f₂ s := by
  intro f₁
  induction f₁ with
  | zero => intro f₂ s h₁ _; exact (Nat.not_lt_zero _ h₁).elim
  | succ f ih =>
    intro f₂ s h₁ h₂
    cases f₂ with
    | zero => exact (Nat.not_lt_zero _ h₂).elim
    | succ g =>
      cases s with
      | nil => rfl
      | cons a s =>
        simp only [List.length_cons] at h₁ h₂
        rw [minPalAux_succ_cons, minPalAux_succ_cons]
        apply prefMin_congr
        intro k _
        apply ih
        · rw [List.length_drop]
          simp only [List.length_cons]
          omega
        · rw [List.length_drop]
          simp only [List.length_cons]
          omega

/-- The minimum number of palindromic pieces: the worker at the
canonical fuel `s.length + 1`. -/
def minPal (s : List Nat) : Nat :=
  minPalAux (s.length + 1) s

/-- At any adequate fuel the worker computes `minPal`. -/
theorem minPalAux_eq_minPal (f : Nat) (s : List Nat)
    (hf : s.length < f) : minPalAux f s = minPal s :=
  minPalAux_irrel f (s.length + 1) s hf (by omega)

theorem minPal_nil : minPal [] = 0 := rfl

/-- The unfuelled recurrence, on a cons: the cheapest split with
the cost function itself at every suffix. -/
theorem minPal_cons (a : Nat) (s : List Nat) :
    minPal (a :: s) = prefMin minPal (a :: s) (a :: s).length := by
  have hunf : minPal (a :: s) =
      prefMin (minPalAux ((a :: s).length)) (a :: s) (a :: s).length := rfl
  rw [hunf]
  apply prefMin_congr
  intro j _
  apply minPalAux_eq_minPal
  rw [List.length_drop]
  simp only [List.length_cons]
  omega

/-- Split bound at the level of `minPal`: a palindromic prefix of
length `k` bounds the piece count by one plus the count of the
remaining suffix. -/
theorem minPal_le_split (s : List Nat) (hs : s ≠ []) (k : Nat)
    (h1 : 1 ≤ k) (h2 : k ≤ s.length) (hpal : IsPalindrome (s.take k)) :
    minPal s ≤ 1 + minPal (s.drop k) := by
  cases s with
  | nil => exact (hs rfl).elim
  | cons a s =>
    rw [minPal_cons]
    exact prefMin_le minPal (a :: s) (a :: s).length k h1 h2 hpal

/-- Attainment at the level of `minPal`: the piece count is
either the all-singletons count or is attained at a palindromic
prefix split. -/
theorem minPal_attained (s : List Nat) (hs : s ≠ []) :
    minPal s = s.length ∨
      ∃ k, 1 ≤ k ∧ k ≤ s.length ∧ IsPalindrome (s.take k) ∧
        minPal s = 1 + minPal (s.drop k) := by
  cases s with
  | nil => exact (hs rfl).elim
  | cons a s =>
    rw [minPal_cons]
    exact prefMin_attained minPal (a :: s) (a :: s).length

/-- The all-singletons partition: every singleton is a
palindrome, so every string has a palindromic partition with one
piece per symbol. -/
theorem palPartition_singletons : ∀ (s : List Nat),
    PalPartition s (s.map fun x => [x]) := by
  intro s
  induction s with
  | nil => exact PalPartition.nil
  | cons a s ih =>
    exact PalPartition.cons [a] s (s.map fun x => [x]) (by simp)
      (by rfl) ih

/-- Optimality: no palindromic partition beats the computed
count. Induction on the partition derivation; the first piece
`p` splits at `k = p.length`. -/
theorem minPal_le_of_partition : ∀ {s : List Nat} {ps : List (List Nat)},
    PalPartition s ps → minPal s ≤ ps.length := by
  intro s ps h
  induction h with
  | nil => exact Nat.zero_le _
  | cons p s ps hne hpal hrec ih =>
    obtain ⟨a, p', hp⟩ := List.exists_cons_of_ne_nil hne
    subst hp
    have htake : ((a :: p') ++ s).take (a :: p').length = a :: p' := by
      rw [List.take_append, List.take_of_length_le (Nat.le_refl _)]
      simp
    have hdrop : ((a :: p') ++ s).drop (a :: p').length = s := by
      rw [List.drop_append, List.drop_eq_nil_of_le (Nat.le_refl _)]
      simp
    have hsplit := minPal_le_split ((a :: p') ++ s) (by simp)
      (a :: p').length (by simp only [List.length_cons]; omega)
      (by simp only [List.length_append]; omega) (by rwa [htake])
    rw [hdrop] at hsplit
    simp only [List.length_cons]
    omega

/-- The computed count never exceeds the all-singletons count. -/
theorem minPal_le_length (s : List Nat) : minPal s ≤ s.length := by
  have h := minPal_le_of_partition (palPartition_singletons s)
  rwa [List.length_map] at h

/-- A nonempty palindrome needs exactly one piece. -/
theorem minPal_of_palindrome (s : List Nat) (hs : s ≠ [])
    (hpal : IsPalindrome s) : minPal s = 1 := by
  have hlen : 1 ≤ s.length := by
    cases s with
    | nil => exact (hs rfl).elim
    | cons a s => simp only [List.length_cons]; omega
  have htake : s.take s.length = s :=
    List.take_of_length_le (Nat.le_refl _)
  have hdrop : s.drop s.length = [] :=
    List.drop_eq_nil_of_le (Nat.le_refl _)
  have hle := minPal_le_split s hs s.length hlen (Nat.le_refl _)
    (by rwa [htake])
  rw [hdrop, minPal_nil] at hle
  rcases minPal_attained s hs with hatt | ⟨k, hk1, hk2, hkpal, hkEq⟩
  · omega
  · omega

/-- Achievability, in bounded form: a partition into exactly
`minPal s` pieces exists. Bounded strong induction on the string
length: the attained case splits off the first piece and recurses
on the strictly shorter suffix; the default case is the
all-singletons partition. -/
theorem exists_partition_of_minPal_aux : ∀ (k : Nat) (s : List Nat),
    s.length ≤ k → ∃ ps, PalPartition s ps ∧ ps.length = minPal s := by
  intro k
  induction k with
  | zero =>
    intro s h
    cases s with
    | nil => exact ⟨[], PalPartition.nil, by simp [minPal_nil]⟩
    | cons a s => simp [List.length_cons] at h
  | succ k ih =>
    intro s h
    cases s with
    | nil => exact ⟨[], PalPartition.nil, by simp [minPal_nil]⟩
    | cons a s =>
      have hs : (a :: s) ≠ [] := by simp
      rcases minPal_attained (a :: s) hs with hatt |
        ⟨j, hj1, hj2, hjpal, hjEq⟩
      · exact ⟨(a :: s).map fun x => [x], palPartition_singletons _,
          by rw [List.length_map]; exact hatt.symm⟩
      · have hdrop_len : ((a :: s).drop j).length ≤ k := by
          rw [List.length_drop]
          simp only [List.length_cons] at h ⊢
          omega
        obtain ⟨ps', hps', hlen'⟩ := ih ((a :: s).drop j) hdrop_len
        have hne : (a :: s).take j ≠ [] := by
          intro hnil
          have hl := congrArg List.length hnil
          rw [List.length_take] at hl
          change min j ((a :: s).length) = 0 at hl
          omega
        refine ⟨(a :: s).take j :: ps', ?_, ?_⟩
        · have hjoin : (a :: s).take j ++ (a :: s).drop j = a :: s :=
            List.take_append_drop j (a :: s)
          have hpart : PalPartition ((a :: s).take j ++ (a :: s).drop j)
              ((a :: s).take j :: ps') :=
            PalPartition.cons _ _ _ hne hjpal hps'
          rwa [hjoin] at hpart
        · show ps'.length + 1 = minPal (a :: s)
          omega

/-- Achievability: a partition into exactly `minPal s` pieces
exists. -/
theorem exists_partition_of_minPal (s : List Nat) :
    ∃ ps, PalPartition s ps ∧ ps.length = minPal s :=
  exists_partition_of_minPal_aux s.length s (Nat.le_refl _)

/-- Correctness (the draft's headline, repaired): the computed
value is the minimum palindromic piece count — a partition of
exactly that many pieces exists, and every palindromic partition
has at least that many pieces. -/
theorem palindrome_partitioning_correctness (s : List Nat) :
    (∃ ps, PalPartition s ps ∧ ps.length = minPal s) ∧
    ∀ ps, PalPartition s ps → minPal s ≤ ps.length :=
  ⟨exists_partition_of_minPal s,
   fun _ h => minPal_le_of_partition h⟩

end AxiomCode
