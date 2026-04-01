/-!
# AxiomCode — Custom Proof Tactics

Domain-specific tactics for accelerating proof search on common algorithm patterns.
-/

import Mathlib.Tactic

namespace AxiomCode

/-- Tactic for proving sorted list properties by induction. -/
macro "sort_induction" : tactic =>
  `(tactic|
    (try induction' l with a l ih
     · simp [Sorted]
     · simp [Sorted] at *
       aesop))

/-- Tactic for proving permutation properties. -/
macro "perm_tactic" : tactic =>
  `(tactic|
    (try apply List.Perm.trans _ _
     · aesop))

/-- Tactic for proving bounds on list indices. -/
macro "bound_index" : tactic =>
  `(tactic|
    (try omega))

/-- Combined tactic for sorting algorithm correctness proofs. -/
macro "prove_sort" : tactic =>
  `(tactic|
    (constructor
     · sort_induction
     · perm_tactic))

end AxiomCode
