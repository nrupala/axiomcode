import Spec
import Tactics
import Algorithms.Graph

/-!
# AxiomCode — Verified Floyd-Warshall

Promoted from `lean/drafts/floyd_warshall_correctness {v.lean` under
the L2 promotion procedure (`lean/PROMOTION.md`). Authored and proved
by Arjun (Item 6, own-hands track), against the graph platform
(`Algorithms.Graph`, `WGraph`).

Statement-honesty record. The draft was an incoherent shell: it
imported Mathlib + Aesop against the library's core discipline,
defined a fieldless `Graph (V : Type)`, a body-less `shortestPaths`,
and a statement in notation soup (`shortestPaths G[u, v]`,
`Nat.maxRec 0`) that cannot elaborate. Nothing is carried literally;
the classical claim is authored here in full.

The claim. Distances are `Option Int` (`none` = unreachable).
`minVia wg S u v` is the bounded-intermediate minimum, defined by the
Floyd-Warshall recursion itself; `fwRun` is the same recursion in
matrix-fold form, and `fwRun_eq_minVia` identifies them. The headline
`fwRun_correct`: under `NoNegCycle` — every closed walk has
nonnegative weight — the computed entry is `some w` exactly when `w`
is the minimum weight of a walk from `u` to `v` whose intermediate
vertices lie in `S`: attained by such a walk (`minVia_sound`, no
hypothesis needed) and bounding every such walk (`minVia_optimal`).
The hypothesis is load-bearing and named, not hidden: with a
negative closed walk, walk weights are unbounded below while the
recursion still prints a finite number, so no minimum exists.
-/

namespace AxiomCode

/-- Minimum in the `Option Int` distance algebra (`none` = ∞). -/
def omin (a b : Option Int) : Option Int :=
  match a, b with
  | some x, some y => some (min x y)
  | some x, none => some x
  | none, b => b

/-- Addition in the distance algebra (`none` absorbs). -/
def oadd (a b : Option Int) : Option Int :=
  match a, b with
  | some x, some y => some (x + y)
  | _, _ => none

theorem omin_eq_some {a b : Option Int} {w : Int} (h : omin a b = some w) :
    a = some w ∨ b = some w := by
  cases a with
  | none => exact Or.inr h
  | some x =>
    cases b with
    | none => exact Or.inl h
    | some y =>
      have hmin : min x y = w := by
        have := h; simp only [omin] at this; exact Option.some.inj this
      have : min x y = x ∨ min x y = y := by omega
      rcases this with hm | hm
      · exact Or.inl (by rw [← hmin, hm])
      · exact Or.inr (by rw [← hmin, hm])

theorem oadd_eq_some {a b : Option Int} {w : Int} (h : oadd a b = some w) :
    ∃ x y, a = some x ∧ b = some y ∧ x + y = w := by
  cases a with
  | none => simp only [oadd] at h; exact absurd h (by simp)
  | some x =>
    cases b with
    | none => simp only [oadd] at h; exact absurd h (by simp)
    | some y =>
      exact ⟨x, y, rfl, rfl, by
        have := h; simp only [oadd] at this; exact Option.some.inj this⟩

/-- The best direct-edge weight from `u` to `v` (minimum over parallel
edges), or `none` when there is no direct edge. -/
def edgeMin (wg : WGraph) (u v : Nat) : Option Int :=
  (wg.edges.filter (fun e => decide (e.1 = u ∧ e.2.1 = v))).foldr
    (fun e acc => omin (some e.2.2) acc) none

theorem edgeMin_eq_some {wg : WGraph} {u v : Nat} {w : Int}
    (h : edgeMin wg u v = some w) : (u, v, w) ∈ wg.edges := by
  unfold edgeMin at h
  have hgen : ∀ (l : List (Nat × Nat × Int)) (acc : Option Int),
      l.foldr (fun e acc => omin (some e.2.2) acc) acc = some w →
      acc = some w ∨ ∃ e ∈ l, e.2.2 = w := by
    intro l
    induction l with
    | nil => intro acc hacc; exact Or.inl hacc
    | cons e l ih =>
      intro acc hacc
      simp only [List.foldr_cons] at hacc
      rcases omin_eq_some hacc with h1 | h1
      · exact Or.inr ⟨e, List.mem_cons_self, by
          have : some e.2.2 = some w := h1; exact Option.some.inj this⟩
      · rcases ih acc h1 with h2 | h2
        · exact Or.inl h2
        · obtain ⟨e', he', hw'⟩ := h2
          exact Or.inr ⟨e', List.mem_cons_of_mem e he', hw'⟩
  rcases hgen _ none h with h1 | h1
  · simp at h1
  · obtain ⟨e, he, hw⟩ := h1
    have hef : e ∈ wg.edges.filter (fun e => e.1 = u && e.2.1 = v) :=
      he
    rw [List.mem_filter] at hef
    obtain ⟨heedges, hcond⟩ := hef
    obtain ⟨h1, h2⟩ := (Bool.and_eq_true _ _).mp hcond
    have h1e : e.1 = u := decide_eq_true_eq.mp h1
    have h2e : e.2.1 = v := decide_eq_true_eq.mp h2
    obtain ⟨a, b, c⟩ := e
    dsimp only at h1e h2e hw
    subst h1e; subst h2e; subst hw
    exact heedges

/-- The Floyd-Warshall initial matrix: 0 on the diagonal (improved by
a negative self-loop), the best direct edge elsewhere. -/
def fwInit (wg : WGraph) (u v : Nat) : Option Int :=
  if u = v then omin (some 0) (edgeMin wg u v) else edgeMin wg u v

/-- Bounded-intermediate minimum: `minVia wg S u v` is the minimum
weight of a walk from `u` to `v` whose intermediate vertices all lie
in `S` — defined by the Floyd-Warshall recursion itself (relax
through the head of `S` after solving for the tail). -/
def minVia (wg : WGraph) : List Nat → Nat → Nat → Option Int
  | [], u, v => fwInit wg u v
  | k :: S, u, v => omin (minVia wg S u v)
      (oadd (minVia wg S u k) (minVia wg S k v))

/-- The algorithm, in matrix-fold form: start from `fwInit`, relax
through each intermediate of `S` in turn. -/
def fwStep (d : Nat → Nat → Option Int) (k u v : Nat) : Option Int :=
  omin (d u v) (oadd (d u k) (d k v))

def fwRun (wg : WGraph) (S : List Nat) : Nat → Nat → Option Int :=
  S.foldr (fun k d u v => fwStep d k u v) (fwInit wg)

theorem fwRun_eq_minVia (wg : WGraph) (S : List Nat) (u v : Nat) :
    fwRun wg S u v = minVia wg S u v := by
  induction S generalizing u v with
  | nil => rfl
  | cons k S ih =>
    show fwStep (fwRun wg S) k u v = _
    unfold fwStep
    rw [ih u v, ih u k, ih k v]
    rfl

/-- A walk in a weighted graph, as data for the specification: the
vertex list `vs` records every vertex visited after the start, ending
at the target; the intermediates are `vs.dropLast`. -/
inductive Walk (wg : WGraph) : Nat → Nat → Int → List Nat → Prop
  | nil {u : Nat} : Walk wg u u 0 []
  | cons {u x v : Nat} {w₁ w₂ : Int} {vs : List Nat} :
      (u, x, w₁) ∈ wg.edges → Walk wg x v w₂ vs →
      Walk wg u v (w₁ + w₂) (x :: vs)

theorem Walk.append {wg : WGraph} {u k v : Nat} {w₁ w₂ : Int}
    {vs₁ vs₂ : List Nat} (h₁ : Walk wg u k w₁ vs₁) (h₂ : Walk wg k v w₂ vs₂) :
    Walk wg u v (w₁ + w₂) (vs₁ ++ vs₂) := by
  induction h₁ generalizing v with
  | nil =>
    simp only [List.nil_append, Int.zero_add]
    exact h₂
  | cons he htail ih =>
    have h := ih h₂
    rw [List.cons_append, Int.add_assoc]
    exact Walk.cons he h

theorem Walk.getLast_eq {wg : WGraph} {u v : Nat} {w : Int} {vs : List Nat}
    (h : Walk wg u v w vs) (hvs : vs ≠ []) : vs.getLast hvs = v := by
  induction h with
  | nil => exact absurd rfl hvs
  | cons he htail ih =>
    rename_i u x v w₁ w₂ vs
    cases vs with
    | nil =>
      cases htail with
      | nil => rfl
    | cons b l =>
      rw [List.getLast_cons_cons]
      exact ih (by simp)

theorem Walk.mem_dropLast_or_eq {wg : WGraph} {u v : Nat} {w : Int}
    {vs : List Nat} (h : Walk wg u v w vs) {z : Nat} (hz : z ∈ vs) :
    z ∈ vs.dropLast ∨ z = v := by
  cases vs with
  | nil => simp at hz
  | cons a vs =>
    have hcat := List.dropLast_concat_getLast (l := a :: vs) (by simp)
    rw [h.getLast_eq (by simp)] at hcat
    rw [← hcat] at hz
    rw [List.mem_append] at hz
    rcases hz with hz | hz
    · exact Or.inl hz
    · exact Or.inr (List.mem_singleton.mp hz)

theorem dropLast_append_ne {α : Type} {l₁ l₂ : List α} (h : l₂ ≠ []) :
    (l₁ ++ l₂).dropLast = l₁ ++ l₂.dropLast := by
  induction l₁ with
  | nil => rfl
  | cons a l₁ ih =>
    have hne : l₁ ++ l₂ ≠ [] := by
      cases l₁ with
      | nil => simp [h]
      | cons b l₁ => simp
    have hstep : (a :: (l₁ ++ l₂)).dropLast = a :: (l₁ ++ l₂).dropLast := by
      cases h₁ : l₁ ++ l₂ with
      | nil => exact absurd h₁ hne
      | cons b l => rfl
    rw [List.cons_append, hstep, ih, List.cons_append]

/-- Soundness: every finite `minVia` entry is realized by a walk
whose intermediate vertices all lie in `S`. -/
theorem minVia_sound (wg : WGraph) : ∀ (S : List Nat) (u v : Nat) (w : Int),
    minVia wg S u v = some w →
    ∃ vs, Walk wg u v w vs ∧ ∀ z ∈ vs.dropLast, z ∈ S := by
  intro S
  induction S with
  | nil =>
    intro u v w h
    simp only [minVia, fwInit] at h
    by_cases huv : u = v
    · subst huv
      rw [ite_eq_left rfl] at h
      rcases omin_eq_some h with h3 | h3
      · have hw : w = 0 := (Option.some.inj h3).symm
        exact ⟨[], by rw [hw]; exact Walk.nil, by simp⟩
      · have hedge := edgeMin_eq_some h3
        exact ⟨[u], by simpa using Walk.cons hedge Walk.nil, by simp⟩
    · rw [ite_eq_right huv] at h
      have hedge := edgeMin_eq_some h
      exact ⟨[v], by simpa using Walk.cons hedge Walk.nil, by simp⟩
  | cons k S ih =>
    intro u v w h
    have hEq : minVia wg (k :: S) u v =
        omin (minVia wg S u v) (oadd (minVia wg S u k) (minVia wg S k v)) :=
      rfl
    rw [hEq] at h
    rcases omin_eq_some h with h1 | h1
    · obtain ⟨vs, hwalk, hints⟩ := ih u v w h1
      exact ⟨vs, hwalk, fun z hz => List.mem_cons_of_mem k (hints z hz)⟩
    · obtain ⟨w₁, w₂, hk1, hk2, hsum⟩ := oadd_eq_some h1
      obtain ⟨vs₁, hwalk₁, hints₁⟩ := ih u k w₁ hk1
      obtain ⟨vs₂, hwalk₂, hints₂⟩ := ih k v w₂ hk2
      refine ⟨vs₁ ++ vs₂, by rw [← hsum]; exact Walk.append hwalk₁ hwalk₂, ?_⟩
      intro z hz
      by_cases hvs₂ : vs₂ = []
      · subst hvs₂
        rw [List.append_nil] at hz
        exact List.mem_cons_of_mem k (hints₁ z hz)
      · rw [dropLast_append_ne hvs₂] at hz
        rw [List.mem_append] at hz
        rcases hz with hz | hz
        · rcases hwalk₁.mem_dropLast_or_eq hz with hz' | hz'
          · exact List.mem_cons_of_mem k (hints₁ z hz')
          · exact hz' ▸ List.mem_cons_self
        · exact List.mem_cons_of_mem k (hints₂ z hz)

theorem omin_some_is_some (x : Int) (b : Option Int) :
    ∃ w, omin (some x) b = some w ∧ w ≤ x := by
  cases b with
  | none => exact ⟨x, rfl, by omega⟩
  | some y => exact ⟨min x y, rfl, by omega⟩

theorem omin_le_of_eq {a b : Option Int} {w x : Int}
    (h : omin a b = some w) (ha : a = some x) : w ≤ x := by
  subst ha
  cases b with
  | none =>
    simp only [omin] at h
    have : x = w := Option.some.inj h
    omega
  | some y =>
    have hmin : min x y = w := by
      have := h; simp only [omin] at this; exact Option.some.inj this
    omega

theorem omin_le_of_eq_right {a b : Option Int} {w y : Int}
    (h : omin a b = some w) (hb : b = some y) : w ≤ y := by
  subst hb
  cases a with
  | none =>
    simp only [omin] at h
    have : y = w := Option.some.inj h
    omega
  | some x =>
    have hmin : min x y = w := by
      have := h; simp only [omin] at this; exact Option.some.inj this
    omega

/-- Reverse edge-minimum characterization: a real edge's weight
bounds the edge minimum from above (and the minimum is attained). -/
theorem edgeMin_le_of_mem {wg : WGraph} {u v : Nat} {w : Int}
    (h : (u, v, w) ∈ wg.edges) :
    ∃ w', edgeMin wg u v = some w' ∧ w' ≤ w := by
  have hgen : ∀ (l : List (Nat × Nat × Int)) (e : Nat × Nat × Int),
      e ∈ l → ∃ w', l.foldr (fun e acc => omin (some e.2.2) acc) none =
        some w' ∧ w' ≤ e.2.2 := by
    intro l
    induction l with
    | nil => intro e he; simp at he
    | cons a l ih =>
      intro e he
      simp only [List.foldr_cons]
      rcases List.mem_cons.mp he with rfl | he'
      · obtain ⟨w', hw', hle⟩ := omin_some_is_some e.2.2
          (l.foldr (fun e acc => omin (some e.2.2) acc) none)
        exact ⟨w', hw', hle⟩
      · obtain ⟨w', hw', hle⟩ := ih e he'
        refine ⟨min a.2.2 w', ?_, by omega⟩
        rw [hw']; simp only [omin]
  have hmem : (u, v, w) ∈ wg.edges.filter
      (fun e => decide (e.1 = u ∧ e.2.1 = v)) := by
    rw [List.mem_filter]
    exact ⟨h, by simp⟩
  obtain ⟨w', hw', hle⟩ := hgen _ _ hmem
  exact ⟨w', hw', hle⟩

/-- Splitting a walk at the first occurrence of `k` among its
intermediates: the head walk ends at `k` and never passes through
`k` earlier; the tail walk's intermediates are original ones. -/
theorem Walk.split_first {wg : WGraph} {u v : Nat} {w : Int}
    {vs : List Nat} (h : Walk wg u v w vs) :
    ∀ k, k ∈ vs.dropLast →
    ∃ w₁ w₂ vs₁ vs₂, Walk wg u k w₁ vs₁ ∧ Walk wg k v w₂ vs₂ ∧
      w = w₁ + w₂ ∧
      (∀ z ∈ vs₁.dropLast, z ∈ vs.dropLast ∧ z ≠ k) ∧
      (∀ z ∈ vs₂.dropLast, z ∈ vs.dropLast) ∧
      vs₂.length < vs.length ∧ vs₁.length ≤ vs.length := by
  induction h with
  | nil => intro k hk; simp at hk
  | cons he htail ih =>
    rename_i u x v w₁ w₂ vsT
    intro k hk
    cases vsT with
    | nil => simp at hk
    | cons y vsT' =>
      have hdl : (x :: y :: vsT').dropLast = x :: (y :: vsT').dropLast := rfl
      rw [hdl] at hk
      by_cases hxk : x = k
      · refine ⟨w₁, w₂, [k], y :: vsT',
          by simpa using Walk.cons (hxk ▸ he) Walk.nil,
          hxk ▸ htail, rfl, ?_, ?_, by simp, by simp⟩
        · intro z hz; simp at hz
        · intro z hz
          rw [hdl]
          exact List.mem_cons_of_mem x hz
      · have hkT : k ∈ (y :: vsT').dropLast := by
          rcases List.mem_cons.mp hk with h | h
          · exact absurd h.symm hxk
          · exact h
        obtain ⟨w₁', w₂', vs₁', vs₂, hA', hC, hw', hb1, hb2, hlen2, hlen1⟩ :=
          ih k hkT
        have hlen : (x :: y :: vsT').length = (y :: vsT').length + 1 := rfl
        refine ⟨w₁ + w₁', w₂', x :: vs₁', vs₂, Walk.cons he hA', hC,
          by omega, ?_, ?_, by omega, by
            have : (x :: vs₁').length = vs₁'.length + 1 := rfl
            omega⟩
        · intro z hz
          cases vs₁' with
          | nil => simp at hz
          | cons a vs₁'' =>
            have hdl' : (x :: a :: vs₁'').dropLast =
                x :: (a :: vs₁'').dropLast := rfl
            rw [hdl'] at hz
            rw [hdl]
            rcases List.mem_cons.mp hz with rfl | hz'
            · exact ⟨List.mem_cons_self, hxk⟩
            · obtain ⟨hz1, hz2⟩ := hb1 z hz'
              exact ⟨List.mem_cons_of_mem x hz1, hz2⟩
        · intro z hz
          rw [hdl]
          exact List.mem_cons_of_mem x (hb2 z hz)

/-- The classical Floyd-Warshall hypothesis, named on the theorem:
no closed walk has negative total weight. Without it, walk weights
are unbounded below (loop the negative cycle) while the recursion
still prints a finite number — so no minimum claim is possible. -/
def NoNegCycle (wg : WGraph) : Prop :=
  ∀ (a : Nat) (w : Int) (vs : List Nat), Walk wg a a w vs → 0 ≤ w

theorem omin_is_some_of_right {a : Option Int} {y : Int} (hb : b = some y) :
    ∃ w, omin a b = some w ∧ w ≤ y := by
  subst hb
  cases a with
  | none => exact ⟨y, rfl, by omega⟩
  | some x => exact ⟨min x y, rfl, by omega⟩

theorem omin_is_some_of_left {b : Option Int} {x : Int} (ha : a = some x) :
    ∃ w, omin a b = some w ∧ w ≤ x := by
  subst ha
  cases b with
  | none => exact ⟨x, rfl, by omega⟩
  | some y => exact ⟨min x y, rfl, by omega⟩

/-- Auxiliary for optimality: from the source vertex `k`, any walk
whose intermediates lie in `k :: S` is bounded below by the
`S`-minimum — the closed head segment (if the walk returns to `k`)
is discarded via `NoNegCycle`. Proved by bounded induction on the
walk's vertex-list length, given optimality at `S` (`hS`). -/
theorem minVia_optimal_from_source {wg : WGraph} (hNC : NoNegCycle wg)
    {S : List Nat} {k v : Nat}
    (hS : ∀ (x y : Nat) (w : Int) (vs : List Nat), Walk wg x y w vs →
      (∀ z ∈ vs.dropLast, z ∈ S) → ∃ w', minVia wg S x y = some w' ∧ w' ≤ w) :
    ∀ (m : Nat) (w : Int) (vs : List Nat), vs.length ≤ m →
      Walk wg k v w vs → (∀ z ∈ vs.dropLast, z ∈ k :: S) →
      ∃ w', minVia wg S k v = some w' ∧ w' ≤ w := by
  intro m
  induction m with
  | zero =>
    intro w vs hlen hwalk hints
    cases vs with
    | nil => exact hS k v w [] hwalk (by simp)
    | cons a vs => simp [List.length_cons] at hlen
  | succ m ih =>
    intro w vs hlen hwalk hints
    by_cases hk : k ∈ vs.dropLast
    · obtain ⟨w₁, w₂, vs₁, vs₂, hM, hC, hw, hb1, hb2, hlen2, hlen1⟩ :=
        hwalk.split_first k hk
      obtain ⟨w', hw', hle⟩ := ih w₂ vs₂ (by omega) hC
        (fun z hz => hints z (hb2 z hz))
      have hMnn : 0 ≤ w₁ := hNC k w₁ vs₁ hM
      exact ⟨w', hw', by omega⟩
    · exact hS k v w vs hwalk (fun z hz => by
        have hzk := hints z hz
        rcases List.mem_cons.mp hzk with h | h
        · exact absurd (h ▸ hz) hk
        · exact h)

/-- A walk with no intermediates is the empty walk or a single
edge. -/
theorem Walk.classify_of_dropLast_eq_nil {wg : WGraph} {u v : Nat}
    {w : Int} {vs : List Nat} (h : Walk wg u v w vs)
    (hdl : vs.dropLast = []) :
    (u = v ∧ w = 0 ∧ vs = []) ∨
    (∃ w₁, (u, v, w₁) ∈ wg.edges ∧ w = w₁ ∧ vs = [v]) := by
  induction h with
  | nil => exact Or.inl ⟨rfl, rfl, rfl⟩
  | cons he htail ih =>
    rename_i u x v w₁ w₂ vsT
    cases vsT with
    | nil =>
      cases htail with
      | nil => exact Or.inr ⟨w₁, he, by omega, rfl⟩
    | cons y vsT' =>
      have hdl' : (x :: y :: vsT').dropLast = x :: (y :: vsT').dropLast :=
        rfl
      rw [hdl'] at hdl
      simp at hdl

/-- Optimality: under `NoNegCycle`, every walk's weight bounds the
`minVia` entry below, and the entry is attained (is `some`). With
`minVia_sound`, the entry is exactly the minimum walk weight over
walks with intermediates in `S`. -/
theorem minVia_optimal (wg : WGraph) (hNC : NoNegCycle wg) :
    ∀ (S : List Nat) (u v : Nat) (w : Int) (vs : List Nat),
    Walk wg u v w vs → (∀ z ∈ vs.dropLast, z ∈ S) →
    ∃ w', minVia wg S u v = some w' ∧ w' ≤ w := by
  intro S
  induction S with
  | nil =>
    intro u v w vs hwalk hints
    have hdl : vs.dropLast = [] := by
      cases hd : vs.dropLast with
      | nil => rfl
      | cons a l =>
        exact absurd (hints a (by rw [hd]; exact List.mem_cons_self))
          (by simp)
    rcases hwalk.classify_of_dropLast_eq_nil hdl with
      ⟨rfl, rfl, rfl⟩ | ⟨w₁, he, rfl, rfl⟩
    · have hEq : minVia wg [] u u = omin (some 0) (edgeMin wg u u) := by
        simp [minVia, fwInit]
      obtain ⟨w', hw', hle⟩ := omin_some_is_some 0 (edgeMin wg u u)
      exact ⟨w', by rw [hEq]; exact hw', hle⟩
    · obtain ⟨w', hw', hle⟩ := edgeMin_le_of_mem he
      by_cases huv : u = v
      · subst huv
        have hEq : minVia wg [] u u = omin (some 0) (edgeMin wg u u) := by
          simp [minVia, fwInit]
        obtain ⟨w'', hw'', hle''⟩ := omin_is_some_of_right hw'
        exact ⟨w'', by rw [hEq]; exact hw'', by omega⟩
      · have hEq : minVia wg [] u v = edgeMin wg u v := by
          simp [minVia, fwInit, huv]
        exact ⟨w', by rw [hEq]; exact hw', by omega⟩
  | cons k S ih =>
    intro u v w vs hwalk hints
    have hEq : minVia wg (k :: S) u v =
        omin (minVia wg S u v) (oadd (minVia wg S u k) (minVia wg S k v)) :=
      rfl
    by_cases hk : k ∈ vs.dropLast
    · obtain ⟨w₁, w₂, vs₁, vs₂, hA, hB, hw, hb1, hb2, hlen2, hlen1⟩ :=
        hwalk.split_first k hk
      obtain ⟨a', ha', hale⟩ := ih u k w₁ vs₁ hA (fun z hz => by
        obtain ⟨hz1, hz2⟩ := hb1 z hz
        have := hints z hz1
        rcases List.mem_cons.mp this with h | h
        · exact absurd h hz2
        · exact h)
      obtain ⟨b', hb', hble⟩ := minVia_optimal_from_source hNC ih
        vs₂.length w₂ vs₂ (by omega) hB
        (fun z hz => hints z (hb2 z hz))
      obtain ⟨w'', hw'', hle''⟩ := omin_is_some_of_right (a := minVia wg S u v)
        (b := oadd (minVia wg S u k) (minVia wg S k v))
        (by rw [ha', hb']; rfl)
      exact ⟨w'', by rw [hEq]; exact hw'', by omega⟩
    · obtain ⟨w', hw', hle⟩ := ih u v w vs hwalk (fun z hz => by
        have hzk := hints z hz
        rcases List.mem_cons.mp hzk with h | h
        · exact absurd (h ▸ hz) hk
        · exact h)
      obtain ⟨w'', hw'', hle''⟩ := omin_is_some_of_left (a := minVia wg S u v)
        (b := oadd (minVia wg S u k) (minVia wg S k v)) hw'
      exact ⟨w'', by rw [hEq]; exact hw'', by omega⟩

/-- The Floyd-Warshall correctness theorem, in full: under
`NoNegCycle`, the computed entry is `some w` exactly when `w` is the
minimum weight of a walk from `u` to `v` whose intermediate vertices
lie in `S` — attained by a walk, and bounding every such walk. -/
theorem minVia_correct (wg : WGraph) (hNC : NoNegCycle wg)
    (S : List Nat) (u v : Nat) :
    ∀ w, minVia wg S u v = some w ↔
      (∃ vs, Walk wg u v w vs ∧ ∀ z ∈ vs.dropLast, z ∈ S) ∧
      (∀ (w' : Int) (vs : List Nat), Walk wg u v w' vs →
        (∀ z ∈ vs.dropLast, z ∈ S) → w ≤ w') := by
  intro w
  constructor
  · intro h
    obtain ⟨vs, hwalk, hints⟩ := minVia_sound wg S u v w h
    refine ⟨⟨vs, hwalk, hints⟩, ?_⟩
    intro w' vs' hwalk' hints'
    obtain ⟨w'', hw'', hle⟩ := minVia_optimal wg hNC S u v w' vs' hwalk' hints'
    rw [h] at hw''
    have hww : w = w'' := Option.some.inj hw''
    omega
  · intro h
    obtain ⟨⟨vs, hwalk, hints⟩, hmin⟩ := h
    obtain ⟨w', hw', hle⟩ := minVia_optimal wg hNC S u v w vs hwalk hints
    obtain ⟨vs₂, hwalk₂, hints₂⟩ := minVia_sound wg S u v w' hw'
    have hle2 : w ≤ w' := hmin w' vs₂ hwalk₂ hints₂
    have hww : w = w' := by omega
    rw [hww]; exact hw'

/-- The same statement for the algorithm in matrix-fold form. -/
theorem fwRun_correct (wg : WGraph) (hNC : NoNegCycle wg)
    (S : List Nat) (u v : Nat) :
    ∀ w, fwRun wg S u v = some w ↔
      (∃ vs, Walk wg u v w vs ∧ ∀ z ∈ vs.dropLast, z ∈ S) ∧
      (∀ (w' : Int) (vs : List Nat), Walk wg u v w' vs →
        (∀ z ∈ vs.dropLast, z ∈ S) → w ≤ w') := by
  intro w
  rw [fwRun_eq_minVia]
  exact minVia_correct wg hNC S u v w

end AxiomCode
