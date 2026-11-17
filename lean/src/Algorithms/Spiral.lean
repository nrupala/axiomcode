import Spec
import Tactics

/-!
# AxiomCode — Verified Spiral Matrix

Promoted from `lean/drafts/algorithm_correctness (m.lean` under the
L2 promotion procedure (`lean/PROMOTION.md`). The draft's shells are
authored for real: `SpiralMatrix` gains the fields its statement
references (`rows`, `cols`, `matrix`), `spiralOrder` is the genuine
ring-by-ring spiral traversal (coordinates generated ring by ring —
top row, right column, bottom row, left column — then the inner
submatrix offset by `(1, 1)`), and `isSpiralMatrix` decides whether
the spiral traversal of the matrix is exactly `0, 1, …, rows*cols-1`.

Statement honesty: **the draft's iff is FALSE as stated**, under the
reading its own doc comment gives ("all elements are visited in a
spiral order"). Its right-hand side uses `List.flatten` — row-major
order — but spiral order is not row-major order. Counterexample:
`m = ⟨2, 2, [[0, 1], [3, 2]]⟩`. The spiral traversal of `m` is
`[0, 1, 2, 3] = List.range 4`, so the left-hand side holds under the
doc's meaning; but `List.flatten m.matrix = [0, 1, 3, 2] ≠
List.range 4`, so the right-hand side fails. (The two orders also
differ in the other direction: `[[0, 1], [2, 3]]` flattens to the
range but its spiral traversal is `[0, 1, 3, 2]`.) The theorem is
carried in the draft's exact iff shape with the right-hand side
repaired to the spiral traversal the doc comment describes; both
counterexamples are proved below as `spiral_example_two_by_two`
(the repaired predicate holds) and
`spiral_counterexample_row_major` (row-major order does not imply
it). With `isSpiralMatrix` authored as the decision procedure for
the repaired claim, the iff itself is the unfolding of that
definition — the substantive content is the traversal.
-/

namespace AxiomCode

/-- A matrix presented with its dimensions. -/
structure SpiralMatrix where
  rows : Nat
  cols : Nat
  matrix : List (List Nat)
deriving DecidableEq, Repr

/-- Spiral coordinates of a `rows × cols` grid, ring by ring, with
`fuel` bounding the number of rings. In the ring case the grid is
`(rows + 1) × (cols + 1)`: the top row, the right column below the
corner, the bottom row right-to-left (when there is a row below the
top), the left column bottom-to-top (when there is a column right
of the left), then the inner subgrid's coordinates offset by
`(1, 1)`. -/
def spiralCoordsAux : Nat → Nat → Nat → List (Nat × Nat)
  | 0, _, _ => []
  | _, 0, _ => []
  | _, _ + 1, 0 => []
  | fuel + 1, rows + 1, cols + 1 =>
    (List.range (cols + 1)).map (fun j => (0, j))
    ++ (List.range rows).map (fun i => (i + 1, cols))
    ++ (if 1 ≤ rows then
          (List.range cols).map (fun j => (rows, cols - 1 - j))
        else [])
    ++ (if 1 ≤ cols then
          (List.range (rows - 1)).map (fun i => (rows - 1 - i, 0))
        else [])
    ++ (spiralCoordsAux fuel (rows - 1) (cols - 1)).map
        (fun p => (p.1 + 1, p.2 + 1))

/-- Spiral coordinates of a `rows × cols` grid (`rows` rings of
fuel always suffice: each ring strips two rows). -/
def spiralCoords (rows cols : Nat) : List (Nat × Nat) :=
  spiralCoordsAux rows rows cols

/-- The number of columns of a matrix: the longest row. -/
def numCols (matrix : List (List Nat)) : Nat :=
  (matrix.map List.length).foldl max 0

/-- The elements of the matrix in spiral order. -/
def spiralOrder (matrix : List (List Nat)) : List Nat :=
  (spiralCoords matrix.length (numCols matrix)).map
    (fun p => matrix[p.1]![p.2]!)

/-- Whether the matrix's spiral traversal is exactly
`0, 1, …, rows * cols - 1`. -/
def isSpiralMatrix (m : SpiralMatrix) : Bool :=
  decide (spiralOrder m.matrix = List.range (m.rows * m.cols))

/-- The draft's theorem with its right-hand side repaired from
row-major (`List.flatten`) to the spiral traversal its doc comment
describes (see the module doc for the counterexample to the draft's
form): `isSpiralMatrix` holds exactly when the spiral traversal is
the range. -/
theorem SpiralMatrix.algorithm_correctness (m : SpiralMatrix) :
    isSpiralMatrix m ↔
      spiralOrder m.matrix = List.range (m.rows * m.cols) := by
  simp only [isSpiralMatrix, decide_eq_true_eq]

/-- The counterexample matrix of the module doc satisfies the
repaired predicate: its spiral traversal is `[0, 1, 2, 3]`. -/
theorem spiral_example_two_by_two :
    isSpiralMatrix ⟨2, 2, [[0, 1], [3, 2]]⟩ = true := by
  decide

/-- Row-major order does not imply the spiral property:
`[[0, 1], [2, 3]]` flattens to the range, but its spiral traversal
is `[0, 1, 3, 2]`. -/
theorem spiral_counterexample_row_major :
    isSpiralMatrix ⟨2, 2, [[0, 1], [2, 3]]⟩ = false := by
  decide

/-- A `3 × 3` spiral: the traversal is `[0, 1, …, 8]`. -/
theorem spiral_example_three_by_three :
    isSpiralMatrix ⟨3, 3, [[0, 1, 2], [7, 8, 3], [6, 5, 4]]⟩ = true := by
  decide

end AxiomCode
