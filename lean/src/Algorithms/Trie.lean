import Spec
import Tactics

/-!
# AxiomCode — Verified Trie (insert / lookup)

A formally verified trie over `Nat`-labelled edges, with the
insert/lookup correctness theorem.

Promoted from `lean/drafts/insert_lookup_correctness (trie.lean` under
the L2 promotion procedure (`lean/PROMOTION.md`). The draft's shells are
authored for real: the structure gains its two fields (the node's
optional value and its association list of children), and `insert` /
`lookup` gain their bodies. Two draft defects are recorded, not silently
repaired:

- The draft's path type, `Path trie.root`, is ill-formed — the structure
  has no `root` field and no `Path` type exists. A path is authored as
  what it can only mean here: the list of edge labels from the root,
  `List Nat`.
- The draft's bare names `insert` / `lookup` cannot be kept:
  `AxiomCode.insert` is already the insertion-sort entry's function.
  The operations are authored as `Trie.insert` / `Trie.lookup`; the
  theorem keeps the draft's name, `insert_lookup_correctness`, and its
  statement's shape.
-/

namespace AxiomCode

/-- A trie over `Nat`-labelled edges: each node carries an optional value
(the entry for the path from the root to this node) and an association
list of children, one per edge label. -/
structure Trie (α : Type) where
  value : Option α
  children : List (Nat × Trie α)

/-- The empty trie: no entries anywhere. -/
def Trie.empty {α : Type} : Trie α :=
  ⟨none, []⟩

/-- Look up the child of a node reached by edge label `c` in an
association list of children; a missing label denotes the empty trie. -/
def getChildList {α : Type} : List (Nat × Trie α) → Nat → Trie α
  | [], _ => ⟨none, []⟩
  | (k, child) :: rest, c => if k = c then child else getChildList rest c

/-- Replace or add the child for edge label `c` in an association list of
children. -/
def setChildList {α : Type} : List (Nat × Trie α) → Nat → Trie α → List (Nat × Trie α)
  | [], c, child => [(c, child)]
  | (k, old) :: rest, c, child =>
    if k = c then (c, child) :: rest else (k, old) :: setChildList rest c child

/-- The child of a trie node along edge label `c` (the empty trie if the
edge is absent). -/
def Trie.getChild {α : Type} (t : Trie α) (c : Nat) : Trie α :=
  getChildList t.children c

/-- The trie node with its child along edge label `c` replaced. -/
def Trie.setChild {α : Type} (t : Trie α) (c : Nat) (child : Trie α) : Trie α :=
  ⟨t.value, setChildList t.children c child⟩

theorem getChildList_setChildList {α : Type} (cs : List (Nat × Trie α))
    (c : Nat) (child : Trie α) :
    getChildList (setChildList cs c child) c = child := by
  induction cs with
  | nil => simp [setChildList, getChildList]
  | cons p rest ih =>
    obtain ⟨k, old⟩ := p
    by_cases h : k = c
    · subst h
      simp [setChildList, getChildList]
    · simp [setChildList, getChildList, h, ih]

theorem Trie.getChild_setChild {α : Type} (t : Trie α) (c : Nat) (child : Trie α) :
    (t.setChild c child).getChild c = child :=
  getChildList_setChildList t.children c child

/-- Look up the entry for a path: follow the edges from the root and read
the node's value. -/
def Trie.lookup {α : Type} : Trie α → List Nat → Option α
  | t, [] => t.value
  | t, c :: cs => Trie.lookup (t.getChild c) cs

/-- Insert an entry: store `v` at the node reached by the path, creating
intermediate nodes as needed. -/
def Trie.insert {α : Type} : Trie α → List Nat → α → Trie α
  | t, [], v => ⟨some v, t.children⟩
  | t, c :: cs, v => t.setChild c (Trie.insert (t.getChild c) cs v)

/-- The draft's statement, with the path authored as the list of edge
labels from the root: after inserting `value` at `path`, looking up
`path` returns `value`. -/
theorem insert_lookup_correctness {α : Type} (trie : Trie α) (path : List Nat)
    (value : α) :
    Trie.lookup (Trie.insert trie path value) path = some value := by
  induction path generalizing trie with
  | nil => rfl
  | cons c cs ih =>
    show Trie.lookup
        (Trie.getChild
          (Trie.setChild trie c (Trie.insert (Trie.getChild trie c) cs value)) c)
        cs = some value
    rw [Trie.getChild_setChild]
    exact ih (Trie.getChild trie c)

/-- Corollary: the statement for the empty trie. -/
theorem lookup_empty_insert {α : Type} (path : List Nat) (value : α) :
    Trie.lookup (Trie.insert Trie.empty path value) path = some value :=
  insert_lookup_correctness _ _ _

end AxiomCode
