import Mathlib
import Aesop
import Mathlib.Graph



/-- implement Bellman-Ford algorithm for shortest paths that handles negative edge weights, prove it detects negative cycles and computes correct distances otherwise -/
theorem bellman_ford_correct (g : Graph) : True := by sorry