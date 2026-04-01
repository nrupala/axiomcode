import Lake
open Lake DSL

package axiomcode where
  srcDir := "src"

lean_lib AxiomCode where
  roots := #[`Spec, `Tactics, `Algorithms]

require mathlib from git
  "https://github.com/leanprover-community/mathlib4.git"
