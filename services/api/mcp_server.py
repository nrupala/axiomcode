"""AxiomCode verification MCP server — the agent-native interface.

Tools: verify(code, max_attempts), check_certificate(certificate),
pricing(), usage_report().
Auth: Authorization: Bearer <api_key>. Keys are provisioned in the
durable store (store.py — only SHA-256 hashes are kept); the server
process's own key is supplied via AXIOMCODE_API_KEY and provisioned
at startup if unknown (label AXIOMCODE_API_KEY_LABEL, default
"mcp-server"). The caller's identity is the hash of the presented
key — tools take no identity parameter, so no caller can meter,
spend or impersonate under another key.

Production build: certificates are Ed25519-signed (ca.py, format v2);
metering, revocation, grants and the hash-chained audit log live in
the durable store (store.py). Trial policy (W3) applies exactly as
on REST: a new key's first 10 cases return verdicts without a
certificate; certificates unlock with paid credits. Per-key rate
limit + proof concurrency cap (limits.py) and submission size /
proof timeout caps (W5) apply too — all enforced by the shared
verify_service flow so the interfaces cannot drift.

Run: uvicorn mcp_server:mcp_app --port 8092
(Uses Streamable HTTP transport so remote agents can connect.)
"""

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, "/home/hatch/workspace/axiomcode/repo")
sys.path.insert(0, os.path.dirname(__file__))

import ca
import limits
import verify_service
from billing import price_per_compute_s, usage_for
from mcp.server.fastmcp import FastMCP
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from store import Store

from core.prover import iterative_proof_search

# ─── config ──────────────────────────────────────────────────────────────
_HERE = Path(__file__).parent
WORK_ROOT = os.environ.get("AXIOMCODE_WORK_ROOT", tempfile.gettempdir())
TOOLCHAIN = "leanprover/lean4:v4.35.0-rc3"
MAX_CODE_BYTES = int(os.environ.get("AXIOMCODE_MAX_CODE_BYTES", "262144"))
TRIAL_CASES = verify_service.TRIAL_CASES
PROOF_TIMEOUT_S = verify_service.PROOF_TIMEOUT_S

CA = ca.CA.load_or_create()
STORE = Store()
LIMITER = limits.RateLimiter()
GATE = limits.ConcurrencyGate()

# The server process's own API key (clients present it as Bearer).
# Provisioned into the store at startup if unknown; a later operator
# revocation in the store wins over this env var (ensure, not force).
_SERVER_KEY = os.environ.get("AXIOMCODE_API_KEY", "")
if _SERVER_KEY:
    STORE.ensure_api_key(_SERVER_KEY, label=os.environ.get("AXIOMCODE_API_KEY_LABEL", "mcp-server"))

mcp = FastMCP("axiomcode-verify")


class _KeyCtx:
    key_hash = ""


_KEY = _KeyCtx()


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        auth = request.headers.get("authorization", "")
        key = auth[7:] if auth.lower().startswith("bearer ") else ""
        row = STORE.authenticate_api_key(key) if key else None
        if row is None:
            return JSONResponse({"error": "invalid or missing API key"}, status_code=401)
        _KEY.key_hash = str(row["key_hash"])
        return await call_next(request)


@mcp.tool()
def verify(code: str, max_attempts: int = 1) -> dict:
    """Machine-verify a Lean 4 proof and get a signed certificate of the verdict.
    The proof is really compiled — sorry/admit never counts as verified.
    Anyone can re-check the certificate without trusting us:
    verification-as-evidence, not verification-as-opinion.
    Trial keys (first 10 cases, no credit balance) get the verdict
    with certificate=None; certificates unlock with a credit pack."""
    key_hash = _KEY.key_hash
    if len(code.encode()) > MAX_CODE_BYTES:
        return {"error": "code_too_large", "max_bytes": MAX_CODE_BYTES}
    if not LIMITER.allow(key_hash):
        return {"error": "rate_limited", "detail": f"over {LIMITER.limit} requests per minute for this key"}
    try:
        return verify_service.execute_verification(
            store=STORE,
            authority=CA,
            key_hash=key_hash,
            code=code,
            max_attempts=max_attempts,
            work_root=WORK_ROOT,
            prefix="ax-mcp-",
            toolchain=TOOLCHAIN,
            search=iterative_proof_search,
            gate=GATE,
            timeout_s=PROOF_TIMEOUT_S,
            trial_cases=TRIAL_CASES,
        )
    except verify_service.PaymentRequiredError:
        return {
            "error": "payment_required",
            "detail": "trial cases exhausted and no credit balance; certificates unlock with a credit pack",
            "trial": {"cases_used": TRIAL_CASES, "cases_left": 0, "certificates": "unlock with a credit pack"},
        }
    except verify_service.TooManyConcurrentError:
        return {"error": "too_many_concurrent_proofs", "detail": f"at most {GATE.limit} proofs in flight per key"}
    except verify_service.ProofTimeoutError:
        return {"error": "proof_timeout", "timeout_s": PROOF_TIMEOUT_S}


@mcp.tool()
def usage_report() -> dict:
    """Total metered spend for the calling API key, in credits and USD."""
    return usage_for(STORE, _KEY.key_hash)


@mcp.tool()
def check_certificate(certificate: dict) -> dict:
    """Re-verify a verification certificate: signature, validity window,
    revocation status. Anyone can check — never take our word for it.
    (Authenticated like every tool; consumes no trial case or credits.)"""
    if not LIMITER.allow(_KEY.key_hash):
        return {"error": "rate_limited", "detail": f"over {LIMITER.limit} requests per minute for this key"}
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
            "via": "mcp",
        },
    )
    return result


@mcp.tool()
def pricing() -> dict:
    """Current price list: rate per compute-second and what it covers."""
    from billing import load_pricing

    p = load_pricing()
    return {
        "rate_credits_per_s": round(price_per_compute_s(p), 4),
        "credit_usd": 0.01,
        "covers": {k: v for k, v in p.items() if k != "multiple"},
        "multiple": p["multiple"],
    }


mcp_app = mcp.streamable_http_app()
mcp_app.add_middleware(AuthMiddleware)
