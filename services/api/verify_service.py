"""AxiomCode verification service (W3 + W5) — the one verify flow
both servers (REST verify_api, MCP mcp_server) run, so trial rules,
metering and isolation cannot drift between interfaces.

execute_verification():
  1. Look at the key's balance (store.balance_for) and trial cases
     used (store.trial_cases_used).
  2. Balance > 0            -> paid case: run proof, meter the call,
                               issue + record the certificate.
     Trial cases left       -> trial case: run proof, record a free
                               zero-credit trial meter event, return
                               verdict + attempts with certificate
                               None and a trial summary. NO cert is
                               recorded.
     Neither                -> PaymentRequiredError, raised BEFORE the
                               proof runs (no free compute).
  3. The proof itself runs under the per-key ConcurrencyGate and a
     wall-clock timeout (run_proof).

Caller identity is the API key's SHA-256 hash everywhere (metering,
certificate key_id, limits) — never a caller-supplied string.

W5 isolation: every proof gets a fresh temp project under
AXIOMCODE_WORK_ROOT, removed in a finally block (including on the
timeout path). The timeout is a client-facing deadline enforced with
a worker thread: Python threads cannot be killed, so on timeout the
response goes out and the orphaned prover thread finishes in the
background against a project dir that is already being removed —
its writes start failing and it exits. No state outside the store
(lock-guarded) is shared between concurrent jobs.
"""

import hashlib
import os
import shutil
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeout
from pathlib import Path

import billing
from limits import ConcurrencyGate

TRIAL_CASES = int(os.environ.get("AXIOMCODE_TRIAL_CASES", "10"))
PROOF_TIMEOUT_S = float(os.environ.get("AXIOMCODE_PROOF_TIMEOUT_S", "600"))

_LAKEFILE = "import Lake\nopen Lake DSL\npackage v where\nlean_lib V where\n  roots := #[`V]\n"


class PaymentRequiredError(Exception):
    """Trial exhausted and no credit balance — refuse before proving."""

    def __init__(self, key_hash: str, trial_cases: int):
        super().__init__("payment required: trial cases exhausted and no credit balance")
        self.key_hash = key_hash
        self.trial_cases = trial_cases


class ProofTimeoutError(Exception):
    """The proof exceeded its wall-clock budget."""


class TooManyConcurrentError(Exception):
    """The key already has its maximum proofs in flight."""


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


def execute_verification(
    *,
    store,
    authority,
    key_hash,
    code,
    max_attempts,
    work_root,
    prefix,
    toolchain,
    search,
    extra_subject=None,
    gate: ConcurrencyGate | None = None,
    timeout_s: float = PROOF_TIMEOUT_S,
    trial_cases: int = TRIAL_CASES,
) -> dict:
    """Run one verification case for an authenticated key.

    Returns the response dict (REST shape):
      paid:  {verified, attempts, certificate, usage}
      trial: {verified, attempts, certificate: None, usage, trial:
              {cases_used, cases_left,
               certificates: "unlock with a credit pack"}}
    Raises PaymentRequiredError (before proving), ProofTimeoutError,
    TooManyConcurrentError."""
    balance = store.balance_for(key_hash)
    used = store.trial_cases_used(key_hash)
    paid = balance > 0
    if not paid and used >= trial_cases:
        raise PaymentRequiredError(key_hash, trial_cases)

    if gate is not None and not gate.acquire(key_hash):
        raise TooManyConcurrentError(key_hash)
    try:
        verified, attempts, compute_s = run_proof(
            code,
            max_attempts,
            work_root=work_root,
            prefix=prefix,
            toolchain=toolchain,
            timeout_s=timeout_s,
            search=search,
        )
    finally:
        if gate is not None:
            gate.release(key_hash)

    code_sha = hashlib.sha256(code.encode()).hexdigest()
    if paid:
        usage = billing.meter(store, key_hash, code_sha, verified, compute_s)
        subject = {
            "code_sha256": code_sha,
            "verified": verified,
            "attempts": attempts,
            "toolchain": toolchain,
            "key_id": key_hash,
        }
        if extra_subject:
            resolved = extra_subject() if callable(extra_subject) else extra_subject
            subject.update(resolved)
        cert = authority.issue(subject)
        store.record_cert(cert)
        return {"verified": verified, "attempts": attempts, "certificate": cert, "usage": usage}

    usage = billing.meter(store, key_hash, code_sha, verified, compute_s, trial=True)
    used += 1
    return {
        "verified": verified,
        "attempts": attempts,
        "certificate": None,
        "usage": usage,
        "trial": {
            "cases_used": used,
            "cases_left": max(trial_cases - used, 0),
            "certificates": "unlock with a credit pack",
        },
    }
