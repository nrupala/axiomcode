"""AxiomCode verification MCP server — the agent-native interface.

Tool: verify(code, max_attempts) -> {verified, attempts, certificate, usage}
Auth: Authorization: Bearer <api_key> (keys in API_KEYS_FILE, one per line: <key_id>:<key>)
Metering: every call appended to METER_LOG (JSONL) — the audit log doubles as
the billing record. Priced in compute-seconds; see CREDITS_PER_COMPUTE_S.

Run: uvicorn mcp_server:mcp_app --port 8092
(Uses Streamable HTTP transport so remote agents can connect.)
"""

import hashlib
import os
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, "/home/hatch/workspace/axiomcode/repo")
sys.path.insert(0, os.path.dirname(__file__))

from billing import load_keys, meter, price_per_compute_s, usage_for
from certs import issue as issue_cert
from mcp.server.fastmcp import FastMCP
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from core.prover import iterative_proof_search

# ─── config ──────────────────────────────────────────────────────────────
API_KEYS_FILE = os.environ.get("AXIOMCODE_API_KEYS", "/home/hatch/workspace/axiomcode/api-prototype/keys.txt")
METER_LOG = os.environ.get("AXIOMCODE_METER_LOG", "/home/hatch/workspace/axiomcode/api-prototype/meter.jsonl")
CERT_SECRET = os.environ.get("AXIOMCODE_CERT_SECRET", "dev-secret-change-me").encode()
TOOLCHAIN = "leanprover/lean4:v4.35.0-rc3"

mcp = FastMCP("axiomcode-verify")


class _KeyCtx:
    id = "anonymous"


_KEY = _KeyCtx()


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        auth = request.headers.get("authorization", "")
        key = auth[7:] if auth.lower().startswith("bearer ") else ""
        kid = load_keys(API_KEYS_FILE).get(key)
        if not kid:
            return JSONResponse({"error": "invalid or missing API key"}, status_code=401)
        _KEY.id = kid
        return await call_next(request)


@mcp.tool()
def verify(code: str, max_attempts: int = 1) -> dict:
    """Machine-verify a Lean 4 proof and get a signed certificate of the verdict.
    The proof is really compiled — sorry/admit never counts as verified.
    Anyone can re-check the certificate without trusting us:
    verification-as-evidence, not verification-as-opinion."""
    key_id = _KEY.id
    proj = Path(tempfile.mkdtemp(prefix="ax-mcp-"))
    (proj / "lean-toolchain").write_text(TOOLCHAIN)
    (proj / "lakefile.lean").write_text(
        "import Lake\nopen Lake DSL\npackage v where\nlean_lib V where\n  roots := #[`V]\n"
    )
    src = proj / "V.lean"

    def writer(c: str) -> Path:
        src.write_text(c)
        return src

    t0 = time.time()
    verified, _, attempts, _ = iterative_proof_search(
        writer,
        proj,
        code,
        None,
        "none",
        max_attempts=max_attempts,
        use_pantograph=False,
    )
    compute_s = time.time() - t0

    code_sha = hashlib.sha256(code.encode()).hexdigest()
    usage = meter(METER_LOG, key_id, code_sha, verified, compute_s)
    cert = issue_cert(
        {
            "code_sha256": code_sha,
            "verified": verified,
            "attempts": attempts,
            "toolchain": TOOLCHAIN,
            "key_id": key_id,
        }
    )
    return {
        "verified": verified,
        "attempts": attempts,
        "certificate": cert,
        "usage": usage,
    }


@mcp.tool()
def usage_report() -> dict:
    """Total metered spend for the calling API key, in credits and USD."""
    return usage_for(METER_LOG, _KEY.id)


@mcp.tool()
def check_certificate(certificate: dict) -> dict:
    """Re-verify a verification certificate: signature, validity window,
    revocation status. Anyone can check — never take our word for it."""
    from certs import check as check_cert

    return check_cert(certificate)


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
