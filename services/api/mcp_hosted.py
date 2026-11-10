"""AxiomCode hosted MCP — the agent gate.

The hosted form of the AxiomCode MCP interface: a Streamable HTTP
MCP app mounted into the production FastAPI service (verify_api.py)
at /mcp, so an AI agent gets the same verification service a human
gets over REST — the same store, the same CA, the same limiter and,
since the public flip (F-AX-5), the same durable FIFO proof queue.

Design rules, in order of importance:

  * No new trust surface. This module owns no state. verify_api
    injects the very callables its REST routes use (submit_verification,
    job_view, check_certificate_body), so the two interfaces cannot
    drift: trial policy, eligibility-before-admission, queueing,
    metering and revocation behave identically because they ARE the
    same code paths.
  * Identity is the credential, exactly as on REST. The caller
    presents an API key (Authorization: Bearer, or X-Api-Key); the
    key's SHA-256 hash is the identity. Tools take no identity
    parameter, so no caller can meter, spend or read jobs under
    another key.
  * Identity is request-scoped. KeyAuthMiddleware (pure ASGI)
    authenticates before the MCP app sees the request and stores
    the key hash in a ContextVar — never a module global. (The
    legacy standalone server, mcp_server.py, keeps the caller's
    hash in a module-level variable; under concurrent requests
    that can cross-contaminate identities. Do not copy that shape.)

Transport: Streamable HTTP, stateless, JSON responses. Stateless
fits the product's interaction model — submission is either an
immediate verdict or a job id the caller polls with job_status;
there is no server-side session worth pinning — and it keeps the
leg safe behind the tunnel and across process restarts (queued
jobs are durable in the store, not in a session).

Tool results mirror the REST bodies exactly. Where REST answers
with a non-200 status, the tool returns the same body dict the
REST route would have sent:

    202 queued        -> {"status": "queued", "job_id", "position", "note"}
    402 ineligible    -> {"error": "payment_required", ..., "trial": {...}}
    413 too large     -> {"error": "code_too_large", "max_bytes": ...}
    429 rate limited  -> {"error": "rate_limited", "detail": ...}
    504 proof timeout -> {"error": "proof_timeout", "timeout_s": ...}
    404 job status    -> {"error": "not_found", "detail": "no such job"}

Auth failures never reach a tool: the middleware answers
401 {"error": "invalid or missing API key"} first.
"""

import os
from collections.abc import Callable
from contextlib import asynccontextmanager
from contextvars import ContextVar
from dataclasses import dataclass

from mcp.server.fastmcp import FastMCP
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from mcp.server.transport_security import TransportSecuritySettings
from starlette.applications import Starlette
from starlette.responses import JSONResponse

# The service's public host (gate.yaml's base_url). The MCP
# transport's DNS-rebinding protection validates the Host header;
# requests reach this app either locally or through the Cloudflare
# tunnel carrying this host — both must be named, or the transport
# answers 421 to legitimate callers. AXIOMCODE_MCP_ALLOWED_HOSTS
# (comma-separated) adds hosts for staging/other deployments.
_PUBLIC_HOST = "api.axiom-code.com"


def _transport_security() -> TransportSecuritySettings:
    hosts = ["127.0.0.1", "127.0.0.1:*", "localhost", "localhost:*", "[::1]", "[::1]:*", _PUBLIC_HOST]
    origins = [
        "http://127.0.0.1",
        "http://127.0.0.1:*",
        "http://localhost",
        "http://localhost:*",
        "http://[::1]",
        "http://[::1]:*",
        f"https://{_PUBLIC_HOST}",
    ]
    for extra in (part.strip() for part in os.environ.get("AXIOMCODE_MCP_ALLOWED_HOSTS", "").split(",")):
        if extra:
            hosts.append(extra)
            origins.append(f"https://{extra}")
    return TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=hosts,
        allowed_origins=origins,
    )


# The authenticated caller's identity (an API key's SHA-256 hash)
# for the request currently being served. Set by KeyAuthMiddleware
# only; tools read it through _caller().
current_key_hash: ContextVar[str] = ContextVar("axiomcode_mcp_key_hash", default="")


def _caller() -> str:
    key_hash = current_key_hash.get()
    if not key_hash:
        # Unreachable on the hosted path (the middleware authenticates
        # before any tool runs); a loud failure, never a silent
        # fall-back to some ambient identity.
        raise RuntimeError("MCP tool called without an authenticated API key")
    return key_hash


class KeyAuthMiddleware:
    """Pure-ASGI API-key authentication for the hosted MCP app.

    Accepts the same credentials as REST (X-Api-Key header or
    Authorization: Bearer). `authenticate(presented)` resolves a
    presented key to its hash identity, or None to reject. Pure ASGI
    (not BaseHTTPMiddleware) so the ContextVar set here is the one
    the tool call observes — no task boundary in between.
    """

    def __init__(self, app, authenticate: Callable[[str], str | None]):
        self.app = app
        self.authenticate = authenticate

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        headers = {k.decode("latin-1").lower(): v.decode("latin-1") for k, v in scope.get("headers", [])}
        presented = headers.get("x-api-key", "")
        if not presented:
            auth = headers.get("authorization", "")
            presented = auth[7:] if auth.lower().startswith("bearer ") else ""
        key_hash = self.authenticate(presented)
        if key_hash is None:
            response = JSONResponse({"error": "invalid or missing API key"}, status_code=401)
            await response(scope, receive, send)
            return
        token = current_key_hash.set(key_hash)
        try:
            await self.app(scope, receive, send)
        finally:
            current_key_hash.reset(token)


@dataclass
class HostedMcp:
    server: FastMCP
    app: Starlette
    session_manager: StreamableHTTPSessionManager


class McpMount:
    """The static mount point verify_api attaches at /mcp.

    A Streamable HTTP session manager can be run only ONCE per
    instance ("RuntimeError: .run() can only be called once"), so a
    HostedMcp cannot outlive a single app lifespan — yet the mount
    itself is fixed when the FastAPI app is built. This mount is
    therefore a dispatcher: it holds the deps, builds a HostedMcp
    eagerly (so a broken mcp package fails at import, where
    verify_api's guard can see it), and builds a FRESH one on every
    lifespan entry via run(). Requests arriving with no live
    instance (before the first startup, or after a failed rebuild)
    get an honest 503, never a hang or a wrong answer. Auth wraps
    the dispatcher, so even the 503 path requires a valid key.
    """

    def __init__(
        self,
        *,
        authenticate: Callable[[str], str | None],
        submit: Callable[[str, str, int], tuple[int, dict]],
        job_view: Callable[[str, str], dict | None],
        check: Callable[[str, dict], tuple[int, dict]],
        revoked_view: Callable[[], dict],
        usage: Callable[[str], dict],
        pricing: Callable[[], dict],
    ):
        self._deps = {
            "submit": submit,
            "job_view": job_view,
            "check": check,
            "revoked_view": revoked_view,
            "usage": usage,
            "pricing": pricing,
        }
        self._current: HostedMcp | None = build_hosted_mcp(**self._deps)
        self._authed = KeyAuthMiddleware(self._dispatch, authenticate)

    async def __call__(self, scope, receive, send):
        await self._authed(scope, receive, send)

    async def _dispatch(self, scope, receive, send):
        current = self._current
        if current is None:
            response = JSONResponse({"error": "mcp_unavailable"}, status_code=503)
            await response(scope, receive, send)
            return
        await current.app(scope, receive, send)

    @asynccontextmanager
    async def run(self):
        """App-lifespan hook: rebuild a fresh HostedMcp and run its
        session manager for the life of the app. A failed rebuild
        disables the leg (503s) but never takes REST down with it."""
        try:
            self._current = build_hosted_mcp(**self._deps)
        except Exception as e:  # noqa: BLE001 — the leg dies, not the API
            print(f"mcp_hosted: rebuild failed ({type(e).__name__}: {e})", flush=True)
            self._current = None
        if self._current is None:
            yield
            return
        async with self._current.session_manager.run():
            yield


def build_hosted_mcp(
    *,
    submit: Callable[[str, str, int], tuple[int, dict]],
    job_view: Callable[[str, str], dict | None],
    check: Callable[[str, dict], tuple[int, dict]],
    revoked_view: Callable[[], dict],
    usage: Callable[[str], dict],
    pricing: Callable[[], dict],
) -> HostedMcp:
    """Build the hosted MCP server around verify_api's own callables.

    submit(key_hash, code, max_attempts) -> (http_status, body) is the
    REST /verify admission path itself; job_view and check are the
    shared bodies behind GET /verify/jobs/{id} and POST /check.
    """
    _pricing_source = pricing
    # streamable_http_path="/": the app is mounted at /mcp by
    # verify_api, so the transport must answer at the mount root —
    # the FastMCP default path ("/mcp") would nest it at /mcp/mcp.
    server = FastMCP(
        "axiomcode-verify",
        stateless_http=True,
        json_response=True,
        streamable_http_path="/",
        transport_security=_transport_security(),
    )

    @server.tool()
    def verify(code: str, max_attempts: int = 1) -> dict:
        """Machine-verify a Lean 4 proof and get a signed certificate of the verdict.
        The proof is really compiled — sorry/admit never counts as verified.
        Anyone can re-check the certificate without trusting us:
        verification-as-evidence, not verification-as-opinion.
        Trial keys (first 10 cases, no credit balance) get the verdict
        with certificate=None; certificates unlock with a credit pack.
        When every proof slot is busy the submission joins the FIFO
        queue instead of failing: the result is {"status": "queued",
        "job_id", "position", "note"} — poll job_status(job_id) for
        the finished verdict."""
        _status, body = submit(_caller(), code, max_attempts)
        return body

    @server.tool()
    def job_status(job_id: str) -> dict:
        """Position or result for a verification job you submitted.
        Only the submitting key can read its job — another key's job
        and an unknown id are indistinguishable ({"error": "not_found"}),
        so a job's existence never leaks across customers."""
        view = job_view(_caller(), job_id)
        if view is None:
            return {"error": "not_found", "detail": "no such job"}
        return view

    @server.tool()
    def check_certificate(certificate: dict) -> dict:
        """Re-verify a verification certificate: signature, validity window,
        revocation status. Anyone can check — never take our word for it.
        (Authenticated like every tool; consumes no trial case or credits.)"""
        _status, body = check(_caller(), certificate)
        return body

    @server.tool()
    def revoked() -> dict:
        """The public revocation list: issuer + revoked certificate serials."""
        return revoked_view()

    @server.tool()
    def health() -> dict:
        """Service liveness, the MCP twin of GET /health."""
        return {"status": "ok"}

    @server.tool()
    def usage_report() -> dict:
        """Total metered spend for the calling API key, in credits and USD."""
        return usage(_caller())

    @server.tool()
    def pricing() -> dict:
        """Current price list: rate per compute-second and what it covers."""
        # The injected callable is captured under a different name:
        # this tool's own def rebinds `pricing` in the builder scope.
        return _pricing_source()

    app = server.streamable_http_app()
    return HostedMcp(server=server, app=app, session_manager=server.session_manager)
