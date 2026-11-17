import Spec
import Tactics
import Algorithms.ProductExceptSelf
import Algorithms.RainWater

/-!
# AxiomCode — Verified Candy Distribution

Promoted from `lean/drafts/each_child_gets_one_candy (dist.lean`
under the L2 promotion procedure (`lean/PROMOTION.md`). The draft
names no algorithm: its `CandyDistribution` is a fieldless shell
and its first three theorems quantify over an *arbitrary*
distribution `dist`. The algorithm authored here is the fair
share: with `q = candies / children` and `r = candies % children`,
the first `r` children get `q + 1` candies and the rest get `q`
(`distribute`), packaged as `candyDistribution`.

Statement honesty, three records:

1. **Theorems 1–3 are FALSE as stated** — over an arbitrary
   distribution. The all-zeros distribution refutes 1 (no child
   gets a candy) and 2 (the total is `0`, not `candies`); a spiked
   distribution refutes 3 (`children = 2`, `candies = 4`,
   distribution `[4, 0]`: child `0` gets `4 > 4 / 2 + 1 = 3`). They
   are carried as claims about the authored algorithm's output,
   which is what the draft's doc comment ("the correctness of the
   candy distribution algorithm") intends. Theorem 2 additionally
   needs `0 < children`, which the draft omits: at `children = 0`
   the distribution is empty and sums to `0 ≠ candies`.
2. The draft's `∑ i in Finset.range …` sums are Mathlib notation;
   the library is Mathlib-free, so the totals are carried as
   `List.sum` of the distribution (the same quantity: the sum of
   the entries). The draft's proof-carrying indexing is carried in
   the library's `!` form.
3. Theorem 4 *is* a claim about an arbitrary distribution and is
   carried as one, with the draft's three hypotheses. One further
   hypothesis is authoring-forced and recorded: the draft indexes
   `dist.distribution[i]` for `i < dist.children` and sums over
   `Finset.range dist.children`, which presupposes
   `dist.distribution.length = dist.children`; it is stated
   explicitly as `hlen`.
-/

namespace AxiomCode

/-- A candy distribution: `distribution[i]` is the number of
candies child `i` receives. -/
structure CandyDistribution where
  children : Nat
  distribution : List Nat
deriving DecidableEq, Repr

/-- The fair-share distribution of `candies` among `children`:
every child gets `candies / children`, and the first
`candies % children` children get one extra. -/
def distribute (candies children : Nat) : List Nat :=
  (List.range children).map
    (fun i => candies / children + if i < candies % children then 1 else 0)

/-- The distribution produced by the fair-share algorithm. -/
def candyDistribution (candies children : Nat) : CandyDistribution :=
  ⟨children, distribute candies children⟩

/-- Entry `i` of the fair-share distribution. -/
theorem getElem!_distribute (candies children i : Nat) (hi : i < children) :
    (distribute candies children)[i]! =
      candies / children + if i < candies % children then 1 else 0 := by
  show ((List.range children).map
    (fun i => candies / children + if i < candies % children then 1 else 0))[i]! = _
  rw [getElem!_map_of_lt (by rw [List.length_range]; exact hi),
    getElem!_eq_getElem_of_lt (by rw [List.length_range]; exact hi),
    List.getElem_range]

/-- The draft's first theorem, about the authored algorithm's
output: when there are at least as many candies as children, every
child gets at least one candy. -/
theorem each_child_gets_one_candy (candies children : Nat)
    (h : children ≤ candies) :
    ∀ i < children,
      (candyDistribution candies children).distribution[i]! > 0 := by
  intro i hi
  show (distribute candies children)[i]! > 0
  rw [getElem!_distribute candies children i hi]
  have hq : 0 < candies / children := Nat.div_pos h (by omega)
  by_cases h2 : i < candies % children
  · simp only [h2, ite_true]
    omega
  · simp only [h2, ite_false]
    omega

/-- Summing a constant over a range. -/
theorem sum_range_const (q : Nat) :
    ∀ n : Nat, ((List.range n).map (fun _ => q)).sum = n * q := by
  intro n
  induction n with
  | zero => simp
  | succ n ih =>
    rw [List.range_succ, List.map_append, List.sum_append, ih,
      List.map_cons, List.map_nil, List.sum_cons, List.sum_nil,
      Nat.add_zero, Nat.succ_mul]

/-- The sum of pointwise sums over a list splits. -/
theorem sum_map_add {f g : Nat → Nat} (l : List Nat) :
    (l.map (fun i => f i + g i)).sum = (l.map f).sum + (l.map g).sum := by
  induction l with
  | nil => rfl
  | cons a l ih =>
    rw [List.map_cons, List.map_cons, List.map_cons, List.sum_cons,
      List.sum_cons, List.sum_cons, ih]
    omega

/-- The sum of the indicator `i < r` over `range n`, when the
threshold covers the whole range. -/
theorem sum_range_indicator_ge (r : Nat) :
    ∀ n : Nat, n ≤ r →
      ((List.range n).map (fun i => if i < r then 1 else 0)).sum = n := by
  intro n
  induction n with
  | zero => intro _; rfl
  | succ n ih =>
    intro hn
    rw [List.range_succ, List.map_append, List.sum_append,
      ih (by omega), List.map_cons, List.map_nil, List.sum_cons,
      List.sum_nil, Nat.add_zero,
      show (if n < r then (1 : Nat) else 0) = 1 from
        ite_eq_left (by omega : n < r)]

/-- The sum of the indicator `i < r` over `range n` is `r` when
`r ≤ n`. -/
theorem sum_range_indicator (r : Nat) :
    ∀ n : Nat, r ≤ n →
      ((List.range n).map (fun i => if i < r then 1 else 0)).sum = r := by
  intro n
  induction n with
  | zero =>
    intro h
    have : r = 0 := by omega
    rw [this]
    rfl
  | succ n ih =>
    intro hn
    rw [List.range_succ, List.map_append, List.sum_append,
      List.map_cons, List.map_nil, List.sum_cons, List.sum_nil,
      Nat.add_zero]
    by_cases hcase : r = n + 1
    · rw [sum_range_indicator_ge r n (by omega),
        show (if n < r then (1 : Nat) else 0) = 1 from
          ite_eq_left (by omega : n < r), hcase]
    · rw [ih (by omega),
        show (if n < r then (1 : Nat) else 0) = 0 from
          ite_eq_right (by omega : ¬ n < r), Nat.add_zero]

/-- The draft's second theorem, about the authored algorithm's
output: the total distributed is exactly `candies`. -/
theorem total_candies_distributed (candies children : Nat)
    (hch : 0 < children) :
    (candyDistribution candies children).distribution.sum = candies := by
  show (distribute candies children).sum = candies
  have hsplit :
      (distribute candies children).sum =
        ((List.range children).map (fun _ => candies / children)).sum +
        ((List.range children).map
          (fun i => if i < candies % children then 1 else 0)).sum :=
    sum_map_add (List.range children)
  rw [hsplit, sum_range_const,
    sum_range_indicator _ _ (by
      have := Nat.mod_lt candies hch
      omega),
    Nat.div_add_mod]

/-- The draft's third theorem, about the authored algorithm's
output: no child gets more than `candies / children + 1`. -/
theorem no_child_gets_too_many_candies (candies children : Nat) :
    ∀ i < children,
      (candyDistribution candies children).distribution[i]! ≤
        candies / children + 1 := by
  intro i hi
  show (distribute candies children)[i]! ≤ candies / children + 1
  rw [getElem!_distribute candies children i hi]
  by_cases h2 : i < candies % children
  · simp only [h2, ite_true]
    omega
  · simp only [h2, ite_false]
    omega

/-- A list whose every entry (by index) is at most `q` sums to at
most `length * q`. -/
theorem sum_le_of_getElem!_le {l : List Nat} {q : Nat}
    (h : ∀ j, j < l.length → l[j]! ≤ q) : l.sum ≤ l.length * q := by
  induction l with
  | nil => simp
  | cons a l ih =>
    rw [List.sum_cons, List.length_cons, Nat.succ_mul]
    have ha : a ≤ q := by
      have h0 := h 0 (by simp)
      rwa [getElem!_cons_zero] at h0
    have htail : ∀ j, j < l.length → l[j]! ≤ q := by
      intro j hj
      have h1 := h (j + 1) (by simp; omega)
      rwa [getElem!_cons_succ] at h1
    have hsum := ih htail
    omega

/-- If one entry of such a list is `0`, the sum drops by a whole
`q`: it is at most `(length - 1) * q`. -/
theorem sum_le_pred_mul_of_eq_zero {l : List Nat} {q : Nat} {i : Nat}
    (h : ∀ j, j < l.length → l[j]! ≤ q) (hi : i < l.length)
    (hz : l[i]! = 0) : l.sum ≤ (l.length - 1) * q := by
  induction l generalizing i with
  | nil => exact absurd hi (by simp)
  | cons a l ih =>
    cases i with
    | zero =>
      have ha : a = 0 := by
        have h0 := hz
        rwa [getElem!_cons_zero] at h0
      have htail : ∀ j, j < l.length → l[j]! ≤ q := by
        intro j hj
        have h1 := h (j + 1) (by simp; omega)
        rwa [getElem!_cons_succ] at h1
      have hsum := sum_le_of_getElem!_le htail
      rw [List.sum_cons, ha, Nat.zero_add, List.length_cons,
        Nat.add_sub_cancel]
      exact hsum
    | succ i =>
      have ha : a ≤ q := by
        have h0 := h 0 (by simp)
        rwa [getElem!_cons_zero] at h0
      have htail : ∀ j, j < l.length → l[j]! ≤ q := by
        intro j hj
        have h1 := h (j + 1) (by simp; omega)
        rwa [getElem!_cons_succ] at h1
      have hz' : l[i]! = 0 := by
        have h0 := hz
        rwa [getElem!_cons_succ] at h0
      have hi' : i < l.length := by
        have h0 := hi
        simp at h0
        omega
      have hsum := ih htail hi' hz'
      have hlen1 : 1 ≤ l.length := by omega
      have key : q + (l.length - 1) * q = l.length * q := by
        rw [Nat.add_comm q ((l.length - 1) * q), ← Nat.succ_mul,
          Nat.succ_eq_add_one, Nat.sub_add_cancel hlen1]
      rw [List.sum_cons, List.length_cons, Nat.add_sub_cancel]
      omega

/-- The draft's fourth theorem, carried as stated (an arbitrary
distribution, the draft's three hypotheses, plus the recorded
length hypothesis `hlen`): every child gets at least one candy
and at most `candies / children + 1`. The upper bound is the
hypothesis `h2` itself; the lower bound is the content: if some
child got `0`, the total would be at most
`(children - 1) * (candies / children) < candies`. -/
theorem candy_distribution_correctness (dist : CandyDistribution)
    (candies : Nat)
    (hge : dist.children ≤ candies)
    (h2 : ∀ i : Nat, dist.distribution[i]! ≤ candies / dist.children)
    (h3 : dist.distribution.sum = candies)
    (hlen : dist.distribution.length = dist.children) :
    ∀ i : Nat, i < dist.children → 0 < dist.distribution[i]! ∧
      dist.distribution[i]! ≤ candies / dist.children + 1 := by
  intro i hi
  refine ⟨?_, by have := h2 i; omega⟩
  by_cases hz : dist.distribution[i]! = 0
  · exfalso
    have h2' : ∀ j, j < dist.distribution.length →
        dist.distribution[j]! ≤ candies / dist.children :=
      fun j _ => h2 j
    have hi' : i < dist.distribution.length := by omega
    have hsum := sum_le_pred_mul_of_eq_zero h2' hi' hz
    rw [hlen] at hsum
    have hq : 1 ≤ candies / dist.children :=
      Nat.div_pos hge (by omega)
    have hdiv : candies / dist.children * dist.children ≤ candies :=
      Nat.div_mul_le_self candies dist.children
    have hprod : (dist.children - 1) * (candies / dist.children) =
        candies / dist.children * dist.children - candies / dist.children := by
      rw [Nat.mul_comm (dist.children - 1) _, Nat.mul_sub, Nat.mul_one]
    omega
  · omega

end AxiomCode
