import Spec
import Tactics
import Algorithms.Graph
import Algorithms.Kruskal


/-!
# Articulation points

A vertex is an articulation point when removing it
disconnects some pair of remaining vertices that were
connected before. The algorithm here is the naive one —
remove each vertex in turn and re-check every pair with the
decidable reachability oracle (`connectedP`, from the
Kruskal entry) — and its correctness is the full
characterization `mem_articulationPoints`: a vertex is in
the output iff it is an articulation point in the stated
sense. The naive form is chosen deliberately: its
correctness is by construction against the specification,
whereas the DFS/lowlink algorithm's correctness rests on a
DFS-tree characterization (discovery times, tree and back
edges, subtree intervals) that this library does not carry;
building that machinery is a platform gap, recorded as such,
not a gap in this entry's claim.

## Statement-honesty record

The draft this entry promotes
(`articulationpointsalgorithmcorrectness (g.lean`) was a
shell that did not elaborate: a fieldless `Graph`, references
to a `G.vertices` the structure does not have,
`isArticulationPoint` as a constant with no body, and its
theorem closed with a placeholder proof. Worse, the draft
contained no algorithm at all: its "output" was a universally
quantified `Set G.vertices` parameter, so as written it
asserted that EVERY vertex set consists of articulation
points — false on its face (single-vertex graph, the set
containing that vertex: no pair of remaining vertices exists
to disconnect). Only the soundness direction was even
attempted. The repair, in the least-repair form: a real
algorithm (`articulationPoints`, a list, in the platform's
list vocabulary) and the full iff against the standard
specification (`IsArticulationPoint`, stated with the
platform's `Graph.Reach` over the symmetrized graph, removal
as the induced subgraph on the remaining vertices) — the
completeness direction the draft never attempted is proved
as well.
-/

namespace AxiomCode

/-- The specification: `v` is an articulation point of `g` when
removing it disconnects some pair of remaining vertices that
were connected in `g` (undirected reachability throughout, via
the symmetrized graph; removal is the induced subgraph on the
remaining vertices). -/
def IsArticulationPoint (g : Graph) (v : Nat) : Prop :=
  v ∈ g.vertices ∧ ∃ u ∈ g.vertices, ∃ w ∈ g.vertices,
    u ≠ v ∧ w ≠ v ∧ Graph.Reach g.symmetrize u w ∧
    ¬ Graph.Reach (g.induced (g.vertices.erase v)).symmetrize u w

/-- The per-vertex test of the naive algorithm: some pair of
remaining vertices is connected in `g` (decidable oracle) but
not in the graph with `v` removed. -/
def articulationTest (g : Graph) (v : Nat) : Bool :=
  g.vertices.any (fun u => g.vertices.any (fun w =>
    decide (u ≠ v) && decide (w ≠ v) &&
    connectedP g.edges g.vertices u w &&
    !(connectedP (g.induced (g.vertices.erase v)).edges
        (g.vertices.erase v) u w)))

/-- The naive articulation-points algorithm: remove each
vertex in turn and re-check all pairs with the reachability
oracle. Its correctness is by construction against
`IsArticulationPoint` — no DFS-tree machinery is needed. -/
def articulationPoints (g : Graph) : List Nat :=
  g.vertices.filter (fun v => articulationTest g v)

theorem articulationPoints_nodup {g : Graph} (hV : g.vertices.Nodup) :
    (articulationPoints g).Nodup := hV.filter _

theorem articulationPoints_subset {g : Graph} :
    ∀ v ∈ articulationPoints g, v ∈ g.vertices :=
  fun v hv => (List.mem_filter.mp hv).1

/-- Endpoint well-formedness of the edges of the graph with
`v` removed, relative to the remaining vertices. -/
theorem induced_edges_endpoints {g : Graph} (v : Nat) :
    ∀ e ∈ (g.induced (g.vertices.erase v)).edges,
      e.1 ∈ g.vertices.erase v ∧ e.2 ∈ g.vertices.erase v := by
  intro e he
  have h2 := Graph.mem_edges_induced.mp he
  exact ⟨h2.2.1, h2.2.2⟩

/-- **Correctness, full iff**: the naive algorithm outputs
exactly the articulation points — a vertex is in the output
iff its removal disconnects some previously connected pair of
remaining vertices. Both directions are the oracle bridge
`connectedP_iff` applied to the graph and to the graph with
the vertex removed. -/
theorem mem_articulationPoints {g : Graph} (hV : g.vertices.Nodup)
    (hE : ∀ e ∈ g.edges, e.1 ∈ g.vertices ∧ e.2 ∈ g.vertices) {v : Nat} :
    v ∈ articulationPoints g ↔ IsArticulationPoint g v := by
  have hends1 := hE
  have hends2 := induced_edges_endpoints (g := g) v
  have hVerase : (g.vertices.erase v).Nodup := hV.erase _
  constructor
  · intro h
    obtain ⟨hv, hpred⟩ := List.mem_filter.mp h
    have hpred' : g.vertices.any (fun u => g.vertices.any (fun w =>
        decide (u ≠ v) && decide (w ≠ v) &&
        connectedP g.edges g.vertices u w &&
        !(connectedP (g.induced (g.vertices.erase v)).edges
            (g.vertices.erase v) u w))) = true := hpred
    rw [List.any_eq_true] at hpred'
    obtain ⟨u, hu, hpred'⟩ := hpred'
    rw [List.any_eq_true] at hpred'
    obtain ⟨w, hw, hpred'⟩ := hpred'
    rw [Bool.and_eq_true, Bool.and_eq_true, Bool.and_eq_true] at hpred'
    obtain ⟨⟨⟨h1, h2⟩, h3⟩, h4⟩ := hpred'
    have hu' : u ∈ g.vertices.erase v := (List.mem_erase_of_ne (of_decide_eq_true h1)).mpr hu
    refine ⟨hv, u, hu, w, hw, of_decide_eq_true h1, of_decide_eq_true h2,
      (connectedP_iff hV hends1 hu).mp h3, ?_⟩
    intro hreach
    have hc : connectedP (g.induced (g.vertices.erase v)).edges
        (g.vertices.erase v) u w = true :=
      (connectedP_iff hVerase hends2 hu').mpr hreach
    rw [hc] at h4
    exact Bool.false_ne_true h4
  · rintro ⟨hv, u, hu, w, hw, huv, hwv, hreach, hnreach⟩
    have hu' : u ∈ g.vertices.erase v := (List.mem_erase_of_ne huv).mpr hu
    apply List.mem_filter.mpr
    refine ⟨hv, ?_⟩
    show g.vertices.any (fun u => g.vertices.any (fun w =>
      decide (u ≠ v) && decide (w ≠ v) &&
      connectedP g.edges g.vertices u w &&
      !(connectedP (g.induced (g.vertices.erase v)).edges
          (g.vertices.erase v) u w))) = true
    rw [List.any_eq_true]
    refine ⟨u, hu, ?_⟩
    rw [List.any_eq_true]
    refine ⟨w, hw, ?_⟩
    rw [Bool.and_eq_true, Bool.and_eq_true, Bool.and_eq_true]
    refine ⟨⟨⟨decide_eq_true huv, decide_eq_true hwv⟩,
      (connectedP_iff hV hends1 hu).mpr hreach⟩, ?_⟩
    cases hc : connectedP (g.induced (g.vertices.erase v)).edges
        (g.vertices.erase v) u w with
    | false => rfl
    | true =>
      exact absurd ((connectedP_iff hVerase hends2 hu').mp hc) hnreach

end AxiomCode
