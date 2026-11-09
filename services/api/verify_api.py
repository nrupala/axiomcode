"""AxiomCode verification API (production build).

POST /verify {code} -> {verified, attempts, certificate, usage}
     — or, when every proof slot is busy, 202 {status: queued,
     job_id, position}: the request joins the durable FIFO queue
     (jobqueue.py, F-AX-5) and is verified in order.
GET  /verify/jobs/{job_id} -> queue position or the finished result
     (the submitting key only; any other key gets a 404)
POST /check  {certificate} -> {valid, ...}
GET  /revoked -> {issuer, revoked: [serial...]}   (public CRL)
GET  /.well-known/axiomcode-keys.json -> published CA public keys
GET  /health -> {status: ok}
POST /billing/webhook -> Stripe webhook (credits granted here)

Access (W3): /verify and /check require an API key (X-Api-Key header
or Authorization: Bearer). Identity comes ONLY from the credential —
the key's SHA-256 hash is the caller identity for metering, trial
counting and limits; request bodies carry no identity at all. A new
key's first 10 verification cases are a free trial: verdict +
transcript, NO certificate. Certificates unlock once the key holds
paid credits (packs via Stripe, W4). Per-key rate limit + proof
concurrency cap apply (limits.py); submission size and proof
wall-clock are capped (W5).

Certificates are Ed25519-signed attestations (ca.py, format v2)
binding: code hash + verified verdict + toolchain version + validity
window. Anyone holding the cert and the published public key can
confirm *what* was checked and *what* the machine said — without
trusting the server's word for it. All state (certificates,
revocations, meter, grants, audit) lives in the durable store
(store.py); issuance / revocation / verification events land in its
hash-chained audit log.
"""

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import ca
import jobqueue
import limits
import stripe_billing
import verify_service
from core.prover import iterative_proof_search, lean_version
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from store import Store

TOOLCHAIN = "leanprover/lean4:v4.35.0-rc3"
WORK_ROOT = os.environ.get("AXIOMCODE_WORK_ROOT", tempfile.gettempdir())
MAX_CODE_BYTES = int(os.environ.get("AXIOMCODE_MAX_CODE_BYTES", "262144"))
TRIAL_CASES = verify_service.TRIAL_CASES
PROOF_TIMEOUT_S = verify_service.PROOF_TIMEOUT_S

CA = ca.CA.load_or_create()
STORE = Store()
LIMITER = limits.RateLimiter()
GATE = limits.ConcurrencyGate()  # legacy per-key gate; admission is owned by QUEUE below

app = FastAPI(
    title="AxiomCode Verify",
    description="Verification-as-evidence: every verdict ships a signed certificate "
    "anyone can re-check without trusting us. Don't trust our AI — verify our proof.",
)


def _payment_required_body() -> dict:
    return {
        "error": "payment_required",
        "detail": "trial cases exhausted and no credit balance; certificates unlock with a credit pack",
        "trial": {"cases_used": TRIAL_CASES, "cases_left": 0, "certificates": "unlock with a credit pack"},
    }


def _run_once(key_hash: str, code: str, max_attempts: int) -> tuple[dict, int]:
    """Run one verification now (the caller owns admission) and map
    the service's refusals to their public bodies. Eligibility is
    re-checked inside execute_verification, so a queued job whose
    trial ran out while it waited still refuses before proving."""
    try:
        return (
            verify_service.execute_verification(
                store=STORE,
                authority=CA,
                key_hash=key_hash,
                code=code,
                max_attempts=max_attempts,
                work_root=WORK_ROOT,
                prefix="ax-api-",
                toolchain=TOOLCHAIN,
                search=iterative_proof_search,
                extra_subject=lambda: {"lean_version": lean_version()},
                gate=None,
                timeout_s=PROOF_TIMEOUT_S,
                trial_cases=TRIAL_CASES,
            ),
            200,
        )
    except verify_service.PaymentRequiredError:
        return _payment_required_body(), 402
    except verify_service.ProofTimeoutError:
        return {"error": "proof_timeout", "timeout_s": PROOF_TIMEOUT_S}, 504


def _run_queued_job(job: dict) -> dict:
    body, _status = _run_once(job["key_hash"], job["code"], job["max_attempts"])
    return body


JOBS = jobqueue.JobStore()
QUEUE = jobqueue.ProofQueue(JOBS, _run_queued_job)


@app.on_event("startup")
def _start_queue() -> None:
    QUEUE.start()


class VerifyRequest(BaseModel):
    code: str
    max_attempts: int = 1


class CheckRequest(BaseModel):
    certificate: dict


class CheckoutRequest(BaseModel):
    pack: str
    success_url: str | None = None
    cancel_url: str | None = None


def require_api_key(request: Request) -> str:
    """Authenticate the caller; return the key's hash (its identity).
    Missing, unknown or revoked keys get a 401."""
    presented = request.headers.get("x-api-key", "")
    if not presented:
        auth = request.headers.get("authorization", "")
        presented = auth[7:] if auth.lower().startswith("bearer ") else ""
    row = STORE.authenticate_api_key(presented) if presented else None
    if row is None:
        raise HTTPException(status_code=401, detail="invalid or missing API key")
    return str(row["key_hash"])


def _rate_limited(key_hash: str) -> JSONResponse | None:
    if LIMITER.allow(key_hash):
        return None
    return JSONResponse(
        status_code=429,
        content={"error": "rate_limited", "detail": f"over {LIMITER.limit} requests per minute for this key"},
    )


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/verify")
def verify(req: VerifyRequest, key_hash: str = Depends(require_api_key)):
    if len(req.code.encode()) > MAX_CODE_BYTES:
        return JSONResponse(
            status_code=413,
            content={"error": "code_too_large", "max_bytes": MAX_CODE_BYTES},
        )
    limited = _rate_limited(key_hash)
    if limited is not None:
        return limited
    # Eligibility is decided BEFORE admission: a key that cannot pay
    # gets its 402 here and never occupies a proof slot or a place in
    # line (no free compute, no queue squatting).
    if STORE.balance_for(key_hash) <= 0 and STORE.trial_cases_used(key_hash) >= TRIAL_CASES:
        return JSONResponse(status_code=402, content=_payment_required_body())
    # Fast path: a slot is free and nobody is waiting — run now, the
    # response shape is unchanged from the pre-queue service.
    if QUEUE.acquire_immediate(key_hash):
        try:
            body, status = _run_once(key_hash, req.code, req.max_attempts)
        finally:
            QUEUE.release(key_hash)
        return JSONResponse(status_code=status, content=body) if status != 200 else body
    # Busy: the request joins the durable FIFO queue (F-AX-5). The
    # caller gets a job id and a checkable position — never a silent
    # wait. Eligibility is re-checked when the job runs.
    job_id, position = QUEUE.enqueue(key_hash, req.code, req.max_attempts)
    STORE.append_audit("job_queued", {"job_id": job_id, "key_hash": key_hash, "position": position})
    return JSONResponse(
        status_code=202,
        content={
            "status": "queued",
            "job_id": job_id,
            "position": position,
            "note": jobqueue.QUEUE_NOTE,
        },
    )


@app.get("/verify/jobs/{job_id}")
def verify_job(job_id: str, key_hash: str = Depends(require_api_key)):
    """Queue position / result for a job. Only the submitting key can
    read its job — any other key (or an unknown id) gets a 404, so a
    job's existence never leaks across customers."""
    job = JOBS.get_job(job_id)
    if job is None or job["key_hash"] != key_hash:
        raise HTTPException(status_code=404, detail="no such job")
    if job["status"] == "queued":
        return {"status": "queued", "job_id": job_id, "position": JOBS.job_position(job_id)}
    if job["status"] == "running":
        return {"status": "running", "job_id": job_id}
    if job["status"] == "done":
        return {"status": "done", "job_id": job_id, "result": job["result"]}
    return {"status": "failed", "job_id": job_id, "error": job["error"]}


@app.post("/check")
def check(req: CheckRequest, key_hash: str = Depends(require_api_key)):
    # A read of an existing certificate: authenticated + rate limited,
    # but consumes no trial case and no credits.
    limited = _rate_limited(key_hash)
    if limited is not None:
        return limited
    result = ca.verify_certificate(req.certificate, ca=CA)
    serial = req.certificate.get("serial") if isinstance(req.certificate, dict) else None
    if result.get("valid") and serial and STORE.is_revoked(serial):
        result = {"valid": False, "reason": "revoked", "payload": req.certificate}
    STORE.append_audit(
        "verification",
        {
            "serial": serial,
            "valid": bool(result.get("valid")),
            "reason": result.get("reason"),
            "via": "rest",
        },
    )
    return result


@app.get("/revoked")
def revoked():
    return {"issuer": ca.ISSUER, "revoked": sorted(STORE.revoked_serials())}


@app.get("/.well-known/axiomcode-keys.json")
def ca_public_keys():
    return CA.public_keys_payload()


def _plain_event_data(obj):
    """Recursively convert a Stripe event object to plain data.

    stripe-python >= 12 returns attribute-access objects (stripe.Event
    is not a dict and not JSON-serializable), so the verified event must
    be converted before handle_webhook consumes it. (F0 staging,
    2026-10-20: json.dumps(event) raised TypeError on every real event,
    so the route answered 400 to all genuine Stripe deliveries.)"""
    if isinstance(obj, dict):
        return {k: _plain_event_data(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_plain_event_data(v) for v in obj]
    if hasattr(obj, "to_dict"):
        return _plain_event_data(obj.to_dict())
    return obj


@app.post("/billing/checkout")
def billing_checkout(req: CheckoutRequest, key_hash: str = Depends(require_api_key)):
    """Create a Stripe Checkout Session for a credit pack, bound to
    the caller's key (the webhook grants on client_reference_id).
    Like the webhook route, this answers 501 rather than pretending
    when Stripe is not configured on this host."""
    try:
        import stripe  # noqa: F401 — availability probe, same as the webhook route
    except ImportError:
        return JSONResponse(status_code=501, content={"error": "stripe_not_configured"})
    if not os.environ.get("STRIPE_SECRET_KEY"):
        return JSONResponse(status_code=501, content={"error": "stripe_not_configured"})
    try:
        session = stripe_billing.create_checkout_session(
            req.pack,
            key_hash,
            success_url=req.success_url or stripe_billing.DEFAULT_SUCCESS_URL,
            cancel_url=req.cancel_url or stripe_billing.DEFAULT_CANCEL_URL,
        )
    except ValueError as e:  # unknown pack or unconfigured price
        return JSONResponse(status_code=400, content={"error": str(e)})
    return {"checkout_url": session.get("url"), "session_id": session.get("id"), "pack": req.pack}


@app.post("/billing/webhook")
async def billing_webhook(request: Request):
    """Stripe webhook: grants pack credits on checkout completion
    and reverses them on refund (stripe_billing.handle_webhook,
    idempotent on Stripe ids). Needs the stripe package and
    STRIPE_WEBHOOK_SECRET in the deploy environment; without them
    the route answers 501 rather than accepting unverifiable events."""
    payload = await request.body()
    signature = request.headers.get("stripe-signature", "")
    secret = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
    try:
        import stripe
    except ImportError:
        print("billing_webhook: stripe package not installed — webhook disabled", flush=True)
        return JSONResponse(status_code=501, content={"error": "stripe_not_configured"})
    if not secret:
        print("billing_webhook: STRIPE_WEBHOOK_SECRET not set — webhook disabled", flush=True)
        return JSONResponse(status_code=501, content={"error": "stripe_not_configured"})

    def verify_signature(raw: bytes, sig: str) -> dict:
        event = stripe.Webhook.construct_event(raw, sig, secret)
        parsed: dict = _plain_event_data(event)
        return parsed

    try:
        return stripe_billing.handle_webhook(STORE, payload, signature, verify_signature)
    except Exception:  # bad signature or malformed event — not from Stripe as-is
        return JSONResponse(status_code=400, content={"error": "invalid_signature_or_payload"})
