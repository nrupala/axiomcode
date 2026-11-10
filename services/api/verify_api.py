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
from contextlib import asynccontextmanager

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import billing
import ca
import jobqueue
import limits
import stripe_billing
import verify_service
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from store import Store

from core.prover import iterative_proof_search, lean_version

TOOLCHAIN = "leanprover/lean4:v4.35.0-rc3"
WORK_ROOT = os.environ.get("AXIOMCODE_WORK_ROOT", tempfile.gettempdir())
MAX_CODE_BYTES = int(os.environ.get("AXIOMCODE_MAX_CODE_BYTES", "262144"))
TRIAL_CASES = verify_service.TRIAL_CASES
PROOF_TIMEOUT_S = verify_service.PROOF_TIMEOUT_S

CA = ca.CA.load_or_create()
STORE = Store()
LIMITER = limits.RateLimiter()
GATE = limits.ConcurrencyGate()  # legacy per-key gate; admission is owned by QUEUE below


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


def authenticate_key(presented: str) -> str | None:
    """Resolve a presented API key to its identity — the key's
    SHA-256 hash — or None when the key is missing, unknown or
    revoked. The one identity rule for every interface: the REST
    dependency and the hosted-MCP middleware both resolve through
    here, so no leg can authenticate differently."""
    row = STORE.authenticate_api_key(presented) if presented else None
    return str(row["key_hash"]) if row is not None else None


def submit_verification(key_hash: str, code: str, max_attempts: int) -> tuple[int, dict]:
    """Admission + execution for one verification case, shared by the
    REST /verify route and the hosted MCP verify tool so the two
    interfaces cannot drift: same size cap, same rate limit, same
    eligibility, same fast path, same queue. Returns (status, body).

    Eligibility is decided BEFORE admission: a key that cannot pay
    gets its 402 here and never occupies a proof slot or a place in
    line (no free compute, no queue squatting). Eligibility is also
    re-checked inside execute_verification, so a queued job whose
    trial ran out while it waited still refuses before proving."""
    if len(code.encode()) > MAX_CODE_BYTES:
        return 413, {"error": "code_too_large", "max_bytes": MAX_CODE_BYTES}
    if not LIMITER.allow(key_hash):
        return 429, {
            "error": "rate_limited",
            "detail": f"over {LIMITER.limit} requests per minute for this key",
        }
    if STORE.balance_for(key_hash) <= 0 and STORE.trial_cases_used(key_hash) >= TRIAL_CASES:
        return 402, _payment_required_body()
    # Fast path: a slot is free and nobody is waiting — run now, the
    # response shape is unchanged from the pre-queue service.
    if QUEUE.acquire_immediate(key_hash):
        try:
            body, status = _run_once(key_hash, code, max_attempts)
            return status, body
        finally:
            QUEUE.release(key_hash)
    # Busy: the submission joins the durable FIFO queue (F-AX-5). The
    # caller gets a job id and a checkable position — never a silent
    # wait.
    job_id, position = QUEUE.enqueue(key_hash, code, max_attempts)
    STORE.append_audit("job_queued", {"job_id": job_id, "key_hash": key_hash, "position": position})
    return 202, {
        "status": "queued",
        "job_id": job_id,
        "position": position,
        "note": jobqueue.QUEUE_NOTE,
    }


def job_view(key_hash: str, job_id: str) -> dict | None:
    """Queue position / result for a job, or None when the job does
    not exist OR belongs to another key — deliberately
    indistinguishable, so a job's existence never leaks across
    customers. Shared by REST and MCP."""
    job = JOBS.get_job(job_id)
    if job is None or job["key_hash"] != key_hash:
        return None
    if job["status"] == "queued":
        return {"status": "queued", "job_id": job_id, "position": JOBS.job_position(job_id)}
    if job["status"] == "running":
        return {"status": "running", "job_id": job_id}
    if job["status"] == "done":
        return {"status": "done", "job_id": job_id, "result": job["result"]}
    return {"status": "failed", "job_id": job_id, "error": job["error"]}


def check_certificate_body(key_hash: str, certificate: dict, via: str) -> tuple[int, dict]:
    """Certificate re-verification shared by REST /check and the MCP
    check_certificate tool: authenticated + rate limited, revocation
    aware, audited under the calling interface's name (via). A read
    of an existing certificate — consumes no trial case, no credits.
    Returns (status, body)."""
    if not LIMITER.allow(key_hash):
        return 429, {
            "error": "rate_limited",
            "detail": f"over {LIMITER.limit} requests per minute for this key",
        }
    result = ca.verify_certificate(certificate, ca=CA)
    serial = certificate.get("serial") if isinstance(certificate, dict) else None
    if result.get("valid") and serial and STORE.is_revoked(serial):
        result = {"valid": False, "reason": "revoked", "payload": certificate}
    STORE.append_audit(
        "verification",
        {
            "serial": serial,
            "valid": bool(result.get("valid")),
            "reason": result.get("reason"),
            "via": via,
        },
    )
    return 200, result


def _pricing_view() -> dict:
    p = billing.load_pricing()
    return {
        "rate_credits_per_s": round(billing.price_per_compute_s(p), 4),
        "credit_usd": 0.01,
        "covers": {k: v for k, v in p.items() if k != "multiple"},
        "multiple": p["multiple"],
    }


# ─── hosted MCP (the agent gate) ─────────────────────────────────────
# The MCP leg runs in this process, mounted at /mcp, and shares this
# module's store, CA, limiter and proof queue through the callables
# above — it owns no state of its own (mcp_hosted.py carries the
# design). If the mcp package is unavailable or incompatible in this
# environment, REST must not die with it: the mount is guarded and
# the failure is printed, never swallowed.
MCP_MOUNT = None
try:
    import mcp_hosted

    MCP_MOUNT = mcp_hosted.McpMount(
        authenticate=authenticate_key,
        submit=submit_verification,
        job_view=job_view,
        check=lambda key_hash, cert: check_certificate_body(key_hash, cert, via="mcp"),
        revoked_view=lambda: {"issuer": ca.ISSUER, "revoked": sorted(STORE.revoked_serials())},
        usage=lambda key_hash: billing.usage_for(STORE, key_hash),
        pricing=_pricing_view,
    )
except Exception as e:  # noqa: BLE001 — the guard is the point; see above
    print(f"verify_api: hosted MCP disabled ({type(e).__name__}: {e})", flush=True)


@asynccontextmanager
async def _lifespan(_app: FastAPI):
    QUEUE.start()
    if MCP_MOUNT is not None:
        async with MCP_MOUNT.run():
            yield
    else:
        yield


app = FastAPI(
    title="AxiomCode Verify",
    description="Verification-as-evidence: every verdict ships a signed certificate "
    "anyone can re-check without trusting us. Don't trust our AI — verify our proof.",
    lifespan=_lifespan,
)
if MCP_MOUNT is not None:
    app.mount("/mcp", MCP_MOUNT)


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
    key_hash = authenticate_key(presented)
    if key_hash is None:
        raise HTTPException(status_code=401, detail="invalid or missing API key")
    return key_hash


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/verify")
def verify(req: VerifyRequest, key_hash: str = Depends(require_api_key)):
    # The admission path itself lives in submit_verification, shared
    # with the hosted MCP verify tool so the interfaces cannot drift.
    status, body = submit_verification(key_hash, req.code, req.max_attempts)
    return JSONResponse(status_code=status, content=body) if status != 200 else body


@app.get("/verify/jobs/{job_id}")
def verify_job(job_id: str, key_hash: str = Depends(require_api_key)):
    """Queue position / result for a job. Only the submitting key can
    read its job — any other key (or an unknown id) gets a 404, so a
    job's existence never leaks across customers."""
    view = job_view(key_hash, job_id)
    if view is None:
        raise HTTPException(status_code=404, detail="no such job")
    return view


@app.post("/check")
def check(req: CheckRequest, key_hash: str = Depends(require_api_key)):
    # A read of an existing certificate: authenticated + rate limited,
    # but consumes no trial case and no credits.
    status, body = check_certificate_body(key_hash, req.certificate, via="rest")
    return JSONResponse(status_code=status, content=body) if status != 200 else body


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
