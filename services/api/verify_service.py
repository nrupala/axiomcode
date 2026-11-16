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

import billing
from limits import ConcurrencyGate
from proof_runner import (  # noqa: F401  (extracted, Slice 4 S3; re-exported for callers)
    _LAKEFILE,
    ProofTimeoutError,
    run_proof,
)

TRIAL_CASES = int(os.environ.get("AXIOMCODE_TRIAL_CASES", "10"))
PROOF_TIMEOUT_S = float(os.environ.get("AXIOMCODE_PROOF_TIMEOUT_S", "600"))


class PaymentRequiredError(Exception):
    """Trial exhausted and no credit balance — refuse before proving."""

    def __init__(self, key_hash: str, trial_cases: int):
        super().__init__("payment required: trial cases exhausted and no credit balance")
        self.key_hash = key_hash
        self.trial_cases = trial_cases


class TooManyConcurrentError(Exception):
    """The key already has its maximum proofs in flight."""


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
        prior = store.find_prior_cert(key_hash, code_sha, exclude_serial=cert["serial"])
        store.record_cert(cert, renews=prior)
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
