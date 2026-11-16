import Lake
open Lake DSL

package axiomcode where
  srcDir := "src"

lean_lib AxiomCode where
  -- L2 (2026-11-16): `Algorithms` is back in roots as the promotion target —
  -- only machine-checked, sorry-free promoted modules live under
  -- src/Algorithms/ (promotion procedure: PROMOTION.md). The remaining
  -- unverified drafts stay quarantined in lean/drafts/, outside the build.
  roots := #[`Spec, `Tactics, `Algorithms]

-- Tracks Mathlib master; `lake update` resolves the matching Lean toolchain
-- into lean-toolchain (currently v4.35.0-rc3, as required by Mathlib master).
require mathlib from git
  "https://github.com/leanprover-community/mathlib4.git"
