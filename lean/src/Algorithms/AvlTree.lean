import Spec
import Tactics

/-!
# AVL trees

An AVL tree over `Nat` keys: a binary search tree kept
height-balanced by rebalancing insertion (`AvlTree.insert`, built on
`AvlTree.bal` with single and double rotations). Search
(`AvlTree.search`) is proved sound and complete against the inorder
contents on BSTs.

## Draft defect record (promotion standard: defect + counterexample)

The draft (`lean/drafts/avl_tree_correctness.lean`) did not
elaborate: it imported Mathlib and Aesop (not built in this working
copy); `height` and `balanceFactor` were written with `:=` and no
body, which is a parse error; `AVLNode` was never defined;
`AVLTree` was a fieldless structure, so `t.root`, `n.left`,
`n.right` and `n \in t.root` referenced fields and a membership that
do not exist; `AVLTree.mk (some n)` supplied an argument to a
fieldless constructor; `|balanceFactor n|` used absolute-value
notation that core Lean does not provide for `Int`; and the theorem
was left with an unfinished proof placeholder.

The intended claim was also false as stated: it asserted that in
EVERY tree, every node's balance factor is within 1. The
right-leaning chain `node leaf 0 (node leaf 1 (node leaf 2 leaf))`
is a counterexample: the root's balance factor is `0 - 2 = -2`, of
absolute value `2 > 1`. Bounded balance factors are an invariant —
true of the empty tree and preserved by insertion — not a property
of arbitrary trees. The draft also contained no operation whose
correctness could be stated.

## Repair (shape preserved)

The draft's first conjunct is repaired as the recursive predicate
`AvlTree.Balanced`, with the bridge theorem
`balanced_balanceFactor`: in a balanced tree, every subtree's
balance factor has absolute value at most 1 (`Int.natAbs`, since
core Lean has no `|·|` notation for `Int`). The draft's second
conjunct — the height of a node is one plus the maximum subtree
height — is `height_node`, the defining equation of `height`. The
headline keeps the draft's name `avl_tree_correctness`: on a BST
that is balanced, insertion preserves both invariants, adds exactly
the inserted key to the contents, and the inserted key is found by
search.
-/

namespace AxiomCode

/-- An AVL tree: a binary search tree of `Nat` keys (an ordered set),
kept height-balanced by insertion. `leaf` is the empty tree. -/
inductive AvlTree where
  | leaf : AvlTree
  | node (l : AvlTree) (k : Nat) (r : AvlTree) : AvlTree

/-- The height of a tree: the empty tree has height 0, and a node's
height is one more than the greater of its subtrees' heights. This is
the draft's second conjunct, as the defining equation of `height`. -/
def height : AvlTree → Nat
  | .leaf => 0
  | .node l _ r => max (height l) (height r) + 1

/-- The balance factor of a tree's root: left height minus right
height, in `Int` (the draft's `balanceFactor`). The empty tree's
factor is 0. -/
def balanceFactor : AvlTree → Int
  | .leaf => 0
  | .node l _ r => (height l : Int) - (height r : Int)

/-- The contents of a tree: its keys in inorder (left subtree, root
key, right subtree). -/
def AvlTree.contents : AvlTree → List Nat
  | .leaf => []
  | .node l k r => AvlTree.contents l ++ k :: AvlTree.contents r

/-- Membership in a tree is membership in its contents. -/
instance : Membership Nat AvlTree where
  mem t x := x ∈ AvlTree.contents t

theorem AvlTree.mem_def {x : Nat} {t : AvlTree} :
    x ∈ t ↔ x ∈ AvlTree.contents t := Iff.rfl

/-- All subtrees of a tree, itself included. -/
def AvlTree.subtrees : AvlTree → List AvlTree
  | .leaf => [.leaf]
  | .node l k r => .node l k r :: (AvlTree.subtrees l ++ AvlTree.subtrees r)

/-- The BST invariant, in contents form: at every node, every key of
the left subtree is below the node's key and every key of the right
subtree is above it, recursively. -/
inductive AvlTree.BST : AvlTree → Prop where
  | leaf : AvlTree.BST .leaf
  | node {l r : AvlTree} {k : Nat} :
      AvlTree.BST l → AvlTree.BST r →
      (∀ x ∈ AvlTree.contents l, x < k) →
      (∀ x ∈ AvlTree.contents r, k < x) →
      AvlTree.BST (.node l k r)

/-- The AVL balance invariant, in the draft's shape: at every node,
the two subtree heights differ by at most one — equivalently, every
node's `balanceFactor` lies in `[-1, 1]` (bridge theorem
`balanced_balanceFactor` below). -/
inductive AvlTree.Balanced : AvlTree → Prop where
  | leaf : AvlTree.Balanced .leaf
  | node {l r : AvlTree} {k : Nat} :
      AvlTree.Balanced l → AvlTree.Balanced r →
      height l ≤ height r + 1 → height r ≤ height l + 1 →
      AvlTree.Balanced (.node l k r)

/-- BST search: descend left or right by comparison with the node's
key. -/
def AvlTree.search : AvlTree → Nat → Bool
  | .leaf, _ => false
  | .node l k r, x =>
    if x < k then AvlTree.search l x
    else if k < x then AvlTree.search r x
    else true

theorem height_leaf : height AvlTree.leaf = 0 := rfl

theorem height_node (l r : AvlTree) (k : Nat) :
    height (.node l k r) = max (height l) (height r) + 1 := rfl

theorem balanceFactor_leaf : balanceFactor AvlTree.leaf = 0 := rfl

theorem balanceFactor_node (l r : AvlTree) (k : Nat) :
    balanceFactor (.node l k r) = (height l : Int) - (height r : Int) := rfl

theorem AvlTree.contents_leaf : AvlTree.contents AvlTree.leaf = [] := rfl

theorem AvlTree.contents_node (l r : AvlTree) (k : Nat) :
    AvlTree.contents (.node l k r) =
      AvlTree.contents l ++ k :: AvlTree.contents r := rfl

theorem AvlTree.mem_node {x : Nat} {l r : AvlTree} {k : Nat} :
    x ∈ AvlTree.contents (.node l k r) ↔
      x ∈ AvlTree.contents l ∨ x = k ∨ x ∈ AvlTree.contents r := by
  simp [AvlTree.contents, List.mem_append, List.mem_cons]

/-- A balanced tree's root balance factor is within 1. -/
theorem AvlTree.Balanced.balanceFactor_le {t : AvlTree}
    (h : AvlTree.Balanced t) : (balanceFactor t).natAbs ≤ 1 := by
  cases t with
  | leaf => simp [balanceFactor]
  | node l k r =>
    cases h with
    | node _ _ h1 h2 =>
      rw [balanceFactor_node]
      omega

/-- Every subtree of a balanced tree is balanced. -/
theorem AvlTree.Balanced.subtrees {t s : AvlTree}
    (h : AvlTree.Balanced t) (hs : s ∈ AvlTree.subtrees t) :
    AvlTree.Balanced s := by
  induction h with
  | leaf =>
    simp [AvlTree.subtrees] at hs
    subst hs
    exact AvlTree.Balanced.leaf
  | node hl hr h1 h2 ihl ihr =>
    rename_i l r k
    simp [AvlTree.subtrees, List.mem_append] at hs
    rcases hs with rfl | hs | hs
    · exact AvlTree.Balanced.node hl hr h1 h2
    · exact ihl hs
    · exact ihr hs

/-- The draft's first conjunct, carried: in a balanced tree, every
node's balance factor is within 1 in absolute value. -/
theorem balanced_balanceFactor (t : AvlTree) (h : AvlTree.Balanced t) :
    ∀ s ∈ AvlTree.subtrees t, (balanceFactor s).natAbs ≤ 1 :=
  fun s hs => (h.subtrees hs).balanceFactor_le

/-- The BST invariant is exactly strict sortedness of the contents. -/
theorem AvlTree.bst_iff {t : AvlTree} :
    AvlTree.BST t ↔ List.Pairwise (· < ·) (AvlTree.contents t) := by
  induction t with
  | leaf =>
    constructor
    · intro _; exact List.Pairwise.nil
    · intro _; exact AvlTree.BST.leaf
  | node l k r ihl ihr =>
    constructor
    · intro h
      cases h with
      | node hl hr hb1 hb2 =>
        rw [AvlTree.contents_node, List.pairwise_append]
        refine ⟨ihl.mp hl, ?_, ?_⟩
        · rw [List.pairwise_cons]
          exact ⟨fun y hy => hb2 y hy, ihr.mp hr⟩
        · intro a ha b hb
          rw [List.mem_cons] at hb
          rcases hb with rfl | hb
          · exact hb1 a ha
          · have h1 := hb1 a ha; have h2 := hb2 b hb; omega
    · intro h
      rw [AvlTree.contents_node, List.pairwise_append] at h
      obtain ⟨hpl, hpr, hcross⟩ := h
      rw [List.pairwise_cons] at hpr
      obtain ⟨hklt, hpr⟩ := hpr
      refine AvlTree.BST.node (ihl.mpr hpl) (ihr.mpr hpr) ?_ hklt
      intro a ha
      exact hcross a ha k List.mem_cons_self

/-- Search is sound and complete against the contents, on BSTs:
`search t x = true` exactly when `x` is a key of `t`. -/
theorem AvlTree.search_eq_true_iff {t : AvlTree} (h : AvlTree.BST t) {x : Nat} :
    AvlTree.search t x = true ↔ x ∈ AvlTree.contents t := by
  induction t with
  | leaf => simp [AvlTree.search, AvlTree.contents]
  | node l k r ihl ihr =>
    cases h with
    | node hl hr hb1 hb2 =>
      by_cases h1 : x < k
      · have hsearch : AvlTree.search (.node l k r) x = AvlTree.search l x := by
          simp [AvlTree.search, h1]
        rw [hsearch, ihl hl, AvlTree.mem_node]
        constructor
        · intro hx; exact Or.inl hx
        · intro hx
          rcases hx with hx | rfl | hx
          · exact hx
          · simp at h1
          · exfalso; have h2 := hb2 x hx; omega
      · by_cases h2 : k < x
        · have hsearch : AvlTree.search (.node l k r) x = AvlTree.search r x := by
            simp [AvlTree.search, h1, h2]
          rw [hsearch, ihr hr, AvlTree.mem_node]
          constructor
          · intro hx; exact Or.inr (Or.inr hx)
          · intro hx
            rcases hx with hx | rfl | hx
            · exfalso; have h3 := hb1 x hx; omega
            · simp at h2
            · exact hx
        · have hxk : x = k := by omega
          subst hxk
          have hsearch : AvlTree.search (.node l x r) x = true := by
            simp [AvlTree.search]
          rw [hsearch]
          simp [AvlTree.mem_node]

/-- Rebalance a left-heavy node: `l` is two taller than `r`.
Single right rotation when the left child's left subtree is at least
as tall as its right; double rotation otherwise. The fallbacks
(`l` a leaf, or the left child's right subtree a leaf in the double
case) are unreachable under the height conditions at the use sites;
they return the plain node so the function is total. -/
def AvlTree.balLeft (l : AvlTree) (k : Nat) (r : AvlTree) : AvlTree :=
  match l with
  | .node ll lk lr =>
    if height lr ≤ height ll then
      .node ll lk (.node lr k r)
    else
      match lr with
      | .node lrl lrk lrr => .node (.node ll lk lrl) lrk (.node lrr k r)
      | .leaf => .node l k r
  | .leaf => .node l k r

/-- Rebalance a right-heavy node: mirror of `balLeft`. -/
def AvlTree.balRight (l : AvlTree) (k : Nat) (r : AvlTree) : AvlTree :=
  match r with
  | .node rl rk rr =>
    if height rl ≤ height rr then
      .node (.node l k rl) rk rr
    else
      match rl with
      | .node rll rlk rlr => .node (.node l k rll) rlk (.node rlr rk rr)
      | .leaf => .node l k r
  | .leaf => .node l k r

/-- The rebalancing smart constructor used by insertion: if one side
is two taller than the other, rebalance with `balLeft` / `balRight`;
otherwise a plain node. -/
def AvlTree.bal (l : AvlTree) (k : Nat) (r : AvlTree) : AvlTree :=
  if height r + 1 < height l then AvlTree.balLeft l k r
  else if height l + 1 < height r then AvlTree.balRight l k r
  else .node l k r

/-- Rotations preserve the inorder contents exactly: the contents of
`bal l k r` are the contents of the un-rebalanced node. -/
theorem AvlTree.bal_contents (l r : AvlTree) (k : Nat) :
    AvlTree.contents (AvlTree.bal l k r) =
      AvlTree.contents l ++ k :: AvlTree.contents r := by
  by_cases hL : height r + 1 < height l
  · have hb : AvlTree.bal l k r = AvlTree.balLeft l k r := by
      simp only [AvlTree.bal, hL, ite_eq_left, ite_true, ite_false]
    rw [hb]
    cases l with
    | leaf => simp only [height] at hL; omega
    | node ll lk lr =>
      by_cases hS : height lr ≤ height ll
      · have hbl : AvlTree.balLeft (.node ll lk lr) k r =
            .node ll lk (.node lr k r) := by
          simp only [AvlTree.balLeft, hS, ite_true, ite_false]
        rw [hbl]
        simp [AvlTree.contents, List.append_assoc]
      · cases lr with
        | leaf => simp only [height] at hS; omega
        | node lrl lrk lrr =>
          have hbl : AvlTree.balLeft (.node ll lk (.node lrl lrk lrr)) k r =
              .node (.node ll lk lrl) lrk (.node lrr k r) := by
            simp only [AvlTree.balLeft, hS, ite_true, ite_false]
          rw [hbl]
          simp [AvlTree.contents, List.append_assoc]
  · by_cases hR : height l + 1 < height r
    · have hb : AvlTree.bal l k r = AvlTree.balRight l k r := by
        simp only [AvlTree.bal, hL, ite_eq_right, hR, ite_eq_left, ite_true, ite_false]
      rw [hb]
      cases r with
      | leaf => simp only [height] at hR; omega
      | node rl rk rr =>
        by_cases hS : height rl ≤ height rr
        · have hbr : AvlTree.balRight l k (.node rl rk rr) =
              .node (.node l k rl) rk rr := by
            simp only [AvlTree.balRight, hS, ite_true, ite_false]
          rw [hbr]
          simp [AvlTree.contents, List.append_assoc]
        · cases rl with
          | leaf => simp only [height] at hS; omega
          | node rll rlk rlr =>
            have hbr : AvlTree.balRight l k (.node (.node rll rlk rlr) rk rr) =
                .node (.node l k rll) rlk (.node rlr rk rr) := by
              simp only [AvlTree.balRight, hS, ite_true, ite_false]
            rw [hbr]
            simp [AvlTree.contents, List.append_assoc]
    · have hb : AvlTree.bal l k r = .node l k r := by
        simp only [AvlTree.bal, hL, ite_eq_right, hR, ite_true, ite_false]
      rw [hb]
      simp [AvlTree.contents]

/-- The specification of `bal`: from balanced subtrees whose heights
differ by at most two, it produces a balanced tree whose height is
the plain node's height, or one less when a rotation was forced (in
which case the heights differed by exactly two). -/
theorem AvlTree.bal_spec {l r : AvlTree} (hl : AvlTree.Balanced l)
    (hr : AvlTree.Balanced r)
    (h1 : height l ≤ height r + 2) (h2 : height r ≤ height l + 2) (k : Nat) :
    AvlTree.Balanced (AvlTree.bal l k r) ∧
    (height (AvlTree.bal l k r) = max (height l) (height r) + 1 ∨
     height (AvlTree.bal l k r) = max (height l) (height r) ∧
       (height l = height r + 2 ∨ height r = height l + 2)) := by
  by_cases hL : height r + 1 < height l
  · have hb : AvlTree.bal l k r = AvlTree.balLeft l k r := by
      simp only [AvlTree.bal, hL, ite_eq_left, ite_true, ite_false]
    cases l with
    | leaf => simp only [height] at hL; omega
    | node ll lk lr =>
      cases hl with
      | node hbl hbr hle1 hle2 =>
        have e_l : height (.node ll lk lr) =
            max (height ll) (height lr) + 1 := height_node _ _ _
        by_cases hS : height lr ≤ height ll
        · have hrot : AvlTree.balLeft (.node ll lk lr) k r =
              .node ll lk (.node lr k r) := by
            simp only [AvlTree.balLeft, hS, ite_true, ite_false]
          have e_lr : height (.node lr k r) =
              max (height lr) (height r) + 1 := height_node _ _ _
          rw [hb, hrot]
          refine ⟨?_, ?_⟩
          · refine AvlTree.Balanced.node hbl ?_ ?_ ?_
            · exact AvlTree.Balanced.node hbr hr (by omega) (by omega)
            · omega
            · omega
          · have e : height (.node ll lk (.node lr k r)) =
                max (height ll) (max (height lr) (height r) + 1) + 1 := by
              simp only [height]
            omega
        · cases lr with
          | leaf => simp only [height] at hS; omega
          | node lrl lrk lrr =>
            cases hbr with
            | node hblrl hblrr hle3 hle4 =>
              have e_lr : height (.node lrl lrk lrr) =
                  max (height lrl) (height lrr) + 1 := height_node _ _ _
              have hrot : AvlTree.balLeft (.node ll lk (.node lrl lrk lrr)) k r =
                  .node (.node ll lk lrl) lrk (.node lrr k r) := by
                simp only [AvlTree.balLeft, hS, ite_true, ite_false]
              have e1 : height (.node ll lk lrl) =
                  max (height ll) (height lrl) + 1 := height_node _ _ _
              have e2 : height (.node lrr k r) =
                  max (height lrr) (height r) + 1 := height_node _ _ _
              rw [hb, hrot]
              refine ⟨?_, ?_⟩
              · refine AvlTree.Balanced.node ?_ ?_ ?_ ?_
                · exact AvlTree.Balanced.node hbl hblrl (by omega) (by omega)
                · exact AvlTree.Balanced.node hblrr hr (by omega) (by omega)
                · omega
                · omega
              · have e : height (.node (.node ll lk lrl) lrk (.node lrr k r)) =
                    max (max (height ll) (height lrl) + 1)
                      (max (height lrr) (height r) + 1) + 1 := by
                  simp only [height]
                omega
  · by_cases hR : height l + 1 < height r
    · have hb : AvlTree.bal l k r = AvlTree.balRight l k r := by
        simp only [AvlTree.bal, hL, ite_eq_right, hR, ite_eq_left, ite_true, ite_false]
      cases r with
      | leaf => simp only [height] at hR; omega
      | node rl rk rr =>
        cases hr with
        | node hbrl hbrr hre1 hre2 =>
          have e_r : height (.node rl rk rr) =
              max (height rl) (height rr) + 1 := height_node _ _ _
          by_cases hS : height rl ≤ height rr
          · have hrot : AvlTree.balRight l k (.node rl rk rr) =
                .node (.node l k rl) rk rr := by
              simp only [AvlTree.balRight, hS, ite_true, ite_false]
            have e_rl : height (.node l k rl) =
                max (height l) (height rl) + 1 := height_node _ _ _
            rw [hb, hrot]
            refine ⟨?_, ?_⟩
            · refine AvlTree.Balanced.node ?_ hbrr ?_ ?_
              · exact AvlTree.Balanced.node hl hbrl (by omega) (by omega)
              · omega
              · omega
            · have e : height (.node (.node l k rl) rk rr) =
                  max (max (height l) (height rl) + 1) (height rr) + 1 := by
                simp only [height]
              omega
          · cases rl with
            | leaf => simp only [height] at hS; omega
            | node rll rlk rlr =>
              cases hbrl with
              | node hbrll hbrlr hre3 hre4 =>
                have e_rl : height (.node rll rlk rlr) =
                    max (height rll) (height rlr) + 1 := height_node _ _ _
                have hrot : AvlTree.balRight l k (.node (.node rll rlk rlr) rk rr) =
                    .node (.node l k rll) rlk (.node rlr rk rr) := by
                  simp only [AvlTree.balRight, hS, ite_true, ite_false]
                have e1 : height (.node l k rll) =
                    max (height l) (height rll) + 1 := height_node _ _ _
                have e2 : height (.node rlr rk rr) =
                    max (height rlr) (height rr) + 1 := height_node _ _ _
                rw [hb, hrot]
                refine ⟨?_, ?_⟩
                · refine AvlTree.Balanced.node ?_ ?_ ?_ ?_
                  · exact AvlTree.Balanced.node hl hbrll (by omega) (by omega)
                  · exact AvlTree.Balanced.node hbrlr hbrr (by omega) (by omega)
                  · omega
                  · omega
                · have e : height (.node (.node l k rll) rlk (.node rlr rk rr)) =
                      max (max (height l) (height rll) + 1)
                        (max (height rlr) (height rr) + 1) + 1 := by
                    simp only [height]
                  omega
    · have hb : AvlTree.bal l k r = .node l k r := by
        simp only [AvlTree.bal, hL, ite_eq_right, hR, ite_true, ite_false]
      rw [hb]
      refine ⟨AvlTree.Balanced.node hl hr (by omega) (by omega), ?_⟩
      exact Or.inl (height_node l r k)

/-- AVL insertion: descend as in BST search; on the way back up,
restore balance with `bal`. Inserting an existing key leaves the
tree unchanged. -/
def AvlTree.insert (x : Nat) : AvlTree → AvlTree
  | .leaf => .node .leaf x .leaf
  | .node l k r =>
    if x < k then AvlTree.bal (AvlTree.insert x l) k r
    else if k < x then AvlTree.bal l k (AvlTree.insert x r)
    else .node l k r

/-- The contents of an insertion, characterised exactly: the keys of
`insert x t` are `x` and the keys of `t`. No hypothesis on `t`. -/
theorem AvlTree.mem_insert (x : Nat) (t : AvlTree) :
    ∀ y, y ∈ AvlTree.contents (AvlTree.insert x t) ↔
      y = x ∨ y ∈ AvlTree.contents t := by
  induction t with
  | leaf => intro y; simp [AvlTree.insert, AvlTree.contents]
  | node l k r ihl ihr =>
    intro y
    by_cases h1 : x < k
    · have hins : AvlTree.insert x (.node l k r) =
          AvlTree.bal (AvlTree.insert x l) k r := by
        simp only [AvlTree.insert, h1, ite_eq_left, ite_true, ite_false]
      rw [hins, AvlTree.bal_contents]
      simp only [AvlTree.contents_node, List.mem_append, List.mem_cons, ihl,
        or_assoc]
    · by_cases h2 : k < x
      · have hins : AvlTree.insert x (.node l k r) =
            AvlTree.bal l k (AvlTree.insert x r) := by
          simp only [AvlTree.insert, h1, ite_eq_right, h2, ite_eq_left,
            ite_true, ite_false]
        rw [hins, AvlTree.bal_contents]
        simp only [AvlTree.contents_node, List.mem_append, List.mem_cons, ihr,
          or_assoc]
        constructor <;> intro h <;> rcases h with h | h | h | h <;>
          first
            | exact Or.inl h
            | exact Or.inr (Or.inl h)
            | exact Or.inr (Or.inr (Or.inl h))
            | exact Or.inr (Or.inr (Or.inr h))
      · have hxk : x = k := by omega
        have hins : AvlTree.insert x (.node l k r) = .node l k r := by
          simp only [AvlTree.insert, h1, h2, ite_true, ite_false]
        rw [hins, hxk]
        constructor
        · intro h; exact Or.inr h
        · intro h
          rcases h with rfl | h
          · rw [AvlTree.mem_node]; exact Or.inr (Or.inl rfl)
          · exact h

/-- `bal` preserves the BST invariant: via `bst_iff`, its contents
are the un-rebalanced node's contents, which are strictly sorted
from the two sides' sortedness and the two bounds. -/
theorem AvlTree.bst_bal {a b : AvlTree} {k : Nat}
    (ha : AvlTree.BST a) (hb : AvlTree.BST b)
    (h1 : ∀ z ∈ AvlTree.contents a, z < k)
    (h2 : ∀ z ∈ AvlTree.contents b, k < z) :
    AvlTree.BST (AvlTree.bal a k b) := by
  rw [AvlTree.bst_iff, AvlTree.bal_contents, List.pairwise_append]
  refine ⟨AvlTree.bst_iff.mp ha, ?_, ?_⟩
  · rw [List.pairwise_cons]
    exact ⟨h2, AvlTree.bst_iff.mp hb⟩
  · intro z hz w hw
    rw [List.mem_cons] at hw
    rcases hw with rfl | hw
    · exact h1 z hz
    · have h3 := h1 z hz; have h4 := h2 w hw; omega

/-- Insertion preserves the BST invariant. -/
theorem AvlTree.bst_insert (x : Nat) {t : AvlTree} (h : AvlTree.BST t) :
    AvlTree.BST (AvlTree.insert x t) := by
  induction t with
  | leaf =>
    refine AvlTree.BST.node AvlTree.BST.leaf AvlTree.BST.leaf ?_ ?_ <;>
      simp [AvlTree.contents]
  | node l k r ihl ihr =>
    cases h with
    | node hl hr hb1 hb2 =>
      by_cases h1 : x < k
      · have hins : AvlTree.insert x (.node l k r) =
            AvlTree.bal (AvlTree.insert x l) k r := by
          simp only [AvlTree.insert, h1, ite_eq_left, ite_true, ite_false]
        rw [hins]
        refine AvlTree.bst_bal (ihl hl) hr ?_ hb2
        intro z hz
        have hz2 := (AvlTree.mem_insert x l z).mp hz
        rcases hz2 with rfl | hz2
        · exact h1
        · exact hb1 z hz2
      · by_cases h2 : k < x
        · have hins : AvlTree.insert x (.node l k r) =
              AvlTree.bal l k (AvlTree.insert x r) := by
            simp only [AvlTree.insert, h1, ite_eq_right, h2, ite_eq_left,
              ite_true, ite_false]
          rw [hins]
          refine AvlTree.bst_bal hl (ihr hr) hb1 ?_
          intro z hz
          have hz2 := (AvlTree.mem_insert x r z).mp hz
          rcases hz2 with rfl | hz2
          · exact h2
          · exact hb2 z hz2
        · have hins : AvlTree.insert x (.node l k r) = .node l k r := by
            simp only [AvlTree.insert, h1, h2, ite_true, ite_false]
          rw [hins]
          exact AvlTree.BST.node hl hr hb1 hb2

/-- Insertion preserves the balance invariant, and the height moves
by at most one and never shrinks. -/
theorem AvlTree.insert_spec (x : Nat) {t : AvlTree}
    (h : AvlTree.Balanced t) :
    AvlTree.Balanced (AvlTree.insert x t) ∧
    height t ≤ height (AvlTree.insert x t) ∧
    height (AvlTree.insert x t) ≤ height t + 1 := by
  induction t with
  | leaf =>
    refine ⟨?_, by simp only [AvlTree.insert, height]; omega,
      by simp only [AvlTree.insert, height]; omega⟩
    exact AvlTree.Balanced.node AvlTree.Balanced.leaf AvlTree.Balanced.leaf
      (by omega) (by omega)
  | node l k r ihl ihr =>
    cases h with
    | node hl hr hle1 hle2 =>
      have e_t : height (.node l k r) = max (height l) (height r) + 1 :=
        height_node _ _ _
      by_cases h1 : x < k
      · have hins : AvlTree.insert x (.node l k r) =
            AvlTree.bal (AvlTree.insert x l) k r := by
          simp only [AvlTree.insert, h1, ite_eq_left, ite_true, ite_false]
        obtain ⟨hbal, ih1, ih2⟩ := ihl hl
        obtain ⟨hbal2, hdisj⟩ := AvlTree.bal_spec hbal hr (by omega) (by omega) k
        rw [hins]
        refine ⟨hbal2, ?_, ?_⟩
        · rcases hdisj with hd | ⟨hd, hd2⟩
          · omega
          · rcases hd2 with hd3 | hd3 <;> omega
        · rcases hdisj with hd | ⟨hd, -⟩ <;> omega
      · by_cases h2 : k < x
        · have hins : AvlTree.insert x (.node l k r) =
              AvlTree.bal l k (AvlTree.insert x r) := by
            simp only [AvlTree.insert, h1, ite_eq_right, h2, ite_eq_left,
              ite_true, ite_false]
          obtain ⟨hbal, ih1, ih2⟩ := ihr hr
          obtain ⟨hbal2, hdisj⟩ :=
            AvlTree.bal_spec hl hbal (by omega) (by omega) k
          rw [hins]
          refine ⟨hbal2, ?_, ?_⟩
          · rcases hdisj with hd | ⟨hd, hd2⟩
            · omega
            · rcases hd2 with hd3 | hd3 <;> omega
          · rcases hdisj with hd | ⟨hd, -⟩ <;> omega
        · have hins : AvlTree.insert x (.node l k r) = .node l k r := by
            simp only [AvlTree.insert, h1, h2, ite_true, ite_false]
          rw [hins]
          exact ⟨AvlTree.Balanced.node hl hr hle1 hle2, by omega, by omega⟩

/-- Insertion preserves balance (the second component of
`insert_spec`, named for the exit check). -/
theorem AvlTree.balanced_insert (x : Nat) {t : AvlTree}
    (h : AvlTree.Balanced t) : AvlTree.Balanced (AvlTree.insert x t) :=
  (AvlTree.insert_spec x h).1

/-- Search after insertion: the inserted key is found, and every
previously found key still is (on BSTs). -/
theorem AvlTree.search_insert {t : AvlTree} (h : AvlTree.BST t)
    (x y : Nat) :
    AvlTree.search (AvlTree.insert x t) y = true ↔
      y = x ∨ AvlTree.search t y = true := by
  rw [AvlTree.search_eq_true_iff (AvlTree.bst_insert x h),
    AvlTree.search_eq_true_iff h, AvlTree.mem_insert]

/-- The headline bundle, keeping the draft's theorem name: on a BST
that is balanced, insertion keeps both invariants, adds exactly the
inserted key to the contents, and the inserted key is found by
search. -/
theorem avl_tree_correctness (t : AvlTree) (x : Nat)
    (hb : AvlTree.BST t) (hbal : AvlTree.Balanced t) :
    AvlTree.BST (AvlTree.insert x t) ∧
    AvlTree.Balanced (AvlTree.insert x t) ∧
    (∀ y, y ∈ AvlTree.contents (AvlTree.insert x t) ↔
      y = x ∨ y ∈ AvlTree.contents t) ∧
    AvlTree.search (AvlTree.insert x t) x = true :=
  ⟨AvlTree.bst_insert x hb, AvlTree.balanced_insert x hbal,
   AvlTree.mem_insert x t,
   (AvlTree.search_insert hb x x).mpr (Or.inl rfl)⟩

end AxiomCode
