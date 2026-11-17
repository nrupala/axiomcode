import Spec
import Tactics

/-!
# B-trees

A B-tree of `Nat` keys in the 2–4 form: every node holds at most 3
keys; a non-root node holds at least 1. An internal node is a list
of (child, separator) pairs (`PairsOf BTree`) together with a
rightmost child, so a node with `p` pairs has `p + 1` children and
`p` keys by construction. Insertion (`BTree.insert`) is bottom-up
with split-on-full: an overflowing leaf or internal node splits
around its median key, which rises into the parent; a root split
grows the tree's height by one.

## Draft defect record (promotion standard: defect + counterexample)

The draft (`lean/drafts/btree_correctness.lean`) did not elaborate:
it imported Mathlib and Aesop (not built in this working copy);
`isBalanced` and `isValidBTree` were written with `:=` and no body,
which is a parse error; `BTree` was a fieldless structure — with no
keys and no children, no B-tree property is expressible over it at
all; and the theorem was left with an unfinished proof placeholder.

The intended claim, `∀ t, isValidBTree t → isBalanced t`, is
vacuous as stated: with both predicates undefined over a fieldless
type it constrains nothing, so there is no content to preserve
literally. The claim it points at is the standard B-tree theorem —
validity implies balance — and that is what is proved here.

## Repair (shape preserved)

Validity (`BTree.isValid`, with `BTree.pairsValid` threading the
range bounds through a node's pairs) is authored to carry the
B-tree invariants: leaf key lists strictly sorted, key counts
between the minimum (0 for a root, 1 otherwise) and the capacity
3, every key within its range bounds, 1 to 3 pairs at an internal
node, and all children of equal height. The draft's headline is
carried as `BTree.valid_isBalanced`: in a valid tree every leaf
sits at depth equal to the tree's height (`BTree.isBalanced`, the
draft's predicate name, now a real definition via leaf depths).
The bundle keeping the draft's theorem name is
`btree_correctness`.

## What is proved

- Bounds: every key of a valid tree lies in range
  (`BTree.bvalid_bounds`, `BTree.pairsValid_bounds`); the contents
  of a valid tree are strictly sorted (`BTree.bvalid_pairwise`).
- Search (`BTree.search`) is sound and complete against the
  inorder contents on valid trees (`BTree.search_eq_true_iff`).
- Insertion's contents are exactly the inserted key adjoined
  (`BTree.mem_insert`, no hypotheses), via the contents behaviour
  of both split operations (`BTree.leafSplit_mem`,
  `BTree.nodeSplit_mem`).
- Insertion preserves validity in full split-on-full form
  (`BTree.isValid_insert`, from `ins_valid_joint` and
  `BTree.leafSplit_valid`): an in-range key inserted into a valid
  tree yields a valid tree of the same height, or of height one
  more when the root splits; the two halves of a split are valid
  under the bounds tightened by the rising median.
- The measure inductions run on a house size function
  (`BTree.tsize` / `BTree.psize`) so every equation used is
  available verbatim.
-/

namespace AxiomCode

/-- A list of (child, separator) pairs over an arbitrary child
type: the shape of an internal node's contents. Kept as its own
parameterised inductive (rather than a mutual family member) so
that ordinary induction over pair lists is available. -/
inductive PairsOf (α : Type) where
  | nil : PairsOf α
  | cons (c : α) (k : Nat) (rest : PairsOf α) : PairsOf α

/-- A B-tree of `Nat` keys with capacity 3: every node holds at most
3 keys. The pair list carries (child, separator) pairs; with the
rightmost child `last`, a node with `p` pairs has `p + 1` children
and `p` keys — the B-tree arity law holds by construction. -/
inductive BTree where
  | leaf (ks : List Nat) : BTree
  | node (ps : PairsOf BTree) (last : BTree) : BTree

/-- The (child, separator) pairs of a B-tree node. -/
abbrev BPairs := PairsOf BTree

/-- The number of (child, separator) pairs — the key count of an
internal node. -/
def BPairs.length : BPairs → Nat
  | .nil => 0
  | .cons _ _ rest => BPairs.length rest + 1

/-- The child subtrees carried by a pair list, left to right. -/
def BPairs.children : BPairs → List BTree
  | .nil => []
  | .cons c _ rest => c :: BPairs.children rest

/-- The height of a B-tree: leaves have height 0; an internal node's
height is its rightmost child's height plus one (validity forces
all children to share it). -/
def BTree.height : BTree → Nat
  | .leaf _ => 0
  | .node _ last => BTree.height last + 1

mutual
/-- The inorder contents: a leaf's keys; at a node, each child's
contents followed by its separator, ending with the last child. -/
def BTree.contents : BTree → List Nat
  | .leaf ks => ks
  | .node ps last => BTree.contentsPairs ps last
termination_by t => sizeOf t

/-- The contents contributed by a pair list together with the
rightmost child. -/
def BTree.contentsPairs : BPairs → BTree → List Nat
  | .nil, last => BTree.contents last
  | .cons c k rest, last =>
    BTree.contents c ++ k :: BTree.contentsPairs rest last
termination_by ps last => sizeOf ps + sizeOf last
end

mutual
/-- A custom size measure for B-trees (the measure for the
well-founded inductions below; kept house-defined so its equations
are available verbatim). A leaf counts 1. -/
def BTree.tsize : BTree → Nat
  | .leaf _ => 1
  | .node ps last => BTree.psize ps + BTree.tsize last + 1
termination_by t => sizeOf t

/-- The size contributed by a pair list. -/
def BTree.psize : BPairs → Nat
  | .nil => 1
  | .cons c _ rest => BTree.tsize c + BTree.psize rest + 1
termination_by ps => sizeOf ps
end

theorem BTree.psize_pos : ∀ (ps : BPairs), 1 ≤ BTree.psize ps
  | .nil => by simp [BTree.psize]
  | .cons c _ rest => by
    have ih := BTree.psize_pos rest
    simp only [BTree.psize]
    omega

theorem BTree.tsize_pos (t : BTree) : 1 ≤ BTree.tsize t := by
  cases t with
  | leaf ks => simp [BTree.tsize]
  | node ps last =>
    have h := BTree.psize_pos ps
    simp only [BTree.tsize]
    omega

instance : Membership Nat BTree where
  mem t x := x ∈ BTree.contents t

theorem BTree.mem_def {x : Nat} {t : BTree} :
    x ∈ t ↔ x ∈ BTree.contents t := Iff.rfl

mutual
/-- The depths of all leaves of `t`, where the root sits at depth
`d`. -/
def BTree.leafDepthsAt : BTree → Nat → List Nat
  | .leaf _, d => [d]
  | .node ps last, d => BTree.leafDepthsPairs ps last (d + 1)
termination_by t _ => sizeOf t

/-- The leaf depths contributed by a pair list and the rightmost
child, at child depth `d`. -/
def BTree.leafDepthsPairs : BPairs → BTree → Nat → List Nat
  | .nil, last, d => BTree.leafDepthsAt last d
  | .cons c _ rest, last, d =>
    BTree.leafDepthsAt c d ++ BTree.leafDepthsPairs rest last d
termination_by ps last _ => sizeOf ps + sizeOf last
end

/-- The depths of all leaves, the root at depth 0. -/
def BTree.leafDepths (t : BTree) : List Nat := BTree.leafDepthsAt t 0

/-- The balance predicate of the repaired draft claim: every leaf
sits at depth equal to the tree's height — uniform leaf depth. -/
def BTree.isBalanced (t : BTree) : Prop :=
  ∀ d ∈ BTree.leafDepths t, d = BTree.height t

/-- Range discipline: `x` lies strictly between the optional bounds
`lo` and `hi`. -/
def InRange (lo hi : Option Nat) (x : Nat) : Prop :=
  (∀ a, lo = some a → a < x) ∧ (∀ b, hi = some b → x < b)

theorem inRange_none_none (x : Nat) : InRange none none x := by
  unfold InRange
  constructor
  · intro a h
    cases h
  · intro b h
    cases h

theorem InRange.lo_lt {hi : Option Nat} {a x : Nat}
    (h : InRange (some a) hi x) : a < x := h.1 a rfl

theorem InRange.lt_hi {lo : Option Nat} {b x : Nat}
    (h : InRange lo (some b) x) : x < b := h.2 b rfl

theorem inRange_trans_hi {lo hi : Option Nat} {k m : Nat}
    (hm : InRange lo (some k) m) (hk : InRange lo hi k) :
    InRange lo hi m :=
  ⟨hm.1, fun b hb => by
    have h1 : m < k := hm.2 k rfl
    have h2 : k < b := hk.2 b hb
    omega⟩

theorem inRange_trans_lo {lo hi : Option Nat} {k m : Nat}
    (hm : InRange (some k) hi m) (hk : InRange lo hi k) :
    InRange lo hi m :=
  ⟨fun a ha => by
    have h1 : a < k := hk.1 a ha
    have h2 : k < m := hm.1 k rfl
    omega, hm.2⟩

theorem inRange_some_lo_of_lt {lo hi : Option Nat} {k m : Nat}
    (hk : InRange lo hi k) (h : m < k) : InRange (some m) hi k :=
  ⟨fun a ha => by cases ha; exact h, hk.2⟩

theorem inRange_some_hi_of_lt {lo hi : Option Nat} {k m : Nat}
    (hm : InRange lo hi m) (h : m < k) : InRange lo (some k) m :=
  ⟨hm.1, fun b hb => by cases hb; exact h⟩

mutual
/-- Validity of a pair list together with its rightmost child,
under bounds `lo`/`hi`: each pair's child is a valid non-root tree
under the bounds tightened by its separator, each separator lies
in range, and the rightmost child is valid under the final bounds.
Children use minimum key count 1. -/
def BTree.pairsValid (lo hi : Option Nat) : BPairs → BTree → Prop
  | .nil, last => BTree.isValid 1 lo hi last
  | .cons c k rest, last =>
    BTree.isValid 1 lo (some k) c ∧ InRange lo hi k ∧
      BTree.pairsValid (some k) hi rest last
termination_by ps last => sizeOf ps + sizeOf last

/-- B-tree validity at minimum key count `minK` (0 for a root, 1 for
any other tree) under bounds `lo`/`hi`: a leaf's keys are strictly
sorted, number between `minK` and the capacity 3, and all lie in
range; an internal node has 1 to 3 pairs, a valid pair list, and
all children of equal height. -/
def BTree.isValid (minK : Nat) (lo hi : Option Nat) : BTree → Prop
  | .leaf ks =>
    List.Pairwise (· < ·) ks ∧ minK ≤ ks.length ∧ ks.length ≤ 3 ∧
      ∀ x ∈ ks, InRange lo hi x
  | .node ps last =>
    1 ≤ BPairs.length ps ∧ BPairs.length ps ≤ 3 ∧
      BTree.pairsValid lo hi ps last ∧
      ∀ c ∈ BPairs.children ps, BTree.height c = BTree.height last
termination_by t => sizeOf t
end

/-- Bounds, measure form: in a valid tree every content key lies in
range. Induction on the height bound; the pair list is handled by an
inner induction, using that validity forces all children to the
rightmost child's height. -/
theorem bvalid_bounds_aux : ∀ (n : Nat) {minK : Nat} {lo hi : Option Nat}
    {t : BTree}, BTree.height t ≤ n → BTree.isValid minK lo hi t →
    ∀ y ∈ BTree.contents t, InRange lo hi y := by
  intro n
  induction n with
  | zero =>
    intro minK lo hi t hh hv y hy
    cases t with
    | leaf ks =>
      simp only [BTree.isValid] at hv
      simp only [BTree.contents] at hy
      exact hv.2.2.2 y hy
    | node ps last =>
      simp only [BTree.height] at hh
      omega
  | succ n ih =>
    intro minK lo hi t hh hv y hy
    cases t with
    | leaf ks =>
      simp only [BTree.isValid] at hv
      simp only [BTree.contents] at hy
      exact hv.2.2.2 y hy
    | node ps last =>
      simp only [BTree.isValid] at hv
      obtain ⟨h1, h2, hpv, huni⟩ := hv
      simp only [BTree.height] at hh
      simp only [BTree.contents] at hy
      have key : ∀ (lo : Option Nat) (ps : BPairs),
          BTree.pairsValid lo hi ps last →
          (∀ c ∈ BPairs.children ps, BTree.height c = BTree.height last) →
          ∀ y ∈ BTree.contentsPairs ps last, InRange lo hi y := by
        intro lo ps
        induction ps generalizing lo with
        | nil =>
          intro hpv huni y hy
          simp only [BTree.pairsValid] at hpv
          simp only [BTree.contentsPairs] at hy
          exact ih (by omega) hpv y hy
        | cons c k rest ihp =>
          intro hpv huni y hy
          simp only [BTree.pairsValid] at hpv
          obtain ⟨hc, hk, hrest⟩ := hpv
          simp only [BTree.contentsPairs, List.mem_append, List.mem_cons] at hy
          have hc_h : BTree.height c ≤ n := by
            have hcu := huni c (by
              simp only [BPairs.children]; exact List.mem_cons_self)
            omega
          have huni' : ∀ c' ∈ BPairs.children rest,
              BTree.height c' = BTree.height last :=
            fun c' hc' => huni c' (by
              simp only [BPairs.children]
              exact List.mem_cons_of_mem c hc')
          rcases hy with hy | rfl | hy
          · exact inRange_trans_hi (ih hc_h hc y hy) hk
          · exact hk
          · exact inRange_trans_lo (ihp (some k) hrest huni' y hy) hk
      exact key lo ps hpv huni y hy

/-- Bounds: in a valid tree, every content key lies in range. -/
theorem BTree.bvalid_bounds {minK : Nat} {lo hi : Option Nat} {t : BTree}
    (hv : BTree.isValid minK lo hi t) :
    ∀ y ∈ BTree.contents t, InRange lo hi y :=
  bvalid_bounds_aux (BTree.height t) (Nat.le_refl _) hv

/-- Bounds for a pair list: every key in the contributed contents
lies in range. -/
theorem BTree.pairsValid_bounds {lo hi : Option Nat} (ps : BPairs)
    (last : BTree) (hpv : BTree.pairsValid lo hi ps last) :
    ∀ y ∈ BTree.contentsPairs ps last, InRange lo hi y := by
  induction ps generalizing lo with
  | nil =>
    intro y hy
    simp only [BTree.pairsValid] at hpv
    simp only [BTree.contentsPairs] at hy
    exact BTree.bvalid_bounds hpv y hy
  | cons c k rest ihp =>
    intro y hy
    simp only [BTree.pairsValid] at hpv
    obtain ⟨hc, hk, hrest⟩ := hpv
    simp only [BTree.contentsPairs, List.mem_append, List.mem_cons] at hy
    rcases hy with hy | rfl | hy
    · exact inRange_trans_hi (BTree.bvalid_bounds hc y hy) hk
    · exact hk
    · exact inRange_trans_lo (ihp hrest y hy) hk

/-- Uniform leaf depth, measure form: in a valid tree every leaf
sits at depth `height t` (counted from depth `e`). -/
theorem bvalid_leafDepths_aux : ∀ (n : Nat) {minK : Nat} {lo hi : Option Nat}
    {t : BTree}, BTree.height t ≤ n → BTree.isValid minK lo hi t →
    ∀ e, ∀ d ∈ BTree.leafDepthsAt t e, d = BTree.height t + e := by
  intro n
  induction n with
  | zero =>
    intro minK lo hi t hh hv e d hd
    cases t with
    | leaf ks =>
      simp only [BTree.leafDepthsAt, List.mem_singleton] at hd
      subst hd
      simp only [BTree.height, Nat.zero_add]
    | node ps last =>
      simp only [BTree.height] at hh
      omega
  | succ n ih =>
    intro minK lo hi t hh hv e d hd
    cases t with
    | leaf ks =>
      simp only [BTree.leafDepthsAt, List.mem_singleton] at hd
      subst hd
      simp only [BTree.height, Nat.zero_add]
    | node ps last =>
      simp only [BTree.isValid] at hv
      obtain ⟨h1, h2, hpv, huni⟩ := hv
      simp only [BTree.height] at hh
      simp only [BTree.leafDepthsAt] at hd
      have key : ∀ (lo : Option Nat) (ps : BPairs),
          BTree.pairsValid lo hi ps last →
          (∀ c ∈ BPairs.children ps, BTree.height c = BTree.height last) →
          ∀ d ∈ BTree.leafDepthsPairs ps last (e + 1),
            d = BTree.height last + (e + 1) := by
        intro lo ps
        induction ps generalizing lo with
        | nil =>
          intro hpv huni d hd
          simp only [BTree.pairsValid] at hpv
          simp only [BTree.leafDepthsPairs] at hd
          exact ih (by omega) hpv (e + 1) d hd
        | cons c k rest ihp =>
          intro hpv huni d hd
          simp only [BTree.pairsValid] at hpv
          obtain ⟨hc, hk, hrest⟩ := hpv
          simp only [BTree.leafDepthsPairs, List.mem_append] at hd
          have hcu := huni c (by
            simp only [BPairs.children]; exact List.mem_cons_self)
          have huni' : ∀ c' ∈ BPairs.children rest,
              BTree.height c' = BTree.height last :=
            fun c' hc' => huni c' (by
              simp only [BPairs.children]
              exact List.mem_cons_of_mem c hc')
          rcases hd with hd | hd
          · have hcd := ih (by omega) hc (e + 1) d hd
            omega
          · exact ihp (some k) hrest huni' d hd
      have hfin := key lo ps hpv huni d hd
      simp only [BTree.height]
      omega

/-- The repaired headline: validity implies balance — every leaf of
a valid B-tree sits at the same depth, the tree's height. -/
theorem BTree.valid_isBalanced {minK : Nat} {lo hi : Option Nat}
    {t : BTree} (hv : BTree.isValid minK lo hi t) :
    BTree.isBalanced t := by
  intro d hd
  have h := bvalid_leafDepths_aux (BTree.height t) (Nat.le_refl _) hv 0 d hd
  simpa using h

/-- Ordering, measure form: the contents of a valid tree are
strictly sorted. -/
theorem bvalid_pairwise_aux : ∀ (n : Nat) {minK : Nat} {lo hi : Option Nat}
    {t : BTree}, BTree.height t ≤ n → BTree.isValid minK lo hi t →
    List.Pairwise (· < ·) (BTree.contents t) := by
  intro n
  induction n with
  | zero =>
    intro minK lo hi t hh hv
    cases t with
    | leaf ks =>
      simp only [BTree.isValid] at hv
      simp only [BTree.contents]
      exact hv.1
    | node ps last =>
      simp only [BTree.height] at hh
      omega
  | succ n ih =>
    intro minK lo hi t hh hv
    cases t with
    | leaf ks =>
      simp only [BTree.isValid] at hv
      simp only [BTree.contents]
      exact hv.1
    | node ps last =>
      simp only [BTree.isValid] at hv
      obtain ⟨h1, h2, hpv, huni⟩ := hv
      simp only [BTree.height] at hh
      simp only [BTree.contents]
      have key : ∀ (lo : Option Nat) (ps : BPairs),
          BTree.pairsValid lo hi ps last →
          (∀ c ∈ BPairs.children ps, BTree.height c = BTree.height last) →
          List.Pairwise (· < ·) (BTree.contentsPairs ps last) := by
        intro lo ps
        induction ps generalizing lo with
        | nil =>
          intro hpv huni
          simp only [BTree.pairsValid] at hpv
          simp only [BTree.contentsPairs]
          exact ih (by omega) hpv
        | cons c k rest ihp =>
          intro hpv huni
          simp only [BTree.pairsValid] at hpv
          obtain ⟨hc, hk, hrest⟩ := hpv
          simp only [BTree.contentsPairs]
          rw [List.pairwise_append]
          have hc_h : BTree.height c ≤ n := by
            have hcu := huni c (by
              simp only [BPairs.children]; exact List.mem_cons_self)
            omega
          have huni' : ∀ c' ∈ BPairs.children rest,
              BTree.height c' = BTree.height last :=
            fun c' hc' => huni c' (by
              simp only [BPairs.children]
              exact List.mem_cons_of_mem c hc')
          refine ⟨ih hc_h hc, ?_, ?_⟩
          · rw [List.pairwise_cons]
            refine ⟨?_, ihp (some k) hrest huni'⟩
            intro y hy
            have hyb := BTree.pairsValid_bounds rest last hrest y hy
            exact hyb.lo_lt
          · intro a ha b hb
            have hab := BTree.bvalid_bounds hc a ha
            rw [List.mem_cons] at hb
            rcases hb with rfl | hb
            · exact hab.lt_hi
            · have hbb := BTree.pairsValid_bounds rest last hrest b hb
              have hlt1 : a < k := hab.lt_hi
              have hlt2 : k < b := hbb.lo_lt
              omega
      exact key lo ps hpv huni

/-- Ordering: the contents of a valid tree are strictly sorted. -/
theorem BTree.bvalid_pairwise {minK : Nat} {lo hi : Option Nat} {t : BTree}
    (hv : BTree.isValid minK lo hi t) :
    List.Pairwise (· < ·) (BTree.contents t) :=
  bvalid_pairwise_aux (BTree.height t) (Nat.le_refl _) hv

/-- Membership search in a key list. -/
def listSearch : List Nat → Nat → Bool
  | [], _ => false
  | a :: ks, x => if x = a then true else listSearch ks x

theorem listSearch_eq_true_iff {ks : List Nat} {x : Nat} :
    listSearch ks x = true ↔ x ∈ ks := by
  induction ks with
  | nil => simp [listSearch]
  | cons a ks ih =>
    by_cases h : x = a
    · subst h
      simp [listSearch]
    · simp [listSearch, h, ih]

mutual
/-- B-tree search: at a leaf, look in the key list; at a node,
compare against each separator in turn — equal means found,
smaller means descend into that pair's child, larger means move
to the next pair; the last pair's larger side is the rightmost
child. -/
def BTree.search : BTree → Nat → Bool
  | .leaf ks, x => listSearch ks x
  | .node ps last, x => BTree.searchPairs ps last x
termination_by t _ => sizeOf t

/-- Search within a pair list and its rightmost child. -/
def BTree.searchPairs : BPairs → BTree → Nat → Bool
  | .nil, last, x => BTree.search last x
  | .cons c k rest, last, x =>
    if x = k then true
    else if x < k then BTree.search c x
    else BTree.searchPairs rest last x
termination_by ps last _ => sizeOf ps + sizeOf last
end

/-- Search correctness, joint measure form: the tree statement and
the pair-list statement proved together by induction on the size
bound — each descends into strictly smaller components (a child, or
the tail pair list with the same rightmost child). Exclusion of the
subtree not descended into is by the bounds lemmas. -/
theorem search_joint : ∀ (n : Nat),
    (∀ {minK : Nat} {lo hi : Option Nat} {t : BTree},
      BTree.tsize t ≤ n → BTree.isValid minK lo hi t →
      ∀ x, BTree.search t x = true ↔ x ∈ BTree.contents t) ∧
    (∀ {lo hi : Option Nat} (ps : BPairs) (last : BTree),
      BTree.psize ps + BTree.tsize last ≤ n →
      BTree.pairsValid lo hi ps last →
      ∀ x, BTree.searchPairs ps last x = true ↔
        x ∈ BTree.contentsPairs ps last) := by
  intro n
  induction n with
  | zero =>
    constructor
    · intro minK lo hi t hh hv x
      have hpos := BTree.tsize_pos t
      omega
    · intro lo hi ps last hh hpv x
      have h1 := BTree.psize_pos ps
      have h2 := BTree.tsize_pos last
      omega
  | succ n ih =>
    obtain ⟨ih1, ih2⟩ := ih
    have key2 : ∀ {lo hi : Option Nat} (ps : BPairs) (last : BTree),
        BTree.psize ps + BTree.tsize last ≤ n + 1 →
        BTree.pairsValid lo hi ps last →
        ∀ x, BTree.searchPairs ps last x = true ↔
          x ∈ BTree.contentsPairs ps last := by
      intro lo hi ps last hh hpv x
      cases ps with
      | nil =>
        simp only [BTree.pairsValid] at hpv
        simp only [BTree.searchPairs, BTree.contentsPairs]
        refine ih1 (t := last) (minK := 1) ?_ hpv x
        simp only [BTree.psize] at hh
        omega
      | cons c k rest =>
        simp only [BTree.pairsValid] at hpv
        obtain ⟨hc, hk, hrest⟩ := hpv
        simp only [BTree.psize] at hh
        by_cases h1 : x = k
        · subst h1
          simp [BTree.searchPairs, BTree.contentsPairs]
        · by_cases h2 : x < k
          · have hs : BTree.searchPairs (.cons c k rest) last x =
                BTree.search c x := by
              simp only [BTree.searchPairs, h1, h2, ite_true, ite_false]
            rw [hs]
            refine (ih1 (t := c) (minK := 1) ?_ hc x).trans ?_
            · have hcpos := BTree.tsize_pos c
              have hrpos := BTree.psize_pos rest
              omega
            · constructor
              · intro hx
                simp only [BTree.contentsPairs, List.mem_append,
                  List.mem_cons]
                exact Or.inl hx
              · intro hx
                simp only [BTree.contentsPairs, List.mem_append,
                  List.mem_cons] at hx
                rcases hx with hx | rfl | hx
                · exact hx
                · exact absurd rfl h1
                · have hxb := BTree.pairsValid_bounds rest last hrest x hx
                  have hlt : k < x := hxb.lo_lt
                  omega
          · have hs : BTree.searchPairs (.cons c k rest) last x =
                BTree.searchPairs rest last x := by
              simp only [BTree.searchPairs, h1, h2, ite_true, ite_false]
            rw [hs]
            refine (ih2 rest last ?_ hrest x).trans ?_
            · have hcpos := BTree.tsize_pos c
              omega
            · constructor
              · intro hx
                simp only [BTree.contentsPairs, List.mem_append,
                  List.mem_cons]
                exact Or.inr (Or.inr hx)
              · intro hx
                simp only [BTree.contentsPairs, List.mem_append,
                  List.mem_cons] at hx
                rcases hx with hx | rfl | hx
                · have hxb := BTree.bvalid_bounds hc x hx
                  have hlt : x < k := hxb.lt_hi
                  omega
                · exact absurd rfl h1
                · exact hx
    refine ⟨?_, key2⟩
    intro minK lo hi t hh hv x
    cases t with
    | leaf ks =>
      simp only [BTree.isValid] at hv
      simp only [BTree.search, BTree.contents]
      exact listSearch_eq_true_iff
    | node ps last =>
      simp only [BTree.isValid] at hv
      obtain ⟨h1, h2, hpv, huni⟩ := hv
      simp only [BTree.search, BTree.contents]
      refine key2 ps last ?_ hpv x
      simp only [BTree.tsize] at hh
      omega

/-- Search correctness: on a valid tree, search finds exactly the
keys in the contents. -/
theorem BTree.search_eq_true_iff {minK : Nat} {lo hi : Option Nat}
    {t : BTree} (hv : BTree.isValid minK lo hi t) (x : Nat) :
    BTree.search t x = true ↔ x ∈ BTree.contents t :=
  (search_joint (BTree.tsize t)).1 (Nat.le_refl _) hv x

/-- Ordered insertion into a key list: the key is placed at its
sorted position; inserting an existing key changes nothing. -/
def insertKey (x : Nat) : List Nat → List Nat
  | [] => [x]
  | a :: ks =>
    if x = a then a :: ks
    else if x < a then x :: a :: ks
    else a :: insertKey x ks

theorem mem_insertKey {x y : Nat} {ks : List Nat} :
    y ∈ insertKey x ks ↔ y = x ∨ y ∈ ks := by
  induction ks with
  | nil => simp [insertKey]
  | cons a ks ih =>
    by_cases h1 : x = a
    · subst h1
      simp [insertKey]
    · by_cases h2 : x < a
      · simp [insertKey, h1, h2]
      · simp only [insertKey, h1, h2, ite_true, ite_false, List.mem_cons, ih]
        constructor <;> intro h <;> rcases h with h | h | h <;>
          first
            | exact Or.inl h
            | exact Or.inr (Or.inl h)
            | exact Or.inr (Or.inr h)

theorem pairwise_insertKey {x : Nat} {ks : List Nat}
    (h : List.Pairwise (· < ·) ks) :
    List.Pairwise (· < ·) (insertKey x ks) := by
  induction ks with
  | nil => simp [insertKey]
  | cons a ks ih =>
    rw [List.pairwise_cons] at h
    obtain ⟨ha, hks⟩ := h
    by_cases h1 : x = a
    · subst h1
      have hins : insertKey x (x :: ks) = x :: ks := by
        simp [insertKey]
      rw [hins]
      exact List.pairwise_cons.mpr ⟨ha, hks⟩
    · by_cases h2 : x < a
      · simp only [insertKey, h1, h2, ite_true, ite_false]
        rw [List.pairwise_cons]
        refine ⟨?_, List.pairwise_cons.mpr ⟨ha, hks⟩⟩
        intro y hy
        rw [List.mem_cons] at hy
        rcases hy with rfl | hy
        · exact h2
        · have hay := ha y hy
          omega
      · simp only [insertKey, h1, h2, ite_true, ite_false]
        rw [List.pairwise_cons]
        refine ⟨?_, ih hks⟩
        intro y hy
        have hy2 : y = x ∨ y ∈ ks := mem_insertKey.mp hy
        rcases hy2 with rfl | hy2
        · omega
        · exact ha y hy2

theorem length_insertKey_le {x : Nat} {ks : List Nat} :
    (insertKey x ks).length ≤ ks.length + 1 := by
  induction ks with
  | nil => simp [insertKey]
  | cons a ks ih =>
    by_cases h1 : x = a
    · subst h1
      simp [insertKey]
    · by_cases h2 : x < a
      · simp [insertKey, h1, h2]
      · simp only [insertKey, h1, h2, ite_true, ite_false, List.length_cons]
        omega

theorem length_insertKey_ge {x : Nat} {ks : List Nat} :
    ks.length ≤ (insertKey x ks).length := by
  induction ks with
  | nil => simp [insertKey]
  | cons a ks ih =>
    by_cases h1 : x = a
    · subst h1
      simp [insertKey]
    · by_cases h2 : x < a
      · simp [insertKey, h1, h2]
      · simp only [insertKey, h1, h2, ite_true, ite_false, List.length_cons]
        omega

/-- The result of inserting into a subtree: either a finished tree
(`ok`), or a `split` — two valid trees and the median key that must
rise into the parent. -/
inductive Ins where
  | ok (t : BTree) : Ins
  | split (l : BTree) (m : Nat) (r : BTree) : Ins

/-- Splitting a full leaf: four sorted keys `a < b < c < d` become
`[a]`, the rising median `b`, and `[c, d]`. Any other shape is the
identity (never used: splitting is only invoked at length 4). -/
def BTree.leafSplit (ks : List Nat) : Ins :=
  match ks with
  | [a, b, c, d] => .split (.leaf [a]) b (.leaf [c, d])
  | _ => .ok (.leaf ks)

/-- Insert into a leaf: ordered-insert the key; if the leaf
overflows (4 keys), split it. -/
def BTree.insLeaf (x : Nat) (ks : List Nat) : Ins :=
  let ks' := insertKey x ks
  if ks'.length ≤ 3 then .ok (.leaf ks') else BTree.leafSplit ks'

/-- Splitting a full internal node: four pairs
`(c0,k0) (c1,k1) (c2,k2) (c3,k3)` with rightmost child `last`
become the left node `(c0,k0)` with rightmost `c1`, the rising
median `k1`, and the right node `(c2,k2) (c3,k3)` with rightmost
`last`. Any other shape is the identity (never used: splitting is
only invoked at 4 pairs). -/
def BTree.nodeSplit (ps : BPairs) (last : BTree) : Ins :=
  match ps with
  | .cons c0 k0 (.cons c1 k1 (.cons c2 k2 (.cons c3 k3 .nil))) =>
    .split (.node (.cons c0 k0 .nil) c1) k1
      (.node (.cons c2 k2 (.cons c3 k3 .nil)) last)
  | _ => .ok (.node ps last)

mutual
/-- Insertion into a subtree, returning an `Ins`. At a node, the
pair list absorbs a child split by growing one pair; if it reaches
4 pairs the node itself splits. -/
def BTree.ins (x : Nat) : BTree → Ins
  | .leaf ks => BTree.insLeaf x ks
  | .node ps last =>
    let (ps', last') := BTree.insPairs x ps last
    if BPairs.length ps' ≤ 3 then .ok (.node ps' last')
    else BTree.nodeSplit ps' last'
termination_by t => sizeOf t

/-- Insertion into a pair list and its rightmost child: the result
pair list (with the rightmost child) has the same contents as the
original plus the inserted key; a split of the child descended
into is absorbed as one extra pair. -/
def BTree.insPairs (x : Nat) : BPairs → BTree → BPairs × BTree
  | .nil, last =>
    match BTree.ins x last with
    | .ok t' => (.nil, t')
    | .split l m r => (.cons l m .nil, r)
  | .cons c k rest, last =>
    if x = k then (.cons c k rest, last)
    else if x < k then
      match BTree.ins x c with
      | .ok c' => (.cons c' k rest, last)
      | .split l m r => (.cons l m (.cons r k rest), last)
    else
      let (ps', last') := BTree.insPairs x rest last
      (.cons c k ps', last')
termination_by ps last => sizeOf ps + sizeOf last
end

/-- B-tree insertion: insert into the root; if the root splits,
grow a new root of height one more. -/
def BTree.insert (x : Nat) (t : BTree) : BTree :=
  match BTree.ins x t with
  | .ok t' => t'
  | .split l m r => .node (.cons l m .nil) r

/-- Membership in a pair list's contents, one pair unfolded. -/
theorem BTree.mem_contentsPairs_cons {c : BTree} {k : Nat} {rest : BPairs}
    {last : BTree} {y : Nat} :
    y ∈ BTree.contentsPairs (.cons c k rest) last ↔
      y ∈ BTree.contents c ∨ y = k ∨ y ∈ BTree.contentsPairs rest last := by
  simp [BTree.contentsPairs, List.mem_append, List.mem_cons]

/-- The contents behaviour of `leafSplit`: a split's two leaves and
rising key hold exactly the original list's keys; a non-split
(fallback) result is the leaf itself. -/
theorem BTree.leafSplit_mem : ∀ (ks : List Nat),
    (∀ t', BTree.leafSplit ks = .ok t' →
      ∀ y, y ∈ BTree.contents t' ↔ y ∈ ks) ∧
    (∀ l m r, BTree.leafSplit ks = .split l m r →
      ∀ y, (y ∈ BTree.contents l ∨ y = m ∨ y ∈ BTree.contents r) ↔ y ∈ ks)
  | [] => by
    constructor
    · intro t' ht' y
      simp only [BTree.leafSplit] at ht'
      cases ht'
      simp [BTree.contents]
    · intro l m r ht'
      simp only [BTree.leafSplit] at ht'
      cases ht'
  | [a] => by
    constructor
    · intro t' ht' y
      simp only [BTree.leafSplit] at ht'
      cases ht'
      simp [BTree.contents]
    · intro l m r ht'
      simp only [BTree.leafSplit] at ht'
      cases ht'
  | [a, b] => by
    constructor
    · intro t' ht' y
      simp only [BTree.leafSplit] at ht'
      cases ht'
      simp [BTree.contents]
    · intro l m r ht'
      simp only [BTree.leafSplit] at ht'
      cases ht'
  | [a, b, c] => by
    constructor
    · intro t' ht' y
      simp only [BTree.leafSplit] at ht'
      cases ht'
      simp [BTree.contents]
    · intro l m r ht'
      simp only [BTree.leafSplit] at ht'
      cases ht'
  | [a, b, c, d] => by
    constructor
    · intro t' ht'
      simp only [BTree.leafSplit] at ht'
      cases ht'
    · intro l m r ht' y
      simp only [BTree.leafSplit] at ht'
      cases ht'
      simp [BTree.contents]
  | a :: b :: c :: d :: e :: rest => by
    constructor
    · intro t' ht' y
      simp only [BTree.leafSplit] at ht'
      cases ht'
      simp [BTree.contents]
    · intro l m r ht'
      simp only [BTree.leafSplit] at ht'
      cases ht'

/-- The contents behaviour of `nodeSplit`: a split's two nodes and
rising key hold exactly the original pair list's contents; a
non-split (fallback) result is the node itself. -/
theorem BTree.nodeSplit_mem : ∀ (ps : BPairs) (last : BTree),
    (∀ t', BTree.nodeSplit ps last = .ok t' →
      ∀ y, y ∈ BTree.contents t' ↔ y ∈ BTree.contentsPairs ps last) ∧
    (∀ l m r, BTree.nodeSplit ps last = .split l m r →
      ∀ y, (y ∈ BTree.contents l ∨ y = m ∨ y ∈ BTree.contents r) ↔
        y ∈ BTree.contentsPairs ps last)
  | .nil, last => by
    constructor
    · intro t' ht' y
      simp only [BTree.nodeSplit] at ht'
      cases ht'
      simp [BTree.contents]
    · intro l m r ht'
      simp only [BTree.nodeSplit] at ht'
      cases ht'
  | .cons c0 k0 .nil, last => by
    constructor
    · intro t' ht' y
      simp only [BTree.nodeSplit] at ht'
      cases ht'
      simp [BTree.contents]
    · intro l m r ht'
      simp only [BTree.nodeSplit] at ht'
      cases ht'
  | .cons c0 k0 (.cons c1 k1 .nil), last => by
    constructor
    · intro t' ht' y
      simp only [BTree.nodeSplit] at ht'
      cases ht'
      simp [BTree.contents]
    · intro l m r ht'
      simp only [BTree.nodeSplit] at ht'
      cases ht'
  | .cons c0 k0 (.cons c1 k1 (.cons c2 k2 .nil)), last => by
    constructor
    · intro t' ht' y
      simp only [BTree.nodeSplit] at ht'
      cases ht'
      simp [BTree.contents]
    · intro l m r ht'
      simp only [BTree.nodeSplit] at ht'
      cases ht'
  | .cons c0 k0 (.cons c1 k1 (.cons c2 k2 (.cons c3 k3 .nil))), last => by
    constructor
    · intro t' ht'
      simp only [BTree.nodeSplit] at ht'
      cases ht'
    · intro l m r ht' y
      simp only [BTree.nodeSplit] at ht'
      cases ht'
      simp only [BTree.contents, BTree.contentsPairs, List.mem_append,
        List.mem_cons]
      aesop
  | .cons c0 k0 (.cons c1 k1 (.cons c2 k2 (.cons c3 k3 (.cons c4 k4 rest)))), last => by
    constructor
    · intro t' ht' y
      simp only [BTree.nodeSplit] at ht'
      cases ht'
      simp [BTree.contents]
    · intro l m r ht'
      simp only [BTree.nodeSplit] at ht'
      cases ht'

/-- Contents of insertion, joint measure form: inserting `x`
adjoins exactly `x` to the contents — stated for `ins` (both
result forms) and for `insPairs` together, by induction on the
size bound. No validity hypothesis: this holds for every tree. -/
theorem ins_mem_joint : ∀ (n : Nat),
    (∀ {t : BTree}, BTree.tsize t ≤ n → ∀ x,
      (∀ t', BTree.ins x t = .ok t' →
        ∀ y, y ∈ BTree.contents t' ↔ y = x ∨ y ∈ BTree.contents t) ∧
      (∀ l m r, BTree.ins x t = .split l m r →
        ∀ y, (y ∈ BTree.contents l ∨ y = m ∨ y ∈ BTree.contents r) ↔
          y = x ∨ y ∈ BTree.contents t)) ∧
    (∀ (ps : BPairs) (last : BTree),
      BTree.psize ps + BTree.tsize last ≤ n → ∀ x,
      ∀ ps' last', BTree.insPairs x ps last = (ps', last') →
        ∀ y, y ∈ BTree.contentsPairs ps' last' ↔
          y = x ∨ y ∈ BTree.contentsPairs ps last) := by
  intro n
  induction n with
  | zero =>
    constructor
    · intro t hh x
      have hpos := BTree.tsize_pos t
      omega
    · intro ps last hh x
      have h1 := BTree.psize_pos ps
      have h2 := BTree.tsize_pos last
      omega
  | succ n ih =>
    obtain ⟨ih1, ih2⟩ := ih
    have key2 : ∀ (ps : BPairs) (last : BTree),
        BTree.psize ps + BTree.tsize last ≤ n + 1 → ∀ x,
        ∀ ps' last', BTree.insPairs x ps last = (ps', last') →
          ∀ y, y ∈ BTree.contentsPairs ps' last' ↔
            y = x ∨ y ∈ BTree.contentsPairs ps last := by
      intro ps last hh x
      cases ps with
      | nil =>
        cases hins : BTree.ins x last with
        | ok t' =>
          intro ps' last' heq y
          have hpair : BTree.insPairs x PairsOf.nil last =
              (PairsOf.nil, t') := by
            simp only [BTree.insPairs, hins]
          rw [hpair] at heq
          cases heq
          simp only [BTree.contentsPairs]
          exact (ih1 (t := last)
            (by simp only [BTree.psize] at hh; omega) x).1 t' hins y
        | split l m r =>
          intro ps' last' heq y
          have hpair : BTree.insPairs x PairsOf.nil last =
              (.cons l m .nil, r) := by
            simp only [BTree.insPairs, hins]
          rw [hpair] at heq
          cases heq
          have hih := (ih1 (t := last)
            (by simp only [BTree.psize] at hh; omega) x).2 l m r hins y
          rw [BTree.mem_contentsPairs_cons]
          simp only [BTree.contentsPairs]
          exact hih
      | cons c k rest =>
        by_cases h1 : x = k
        · intro ps' last' heq y
          have hpair : BTree.insPairs x (.cons c k rest) last =
              (.cons c k rest, last) := by
            simp only [BTree.insPairs, h1, ite_true, ite_false]
          rw [hpair] at heq
          cases heq
          constructor
          · intro hy; exact Or.inr hy
          · intro hy
            rcases hy with rfl | hy
            · rw [BTree.mem_contentsPairs_cons]
              exact Or.inr (Or.inl h1)
            · exact hy
        · by_cases h2 : x < k
          · cases hins : BTree.ins x c with
            | ok c' =>
              intro ps' last' heq y
              have hpair : BTree.insPairs x (.cons c k rest) last =
                  (.cons c' k rest, last) := by
                simp only [BTree.insPairs, h1, h2, hins, ite_true, ite_false]
              rw [hpair] at heq
              cases heq
              have hih := (ih1 (t := c)
                (by simp only [BTree.psize] at hh; omega) x).1 c' hins y
              rw [BTree.mem_contentsPairs_cons,
                BTree.mem_contentsPairs_cons]
              aesop
            | split l m r =>
              intro ps' last' heq y
              have hpair : BTree.insPairs x (.cons c k rest) last =
                  (.cons l m (.cons r k rest), last) := by
                simp only [BTree.insPairs, h1, h2, hins, ite_true, ite_false]
              rw [hpair] at heq
              cases heq
              have hih := (ih1 (t := c)
                (by simp only [BTree.psize] at hh; omega) x).2 l m r hins y
              rw [BTree.mem_contentsPairs_cons,
                BTree.mem_contentsPairs_cons,
                BTree.mem_contentsPairs_cons]
              aesop
          · cases hrec : BTree.insPairs x rest last with
            | mk ps'' last'' =>
              intro ps' last' heq y
              have hpair : BTree.insPairs x (.cons c k rest) last =
                  (.cons c k ps'', last'') := by
                simp only [BTree.insPairs, h1, h2, hrec, ite_true, ite_false]
              rw [hpair] at heq
              cases heq
              have hih := ih2 rest last
                (by simp only [BTree.psize] at hh; omega) x ps'' last'' hrec y
              rw [BTree.mem_contentsPairs_cons,
                BTree.mem_contentsPairs_cons]
              aesop
    refine ⟨?_, key2⟩
    intro t hh x
    cases t with
    | leaf ks =>
      have hins : BTree.ins x (.leaf ks) = BTree.insLeaf x ks := by
        simp only [BTree.ins]
      by_cases hlen : (insertKey x ks).length ≤ 3
      · have hok : BTree.insLeaf x ks = .ok (.leaf (insertKey x ks)) := by
          simp only [BTree.insLeaf, hlen, ite_true, ite_false]
        constructor
        · intro t' ht' y
          rw [hins, hok] at ht'
          cases ht'
          simp only [BTree.contents]
          exact mem_insertKey
        · intro l m r ht' y
          rw [hins, hok] at ht'
          cases ht'
      · have hsp : BTree.insLeaf x ks =
            BTree.leafSplit (insertKey x ks) := by
          simp only [BTree.insLeaf, hlen, ite_true, ite_false]
        obtain ⟨hok, hsplit⟩ := BTree.leafSplit_mem (insertKey x ks)
        constructor
        · intro t' ht' y
          rw [hins, hsp] at ht'
          simp only [BTree.contents]
          exact (hok t' ht' y).trans mem_insertKey
        · intro l m r ht' y
          rw [hins, hsp] at ht'
          simp only [BTree.contents]
          exact (hsplit l m r ht' y).trans mem_insertKey
    | node ps last =>
      cases hrec : BTree.insPairs x ps last with
      | mk ps' last' =>
        have hih := key2 ps last
          (by simp only [BTree.tsize] at hh; omega) x ps' last' hrec
        by_cases hlen : BPairs.length ps' ≤ 3
        · have hins : BTree.ins x (.node ps last) = .ok (.node ps' last') := by
            simp only [BTree.ins, hrec, hlen, ite_true, ite_false]
          constructor
          · intro t' ht' y
            rw [hins] at ht'
            cases ht'
            simp only [BTree.contents]
            exact hih y
          · intro l m r ht' y
            rw [hins] at ht'
            cases ht'
        · have hins : BTree.ins x (.node ps last) =
              BTree.nodeSplit ps' last' := by
            simp only [BTree.ins, hrec, hlen, ite_true, ite_false]
          obtain ⟨hok, hsplit⟩ := BTree.nodeSplit_mem ps' last'
          constructor
          · intro t' ht' y
            rw [hins] at ht'
            simp only [BTree.contents]
            exact (hok t' ht' y).trans (hih y)
          · intro l m r ht' y
            rw [hins] at ht'
            simp only [BTree.contents]
            exact (hsplit l m r ht' y).trans (hih y)

/-- Contents of insertion: the keys of `insert x t` are exactly `x`
adjoined to the keys of `t`. No validity hypothesis. -/
theorem BTree.mem_insert (x : Nat) (t : BTree) (y : Nat) :
    y ∈ BTree.contents (BTree.insert x t) ↔
      y = x ∨ y ∈ BTree.contents t := by
  obtain ⟨h1, h2⟩ := (ins_mem_joint (BTree.tsize t)).1 (Nat.le_refl _) x
  cases hins : BTree.ins x t with
  | ok t' =>
    have htop : BTree.insert x t = t' := by
      simp only [BTree.insert, hins]
    rw [htop]
    exact h1 t' hins y
  | split l m r =>
    have htop : BTree.insert x t = .node (.cons l m .nil) r := by
      simp only [BTree.insert, hins]
    rw [htop]
    have hih := h2 l m r hins y
    simp only [BTree.contents, BTree.contentsPairs, List.mem_append,
      List.mem_cons]
    exact hih

/-- The validity behaviour of a leaf split: when `insertKey x ks`
has four keys (so `leafSplit` really splits), the two leaves are
valid non-root trees under the bounds tightened by the rising
median, the median is in range, and both leaves have height 0. -/
theorem BTree.leafSplit_valid {minK : Nat} {lo hi : Option Nat}
    {ks : List Nat} (hpw : List.Pairwise (· < ·) ks)
    (hmin : minK ≤ ks.length) (hmax : ks.length ≤ 3)
    (hrange : ∀ y ∈ ks, InRange lo hi y) (x : Nat) (hx : InRange lo hi x)
    (hlen4 : (insertKey x ks).length = 4) :
    ∀ l m r, BTree.leafSplit (insertKey x ks) = .split l m r →
      BTree.isValid 1 lo (some m) l ∧ InRange lo hi m ∧
      BTree.isValid 1 (some m) hi r ∧
      BTree.height l = 0 ∧ BTree.height r = 0 := by
  have hall : ∀ y ∈ insertKey x ks, InRange lo hi y := by
    intro y hy
    have hy2 := mem_insertKey.mp hy
    rcases hy2 with rfl | hy2
    · exact hx
    · exact hrange y hy2
  have hpw' : List.Pairwise (· < ·) (insertKey x ks) :=
    pairwise_insertKey hpw
  cases hks : insertKey x ks with
  | nil =>
    rw [hks] at hlen4
    simp only [List.length_nil] at hlen4
    omega
  | cons a ks1 =>
    cases ks1 with
    | nil =>
      rw [hks] at hlen4
      simp only [List.length_cons, List.length_nil] at hlen4
      omega
    | cons b ks2 =>
      cases ks2 with
      | nil =>
        rw [hks] at hlen4
        simp only [List.length_cons, List.length_nil] at hlen4
        omega
      | cons c ks3 =>
        cases ks3 with
        | nil =>
          rw [hks] at hlen4
          simp only [List.length_cons, List.length_nil] at hlen4
          omega
        | cons d ks4 =>
          cases ks4 with
          | cons e rest =>
            rw [hks] at hlen4
            simp only [List.length_cons] at hlen4
            omega
          | nil =>
            intro l m r ht'
            simp only [BTree.leafSplit] at ht'
            cases ht'
            rw [hks] at hpw' hall
            have hpw1 := (List.pairwise_cons.mp hpw').1
            have hpw2 := (List.pairwise_cons.mp
              (List.pairwise_cons.mp hpw').2).1
            have hpw3 := (List.pairwise_cons.mp
              (List.pairwise_cons.mp
                (List.pairwise_cons.mp hpw').2).2).1
            have hab : a < b := hpw1 b List.mem_cons_self
            have hbc : b < c := hpw2 c List.mem_cons_self
            have hbd : b < d :=
              hpw2 d (List.mem_cons_of_mem c List.mem_cons_self)
            have hcd : c < d := hpw3 d List.mem_cons_self
            have haR : InRange lo hi a := hall a List.mem_cons_self
            have hbR : InRange lo hi b :=
              hall b (List.mem_cons_of_mem a List.mem_cons_self)
            have hcR : InRange lo hi c :=
              hall c (List.mem_cons_of_mem a
                (List.mem_cons_of_mem b List.mem_cons_self))
            have hdR : InRange lo hi d :=
              hall d (List.mem_cons_of_mem a
                (List.mem_cons_of_mem b
                  (List.mem_cons_of_mem c List.mem_cons_self)))
            refine ⟨?_, hbR, ?_, rfl, rfl⟩
            · simp only [BTree.isValid]
              refine ⟨?_, by simp, by simp, ?_⟩
              · exact List.pairwise_cons.mpr
                  ⟨fun y hy => (List.not_mem_nil hy).elim,
                    List.Pairwise.nil⟩
              · intro y hy
                rw [List.mem_singleton] at hy
                subst hy
                exact inRange_some_hi_of_lt haR hab
            · simp only [BTree.isValid]
              refine ⟨?_, by simp, by simp, ?_⟩
              · exact List.pairwise_cons.mpr ⟨fun y hy => by
                  rw [List.mem_singleton] at hy
                  subst hy
                  exact hcd,
                  List.pairwise_cons.mpr
                    ⟨fun y hy => (List.not_mem_nil hy).elim,
                      List.Pairwise.nil⟩⟩
              · intro y hy
                simp only [List.mem_cons, List.mem_singleton] at hy
                rcases hy with rfl | rfl | hy
                · exact inRange_some_lo_of_lt hcR hbc
                · exact inRange_some_lo_of_lt hdR hbd
                · exact (List.not_mem_nil hy).elim

/-- Validity of insertion, joint measure form: inserting an
in-range key into a valid tree preserves validity. An `ok` result
is valid at the same bounds and height; a `split` result's two
trees are valid non-root trees under the bounds tightened by the
rising median (which is itself in range), at the original height.
The pair-list statement tracks the rightmost child's height, the
uniform-height condition, and the pair count (never shrinks, grows
by at most one). -/
theorem ins_valid_joint : ∀ (n : Nat),
    (∀ {minK : Nat} {lo hi : Option Nat} {t : BTree},
      BTree.tsize t ≤ n → BTree.isValid minK lo hi t →
      ∀ x, InRange lo hi x →
      (∀ t', BTree.ins x t = .ok t' →
        BTree.isValid minK lo hi t' ∧
        BTree.height t' = BTree.height t) ∧
      (∀ l m r, BTree.ins x t = .split l m r →
        BTree.isValid 1 lo (some m) l ∧ InRange lo hi m ∧
        BTree.isValid 1 (some m) hi r ∧
        BTree.height l = BTree.height t ∧
        BTree.height r = BTree.height t)) ∧
    (∀ {lo hi : Option Nat} (ps : BPairs) (last : BTree),
      BTree.psize ps + BTree.tsize last ≤ n →
      BTree.pairsValid lo hi ps last →
      (∀ c ∈ BPairs.children ps, BTree.height c = BTree.height last) →
      ∀ x, InRange lo hi x →
      ∀ ps' last', BTree.insPairs x ps last = (ps', last') →
        BTree.pairsValid lo hi ps' last' ∧
        BTree.height last' = BTree.height last ∧
        (∀ c ∈ BPairs.children ps', BTree.height c = BTree.height last') ∧
        BPairs.length ps ≤ BPairs.length ps' ∧
        BPairs.length ps' ≤ BPairs.length ps + 1) := by
  intro n
  induction n with
  | zero =>
    constructor
    · intro minK lo hi t hh hv x hx
      have hpos := BTree.tsize_pos t
      omega
    · intro lo hi ps last hh hpv huni x hx
      have h1 := BTree.psize_pos ps
      have h2 := BTree.tsize_pos last
      omega
  | succ n ih =>
    obtain ⟨ih1, ih2⟩ := ih
    have key2 : ∀ {lo hi : Option Nat} (ps : BPairs) (last : BTree),
        BTree.psize ps + BTree.tsize last ≤ n + 1 →
        BTree.pairsValid lo hi ps last →
        (∀ c ∈ BPairs.children ps, BTree.height c = BTree.height last) →
        ∀ x, InRange lo hi x →
        ∀ ps' last', BTree.insPairs x ps last = (ps', last') →
          BTree.pairsValid lo hi ps' last' ∧
          BTree.height last' = BTree.height last ∧
          (∀ c ∈ BPairs.children ps',
            BTree.height c = BTree.height last') ∧
          BPairs.length ps ≤ BPairs.length ps' ∧
          BPairs.length ps' ≤ BPairs.length ps + 1 := by
      intro lo hi ps last hh hpv huni x hx
      cases ps with
      | nil =>
        simp only [BTree.pairsValid] at hpv
        cases hins : BTree.ins x last with
        | ok t' =>
          obtain ⟨hv', hh'⟩ := (ih1 (t := last)
            (by simp only [BTree.psize] at hh; omega) hpv x hx).1 t' hins
          intro ps' last' heq
          have hpair : BTree.insPairs x PairsOf.nil last =
              (PairsOf.nil, t') := by
            simp only [BTree.insPairs, hins]
          rw [hpair] at heq
          cases heq
          refine ⟨?_, hh', ?_, Nat.le_refl 0, by simp [BPairs.length]⟩
          · simp only [BTree.pairsValid]
            exact hv'
          · intro c hc
            simp only [BPairs.children] at hc
            exact (List.not_mem_nil hc).elim
        | split l m r =>
          obtain ⟨hl, hm, hr, hhl, hhr⟩ := (ih1 (t := last)
            (by simp only [BTree.psize] at hh; omega) hpv x hx).2 l m r hins
          intro ps' last' heq
          have hpair : BTree.insPairs x PairsOf.nil last =
              (.cons l m .nil, r) := by
            simp only [BTree.insPairs, hins]
          rw [hpair] at heq
          cases heq
          refine ⟨?_, hhr, ?_, by simp [BPairs.length],
            by simp [BPairs.length]⟩
          · simp only [BTree.pairsValid]
            exact ⟨hl, hm, hr⟩
          · intro c hc
            simp only [BPairs.children, List.mem_singleton] at hc
            rw [hc, hhl, hhr]
      | cons c k rest =>
        simp only [BTree.pairsValid] at hpv
        obtain ⟨hc, hk, hrest⟩ := hpv
        have hc_h : BTree.height c = BTree.height last :=
          huni c (by
            simp only [BPairs.children]; exact List.mem_cons_self)
        have huni' : ∀ c' ∈ BPairs.children rest,
            BTree.height c' = BTree.height last :=
          fun c' hc' => huni c' (by
            simp only [BPairs.children]
            exact List.mem_cons_of_mem c hc')
        by_cases h1 : x = k
        · intro ps' last' heq
          have hpair : BTree.insPairs x (.cons c k rest) last =
              (.cons c k rest, last) := by
            simp only [BTree.insPairs, h1, ite_true, ite_false]
          rw [hpair] at heq
          cases heq
          refine ⟨?_, rfl, huni, Nat.le_refl _, by omega⟩
          simp only [BTree.pairsValid]
          exact ⟨hc, hk, hrest⟩
        · by_cases h2 : x < k
          · cases hins : BTree.ins x c with
            | ok c' =>
              obtain ⟨hc', hh'⟩ := (ih1 (t := c)
                (by simp only [BTree.psize] at hh; omega) hc x
                (inRange_some_hi_of_lt hx h2)).1 c' hins
              intro ps' last' heq
              have hpair : BTree.insPairs x (.cons c k rest) last =
                  (.cons c' k rest, last) := by
                simp only [BTree.insPairs, h1, h2, hins, ite_true, ite_false]
              rw [hpair] at heq
              cases heq
              refine ⟨?_, rfl, ?_, ?_, ?_⟩
              · simp only [BTree.pairsValid]
                exact ⟨hc', hk, hrest⟩
              · intro c'' hc''
                simp only [BPairs.children, List.mem_cons] at hc''
                rcases hc'' with rfl | hc''
                · rw [hh', hc_h]
                · exact huni' c'' hc''
              · simp only [BPairs.length]
                exact Nat.le_refl _
              · simp only [BPairs.length]
                omega
            | split l m r =>
              obtain ⟨hl, hm, hr, hhl, hhr⟩ := (ih1 (t := c)
                (by simp only [BTree.psize] at hh; omega) hc x
                (inRange_some_hi_of_lt hx h2)).2 l m r hins
              intro ps' last' heq
              have hpair : BTree.insPairs x (.cons c k rest) last =
                  (.cons l m (.cons r k rest), last) := by
                simp only [BTree.insPairs, h1, h2, hins, ite_true, ite_false]
              rw [hpair] at heq
              cases heq
              refine ⟨?_, rfl, ?_, ?_, ?_⟩
              · simp only [BTree.pairsValid]
                exact ⟨hl, inRange_trans_hi hm hk, hr,
                  inRange_some_lo_of_lt hk hm.lt_hi, hrest⟩
              · intro c'' hc''
                simp only [BPairs.children, List.mem_cons] at hc''
                rcases hc'' with rfl | rfl | hc''
                · rw [hhl, hc_h]
                · rw [hhr, hc_h]
                · exact huni' c'' hc''
              · simp only [BPairs.length]
                omega
              · simp only [BPairs.length]
                omega
          · cases hrec : BTree.insPairs x rest last with
            | mk ps'' last'' =>
              obtain ⟨hpv'', hlast'', huni'', hlen1, hlen2⟩ :=
                ih2 rest last
                  (by simp only [BTree.psize] at hh; omega) hrest huni' x
                  (inRange_some_lo_of_lt hx (by omega)) ps'' last'' hrec
              intro ps' last' heq
              have hpair : BTree.insPairs x (.cons c k rest) last =
                  (.cons c k ps'', last'') := by
                simp only [BTree.insPairs, h1, h2, hrec, ite_true, ite_false]
              rw [hpair] at heq
              cases heq
              refine ⟨?_, hlast'', ?_, ?_, ?_⟩
              · simp only [BTree.pairsValid]
                exact ⟨hc, hk, hpv''⟩
              · intro c'' hc''
                simp only [BPairs.children, List.mem_cons] at hc''
                rcases hc'' with rfl | hc''
                · rw [hc_h, hlast'']
                · exact huni'' c'' hc''
              · simp only [BPairs.length]
                omega
              · simp only [BPairs.length]
                omega
    refine ⟨?_, key2⟩
    intro minK lo hi t hh hv x hx
    cases t with
    | leaf ks =>
      simp only [BTree.isValid] at hv
      obtain ⟨hpw, hmin, hmax, hrange⟩ := hv
      have hins : BTree.ins x (.leaf ks) = BTree.insLeaf x ks := by
        simp only [BTree.ins]
      by_cases hlen : (insertKey x ks).length ≤ 3
      · have hok : BTree.insLeaf x ks = .ok (.leaf (insertKey x ks)) := by
          simp only [BTree.insLeaf, hlen, ite_true, ite_false]
        constructor
        · intro t' ht'
          rw [hins, hok] at ht'
          cases ht'
          refine ⟨?_, rfl⟩
          simp only [BTree.isValid]
          exact ⟨pairwise_insertKey hpw,
            Nat.le_trans hmin length_insertKey_ge, hlen,
            fun y hy => by
              have hy2 := mem_insertKey.mp hy
              rcases hy2 with rfl | hy2
              · exact hx
              · exact hrange y hy2⟩
        · intro l m r ht'
          rw [hins, hok] at ht'
          cases ht'
      · have hlen4 : (insertKey x ks).length = 4 := by
          have h1 := length_insertKey_le (x := x) (ks := ks)
          omega
        have hsp : BTree.insLeaf x ks =
            BTree.leafSplit (insertKey x ks) := by
          simp only [BTree.insLeaf, hlen, ite_true, ite_false]
        constructor
        · intro t' ht'
          rw [hins, hsp] at ht'
          cases hks : insertKey x ks with
          | nil =>
            rw [hks] at hlen4
            simp only [List.length_nil] at hlen4
            omega
          | cons a ks1 =>
            cases ks1 with
            | nil =>
              rw [hks] at hlen4
              simp only [List.length_cons, List.length_nil] at hlen4
              omega
            | cons b ks2 =>
              cases ks2 with
              | nil =>
                rw [hks] at hlen4
                simp only [List.length_cons, List.length_nil] at hlen4
                omega
              | cons c ks3 =>
                cases ks3 with
                | nil =>
                  rw [hks] at hlen4
                  simp only [List.length_cons, List.length_nil] at hlen4
                  omega
                | cons d ks4 =>
                  cases ks4 with
                  | cons e rest =>
                    rw [hks] at hlen4
                    simp only [List.length_cons] at hlen4
                    omega
                  | nil =>
                    rw [hks] at ht'
                    simp only [BTree.leafSplit] at ht'
                    cases ht'
        · intro l m r ht'
          rw [hins, hsp] at ht'
          exact BTree.leafSplit_valid hpw hmin hmax hrange x hx hlen4
            l m r ht'
    | node ps last =>
      simp only [BTree.isValid] at hv
      obtain ⟨h1len, h2len, hpv, huni⟩ := hv
      cases hrec : BTree.insPairs x ps last with
      | mk ps' last' =>
        obtain ⟨hpv', hlast', huni', hlen1, hlen2⟩ := key2 ps last
          (by simp only [BTree.tsize] at hh; omega) hpv huni x hx
          ps' last' hrec
        by_cases hlen : BPairs.length ps' ≤ 3
        · have hins : BTree.ins x (.node ps last) =
              .ok (.node ps' last') := by
            simp only [BTree.ins, hrec, hlen, ite_true, ite_false]
          constructor
          · intro t' ht'
            rw [hins] at ht'
            cases ht'
            refine ⟨?_, ?_⟩
            · simp only [BTree.isValid]
              exact ⟨by omega, hlen, hpv', huni'⟩
            · simp only [BTree.height]
              omega
          · intro l m r ht'
            rw [hins] at ht'
            cases ht'
        · have hlen4 : BPairs.length ps' = 4 := by omega
          have hins : BTree.ins x (.node ps last) =
              BTree.nodeSplit ps' last' := by
            simp only [BTree.ins, hrec, hlen, ite_true, ite_false]
          cases ps' with
          | nil => simp [BPairs.length] at hlen4
          | cons c0 k0 rest1 =>
            cases rest1 with
            | nil => simp [BPairs.length] at hlen4
            | cons c1 k1 rest2 =>
              cases rest2 with
              | nil => simp [BPairs.length] at hlen4
              | cons c2 k2 rest3 =>
                cases rest3 with
                | nil => simp [BPairs.length] at hlen4
                | cons c3 k3 rest4 =>
                  cases rest4 with
                  | cons c4 k4 rest5 =>
                    simp only [BPairs.length] at hlen4
                    omega
                  | nil =>
                    simp only [BTree.pairsValid] at hpv'
                    obtain ⟨hc0, hk0, hc1, hk1, hc2, hk2, hc3, hk3,
                      hlastv⟩ := hpv'
                    have hc0h : BTree.height c0 = BTree.height last' :=
                      huni' c0 (by
                        simp only [BPairs.children]
                        exact List.mem_cons_self)
                    have hc1h : BTree.height c1 = BTree.height last' :=
                      huni' c1 (by
                        simp only [BPairs.children]
                        exact List.mem_cons_of_mem c0 List.mem_cons_self)
                    have hc2h : BTree.height c2 = BTree.height last' :=
                      huni' c2 (by
                        simp only [BPairs.children]
                        exact List.mem_cons_of_mem c0
                          (List.mem_cons_of_mem c1 List.mem_cons_self))
                    have hc3h : BTree.height c3 = BTree.height last' :=
                      huni' c3 (by
                        simp only [BPairs.children]
                        exact List.mem_cons_of_mem c0
                          (List.mem_cons_of_mem c1
                            (List.mem_cons_of_mem c2 List.mem_cons_self)))
                    constructor
                    · intro t' ht'
                      rw [hins] at ht'
                      simp only [BTree.nodeSplit] at ht'
                      cases ht'
                    · intro l m r ht'
                      rw [hins] at ht'
                      simp only [BTree.nodeSplit] at ht'
                      cases ht'
                      refine ⟨?_, inRange_trans_lo hk1 hk0, ?_, ?_, ?_⟩
                      · simp only [BTree.isValid]
                        refine ⟨by simp [BPairs.length],
                          by simp [BPairs.length], ?_, ?_⟩
                        · simp only [BTree.pairsValid]
                          exact ⟨hc0,
                            inRange_some_hi_of_lt hk0 hk1.lo_lt, hc1⟩
                        · intro c hc
                          simp only [BPairs.children,
                            List.mem_singleton] at hc
                          rw [hc, hc0h, hc1h]
                      · simp only [BTree.isValid]
                        refine ⟨by simp [BPairs.length],
                          by simp [BPairs.length], ?_, ?_⟩
                        · simp only [BTree.pairsValid]
                          exact ⟨hc2, hk2, hc3, hk3, hlastv⟩
                        · intro c hc
                          simp only [BPairs.children, List.mem_cons,
                            List.mem_singleton] at hc
                          rcases hc with rfl | rfl | hc
                          · exact hc2h
                          · exact hc3h
                          · exact (List.not_mem_nil hc).elim
                      · simp only [BTree.height]
                        omega
                      · simp only [BTree.height]
                        omega

/-- Insertion preserves validity (the `ok` and `split` facts of
`ins_valid_joint`, packaged for a finished tree): inserting an
in-range key into a valid tree gives a valid tree of the same
height, or — when the root splits — one of height one more. -/
theorem BTree.isValid_insert {minK : Nat} {lo hi : Option Nat}
    {t : BTree} (hv : BTree.isValid minK lo hi t) (x : Nat)
    (hx : InRange lo hi x) :
    BTree.isValid minK lo hi (BTree.insert x t) ∧
    (BTree.height (BTree.insert x t) = BTree.height t ∨
      BTree.height (BTree.insert x t) = BTree.height t + 1) := by
  obtain ⟨h1, h2⟩ := (ins_valid_joint (BTree.tsize t)).1
    (Nat.le_refl _) hv x hx
  cases hins : BTree.ins x t with
  | ok t' =>
    obtain ⟨hv', hh'⟩ := h1 t' hins
    have htop : BTree.insert x t = t' := by
      simp only [BTree.insert, hins]
    rw [htop]
    exact ⟨hv', Or.inl hh'⟩
  | split l m r =>
    obtain ⟨hl, hm, hr, hhl, hhr⟩ := h2 l m r hins
    have htop : BTree.insert x t = .node (.cons l m .nil) r := by
      simp only [BTree.insert, hins]
    rw [htop]
    refine ⟨?_, Or.inr ?_⟩
    · simp only [BTree.isValid]
      refine ⟨by simp [BPairs.length], by simp [BPairs.length], ?_, ?_⟩
      · simp only [BTree.pairsValid]
        exact ⟨hl, hm, hr⟩
      · intro c hc
        simp only [BPairs.children, List.mem_singleton] at hc
        rw [hc, hhl, hhr]
    · simp only [BTree.height]
      omega

/-- The headline bundle, keeping the draft's theorem name: on a
valid tree, search is correct; inserting any key preserves
validity and balance and adjoins exactly that key to the contents. -/
theorem btree_correctness (t : BTree) (x : Nat)
    (hv : BTree.isValid 0 none none t) :
    (∀ y, BTree.search t y = true ↔ y ∈ BTree.contents t) ∧
    BTree.isValid 0 none none (BTree.insert x t) ∧
    (∀ y, y ∈ BTree.contents (BTree.insert x t) ↔
      y = x ∨ y ∈ BTree.contents t) ∧
    BTree.isBalanced (BTree.insert x t) :=
  ⟨fun y => BTree.search_eq_true_iff hv y,
   (BTree.isValid_insert hv x (inRange_none_none x)).1,
   BTree.mem_insert x t,
   BTree.valid_isBalanced
     (BTree.isValid_insert hv x (inRange_none_none x)).1⟩


end AxiomCode
