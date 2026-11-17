import Spec
import Tactics

/-!
# Rabin–Karp search

Rabin–Karp pattern search over `List Nat` (symbols as naturals),
in its Las Vegas form: a polynomial-hash pre-filter whose
candidates are verified by direct comparison, so the returned
positions are exactly the true occurrences.

## Draft defect record (promotion standard: defect + counterexample)

The draft (`lean/drafts/rabinkarpconfig.hash_correct.lean`) was a
shell: `RabinKarpConfig` was a fieldless structure; `hash` and
`rollHash` were written with `:=` and no body; its `hash_correct`
statement was a literal tautology — `hash s prime d = hash s
prime d` — closed by a proof placeholder; and its headline
`rabin_karp_correctness` quantified over `config.text` and
`config.pattern`, fields that do not exist on the fieldless
structure. Nothing is carried literally; the entry is authored
here, following the recon's direction ("hash subset first"): the
hash algebra the rolling update rests on, then the search.

## What is proved

`phash` is the polynomial hash in Horner form. Its algebra:
`phash_cons` (the head symbol's contribution), `phash_append`
(concatenation), `phash_split` (the extraction identity: a list's
hash is its prefix hash, shifted, plus the remainder's hash) and
`phash_window` (the same identity at two split points, which is
what a rolling window maintains). `phash_window_roll` is the roll
itself, stated for a full window (`i + m < t.length` — at the
text's edge the window truncates and the equation's exponent is
the taken length, not `m`; the hypothesis names exactly that).

The headline is `mem_rkSearch`: the returned positions are
precisely the starts of true occurrences. Soundness rests on the
direct-comparison verification in the filter; completeness on
hash congruence — a true occurrence's hash always matches, so the
pre-filter never drops it. No claim is made about collision
probabilities: the hash here is over `Nat` (unbounded), and the
modular variant's collision analysis is a probabilistic claim of
a different kind, outside this entry.
-/

namespace AxiomCode

/-- Polynomial hash in Horner form:
`phash d [c₀, c₁, …, cₙ₋₁] = c₀·dⁿ⁻¹ + c₁·dⁿ⁻² + … + cₙ₋₁`. -/
def phash (d : Nat) (cs : List Nat) : Nat :=
  cs.foldl (fun h c => h * d + c) 0

theorem phash_nil (d : Nat) : phash d [] = 0 := rfl

theorem phash_cons (d : Nat) (c : Nat) (cs : List Nat) :
    phash d (c :: cs) = c * d ^ cs.length + phash d cs := by
  have step : ∀ (l : List Nat) (h : Nat),
      l.foldl (fun acc x => acc * d + x) h =
        h * d ^ l.length + l.foldl (fun acc x => acc * d + x) 0 := by
    intro l
    induction l with
    | nil => intro h; simp
    | cons a l ih =>
      intro h
      simp only [List.foldl_cons, List.length_cons]
      rw [ih (h * d + a), ih (0 * d + a)]
      have e1 : (0 * d + a) * d ^ l.length = a * d ^ l.length := by simp
      rw [e1, Nat.pow_add_one, Nat.add_mul,
        Nat.mul_assoc h d (d ^ l.length), Nat.mul_comm d (d ^ l.length),
        Nat.add_assoc]
  unfold phash
  simp only [List.foldl_cons]
  rw [step cs (0 * d + c)]
  have e2 : (0 * d + c) * d ^ cs.length = c * d ^ cs.length := by simp
  rw [e2]

theorem phash_append (d : Nat) (a b : List Nat) :
    phash d (a ++ b) = phash d a * d ^ b.length + phash d b := by
  induction a with
  | nil => simp [phash_nil]
  | cons c a ih =>
    rw [List.cons_append, phash_cons, phash_cons, ih,
      List.length_append, Nat.pow_add]
    rw [Nat.add_mul, Nat.mul_assoc c (d ^ a.length) (d ^ b.length),
      Nat.add_assoc]

/-- Split: the hash of a list is the hash of any prefix, shifted,
plus the hash of the remainder. This is the extraction identity
the rolling window rests on. -/
theorem phash_split (d : Nat) (t : List Nat) (i : Nat) :
    phash d t = phash d (t.take i) * d ^ (t.length - i) + phash d (t.drop i) := by
  have key : phash d t = phash d (t.take i ++ t.drop i) := by
    rw [List.take_append_drop]
  rw [key, phash_append, List.length_drop]

/-- The window of length `m` starting at `i`. -/
def window (t : List Nat) (i m : Nat) : List Nat := (t.drop i).take m

/-- Window hash from the two split points, in equation form (no
subtraction): the hash of the whole list determines the window's
hash jointly with the prefix and suffix hashes. -/
theorem phash_window (d : Nat) (t : List Nat) (i m : Nat) :
    phash d (t.drop i) =
      phash d (window t i m) * d ^ (t.length - i - m) +
        phash d (t.drop (i + m)) := by
  have key : phash d (t.drop i) =
      phash d ((t.drop i).take m ++ (t.drop i).drop m) := by
    rw [List.take_append_drop]
  unfold window
  rw [key, phash_append, List.length_drop, List.length_drop, List.drop_drop]

/-- The roll: the hash of the length-`m+1` window at `i` splits
into the outgoing symbol's contribution and the hash of the
length-`m` window at `i+1`. Iterating this against `phash_window`
is the rolling update. -/
theorem phash_window_roll (d : Nat) (t : List Nat) (i m : Nat)
    (h : i < t.length) (hm : i + m < t.length) :
    phash d (window t i (m + 1)) =
      t[i] * d ^ m + phash d (window t (i + 1) m) := by
  unfold window
  rw [← List.getElem_cons_drop h, List.take_succ_cons, phash_cons,
    List.length_take, List.length_drop]
  have hmin : min m (t.length - (i + 1)) = m := by omega
  rw [hmin]

/-- Rabin–Karp search, Las Vegas form: every start position whose
window's hash matches the pattern's hash AND whose window verifies
by direct comparison. The hash is a pre-filter; correctness rests
on the verification. -/
def rkSearch (d : Nat) (text pat : List Nat) : List Nat :=
  (List.range (text.length + 1 - pat.length)).filter (fun i =>
    decide (phash d (window text i pat.length) = phash d pat ∧
      window text i pat.length = pat))

/-- The search is exact: it returns precisely the start positions
of true occurrences. The forward direction is the verification
(soundness); the backward direction is hash congruence — a true
occurrence's hash always matches, so the pre-filter never drops
it (completeness). -/
theorem mem_rkSearch {d : Nat} {text pat : List Nat} {i : Nat} :
    i ∈ rkSearch d text pat ↔
      i + pat.length ≤ text.length ∧ window text i pat.length = pat := by
  unfold rkSearch
  rw [List.mem_filter, List.mem_range]
  constructor
  · intro h
    obtain ⟨h1, h2⟩ := h
    rw [decide_eq_true_eq] at h2
    exact ⟨by omega, h2.2⟩
  · intro h
    refine ⟨by omega, ?_⟩
    rw [decide_eq_true_eq]
    exact ⟨by rw [h.2], h.2⟩

end AxiomCode
