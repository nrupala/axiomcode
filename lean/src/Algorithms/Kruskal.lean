import Spec
import Tactics
import Algorithms.Graph
import Algorithms.BellmanFord
import Algorithms.TopologicalSort


/-!
# Kruskal's algorithm — minimum spanning forests

The greedy algorithm: sort the edges by weight, scan them in
that order, and keep an edge exactly when its endpoints are
not already connected through the edges kept so far. The
output is a minimum-weight spanning forest
(`kruskal_correctness`); on a connected graph with at least
one vertex it is a spanning tree with one fewer edge than
vertices (`kruskal_tree_length`).

## Statement-honesty record

The draft this entry promotes (`kruskal_correctness {v.lean`)
was a shell that did not elaborate: it imported all of Mathlib
against this library's core-only discipline, declared a
fieldless `Edge` and `Graph`, gave `isSpanningTree` and
`kruskal` as constants with no bodies and no return types,
and closed its theorem with a placeholder proof. Its intended
claim was also false as stated: it carried no hypothesis on
the graph, but a disconnected graph has no spanning tree at
all — counterexample: vertices `[0, 1]`, edges `[]`. It also
omitted minimality, the algorithm's entire purpose. The
repair, in the least-repair form: the statement is made
against the platform's weighted graph `WGraph`, under the
platform well-formedness hypotheses (vertex list nodup, edge
endpoints among the vertices); the claim is the minimum
spanning FOREST — the true claim for arbitrary graphs — with
the tree form recovered under the added connectedness
hypothesis (`kruskal_tree_length`). The proposition shape —
the greedy output spans the graph and is minimum — is
preserved and strengthened: minimality, absent from the
draft, is proved (`kruskal_correctness`, fifth component).

## Design notes

Undirected reachability over a weighted edge list `F` is
`UReach V F`: reachability in the symmetrized projection.
The greedy pass tests connectivity with a decidable oracle —
flood-fill expansion (`iterReach`) run `V.length` times,
proved to agree with `UReach` (`connectedP_iff`); this
core's list library names its own duplicate-removal
differently and gives it a thin API, so the oracle carries
its own (`dedupN`). The forest invariant is the acyclicity
form this library's vocabulary supports: erasing any kept
edge disconnects its endpoints. Minimality is the counting
form of the cycle property: at every weight threshold the
output has at least as many light edges as any spanning
forest (`kruskal_threshold`), proved via component
representatives (`repsFrom` — the last member of each
component in vertex-list order) and the cardinality formula
`|F| + compCount V F = |V|` for forests
(`forest_cardinality`); a weight comparison by strong
induction (`weight_le_of_threshold`) finishes.
-/

namespace AxiomCode

/-- Undirected reachability in a weighted edge list: `UReach V F u v`
holds when `v` is reachable from `u` in the symmetrization of the
graph with vertex list `V` and edge list `F` (weights ignored). The
vertex list is carried for the statements' well-formedness
hypotheses; reachability itself depends only on the edges. -/
def UReach (V : List Nat) (F : List (Nat × Nat × Int)) (u v : Nat) : Prop :=
  Graph.Reach (⟨V, F⟩ : WGraph).toGraph.symmetrize u v

/-- Edge membership in the symmetrized projection, in triple form. -/
theorem mem_fgraph_edges {V : List Nat} {F : List (Nat × Nat × Int)}
    {a b : Nat} :
    (a, b) ∈ ((⟨V, F⟩ : WGraph).toGraph.symmetrize).edges ↔
    (∃ w, (a, b, w) ∈ F) ∨ (∃ w, (b, a, w) ∈ F) := by
  simp only [Graph.mem_edges_symmetrize, WGraph.mem_toGraph_edges]

theorem UReach.refl {V : List Nat} {F : List (Nat × Nat × Int)} (u : Nat) :
    UReach V F u u :=
  Graph.Reach.refl u

/-- Reachability in an undirected graph is symmetric. -/
theorem reach_symm {g : Graph} (hund : g.Undirected) {u v : Nat}
    (h : Graph.Reach g u v) : Graph.Reach g v u := by
  induction h with
  | refl => exact Graph.Reach.refl _
  | step he _ ih => exact ih.trans (Graph.Reach.of_edge (hund _ _ he))

theorem UReach.symm {V : List Nat} {F : List (Nat × Nat × Int)} {u v : Nat}
    (h : UReach V F u v) : UReach V F v u := by
  apply reach_symm _ h
  intro a b hab
  rw [mem_fgraph_edges] at hab ⊢
  rcases hab with ⟨w, hw⟩ | ⟨w, hw⟩
  · exact Or.inr ⟨w, hw⟩
  · exact Or.inl ⟨w, hw⟩

theorem UReach.trans {V : List Nat} {F : List (Nat × Nat × Int)} {u v w : Nat}
    (h₁ : UReach V F u v) (h₂ : UReach V F v w) : UReach V F u w :=
  Graph.Reach.trans h₁ h₂

/-- Enlarging the edge list cannot destroy undirected reachability. -/
theorem UReach.mono {V : List Nat} {F F' : List (Nat × Nat × Int)}
    (h : ∀ e ∈ F, e ∈ F') {u v : Nat} :
    UReach V F u v → UReach V F' u v := by
  apply Graph.Reach.mono
  intro e he
  obtain ⟨a, b⟩ := e
  rw [mem_fgraph_edges] at he ⊢
  rcases he with ⟨w, hw⟩ | ⟨w, hw⟩
  · exact Or.inl ⟨w, h _ hw⟩
  · exact Or.inr ⟨w, h _ hw⟩

/-- A listed edge joins its endpoints (in either direction). -/
theorem UReach.of_edge {V : List Nat} {F : List (Nat × Nat × Int)}
    {a b : Nat} {w : Int} (h : (a, b, w) ∈ F) : UReach V F a b :=
  Graph.Reach.of_edge (mem_fgraph_edges.mpr (Or.inl ⟨w, h⟩))

/-- In the empty edge list, reachability is equality. -/
theorem UReach.eq_of_empty {V : List Nat} {u v : Nat}
    (h : UReach V [] u v) : u = v := by
  induction h with
  | refl => rfl
  | step he _ _ =>
    have hcon := mem_fgraph_edges.mp he
    rcases hcon with ⟨w, hw⟩ | ⟨w, hw⟩ <;> simp at hw

/-- The one-edge decomposition, forward direction: a walk in the
enlarged graph decomposes into a walk of the original graph, using
the new edge at most once in one of its two directions. Proved by
induction on the reachability derivation — the disjunction is
closed under prepending any edge of the enlarged graph, using
symmetry of the base relation to collapse repeated uses of the
new edge. -/
theorem UReach.add_edge_fwd {V : List Nat} {F : List (Nat × Nat × Int)}
    {a b : Nat} (w : Int) {u v : Nat} (h : UReach V ((a, b, w) :: F) u v) :
    UReach V F u v ∨ (UReach V F u a ∧ UReach V F b v) ∨
      (UReach V F u b ∧ UReach V F a v) := by
  induction h with
  | refl => exact Or.inl (UReach.refl _)
  | step he htail ih =>
    rename_i x y z
    have he' := mem_fgraph_edges.mp he
    rcases he' with ⟨w', hw'⟩ | ⟨w', hw'⟩
    · -- the step edge is a listed triple, read forward
      rw [List.mem_cons] at hw'
      rcases hw' with htri | htri
      · -- the step is the new edge itself: x = a, y = b
        have hx : a = x := (congrArg Prod.fst htri).symm
        have hy : b = y := (congrArg (fun e => e.2.1) htri).symm
        subst hx; subst hy
        rcases ih with h1 | ⟨h1, h2⟩ | ⟨h1, h2⟩
        · exact Or.inr (Or.inl ⟨UReach.refl a, h1⟩)
        · exact Or.inl (h1.symm.trans h2)
        · exact Or.inl h2
      · -- the step is an old edge: prepend it to each disjunct
        have hstep : UReach V F x y := UReach.of_edge htri
        rcases ih with h1 | ⟨h1, h2⟩ | ⟨h1, h2⟩
        · exact Or.inl (hstep.trans h1)
        · exact Or.inr (Or.inl ⟨hstep.trans h1, h2⟩)
        · exact Or.inr (Or.inr ⟨hstep.trans h1, h2⟩)
    · -- the step edge is a listed triple, read backward
      rw [List.mem_cons] at hw'
      rcases hw' with htri | htri
      · -- the step is the new edge reversed: x = b, y = a
        have hx : b = x := (congrArg (fun e => e.2.1) htri).symm
        have hy : a = y := (congrArg Prod.fst htri).symm
        subst hx; subst hy
        rcases ih with h1 | ⟨h1, h2⟩ | ⟨h1, h2⟩
        · exact Or.inr (Or.inr ⟨UReach.refl b, h1⟩)
        · exact Or.inl h2
        · exact Or.inl (h1.symm.trans h2)
      · have hstep : UReach V F x y := (UReach.of_edge htri).symm
        rcases ih with h1 | ⟨h1, h2⟩ | ⟨h1, h2⟩
        · exact Or.inl (hstep.trans h1)
        · exact Or.inr (Or.inl ⟨hstep.trans h1, h2⟩)
        · exact Or.inr (Or.inr ⟨hstep.trans h1, h2⟩)

/-- The one-edge decomposition: adding an undirected edge `(a, b)`
to `F` creates exactly the walks that use the new edge at most
once, in one of its two directions. -/
theorem UReach.add_edge {V : List Nat} {F : List (Nat × Nat × Int)}
    {a b : Nat} (w : Int) {u v : Nat} :
    UReach V ((a, b, w) :: F) u v ↔
    UReach V F u v ∨ (UReach V F u a ∧ UReach V F b v) ∨
      (UReach V F u b ∧ UReach V F a v) := by
  constructor
  · exact UReach.add_edge_fwd w
  · rintro (h | ⟨h1, h2⟩ | ⟨h1, h2⟩)
    · exact UReach.mono (fun e he => List.mem_cons_of_mem _ he) h
    · exact (UReach.mono (fun e he => List.mem_cons_of_mem _ he) h1).trans
        ((UReach.of_edge (List.mem_cons_self)).trans
          (UReach.mono (fun e he => List.mem_cons_of_mem _ he) h2))
    · exact (UReach.mono (fun e he => List.mem_cons_of_mem _ he) h1).trans
        ((UReach.of_edge (List.mem_cons_self)).symm.trans
          (UReach.mono (fun e he => List.mem_cons_of_mem _ he) h2))


/-- Insert an edge into an edge list, just before the first edge
whose weight is at least its own. -/
def insertEdge (e : Nat × Nat × Int) :
    List (Nat × Nat × Int) → List (Nat × Nat × Int)
  | [] => [e]
  | f :: fs => if e.2.2 ≤ f.2.2 then e :: f :: fs else f :: insertEdge e fs

/-- Insertion sort of an edge list by weight, ascending. -/
def sortEdges : List (Nat × Nat × Int) → List (Nat × Nat × Int)
  | [] => []
  | e :: es => insertEdge e (sortEdges es)

theorem insertEdge_step (e f : Nat × Nat × Int) (fs : List (Nat × Nat × Int)) :
    insertEdge e (f :: fs) =
      if e.2.2 ≤ f.2.2 then e :: f :: fs else f :: insertEdge e fs := rfl

theorem insertEdge_perm (e : Nat × Nat × Int) :
    ∀ (l : List (Nat × Nat × Int)), (insertEdge e l).Perm (e :: l) := by
  intro l
  induction l with
  | nil => exact List.Perm.refl _
  | cons f fs ih =>
    by_cases h : e.2.2 ≤ f.2.2
    · rw [insertEdge_step, ite_eq_left h]
    · rw [insertEdge_step, ite_eq_right h]
      exact (List.Perm.cons f ih).trans (List.Perm.swap e f fs)

theorem sortEdges_perm : ∀ (l : List (Nat × Nat × Int)),
    (sortEdges l).Perm l := by
  intro l
  induction l with
  | nil => exact List.Perm.refl _
  | cons e es ih =>
    have hstep : sortEdges (e :: es) = insertEdge e (sortEdges es) := rfl
    rw [hstep]
    exact (insertEdge_perm e (sortEdges es)).trans (List.Perm.cons e ih)

theorem insertEdge_sorted (e : Nat × Nat × Int) :
    ∀ (l : List (Nat × Nat × Int)),
    l.Pairwise (fun a b => a.2.2 ≤ b.2.2) →
    (insertEdge e l).Pairwise (fun a b => a.2.2 ≤ b.2.2) := by
  intro l
  induction l with
  | nil =>
    intro _
    exact List.Pairwise.cons (fun y hy => by simp at hy) List.Pairwise.nil
  | cons f fs ih =>
    intro h
    rw [List.pairwise_cons] at h
    obtain ⟨hf, hfs⟩ := h
    by_cases hle : e.2.2 ≤ f.2.2
    · rw [insertEdge_step, ite_eq_left hle, List.pairwise_cons]
      refine ⟨fun y hy => ?_, List.pairwise_cons.mpr ⟨hf, hfs⟩⟩
      rw [List.mem_cons] at hy
      rcases hy with rfl | hy
      · exact hle
      · exact Int.le_trans hle (hf y hy)
    · rw [insertEdge_step, ite_eq_right hle, List.pairwise_cons]
      have hfe : f.2.2 ≤ e.2.2 := by omega
      refine ⟨fun y hy => ?_, ih hfs⟩
      have hym : y ∈ e :: fs := (insertEdge_perm e fs).mem_iff.mp hy
      rw [List.mem_cons] at hym
      rcases hym with rfl | hym
      · exact hfe
      · exact hf y hym

theorem sortEdges_sorted : ∀ (l : List (Nat × Nat × Int)),
    (sortEdges l).Pairwise (fun a b => a.2.2 ≤ b.2.2) := by
  intro l
  induction l with
  | nil => exact List.Pairwise.nil
  | cons e es ih =>
    have hstep : sortEdges (e :: es) = insertEdge e (sortEdges es) := rfl
    rw [hstep]
    exact insertEdge_sorted e (sortEdges es) ih


/-- Deduplicate a vertex list, keeping first occurrences. (This
core's list library names its own duplicate-removal differently
and gives it a thin API, so the library carries its own.) -/
def dedupN : List Nat → List Nat
  | [] => []
  | x :: xs => x :: (dedupN xs).filter (fun y => y ≠ x)

theorem mem_dedupN {y : Nat} : ∀ {l : List Nat}, y ∈ dedupN l ↔ y ∈ l := by
  intro l
  induction l with
  | nil => exact Iff.rfl
  | cons x xs ih =>
    have hstep : dedupN (x :: xs) = x :: (dedupN xs).filter (fun y => y ≠ x) := rfl
    rw [hstep]
    constructor
    · intro hy
      rw [List.mem_cons] at hy
      rcases hy with rfl | hy
      · exact List.mem_cons_self
      · rw [List.mem_filter] at hy
        exact List.mem_cons_of_mem _ (ih.mp hy.1)
    · intro hy
      rw [List.mem_cons] at hy
      rw [List.mem_cons]
      rcases hy with rfl | hy
      · exact Or.inl rfl
      · by_cases h : y = x
        · exact Or.inl h
        · exact Or.inr (List.mem_filter.mpr ⟨ih.mpr hy, decide_eq_true h⟩)

theorem dedupN_nodup : ∀ (l : List Nat), (dedupN l).Nodup := by
  intro l
  induction l with
  | nil => exact List.nodup_nil
  | cons x xs ih =>
    have hstep : dedupN (x :: xs) = x :: (dedupN xs).filter (fun y => y ≠ x) := rfl
    rw [hstep]
    refine List.Pairwise.cons ?_ (ih.filter _)
    intro y hy
    rw [List.mem_filter] at hy
    have hyx : y ≠ x := of_decide_eq_true hy.2
    exact fun h => hyx h.symm

theorem filter_ne_self {x : Nat} : ∀ {l : List Nat},
    (∀ y ∈ l, y ≠ x) → l.filter (fun y => y ≠ x) = l := by
  intro l
  induction l with
  | nil => intro _; rfl
  | cons z zs ih =>
    intro h
    have hz : z ≠ x := h z (List.mem_cons_self)
    rw [List.filter_cons, ite_eq_left (decide_eq_true hz),
      ih (fun y hy => h y (List.mem_cons_of_mem _ hy))]

theorem dedupN_eq_of_nodup : ∀ {l : List Nat}, l.Nodup → dedupN l = l := by
  intro l
  induction l with
  | nil => intro _; rfl
  | cons x xs ih =>
    intro h
    rw [List.nodup_cons] at h
    have hstep : dedupN (x :: xs) = x :: (dedupN xs).filter (fun y => y ≠ x) := rfl
    have hall : ∀ y ∈ dedupN xs, y ≠ x := by
      intro y hy hxy
      apply h.1
      rw [← hxy]
      exact mem_dedupN.mp hy
    rw [hstep, filter_ne_self hall, ih h.2]

/-- One expansion step's raw output: the set `S` together with
every vertex adjacent to a member of `S` along the pair list
`es`, in either direction. -/
def nbrs (S : List Nat) : List (Nat × Nat) → List Nat
  | [] => S
  | (x, y) :: es =>
    if x ∈ S then y :: nbrs S es
    else if y ∈ S then x :: nbrs S es
    else nbrs S es

theorem nbrs_cons (S : List Nat) (x y : Nat) (es : List (Nat × Nat)) :
    nbrs S ((x, y) :: es) =
      if x ∈ S then y :: nbrs S es
      else if y ∈ S then x :: nbrs S es
      else nbrs S es := rfl

theorem subset_nbrs {S : List Nat} : ∀ {es : List (Nat × Nat)} {y : Nat},
    y ∈ S → y ∈ nbrs S es := by
  intro es
  induction es with
  | nil => intro y hy; exact hy
  | cons e es ih =>
    obtain ⟨x, z⟩ := e
    intro y hy
    rw [nbrs_cons]
    by_cases hx : x ∈ S
    · rw [ite_eq_left hx]; exact List.mem_cons_of_mem _ (ih hy)
    · rw [ite_eq_right hx]
      by_cases hz : z ∈ S
      · rw [ite_eq_left hz]; exact List.mem_cons_of_mem _ (ih hy)
      · rw [ite_eq_right hz]; exact ih hy

theorem mem_nbrs {S : List Nat} : ∀ {es : List (Nat × Nat)} {y : Nat},
    y ∈ nbrs S es ↔ y ∈ S ∨ ∃ x ∈ S, (x, y) ∈ es ∨ (y, x) ∈ es := by
  intro es
  induction es with
  | nil =>
    intro y
    constructor
    · intro hy; exact Or.inl hy
    · rintro (hy | ⟨x, -, h⟩)
      · exact hy
      · simp at h
  | cons e es ih =>
    obtain ⟨x, z⟩ := e
    intro y
    rw [nbrs_cons]
    by_cases hx : x ∈ S
    · rw [ite_eq_left hx]
      constructor
      · intro hy
        rw [List.mem_cons] at hy
        rcases hy with rfl | hy
        · exact Or.inr ⟨x, hx, Or.inl (List.mem_cons_self)⟩
        · rw [ih] at hy
          rcases hy with hy | ⟨x', hx', hadj⟩
          · exact Or.inl hy
          · exact Or.inr ⟨x', hx', hadj.imp
              (fun h => List.mem_cons_of_mem _ h)
              (fun h => List.mem_cons_of_mem _ h)⟩
      · rintro (hy | ⟨x', hx', hadj⟩)
        · exact List.mem_cons_of_mem _ (ih.mpr (Or.inl hy))
        · rcases hadj with h | h
          · rw [List.mem_cons] at h
            rcases h with h | h
            · obtain ⟨rfl, rfl⟩ := Prod.ext_iff.mp h
              exact List.mem_cons_self
            · exact List.mem_cons_of_mem _ (ih.mpr (Or.inr ⟨x', hx', Or.inl h⟩))
          · rw [List.mem_cons] at h
            rcases h with h | h
            · obtain ⟨rfl, -⟩ := Prod.ext_iff.mp h
              exact List.mem_cons_of_mem _ (ih.mpr (Or.inl hx))
            · exact List.mem_cons_of_mem _ (ih.mpr (Or.inr ⟨x', hx', Or.inr h⟩))
    · rw [ite_eq_right hx]
      by_cases hz : z ∈ S
      · rw [ite_eq_left hz]
        constructor
        · intro hy
          rw [List.mem_cons] at hy
          rcases hy with rfl | hy
          · exact Or.inr ⟨z, hz, Or.inr (List.mem_cons_self)⟩
          · rw [ih] at hy
            rcases hy with hy | ⟨x', hx', hadj⟩
            · exact Or.inl hy
            · exact Or.inr ⟨x', hx', hadj.imp
                (fun h => List.mem_cons_of_mem _ h)
                (fun h => List.mem_cons_of_mem _ h)⟩
        · rintro (hy | ⟨x', hx', hadj⟩)
          · exact List.mem_cons_of_mem _ (ih.mpr (Or.inl hy))
          · rcases hadj with h | h
            · rw [List.mem_cons] at h
              rcases h with h | h
              · obtain ⟨-, rfl⟩ := Prod.ext_iff.mp h
                exact List.mem_cons_of_mem _ (ih.mpr (Or.inl hz))
              · exact List.mem_cons_of_mem _ (ih.mpr (Or.inr ⟨x', hx', Or.inl h⟩))
            · rw [List.mem_cons] at h
              rcases h with h | h
              · obtain ⟨rfl, -⟩ := Prod.ext_iff.mp h
                exact List.mem_cons_self
              · exact List.mem_cons_of_mem _ (ih.mpr (Or.inr ⟨x', hx', Or.inr h⟩))
      · rw [ite_eq_right hz]
        constructor
        · intro hy
          rw [ih] at hy
          rcases hy with hy | ⟨x', hx', hadj⟩
          · exact Or.inl hy
          · exact Or.inr ⟨x', hx', hadj.imp
              (fun h => List.mem_cons_of_mem _ h)
              (fun h => List.mem_cons_of_mem _ h)⟩
        · rintro (hy | ⟨x', hx', hadj⟩)
          · exact ih.mpr (Or.inl hy)
          · apply ih.mpr (Or.inr ⟨x', hx', ?_⟩)
            rcases hadj with h | h
            · rw [List.mem_cons] at h
              rcases h with h | h
              · exfalso
                obtain ⟨h1, -⟩ := Prod.ext_iff.mp h
                have h1' : x' = x := h1
                rw [h1'] at hx'
                exact hx hx'
              · exact Or.inl h
            · rw [List.mem_cons] at h
              rcases h with h | h
              · exfalso
                obtain ⟨-, h2⟩ := Prod.ext_iff.mp h
                have h2' : x' = z := h2
                rw [h2'] at hx'
                exact hz hx'
              · exact Or.inr h

/-- One full expansion step: the deduplicated neighbours. -/
def expand (es : List (Nat × Nat)) (S : List Nat) : List Nat :=
  dedupN (nbrs S es)

theorem mem_expand {es : List (Nat × Nat)} {S : List Nat} {y : Nat} :
    y ∈ expand es S ↔ y ∈ nbrs S es := mem_dedupN

/-- The `k`-fold expansion of `S` along `es`: everything within
walk distance `k` of `S`. -/
def iterReach (es : List (Nat × Nat)) (S : List Nat) : Nat → List Nat
  | 0 => dedupN S
  | k + 1 => expand es (iterReach es S k)

theorem iterReach_zero (es : List (Nat × Nat)) (S : List Nat) :
    iterReach es S 0 = dedupN S := rfl

theorem iterReach_succ (es : List (Nat × Nat)) (S : List Nat) (k : Nat) :
    iterReach es S (k + 1) = expand es (iterReach es S k) := rfl

theorem iterReach_nodup (es : List (Nat × Nat)) (S : List Nat) :
    ∀ k, (iterReach es S k).Nodup := by
  intro k
  induction k with
  | zero => rw [iterReach_zero]; exact dedupN_nodup _
  | succ k _ => rw [iterReach_succ]; exact dedupN_nodup _

theorem iterReach_succ_of_mem {es : List (Nat × Nat)} {S : List Nat}
    {y : Nat} {k : Nat} (hy : y ∈ iterReach es S k) :
    y ∈ iterReach es S (k + 1) := by
  rw [iterReach_succ, mem_expand, mem_nbrs]
  exact Or.inl hy

theorem mem_iterReach_of_mem {es : List (Nat × Nat)} {S : List Nat}
    {y : Nat} (hy : y ∈ S) : ∀ {k}, y ∈ iterReach es S k := by
  intro k
  induction k with
  | zero => rw [iterReach_zero]; exact mem_dedupN.mpr hy
  | succ k ih => exact iterReach_succ_of_mem ih

theorem iterReach_mono_le {es : List (Nat × Nat)} {S : List Nat} {y : Nat} :
    ∀ {k k' : Nat}, k ≤ k' → y ∈ iterReach es S k → y ∈ iterReach es S k' := by
  intro k k' h
  induction h with
  | refl => intro hy; exact hy
  | @step m _ ih => intro hy; exact iterReach_succ_of_mem (ih hy)


theorem iterReach_sound {V : List Nat} {es : List (Nat × Nat)} :
    ∀ {k : Nat} {S : List Nat} {y : Nat}, y ∈ iterReach es S k →
    ∃ x ∈ S, Graph.Reach (⟨V, es⟩ : Graph).symmetrize x y := by
  intro k
  induction k with
  | zero =>
    intro S y hy
    rw [iterReach_zero] at hy
    exact ⟨y, mem_dedupN.mp hy, Graph.Reach.refl y⟩
  | succ k ih =>
    intro S y hy
    rw [iterReach_succ, mem_expand, mem_nbrs] at hy
    rcases hy with hy | ⟨x, hx, hadj⟩
    · exact ih hy
    · obtain ⟨x₀, hx₀, hreach⟩ := ih hx
      have hedge : (x, y) ∈ (⟨V, es⟩ : Graph).symmetrize.edges :=
        Graph.mem_edges_symmetrize.mpr hadj
      exact ⟨x₀, hx₀, hreach.trans (Graph.Reach.step hedge (Graph.Reach.refl y))⟩

theorem iterReach_subset {V : List Nat} {es : List (Nat × Nat)}
    (hends : ∀ e ∈ es, e.1 ∈ V ∧ e.2 ∈ V) {S : List Nat}
    (hS : ∀ y ∈ S, y ∈ V) : ∀ {k : Nat} {y : Nat},
    y ∈ iterReach es S k → y ∈ V := by
  intro k
  induction k with
  | zero =>
    intro y hy
    rw [iterReach_zero] at hy
    exact hS y (mem_dedupN.mp hy)
  | succ k ih =>
    intro y hy
    rw [iterReach_succ, mem_expand, mem_nbrs] at hy
    rcases hy with hy | ⟨x, hx, hadj⟩
    · exact ih hy
    · rcases hadj with h | h
      · exact (hends (x, y) h).2
      · exact (hends (y, x) h).1

/-- Once an iterate is closed under expansion, every later
iterate stays inside it. -/
theorem iterReach_closed_mono {es : List (Nat × Nat)} {S : List Nat} {k : Nat}
    (hclosed : ∀ y ∈ nbrs (iterReach es S k) es, y ∈ iterReach es S k) :
    ∀ {d : Nat} {y : Nat}, y ∈ iterReach es S (k + d) → y ∈ iterReach es S k := by
  intro d
  induction d with
  | zero => intro y hy; exact hy
  | succ d ih =>
    intro y hy
    have hy' : y ∈ iterReach es S ((k + d) + 1) := hy
    rw [iterReach_succ, mem_expand, mem_nbrs] at hy'
    rcases hy' with hy' | ⟨x, hx, hadj⟩
    · exact ih hy'
    · exact hclosed y (mem_nbrs.mpr (Or.inr ⟨x, ih hx, hadj⟩))

/-- While no iterate up to `k` is closed, the iterates strictly
grow: the `k`-th has at least `k + |S|` elements. -/
theorem iterReach_growth {es : List (Nat × Nat)} {S : List Nat} (hS : S.Nodup) :
    ∀ {k : Nat}, (∀ j < k, ¬ ∀ y ∈ nbrs (iterReach es S j) es,
        y ∈ iterReach es S j) →
    k + S.length ≤ (iterReach es S k).length := by
  intro k
  induction k with
  | zero =>
    intro _
    rw [iterReach_zero, dedupN_eq_of_nodup hS, Nat.zero_add]
    exact Nat.le_refl _
  | succ k ih =>
    intro hnc
    have hnc_k : ¬ ∀ y ∈ nbrs (iterReach es S k) es, y ∈ iterReach es S k :=
      hnc k (Nat.lt_succ_self k)
    have hex : ∃ y, y ∈ nbrs (iterReach es S k) es ∧ y ∉ iterReach es S k := by
      apply Classical.byContradiction
      intro hcon
      apply hnc_k
      intro y hy
      apply Classical.byContradiction
      intro hyout
      exact hcon ⟨y, hy, hyout⟩
    obtain ⟨y, hy1, hy2⟩ := hex
    have ih' := ih (fun j hj => hnc j (Nat.lt_succ_of_lt hj))
    have hsub : ∀ z ∈ y :: iterReach es S k, z ∈ iterReach es S (k + 1) := by
      intro z hz
      rw [List.mem_cons] at hz
      rcases hz with rfl | hz
      · rw [iterReach_succ, mem_expand]; exact hy1
      · exact iterReach_succ_of_mem hz
    have hle := nodup_length_le (y :: iterReach es S k) (iterReach es S (k + 1))
      (List.nodup_cons.mpr ⟨hy2, iterReach_nodup es S k⟩)
      (iterReach_nodup es S (k + 1)) hsub
    rw [List.length_cons] at hle
    omega

/-- Some iterate at or before `V.length` is closed under
expansion: the stabilization point of the reachability flood. -/
theorem iterReach_stab {V : List Nat} (hV : V.Nodup)
    {es : List (Nat × Nat)} (hends : ∀ e ∈ es, e.1 ∈ V ∧ e.2 ∈ V)
    {u : Nat} (hu : u ∈ V) :
    ∃ k ≤ V.length, ∀ y ∈ nbrs (iterReach es [u] k) es, y ∈ iterReach es [u] k := by
  have h1 : ∀ y ∈ iterReach es [u] 0, y ∈ V := fun y hy =>
    iterReach_subset hends (S := [u]) (fun z hz => by
      rw [List.mem_singleton] at hz; subst hz; exact hu) hy
  have key : ∀ N : Nat, ∀ k : Nat, V.length - k ≤ N →
      (∀ j < k, ¬ ∀ y ∈ nbrs (iterReach es [u] j) es, y ∈ iterReach es [u] j) →
      ∃ k' ≤ V.length, ∀ y ∈ nbrs (iterReach es [u] k') es,
        y ∈ iterReach es [u] k' := by
    intro N
    induction N with
    | zero =>
      intro k hk hnc
      have hg := iterReach_growth (List.nodup_cons.mpr ⟨by simp, List.nodup_nil⟩) hnc
      have hsub : ∀ y ∈ iterReach es [u] k, y ∈ V := fun y hy =>
        iterReach_subset hends (S := [u]) (fun z hz => by
          rw [List.mem_singleton] at hz; subst hz; exact hu) hy
      have hle := nodup_length_le (iterReach es [u] k) V
        (iterReach_nodup _ _ _) hV hsub
      simp only [List.length_singleton] at hg
      omega
    | succ N ih =>
      intro k hk hnc
      by_cases hclosed : ∀ y ∈ nbrs (iterReach es [u] k) es,
          y ∈ iterReach es [u] k
      · refine ⟨k, ?_, hclosed⟩
        have hg := iterReach_growth (List.nodup_cons.mpr ⟨by simp, List.nodup_nil⟩) hnc
        have hsub : ∀ y ∈ iterReach es [u] k, y ∈ V := fun y hy =>
          iterReach_subset hends (S := [u]) (fun z hz => by
            rw [List.mem_singleton] at hz; subst hz; exact hu) hy
        have hle := nodup_length_le (iterReach es [u] k) V
          (iterReach_nodup _ _ _) hV hsub
        simp only [List.length_singleton] at hg
        omega
      · have hg := iterReach_growth (List.nodup_cons.mpr ⟨by simp, List.nodup_nil⟩) hnc
        have hsub : ∀ y ∈ iterReach es [u] k, y ∈ V := fun y hy =>
          iterReach_subset hends (S := [u]) (fun z hz => by
            rw [List.mem_singleton] at hz; subst hz; exact hu) hy
        have hle := nodup_length_le (iterReach es [u] k) V
          (iterReach_nodup _ _ _) hV hsub
        simp only [List.length_singleton] at hg
        apply ih (k + 1) (by omega)
        intro j hj
        rcases Nat.lt_succ_iff_lt_or_eq.mp hj with hj | rfl
        · exact hnc j hj
        · exact hclosed
  exact key V.length 0 (Nat.sub_le _ _) (fun j hj => (Nat.not_lt_zero j hj).elim)

/-- Against a closed iterate, reachability stays inside: the
flood has found the whole connected component. -/
theorem iterReach_complete {V : List Nat} {es : List (Nat × Nat)} {S : List Nat}
    {k : Nat}
    (hclosed : ∀ y ∈ nbrs (iterReach es S k) es, y ∈ iterReach es S k)
    {x y : Nat} (h : Graph.Reach (⟨V, es⟩ : Graph).symmetrize x y)
    (hx : x ∈ iterReach es S k) : y ∈ iterReach es S k := by
  induction h with
  | refl => exact hx
  | step he htail ih =>
    rename_i p q r
    exact ih (hclosed q (mem_nbrs.mpr
      (Or.inr ⟨p, hx, Graph.mem_edges_symmetrize.mp he⟩)))

/-- The decidable reachability test over a pair list: expand the
singleton `{u}` exactly `V.length` times and test membership. -/
def connectedP (es : List (Nat × Nat)) (V : List Nat) (u v : Nat) : Bool :=
  decide (v ∈ iterReach es [u] V.length)

/-- The decidable test agrees with undirected reachability. -/
theorem connectedP_iff {V : List Nat} (hV : V.Nodup) {es : List (Nat × Nat)}
    (hends : ∀ e ∈ es, e.1 ∈ V ∧ e.2 ∈ V) {u v : Nat} (hu : u ∈ V) :
    connectedP es V u v = true ↔ Graph.Reach (⟨V, es⟩ : Graph).symmetrize u v := by
  constructor
  · intro h
    have hv : v ∈ iterReach es [u] V.length := of_decide_eq_true h
    obtain ⟨x, hx, hreach⟩ := iterReach_sound (V := V) hv
    rw [List.mem_singleton] at hx
    subst hx
    exact hreach
  · intro h
    obtain ⟨k, hk, hclosed⟩ := iterReach_stab hV hends hu
    have hv : v ∈ iterReach es [u] k :=
      iterReach_complete hclosed h (mem_iterReach_of_mem (List.mem_cons_self))
    have hv2 : v ∈ iterReach es [u] V.length := iterReach_mono_le hk hv
    exact decide_eq_true hv2


/-- The oracle instantiated at a weighted edge list: the
decidable test on the projected pair list agrees with
undirected reachability `UReach`. -/
theorem ureach_iff_connectedP {V : List Nat} (hV : V.Nodup)
    {F : List (Nat × Nat × Int)}
    (hends : ∀ e ∈ F, e.1 ∈ V ∧ e.2.1 ∈ V) {u v : Nat} (hu : u ∈ V) :
    connectedP (F.map (fun e => (e.1, e.2.1))) V u v = true ↔ UReach V F u v :=
  connectedP_iff hV (es := F.map (fun e => (e.1, e.2.1)))
    (fun e he => by
      rw [List.mem_map] at he
      obtain ⟨f, hf, rfl⟩ := he
      exact hends f hf) hu

/-- The greedy pass: scan the edges in the order given (the
caller passes them weight-sorted), keeping an edge exactly when
its endpoints are not already connected through the edges kept
so far. The accumulator holds the kept edges. -/
def kruskalAux (V : List Nat) :
    List (Nat × Nat × Int) → List (Nat × Nat × Int) → List (Nat × Nat × Int)
  | [], F => F
  | e :: es, F =>
    if connectedP (F.map (fun t => (t.1, t.2.1))) V e.1 e.2.1
    then kruskalAux V es F
    else kruskalAux V es (e :: F)

/-- **Kruskal's algorithm**: sort the edges by weight and run
the greedy pass. -/
def kruskal (wg : WGraph) : List (Nat × Nat × Int) :=
  kruskalAux wg.vertices (sortEdges wg.edges) []

/-- The greedy invariant, proved by induction on the edge list.
Under platform well-formedness of the ambient edge set `E`
(endpoints among the vertices), a weight-sorted remaining list
`L`, and an accumulator `F` that is already a forest of
`E`-edges whose weights all precede those of `L`, the output
`kruskalAux V L F` is a forest of `E`-edges extending `F`,
and every edge of `F ++ L` has its endpoints joined in the
output by a walk using only output edges of at most its own
weight (the weight-bounded spanning property — the form of the
cycle property the minimality argument consumes). -/
theorem kruskalAux_spec (V : List Nat) (hV : V.Nodup) (E : List (Nat × Nat × Int))
    (hE : ∀ e ∈ E, e.1 ∈ V ∧ e.2.1 ∈ V) :
    ∀ (L F : List (Nat × Nat × Int)),
    L.Pairwise (fun a b => a.2.2 ≤ b.2.2) →
    (∀ e ∈ L, e ∈ E) →
    (∀ e ∈ F, e ∈ E) →
    (∀ e ∈ F, e.1 ∈ V ∧ e.2.1 ∈ V) →
    F.Nodup →
    (∀ e ∈ F, ¬ UReach V (F.erase e) e.1 e.2.1) →
    (∀ f ∈ F, ∀ t ∈ L, f.2.2 ≤ t.2.2) →
    (∀ e ∈ kruskalAux V L F, e ∈ E) ∧ (kruskalAux V L F).Nodup ∧
    (∀ e ∈ F, e ∈ kruskalAux V L F) ∧
    (∀ e ∈ kruskalAux V L F, ¬ UReach V ((kruskalAux V L F).erase e) e.1 e.2.1) ∧
    (∀ e ∈ F ++ L, UReach V ((kruskalAux V L F).filter (fun f => f.2.2 ≤ e.2.2))
      e.1 e.2.1) := by
  intro L
  induction L with
  | nil =>
    intro F _ _ hFE _ hFnd hFforest _
    refine ⟨hFE, hFnd, fun e he => he, hFforest, ?_⟩
    intro e he
    simp only [List.append_nil] at he
    exact UReach.of_edge (List.mem_filter.mpr ⟨he, decide_eq_true (Int.le_refl _)⟩)
  | cons t es ih =>
    obtain ⟨a, b, w⟩ := t
    intro F hsorted hLE hFE hFends hFnd hFforest hFw
    rw [List.pairwise_cons] at hsorted
    obtain ⟨htes, hessorted⟩ := hsorted
    have htE : (a, b, w) ∈ E := hLE (a, b, w) (List.mem_cons_self)
    have htends : a ∈ V ∧ b ∈ V := hE (a, b, w) htE
    have hstep : kruskalAux V ((a, b, w) :: es) F =
        if connectedP (F.map (fun e => (e.1, e.2.1))) V a b
        then kruskalAux V es F else kruskalAux V es ((a, b, w) :: F) := rfl
    have hForacle : connectedP (F.map (fun e => (e.1, e.2.1))) V a b = true ↔
        UReach V F a b :=
      ureach_iff_connectedP hV (fun f hf => hFends f hf) htends.1
    by_cases htest : connectedP (F.map (fun e => (e.1, e.2.1))) V a b = true
    · -- REJECT: the endpoints are already joined in `F`; the edge
      -- is skipped, and its endpoints stay joined through `F`,
      -- whose edges all persist with weight at most `w`.
      rw [hstep, ite_eq_left htest]
      have htconn : UReach V F a b := hForacle.mp htest
      obtain ⟨ih1, ih2, ih3, ih4, ih5⟩ := ih F hessorted
        (fun e he => hLE e (List.mem_cons_of_mem _ he)) hFE hFends hFnd hFforest
        (fun f hf t' ht' => hFw f hf t' (List.mem_cons_of_mem _ ht'))
      refine ⟨ih1, ih2, ih3, ih4, ?_⟩
      intro e he
      rw [List.mem_append, List.mem_cons] at he
      rcases he with he | rfl | he
      · exact ih5 e (List.mem_append_left _ he)
      · exact UReach.mono (fun f hf => List.mem_filter.mpr
          ⟨ih3 f hf, decide_eq_true (hFw f hf (a, b, w) (List.mem_cons_self))⟩) htconn
      · exact ih5 e (List.mem_append_right _ he)
    · -- ACCEPT: the edge joins two different components of `F`,
      -- so it extends the forest.
      have hfalse : connectedP (F.map (fun e => (e.1, e.2.1))) V a b = false :=
        Bool.eq_false_iff.mpr htest
      rw [hstep, ite_eq_right htest]
      have htnconn : ¬ UReach V F a b := fun hcon => htest (hForacle.mpr hcon)
      have htF : (a, b, w) ∉ F := fun hm => htnconn (UReach.of_edge hm)
      have hFforest' : ∀ e ∈ (a, b, w) :: F,
          ¬ UReach V (((a, b, w) :: F).erase e) e.1 e.2.1 := by
        intro e he
        rw [List.mem_cons] at he
        rcases he with rfl | he
        · have herase : ((a, b, w) :: F).erase (a, b, w) = F := by simp [List.erase]
          rw [herase]
          exact htnconn
        · have hne : (a, b, w) ≠ e := by
            intro h
            apply htF
            rw [h]
            exact he
          have hba : ((a, b, w) == e) = false := by
            rw [Bool.eq_false_iff]; intro hb; exact hne (beq_iff_eq.mp hb)
          have herase : ((a, b, w) :: F).erase e = (a, b, w) :: (F.erase e) := by
            simp [List.erase, hba]
          rw [herase]
          intro hcon
          rw [UReach.add_edge] at hcon
          rcases hcon with h1 | ⟨h1, h2⟩ | ⟨h1, h2⟩
          · exact hFforest e he h1
          · exact htnconn (((UReach.mono
                (fun f hf => List.mem_of_mem_erase hf) h1).symm.trans
              (UReach.of_edge he)).trans
              (UReach.mono (fun f hf => List.mem_of_mem_erase hf) h2).symm)
          · exact htnconn (((UReach.mono
                (fun f hf => List.mem_of_mem_erase hf) h2).trans
              (UReach.of_edge he).symm).trans
              (UReach.mono (fun f hf => List.mem_of_mem_erase hf) h1))
      obtain ⟨ih1, ih2, ih3, ih4, ih5⟩ := ih ((a, b, w) :: F) hessorted
        (fun e he => hLE e (List.mem_cons_of_mem _ he))
        (fun e he => by
          rw [List.mem_cons] at he
          rcases he with rfl | he
          · exact htE
          · exact hFE e he)
        (fun e he => by
          rw [List.mem_cons] at he
          rcases he with rfl | he
          · exact htends
          · exact hFends e he)
        (List.nodup_cons.mpr ⟨htF, hFnd⟩) hFforest'
        (fun f hf t' ht' => by
          rw [List.mem_cons] at hf
          rcases hf with rfl | hf
          · exact htes t' ht'
          · exact hFw f hf t' (List.mem_cons_of_mem _ ht'))
      refine ⟨ih1, ih2, fun e he => ih3 e (List.mem_cons_of_mem _ he), ih4,
        fun e he => ih5 e (by
          rw [List.mem_append, List.mem_cons] at he
          rw [List.mem_append, List.mem_cons]
          rcases he with he | rfl | he
          · exact Or.inl (Or.inr he)
          · exact Or.inl (Or.inl rfl)
          · exact Or.inr he)⟩

/-- The output of Kruskal's algorithm is a spanning forest of
the graph: a nodup, acyclic (in the undirected-reachability
sense) set of the graph's own edges joining the endpoints of
every edge of the graph. -/
theorem kruskal_forest (wg : WGraph) (hV : wg.vertices.Nodup)
    (hE : ∀ e ∈ wg.edges, e.1 ∈ wg.vertices ∧ e.2.1 ∈ wg.vertices) :
    (∀ e ∈ kruskal wg, e ∈ wg.edges) ∧ (kruskal wg).Nodup ∧
    (∀ e ∈ kruskal wg, ¬ UReach wg.vertices ((kruskal wg).erase e) e.1 e.2.1) ∧
    (∀ e ∈ wg.edges, UReach wg.vertices (kruskal wg) e.1 e.2.1) := by
  have hspec := kruskalAux_spec wg.vertices hV wg.edges hE (sortEdges wg.edges) []
    (sortEdges_sorted wg.edges)
    (fun e he => (sortEdges_perm wg.edges).mem_iff.mp he)
    (fun e he => by simp at he) (fun e he => by simp at he) (List.nodup_nil)
    (fun e he => by simp at he) (fun f hf => by simp at hf)
  obtain ⟨h1, h2, -, h4, h5⟩ := hspec
  refine ⟨h1, h2, h4, ?_⟩
  intro e he
  have hmem : e ∈ [] ++ sortEdges wg.edges :=
    List.mem_append_right _ ((sortEdges_perm wg.edges).mem_iff.mpr he)
  exact UReach.mono (fun f hf => (List.mem_filter.mp hf).1) (h5 e hmem)


/-- Both endpoints of a `Before` fact occur in the list. -/
theorem before_mem {a b : Nat} : ∀ {l : List Nat}, Before a b l → a ∈ l ∧ b ∈ l := by
  intro l h
  induction h with
  | head hv => exact ⟨List.mem_cons_self, List.mem_cons_of_mem _ hv⟩
  | cons _ ih => exact ⟨List.mem_cons_of_mem _ ih.1, List.mem_cons_of_mem _ ih.2⟩

/-- At the head of the list, `Before` is membership in the tail. -/
theorem before_head {x u : Nat} {xs : List Nat} (hx : x ∉ xs) :
    Before x u (x :: xs) ↔ u ∈ xs := by
  constructor
  · intro h
    cases h with
    | head hv => exact hv
    | cons h' => exact absurd (before_mem h').1 hx
  · intro hu
    exact Before.head hu

/-- Nothing in the tail is before the head. -/
theorem before_target_head {v x : Nat} {xs : List Nat} (hx : x ∉ xs) :
    ¬ Before v x (x :: xs) := by
  intro h
  cases h with
  | head hm => exact hx hm
  | cons h' => exact hx (before_mem h').2

/-- `Before` inside a cons whose head is neither endpoint is
`Before` in the tail. -/
theorem before_cons_tail {x v u : Nat} {xs : List Nat} (hv : v ≠ x) (hu : u ≠ x) :
    Before v u (x :: xs) ↔ Before v u xs := by
  constructor
  · intro h
    cases h with
    | head _ => exact (hv rfl).elim
    | cons h' => exact h'
  · intro h
    exact Before.cons h

/-- Trichotomy: of two distinct members of a list, one is
before the other. -/
theorem before_trichotomy {x y : Nat} : ∀ {l : List Nat}, l.Nodup →
    x ∈ l → y ∈ l → x ≠ y → Before x y l ∨ Before y x l := by
  intro l
  induction l with
  | nil => intro _ hx _ _; simp at hx
  | cons z vs ih =>
    intro hnd hx hy hne
    rw [List.nodup_cons] at hnd
    rw [List.mem_cons] at hx hy
    rcases hx with rfl | hx
    · rcases hy with hy | hy
      · exact (hne hy.symm).elim
      · exact Or.inl (Before.head hy)
    · rcases hy with rfl | hy
      · exact Or.inr (Before.head hx)
      · rcases ih hnd.2 hx hy hne with h | h
        · exact Or.inl (Before.cons h)
        · exact Or.inr (Before.cons h)

/-- Component representatives: scan the vertex list, keeping a
vertex exactly when it is not connected (in `F`) to any vertex
later in the list — the last member, in list order, of each
connected component met by the list. -/
def repsFrom (V : List Nat) (F : List (Nat × Nat × Int)) : List Nat → List Nat
  | [] => []
  | v :: vs => if vs.any (fun u => connectedP (F.map (fun e => (e.1, e.2.1))) V v u)
    then repsFrom V F vs else v :: repsFrom V F vs

/-- The number of connected components of the edge list `F`
inside the vertex list `V`. -/
def compCount (V : List Nat) (F : List (Nat × Nat × Int)) : Nat :=
  (repsFrom V F V).length

theorem mem_repsFrom {V : List Nat} (hV : V.Nodup)
    {F : List (Nat × Nat × Int)} (hends : ∀ e ∈ F, e.1 ∈ V ∧ e.2.1 ∈ V) :
    ∀ {vs : List Nat}, vs.Nodup → (∀ x ∈ vs, x ∈ V) → ∀ {v : Nat},
    v ∈ repsFrom V F vs ↔
      v ∈ vs ∧ ∀ u ∈ vs, Before v u vs → ¬ UReach V F v u := by
  intro vs
  induction vs with
  | nil =>
    intro _ _ v
    have h0 : repsFrom V F ([] : List Nat) = [] := rfl
    rw [h0]
    simp
  | cons x xs ih =>
    intro hnd hsub v
    rw [List.nodup_cons] at hnd
    have hxV : x ∈ V := hsub x (List.mem_cons_self)
    have hxs : ∀ y ∈ xs, y ∈ V := fun y hy => hsub y (List.mem_cons_of_mem _ hy)
    have hstep : repsFrom V F (x :: xs) =
        if xs.any (fun u => connectedP (F.map (fun e => (e.1, e.2.1))) V x u)
        then repsFrom V F xs else x :: repsFrom V F xs := rfl
    rw [hstep]
    by_cases hany : xs.any (fun u => connectedP (F.map (fun e => (e.1, e.2.1))) V x u) = true
    · rw [ite_eq_left hany]
      obtain ⟨u, hu, hconn⟩ := List.any_eq_true.mp hany
      have huReach : UReach V F x u := (ureach_iff_connectedP hV hends hxV).mp hconn
      constructor
      · intro h
        have hih := (ih hnd.2 hxs).mp h
        refine ⟨List.mem_cons_of_mem _ hih.1, ?_⟩
        intro y hy hbefore
        rw [List.mem_cons] at hy
        have hvx : v ≠ x := fun h => hnd.1 (h ▸ hih.1)
        rcases hy with rfl | hy
        · exact absurd hbefore (before_target_head hnd.1)
        · have hyx : y ≠ x := fun h => hnd.1 (h ▸ hy)
          exact hih.2 y hy ((before_cons_tail hvx hyx).mp hbefore)
      · rintro ⟨hmem, hcond⟩
        rw [List.mem_cons] at hmem
        rcases hmem with rfl | hmem
        · exact absurd huReach (hcond u (List.mem_cons_of_mem _ hu) (Before.head hu))
        · apply (ih hnd.2 hxs).mpr
          refine ⟨hmem, ?_⟩
          intro y hy hbefore
          exact hcond y (List.mem_cons_of_mem _ hy) (Before.cons hbefore)
    · rw [ite_eq_right hany]
      constructor
      · intro h
        rw [List.mem_cons] at h
        rcases h with rfl | h
        · refine ⟨List.mem_cons_self, ?_⟩
          intro y hy hbefore
          rw [List.mem_cons] at hy
          rcases hy with rfl | hy
          · exact absurd hbefore (by
              rw [before_head hnd.1]; exact hnd.1)
          · intro hU
            have hvV : v ∈ V := hsub v (List.mem_cons_self)
            have hconn : connectedP (F.map (fun e => (e.1, e.2.1))) V v y = true :=
              (ureach_iff_connectedP hV hends hvV).mpr hU
            exact hany (List.any_eq_true.mpr ⟨y, hy, hconn⟩)
        · have hih := (ih hnd.2 hxs).mp h
          refine ⟨List.mem_cons_of_mem _ hih.1, ?_⟩
          intro y hy hbefore
          rw [List.mem_cons] at hy
          have hvx : v ≠ x := fun h => hnd.1 (h ▸ hih.1)
          rcases hy with rfl | hy
          · exact absurd hbefore (before_target_head hnd.1)
          · have hyx : y ≠ x := fun h => hnd.1 (h ▸ hy)
            exact hih.2 y hy ((before_cons_tail hvx hyx).mp hbefore)
      · rintro ⟨hmem, hcond⟩
        rw [List.mem_cons] at hmem
        rcases hmem with rfl | hmem
        · exact List.mem_cons_self
        · apply List.mem_cons_of_mem
          apply (ih hnd.2 hxs).mpr
          refine ⟨hmem, ?_⟩
          intro y hy hbefore
          exact hcond y (List.mem_cons_of_mem _ hy) (Before.cons hbefore)

theorem repsFrom_sublist {V : List Nat} {F : List (Nat × Nat × Int)} :
    ∀ {vs : List Nat}, List.Sublist (repsFrom V F vs) vs := by
  intro vs
  induction vs with
  | nil => exact List.Sublist.refl _
  | cons x xs ih =>
    have hstep : repsFrom V F (x :: xs) =
        if xs.any (fun u => connectedP (F.map (fun e => (e.1, e.2.1))) V x u)
        then repsFrom V F xs else x :: repsFrom V F xs := rfl
    rw [hstep]
    by_cases hany : xs.any (fun u => connectedP (F.map (fun e => (e.1, e.2.1))) V x u) = true
    · rw [ite_eq_left hany]
      exact List.Sublist.cons x ih
    · rw [ite_eq_right hany]
      exact List.Sublist.cons_cons x ih

theorem repsFrom_nodup {V : List Nat} {F : List (Nat × Nat × Int)}
    {vs : List Nat} (h : vs.Nodup) : (repsFrom V F vs).Nodup :=
  repsFrom_sublist.nodup h


/-- In a nodup list, nothing is before itself. -/
theorem before_irrefl {a : Nat} : ∀ {l : List Nat}, l.Nodup → ¬ Before a a l := by
  intro l
  induction l with
  | nil => intro _ h; cases h
  | cons x xs ih =>
    intro hnd h
    rw [List.nodup_cons] at hnd
    cases h with
    | head hm => exact hnd.1 hm
    | cons h' => exact ih hnd.2 h'

/-- `Before` is transitive in a nodup list. -/
theorem before_trans {x y z : Nat} : ∀ {l : List Nat}, l.Nodup →
    Before x y l → Before y z l → Before x z l := by
  intro l
  induction l with
  | nil => intro _ h1 _; cases h1
  | cons c cs ih =>
    intro hnd h1 h2
    rw [List.nodup_cons] at hnd
    cases h1 with
    | head hm =>
      cases h2 with
      | head hm2 => exact Before.head hm2
      | cons h2' => exact Before.head (before_mem h2').2
    | cons h1' =>
      cases h2 with
      | head hm2 => exact absurd (before_mem h1').2 hnd.1
      | cons h2' => exact Before.cons (ih hnd.2 h1' h2')

/-- Refinement of representatives: if every `F₁`-connection is
an `F₂`-connection, every `F₂`-representative is an
`F₁`-representative. -/
theorem repsFrom_mono {V : List Nat} (hV : V.Nodup)
    {F₁ F₂ : List (Nat × Nat × Int)}
    (hends₁ : ∀ e ∈ F₁, e.1 ∈ V ∧ e.2.1 ∈ V)
    (hends₂ : ∀ e ∈ F₂, e.1 ∈ V ∧ e.2.1 ∈ V)
    (hsub : ∀ x ∈ V, ∀ y ∈ V, UReach V F₁ x y → UReach V F₂ x y) :
    ∀ {vs : List Nat}, vs.Nodup → (∀ x ∈ vs, x ∈ V) →
    ∀ {v : Nat}, v ∈ repsFrom V F₂ vs → v ∈ repsFrom V F₁ vs := by
  intro vs hnd hsubV v hv
  have h2 := (mem_repsFrom hV hends₂ hnd hsubV).mp hv
  apply (mem_repsFrom hV hends₁ hnd hsubV).mpr
  refine ⟨h2.1, ?_⟩
  intro u hu hbefore hU
  exact h2.2 u hu hbefore (hsub v (hsubV v h2.1) u (hsubV u hu) hU)

/-- Every vertex of the list has a representative: some member
of `repsFrom` connected to it. -/
theorem repsFrom_exists {V : List Nat} (hV : V.Nodup)
    {F : List (Nat × Nat × Int)} (hends : ∀ e ∈ F, e.1 ∈ V ∧ e.2.1 ∈ V) :
    ∀ {vs : List Nat}, vs.Nodup → (∀ x ∈ vs, x ∈ V) → ∀ {v : Nat},
    v ∈ vs → ∃ r ∈ repsFrom V F vs, UReach V F v r := by
  intro vs
  induction vs with
  | nil => intro _ _ v hv; simp at hv
  | cons x xs ih =>
    intro hnd hsub v hv
    rw [List.nodup_cons] at hnd
    have hxV : x ∈ V := hsub x (List.mem_cons_self)
    have hxs : ∀ y ∈ xs, y ∈ V := fun y hy => hsub y (List.mem_cons_of_mem _ hy)
    have hstep : repsFrom V F (x :: xs) =
        if xs.any (fun u => connectedP (F.map (fun e => (e.1, e.2.1))) V x u)
        then repsFrom V F xs else x :: repsFrom V F xs := rfl
    rw [List.mem_cons] at hv
    rcases hv with h | hv
    · by_cases hany : xs.any (fun u => connectedP (F.map (fun e => (e.1, e.2.1))) V x u) = true
      · obtain ⟨u, hu, hconn⟩ := List.any_eq_true.mp hany
        have huReach : UReach V F x u := (ureach_iff_connectedP hV hends hxV).mp hconn
        obtain ⟨r, hr, hur⟩ := ih hnd.2 hxs hu
        refine ⟨r, ?_, ?_⟩
        · rw [hstep, ite_eq_left hany]; exact hr
        · rw [h]; exact huReach.trans hur
      · refine ⟨x, ?_, ?_⟩
        · rw [hstep, ite_eq_right hany]; exact List.mem_cons_self
        · rw [h]; exact UReach.refl x
    · obtain ⟨r, hr, hvr⟩ := ih hnd.2 hxs hv
      by_cases hany : xs.any (fun u => connectedP (F.map (fun e => (e.1, e.2.1))) V x u) = true
      · have hr' : r ∈ repsFrom V F (x :: xs) := by
          rw [hstep, ite_eq_left hany]; exact hr
        exact ⟨r, hr', hvr⟩
      · have hr' : r ∈ repsFrom V F (x :: xs) := by
          rw [hstep, ite_eq_right hany]; exact List.mem_cons_of_mem _ hr
        exact ⟨r, hr', hvr⟩

/-- Two representatives connected to each other are equal:
each component has exactly one representative. -/
theorem repsFrom_unique {V : List Nat} (hV : V.Nodup)
    {F : List (Nat × Nat × Int)} (hends : ∀ e ∈ F, e.1 ∈ V ∧ e.2.1 ∈ V)
    {r₁ r₂ : Nat} (h1 : r₁ ∈ repsFrom V F V) (h2 : r₂ ∈ repsFrom V F V)
    (hU : UReach V F r₁ r₂) : r₁ = r₂ := by
  apply Classical.byContradiction
  intro hne
  have hc1 := (mem_repsFrom hV hends hV (fun x hx => hx)).mp h1
  have hc2 := (mem_repsFrom hV hends hV (fun x hx => hx)).mp h2
  rcases before_trichotomy hV hc1.1 hc2.1 hne with hb | hb
  · exact hc1.2 r₂ hc2.1 hb hU
  · exact hc2.2 r₁ hc1.1 hb hU.symm

/-- Undirected reachability does not see the orientation of
the added edge. -/
theorem ureach_add_edge_symm {V : List Nat} {F : List (Nat × Nat × Int)}
    {a b : Nat} (w : Int) {x y : Nat} :
    UReach V ((a, b, w) :: F) x y ↔ UReach V ((b, a, w) :: F) x y := by
  rw [UReach.add_edge, UReach.add_edge]
  constructor
  · rintro (h | ⟨h1, h2⟩ | ⟨h1, h2⟩)
    · exact Or.inl h
    · exact Or.inr (Or.inr ⟨h1, h2⟩)
    · exact Or.inr (Or.inl ⟨h1, h2⟩)
  · rintro (h | ⟨h1, h2⟩ | ⟨h1, h2⟩)
    · exact Or.inl h
    · exact Or.inr (Or.inr ⟨h1, h2⟩)
    · exact Or.inr (Or.inl ⟨h1, h2⟩)

/-- Representatives depend only on the reachability relation:
two edge lists with the same connections on `V` have the same
representatives. -/
theorem repsFrom_congr {V : List Nat} (hV : V.Nodup)
    {F₁ F₂ : List (Nat × Nat × Int)}
    (hends₁ : ∀ e ∈ F₁, e.1 ∈ V ∧ e.2.1 ∈ V)
    (hends₂ : ∀ e ∈ F₂, e.1 ∈ V ∧ e.2.1 ∈ V)
    (hrel : ∀ x ∈ V, ∀ y ∈ V, UReach V F₁ x y ↔ UReach V F₂ x y) :
    ∀ v ∈ V, v ∈ repsFrom V F₁ V ↔ v ∈ repsFrom V F₂ V := by
  intro v hv
  constructor
  · intro h
    have hc := (mem_repsFrom hV hends₁ hV (fun x hx => hx)).mp h
    apply (mem_repsFrom hV hends₂ hV (fun x hx => hx)).mpr
    exact ⟨hc.1, fun u hu hb hU => hc.2 u hu hb ((hrel v hv u hu).mpr hU)⟩
  · intro h
    have hc := (mem_repsFrom hV hends₂ hV (fun x hx => hx)).mp h
    apply (mem_repsFrom hV hends₁ hV (fun x hx => hx)).mpr
    exact ⟨hc.1, fun u hu hb hU => hc.2 u hu hb ((hrel v hv u hu).mp hU)⟩

/-- One merge step, one orientation: if `r` (the representative
of `a`'s component) comes before `s` (the representative of
`b`'s component) in `V`, then adding the edge `(a, b)` drops
`r` from the representatives, keeps `s`, and every old
representative is `r` or a representative of the enlarged
graph. -/
theorem repsFrom_add_edge_case {V : List Nat} (hV : V.Nodup)
    {F : List (Nat × Nat × Int)} (hends : ∀ e ∈ F, e.1 ∈ V ∧ e.2.1 ∈ V)
    {a b : Nat} (w : Int)
    (hends' : ∀ e ∈ (a, b, w) :: F, e.1 ∈ V ∧ e.2.1 ∈ V)
    (hnconn : ¬ UReach V F a b)
    {r s : Nat} (hr : r ∈ repsFrom V F V) (hs : s ∈ repsFrom V F V)
    (har : UReach V F a r) (hbs : UReach V F b s)
    (hbefore : Before r s V) (hrs : r ≠ s) :
    r ∉ repsFrom V ((a, b, w) :: F) V ∧ s ∈ repsFrom V ((a, b, w) :: F) V ∧
    ∀ v ∈ repsFrom V F V, v ∈ r :: repsFrom V ((a, b, w) :: F) V := by
  have hcr := (mem_repsFrom hV hends hV (fun x hx => hx)).mp hr
  have hcs := (mem_repsFrom hV hends hV (fun x hx => hx)).mp hs
  have hGrs : UReach V ((a, b, w) :: F) r s :=
    ((UReach.mono (fun e he => List.mem_cons_of_mem _ he) har.symm).trans
      (UReach.of_edge (List.mem_cons_self))).trans
      (UReach.mono (fun e he => List.mem_cons_of_mem _ he) hbs)
  have hdrop : r ∉ repsFrom V ((a, b, w) :: F) V := by
    intro hcon
    have hc := (mem_repsFrom hV hends' hV (fun x hx => hx)).mp hcon
    exact hc.2 s hcs.1 hbefore hGrs
  have hsurv : s ∈ repsFrom V ((a, b, w) :: F) V := by
    apply (mem_repsFrom hV hends' hV (fun x hx => hx)).mpr
    refine ⟨hcs.1, ?_⟩
    intro u huV hbefore' hU
    rw [UReach.add_edge] at hU
    rcases hU with h1 | ⟨h1, h2⟩ | ⟨h1, h2⟩
    · exact hcs.2 u huV hbefore' h1
    · exact hrs (repsFrom_unique hV hends hs hr (h1.trans har)).symm
    · exact hcr.2 u huV (before_trans hV hbefore hbefore') (har.symm.trans h2)
  refine ⟨hdrop, hsurv, ?_⟩
  intro v hv
  have hcv := (mem_repsFrom hV hends hV (fun x hx => hx)).mp hv
  by_cases hvr : v = r
  · rw [hvr]; exact List.mem_cons_self
  · by_cases hvs : v = s
    · rw [hvs]; exact List.mem_cons_of_mem _ hsurv
    · apply List.mem_cons_of_mem
      apply (mem_repsFrom hV hends' hV (fun x hx => hx)).mpr
      refine ⟨hcv.1, ?_⟩
      intro u huV hbefore' hU
      rw [UReach.add_edge] at hU
      rcases hU with h1 | ⟨h1, h2⟩ | ⟨h1, h2⟩
      · exact hcv.2 u huV hbefore' h1
      · exact hvr (repsFrom_unique hV hends hv hr (h1.trans har))
      · exact hvs (repsFrom_unique hV hends hv hs (h1.trans hbs))

/-- Adding one forest edge between two different components
drops the component count by exactly one. -/
theorem compCount_add_edge {V : List Nat} (hV : V.Nodup)
    {F : List (Nat × Nat × Int)} (hends : ∀ e ∈ F, e.1 ∈ V ∧ e.2.1 ∈ V)
    {a b : Nat} (ha : a ∈ V) (hb : b ∈ V) (hab : a ≠ b) (w : Int)
    (hends' : ∀ e ∈ (a, b, w) :: F, e.1 ∈ V ∧ e.2.1 ∈ V)
    (hnconn : ¬ UReach V F a b) :
    compCount V ((a, b, w) :: F) + 1 = compCount V F := by
  obtain ⟨ra, hra, hara⟩ := repsFrom_exists hV hends hV (fun x hx => hx) ha
  obtain ⟨rb, hrb, hbrb⟩ := repsFrom_exists hV hends hV (fun x hx => hx) hb
  have hraV : ra ∈ V := ((mem_repsFrom hV hends hV (fun x hx => hx)).mp hra).1
  have hrbV : rb ∈ V := ((mem_repsFrom hV hends hV (fun x hx => hx)).mp hrb).1
  have hrarb : ra ≠ rb := by
    intro h
    apply hnconn
    rw [← h] at hbrb
    exact hara.trans hbrb.symm
  have hGsub : ∀ v ∈ repsFrom V ((a, b, w) :: F) V, v ∈ repsFrom V F V :=
    fun v hv => repsFrom_mono hV hends hends'
      (fun x _ y _ hxy => UReach.mono (fun e he => List.mem_cons_of_mem _ he) hxy)
      hV (fun x hx => hx) hv
  have bounds : ∀ (d : Nat), d ∈ repsFrom V F V →
      d ∉ repsFrom V ((a, b, w) :: F) V →
      (∀ v ∈ repsFrom V F V, v ∈ d :: repsFrom V ((a, b, w) :: F) V) →
      (repsFrom V ((a, b, w) :: F) V).length + 1 = (repsFrom V F V).length := by
    intro d hdF hd hsub
    have h1 := nodup_length_le (d :: repsFrom V ((a, b, w) :: F) V) (repsFrom V F V)
      (List.nodup_cons.mpr ⟨hd, repsFrom_nodup hV⟩) (repsFrom_nodup hV)
      (fun z hz => by
        rw [List.mem_cons] at hz
        rcases hz with rfl | hz
        · exact hdF
        · exact hGsub z hz)
    have h2 := nodup_length_le (repsFrom V F V) (d :: repsFrom V ((a, b, w) :: F) V)
      (repsFrom_nodup hV) (List.nodup_cons.mpr ⟨hd, repsFrom_nodup hV⟩) hsub
    rw [List.length_cons] at h1 h2
    omega
  show (repsFrom V ((a, b, w) :: F) V).length + 1 = (repsFrom V F V).length
  rcases before_trichotomy hV hraV hrbV hrarb with hb1 | hb1
  · have hc := repsFrom_add_edge_case hV hends w hends' hnconn hra hrb hara hbrb hb1 hrarb
    exact bounds ra hra hc.1 hc.2.2
  · have hends'' : ∀ e ∈ (b, a, w) :: F, e.1 ∈ V ∧ e.2.1 ∈ V := by
      intro e he
      rw [List.mem_cons] at he
      rcases he with rfl | he
      · exact ⟨hb, ha⟩
      · exact hends e he
    have hnconn' : ¬ UReach V F b a := fun h => hnconn h.symm
    have hc := repsFrom_add_edge_case hV hends w hends'' hnconn' hrb hra hbrb hara hb1
      hrarb.symm
    have htr : ∀ v ∈ V, v ∈ repsFrom V ((b, a, w) :: F) V ↔
        v ∈ repsFrom V ((a, b, w) :: F) V :=
      repsFrom_congr hV hends'' hends' (fun x _ y _ => (ureach_add_edge_symm w).symm)
    have hd : rb ∉ repsFrom V ((a, b, w) :: F) V := by
      intro hcon
      exact hc.1 ((htr rb hrbV).mpr hcon)
    have hsub : ∀ v ∈ repsFrom V F V, v ∈ rb :: repsFrom V ((a, b, w) :: F) V := by
      intro v hv
      have hvV : v ∈ V := ((mem_repsFrom hV hends hV (fun x hx => hx)).mp hv).1
      have h := hc.2.2 v hv
      rw [List.mem_cons] at h ⊢
      rcases h with rfl | h
      · exact Or.inl rfl
      · exact Or.inr ((htr v hvV).mp h)
    exact bounds rb hrb hd hsub

/-- The cardinality formula for a forest: the number of edges
plus the number of connected components is the number of
vertices. -/
theorem forest_cardinality {V : List Nat} (hV : V.Nodup) :
    ∀ {F : List (Nat × Nat × Int)}, (∀ e ∈ F, e.1 ∈ V ∧ e.2.1 ∈ V) →
    F.Nodup → (∀ e ∈ F, ¬ UReach V (F.erase e) e.1 e.2.1) →
    F.length + compCount V F = V.length := by
  intro F
  induction F with
  | nil =>
    intro _ _ _
    have hsub : ∀ v ∈ V, v ∈ repsFrom V [] V := by
      intro v hv
      apply (mem_repsFrom hV (fun e he => (List.not_mem_nil he).elim)
        hV (fun x hx => hx)).mpr
      refine ⟨hv, ?_⟩
      intro u _ hbefore hU
      rw [UReach.eq_of_empty hU] at hbefore
      exact before_irrefl hV hbefore
    have h1 := nodup_length_le V (repsFrom V [] V) hV (repsFrom_nodup hV) hsub
    have h2 := nodup_length_le (repsFrom V [] V) V (repsFrom_nodup hV) hV
      (fun z hz => repsFrom_sublist.subset hz)
    have hcc : compCount V [] = (repsFrom V [] V).length := rfl
    show 0 + compCount V [] = V.length
    omega
  | cons e F ih =>
    obtain ⟨a, b, w⟩ := e
    intro hends hnd hforest
    rw [List.nodup_cons] at hnd
    have htends : a ∈ V ∧ b ∈ V := hends (a, b, w) (List.mem_cons_self)
    have hendsF : ∀ e ∈ F, e.1 ∈ V ∧ e.2.1 ∈ V :=
      fun e he => hends e (List.mem_cons_of_mem _ he)
    have hforestF : ∀ e ∈ F, ¬ UReach V (F.erase e) e.1 e.2.1 := by
      intro e he hU
      apply hforest e (List.mem_cons_of_mem _ he)
      have hne : (a, b, w) ≠ e := fun h => hnd.1 (h ▸ he)
      have hba : ((a, b, w) == e) = false := by
        rw [Bool.eq_false_iff]; intro hb; exact hne (beq_iff_eq.mp hb)
      have herase : ((a, b, w) :: F).erase e = (a, b, w) :: (F.erase e) := by
        simp [List.erase, hba]
      rw [herase]
      exact UReach.mono (fun f hf => List.mem_cons_of_mem _ hf) hU
    have ih' := ih hendsF hnd.2 hforestF
    have hnconn : ¬ UReach V F a b := by
      have h := hforest (a, b, w) (List.mem_cons_self)
      have herase : ((a, b, w) :: F).erase (a, b, w) = F := by simp [List.erase]
      rw [herase] at h
      exact h
    have hab : a ≠ b := by
      intro h
      apply hnconn
      rw [h]
      exact UReach.refl b
    have hmerge := compCount_add_edge hV hendsF htends.1 htends.2 hab w
      (fun e he => by
        rw [List.mem_cons] at he
        rcases he with rfl | he
        · exact htends
        · exact hendsF e he) hnconn
    rw [List.length_cons]
    omega


/-- A filtered forest is a forest. -/
theorem forest_filter {V : List Nat} {F : List (Nat × Nat × Int)} (θ : Int)
    (hnd : F.Nodup)
    (hF : ∀ e ∈ F, ¬ UReach V (F.erase e) e.1 e.2.1) :
    ∀ e ∈ F.filter (fun f => f.2.2 ≤ θ),
    ¬ UReach V ((F.filter (fun f => f.2.2 ≤ θ)).erase e) e.1 e.2.1 := by
  intro e he hU
  apply hF e (List.mem_filter.mp he).1
  exact UReach.mono (fun f hf => by
    have hf1 : f ∈ F.filter (fun f => f.2.2 ≤ θ) := List.mem_of_mem_erase hf
    have hfne : f ≠ e := by
      intro hfe
      subst hfe
      exact List.Nodup.not_mem_erase (hnd.filter _) hf
    exact (List.mem_erase_of_ne hfne).mpr (List.mem_filter.mp hf1).1) hU

theorem hends_filter {V : List Nat} {F : List (Nat × Nat × Int)} (θ : Int)
    (hends : ∀ e ∈ F, e.1 ∈ V ∧ e.2.1 ∈ V) :
    ∀ e ∈ F.filter (fun f => f.2.2 ≤ θ), e.1 ∈ V ∧ e.2.1 ∈ V :=
  fun e he => hends e (List.mem_filter.mp he).1

/-- Walks transfer along edge-wise connections: if every `F`
edge has its endpoints joined in `G`, every `F`-walk is a
`G`-walk. -/
theorem ureach_of_edges_reach {V : List Nat} {F G : List (Nat × Nat × Int)}
    (h : ∀ e ∈ F, UReach V G e.1 e.2.1) {x y : Nat} (hxy : UReach V F x y) :
    UReach V G x y := by
  induction hxy with
  | refl => exact UReach.refl _
  | step he htail ih =>
    rename_i p q r
    rw [mem_fgraph_edges] at he
    rcases he with ⟨w, hw⟩ | ⟨w, hw⟩
    · exact (h (p, q, w) hw).trans ih
    · exact (h (q, p, w) hw).symm.trans ih

theorem kruskal_threshold_reach_aux (wg : WGraph)
    (h5 : ∀ e ∈ [] ++ sortEdges wg.edges,
      UReach wg.vertices ((kruskal wg).filter (fun f => f.2.2 ≤ e.2.2)) e.1 e.2.1)
    {T : List (Nat × Nat × Int)} (hT : ∀ e ∈ T, e ∈ wg.edges) (θ : Int)
    {x y : Nat} (h : UReach wg.vertices (T.filter (fun f => f.2.2 ≤ θ)) x y) :
    UReach wg.vertices ((kruskal wg).filter (fun f => f.2.2 ≤ θ)) x y := by
  induction h with
  | refl => exact UReach.refl _
  | step he htail ih =>
    rename_i p q r
    rw [mem_fgraph_edges] at he
    rcases he with ⟨w, hw⟩ | ⟨w, hw⟩
    · have hwT : (p, q, w) ∈ T := (List.mem_filter.mp hw).1
      have hwθ : w ≤ θ := of_decide_eq_true (List.mem_filter.mp hw).2
      have hwalk := h5 (p, q, w) (List.mem_append_right _
        ((sortEdges_perm wg.edges).mem_iff.mpr (hT (p, q, w) hwT)))
      have hstep : UReach wg.vertices ((kruskal wg).filter (fun f => f.2.2 ≤ θ)) p q :=
        UReach.mono (fun f hf => List.mem_filter.mpr
          ⟨(List.mem_filter.mp hf).1,
            decide_eq_true (Int.le_trans (of_decide_eq_true (List.mem_filter.mp hf).2)
              hwθ)⟩) hwalk
      exact hstep.trans ih
    · have hwT : (q, p, w) ∈ T := (List.mem_filter.mp hw).1
      have hwθ : w ≤ θ := of_decide_eq_true (List.mem_filter.mp hw).2
      have hwalk := h5 (q, p, w) (List.mem_append_right _
        ((sortEdges_perm wg.edges).mem_iff.mpr (hT (q, p, w) hwT)))
      have hstep : UReach wg.vertices ((kruskal wg).filter (fun f => f.2.2 ≤ θ)) q p :=
        UReach.mono (fun f hf => List.mem_filter.mpr
          ⟨(List.mem_filter.mp hf).1,
            decide_eq_true (Int.le_trans (of_decide_eq_true (List.mem_filter.mp hf).2)
              hwθ)⟩) hwalk
      exact hstep.symm.trans ih

/-- The threshold form of the cycle property: a walk in the
competitor's light edges is a walk in the output's light
edges, at every threshold. -/
theorem kruskal_threshold_reach (wg : WGraph) (hV : wg.vertices.Nodup)
    (hE : ∀ e ∈ wg.edges, e.1 ∈ wg.vertices ∧ e.2.1 ∈ wg.vertices)
    {T : List (Nat × Nat × Int)} (hT : ∀ e ∈ T, e ∈ wg.edges) (θ : Int) :
    ∀ {x y : Nat}, x ∈ wg.vertices → y ∈ wg.vertices →
    UReach wg.vertices (T.filter (fun f => f.2.2 ≤ θ)) x y →
    UReach wg.vertices ((kruskal wg).filter (fun f => f.2.2 ≤ θ)) x y := by
  have hspec := kruskalAux_spec wg.vertices hV wg.edges hE (sortEdges wg.edges) []
    (sortEdges_sorted wg.edges)
    (fun e he => (sortEdges_perm wg.edges).mem_iff.mp he)
    (fun e he => by simp at he) (fun e he => by simp at he) (List.nodup_nil)
    (fun e he => by simp at he) (fun f hf => by simp at hf)
  obtain ⟨-, -, -, -, h5⟩ := hspec
  intro x y _ _ h
  exact kruskal_threshold_reach_aux wg h5 hT θ h

/-- At every weight threshold, the output has at least as many
light edges as any spanning forest: the counting form of
minimality. -/
theorem kruskal_threshold (wg : WGraph) (hV : wg.vertices.Nodup)
    (hE : ∀ e ∈ wg.edges, e.1 ∈ wg.vertices ∧ e.2.1 ∈ wg.vertices)
    {T : List (Nat × Nat × Int)} (hTsub : ∀ e ∈ T, e ∈ wg.edges)
    (hTends : ∀ e ∈ T, e.1 ∈ wg.vertices ∧ e.2.1 ∈ wg.vertices)
    (hTnd : T.Nodup)
    (hTforest : ∀ e ∈ T, ¬ UReach wg.vertices (T.erase e) e.1 e.2.1)
    (θ : Int) :
    (T.filter (fun f => f.2.2 ≤ θ)).length ≤
      ((kruskal wg).filter (fun f => f.2.2 ≤ θ)).length := by
  have hRf := kruskal_forest wg hV hE
  have hRends : ∀ e ∈ kruskal wg, e.1 ∈ wg.vertices ∧ e.2.1 ∈ wg.vertices :=
    fun e he => hE e (hRf.1 e he)
  have hcardT := forest_cardinality hV (hends_filter θ hTends) (hTnd.filter _)
    (forest_filter θ hTnd hTforest)
  have hcardR := forest_cardinality hV (hends_filter θ hRends) (hRf.2.1.filter _)
    (forest_filter θ hRf.2.1 hRf.2.2.1)
  have hcomp : compCount wg.vertices ((kruskal wg).filter (fun f => f.2.2 ≤ θ)) ≤
      compCount wg.vertices (T.filter (fun f => f.2.2 ≤ θ)) := by
    show (repsFrom wg.vertices ((kruskal wg).filter (fun f => f.2.2 ≤ θ))
        wg.vertices).length ≤
      (repsFrom wg.vertices (T.filter (fun f => f.2.2 ≤ θ)) wg.vertices).length
    exact nodup_length_le _ _ (repsFrom_nodup hV) (repsFrom_nodup hV)
      (fun z hz => repsFrom_mono hV (hends_filter θ hTends) (hends_filter θ hRends)
        (fun x hx y hy hxy => kruskal_threshold_reach wg hV hE hTsub θ hx hy hxy)
        hV (fun x hx => hx) hz)
  omega

/-- Every nonempty edge list has a minimum-weight edge. -/
theorem exists_min_weight : ∀ (l : List (Nat × Nat × Int)), l ≠ [] →
    ∃ t₀ ∈ l, ∀ t ∈ l, t₀.2.2 ≤ t.2.2 := by
  intro l
  induction l with
  | nil => intro h; exact absurd rfl h
  | cons x xs ih =>
    intro _
    cases xs with
    | nil =>
      exact ⟨x, List.mem_cons_self, fun t ht => by
        rw [List.mem_cons] at ht
        rcases ht with rfl | ht
        · exact Int.le_refl _
        · simp at ht⟩
    | cons y ys =>
      obtain ⟨m, hm, hmin⟩ := ih (by simp)
      by_cases h : x.2.2 ≤ m.2.2
      · refine ⟨x, List.mem_cons_self, ?_⟩
        intro t ht
        rw [List.mem_cons] at ht
        rcases ht with rfl | ht
        · exact Int.le_refl _
        · exact Int.le_trans h (hmin t ht)
      · refine ⟨m, List.mem_cons_of_mem _ hm, ?_⟩
        intro t ht
        rw [List.mem_cons] at ht
        rcases ht with rfl | ht
        · omega
        · exact hmin t ht

/-- How a weight-filter count changes when one edge is erased. -/
theorem filter_erase_length (θ : Int) (e : Nat × Nat × Int) :
    ∀ (l : List (Nat × Nat × Int)), e ∈ l →
    ((l.erase e).filter (fun f => f.2.2 ≤ θ)).length =
      (l.filter (fun f => f.2.2 ≤ θ)).length - (if e.2.2 ≤ θ then 1 else 0) := by
  intro l
  induction l with
  | nil => intro h; simp at h
  | cons x xs ih =>
    intro h
    rw [List.mem_cons] at h
    by_cases hxe : x = e
    · subst hxe
      have herase : ((x :: xs).erase x) = xs := by simp [List.erase]
      rw [herase]
      by_cases hw : x.2.2 ≤ θ
      · rw [List.filter_cons, ite_eq_left (decide_eq_true hw), ite_eq_left hw,
          List.length_cons]
        omega
      · rw [List.filter_cons, ite_eq_right (fun hh => hw (of_decide_eq_true hh)),
          ite_eq_right hw, Nat.sub_zero]
    · have hne : x ≠ e := hxe
      have hba : (x == e) = false := by
        rw [Bool.eq_false_iff]; intro hb; exact hne (beq_iff_eq.mp hb)
      have herase : ((x :: xs).erase e) = x :: (xs.erase e) := by
        simp [List.erase, hba]
      have he : e ∈ xs := by
        rcases h with h | h
        · exact (hne h.symm).elim
        · exact h
      have ih' := ih he
      rw [herase]
      by_cases hw : x.2.2 ≤ θ
      · rw [List.filter_cons, ite_eq_left (decide_eq_true hw), List.filter_cons,
          ite_eq_left (decide_eq_true hw), List.length_cons, List.length_cons]
        have hc : (if e.2.2 ≤ θ then 1 else 0) ≤ 1 := by split <;> omega
        have hB : (if e.2.2 ≤ θ then 1 else 0) ≤
            (xs.filter (fun f => f.2.2 ≤ θ)).length := by
          by_cases heθ : e.2.2 ≤ θ
          · rw [ite_eq_left heθ]
            exact List.length_pos_of_mem
              (List.mem_filter.mpr ⟨he, decide_eq_true heθ⟩)
          · rw [ite_eq_right heθ]
            exact Nat.zero_le _
        omega
      · rw [List.filter_cons, ite_eq_right (fun hh => hw (of_decide_eq_true hh)),
          List.filter_cons, ite_eq_right (fun hh => hw (of_decide_eq_true hh))]
        exact ih'

/-- Erasing an edge removes exactly its weight from the total. -/
theorem chainWeight_erase (e : Nat × Nat × Int) :
    ∀ (l : List (Nat × Nat × Int)), e ∈ l →
    chainWeight (l.erase e) = chainWeight l - e.2.2 := by
  intro l
  induction l with
  | nil => intro h; simp at h
  | cons x xs ih =>
    intro h
    rw [List.mem_cons] at h
    by_cases hxe : x = e
    · subst hxe
      have herase : ((x :: xs).erase x) = xs := by simp [List.erase]
      have hcw : chainWeight (x :: xs) = x.2.2 + chainWeight xs := rfl
      rw [herase, hcw]
      omega
    · have hne : x ≠ e := hxe
      have hba : (x == e) = false := by
        rw [Bool.eq_false_iff]; intro hb; exact hne (beq_iff_eq.mp hb)
      have herase : ((x :: xs).erase e) = x :: (xs.erase e) := by
        simp [List.erase, hba]
      have he : e ∈ xs := by
        rcases h with h | h
        · exact (hne h.symm).elim
        · exact h
      have hcw : chainWeight (x :: xs) = x.2.2 + chainWeight xs := rfl
      have hcw2 : chainWeight (x :: (xs.erase e)) = x.2.2 + chainWeight (xs.erase e) := rfl
      rw [herase, hcw, hcw2, ih he]
      omega

/-- The weight comparison: if at every threshold `F` has at
least as many light edges as `T`, and the two lists have the
same length, then `F` weighs no more than `T`. Proved by strong
induction on the length, removing a minimum-weight edge of `T`
and a no-heavier edge of `F` at each step. -/
theorem weight_le_of_threshold {F T : List (Nat × Nat × Int)}
    (hcount : ∀ θ : Int, (T.filter (fun f => f.2.2 ≤ θ)).length ≤
      (F.filter (fun f => f.2.2 ≤ θ)).length)
    (hlen : F.length = T.length) :
    chainWeight F ≤ chainWeight T := by
  have key : ∀ n : Nat, ∀ (F T : List (Nat × Nat × Int)), T.length ≤ n →
      (∀ θ : Int, (T.filter (fun f => f.2.2 ≤ θ)).length ≤
        (F.filter (fun f => f.2.2 ≤ θ)).length) →
      F.length = T.length → chainWeight F ≤ chainWeight T := by
    intro n
    induction n with
    | zero =>
      intro F T hTlen _ hlen
      have hT : T = [] := List.eq_nil_iff_length_eq_zero.mpr (Nat.le_zero.mp hTlen)
      have hF : F = [] := List.eq_nil_iff_length_eq_zero.mpr (by omega)
      rw [hT, hF]
      exact Int.le_refl _
    | succ n ih =>
      intro F T hTlen hcount hlen
      cases T with
      | nil =>
        have hF : F = [] := List.eq_nil_iff_length_eq_zero.mpr hlen
        rw [hF]
        exact Int.le_refl _
      | cons t T' =>
        obtain ⟨t₀, ht₀, hmin⟩ := exists_min_weight (t :: T') (by simp)
        have ht₀mem : t₀ ∈ (t :: T').filter (fun f => f.2.2 ≤ t₀.2.2) :=
          List.mem_filter.mpr ⟨ht₀, decide_eq_true (Int.le_refl _)⟩
        have hpos : 0 < ((t :: T').filter (fun f => f.2.2 ≤ t₀.2.2)).length :=
          List.length_pos_of_mem ht₀mem
        obtain ⟨f₀, hf₀⟩ : ∃ f₀, f₀ ∈ F.filter (fun f => f.2.2 ≤ t₀.2.2) := by
          cases hF : F.filter (fun f => f.2.2 ≤ t₀.2.2) with
          | nil =>
            have hcnt := hcount t₀.2.2
            rw [hF] at hcnt
            have hcnt2 : ((t :: T').filter (fun f => f.2.2 ≤ t₀.2.2)).length ≤ 0 := hcnt
            omega
          | cons f₀ fs => exact ⟨f₀, List.mem_cons_self⟩
        rw [List.mem_filter] at hf₀
        obtain ⟨hf₀F, hf₀w⟩ := hf₀
        have hf₀w' : f₀.2.2 ≤ t₀.2.2 := of_decide_eq_true hf₀w
        have hcount' : ∀ θ : Int,
            (((t :: T').erase t₀).filter (fun f => f.2.2 ≤ θ)).length ≤
            ((F.erase f₀).filter (fun f => f.2.2 ≤ θ)).length := by
          intro θ
          have hTe := filter_erase_length θ t₀ (t :: T') ht₀
          have hFe := filter_erase_length θ f₀ F hf₀F
          have hc := hcount θ
          by_cases hθ : t₀.2.2 ≤ θ
          · rw [ite_eq_left hθ] at hTe
            rw [ite_eq_left (Int.le_trans hf₀w' hθ)] at hFe
            omega
          · rw [ite_eq_right hθ] at hTe
            have hTθ : ((t :: T').filter (fun f => f.2.2 ≤ θ)) = [] :=
              List.filter_eq_nil_iff.mpr (fun a ha hpa =>
                hθ (Int.le_trans (hmin a ha) (of_decide_eq_true hpa)))
            rw [hTθ] at hTe
            simp only [List.length_nil, Nat.sub_zero] at hTe
            omega
        have ih' := ih (F.erase f₀) ((t :: T').erase t₀)
          (by rw [List.length_erase_of_mem ht₀]; omega) hcount'
          (by rw [List.length_erase_of_mem ht₀, List.length_erase_of_mem hf₀F, hlen])
        have hw1 := chainWeight_erase f₀ F hf₀F
        have hw2 := chainWeight_erase t₀ (t :: T') ht₀
        omega
  exact key T.length F T (Nat.le_refl _) hcount hlen

/-- Minimality: the output of Kruskal's algorithm weighs no
more than any spanning forest of the same graph. -/
theorem kruskal_minimal (wg : WGraph) (hV : wg.vertices.Nodup)
    (hE : ∀ e ∈ wg.edges, e.1 ∈ wg.vertices ∧ e.2.1 ∈ wg.vertices)
    {T : List (Nat × Nat × Int)} (hTsub : ∀ e ∈ T, e ∈ wg.edges)
    (hTends : ∀ e ∈ T, e.1 ∈ wg.vertices ∧ e.2.1 ∈ wg.vertices)
    (hTnd : T.Nodup)
    (hTforest : ∀ e ∈ T, ¬ UReach wg.vertices (T.erase e) e.1 e.2.1)
    (hTspan : ∀ e ∈ wg.edges, UReach wg.vertices T e.1 e.2.1) :
    chainWeight (kruskal wg) ≤ chainWeight T := by
  have hRf := kruskal_forest wg hV hE
  have hRends : ∀ e ∈ kruskal wg, e.1 ∈ wg.vertices ∧ e.2.1 ∈ wg.vertices :=
    fun e he => hE e (hRf.1 e he)
  have hrel : ∀ x ∈ wg.vertices, ∀ y ∈ wg.vertices,
      UReach wg.vertices T x y ↔ UReach wg.vertices (kruskal wg) x y :=
    fun x _ y _ => ⟨fun h => ureach_of_edges_reach
        (fun e he => hRf.2.2.2 e (hTsub e he)) h,
      fun h => ureach_of_edges_reach (fun e he => hTspan e (hRf.1 e he)) h⟩
  have hcompEq : compCount wg.vertices T = compCount wg.vertices (kruskal wg) := by
    have hincl1 : ∀ z ∈ repsFrom wg.vertices T wg.vertices,
        z ∈ repsFrom wg.vertices (kruskal wg) wg.vertices :=
      fun z hz => (repsFrom_congr hV hTends hRends hrel z
        ((mem_repsFrom hV hTends hV (fun x hx => hx)).mp hz).1).mp hz
    have hincl2 : ∀ z ∈ repsFrom wg.vertices (kruskal wg) wg.vertices,
        z ∈ repsFrom wg.vertices T wg.vertices :=
      fun z hz => (repsFrom_congr hV hTends hRends hrel z
        ((mem_repsFrom hV hRends hV (fun x hx => hx)).mp hz).1).mpr hz
    have h1 := nodup_length_le _ _ (repsFrom_nodup hV) (repsFrom_nodup hV) hincl1
    have h2 := nodup_length_le _ _ (repsFrom_nodup hV) (repsFrom_nodup hV) hincl2
    show (repsFrom wg.vertices T wg.vertices).length =
      (repsFrom wg.vertices (kruskal wg) wg.vertices).length
    omega
  have hcardT := forest_cardinality hV hTends hTnd hTforest
  have hcardR := forest_cardinality hV hRends hRf.2.1 hRf.2.2.1
  have hlen : (kruskal wg).length = T.length := by omega
  exact weight_le_of_threshold
    (fun θ => kruskal_threshold wg hV hE hTsub hTends hTnd hTforest θ) hlen

/-- **Kruskal correctness.** Under platform well-formedness
(vertex list nodup, edge endpoints among the vertices), the
output of Kruskal's algorithm is a minimum-weight spanning
forest: a nodup, acyclic set of the graph's own edges, joining
the endpoints of every edge of the graph, of minimum total
weight among all such spanning forests. -/
theorem kruskal_correctness (wg : WGraph) (hV : wg.vertices.Nodup)
    (hE : ∀ e ∈ wg.edges, e.1 ∈ wg.vertices ∧ e.2.1 ∈ wg.vertices) :
    (∀ e ∈ kruskal wg, e ∈ wg.edges) ∧ (kruskal wg).Nodup ∧
    (∀ e ∈ kruskal wg, ¬ UReach wg.vertices ((kruskal wg).erase e) e.1 e.2.1) ∧
    (∀ e ∈ wg.edges, UReach wg.vertices (kruskal wg) e.1 e.2.1) ∧
    (∀ T : List (Nat × Nat × Int), (∀ e ∈ T, e ∈ wg.edges) → T.Nodup →
      (∀ e ∈ T, ¬ UReach wg.vertices (T.erase e) e.1 e.2.1) →
      (∀ e ∈ wg.edges, UReach wg.vertices T e.1 e.2.1) →
      chainWeight (kruskal wg) ≤ chainWeight T) := by
  obtain ⟨h1, h2, h3, h4⟩ := kruskal_forest wg hV hE
  refine ⟨h1, h2, h3, h4, ?_⟩
  intro T hTsub hTnd hTforest hTspan
  exact kruskal_minimal wg hV hE hTsub (fun e he => hE e (hTsub e he)) hTnd
    hTforest hTspan

/-- On a connected graph with at least one vertex, Kruskal's
output is a spanning tree: exactly one fewer edge than
vertices. -/
theorem kruskal_tree_length (wg : WGraph) (hV : wg.vertices.Nodup)
    (hE : ∀ e ∈ wg.edges, e.1 ∈ wg.vertices ∧ e.2.1 ∈ wg.vertices)
    (hconn : Graph.Connected wg.toGraph) (hne : wg.vertices ≠ []) :
    (kruskal wg).length + 1 = wg.vertices.length := by
  have hRf := kruskal_forest wg hV hE
  have hRends : ∀ e ∈ kruskal wg, e.1 ∈ wg.vertices ∧ e.2.1 ∈ wg.vertices :=
    fun e he => hE e (hRf.1 e he)
  have hcard := forest_cardinality hV hRends hRf.2.1 hRf.2.2.1
  have hcomp : compCount wg.vertices (kruskal wg) = 1 := by
    obtain ⟨v, hv⟩ : ∃ v, v ∈ wg.vertices := by
      cases hvs : wg.vertices with
      | nil => exact absurd hvs hne
      | cons v vs => exact ⟨v, List.mem_cons_self⟩
    obtain ⟨r, hr, -⟩ := repsFrom_exists hV hRends hV (fun x hx => hx) hv
    have hrV : r ∈ wg.vertices :=
      ((mem_repsFrom hV hRends hV (fun x hx => hx)).mp hr).1
    have hsub : ∀ z ∈ repsFrom wg.vertices (kruskal wg) wg.vertices, z ∈ [r] := by
      intro z hz
      have hzV : z ∈ wg.vertices :=
        ((mem_repsFrom hV hRends hV (fun x hx => hx)).mp hz).1
      have hreach : UReach wg.vertices (kruskal wg) z r :=
        ureach_of_edges_reach (fun e he => hRf.2.2.2 e he) (hconn z hzV r hrV)
      exact List.mem_singleton.mpr (repsFrom_unique hV hRends hz hr hreach)
    have hlen1 := nodup_length_le _ _ (repsFrom_nodup hV)
      (List.nodup_cons.mpr ⟨by simp, List.nodup_nil⟩) hsub
    have hlen2 := nodup_length_le [r] _
      (List.nodup_cons.mpr ⟨by simp, List.nodup_nil⟩) (repsFrom_nodup hV)
      (fun z hz => by
        rw [List.mem_singleton] at hz
        rw [hz]
        exact hr)
    have hcc : compCount wg.vertices (kruskal wg) =
        (repsFrom wg.vertices (kruskal wg) wg.vertices).length := rfl
    simp only [List.length_singleton] at hlen1 hlen2
    omega
  rw [← hcard, hcomp]

end AxiomCode
