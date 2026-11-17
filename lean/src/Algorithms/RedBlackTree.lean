import Spec
import Tactics

/-!
# Red-black trees

A red-black tree over `Nat` keys, in Okasaki's functional
formulation: insertion descends with `ins`, rebalancing on the way
up with `balance` (the four red-red patterns rotate and recolour),
and the root is blackened by `rbInsert`. The module proves the full
invariant bundle for insertion: the contents gain exactly the
inserted key, the black-height invariant `BHOk` is preserved, the
no-red-red invariant `NoRR` is restored by the blackening, the BST
ordering is preserved, and BST-guided `search` agrees with the
contents.

## Draft defect record (promotion standard: defect + counterexample)

The draft (`lean/drafts/rbtreeinsertioncorrectness.lean`) was a
pure shell: it imported Mathlib and Aesop against the library's
discipline; `Node` was a fieldless structure; `Tree` was never
defined; `isRedBlackTree`, `blackHeight` and `insert` were written
with `:=` and no body; and the claim was closed by a proof
placeholder. Nothing
in it elaborates, and nothing is carried literally — the classical
claim is authored here in full.

## Two design findings (statement level, found by the proof work)

(1) **The contents claim needs bag semantics.** In the form
"inserting `x` adds `x` to the contents", the claim is false for an
insertion that stops at an equal key: the contents do not gain the
element, and the claimed permutation relates lists of different
lengths. `ins` therefore descends right at an equal key, so the
inserted key is always added (a bag, not a set), and the contents
theorem `inorder_rbInsert` holds unconditionally.

(2) **The BST invariant is stated in its rotation-closed form.**
The strict-left form (left subtree `<` the key, key `≤` right
subtree) is NOT preserved by the rotations when duplicate keys are
present: a rotation can move a key equal to the pivot into its left
subtree. `BST` therefore uses `≤` on both sides, which the
rotations do preserve (the four pattern lemmas `BST_P1`–`BST_P4`),
and under which `search` is still exact (`search_eq_true_iff`).

The headline is `rbtree_insertion_correctness`: on a tree
satisfying `BHOk`, `NoRR` and `BST`, `rbInsert` adds exactly the
inserted key to the inorder contents and preserves all three
invariants.
-/

namespace AxiomCode

inductive Colour where
  | red : Colour
  | black : Colour
deriving DecidableEq

inductive RBTree where
  | leaf : RBTree
  | node : Colour → RBTree → Nat → RBTree → RBTree

/-- In-order contents of the tree. -/
def inorder : RBTree → List Nat
  | .leaf => []
  | .node _ l x r => inorder l ++ x :: inorder r

/-- Okasaki's balance: the four red-red patterns rotate and recolour;
every other shape is rebuilt unchanged. -/
def balance : Colour → RBTree → Nat → RBTree → RBTree
  | .black, .node .red (.node .red a x b) y c, z, d =>
      .node .red (.node .black a x b) y (.node .black c z d)
  | .black, .node .red a x (.node .red b y c), z, d =>
      .node .red (.node .black a x b) y (.node .black c z d)
  | .black, a, x, .node .red (.node .red b y c) z d =>
      .node .red (.node .black a x b) y (.node .black c z d)
  | .black, a, x, .node .red b y (.node .red c z d) =>
      .node .red (.node .black a x b) y (.node .black c z d)
  | c, l, x, r => .node c l x r

theorem inorder_balance (c : Colour) (l : RBTree) (x : Nat) (r : RBTree) :
    inorder (balance c l x r) = inorder l ++ x :: inorder r := by
  cases c with
  | red =>
    cases l with
    | leaf => cases r <;> simp [balance, inorder]
    | node c1 l1 y r1 => cases r <;> simp [balance, inorder]
  | black =>
    cases l with
    | leaf =>
      cases r with
      | leaf => simp [balance, inorder, List.append_assoc]
      | node c1 l2 x3 r4 =>
        cases c1 with
        | black => simp [balance, inorder, List.append_assoc]
        | red =>
          cases l2 with
          | leaf =>
            cases r4 with
            | leaf => simp [balance, inorder, List.append_assoc]
            | node c5 l6 x7 r8 =>
              cases c5 with
              | black => simp [balance, inorder, List.append_assoc]
              | red => simp [balance, inorder, List.append_assoc]
          | node c9 l10 x11 r12 =>
            cases c9 with
            | black =>
              cases r4 with
              | leaf => simp [balance, inorder, List.append_assoc]
              | node c13 l14 x15 r16 =>
                cases c13 with
                | black => simp [balance, inorder, List.append_assoc]
                | red => simp [balance, inorder, List.append_assoc]
            | red => simp [balance, inorder, List.append_assoc]
    | node c17 l18 x19 r20 =>
      cases c17 with
      | black =>
        cases r with
        | leaf => simp [balance, inorder, List.append_assoc]
        | node c21 l22 x23 r24 =>
          cases c21 with
          | black => simp [balance, inorder, List.append_assoc]
          | red =>
            cases l22 with
            | leaf =>
              cases r24 with
              | leaf => simp [balance, inorder, List.append_assoc]
              | node c25 l26 x27 r28 =>
                cases c25 with
                | black => simp [balance, inorder, List.append_assoc]
                | red => simp [balance, inorder, List.append_assoc]
            | node c29 l30 x31 r32 =>
              cases c29 with
              | black =>
                cases r24 with
                | leaf => simp [balance, inorder, List.append_assoc]
                | node c33 l34 x35 r36 =>
                  cases c33 with
                  | black => simp [balance, inorder, List.append_assoc]
                  | red => simp [balance, inorder, List.append_assoc]
              | red => simp [balance, inorder, List.append_assoc]
      | red =>
        cases l18 with
        | leaf =>
          cases r20 with
          | leaf =>
            cases r with
            | leaf => simp [balance, inorder, List.append_assoc]
            | node c37 l38 x39 r40 =>
              cases c37 with
              | black => simp [balance, inorder, List.append_assoc]
              | red =>
                cases l38 with
                | leaf =>
                  cases r40 with
                  | leaf => simp [balance, inorder, List.append_assoc]
                  | node c41 l42 x43 r44 =>
                    cases c41 with
                    | black => simp [balance, inorder, List.append_assoc]
                    | red => simp [balance, inorder, List.append_assoc]
                | node c45 l46 x47 r48 =>
                  cases c45 with
                  | black =>
                    cases r40 with
                    | leaf => simp [balance, inorder, List.append_assoc]
                    | node c49 l50 x51 r52 =>
                      cases c49 with
                      | black => simp [balance, inorder, List.append_assoc]
                      | red => simp [balance, inorder, List.append_assoc]
                  | red => simp [balance, inorder, List.append_assoc]
          | node c53 l54 x55 r56 =>
            cases c53 with
            | black =>
              cases r with
              | leaf => simp [balance, inorder, List.append_assoc]
              | node c57 l58 x59 r60 =>
                cases c57 with
                | black => simp [balance, inorder, List.append_assoc]
                | red =>
                  cases l58 with
                  | leaf =>
                    cases r60 with
                    | leaf => simp [balance, inorder, List.append_assoc]
                    | node c61 l62 x63 r64 =>
                      cases c61 with
                      | black => simp [balance, inorder, List.append_assoc]
                      | red => simp [balance, inorder, List.append_assoc]
                  | node c65 l66 x67 r68 =>
                    cases c65 with
                    | black =>
                      cases r60 with
                      | leaf => simp [balance, inorder, List.append_assoc]
                      | node c69 l70 x71 r72 =>
                        cases c69 with
                        | black => simp [balance, inorder, List.append_assoc]
                        | red => simp [balance, inorder, List.append_assoc]
                    | red => simp [balance, inorder, List.append_assoc]
            | red => simp [balance, inorder, List.append_assoc]
        | node c73 l74 x75 r76 =>
          cases c73 with
          | black =>
            cases r20 with
            | leaf =>
              cases r with
              | leaf => simp [balance, inorder, List.append_assoc]
              | node c77 l78 x79 r80 =>
                cases c77 with
                | black => simp [balance, inorder, List.append_assoc]
                | red =>
                  cases l78 with
                  | leaf =>
                    cases r80 with
                    | leaf => simp [balance, inorder, List.append_assoc]
                    | node c81 l82 x83 r84 =>
                      cases c81 with
                      | black => simp [balance, inorder, List.append_assoc]
                      | red => simp [balance, inorder, List.append_assoc]
                  | node c85 l86 x87 r88 =>
                    cases c85 with
                    | black =>
                      cases r80 with
                      | leaf => simp [balance, inorder, List.append_assoc]
                      | node c89 l90 x91 r92 =>
                        cases c89 with
                        | black => simp [balance, inorder, List.append_assoc]
                        | red => simp [balance, inorder, List.append_assoc]
                    | red => simp [balance, inorder, List.append_assoc]
            | node c93 l94 x95 r96 =>
              cases c93 with
              | black =>
                cases r with
                | leaf => simp [balance, inorder, List.append_assoc]
                | node c97 l98 x99 r100 =>
                  cases c97 with
                  | black => simp [balance, inorder, List.append_assoc]
                  | red =>
                    cases l98 with
                    | leaf =>
                      cases r100 with
                      | leaf => simp [balance, inorder, List.append_assoc]
                      | node c101 l102 x103 r104 =>
                        cases c101 with
                        | black => simp [balance, inorder, List.append_assoc]
                        | red => simp [balance, inorder, List.append_assoc]
                    | node c105 l106 x107 r108 =>
                      cases c105 with
                      | black =>
                        cases r100 with
                        | leaf => simp [balance, inorder, List.append_assoc]
                        | node c109 l110 x111 r112 =>
                          cases c109 with
                          | black => simp [balance, inorder, List.append_assoc]
                          | red => simp [balance, inorder, List.append_assoc]
                      | red => simp [balance, inorder, List.append_assoc]
              | red => simp [balance, inorder, List.append_assoc]
          | red => simp [balance, inorder, List.append_assoc]

/-- Okasaki's insertion workhorse: descends to a leaf, rebuilds with
`balance` on the way up. -/
def ins : Nat → RBTree → RBTree
  | x, .leaf => .node .red .leaf x .leaf
  | x, .node c l y r =>
      if x < y then balance c (ins x l) y r
      else balance c l y (ins x r)

theorem perm_prefix_swap (l : List Nat) (a b : Nat) (t : List Nat) :
    List.Perm (l ++ a :: b :: t) (b :: (l ++ a :: t)) := by
  induction l with
  | nil => exact List.Perm.swap b a t
  | cons z l ih =>
    refine (List.Perm.cons z ih).trans ?_
    exact List.Perm.swap b z (l ++ a :: t)

theorem inorder_ins (x : Nat) (t : RBTree) :
    List.Perm (inorder (ins x t)) (x :: inorder t) := by
  induction t with
  | leaf => rfl
  | node c l y r ihl ihr =>
    by_cases h1 : x < y
    · simp only [ins, if_pos h1]
      rw [inorder_balance, inorder]
      exact List.Perm.append_right _ ihl
    · simp only [ins, if_neg h1]
      rw [inorder_balance, inorder]
      have h := List.Perm.append_left (inorder l) (List.Perm.cons y ihr)
      exact h.trans (perm_prefix_swap (inorder l) y x (inorder r))

/-- Black-height invariant: every root-to-leaf path crosses exactly
`n` black nodes (leaves count 0). No colour condition. -/
inductive BHOk : RBTree → Nat → Prop
  | leaf : BHOk .leaf 0
  | red : BHOk l n → BHOk r n → BHOk (.node .red l x r) n
  | black : BHOk l n → BHOk r n → BHOk (.node .black l x r) (n + 1)

/-- Computed black height (left spine; meaningful under the
invariant that both spines agree). -/
def bh : RBTree → Nat
  | .leaf => 0
  | .node .red l _ _ => bh l
  | .node .black l _ _ => bh l + 1

theorem BHOk_bh {t : RBTree} {n : Nat} (h : BHOk t n) : bh t = n := by
  induction h with
  | leaf => rfl
  | red _ _ ihl _ => exact ihl
  | black _ _ ihl _ => show bh _ + 1 = _ + 1; rw [ihl]
theorem bh_balance (c : Colour) (l : RBTree) (x : Nat) (r : RBTree) :
    bh (balance c l x r) = (match c with | .red => bh l | .black => bh l + 1) := by
  cases c with
  | red =>
    cases l with
    | leaf => cases r <;> simp [balance, bh]
    | node c1 l1 y r1 => cases r <;> simp [balance, bh]
  | black =>
    cases l with
    | leaf =>
      cases r with
      | leaf => simp [balance, bh]
      | node c1 l2 x3 r4 =>
        cases c1 with
        | black => simp [balance, bh]
        | red =>
          cases l2 with
          | leaf =>
            cases r4 with
            | leaf => simp [balance, bh]
            | node c5 l6 x7 r8 =>
              cases c5 with
              | black => simp [balance, bh]
              | red => simp [balance, bh]
          | node c9 l10 x11 r12 =>
            cases c9 with
            | black =>
              cases r4 with
              | leaf => simp [balance, bh]
              | node c13 l14 x15 r16 =>
                cases c13 with
                | black => simp [balance, bh]
                | red => simp [balance, bh]
            | red => simp [balance, bh]
    | node c17 l18 x19 r20 =>
      cases c17 with
      | black =>
        cases r with
        | leaf => simp [balance, bh]
        | node c21 l22 x23 r24 =>
          cases c21 with
          | black => simp [balance, bh]
          | red =>
            cases l22 with
            | leaf =>
              cases r24 with
              | leaf => simp [balance, bh]
              | node c25 l26 x27 r28 =>
                cases c25 with
                | black => simp [balance, bh]
                | red => simp [balance, bh]
            | node c29 l30 x31 r32 =>
              cases c29 with
              | black =>
                cases r24 with
                | leaf => simp [balance, bh]
                | node c33 l34 x35 r36 =>
                  cases c33 with
                  | black => simp [balance, bh]
                  | red => simp [balance, bh]
              | red => simp [balance, bh]
      | red =>
        cases l18 with
        | leaf =>
          cases r20 with
          | leaf =>
            cases r with
            | leaf => simp [balance, bh]
            | node c37 l38 x39 r40 =>
              cases c37 with
              | black => simp [balance, bh]
              | red =>
                cases l38 with
                | leaf =>
                  cases r40 with
                  | leaf => simp [balance, bh]
                  | node c41 l42 x43 r44 =>
                    cases c41 with
                    | black => simp [balance, bh]
                    | red => simp [balance, bh]
                | node c45 l46 x47 r48 =>
                  cases c45 with
                  | black =>
                    cases r40 with
                    | leaf => simp [balance, bh]
                    | node c49 l50 x51 r52 =>
                      cases c49 with
                      | black => simp [balance, bh]
                      | red => simp [balance, bh]
                  | red => simp [balance, bh]
          | node c53 l54 x55 r56 =>
            cases c53 with
            | black =>
              cases r with
              | leaf => simp [balance, bh]
              | node c57 l58 x59 r60 =>
                cases c57 with
                | black => simp [balance, bh]
                | red =>
                  cases l58 with
                  | leaf =>
                    cases r60 with
                    | leaf => simp [balance, bh]
                    | node c61 l62 x63 r64 =>
                      cases c61 with
                      | black => simp [balance, bh]
                      | red => simp [balance, bh]
                  | node c65 l66 x67 r68 =>
                    cases c65 with
                    | black =>
                      cases r60 with
                      | leaf => simp [balance, bh]
                      | node c69 l70 x71 r72 =>
                        cases c69 with
                        | black => simp [balance, bh]
                        | red => simp [balance, bh]
                    | red => simp [balance, bh]
            | red => simp [balance, bh]
        | node c73 l74 x75 r76 =>
          cases c73 with
          | black =>
            cases r20 with
            | leaf =>
              cases r with
              | leaf => simp [balance, bh]
              | node c77 l78 x79 r80 =>
                cases c77 with
                | black => simp [balance, bh]
                | red =>
                  cases l78 with
                  | leaf =>
                    cases r80 with
                    | leaf => simp [balance, bh]
                    | node c81 l82 x83 r84 =>
                      cases c81 with
                      | black => simp [balance, bh]
                      | red => simp [balance, bh]
                  | node c85 l86 x87 r88 =>
                    cases c85 with
                    | black =>
                      cases r80 with
                      | leaf => simp [balance, bh]
                      | node c89 l90 x91 r92 =>
                        cases c89 with
                        | black => simp [balance, bh]
                        | red => simp [balance, bh]
                    | red => simp [balance, bh]
            | node c93 l94 x95 r96 =>
              cases c93 with
              | black =>
                cases r with
                | leaf => simp [balance, bh]
                | node c97 l98 x99 r100 =>
                  cases c97 with
                  | black => simp [balance, bh]
                  | red =>
                    cases l98 with
                    | leaf =>
                      cases r100 with
                      | leaf => simp [balance, bh]
                      | node c101 l102 x103 r104 =>
                        cases c101 with
                        | black => simp [balance, bh]
                        | red => simp [balance, bh]
                    | node c105 l106 x107 r108 =>
                      cases c105 with
                      | black =>
                        cases r100 with
                        | leaf => simp [balance, bh]
                        | node c109 l110 x111 r112 =>
                          cases c109 with
                          | black => simp [balance, bh]
                          | red => simp [balance, bh]
                      | red => simp [balance, bh]
              | red => simp [balance, bh]
          | red => simp [balance, bh]

/-- Recolour the root black (leaves unchanged). -/
def blacken : RBTree → RBTree
  | .leaf => .leaf
  | .node _ l x r => .node .black l x r

theorem inorder_blacken (t : RBTree) : inorder (blacken t) = inorder t := by
  cases t <;> rfl

/-- Insertion: `ins` with the root blackened. -/
def rbInsert (x : Nat) (t : RBTree) : RBTree := blacken (ins x t)

theorem inorder_rbInsert (x : Nat) (t : RBTree) :
    List.Perm (inorder (rbInsert x t)) (x :: inorder t) := by
  rw [rbInsert, inorder_blacken]
  exact inorder_ins x t

theorem BHOk_balance {c : Colour} {l : RBTree} {x : Nat} {r : RBTree}
    {n : Nat} (hl : BHOk l n) (hr : BHOk r n) :
    BHOk (balance c l x r) (match c with | .red => n | .black => n + 1) := by
  cases c with
  | red =>
    cases l with
    | leaf => cases r <;> simp only [balance] <;> exact BHOk.red hl hr
    | node c1 l1 y r1 => cases r <;> simp only [balance] <;> exact BHOk.red hl hr
  | black =>
    cases l with
    | leaf =>
      cases r with
      | leaf => simp only [balance]; exact BHOk.black hl hr
      | node c1 l2 x3 r4 =>
        cases c1 with
        | black => simp only [balance]; exact BHOk.black hl hr
        | red =>
          cases l2 with
          | leaf =>
            cases r4 with
            | leaf => simp only [balance]; exact BHOk.black hl hr
            | node c5 l6 x7 r8 =>
              cases c5 with
              | black => simp only [balance]; exact BHOk.black hl hr
              | red => simp only [balance]; cases hr with | red h1 h2 => cases h2 with | red h21 h22 => exact BHOk.red (BHOk.black hl h1) (BHOk.black h21 h22)
          | node c9 l10 x11 r12 =>
            cases c9 with
            | black =>
              cases r4 with
              | leaf => simp only [balance]; exact BHOk.black hl hr
              | node c13 l14 x15 r16 =>
                cases c13 with
                | black => simp only [balance]; exact BHOk.black hl hr
                | red => simp only [balance]; cases hr with | red h1 h2 => cases h2 with | red h21 h22 => exact BHOk.red (BHOk.black hl h1) (BHOk.black h21 h22)
            | red => simp only [balance]; cases hr with | red h1 h2 => cases h1 with | red h11 h12 => exact BHOk.red (BHOk.black hl h11) (BHOk.black h12 h2)
    | node c17 l18 x19 r20 =>
      cases c17 with
      | black =>
        cases r with
        | leaf => simp only [balance]; exact BHOk.black hl hr
        | node c21 l22 x23 r24 =>
          cases c21 with
          | black => simp only [balance]; exact BHOk.black hl hr
          | red =>
            cases l22 with
            | leaf =>
              cases r24 with
              | leaf => simp only [balance]; exact BHOk.black hl hr
              | node c25 l26 x27 r28 =>
                cases c25 with
                | black => simp only [balance]; exact BHOk.black hl hr
                | red => simp only [balance]; cases hr with | red h1 h2 => cases h2 with | red h21 h22 => exact BHOk.red (BHOk.black hl h1) (BHOk.black h21 h22)
            | node c29 l30 x31 r32 =>
              cases c29 with
              | black =>
                cases r24 with
                | leaf => simp only [balance]; exact BHOk.black hl hr
                | node c33 l34 x35 r36 =>
                  cases c33 with
                  | black => simp only [balance]; exact BHOk.black hl hr
                  | red => simp only [balance]; cases hr with | red h1 h2 => cases h2 with | red h21 h22 => exact BHOk.red (BHOk.black hl h1) (BHOk.black h21 h22)
              | red => simp only [balance]; cases hr with | red h1 h2 => cases h1 with | red h11 h12 => exact BHOk.red (BHOk.black hl h11) (BHOk.black h12 h2)
      | red =>
        cases l18 with
        | leaf =>
          cases r20 with
          | leaf =>
            cases r with
            | leaf => simp only [balance]; exact BHOk.black hl hr
            | node c37 l38 x39 r40 =>
              cases c37 with
              | black => simp only [balance]; exact BHOk.black hl hr
              | red =>
                cases l38 with
                | leaf =>
                  cases r40 with
                  | leaf => simp only [balance]; exact BHOk.black hl hr
                  | node c41 l42 x43 r44 =>
                    cases c41 with
                    | black => simp only [balance]; exact BHOk.black hl hr
                    | red => simp only [balance]; cases hr with | red h1 h2 => cases h2 with | red h21 h22 => exact BHOk.red (BHOk.black hl h1) (BHOk.black h21 h22)
                | node c45 l46 x47 r48 =>
                  cases c45 with
                  | black =>
                    cases r40 with
                    | leaf => simp only [balance]; exact BHOk.black hl hr
                    | node c49 l50 x51 r52 =>
                      cases c49 with
                      | black => simp only [balance]; exact BHOk.black hl hr
                      | red => simp only [balance]; cases hr with | red h1 h2 => cases h2 with | red h21 h22 => exact BHOk.red (BHOk.black hl h1) (BHOk.black h21 h22)
                  | red => simp only [balance]; cases hr with | red h1 h2 => cases h1 with | red h11 h12 => exact BHOk.red (BHOk.black hl h11) (BHOk.black h12 h2)
          | node c53 l54 x55 r56 =>
            cases c53 with
            | black =>
              cases r with
              | leaf => simp only [balance]; exact BHOk.black hl hr
              | node c57 l58 x59 r60 =>
                cases c57 with
                | black => simp only [balance]; exact BHOk.black hl hr
                | red =>
                  cases l58 with
                  | leaf =>
                    cases r60 with
                    | leaf => simp only [balance]; exact BHOk.black hl hr
                    | node c61 l62 x63 r64 =>
                      cases c61 with
                      | black => simp only [balance]; exact BHOk.black hl hr
                      | red => simp only [balance]; cases hr with | red h1 h2 => cases h2 with | red h21 h22 => exact BHOk.red (BHOk.black hl h1) (BHOk.black h21 h22)
                  | node c65 l66 x67 r68 =>
                    cases c65 with
                    | black =>
                      cases r60 with
                      | leaf => simp only [balance]; exact BHOk.black hl hr
                      | node c69 l70 x71 r72 =>
                        cases c69 with
                        | black => simp only [balance]; exact BHOk.black hl hr
                        | red => simp only [balance]; cases hr with | red h1 h2 => cases h2 with | red h21 h22 => exact BHOk.red (BHOk.black hl h1) (BHOk.black h21 h22)
                    | red => simp only [balance]; cases hr with | red h1 h2 => cases h1 with | red h11 h12 => exact BHOk.red (BHOk.black hl h11) (BHOk.black h12 h2)
            | red => simp only [balance]; cases hl with | red h1 h2 => cases h2 with | red h21 h22 => exact BHOk.red (BHOk.black h1 h21) (BHOk.black h22 hr)
        | node c73 l74 x75 r76 =>
          cases c73 with
          | black =>
            cases r20 with
            | leaf =>
              cases r with
              | leaf => simp only [balance]; exact BHOk.black hl hr
              | node c77 l78 x79 r80 =>
                cases c77 with
                | black => simp only [balance]; exact BHOk.black hl hr
                | red =>
                  cases l78 with
                  | leaf =>
                    cases r80 with
                    | leaf => simp only [balance]; exact BHOk.black hl hr
                    | node c81 l82 x83 r84 =>
                      cases c81 with
                      | black => simp only [balance]; exact BHOk.black hl hr
                      | red => simp only [balance]; cases hr with | red h1 h2 => cases h2 with | red h21 h22 => exact BHOk.red (BHOk.black hl h1) (BHOk.black h21 h22)
                  | node c85 l86 x87 r88 =>
                    cases c85 with
                    | black =>
                      cases r80 with
                      | leaf => simp only [balance]; exact BHOk.black hl hr
                      | node c89 l90 x91 r92 =>
                        cases c89 with
                        | black => simp only [balance]; exact BHOk.black hl hr
                        | red => simp only [balance]; cases hr with | red h1 h2 => cases h2 with | red h21 h22 => exact BHOk.red (BHOk.black hl h1) (BHOk.black h21 h22)
                    | red => simp only [balance]; cases hr with | red h1 h2 => cases h1 with | red h11 h12 => exact BHOk.red (BHOk.black hl h11) (BHOk.black h12 h2)
            | node c93 l94 x95 r96 =>
              cases c93 with
              | black =>
                cases r with
                | leaf => simp only [balance]; exact BHOk.black hl hr
                | node c97 l98 x99 r100 =>
                  cases c97 with
                  | black => simp only [balance]; exact BHOk.black hl hr
                  | red =>
                    cases l98 with
                    | leaf =>
                      cases r100 with
                      | leaf => simp only [balance]; exact BHOk.black hl hr
                      | node c101 l102 x103 r104 =>
                        cases c101 with
                        | black => simp only [balance]; exact BHOk.black hl hr
                        | red => simp only [balance]; cases hr with | red h1 h2 => cases h2 with | red h21 h22 => exact BHOk.red (BHOk.black hl h1) (BHOk.black h21 h22)
                    | node c105 l106 x107 r108 =>
                      cases c105 with
                      | black =>
                        cases r100 with
                        | leaf => simp only [balance]; exact BHOk.black hl hr
                        | node c109 l110 x111 r112 =>
                          cases c109 with
                          | black => simp only [balance]; exact BHOk.black hl hr
                          | red => simp only [balance]; cases hr with | red h1 h2 => cases h2 with | red h21 h22 => exact BHOk.red (BHOk.black hl h1) (BHOk.black h21 h22)
                      | red => simp only [balance]; cases hr with | red h1 h2 => cases h1 with | red h11 h12 => exact BHOk.red (BHOk.black hl h11) (BHOk.black h12 h2)
              | red => simp only [balance]; cases hl with | red h1 h2 => cases h2 with | red h21 h22 => exact BHOk.red (BHOk.black h1 h21) (BHOk.black h22 hr)
          | red => simp only [balance]; cases hl with | red h1 h2 => cases h1 with | red h11 h12 => exact BHOk.red (BHOk.black h11 h12) (BHOk.black h2 hr)

theorem BHOk_ins (x : Nat) {t : RBTree} {n : Nat} (h : BHOk t n) :
    BHOk (ins x t) n := by
  induction h with
  | leaf => exact BHOk.red BHOk.leaf BHOk.leaf
  | red hl hr ihl ihr =>
    simp only [ins]
    split
    · exact BHOk_balance ihl hr
    · exact BHOk_balance hl ihr
  | black hl hr ihl ihr =>
    simp only [ins]
    split
    · exact BHOk_balance ihl hr
    · exact BHOk_balance hl ihr

theorem BHOk_blacken {t : RBTree} {n : Nat} (h : BHOk t n) :
    ∃ m, BHOk (blacken t) m := by
  cases t with
  | leaf => exact ⟨0, BHOk.leaf⟩
  | node c l y r =>
    cases c with
    | black => exact ⟨n, h⟩
    | red =>
      cases h with
      | red hl hr => exact ⟨n + 1, BHOk.black hl hr⟩

theorem BHOk_rbInsert (x : Nat) {t : RBTree} {n : Nat} (h : BHOk t n) :
    ∃ m, BHOk (rbInsert x t) m :=
  BHOk_blacken (BHOk_ins x h)

/-- The root is not red (leaves count as not red). -/
def IsBlackish : RBTree → Prop
  | .leaf => True
  | .node .red _ _ _ => False
  | .node .black _ _ _ => True

/-- No red node has a red child, anywhere. -/
inductive NoRR : RBTree → Prop
  | leaf : NoRR .leaf
  | black : NoRR l → NoRR r → NoRR (.node .black l x r)
  | red : NoRR l → NoRR r → IsBlackish l → IsBlackish r →
      NoRR (.node .red l x r)

/-- The root-relaxed form: both children satisfy `NoRR` (the root
itself may be red with a red child). This is what `ins` returns. -/
def NoRRRoot : RBTree → Prop
  | .leaf => True
  | .node _ l _ r => NoRR l ∧ NoRR r

theorem NoRR_root {t : RBTree} (h : NoRR t) : NoRRRoot t := by
  cases t with
  | leaf => trivial
  | node c l y r =>
    cases h with
    | black hl hr => exact ⟨hl, hr⟩
    | red hl hr _ _ => exact ⟨hl, hr⟩

theorem blacken_NoRR {t : RBTree} (h : NoRRRoot t) : NoRR (blacken t) := by
  cases t with
  | leaf => exact NoRR.leaf
  | node c l y r => exact NoRR.black h.1 h.2

theorem balance_NoRRRoot_red {l : RBTree} {x : Nat} {r : RBTree}
    (hl : NoRR l) (hr : NoRR r) : NoRRRoot (balance .red l x r) := by
  cases l with
  | leaf => cases r <;> simp only [balance] <;> exact ⟨hl, hr⟩
  | node c1 l1 y r1 => cases r <;> simp only [balance] <;> exact ⟨hl, hr⟩
theorem balance_NoRR_L {l : RBTree} {x : Nat} {r : RBTree}
    (hl : NoRRRoot l) (hr : NoRR r) : NoRR (balance .black l x r) := by
  cases l with
  | leaf =>
    cases r with
    | leaf => simp only [balance]; exact NoRR.black NoRR.leaf hr
    | node c1 l2 x3 r4 =>
      cases c1 with
      | black => simp only [balance]; exact NoRR.black NoRR.leaf hr
      | red =>
        cases l2 with
        | leaf =>
          cases r4 with
          | leaf => simp only [balance]; exact NoRR.black NoRR.leaf hr
          | node c5 l6 x7 r8 =>
            cases c5 with
            | black => simp only [balance]; exact NoRR.black NoRR.leaf hr
            | red => cases hr with | red _ _ _ hc => exact False.elim hc
        | node c9 l10 x11 r12 =>
          cases c9 with
          | black =>
            cases r4 with
            | leaf => simp only [balance]; exact NoRR.black NoRR.leaf hr
            | node c13 l14 x15 r16 =>
              cases c13 with
              | black => simp only [balance]; exact NoRR.black NoRR.leaf hr
              | red => cases hr with | red _ _ _ hc => exact False.elim hc
          | red => cases hr with | red _ _ hb _ => exact False.elim hb
  | node c17 l18 x19 r20 =>
    cases c17 with
    | black =>
      cases r with
      | leaf => simp only [balance]; obtain ⟨h1, h2⟩ := hl; exact NoRR.black (NoRR.black h1 h2) hr
      | node c21 l22 x23 r24 =>
        cases c21 with
        | black => simp only [balance]; obtain ⟨h1, h2⟩ := hl; exact NoRR.black (NoRR.black h1 h2) hr
        | red =>
          cases l22 with
          | leaf =>
            cases r24 with
            | leaf => simp only [balance]; obtain ⟨h1, h2⟩ := hl; exact NoRR.black (NoRR.black h1 h2) hr
            | node c25 l26 x27 r28 =>
              cases c25 with
              | black => simp only [balance]; obtain ⟨h1, h2⟩ := hl; exact NoRR.black (NoRR.black h1 h2) hr
              | red => cases hr with | red _ _ _ hc => exact False.elim hc
          | node c29 l30 x31 r32 =>
            cases c29 with
            | black =>
              cases r24 with
              | leaf => simp only [balance]; obtain ⟨h1, h2⟩ := hl; exact NoRR.black (NoRR.black h1 h2) hr
              | node c33 l34 x35 r36 =>
                cases c33 with
                | black => simp only [balance]; obtain ⟨h1, h2⟩ := hl; exact NoRR.black (NoRR.black h1 h2) hr
                | red => cases hr with | red _ _ _ hc => exact False.elim hc
            | red => cases hr with | red _ _ hb _ => exact False.elim hb
    | red =>
      cases l18 with
      | leaf =>
        cases r20 with
        | leaf =>
          cases r with
          | leaf => simp only [balance]; obtain ⟨h1, h2⟩ := hl; exact NoRR.black (NoRR.red h1 h2 trivial trivial) hr
          | node c37 l38 x39 r40 =>
            cases c37 with
            | black => simp only [balance]; obtain ⟨h1, h2⟩ := hl; exact NoRR.black (NoRR.red h1 h2 trivial trivial) hr
            | red =>
              cases l38 with
              | leaf =>
                cases r40 with
                | leaf => simp only [balance]; obtain ⟨h1, h2⟩ := hl; exact NoRR.black (NoRR.red h1 h2 trivial trivial) hr
                | node c41 l42 x43 r44 =>
                  cases c41 with
                  | black => simp only [balance]; obtain ⟨h1, h2⟩ := hl; exact NoRR.black (NoRR.red h1 h2 trivial trivial) hr
                  | red => cases hr with | red _ _ _ hc => exact False.elim hc
              | node c45 l46 x47 r48 =>
                cases c45 with
                | black =>
                  cases r40 with
                  | leaf => simp only [balance]; obtain ⟨h1, h2⟩ := hl; exact NoRR.black (NoRR.red h1 h2 trivial trivial) hr
                  | node c49 l50 x51 r52 =>
                    cases c49 with
                    | black => simp only [balance]; obtain ⟨h1, h2⟩ := hl; exact NoRR.black (NoRR.red h1 h2 trivial trivial) hr
                    | red => cases hr with | red _ _ _ hc => exact False.elim hc
                | red => cases hr with | red _ _ hb _ => exact False.elim hb
        | node c53 l54 x55 r56 =>
          cases c53 with
          | black =>
            cases r with
            | leaf => simp only [balance]; obtain ⟨h1, h2⟩ := hl; exact NoRR.black (NoRR.red h1 h2 trivial trivial) hr
            | node c57 l58 x59 r60 =>
              cases c57 with
              | black => simp only [balance]; obtain ⟨h1, h2⟩ := hl; exact NoRR.black (NoRR.red h1 h2 trivial trivial) hr
              | red =>
                cases l58 with
                | leaf =>
                  cases r60 with
                  | leaf => simp only [balance]; obtain ⟨h1, h2⟩ := hl; exact NoRR.black (NoRR.red h1 h2 trivial trivial) hr
                  | node c61 l62 x63 r64 =>
                    cases c61 with
                    | black => simp only [balance]; obtain ⟨h1, h2⟩ := hl; exact NoRR.black (NoRR.red h1 h2 trivial trivial) hr
                    | red => cases hr with | red _ _ _ hc => exact False.elim hc
                | node c65 l66 x67 r68 =>
                  cases c65 with
                  | black =>
                    cases r60 with
                    | leaf => simp only [balance]; obtain ⟨h1, h2⟩ := hl; exact NoRR.black (NoRR.red h1 h2 trivial trivial) hr
                    | node c69 l70 x71 r72 =>
                      cases c69 with
                      | black => simp only [balance]; obtain ⟨h1, h2⟩ := hl; exact NoRR.black (NoRR.red h1 h2 trivial trivial) hr
                      | red => cases hr with | red _ _ _ hc => exact False.elim hc
                  | red => cases hr with | red _ _ hb _ => exact False.elim hb
          | red => simp only [balance]; obtain ⟨h1, h2⟩ := hl; cases h2 with | red hb hc _ _ => exact NoRR.red (NoRR.black h1 hb) (NoRR.black hc hr) trivial trivial
      | node c73 l74 x75 r76 =>
        cases c73 with
        | black =>
          cases r20 with
          | leaf =>
            cases r with
            | leaf => simp only [balance]; obtain ⟨h1, h2⟩ := hl; exact NoRR.black (NoRR.red h1 h2 trivial trivial) hr
            | node c77 l78 x79 r80 =>
              cases c77 with
              | black => simp only [balance]; obtain ⟨h1, h2⟩ := hl; exact NoRR.black (NoRR.red h1 h2 trivial trivial) hr
              | red =>
                cases l78 with
                | leaf =>
                  cases r80 with
                  | leaf => simp only [balance]; obtain ⟨h1, h2⟩ := hl; exact NoRR.black (NoRR.red h1 h2 trivial trivial) hr
                  | node c81 l82 x83 r84 =>
                    cases c81 with
                    | black => simp only [balance]; obtain ⟨h1, h2⟩ := hl; exact NoRR.black (NoRR.red h1 h2 trivial trivial) hr
                    | red => cases hr with | red _ _ _ hc => exact False.elim hc
                | node c85 l86 x87 r88 =>
                  cases c85 with
                  | black =>
                    cases r80 with
                    | leaf => simp only [balance]; obtain ⟨h1, h2⟩ := hl; exact NoRR.black (NoRR.red h1 h2 trivial trivial) hr
                    | node c89 l90 x91 r92 =>
                      cases c89 with
                      | black => simp only [balance]; obtain ⟨h1, h2⟩ := hl; exact NoRR.black (NoRR.red h1 h2 trivial trivial) hr
                      | red => cases hr with | red _ _ _ hc => exact False.elim hc
                  | red => cases hr with | red _ _ hb _ => exact False.elim hb
          | node c93 l94 x95 r96 =>
            cases c93 with
            | black =>
              cases r with
              | leaf => simp only [balance]; obtain ⟨h1, h2⟩ := hl; exact NoRR.black (NoRR.red h1 h2 trivial trivial) hr
              | node c97 l98 x99 r100 =>
                cases c97 with
                | black => simp only [balance]; obtain ⟨h1, h2⟩ := hl; exact NoRR.black (NoRR.red h1 h2 trivial trivial) hr
                | red =>
                  cases l98 with
                  | leaf =>
                    cases r100 with
                    | leaf => simp only [balance]; obtain ⟨h1, h2⟩ := hl; exact NoRR.black (NoRR.red h1 h2 trivial trivial) hr
                    | node c101 l102 x103 r104 =>
                      cases c101 with
                      | black => simp only [balance]; obtain ⟨h1, h2⟩ := hl; exact NoRR.black (NoRR.red h1 h2 trivial trivial) hr
                      | red => cases hr with | red _ _ _ hc => exact False.elim hc
                  | node c105 l106 x107 r108 =>
                    cases c105 with
                    | black =>
                      cases r100 with
                      | leaf => simp only [balance]; obtain ⟨h1, h2⟩ := hl; exact NoRR.black (NoRR.red h1 h2 trivial trivial) hr
                      | node c109 l110 x111 r112 =>
                        cases c109 with
                        | black => simp only [balance]; obtain ⟨h1, h2⟩ := hl; exact NoRR.black (NoRR.red h1 h2 trivial trivial) hr
                        | red => cases hr with | red _ _ _ hc => exact False.elim hc
                    | red => cases hr with | red _ _ hb _ => exact False.elim hb
            | red => simp only [balance]; obtain ⟨h1, h2⟩ := hl; cases h2 with | red hb hc _ _ => exact NoRR.red (NoRR.black h1 hb) (NoRR.black hc hr) trivial trivial
        | red => simp only [balance]; obtain ⟨h1, h2⟩ := hl; cases h1 with | red ha hb _ _ => exact NoRR.red (NoRR.black ha hb) (NoRR.black h2 hr) trivial trivial

theorem balance_NoRR_R {l : RBTree} {x : Nat} {r : RBTree}
    (hl : NoRR l) (hr : NoRRRoot r) : NoRR (balance .black l x r) := by
  cases l with
  | leaf =>
    cases r with
    | leaf => simp only [balance]; exact NoRR.black hl NoRR.leaf
    | node c113 l114 x115 r116 =>
      cases c113 with
      | black => simp only [balance]; obtain ⟨h1, h2⟩ := hr; exact NoRR.black hl (NoRR.black h1 h2)
      | red =>
        cases l114 with
        | leaf =>
          cases r116 with
          | leaf => simp only [balance]; obtain ⟨h1, h2⟩ := hr; exact NoRR.black hl (NoRR.red h1 h2 trivial trivial)
          | node c117 l118 x119 r120 =>
            cases c117 with
            | black => simp only [balance]; obtain ⟨h1, h2⟩ := hr; exact NoRR.black hl (NoRR.red h1 h2 trivial trivial)
            | red => simp only [balance]; obtain ⟨h1, h2⟩ := hr; cases h2 with | red hc hd _ _ => exact NoRR.red (NoRR.black hl h1) (NoRR.black hc hd) trivial trivial
        | node c121 l122 x123 r124 =>
          cases c121 with
          | black =>
            cases r116 with
            | leaf => simp only [balance]; obtain ⟨h1, h2⟩ := hr; exact NoRR.black hl (NoRR.red h1 h2 trivial trivial)
            | node c125 l126 x127 r128 =>
              cases c125 with
              | black => simp only [balance]; obtain ⟨h1, h2⟩ := hr; exact NoRR.black hl (NoRR.red h1 h2 trivial trivial)
              | red => simp only [balance]; obtain ⟨h1, h2⟩ := hr; cases h2 with | red hc hd _ _ => exact NoRR.red (NoRR.black hl h1) (NoRR.black hc hd) trivial trivial
          | red => simp only [balance]; obtain ⟨h1, h2⟩ := hr; cases h1 with | red hb hc _ _ => exact NoRR.red (NoRR.black hl hb) (NoRR.black hc h2) trivial trivial
  | node c129 l130 x131 r132 =>
    cases c129 with
    | black =>
      cases r with
      | leaf => simp only [balance]; exact NoRR.black hl NoRR.leaf
      | node c133 l134 x135 r136 =>
        cases c133 with
        | black => simp only [balance]; obtain ⟨h1, h2⟩ := hr; exact NoRR.black hl (NoRR.black h1 h2)
        | red =>
          cases l134 with
          | leaf =>
            cases r136 with
            | leaf => simp only [balance]; obtain ⟨h1, h2⟩ := hr; exact NoRR.black hl (NoRR.red h1 h2 trivial trivial)
            | node c137 l138 x139 r140 =>
              cases c137 with
              | black => simp only [balance]; obtain ⟨h1, h2⟩ := hr; exact NoRR.black hl (NoRR.red h1 h2 trivial trivial)
              | red => simp only [balance]; obtain ⟨h1, h2⟩ := hr; cases h2 with | red hc hd _ _ => exact NoRR.red (NoRR.black hl h1) (NoRR.black hc hd) trivial trivial
          | node c141 l142 x143 r144 =>
            cases c141 with
            | black =>
              cases r136 with
              | leaf => simp only [balance]; obtain ⟨h1, h2⟩ := hr; exact NoRR.black hl (NoRR.red h1 h2 trivial trivial)
              | node c145 l146 x147 r148 =>
                cases c145 with
                | black => simp only [balance]; obtain ⟨h1, h2⟩ := hr; exact NoRR.black hl (NoRR.red h1 h2 trivial trivial)
                | red => simp only [balance]; obtain ⟨h1, h2⟩ := hr; cases h2 with | red hc hd _ _ => exact NoRR.red (NoRR.black hl h1) (NoRR.black hc hd) trivial trivial
            | red => simp only [balance]; obtain ⟨h1, h2⟩ := hr; cases h1 with | red hb hc _ _ => exact NoRR.red (NoRR.black hl hb) (NoRR.black hc h2) trivial trivial
    | red =>
      cases l130 with
      | leaf =>
        cases r132 with
        | leaf =>
          cases r with
          | leaf => simp only [balance]; exact NoRR.black hl NoRR.leaf
          | node c149 l150 x151 r152 =>
            cases c149 with
            | black => simp only [balance]; obtain ⟨h1, h2⟩ := hr; exact NoRR.black hl (NoRR.black h1 h2)
            | red =>
              cases l150 with
              | leaf =>
                cases r152 with
                | leaf => simp only [balance]; obtain ⟨h1, h2⟩ := hr; exact NoRR.black hl (NoRR.red h1 h2 trivial trivial)
                | node c153 l154 x155 r156 =>
                  cases c153 with
                  | black => simp only [balance]; obtain ⟨h1, h2⟩ := hr; exact NoRR.black hl (NoRR.red h1 h2 trivial trivial)
                  | red => simp only [balance]; obtain ⟨h1, h2⟩ := hr; cases h2 with | red hc hd _ _ => exact NoRR.red (NoRR.black hl h1) (NoRR.black hc hd) trivial trivial
              | node c157 l158 x159 r160 =>
                cases c157 with
                | black =>
                  cases r152 with
                  | leaf => simp only [balance]; obtain ⟨h1, h2⟩ := hr; exact NoRR.black hl (NoRR.red h1 h2 trivial trivial)
                  | node c161 l162 x163 r164 =>
                    cases c161 with
                    | black => simp only [balance]; obtain ⟨h1, h2⟩ := hr; exact NoRR.black hl (NoRR.red h1 h2 trivial trivial)
                    | red => simp only [balance]; obtain ⟨h1, h2⟩ := hr; cases h2 with | red hc hd _ _ => exact NoRR.red (NoRR.black hl h1) (NoRR.black hc hd) trivial trivial
                | red => simp only [balance]; obtain ⟨h1, h2⟩ := hr; cases h1 with | red hb hc _ _ => exact NoRR.red (NoRR.black hl hb) (NoRR.black hc h2) trivial trivial
        | node c165 l166 x167 r168 =>
          cases c165 with
          | black =>
            cases r with
            | leaf => simp only [balance]; exact NoRR.black hl NoRR.leaf
            | node c169 l170 x171 r172 =>
              cases c169 with
              | black => simp only [balance]; obtain ⟨h1, h2⟩ := hr; exact NoRR.black hl (NoRR.black h1 h2)
              | red =>
                cases l170 with
                | leaf =>
                  cases r172 with
                  | leaf => simp only [balance]; obtain ⟨h1, h2⟩ := hr; exact NoRR.black hl (NoRR.red h1 h2 trivial trivial)
                  | node c173 l174 x175 r176 =>
                    cases c173 with
                    | black => simp only [balance]; obtain ⟨h1, h2⟩ := hr; exact NoRR.black hl (NoRR.red h1 h2 trivial trivial)
                    | red => simp only [balance]; obtain ⟨h1, h2⟩ := hr; cases h2 with | red hc hd _ _ => exact NoRR.red (NoRR.black hl h1) (NoRR.black hc hd) trivial trivial
                | node c177 l178 x179 r180 =>
                  cases c177 with
                  | black =>
                    cases r172 with
                    | leaf => simp only [balance]; obtain ⟨h1, h2⟩ := hr; exact NoRR.black hl (NoRR.red h1 h2 trivial trivial)
                    | node c181 l182 x183 r184 =>
                      cases c181 with
                      | black => simp only [balance]; obtain ⟨h1, h2⟩ := hr; exact NoRR.black hl (NoRR.red h1 h2 trivial trivial)
                      | red => simp only [balance]; obtain ⟨h1, h2⟩ := hr; cases h2 with | red hc hd _ _ => exact NoRR.red (NoRR.black hl h1) (NoRR.black hc hd) trivial trivial
                  | red => simp only [balance]; obtain ⟨h1, h2⟩ := hr; cases h1 with | red hb hc _ _ => exact NoRR.red (NoRR.black hl hb) (NoRR.black hc h2) trivial trivial
          | red => cases hl with | red _ _ _ hc => exact False.elim hc
      | node c185 l186 x187 r188 =>
        cases c185 with
        | black =>
          cases r132 with
          | leaf =>
            cases r with
            | leaf => simp only [balance]; exact NoRR.black hl NoRR.leaf
            | node c189 l190 x191 r192 =>
              cases c189 with
              | black => simp only [balance]; obtain ⟨h1, h2⟩ := hr; exact NoRR.black hl (NoRR.black h1 h2)
              | red =>
                cases l190 with
                | leaf =>
                  cases r192 with
                  | leaf => simp only [balance]; obtain ⟨h1, h2⟩ := hr; exact NoRR.black hl (NoRR.red h1 h2 trivial trivial)
                  | node c193 l194 x195 r196 =>
                    cases c193 with
                    | black => simp only [balance]; obtain ⟨h1, h2⟩ := hr; exact NoRR.black hl (NoRR.red h1 h2 trivial trivial)
                    | red => simp only [balance]; obtain ⟨h1, h2⟩ := hr; cases h2 with | red hc hd _ _ => exact NoRR.red (NoRR.black hl h1) (NoRR.black hc hd) trivial trivial
                | node c197 l198 x199 r200 =>
                  cases c197 with
                  | black =>
                    cases r192 with
                    | leaf => simp only [balance]; obtain ⟨h1, h2⟩ := hr; exact NoRR.black hl (NoRR.red h1 h2 trivial trivial)
                    | node c201 l202 x203 r204 =>
                      cases c201 with
                      | black => simp only [balance]; obtain ⟨h1, h2⟩ := hr; exact NoRR.black hl (NoRR.red h1 h2 trivial trivial)
                      | red => simp only [balance]; obtain ⟨h1, h2⟩ := hr; cases h2 with | red hc hd _ _ => exact NoRR.red (NoRR.black hl h1) (NoRR.black hc hd) trivial trivial
                  | red => simp only [balance]; obtain ⟨h1, h2⟩ := hr; cases h1 with | red hb hc _ _ => exact NoRR.red (NoRR.black hl hb) (NoRR.black hc h2) trivial trivial
          | node c205 l206 x207 r208 =>
            cases c205 with
            | black =>
              cases r with
              | leaf => simp only [balance]; exact NoRR.black hl NoRR.leaf
              | node c209 l210 x211 r212 =>
                cases c209 with
                | black => simp only [balance]; obtain ⟨h1, h2⟩ := hr; exact NoRR.black hl (NoRR.black h1 h2)
                | red =>
                  cases l210 with
                  | leaf =>
                    cases r212 with
                    | leaf => simp only [balance]; obtain ⟨h1, h2⟩ := hr; exact NoRR.black hl (NoRR.red h1 h2 trivial trivial)
                    | node c213 l214 x215 r216 =>
                      cases c213 with
                      | black => simp only [balance]; obtain ⟨h1, h2⟩ := hr; exact NoRR.black hl (NoRR.red h1 h2 trivial trivial)
                      | red => simp only [balance]; obtain ⟨h1, h2⟩ := hr; cases h2 with | red hc hd _ _ => exact NoRR.red (NoRR.black hl h1) (NoRR.black hc hd) trivial trivial
                  | node c217 l218 x219 r220 =>
                    cases c217 with
                    | black =>
                      cases r212 with
                      | leaf => simp only [balance]; obtain ⟨h1, h2⟩ := hr; exact NoRR.black hl (NoRR.red h1 h2 trivial trivial)
                      | node c221 l222 x223 r224 =>
                        cases c221 with
                        | black => simp only [balance]; obtain ⟨h1, h2⟩ := hr; exact NoRR.black hl (NoRR.red h1 h2 trivial trivial)
                        | red => simp only [balance]; obtain ⟨h1, h2⟩ := hr; cases h2 with | red hc hd _ _ => exact NoRR.red (NoRR.black hl h1) (NoRR.black hc hd) trivial trivial
                    | red => simp only [balance]; obtain ⟨h1, h2⟩ := hr; cases h1 with | red hb hc _ _ => exact NoRR.red (NoRR.black hl hb) (NoRR.black hc h2) trivial trivial
            | red => cases hl with | red _ _ _ hc => exact False.elim hc
        | red => cases hl with | red _ _ hb _ => exact False.elim hb

theorem ins_NoRR (x : Nat) {t : RBTree} (h : NoRR t) :
    NoRRRoot (ins x t) ∧ (IsBlackish t → NoRR (ins x t)) := by
  induction t with
  | leaf =>
    exact ⟨⟨NoRR.leaf, NoRR.leaf⟩,
      fun _ => NoRR.red NoRR.leaf NoRR.leaf trivial trivial⟩
  | node c l y r ihl ihr =>
    cases c with
    | black =>
      cases h with
      | black hl hr =>
        by_cases hlt : x < y
        · have step := balance_NoRR_L (x := y) (ihl hl).1 hr
          simp only [ins, if_pos hlt]
          exact ⟨NoRR_root step, fun _ => step⟩
        · have step := balance_NoRR_R (x := y) hl (ihr hr).1
          simp only [ins, if_neg hlt]
          exact ⟨NoRR_root step, fun _ => step⟩
    | red =>
      cases h with
      | red hl hr hbl hbr =>
        by_cases hlt : x < y
        · have n1 : NoRR (ins x l) := (ihl hl).2 hbl
          have step := balance_NoRRRoot_red (x := y) n1 hr
          simp only [ins, if_pos hlt]
          exact ⟨step, fun hb => False.elim hb⟩
        · have n1 : NoRR (ins x r) := (ihr hr).2 hbr
          have step := balance_NoRRRoot_red (x := y) hl n1
          simp only [ins, if_neg hlt]
          exact ⟨step, fun hb => False.elim hb⟩

theorem rbInsert_NoRR (x : Nat) {t : RBTree} (h : NoRR t) :
    NoRR (rbInsert x t) :=
  blacken_NoRR (ins_NoRR x h).1

theorem mem_inorder_node {c : Colour} {l : RBTree} {x z : Nat} {r : RBTree} :
    z ∈ inorder (.node c l x r) ↔ z ∈ inorder l ∨ z = x ∨ z ∈ inorder r := by
  simp [inorder, List.mem_append, List.mem_cons]

/-- Binary-search-tree ordering, in the rotation-closed form for a
bag: every key in the left subtree is `≤` the node's key, and the
node's key is `≤` every key in the right subtree. (The strict-left
form is NOT preserved by the rotations when duplicate keys are
present — a rotation can move an equal key into the left subtree.) -/
inductive BST : RBTree → Prop
  | leaf : BST .leaf
  | node : BST l → BST r → (∀ y ∈ inorder l, y ≤ x) →
      (∀ y ∈ inorder r, x ≤ y) → BST (.node c l x r)

theorem BST_P1 {a b c' d : RBTree} {x' y x : Nat}
    (hl : BST (.node .red (.node .red a x' b) y c')) (hr : BST d)
    (hlt : ∀ z ∈ inorder (.node .red (.node .red a x' b) y c'), z ≤ x)
    (hge : ∀ z ∈ inorder d, x ≤ z) :
    BST (.node .red (.node .black a x' b) y (.node .black c' x d)) := by
  cases hl with
  | node hbl hbr hltl hgel =>
    cases hbl with
    | node hba hbb hlta hgeb =>
      have hx'y : x' ≤ y :=
        hltl x' (mem_inorder_node.mpr (Or.inr (Or.inl rfl)))
      have hyx : y ≤ x :=
        hlt y (mem_inorder_node.mpr (Or.inr (Or.inl rfl)))
      refine BST.node (BST.node hba hbb hlta hgeb)
        (BST.node hbr hr ?_ hge) ?_ ?_
      · intro z hz
        exact hlt z (mem_inorder_node.mpr (Or.inr (Or.inr hz)))
      · intro z hz
        rcases mem_inorder_node.mp hz with h | h | h
        · exact Nat.le_trans (hlta z h) hx'y
        · subst h; exact hx'y
        · exact hltl z (mem_inorder_node.mpr (Or.inr (Or.inr h)))
      · intro z hz
        rcases mem_inorder_node.mp hz with h | h | h
        · exact hgel z h
        · subst h; exact hyx
        · exact Nat.le_trans hyx (hge z h)

theorem BST_P2 {a b c' d : RBTree} {u v w : Nat}
    (hl : BST (.node .red a u (.node .red b v c'))) (hr : BST d)
    (hlt : ∀ z ∈ inorder (.node .red a u (.node .red b v c')), z ≤ w)
    (hge : ∀ z ∈ inorder d, w ≤ z) :
    BST (.node .red (.node .black a u b) v (.node .black c' w d)) := by
  cases hl with
  | node hbl hbr hltl hgel =>
    cases hbr with
    | node hbb hbc hltb hgec =>
      have huv : u ≤ v :=
        hgel v (mem_inorder_node.mpr (Or.inr (Or.inl rfl)))
      have hvw : v ≤ w :=
        hlt v (mem_inorder_node.mpr
          (Or.inr (Or.inr (mem_inorder_node.mpr (Or.inr (Or.inl rfl))))))
      refine BST.node (BST.node hbl hbb hltl ?_)
        (BST.node hbc hr ?_ hge) ?_ ?_
      · intro z hz
        exact hgel z (mem_inorder_node.mpr (Or.inl hz))
      · intro z hz
        exact hlt z (mem_inorder_node.mpr
          (Or.inr (Or.inr (mem_inorder_node.mpr (Or.inr (Or.inr hz))))))
      · intro z hz
        rcases mem_inorder_node.mp hz with h | h | h
        · exact Nat.le_trans (hltl z h) huv
        · subst h; exact huv
        · exact hltb z h
      · intro z hz
        rcases mem_inorder_node.mp hz with h | h | h
        · exact hgec z h
        · subst h; exact hvw
        · exact Nat.le_trans hvw (hge z h)

theorem BST_P3 {a b c' d : RBTree} {u v w : Nat}
    (hl : BST a) (hr : BST (.node .red (.node .red b u c') v d))
    (hlt : ∀ z ∈ inorder a, z ≤ w)
    (hge : ∀ z ∈ inorder (.node .red (.node .red b u c') v d), w ≤ z) :
    BST (.node .red (.node .black a w b) u (.node .black c' v d)) := by
  cases hr with
  | node hbl hbr hltl hgel =>
    cases hbl with
    | node hbb hbc hltb hgec =>
      have hwu : w ≤ u :=
        hge u (mem_inorder_node.mpr
          (Or.inl (mem_inorder_node.mpr (Or.inr (Or.inl rfl)))))
      have huv : u ≤ v :=
        hltl u (mem_inorder_node.mpr (Or.inr (Or.inl rfl)))
      refine BST.node (BST.node hl hbb hlt ?_)
        (BST.node hbc hbr ?_ hgel) ?_ ?_
      · intro z hz
        exact hge z (mem_inorder_node.mpr
          (Or.inl (mem_inorder_node.mpr (Or.inl hz))))
      · intro z hz
        exact hltl z (mem_inorder_node.mpr (Or.inr (Or.inr hz)))
      · intro z hz
        rcases mem_inorder_node.mp hz with h | h | h
        · exact Nat.le_trans (hlt z h) hwu
        · subst h; exact hwu
        · exact hltb z h
      · intro z hz
        rcases mem_inorder_node.mp hz with h | h | h
        · exact hgec z h
        · subst h; exact huv
        · exact Nat.le_trans huv (hgel z h)

theorem BST_P4 {a b c' d : RBTree} {u v w : Nat}
    (hl : BST a) (hr : BST (.node .red b u (.node .red c' v d)))
    (hlt : ∀ z ∈ inorder a, z ≤ w)
    (hge : ∀ z ∈ inorder (.node .red b u (.node .red c' v d)), w ≤ z) :
    BST (.node .red (.node .black a w b) u (.node .black c' v d)) := by
  cases hr with
  | node hbl hbr hltl hgel =>
    cases hbr with
    | node hbc hbd hltc hged =>
      have hwu : w ≤ u :=
        hge u (mem_inorder_node.mpr (Or.inr (Or.inl rfl)))
      have huv : u ≤ v :=
        hgel v (mem_inorder_node.mpr (Or.inr (Or.inl rfl)))
      refine BST.node (BST.node hl hbl hlt ?_)
        (BST.node hbc hbd hltc hged) ?_ ?_
      · intro z hz
        exact hge z (mem_inorder_node.mpr (Or.inl hz))
      · intro z hz
        rcases mem_inorder_node.mp hz with h | h | h
        · exact Nat.le_trans (hlt z h) hwu
        · subst h; exact hwu
        · exact hltl z h
      · intro z hz
        rcases mem_inorder_node.mp hz with h | h | h
        · exact hgel z (mem_inorder_node.mpr (Or.inl h))
        · subst h; exact huv
        · exact Nat.le_trans huv (hged z h)
theorem BST_balance {c : Colour} {l : RBTree} {x : Nat} {r : RBTree}
    (hl : BST l) (hr : BST r) (hlt : ∀ y ∈ inorder l, y ≤ x)
    (hge : ∀ y ∈ inorder r, x ≤ y) : BST (balance c l x r) := by
  cases c with
  | red =>
    cases l with
    | leaf => cases r <;> simp only [balance] <;> exact BST.node hl hr hlt hge
    | node c1 l1 y r1 => cases r <;> simp only [balance] <;> exact BST.node hl hr hlt hge
  | black =>
    cases l with
    | leaf =>
      cases r with
      | leaf => simp only [balance]; exact BST.node hl hr hlt hge
      | node c1 l2 x3 r4 =>
        cases c1 with
        | black => simp only [balance]; exact BST.node hl hr hlt hge
        | red =>
          cases l2 with
          | leaf =>
            cases r4 with
            | leaf => simp only [balance]; exact BST.node hl hr hlt hge
            | node c5 l6 x7 r8 =>
              cases c5 with
              | black => simp only [balance]; exact BST.node hl hr hlt hge
              | red => simp only [balance]; exact BST_P4 hl hr hlt hge
          | node c9 l10 x11 r12 =>
            cases c9 with
            | black =>
              cases r4 with
              | leaf => simp only [balance]; exact BST.node hl hr hlt hge
              | node c13 l14 x15 r16 =>
                cases c13 with
                | black => simp only [balance]; exact BST.node hl hr hlt hge
                | red => simp only [balance]; exact BST_P4 hl hr hlt hge
            | red => simp only [balance]; exact BST_P3 hl hr hlt hge
    | node c17 l18 x19 r20 =>
      cases c17 with
      | black =>
        cases r with
        | leaf => simp only [balance]; exact BST.node hl hr hlt hge
        | node c21 l22 x23 r24 =>
          cases c21 with
          | black => simp only [balance]; exact BST.node hl hr hlt hge
          | red =>
            cases l22 with
            | leaf =>
              cases r24 with
              | leaf => simp only [balance]; exact BST.node hl hr hlt hge
              | node c25 l26 x27 r28 =>
                cases c25 with
                | black => simp only [balance]; exact BST.node hl hr hlt hge
                | red => simp only [balance]; exact BST_P4 hl hr hlt hge
            | node c29 l30 x31 r32 =>
              cases c29 with
              | black =>
                cases r24 with
                | leaf => simp only [balance]; exact BST.node hl hr hlt hge
                | node c33 l34 x35 r36 =>
                  cases c33 with
                  | black => simp only [balance]; exact BST.node hl hr hlt hge
                  | red => simp only [balance]; exact BST_P4 hl hr hlt hge
              | red => simp only [balance]; exact BST_P3 hl hr hlt hge
      | red =>
        cases l18 with
        | leaf =>
          cases r20 with
          | leaf =>
            cases r with
            | leaf => simp only [balance]; exact BST.node hl hr hlt hge
            | node c37 l38 x39 r40 =>
              cases c37 with
              | black => simp only [balance]; exact BST.node hl hr hlt hge
              | red =>
                cases l38 with
                | leaf =>
                  cases r40 with
                  | leaf => simp only [balance]; exact BST.node hl hr hlt hge
                  | node c41 l42 x43 r44 =>
                    cases c41 with
                    | black => simp only [balance]; exact BST.node hl hr hlt hge
                    | red => simp only [balance]; exact BST_P4 hl hr hlt hge
                | node c45 l46 x47 r48 =>
                  cases c45 with
                  | black =>
                    cases r40 with
                    | leaf => simp only [balance]; exact BST.node hl hr hlt hge
                    | node c49 l50 x51 r52 =>
                      cases c49 with
                      | black => simp only [balance]; exact BST.node hl hr hlt hge
                      | red => simp only [balance]; exact BST_P4 hl hr hlt hge
                  | red => simp only [balance]; exact BST_P3 hl hr hlt hge
          | node c53 l54 x55 r56 =>
            cases c53 with
            | black =>
              cases r with
              | leaf => simp only [balance]; exact BST.node hl hr hlt hge
              | node c57 l58 x59 r60 =>
                cases c57 with
                | black => simp only [balance]; exact BST.node hl hr hlt hge
                | red =>
                  cases l58 with
                  | leaf =>
                    cases r60 with
                    | leaf => simp only [balance]; exact BST.node hl hr hlt hge
                    | node c61 l62 x63 r64 =>
                      cases c61 with
                      | black => simp only [balance]; exact BST.node hl hr hlt hge
                      | red => simp only [balance]; exact BST_P4 hl hr hlt hge
                  | node c65 l66 x67 r68 =>
                    cases c65 with
                    | black =>
                      cases r60 with
                      | leaf => simp only [balance]; exact BST.node hl hr hlt hge
                      | node c69 l70 x71 r72 =>
                        cases c69 with
                        | black => simp only [balance]; exact BST.node hl hr hlt hge
                        | red => simp only [balance]; exact BST_P4 hl hr hlt hge
                    | red => simp only [balance]; exact BST_P3 hl hr hlt hge
            | red => simp only [balance]; exact BST_P2 hl hr hlt hge
        | node c73 l74 x75 r76 =>
          cases c73 with
          | black =>
            cases r20 with
            | leaf =>
              cases r with
              | leaf => simp only [balance]; exact BST.node hl hr hlt hge
              | node c77 l78 x79 r80 =>
                cases c77 with
                | black => simp only [balance]; exact BST.node hl hr hlt hge
                | red =>
                  cases l78 with
                  | leaf =>
                    cases r80 with
                    | leaf => simp only [balance]; exact BST.node hl hr hlt hge
                    | node c81 l82 x83 r84 =>
                      cases c81 with
                      | black => simp only [balance]; exact BST.node hl hr hlt hge
                      | red => simp only [balance]; exact BST_P4 hl hr hlt hge
                  | node c85 l86 x87 r88 =>
                    cases c85 with
                    | black =>
                      cases r80 with
                      | leaf => simp only [balance]; exact BST.node hl hr hlt hge
                      | node c89 l90 x91 r92 =>
                        cases c89 with
                        | black => simp only [balance]; exact BST.node hl hr hlt hge
                        | red => simp only [balance]; exact BST_P4 hl hr hlt hge
                    | red => simp only [balance]; exact BST_P3 hl hr hlt hge
            | node c93 l94 x95 r96 =>
              cases c93 with
              | black =>
                cases r with
                | leaf => simp only [balance]; exact BST.node hl hr hlt hge
                | node c97 l98 x99 r100 =>
                  cases c97 with
                  | black => simp only [balance]; exact BST.node hl hr hlt hge
                  | red =>
                    cases l98 with
                    | leaf =>
                      cases r100 with
                      | leaf => simp only [balance]; exact BST.node hl hr hlt hge
                      | node c101 l102 x103 r104 =>
                        cases c101 with
                        | black => simp only [balance]; exact BST.node hl hr hlt hge
                        | red => simp only [balance]; exact BST_P4 hl hr hlt hge
                    | node c105 l106 x107 r108 =>
                      cases c105 with
                      | black =>
                        cases r100 with
                        | leaf => simp only [balance]; exact BST.node hl hr hlt hge
                        | node c109 l110 x111 r112 =>
                          cases c109 with
                          | black => simp only [balance]; exact BST.node hl hr hlt hge
                          | red => simp only [balance]; exact BST_P4 hl hr hlt hge
                      | red => simp only [balance]; exact BST_P3 hl hr hlt hge
              | red => simp only [balance]; exact BST_P2 hl hr hlt hge
          | red => simp only [balance]; exact BST_P1 hl hr hlt hge

theorem BST_ins (x : Nat) {t : RBTree} (h : BST t) : BST (ins x t) := by
  induction t with
  | leaf =>
    refine BST.node BST.leaf BST.leaf ?_ ?_ <;>
      · intro z hz
        simp [inorder] at hz
  | node c l y r ihl ihr =>
    cases h with
    | node hl hr hlt hge =>
      by_cases hlt2 : x < y
      · simp only [ins, if_pos hlt2]
        refine BST_balance (ihl hl) hr ?_ hge
        intro z hz
        have hz2 : z ∈ x :: inorder l := (inorder_ins x l).mem_iff.mp hz
        rcases List.mem_cons.mp hz2 with rfl | hz3
        · exact Nat.le_of_lt hlt2
        · exact hlt z hz3
      · simp only [ins, if_neg hlt2]
        refine BST_balance hl (ihr hr) hlt ?_
        intro z hz
        have hz2 : z ∈ x :: inorder r := (inorder_ins x r).mem_iff.mp hz
        rcases List.mem_cons.mp hz2 with rfl | hz3
        · exact by omega
        · exact hge z hz3

theorem blacken_BST {t : RBTree} (h : BST t) : BST (blacken t) := by
  cases t with
  | leaf => exact h
  | node c l y r =>
    cases h with
    | node hl hr h1 h2 => exact BST.node hl hr h1 h2

theorem BST_rbInsert (x : Nat) {t : RBTree} (h : BST t) : BST (rbInsert x t) :=
  blacken_BST (BST_ins x h)

/-- BST-guided search. -/
def search (x : Nat) : RBTree → Bool
  | .leaf => false
  | .node _ l y r =>
      if x < y then search x l else if y < x then search x r else true

theorem search_eq_true_iff {t : RBTree} (h : BST t) :
    search x t = true ↔ x ∈ inorder t := by
  induction t with
  | leaf => simp [search, inorder]
  | node c l y r ihl ihr =>
    cases h with
    | node hl hr hlt hge =>
      by_cases h1 : x < y
      · simp only [search, if_pos h1]
        rw [ihl hl]
        constructor
        · intro hx
          exact mem_inorder_node.mpr (Or.inl hx)
        · intro hx
          rcases mem_inorder_node.mp hx with h | h | h
          · exact h
          · subst h; exact absurd h1 (Nat.lt_irrefl _)
          · exact absurd (Nat.lt_of_le_of_lt (hge _ h) h1) (Nat.lt_irrefl _)
      · by_cases h2 : y < x
        · simp only [search, if_neg h1, if_pos h2]
          rw [ihr hr]
          constructor
          · intro hx
            exact mem_inorder_node.mpr (Or.inr (Or.inr hx))
          · intro hx
            rcases mem_inorder_node.mp hx with h | h | h
            · exact absurd (Nat.lt_of_le_of_lt (hlt _ h) h2) (Nat.lt_irrefl _)
            · subst h; exact absurd h2 (Nat.lt_irrefl _)
            · exact h
        · have hxy : x = y := by omega
          simp only [search, if_neg h1, if_neg h2]
          constructor
          · intro _
            exact mem_inorder_node.mpr (Or.inr (Or.inl hxy))
          · intro _
            simp [search, h1, h2]

theorem BST_pairwise {t : RBTree} (h : BST t) :
    List.Pairwise (· ≤ ·) (inorder t) := by
  induction h with
  | leaf => exact List.Pairwise.nil
  | node hl hr hlt hge ihl ihr =>
    rw [inorder, List.pairwise_append]
    refine ⟨ihl, ?_, ?_⟩
    · exact List.Pairwise.cons (fun z hz => hge z hz) ihr
    · intro z hz w hw
      rcases List.mem_cons.mp hw with rfl | hw2
      · exact hlt z hz
      · exact Nat.le_trans (hlt z hz) (hge w hw2)

/-- The headline: insertion into a red-black tree adds exactly the
inserted key to the inorder contents and preserves the black-height
invariant, the no-red-red invariant, and the BST ordering. -/
theorem rbtree_insertion_correctness (x : Nat) {t : RBTree} {n : Nat}
    (hbh : BHOk t n) (hnr : NoRR t) (hbst : BST t) :
    List.Perm (inorder (rbInsert x t)) (x :: inorder t) ∧
      (∃ m, BHOk (rbInsert x t) m) ∧ NoRR (rbInsert x t) ∧
      BST (rbInsert x t) :=
  ⟨inorder_rbInsert x t, BHOk_rbInsert x hbh, rbInsert_NoRR x hnr,
    BST_rbInsert x hbst⟩

/-- After insertion, the inserted key is found by search. -/
theorem search_rbInsert_self (x : Nat) {t : RBTree} (h : BST t) :
    search x (rbInsert x t) = true :=
  (search_eq_true_iff (BST_rbInsert x h)).mpr
    ((inorder_rbInsert x t).mem_iff.mpr (by simp))

end AxiomCode
