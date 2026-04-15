import Mathlib
import Aesop
import Mathlib.Graph



/-- implement topological sort using Kahn's algorithm, prove the output ordering respects all edges (if u→v then u appears before v) -/
theorem topological_sort_correct (g : Graph) : True := by sorry