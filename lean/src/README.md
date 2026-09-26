# Verified library

This directory holds **only machine-checked Lean 4 proofs**: every file here
built cleanly under `lake build` with zero `sorry`/`admit`, as recorded by the
proof certificate's `verification_status: verified`.

Unfinished work lives in `../drafts/`. CI fails the build if any
`sorry`/`admit` appears under this directory.
