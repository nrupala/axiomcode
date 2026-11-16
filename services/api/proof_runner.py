"""AxiomCode proof runner — the shared kernel-leg procedure.

EXTRACTED from services/api/verify_service.py (Slice 4, step S3) so
the hosted service and the offline checker call ONE implementation of
the verdict procedure: scaffold a fresh temp Lake project, elaborate
under the pinned toolchain with a wall-clock deadline, clean up on
every path. `verify_service` imports `run_proof`, `_LAKEFILE`, and
`ProofTimeoutError` back from this module (re-exported; its callers
see no change) — the extraction is a move, not a change.

This module is deliberately free of service context: no store, no
billing, no limits, no env config. The search function (the prover)
is passed in by the caller, exactly as the hosted service passes
`core.prover.iterative_proof_search`.
"""

import shutil
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeout
from pathlib import Path

_LAKEFILE = "import Lake\nopen Lake DSL\npackage v where\nlean_lib V where\n  roots := #[`V]\n"


class ProofTimeoutError(Exception):
    """The proof exceeded its wall-clock budget."""


def run_proof(code, max_attempts, *, work_root, prefix, toolchain, timeout_s, search):
    """Run the Lean prover in a fresh temp project with a deadline.

    Returns (verified, attempts, compute_s). Raises ProofTimeoutError.
    The project dir is always removed, timeout path included."""
    proj = Path(tempfile.mkdtemp(prefix=prefix, dir=work_root))
    try:
        (proj / "lean-toolchain").write_text(toolchain, encoding="utf-8")
        (proj / "lakefile.lean").write_text(_LAKEFILE, encoding="utf-8")
        src = proj / "V.lean"

        def writer(c: str) -> Path:
            src.write_text(c, encoding="utf-8")
            return Path(src)

        executor = ThreadPoolExecutor(max_workers=1)
        try:
            t0 = time.time()
            future = executor.submit(
                search,
                writer,
                proj,
                code,
                None,
                "none",
                max_attempts=max_attempts,
                use_pantograph=False,
            )
            try:
                verified, _final_code, attempts, _log = future.result(timeout=timeout_s)
            except FutureTimeout:
                raise ProofTimeoutError(f"proof exceeded {timeout_s:g}s") from None
            return verified, attempts, time.time() - t0
        finally:
            # Never wait for an orphaned prover thread on the timeout
            # path; it dies against the removed project dir.
            executor.shutdown(wait=False)
    finally:
        shutil.rmtree(proj, ignore_errors=True)
