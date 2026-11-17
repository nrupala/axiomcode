import Spec
import Tactics
import Algorithms.Graph

/-!
# AxiomCode — Verified Topological Sort

Kahn's algorithm over the graph platform (`Algorithms.Graph`):
repeatedly emit a source of the remaining graph (a vertex with no
incoming edge from the remaining vertices) and remove it. Promoted
from `lean/drafts/topologicalsort_correctness.lean` under the L2
promotion procedure (`lean/PROMOTION.md`).

Statement-honesty record. The draft is a shell and its statement is
defective in three ways, recorded here rather than silently repaired:

- It does not elaborate at all. `Graph` is a fieldless structure, yet
  the statement references `g.vertices`, `g.edges` and `#g.vertices`;
  `topologicalSort` is declared to return `List g.vertices`, which is
  not a type; the bound variable `l` in `topologicalSort g = some l`
  is never introduced; and `= some l` compares a list against an
  `Option`. The platform's `Graph` (vertex/edge lists) is what the
  draft's field references can only mean, and the algorithm below
  returns the list directly — the draft's `some` is part of the
  shell's conflation, not a design requirement.
- The edge condition as written, `∀ v w ∈ l, (v, w) ∉ g.edges`, is
  the *wrong property*, and false for every graph with an edge:
  counterexample — vertices `[0, 1]`, edges `[(0, 1)]`, a DAG whose
  only candidate outputs are the permutations of `[0, 1]`; both
  contain `0` and `1`, and the pair `(0, 1)` is an edge, violating
  the condition. No algorithm could satisfy the draft's statement.
  The intended condition — every edge goes *forward* in the output —
  is the one proved below (`Before`).
- The draft's `isDAG` is a body-less `Bool`. Acyclicity is authored
  as the platform's proposition `Graph.IsDAG` (no edge closes a walk
  back to its start), and the draft's length conjunct
  (`l.length = #g.vertices`) is kept as the corollary
  `topologicalSort_length`.

The correctness theorem keeps the draft's shape: under the DAG
hypothesis (plus the platform's well-formedness hypotheses —
duplicate-free vertex list, edge endpoints among the vertices), the
output is a permutation of the vertices and every edge goes forward
in it.
-/

namespace AxiomCode

/-- `Before u v l`: `u` occurs in `l` strictly before `v` — the head
case finds `u` with `v` somewhere in the tail; the cons case skips an
element. -/
inductive Before (u v : Nat) : List Nat → Prop
  | head {xs : List Nat} : v ∈ xs → Before u v (u :: xs)
  | cons {x : Nat} {xs : List Nat} : Before u v xs → Before u v (x :: xs)

/-- Kahn's algorithm with fuel: emit a source of `rem`, remove it,
recurse. The fuel bounds the number of emissions; called with
`rem.length` it can emit every remaining vertex. On a cyclic
remainder no source exists and the output is the partial order
emitted so far — the correctness theorem claims nothing there. -/
def topoSortAux (g : Graph) (rem : List Nat) : Nat → List Nat
  | 0 => []
  | fuel + 1 =>
    match g.findSource rem with
    | none => []
    | some s => s :: topoSortAux g (rem.erase s) fuel

/-- Topological sort of a graph: Kahn's algorithm over its vertex
list, fuelled by the vertex count. -/
def topologicalSort (g : Graph) : List Nat :=
  topoSortAux g g.vertices g.vertices.length

theorem topoSortAux_zero {g : Graph} {rem : List Nat} :
    topoSortAux g rem 0 = [] := rfl

theorem topoSortAux_succ {g : Graph} {rem : List Nat} {fuel : Nat} :
    topoSortAux g rem (fuel + 1) =
      match g.findSource rem with
      | none => []
      | some s => s :: topoSortAux g (rem.erase s) fuel := rfl

/-- The core of Kahn correctness, by induction on the fuel. For any
remaining-vertex list `rem` of a DAG (well-formed in `g`), the
emitted list is a permutation of `rem` and every edge with both
endpoints in `rem` goes forward in it. No acyclicity is needed for
the forward direction of each emitted step — a vertex is only
emitted when nothing remaining points at it — but acyclicity (via
`Graph.exists_source` on the induced subgraph) is what guarantees a
source exists at every step, so the output is complete. -/
theorem topoSortAux_correct : ∀ (fuel : Nat) (g : Graph) (rem : List Nat),
    rem.Nodup → rem ⊆ g.vertices →
    (∀ e ∈ g.edges, e.1 ∈ g.vertices ∧ e.2 ∈ g.vertices) →
    Graph.IsDAG g → rem.length ≤ fuel →
    (topoSortAux g rem fuel).Perm rem ∧
    ∀ u v, (u, v) ∈ g.edges → u ∈ rem → v ∈ rem →
      Before u v (topoSortAux g rem fuel) := by
  intro fuel
  induction fuel with
  | zero =>
    intro g rem _ _ _ _ hlen
    have hrem : rem = [] := by
      cases rem with
      | nil => rfl
      | cons a as => simp at hlen
    subst hrem
    refine ⟨List.Perm.refl _, fun u v _ hu => ?_⟩
    exact absurd hu List.not_mem_nil
  | succ fuel ih =>
    intro g rem hnodup hsub hend hdag hlen
    by_cases hrem : rem = []
    · subst hrem
      have hfs : g.findSource [] = none := rfl
      rw [topoSortAux_succ, hfs]
      refine ⟨List.Perm.refl _, fun u v _ hu => ?_⟩
      exact absurd hu List.not_mem_nil
    · -- A source exists in the induced subgraph on `rem`, so
      -- `findSource` succeeds.
      have hsrc : ∃ s ∈ rem, ∀ u ∈ rem, (u, s) ∉ g.edges := by
        obtain ⟨s, hs, hsrc⟩ := Graph.exists_source (g := g.induced rem)
          (by rw [Graph.vertices_induced]; exact hrem)
          (by rw [Graph.vertices_induced]; exact hnodup)
          (fun e he => ⟨(Graph.mem_edges_induced.mp he).2.1,
            (Graph.mem_edges_induced.mp he).2.2⟩)
          (hdag.induced rem)
        rw [Graph.vertices_induced] at hs hsrc
        exact ⟨s, hs, fun u hu hcon =>
          hsrc u hu (Graph.mem_edges_induced.mpr ⟨hcon, hu, hs⟩)⟩
      cases hfs : g.findSource rem with
      | none =>
        have hsome := Graph.findSource_isSome hsrc
        rw [hfs] at hsome
        exact absurd hsome (by simp)
      | some s =>
        obtain ⟨hs_mem, hs_src⟩ := Graph.findSource_eq_some hfs
        obtain ⟨ihperm, ihbefore⟩ := ih g (rem.erase s) (hnodup.erase s)
          (List.Subset.trans List.erase_subset hsub) hend hdag (by
            rw [List.length_erase_of_mem hs_mem]; omega)
        rw [topoSortAux_succ, hfs]
        refine ⟨(List.Perm.cons s ihperm).trans
          (List.perm_cons_erase hs_mem).symm, fun u v hedge hu hv => ?_⟩
        by_cases hvs : v = s
        · subst hvs
          exact absurd hedge (hs_src u hu)
        · have hv' : v ∈ rem.erase s := (List.mem_erase_of_ne hvs).mpr hv
          by_cases hus : u = s
          · subst hus
            exact Before.head ((ihperm.mem_iff).mpr hv')
          · have hu' : u ∈ rem.erase s := (List.mem_erase_of_ne hus).mpr hu
            exact Before.cons (ihbefore u v hedge hu' hv')

/-- The draft's correctness statement, in its intended shape: for a
DAG, `topologicalSort` returns a permutation of the vertices in
which every edge goes forward. -/
theorem topologicalSort_correctness (g : Graph) (hnodup : g.vertices.Nodup)
    (hend : ∀ e ∈ g.edges, e.1 ∈ g.vertices ∧ e.2 ∈ g.vertices)
    (hdag : Graph.IsDAG g) :
    (topologicalSort g).Perm g.vertices ∧
    ∀ u v, (u, v) ∈ g.edges → Before u v (topologicalSort g) := by
  obtain ⟨hperm, hbefore⟩ := topoSortAux_correct g.vertices.length g g.vertices
    hnodup (fun _ hx => hx) hend hdag (by omega)
  refine ⟨hperm, fun u v hedge => ?_⟩
  exact hbefore u v hedge (hend _ hedge).1 (hend _ hedge).2

/-- The draft's length conjunct: the output has exactly as many
vertices as the graph. -/
theorem topologicalSort_length (g : Graph) (hnodup : g.vertices.Nodup)
    (hend : ∀ e ∈ g.edges, e.1 ∈ g.vertices ∧ e.2 ∈ g.vertices)
    (hdag : Graph.IsDAG g) :
    (topologicalSort g).length = g.vertices.length :=
  ((topologicalSort_correctness g hnodup hend hdag).1).length_eq

end AxiomCode
