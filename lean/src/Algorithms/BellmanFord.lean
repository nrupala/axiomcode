import Spec
import Tactics
import Algorithms.Graph

/-!
# AxiomCode — Verified Bellman-Ford

Bellman-Ford single-source shortest paths over the graph platform's
weighted layer (`WGraph`, `Int` weights, negative weights allowed),
promoted from `lean/drafts/bellmanford_correctness.lean` under the
L2 promotion procedure (`lean/PROMOTION.md`).

Statement-honesty record. The draft is a shell and does not
elaborate at all:

- Its `Graph` is a fieldless structure, yet the statement and the
  signatures reference `g.vertices` (used as a *type*:
  `source : g.vertices`, `List (g.vertices × Int)`) and
  `Graph.vertices` / `Graph.edges` as types. None of these exist.
  The platform's `WGraph` (vertex list, weighted edge triples) is
  what the field references can only mean.
- `initialDistances`, `relaxEdge` and `bellmanFord` are body-less;
  `shortestPaths` is never defined anywhere. Both sides of the
  draft's equation are authored here.
- The hypothesis `n ≥ g.vertices.size` uses `.size` on a list; the
  platform reading is `wg.vertices.length ≤ n` (at least one
  relaxation round per vertex).

The draft's statement is also **false as stated**: it carries no
negative-cycle hypothesis. Counterexample: vertices `[0, 1]`,
edges `[(0, 1, 0), (1, 1, -1)]`, source `0`, `n = 2` (which meets
`n ≥ vertices.length`). The one-edge walk `0 → 1` has weight `0`,
and every reasonable reading of `shortestPaths` disagrees with
the algorithm here: the simple-path reading assigns vertex `1`
the value `0`; the bounded-walk reading used in this module
(walks of at most `vertices.length` edges) assigns `-1` (the
walk `0 → 1 → 1`); the unbounded-walk reading assigns no value
at all — walks `0 → 1 → 1 → … → 1` have weights
`0, -1, -2, …`, unbounded below, so no shortest walk exists.
But relaxation keeps improving along the self-loop: after
2 rounds the computed distance of `1` is `-2`, which matches
none of the readings. So the equation fails for every
definition of the right-hand side. The
repaired statement keeps the draft's shape — same equation, same
round hypothesis — and adds the classical hypothesis the draft
omitted: no negative-weight closed walk reachable from the source
(`WGraph.NoNegCycleFrom`). The well-formedness hypotheses
(duplicate-free vertex list, edge endpoints among the vertices,
source among the vertices) are the platform's standard ones,
carried as hypotheses per the house pattern.

Design decisions (recorded 2026-11-16, Item 6 stage 2A):

- **Distance state.** The draft's state type is a list of
  `(vertex, Int)` pairs, which cannot represent "not yet reached"
  (there is no infinity in `Int`). The algorithm's working state
  here is a function `Nat → Option Int` (`none` = unreached, the
  infinity encoding), which makes update/lookup lemmas
  definitional; the public result `bellmanFord` returns exactly
  the draft's type, `List (Nat × Int)` — the reached vertices with
  their distances, in vertex-list order. `initialDistances` is
  correspondingly a function of the source alone (the state does
  not depend on the graph).
- **`shortestPaths`.** Authored as the bounded-walk minimum: for
  each vertex, the minimum weight over all walks from the source
  with at most `vertices.length` edges (enumerated by
  `chainsFrom`), or unreached if there is no such walk. Under the
  no-negative-cycle hypothesis this is the true shortest-path
  weight: some shortest walk is simple, hence has at most
  `vertices.length - 1` edges (the shortening lemma below), and
  the algorithm's `n ≥ vertices.length` rounds cover every walk
  of at most `vertices.length` edges.
- **Walks.** A walk is a list of edge triples satisfying the
  inductive chaining predicate `WGraph.Chain`; its weight is
  `chainWeight`. All shortest-path content is stated over chains,
  not over the platform's unweighted `Reach` (which forgets
  weights).
-/

namespace AxiomCode

/-- A walk in a weighted graph, as a list of edge triples that
chain together: `Chain wg s es v` says the edges `es`, read in
order, lead from `s` to `v`, and every edge is an edge of `wg`.
`nil` is the empty walk at a vertex; `cons` prepends one edge at
the start vertex. -/
inductive WGraph.Chain (wg : WGraph) : Nat → List (Nat × Nat × Int) → Nat → Prop
  | nil (s : Nat) : Chain wg s [] s
  | cons {s b v : Nat} {w : Int} {es : List (Nat × Nat × Int)} :
      (s, b, w) ∈ wg.edges → Chain wg b es v → Chain wg s ((s, b, w) :: es) v

/-- The total weight of an edge list: the sum of its third
components. -/
def chainWeight : List (Nat × Nat × Int) → Int
  | [] => 0
  | e :: es => e.2.2 + chainWeight es

theorem chainWeight_append (l₁ l₂ : List (Nat × Nat × Int)) :
    chainWeight (l₁ ++ l₂) = chainWeight l₁ + chainWeight l₂ := by
  induction l₁ with
  | nil => simp [chainWeight]
  | cons e es ih =>
    show e.2.2 + chainWeight (es ++ l₂) = (e.2.2 + chainWeight es) + chainWeight l₂
    rw [ih, Int.add_assoc]

/-- The vertices a walk from `s` along `es` passes through: the
start vertex followed by each edge's target. -/
def chainEndpoints (s : Nat) (es : List (Nat × Nat × Int)) : List Nat :=
  s :: es.map (fun e => e.2.1)

/-- The end vertex of a walk from `s` along `es`: the last edge's
target, or `s` for the empty walk. -/
def chainEnd (s : Nat) : List (Nat × Nat × Int) → Nat
  | [] => s
  | e :: es => chainEnd e.2.1 es

/-- Walks concatenate: a walk from `s` to `m` followed by a walk
from `m` to `v` is a walk from `s` to `v` over the appended edge
lists. -/
theorem WGraph.Chain.append {wg : WGraph} {s m : Nat}
    {l₁ : List (Nat × Nat × Int)} (h₁ : Chain wg s l₁ m) :
    ∀ {v : Nat} {l₂ : List (Nat × Nat × Int)},
      Chain wg m l₂ v → Chain wg s (l₁ ++ l₂) v := by
  induction h₁ with
  | nil => intro v l₂ h₂; exact h₂
  | cons he _ ih => intro v l₂ h₂; exact Chain.cons he (ih h₂)

/-- A walk over an appended edge list splits at the join: some
intermediate vertex ends the first part and starts the second. -/
theorem WGraph.Chain.append_split {wg : WGraph} {s v : Nat}
    {l₁ l₂ : List (Nat × Nat × Int)} (h : Chain wg s (l₁ ++ l₂) v) :
    ∃ m, Chain wg s l₁ m ∧ Chain wg m l₂ v := by
  induction l₁ generalizing s with
  | nil => exact ⟨s, Chain.nil s, h⟩
  | cons e l₁ ih =>
    cases h with
    | cons he htail =>
      obtain ⟨m, h1, h2⟩ := ih htail
      exact ⟨m, Chain.cons he h1, h2⟩

/-- Inversion for a walk over a cons list: the head edge starts
at the walk's start, is an edge of the graph, and the tail walks
on from the head edge's target. -/
theorem WGraph.Chain.cons_inv {wg : WGraph} {s v : Nat}
    {e : Nat × Nat × Int} {es : List (Nat × Nat × Int)}
    (h : Chain wg s (e :: es) v) :
    e.1 = s ∧ e ∈ wg.edges ∧ Chain wg e.2.1 es v := by
  cases h with
  | cons he htail => exact ⟨rfl, he, htail⟩

/-- A nonempty walk splits off its last edge: some prefix walk
ends at the last edge's source. -/
theorem WGraph.Chain.split_last {wg : WGraph} {s v : Nat}
    {es : List (Nat × Nat × Int)} (h : Chain wg s es v) (hne : es ≠ []) :
    ∃ (es' : List (Nat × Nat × Int)) (u : Nat) (w : Int),
      es = es' ++ [(u, v, w)] ∧ Chain wg s es' u ∧ (u, v, w) ∈ wg.edges := by
  induction es generalizing s with
  | nil => exact absurd rfl hne
  | cons e es ih =>
    obtain ⟨a, b, w⟩ := e
    obtain ⟨h1, he, htail⟩ := h.cons_inv
    have h1' : a = s := h1
    subst s
    cases es with
    | nil =>
      cases htail
      exact ⟨[], a, w, rfl, Chain.nil a, he⟩
    | cons e' es' =>
      obtain ⟨es'', u, w', hsplit, hchain, hedge⟩ :=
        ih htail (List.cons_ne_nil e' es')
      exact ⟨(a, b, w) :: es'', u, w', by rw [hsplit, List.cons_append],
        Chain.cons he hchain, hedge⟩

/-- Every edge of a walk is an edge of the graph. -/
theorem WGraph.Chain.edges_mem {wg : WGraph} {s v : Nat}
    {es : List (Nat × Nat × Int)} (h : Chain wg s es v) :
    ∀ e ∈ es, e ∈ wg.edges := by
  induction h with
  | nil => intro e he; simp at he
  | cons he _ ih =>
    intro e hem
    rw [List.mem_cons] at hem
    rcases hem with rfl | hm
    · exact he
    · exact ih e hm

/-- A walk ends where `chainEnd` says it does. -/
theorem WGraph.Chain.end_eq {wg : WGraph} {s v : Nat}
    {es : List (Nat × Nat × Int)} (h : Chain wg s es v) :
    chainEnd s es = v := by
  induction h with
  | nil => rfl
  | cons _ _ ih => exact ih

/-- Every vertex a walk passes through is a vertex of the graph,
provided the start vertex is and every edge's endpoints are. -/
theorem WGraph.Chain.endpoints_mem {wg : WGraph} {s v : Nat}
    {es : List (Nat × Nat × Int)} (h : Chain wg s es v)
    (hend : ∀ e ∈ wg.edges, e.1 ∈ wg.vertices ∧ e.2.1 ∈ wg.vertices)
    (hs : s ∈ wg.vertices) :
    ∀ x ∈ chainEndpoints s es, x ∈ wg.vertices := by
  intro x hx
  rw [chainEndpoints, List.mem_cons, List.mem_map] at hx
  rcases hx with rfl | ⟨e, he, rfl⟩
  · exact hs
  · exact (hend e (h.edges_mem e he)).2

/-- Split a list at a membership: it is a prefix, the element, and
a suffix. (Core-only replacement for the Mathlib lemma of this
shape.) -/
theorem mem_split' {α : Type} {x : α} {l : List α} (h : x ∈ l) :
    ∃ s t, l = s ++ x :: t := by
  induction l with
  | nil => simp at h
  | cons a l ih =>
    rw [List.mem_cons] at h
    rcases h with rfl | h
    · exact ⟨[], l, rfl⟩
    · obtain ⟨s, t, ht⟩ := ih h
      exact ⟨a :: s, t, by rw [ht, List.cons_append]⟩

/-- A duplicate-free list drawn from a duplicate-free list is no
longer than it: the pigeonhole bound, by erasure induction. -/
theorem nodup_length_le : ∀ (l vs : List Nat), l.Nodup → vs.Nodup →
    (∀ x ∈ l, x ∈ vs) → l.length ≤ vs.length := by
  intro l
  induction l with
  | nil => intro vs _ _ _; simp
  | cons a l ih =>
    intro vs hnl hvs hmem
    rw [List.nodup_cons] at hnl
    obtain ⟨hna, hnl⟩ := hnl
    have ha : a ∈ vs := hmem a List.mem_cons_self
    have htail : ∀ x ∈ l, x ∈ vs.erase a := by
      intro x hx
      have hne : x ≠ a := fun hh => hna (hh ▸ hx)
      exact (List.mem_erase_of_ne hne).mpr (hmem x (List.mem_cons_of_mem a hx))
    have ih' := ih (vs.erase a) hnl (hvs.erase a) htail
    rw [List.length_erase_of_mem ha] at ih'
    have hpos : 1 ≤ vs.length := by
      cases vs with
      | nil => simp at ha
      | cons b bs => simp
    simp only [List.length_cons]
    omega

/-- A list that is not duplicate-free has a repeated element with
a (possibly empty) segment on each side and between the two
occurrences. -/
theorem not_nodup_split : ∀ {l : List Nat}, ¬ l.Nodup →
    ∃ (l₁ l₂ l₃ : List Nat) (x : Nat),
      l = l₁ ++ x :: l₂ ++ x :: l₃ := by
  intro l
  induction l with
  | nil => intro h; exact absurd List.nodup_nil h
  | cons a l ih =>
    intro h
    by_cases ha : a ∈ l
    · obtain ⟨s, t, ht⟩ := mem_split' ha
      exact ⟨[], s, t, a, by rw [ht]; simp only [List.nil_append,
        List.cons_append]⟩
    · have hnl : ¬ l.Nodup := fun hn => h (List.nodup_cons.mpr ⟨ha, hn⟩)
      obtain ⟨l₁, l₂, l₃, x, hsplit⟩ := ih hnl
      exact ⟨a :: l₁, l₂, l₃, x, by rw [hsplit]; simp only [List.cons_append]⟩

/-- Split a walk where its endpoint list first reaches `x`: if
`chainEndpoints s es = l₁ ++ x :: rest`, the walk splits into a
walk from `s` to `x` and a walk from `x` onward, and the second
part's endpoint list is `x :: rest`. -/
theorem WGraph.Chain.split_endpoints {wg : WGraph} {s v : Nat}
    {es : List (Nat × Nat × Int)} (h : Chain wg s es v) :
    ∀ (l₁ : List Nat) (x : Nat) (rest : List Nat),
      chainEndpoints s es = l₁ ++ x :: rest →
      ∃ es₁ es₂, es = es₁ ++ es₂ ∧ Chain wg s es₁ x ∧ Chain wg x es₂ v ∧
        chainEndpoints x es₂ = x :: rest := by
  induction es generalizing s with
  | nil =>
    intro l₁ x rest he
    have hvs : v = s := by cases h; rfl
    have he' : [s] = l₁ ++ x :: rest := he
    cases l₁ with
    | nil =>
      injection he' with h1 h2
      exact ⟨[], [], rfl, by rw [← h1]; exact Chain.nil s,
        by rw [← h1, hvs]; exact Chain.nil s,
        by simp [chainEndpoints, ← h2]⟩
    | cons c cs =>
      exfalso
      have hlen := congrArg List.length he'
      simp only [List.length_cons, List.length_nil, List.length_append]
        at hlen
      omega
  | cons e es ih =>
    obtain ⟨a, b, w⟩ := e
    obtain ⟨h1, he, htail⟩ := h.cons_inv
    have h1' : a = s := h1
    subst s
    intro l₁ x rest heq
    have heq' : a :: chainEndpoints b es = l₁ ++ x :: rest := heq
    cases l₁ with
    | nil =>
      injection heq' with h1 h2
      subst h1
      exact ⟨[], (a, b, w) :: es, rfl, Chain.nil a, Chain.cons he htail,
        by show a :: chainEndpoints b es = a :: rest; rw [h2]⟩
    | cons c cs =>
      injection heq' with h1 h2
      obtain ⟨es₁, es₂, hsplit, h1', h2', h3'⟩ := ih htail cs x rest h2
      exact ⟨(a, b, w) :: es₁, es₂, by rw [hsplit, List.cons_append],
        Chain.cons he h1', h2', h3'⟩

/-- No negative closed walk is reachable from `source`: every
closed walk at a vertex that `source` can reach, if it uses at
least one edge, has nonnegative weight. This is the hypothesis
the draft's statement omitted (see the module doc for the
counterexample showing it cannot be dropped). -/
def WGraph.NoNegCycleFrom (wg : WGraph) (source : Nat) : Prop :=
  ∀ (x : Nat) (es : List (Nat × Nat × Int)),
    (∃ pre, WGraph.Chain wg source pre x) → WGraph.Chain wg x es x →
    es ≠ [] → 0 ≤ chainWeight es

/-- The shortening lemma: under the no-negative-cycle hypothesis,
every walk from `s` can be shortened to a walk with at most
`vertices.length - 1` edges (a simple walk) of no greater weight,
by repeatedly removing the closed segment between two occurrences
of one vertex. Proved by induction on a bound for the walk's
length; the repeated vertex comes from the pigeonhole bound on
the endpoint list. -/
theorem WGraph.Chain.shorten {wg : WGraph} {s : Nat}
    (hnodup : wg.vertices.Nodup)
    (hend : ∀ e ∈ wg.edges, e.1 ∈ wg.vertices ∧ e.2.1 ∈ wg.vertices)
    (hs : s ∈ wg.vertices)
    (hnc : WGraph.NoNegCycleFrom wg s) :
    ∀ (k : Nat) (es : List (Nat × Nat × Int)) (v : Nat),
      es.length ≤ k → Chain wg s es v →
      ∃ es', Chain wg s es' v ∧ es'.length + 1 ≤ wg.vertices.length ∧
        chainWeight es' ≤ chainWeight es := by
  intro k
  induction k with
  | zero =>
    intro es v hlen h
    cases es with
    | nil =>
      refine ⟨[], h, ?_, by omega⟩
      cases hv : wg.vertices with
      | nil => rw [hv] at hs; simp at hs
      | cons a as => simp only [List.length_cons, List.length_nil]; omega
    | cons e es => simp at hlen
  | succ k ih =>
    intro es v hlen h
    by_cases hsmall : es.length + 1 ≤ wg.vertices.length
    · exact ⟨es, h, hsmall, by omega⟩
    · have hmem : ∀ x ∈ chainEndpoints s es, x ∈ wg.vertices :=
        h.endpoints_mem hend hs
      have hlenep : (chainEndpoints s es).length = es.length + 1 := by
        simp [chainEndpoints]
      have hnd : ¬ (chainEndpoints s es).Nodup := by
        intro hnd
        have hle := nodup_length_le _ _ hnd hnodup hmem
        rw [hlenep] at hle
        omega
      obtain ⟨l₁, l₂, l₃, x, hsplit⟩ := not_nodup_split hnd
      have hsplit' : chainEndpoints s es = l₁ ++ x :: (l₂ ++ x :: l₃) := by
        rw [List.append_assoc] at hsplit
        exact hsplit
      obtain ⟨es₁, es₂, heseq, hch1, hch2, hep2⟩ :=
        h.split_endpoints l₁ x (l₂ ++ x :: l₃) hsplit'
      obtain ⟨cyc, es₃, heseq2, hchc, hch3, hep3⟩ :=
        hch2.split_endpoints (x :: l₂) x l₃ hep2
      obtain ⟨e0, cyc', rfl⟩ : ∃ e t, cyc = e :: t := by
        cases cyc with
        | nil =>
          exfalso
          rw [List.nil_append] at heseq2
          rw [← heseq2] at hep3
          rw [hep2] at hep3
          have hlen2 := congrArg List.length hep3
          simp only [List.length_cons, List.length_append] at hlen2
          omega
        | cons a t => exact ⟨a, t, rfl⟩
      have hw : 0 ≤ chainWeight (e0 :: cyc') :=
        hnc x (e0 :: cyc') ⟨es₁, hch1⟩ hchc (List.cons_ne_nil e0 cyc')
      have hch : Chain wg s (es₁ ++ es₃) v := hch1.append hch3
      have hlen' : (es₁ ++ es₃).length ≤ k := by
        have h1 : es.length =
            es₁.length + (e0 :: cyc').length + es₃.length := by
          have t1 : es.length = (es₁ ++ ((e0 :: cyc') ++ es₃)).length := by
            rw [heseq, heseq2]
          rw [t1, List.length_append, List.length_append]
          omega
        have h2 : (es₁ ++ es₃).length = es₁.length + es₃.length := by
          rw [List.length_append]
        have h3 : (e0 :: cyc').length = cyc'.length + 1 := List.length_cons
        omega
      obtain ⟨es', hch', hlen'', hw'⟩ := ih (es₁ ++ es₃) v hlen' hch
      refine ⟨es', hch', hlen'', ?_⟩
      have hweq : chainWeight es =
          chainWeight es₁ + chainWeight (e0 :: cyc') + chainWeight es₃ := by
        rw [heseq, heseq2]; simp only [chainWeight_append]; omega
      have hweq' : chainWeight (es₁ ++ es₃) =
          chainWeight es₁ + chainWeight es₃ := chainWeight_append _ _
      omega

/-! ## The algorithm -/

/-- Point update of a distance function: `upd d v x` sets the
distance at `v` to `x` if `v` was unreached, and lowers it to
`min (d v) x` otherwise. Every other vertex is untouched. -/
def upd (d : Nat → Option Int) (v : Nat) (x : Int) (u : Nat) :
    Option Int :=
  if u = v then
    match d v with
    | none => some x
    | some dv => some (min dv x)
  else d u

theorem upd_other {d : Nat → Option Int} {v u : Nat} {x : Int}
    (h : u ≠ v) : upd d v x u = d u := by
  simp [upd, h]

/-- At the updated vertex, `upd` always produces a value: it is at
most the proposed value, and at most any previously held value. -/
theorem upd_self {d : Nat → Option Int} {v : Nat} {x : Int} :
    ∃ w', upd d v x v = some w' ∧ w' ≤ x ∧
      ∀ dv, d v = some dv → w' ≤ dv := by
  cases h : d v with
  | none =>
    refine ⟨x, by simp [upd, h], by omega,
      fun dv hdv => by cases hdv⟩
  | some dv =>
    refine ⟨min dv x, by simp [upd, h], by omega, fun dv' hdv' => by
      have h2 := Option.some.inj hdv'; omega⟩

/-- One relaxation step over a single edge: if the edge's source
is unreached, nothing changes; otherwise the target's distance is
updated with `source distance + weight`. -/
def step (d : Nat → Option Int) (e : Nat × Nat × Int) :
    Nat → Option Int :=
  match d e.1 with
  | none => d
  | some du => upd d e.2.1 (du + e.2.2)

/-- A step never raises a held distance. -/
theorem step_le_of_some {d : Nat → Option Int} {e : Nat × Nat × Int}
    {v : Nat} {w dv : Int} (hv : d v = some dv)
    (h : step d e v = some w) : w ≤ dv := by
  cases hdu : d e.1 with
  | none =>
    have h2 : d v = some w := by simpa [step, hdu] using h
    rw [hv] at h2
    have h3 : dv = w := Option.some.inj h2
    omega
  | some du =>
    have h2 : upd d e.2.1 (du + e.2.2) v = some w := by
      simpa [step, hdu] using h
    by_cases hvv : v = e.2.1
    · subst hvv
      obtain ⟨w', hw', -, hw'le⟩ := upd_self (d := d) (v := e.2.1)
        (x := du + e.2.2)
      rw [hw'] at h2
      have h3 : w' = w := Option.some.inj h2
      exact h3 ▸ hw'le dv hv
    · rw [upd_other hvv] at h2
      rw [hv] at h2
      have h3 : dv = w := Option.some.inj h2
      omega

/-- A step never loses a held distance. -/
theorem step_some {d : Nat → Option Int} {e : Nat × Nat × Int}
    {v : Nat} {w : Int} (hv : d v = some w) :
    ∃ w', step d e v = some w' := by
  cases hdu : d e.1 with
  | none => exact ⟨w, by simp [step, hdu, hv]⟩
  | some du =>
    by_cases hvv : v = e.2.1
    · subst hvv
      obtain ⟨w', hw', -, -⟩ := upd_self (d := d) (v := e.2.1)
        (x := du + e.2.2)
      exact ⟨w', by simp [step, hdu, hw']⟩
    · exact ⟨w, by simp [step, hdu, upd_other hvv, hv]⟩

/-- After the step over `(u, v, wₑ)`, the target `v` holds a value
at most `d u + wₑ`, provided `u` was reached. -/
theorem step_some_edge {d : Nat → Option Int} {u v : Nat}
    {wₑ du : Int} (hu : d u = some du) :
    ∃ w', step d (u, v, wₑ) v = some w' ∧ w' ≤ du + wₑ := by
  obtain ⟨w', hw', hw'le, -⟩ := upd_self (d := d) (v := v)
    (x := du + wₑ)
  exact ⟨w', by simp [step, hu, hw'], hw'le⟩

/-- One full round: relax every edge once, in list order, in
place (a `foldl` over the edge list). -/
def relaxEdges (edges : List (Nat × Nat × Int))
    (d : Nat → Option Int) : Nat → Option Int :=
  edges.foldl step d

/-- A round never raises a held distance and never loses one. -/
theorem relaxEdges_le_some (es : List (Nat × Nat × Int)) :
    ∀ (d : Nat → Option Int) (v : Nat) (w : Int), d v = some w →
      ∃ w', relaxEdges es d v = some w' ∧ w' ≤ w := by
  induction es with
  | nil => intro d v w hv; exact ⟨w, hv, by omega⟩
  | cons e es ih =>
    intro d v w hv
    obtain ⟨w₁, hw₁⟩ := step_some hv
    have h1le := step_le_of_some hv hw₁
    obtain ⟨w₂, hw₂, h2le⟩ := ih (step d e) v w₁ hw₁
    exact ⟨w₂, hw₂, by omega⟩

/-- The initial distance function: `0` at the source, unreached
elsewhere. -/
def initialDistances (source : Nat) : Nat → Option Int :=
  fun v => if v = source then some 0 else none

theorem initialDistances_self (source : Nat) :
    initialDistances source source = some 0 := by
  simp [initialDistances]

theorem initialDistances_eq {source v : Nat} {w : Int}
    (h : initialDistances source v = some w) :
    v = source ∧ w = 0 := by
  by_cases hv : v = source
  · subst hv
    exact ⟨rfl, (Option.some.inj (initialDistances_self v ▸ h)).symm⟩
  · exfalso
    simp [initialDistances, hv] at h

/-- Distances after `k` full relaxation rounds from `source`. -/
def bellmanFordRounds (wg : WGraph) (source : Nat) :
    Nat → (Nat → Option Int)
  | 0 => initialDistances source
  | k + 1 => relaxEdges wg.edges (bellmanFordRounds wg source k)

/-- The Bellman-Ford entry point, in the draft's shape: after `n`
rounds, the reached vertices with their computed distances, in
vertex-list order. -/
def bellmanFord (wg : WGraph) (source n : Nat) : List (Nat × Int) :=
  wg.vertices.filterMap
    (fun v => (bellmanFordRounds wg source n v).map (fun w => (v, w)))

theorem relaxEdges_cons (e : Nat × Nat × Int)
    (es : List (Nat × Nat × Int)) (d : Nat → Option Int) :
    relaxEdges (e :: es) d = relaxEdges es (step d e) := by
  unfold relaxEdges
  rw [List.foldl_cons]

/-! ## Realisation: every computed distance is a walk weight -/

/-- A single step preserves realisation: any value it produces
is the weight of a walk (one edge longer at the relaxed vertex). -/
theorem step_realised_preserve {wg : WGraph} {source : Nat}
    (d : Nat → Option Int) (e : Nat × Nat × Int)
    (he : e ∈ wg.edges)
    (hreal : ∀ v w, d v = some w → ∃ c, WGraph.Chain wg source c v ∧
      chainWeight c = w) :
    ∀ v w, step d e v = some w → ∃ c, WGraph.Chain wg source c v ∧
      chainWeight c = w := by
  intro v w h
  cases hdu : d e.1 with
  | none =>
    have h2 : d v = some w := by simpa [step, hdu] using h
    exact hreal v w h2
  | some du =>
    have h2 : upd d e.2.1 (du + e.2.2) v = some w := by
      simpa [step, hdu] using h
    by_cases hvv : v = e.2.1
    · subst hvv
      obtain ⟨c₁, hc₁, hw₁⟩ := hreal e.1 du hdu
      have hsingle : WGraph.Chain wg e.1 [e] e.2.1 :=
        WGraph.Chain.cons he (WGraph.Chain.nil _)
      have h4 : chainWeight (c₁ ++ [e]) = du + e.2.2 := by
        rw [chainWeight_append]
        have h5 : chainWeight [e] = e.2.2 := by simp [chainWeight]
        omega
      by_cases hdv : d e.2.1 = none
      · have h3 : upd d e.2.1 (du + e.2.2) e.2.1 =
            some (du + e.2.2) := by
          simp [upd, hdv]
        rw [h3] at h2
        have hw : w = du + e.2.2 := (Option.some.inj h2).symm
        exact ⟨c₁ ++ [e], hc₁.append hsingle, by omega⟩
      · obtain ⟨dv, hdv2⟩ : ∃ dv, d e.2.1 = some dv := by
          cases hd2 : d e.2.1 with
          | none => exact absurd hd2 hdv
          | some dv => exact ⟨dv, rfl⟩
        have h3 : upd d e.2.1 (du + e.2.2) e.2.1 =
            some (min dv (du + e.2.2)) := by
          simp [upd, hdv2]
        rw [h3] at h2
        have hw : w = min dv (du + e.2.2) := (Option.some.inj h2).symm
        have hmin : min dv (du + e.2.2) = dv ∨
            min dv (du + e.2.2) = du + e.2.2 := by omega
        rcases hmin with hm | hm
        · obtain ⟨c₂, hc₂, hw₂⟩ := hreal e.2.1 dv hdv2
          exact ⟨c₂, hc₂, by omega⟩
        · exact ⟨c₁ ++ [e], hc₁.append hsingle, by omega⟩
    · rw [upd_other hvv] at h2
      exact hreal v w h2

/-- A full round preserves realisation. -/
theorem relaxEdges_realised {wg : WGraph} {source : Nat}
    (es : List (Nat × Nat × Int)) :
    ∀ (d : Nat → Option Int), (∀ e ∈ es, e ∈ wg.edges) →
      (∀ v w, d v = some w → ∃ c, WGraph.Chain wg source c v ∧
        chainWeight c = w) →
      ∀ v w, relaxEdges es d v = some w →
        ∃ c, WGraph.Chain wg source c v ∧ chainWeight c = w := by
  induction es with
  | nil => intro d _hes hreal v w h; exact hreal v w h
  | cons e es ih =>
    intro d hes hreal v w h
    have h' : relaxEdges es (step d e) v = some w := h
    exact ih (step d e)
      (fun e' he' => hes e' (List.mem_cons_of_mem e he'))
      (step_realised_preserve d e (hes e (List.mem_cons_self)) hreal)
      v w h'

/-- Realisation, by induction on rounds: every distance the
algorithm computes is the weight of an actual walk from the
source. No hypothesis is needed for this direction. -/
theorem rounds_realised {wg : WGraph} {source : Nat} :
    ∀ (k : Nat) (v : Nat) (w : Int),
      bellmanFordRounds wg source k v = some w →
      ∃ c, WGraph.Chain wg source c v ∧ chainWeight c = w := by
  intro k
  induction k with
  | zero =>
    intro v w h
    have h2 : initialDistances source v = some w := h
    obtain ⟨hvs, hw0⟩ := initialDistances_eq h2
    subst hvs
    exact ⟨[], WGraph.Chain.nil _, by simp [chainWeight, hw0]⟩
  | succ k ih =>
    intro v w h
    have h' : relaxEdges wg.edges (bellmanFordRounds wg source k) v =
        some w := h
    exact relaxEdges_realised wg.edges _ (fun e he => he) ih v w h'

/-! ## Optimality: computed distances bound every walk -/

/-- The fold-level optimality lemma. After relaxing the edge
list `es₁` (in place, in order) starting from a state `d` that
already bounds every walk of at most `k` edges, the result
bounds every walk of at most `k + 1` edges whose last edge lies
in `es₁` (or which already had at most `k` edges): when the
walk's last edge is processed, its prefix is already bounded,
and later steps only lower distances further. -/
theorem fold_opt {wg : WGraph} {source : Nat} (k : Nat) :
    ∀ (es₁ : List (Nat × Nat × Int)) (d : Nat → Option Int),
      (∀ v c, WGraph.Chain wg source c v → c.length ≤ k →
        ∃ w, d v = some w ∧ w ≤ chainWeight c) →
      ∀ v c, WGraph.Chain wg source c v → c.length ≤ k + 1 →
        (c.length ≤ k ∨ ∃ c₀ u wₑ, c = c₀ ++ [(u, v, wₑ)] ∧
          (u, v, wₑ) ∈ es₁) →
        ∃ w, relaxEdges es₁ d v = some w ∧ w ≤ chainWeight c := by
  intro es₁
  induction es₁ with
  | nil =>
    intro d hyp v c hc hlen hcond
    rcases hcond with hle | ⟨c₀, u, wₑ, -, hmem⟩
    · exact hyp v c hc hle
    · simp at hmem
  | cons e es₁ ih =>
    intro d hyp v c hc hlen hcond
    have hyp' : ∀ v c, WGraph.Chain wg source c v → c.length ≤ k →
        ∃ w, step d e v = some w ∧ w ≤ chainWeight c := by
      intro v c hc hle
      obtain ⟨dv, hdv, hdvle⟩ := hyp v c hc hle
      obtain ⟨w', hw'⟩ := step_some hdv
      have hle2 := step_le_of_some hdv hw'
      exact ⟨w', hw', by omega⟩
    rcases hcond with hle | ⟨c₀, u, wₑ, hceq, hmem⟩
    · rw [relaxEdges_cons]
      exact ih (step d e) hyp' v c hc hlen (Or.inl hle)
    · rw [List.mem_cons] at hmem
      rcases hmem with rfl | hmem
      · -- the walk's last edge is the edge processed first
        rw [hceq] at hc
        obtain ⟨m, hc₀, hc₁⟩ := hc.append_split
        obtain ⟨h1, -, -⟩ := hc₁.cons_inv
        have h1' : u = m := h1
        subst m
        have hc0len : c₀.length ≤ k := by
          have hL : c.length = c₀.length + 1 := by
            rw [hceq]
            simp [List.length_append]
          omega
        obtain ⟨du, hdu, hdule⟩ := hyp u c₀ hc₀ hc0len
        obtain ⟨w', hw', hw'le⟩ := step_some_edge hdu
        obtain ⟨w'', hw'', hw''le⟩ :=
          relaxEdges_le_some es₁ (step d (u, v, wₑ)) v w' hw'
        refine ⟨w'', ?_, ?_⟩
        · rw [relaxEdges_cons]
          exact hw''
        · have hwgt : chainWeight c = chainWeight c₀ + wₑ := by
            rw [hceq, chainWeight_append]
            have h5 : chainWeight [(u, v, wₑ)] = wₑ := by
              simp [chainWeight]
            omega
          omega
      · rw [relaxEdges_cons]
        exact ih (step d e) hyp' v c hc hlen
          (Or.inr ⟨c₀, u, wₑ, hceq, hmem⟩)

/-- Optimality, by induction on rounds: after `k` rounds, the
computed distance at `v` is at most the weight of every walk
from the source to `v` with at most `k` edges. No hypothesis is
needed for this direction either. -/
theorem rounds_opt {wg : WGraph} {source : Nat} :
    ∀ (k : Nat) (v : Nat) (c : List (Nat × Nat × Int)),
      WGraph.Chain wg source c v → c.length ≤ k →
      ∃ w, bellmanFordRounds wg source k v = some w ∧
        w ≤ chainWeight c := by
  intro k
  induction k with
  | zero =>
    intro v c hc hlen
    have hceq : c = [] := by
      cases c with
      | nil => rfl
      | cons e es => simp only [List.length_cons] at hlen; omega
    subst hceq
    have hvs : v = source := by cases hc; rfl
    subst hvs
    exact ⟨0, by simp [bellmanFordRounds, initialDistances],
      by simp [chainWeight]⟩
  | succ k ih =>
    intro v c hc hlen
    show ∃ w, relaxEdges wg.edges (bellmanFordRounds wg source k) v =
      some w ∧ w ≤ chainWeight c
    apply fold_opt k wg.edges (bellmanFordRounds wg source k) ih v c
      hc hlen
    by_cases hle : c.length ≤ k
    · exact Or.inl hle
    · have hne : c ≠ [] := by
        intro hcc
        subst hcc
        simp at hle
      obtain ⟨c₀, u, wₑ, hceq, -, hedge⟩ := hc.split_last hne
      exact Or.inr ⟨c₀, u, wₑ, hceq, hedge⟩

/-! ## The specification: the bounded-walk minimum -/

/-- All walks from `source` to `v` with at most `k` edges,
enumerated: the empty walk at the source, plus every walk of at
most `k` edges ending at some `u` extended by one edge into
`v`. Membership is characterised exactly by
`chainsBetween_sound` and `chainsBetween_complete`. -/
def chainsBetween (wg : WGraph) (source : Nat) :
    Nat → Nat → List (List (Nat × Nat × Int))
  | 0, v => if v = source then [[]] else []
  | k + 1, v =>
    chainsBetween wg source k v ++
      wg.edges.flatMap (fun e =>
        if e.2.1 = v then
          (chainsBetween wg source k e.1).map (fun c => c ++ [e])
        else [])

theorem chainsBetween_sound {wg : WGraph} {source : Nat} :
    ∀ (k : Nat) (v : Nat) (c : List (Nat × Nat × Int)),
      c ∈ chainsBetween wg source k v →
      WGraph.Chain wg source c v ∧ c.length ≤ k := by
  intro k
  induction k with
  | zero =>
    intro v c hc
    simp only [chainsBetween] at hc
    by_cases hv : v = source
    · subst hv
      rw [ite_eq_left rfl] at hc
      simp at hc
      subst hc
      exact ⟨WGraph.Chain.nil _, by simp⟩
    · rw [ite_eq_right hv] at hc
      simp at hc
  | succ k ih =>
    intro v c hc
    simp only [chainsBetween] at hc
    rw [List.mem_append] at hc
    rcases hc with hc | hc
    · obtain ⟨hch, hlen⟩ := ih v c hc
      exact ⟨hch, by omega⟩
    · rw [List.mem_flatMap] at hc
      obtain ⟨e, he, hc⟩ := hc
      by_cases htarget : e.2.1 = v
      · rw [ite_eq_left htarget] at hc
        rw [List.mem_map] at hc
        obtain ⟨c₀, hc₀, hceq⟩ := hc
        obtain ⟨hch₀, hlen₀⟩ := ih e.1 c₀ hc₀
        subst hceq
        refine ⟨hch₀.append ?_, by
          simp only [List.length_append, List.length_cons,
            List.length_nil]
          omega⟩
        have hsingle : WGraph.Chain wg e.1 [e] e.2.1 :=
          WGraph.Chain.cons he (WGraph.Chain.nil _)
        rwa [htarget] at hsingle
      · rw [ite_eq_right htarget] at hc
        simp at hc

theorem chainsBetween_complete {wg : WGraph} {source : Nat} :
    ∀ (k : Nat) (v : Nat) (c : List (Nat × Nat × Int)),
      WGraph.Chain wg source c v → c.length ≤ k →
      c ∈ chainsBetween wg source k v := by
  intro k
  induction k with
  | zero =>
    intro v c hc hlen
    have hceq : c = [] := by
      cases c with
      | nil => rfl
      | cons e es => simp only [List.length_cons] at hlen; omega
    subst hceq
    have hvs : v = source := by cases hc; rfl
    subst hvs
    simp [chainsBetween]
  | succ k ih =>
    intro v c hc hlen
    simp only [chainsBetween, List.mem_append]
    by_cases hle : c.length ≤ k
    · exact Or.inl (ih v c hc hle)
    · have hne : c ≠ [] := by
        intro hcc
        subst hcc
        simp at hle
      obtain ⟨c₀, u, wₑ, hceq, hc₀, hedge⟩ := hc.split_last hne
      have hc0len : c₀.length ≤ k := by
        have hL : c.length = c₀.length + 1 := by
          rw [hceq]
          simp [List.length_append]
        omega
      have hc0mem : c₀ ∈ chainsBetween wg source k u :=
        ih u c₀ hc₀ hc0len
      refine Or.inr ?_
      rw [List.mem_flatMap]
      exact ⟨(u, v, wₑ), hedge, by
        have hcond : (u, v, wₑ).2.1 = v := rfl
        rw [ite_eq_left hcond]
        rw [List.mem_map]
        exact ⟨c₀, hc0mem, by rw [hceq]⟩⟩

/-- The minimum of a list of weights, as an `Option`: `none` on
the empty list. -/
def optMin : List Int → Option Int
  | [] => none
  | w :: ws => some (ws.foldl (fun a b => min a b) w)

theorem foldl_min_spec :
    ∀ (l : List Int) (a : Int),
      (l.foldl (fun a b => min a b) a) ≤ a ∧
      (∀ x ∈ l, (l.foldl (fun a b => min a b) a) ≤ x) ∧
      ((l.foldl (fun a b => min a b) a) = a ∨
        (l.foldl (fun a b => min a b) a) ∈ l) := by
  intro l
  induction l with
  | nil =>
    intro a
    show a ≤ a ∧ (∀ x ∈ ([] : List Int), a ≤ x) ∧
      (a = a ∨ a ∈ ([] : List Int))
    exact ⟨by omega, fun x hx => by simp at hx, Or.inl rfl⟩
  | cons b l ih =>
    intro a
    have hstep : (b :: l).foldl (fun a b => min a b) a =
        l.foldl (fun a b => min a b) (min a b) := rfl
    rw [hstep]
    obtain ⟨h1, h2, h3⟩ := ih (min a b)
    refine ⟨by omega, ?_, ?_⟩
    · intro x hx
      rw [List.mem_cons] at hx
      rcases hx with rfl | hx
      · omega
      · exact h2 x hx
    · rcases h3 with h3 | h3
      · have hmin : min a b = a ∨ min a b = b := by omega
        rcases hmin with hm | hm
        · exact Or.inl (by omega)
        · refine Or.inr ?_
          have hfb : l.foldl (fun a b => min a b) (min a b) = b := by
            omega
          rw [hfb]
          exact List.mem_cons_self
      · exact Or.inr (List.mem_cons_of_mem b h3)

theorem optMin_eq_some {l : List Int} {w : Int}
    (h : optMin l = some w) : w ∈ l ∧ ∀ x ∈ l, w ≤ x := by
  cases l with
  | nil => simp [optMin] at h
  | cons a l =>
    have h2 : (l.foldl (fun a b => min a b) a) = w := by
      have h' := h
      simp only [optMin] at h'
      exact Option.some.inj h'
    obtain ⟨h1, h2le, h3⟩ := foldl_min_spec l a
    subst h2
    constructor
    · rcases h3 with h3 | h3
      · rw [h3]
        exact List.mem_cons_self
      · exact List.mem_cons_of_mem a h3
    · intro x hx
      rw [List.mem_cons] at hx
      rcases hx with rfl | hx
      · omega
      · exact h2le x hx

/-- The shortest-path specification, in the draft's intended
shape: for each vertex (in vertex-list order), the minimum
weight over all walks from the source with at most
`vertices.length` edges, if any such walk exists. Under
`NoNegCycleFrom` this is the true shortest weight: every walk
shortens into the bound with no greater weight
(`WGraph.Chain.shorten`), and relaxation is optimal against
every bounded walk (`rounds_opt`). -/
def shortestPaths (wg : WGraph) (source : Nat) : List (Nat × Int) :=
  wg.vertices.filterMap (fun v =>
    (optMin ((chainsBetween wg source wg.vertices.length v).map
      chainWeight)).map (fun w => (v, w)))

theorem filterMap_congr {α β : Type} {l : List α}
    {f g : α → Option β} (h : ∀ x ∈ l, f x = g x) :
    l.filterMap f = l.filterMap g := by
  induction l with
  | nil => rfl
  | cons a l ih =>
    rw [List.filterMap_cons, List.filterMap_cons,
      h a List.mem_cons_self,
      ih (fun x hx => h x (List.mem_cons_of_mem a hx))]

/-- **Bellman-Ford correctness** — the draft's headline claim,
repaired. The draft stated the equation with no negative-cycle
hypothesis; that form is FALSE (counterexample in the module
doc). With `NoNegCycleFrom` added — and the platform's
well-formedness hypotheses — after `n ≥ vertices.length`
rounds the computed distances equal the shortest-path weights
for every vertex. -/
theorem bellmanFord_correctness {wg : WGraph} {source n : Nat}
    (hnodup : wg.vertices.Nodup)
    (hend : ∀ e ∈ wg.edges, e.1 ∈ wg.vertices ∧
      e.2.1 ∈ wg.vertices)
    (hsrc : source ∈ wg.vertices)
    (hnc : wg.NoNegCycleFrom source)
    (hN : wg.vertices.length ≤ n) :
    bellmanFord wg source n = shortestPaths wg source := by
  unfold bellmanFord shortestPaths
  apply filterMap_congr
  intro v hv
  cases hR : bellmanFordRounds wg source n v with
  | none =>
    have hno : chainsBetween wg source wg.vertices.length v =
        [] := by
      cases hcb : chainsBetween wg source wg.vertices.length v
        with
      | nil => rfl
      | cons c cs =>
        exfalso
        have hc : c ∈ chainsBetween wg source wg.vertices.length
            v := by
          rw [hcb]
          exact List.mem_cons_self
        obtain ⟨hch, hlen⟩ := chainsBetween_sound _ _ _ hc
        obtain ⟨w, hw, -⟩ := rounds_opt n v c hch (by omega)
        rw [hR] at hw
        simp at hw
    rw [hno]
    simp [optMin]
  | some w =>
    have hspec : optMin ((chainsBetween wg source
        wg.vertices.length v).map chainWeight) = some w := by
      obtain ⟨c, hc, hcw⟩ := rounds_realised n v w hR
      obtain ⟨c', hc', hlen', hw'⟩ :=
        WGraph.Chain.shorten hnodup hend hsrc hnc c.length c v
          (by omega) hc
      have hc'mem : c' ∈ chainsBetween wg source
          wg.vertices.length v :=
        chainsBetween_complete _ _ _ hc' (by omega)
      have hwtmem : chainWeight c' ∈
          (chainsBetween wg source wg.vertices.length v).map
            chainWeight :=
        List.mem_map.mpr ⟨c', hc'mem, rfl⟩
      cases hopt : optMin ((chainsBetween wg source
          wg.vertices.length v).map chainWeight) with
      | none =>
        exfalso
        cases hlist : (chainsBetween wg source
            wg.vertices.length v).map chainWeight with
        | nil =>
          rw [hlist] at hwtmem
          simp at hwtmem
        | cons x xs =>
          rw [hlist] at hopt
          simp [optMin] at hopt
      | some w' =>
        obtain ⟨hmem, hle⟩ := optMin_eq_some hopt
        have hw'le : w' ≤ w := by
          have hle2 := hle (chainWeight c') hwtmem
          omega
        have hwle : w ≤ w' := by
          rw [List.mem_map] at hmem
          obtain ⟨c'', hc''mem, hweq⟩ := hmem
          obtain ⟨hch'', hlen''⟩ :=
            chainsBetween_sound _ _ _ hc''mem
          obtain ⟨w₀, hw₀, hw₀le⟩ :=
            rounds_opt n v c'' hch'' (by omega)
          rw [hR] at hw₀
          have hww : w = w₀ := Option.some.inj hw₀
          omega
        have hww : w' = w := by omega
        rw [hww]
    rw [hspec]

end AxiomCode
