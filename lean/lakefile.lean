import Lake
open Lake DSL

package axiomcode where
  srcDir := "src"

lean_lib AxiomCode where
  -- NOTE: `Algorithms` was dropped from roots. The 59 sorry-laden algorithm
  -- files were quarantined to lean/drafts/ (unverified); only machine-checked
  -- modules (Spec, Tactics) belong in the verified library under lean/src/.
  roots := #[`Spec, `Tactics]

-- Tracks Mathlib master; `lake update` resolves the matching Lean toolchain
-- into lean-toolchain (currently v4.35.0-rc3, as required by Mathlib master).
require mathlib from git
  "https://github.com/leanprover-community/mathlib4.git"
