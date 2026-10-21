"""AxiomCode verification API (production build).

POST /verify {code} -> {verified, attempts, certificate, usage}
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

import json
import os
import sys
import tempfile

sys.path.insert(0, "/home/hatch/workspace/axiomcode/repo")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import ca
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
GATE = limits.ConcurrencyGate()

app = FastAPI(
    title="AxiomCode Verify",
    description="Verification-as-evidence: every verdict ships a signed certificate "
    "anyone can re-check without trusting us. Don't trust our AI — verify our proof.",
)


class VerifyRequest(BaseModel):
    code: str
    max_attempts: int = 1


class CheckRequest(BaseModel):
    certificate: dict


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
    try:
        return verify_service.execute_verification(
            store=STORE,
            authority=CA,
            key_hash=key_hash,
            code=req.code,
            max_attempts=req.max_attempts,
            work_root=WORK_ROOT,
            prefix="ax-api-",
            toolchain=TOOLCHAIN,
            search=iterative_proof_search,
            extra_subject=lambda: {"lean_version": lean_version()},
            gate=GATE,
            timeout_s=PROOF_TIMEOUT_S,
            trial_cases=TRIAL_CASES,
        )
    except verify_service.PaymentRequiredError:
        return JSONResponse(
            status_code=402,
            content={
                "error": "payment_required",
                "detail": "trial cases exhausted and no credit balance; certificates unlock with a credit pack",
                "trial": {"cases_used": TRIAL_CASES, "cases_left": 0, "certificates": "unlock with a credit pack"},
            },
        )
    except verify_service.TooManyConcurrentError:
        return JSONResponse(
            status_code=429,
            content={"error": "too_many_concurrent_proofs", "detail": f"at most {GATE.limit} proofs in flight per key"},
        )
    except verify_service.ProofTimeoutError:
        return JSONResponse(
            status_code=504,
            content={"error": "proof_timeout", "timeout_s": PROOF_TIMEOUT_S},
        )


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
        return _plain_event_data(event)

    try:
        return stripe_billing.handle_webhook(STORE, payload, signature, verify_signature)
    except Exception:  # bad signature or malformed event — not from Stripe as-is
        return JSONResponse(status_code=400, content={"error": "invalid_signature_or_payload"})
