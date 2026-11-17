import Spec
import Tactics

/-!
# AxiomCode — Graph platform

The shared graph substrate for the L2 graph entries (Item 6:
topological sort, bellman-ford, floyd-warshall, kruskal, prim,
articulation). Authored under the L2 promotion procedure
(`lean/PROMOTION.md`); it is a platform module, not an algorithm
entry — later Item 6 stages grow it in their own promotions when an
entry needs a new platform notion.

## Design decision (recorded 2026-11-16, Item 6 stage 1)

**Representation.** A graph is a pair of lists: `vertices : List Nat`
and `edges : List (Nat × Nat)`, directed and unweighted. This follows
the library's established list-based, core-only pattern (the trie's
association-list children, the LRU cache's list state) and keeps every
notion decidable-by-inspection where an algorithm needs it. Vertices
are `Nat`, per the Item 6 brief. Well-formedness (vertex list
duplicate-free, edge endpoints among the vertices) is carried as
hypotheses on the theorems that need it, not as structure invariants —
again the house pattern (compare `Spec`'s predicates).

**Weighted layer.** A separate structure `WGraph` with
`edges : List (Nat × Nat × Int)` and a projection `WGraph.toGraph`
that drops the weights. Weights are `Int`, not `Nat`, because
bellman-ford and floyd-warshall must allow negative edge weights.
Two structures rather than one weighted-only structure, so the
unweighted entries (topological sort here, articulation later) state
their theorems over plain pairs; and every unweighted notion below
(`Reach`, `IsDAG`, `Connected`) applies to a weighted graph through
`toGraph`, which is what kruskal and prim will use for their
connectivity/acyclicity content.

**Why not Mathlib's `SimpleGraph`.** Mathlib is a dependency of the
lakefile, and importing its graph theory was considered and rejected
for the platform: `SimpleGraph` is an undirected, loop-free relation
over an arbitrary vertex *type* with finiteness side-conditions,
while these entries are directed-first, list-based algorithms over
`Nat` whose drafts and specifications all speak of vertex/edge
lists. The substrate the entries actually share — adjacency by list
filter, an inductive reachability, induced subgraphs, source
existence in a finite DAG — is small, and hand-rolling it keeps the
platform inside the library's core-only discipline (every module so
far imports only `Spec`/`Tactics`). The one genuinely hard platform
fact, source existence, is proved below from list lemmas alone.

**What each coming entry uses.** Topological sort: `Reach`, `IsDAG`,
`induced`, `exists_source`, `findSource`. Bellman-ford and
floyd-warshall: `WGraph` (weights, `toGraph` for reachability
content). Kruskal and prim: `WGraph`, `Connected`/`Undirected` (via
`symmetrize`), `IsDAG` on `toGraph` for forest content. Articulation:
`symmetrize`, `Reach`, `induced` (vertex removal is induction on the
erased vertex list).
-/

namespace AxiomCode

/-- A directed, unweighted graph over `Nat` vertices, represented as a
vertex list and an edge list of ordered pairs. -/
structure Graph where
  vertices : List Nat
  edges : List (Nat × Nat)

/-- The out-neighbours of `u`: the second components of the edges
whose first component is `u`. -/
def Graph.neighbors (g : Graph) (u : Nat) : List Nat :=
  (g.edges.filter (fun e => e.1 = u)).map Prod.snd

theorem Graph.mem_neighbors {g : Graph} {u v : Nat} :
    v ∈ g.neighbors u ↔ (u, v) ∈ g.edges := by
  constructor
  · intro h
    rw [Graph.neighbors, List.mem_map] at h
    obtain ⟨e, he, h2⟩ := h
    rw [List.mem_filter] at he
    obtain ⟨he, h1⟩ := he
    have h1' : e.1 = u := of_decide_eq_true h1
    have hpair : e = (u, v) := Prod.ext h1' h2
    rw [hpair] at he
    exact he
  · intro h
    rw [Graph.neighbors, List.mem_map]
    refine ⟨(u, v), ?_, rfl⟩
    rw [List.mem_filter]
    exact ⟨h, by rw [decide_eq_true_eq]⟩

/-- Reachability by a directed walk of length ≥ 0: `Reach g u v`
holds when `v` is reachable from `u` following edges forward.
`refl` is the empty walk; `step` prepends one edge. -/
inductive Graph.Reach (g : Graph) : Nat → Nat → Prop
  | refl (v : Nat) : Reach g v v
  | step {u v w : Nat} : (u, v) ∈ g.edges → Reach g v w → Reach g u w

/-- A single edge is a walk of length 1. -/
theorem Graph.Reach.of_edge {g : Graph} {u v : Nat} (h : (u, v) ∈ g.edges) :
    Reach g u v :=
  Reach.step h (Reach.refl v)

/-- Walks concatenate. -/
theorem Graph.Reach.trans {g : Graph} {u v w : Nat}
    (h₁ : Reach g u v) (h₂ : Reach g v w) : Reach g u w := by
  induction h₁ with
  | refl => exact h₂
  | step he _ ih => exact Reach.step he (ih h₂)

/-- Reachability is monotone in the edge set: enlarging the edges
cannot destroy a walk. -/
theorem Graph.Reach.mono {g₁ g₂ : Graph}
    (h : ∀ e ∈ g₁.edges, e ∈ g₂.edges) {u v : Nat} :
    Reach g₁ u v → Reach g₂ u v := by
  intro hr
  induction hr with
  | refl => exact Reach.refl _
  | step he _ ih => exact Reach.step (h _ he) ih

/-- A walk that starts at a vertex of the graph ends at a vertex of
the graph, provided every edge's endpoints are vertices. -/
theorem Graph.Reach.mem_vertices {g : Graph}
    (hend : ∀ e ∈ g.edges, e.1 ∈ g.vertices ∧ e.2 ∈ g.vertices)
    {u v : Nat} (hu : u ∈ g.vertices) (h : Reach g u v) :
    v ∈ g.vertices := by
  induction h with
  | refl => exact hu
  | step he _ ih => exact ih (hend _ he).2

/-- Acyclicity: no edge closes a walk back to its own start.
Equivalently, no vertex reaches itself by a walk of length ≥ 1 (a
self-loop edge is excluded because `Reach` includes the empty walk). -/
def Graph.IsDAG (g : Graph) : Prop :=
  ∀ u v, (u, v) ∈ g.edges → ¬ Reach g v u

/-- The subgraph induced by a vertex list `vs`: the vertices are
`vs`, and the edges are `g`'s edges with both endpoints in `vs`. -/
def Graph.induced (g : Graph) (vs : List Nat) : Graph :=
  ⟨vs, g.edges.filter (fun e => e.1 ∈ vs ∧ e.2 ∈ vs)⟩

theorem Graph.vertices_induced {g : Graph} {vs : List Nat} :
    (g.induced vs).vertices = vs := rfl

theorem Graph.mem_edges_induced {g : Graph} {vs : List Nat} {e : Nat × Nat} :
    e ∈ (g.induced vs).edges ↔ e ∈ g.edges ∧ e.1 ∈ vs ∧ e.2 ∈ vs := by
  unfold Graph.induced
  rw [List.mem_filter]
  constructor
  · rintro ⟨h1, h2⟩
    exact ⟨h1, of_decide_eq_true h2⟩
  · rintro ⟨h1, h2, h3⟩
    exact ⟨h1, by rw [decide_eq_true_eq]; exact ⟨h2, h3⟩⟩

/-- Acyclicity is hereditary: an induced subgraph of a DAG is a DAG. -/
theorem Graph.IsDAG.induced {g : Graph} (hdag : IsDAG g) (vs : List Nat) :
    IsDAG (g.induced vs) := by
  intro u v huv hreach
  have huv' : (u, v) ∈ g.edges := (Graph.mem_edges_induced.mp huv).1
  have hreach' : Reach g v u :=
    Graph.Reach.mono (fun e he => (Graph.mem_edges_induced.mp he).1) hreach
  exact hdag u v huv' hreach'

/-- Whether `s` has an incoming edge from some vertex of `vs`
(decidable form, for the algorithms). -/
def Graph.hasIncomingFrom (g : Graph) (vs : List Nat) (s : Nat) : Bool :=
  g.edges.any (fun e => decide (e.2 = s ∧ e.1 ∈ vs))

theorem Graph.hasIncomingFrom_eq_true {g : Graph} {vs : List Nat} {s : Nat} :
    g.hasIncomingFrom vs s = true ↔ ∃ u ∈ vs, (u, s) ∈ g.edges := by
  unfold Graph.hasIncomingFrom
  rw [List.any_eq_true]
  constructor
  · rintro ⟨e, he, hdec⟩
    obtain ⟨h2, h1⟩ := of_decide_eq_true hdec
    refine ⟨e.1, h1, ?_⟩
    have : e = (e.1, s) := Prod.ext rfl h2
    rw [this] at he
    exact he
  · rintro ⟨u, hu, h⟩
    exact ⟨(u, s), h, by rw [decide_eq_true_eq]; exact ⟨rfl, hu⟩⟩

/-- Find a source of the vertex list `rem` in `g`: a vertex of `rem`
with no incoming edge from `rem`, if one exists. -/
def Graph.findSource (g : Graph) (rem : List Nat) : Option Nat :=
  rem.find? (fun s => !g.hasIncomingFrom rem s)

theorem Graph.findSource_eq_some {g : Graph} {rem : List Nat} {s : Nat}
    (h : g.findSource rem = some s) :
    s ∈ rem ∧ ∀ u ∈ rem, (u, s) ∉ g.edges := by
  unfold Graph.findSource at h
  have hmem : s ∈ rem := List.mem_of_find?_eq_some h
  have hval : (!g.hasIncomingFrom rem s) = true :=
    List.find?_some (p := fun s => !g.hasIncomingFrom rem s) (a := s) (l := rem) h
  refine ⟨hmem, fun u hu hcon => ?_⟩
  have : g.hasIncomingFrom rem s = true :=
    Graph.hasIncomingFrom_eq_true.mpr ⟨u, hu, hcon⟩
  rw [this] at hval
  exact Bool.false_ne_true hval

theorem Graph.findSource_isSome {g : Graph} {rem : List Nat}
    (h : ∃ s ∈ rem, ∀ u ∈ rem, (u, s) ∉ g.edges) :
    (g.findSource rem).isSome := by
  obtain ⟨s, hs, hsrc⟩ := h
  rw [Graph.findSource, List.find?_isSome]
  refine ⟨s, hs, ?_⟩
  show (!g.hasIncomingFrom rem s) = true
  have hnot : ¬ g.hasIncomingFrom rem s = true := by
    rw [Graph.hasIncomingFrom_eq_true]
    rintro ⟨u, hu, hcon⟩
    exact hsrc u hu hcon
  cases hb : g.hasIncomingFrom rem s with
  | true => exact absurd hb hnot
  | false => rfl

/-- The source-ancestor lemma, by strong induction on the vertex
count: in a finite DAG, every vertex has an ancestor (possibly
itself) that is a source — a vertex with no incoming edge from the
graph. Proved by removing the vertex itself and applying the
induction hypothesis to the induced subgraph on the remaining
vertices; the ancestor found there cannot gain an incoming edge from
the removed vertex, or it would reach it and close a cycle. -/
theorem Graph.source_ancestor_aux : ∀ (n : Nat) (g : Graph),
    g.vertices.length ≤ n → g.vertices.Nodup →
    (∀ e ∈ g.edges, e.1 ∈ g.vertices ∧ e.2 ∈ g.vertices) →
    IsDAG g → ∀ v ∈ g.vertices,
    ∃ s ∈ g.vertices, Reach g s v ∧ ∀ u ∈ g.vertices, (u, s) ∉ g.edges := by
  intro n
  induction n with
  | zero =>
    intro g hlen _ _ _ v hv
    have h0 : g.vertices.length = 0 := Nat.eq_zero_of_le_zero hlen
    cases h : g.vertices with
    | nil => simp [h] at hv
    | cons a as => simp [h] at h0
  | succ n ih =>
    intro g hlen hnodup hend hdag v hv
    cases hb : g.hasIncomingFrom g.vertices v with
    | false =>
      refine ⟨v, hv, Reach.refl v, fun u hu hcon => ?_⟩
      have hcon' : g.hasIncomingFrom g.vertices v = true :=
        Graph.hasIncomingFrom_eq_true.mpr ⟨u, hu, hcon⟩
      rw [hb] at hcon'
      exact Bool.false_ne_true hcon'
    | true =>
      obtain ⟨u, hu, huv⟩ := Graph.hasIncomingFrom_eq_true.mp hb
      have huv_ne : u ≠ v := by
        rintro rfl
        exact hdag u u huv (Reach.refl u)
      -- The induced subgraph on the vertices other than `v`.
      have hu_vs : u ∈ g.vertices.erase v := (List.mem_erase_of_ne huv_ne).mpr hu
      have hlen' : (g.induced (g.vertices.erase v)).vertices.length ≤ n := by
        rw [Graph.vertices_induced, List.length_erase_of_mem hv]
        omega
      have hnodup' : (g.induced (g.vertices.erase v)).vertices.Nodup := by
        rw [Graph.vertices_induced]
        exact hnodup.erase v
      have hend' : ∀ e ∈ (g.induced (g.vertices.erase v)).edges,
          e.1 ∈ (g.induced (g.vertices.erase v)).vertices ∧
          e.2 ∈ (g.induced (g.vertices.erase v)).vertices := by
        intro e he
        rw [Graph.vertices_induced]
        exact ⟨(Graph.mem_edges_induced.mp he).2.1,
          (Graph.mem_edges_induced.mp he).2.2⟩
      obtain ⟨s, hs_vs, hreach', hsource'⟩ :=
        ih (g.induced (g.vertices.erase v)) hlen' hnodup' hend'
          (hdag.induced _) u hu_vs
      rw [Graph.vertices_induced] at hs_vs
      have hs : s ∈ g.vertices := List.mem_of_mem_erase hs_vs
      have hreach_su : Reach g s u :=
        Graph.Reach.mono (fun e he => (Graph.mem_edges_induced.mp he).1) hreach'
      have hreach_sv : Reach g s v :=
        hreach_su.trans (Graph.Reach.of_edge huv)
      refine ⟨s, hs, hreach_sv, fun w hw hwedge => ?_⟩
      by_cases hwv : w = v
      · subst hwv
        exact hdag w s hwedge hreach_sv
      · have hw_vs : w ∈ g.vertices.erase v := (List.mem_erase_of_ne hwv).mpr hw
        have hwedge' : (w, s) ∈ (g.induced (g.vertices.erase v)).edges :=
          Graph.mem_edges_induced.mpr ⟨hwedge, hw_vs, hs_vs⟩
        exact hsource' w hw_vs hwedge'

/-- Source existence: a nonempty finite DAG has a source — a vertex
with no incoming edge from the graph. -/
theorem Graph.exists_source {g : Graph} (hne : g.vertices ≠ [])
    (hnodup : g.vertices.Nodup)
    (hend : ∀ e ∈ g.edges, e.1 ∈ g.vertices ∧ e.2 ∈ g.vertices)
    (hdag : IsDAG g) :
    ∃ s ∈ g.vertices, ∀ u ∈ g.vertices, (u, s) ∉ g.edges := by
  obtain ⟨v, hv⟩ : ∃ v, v ∈ g.vertices := by
    cases h : g.vertices with
    | nil => exact absurd h hne
    | cons a as => exact ⟨a, List.mem_cons_self⟩
  obtain ⟨s, hs, _, hsrc⟩ :=
    Graph.source_ancestor_aux g.vertices.length g (by omega) hnodup hend hdag v hv
  exact ⟨s, hs, hsrc⟩

/-- The symmetrization of a graph: both directions of every edge.
This is the underlying undirected graph, used for connectivity. -/
def Graph.symmetrize (g : Graph) : Graph :=
  ⟨g.vertices, g.edges ++ g.edges.map Prod.swap⟩

theorem Graph.mem_edges_symmetrize {g : Graph} {u v : Nat} :
    (u, v) ∈ g.symmetrize.edges ↔ (u, v) ∈ g.edges ∨ (v, u) ∈ g.edges := by
  unfold Graph.symmetrize
  rw [List.mem_append, List.mem_map]
  constructor
  · rintro (h | ⟨e, he, hswap⟩)
    · exact Or.inl h
    · right
      have h1 : e.2 = u := congrArg Prod.fst hswap
      have h2 : e.1 = v := congrArg Prod.snd hswap
      have : e = (v, u) := Prod.ext h2 h1
      rw [this] at he
      exact he
  · rintro (h | h)
    · exact Or.inl h
    · right
      exact ⟨(v, u), h, Prod.ext rfl rfl⟩

/-- An undirected graph: every edge is present in both directions. -/
def Graph.Undirected (g : Graph) : Prop :=
  ∀ u v, (u, v) ∈ g.edges → (v, u) ∈ g.edges

/-- Connectivity: every two vertices are joined by a walk in the
symmetrized graph (direction ignored). -/
def Graph.Connected (g : Graph) : Prop :=
  ∀ u ∈ g.vertices, ∀ v ∈ g.vertices, Reach g.symmetrize u v

/-- A weighted directed graph over `Nat` vertices: edges are triples
`(source, target, weight)` with `Int` weights (negative weights are
admitted — bellman-ford and floyd-warshall need them). -/
structure WGraph where
  vertices : List Nat
  edges : List (Nat × Nat × Int)

/-- Drop the weights: the underlying unweighted graph. Every
unweighted notion (`Reach`, `IsDAG`, `Connected`) applies to a
weighted graph through this projection. -/
def WGraph.toGraph (wg : WGraph) : Graph :=
  ⟨wg.vertices, wg.edges.map (fun e => (e.1, e.2.1))⟩

theorem WGraph.vertices_toGraph {wg : WGraph} :
    wg.toGraph.vertices = wg.vertices := rfl

theorem WGraph.mem_toGraph_edges {wg : WGraph} {u v : Nat} :
    (u, v) ∈ wg.toGraph.edges ↔ ∃ w : Int, (u, v, w) ∈ wg.edges := by
  unfold WGraph.toGraph
  rw [List.mem_map]
  constructor
  · rintro ⟨e, he, hproj⟩
    obtain ⟨a, b, w⟩ := e
    simp only [Prod.mk.injEq] at hproj
    obtain ⟨h1, h2⟩ := hproj
    subst h1
    subst h2
    exact ⟨w, he⟩
  · rintro ⟨w, h⟩
    exact ⟨(u, v, w), h, rfl⟩

end AxiomCode
