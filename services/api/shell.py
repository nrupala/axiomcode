"""AxiomCode interactive shell (the Ask leg) — a conversational
layer over the live verification service, declared as pathway
PW-SHELL in gate.yaml. Design: the slice-2 report
(workspace/axiomcode/interactive-shell-slice2-report.md).

The shell is how a human talks to the service: phrase what you want
verified, submit it, hear the verdict in plain words, ask about
usage, pricing, revocation. Its one absolute invariant: THE MODEL
NEVER JUDGES. Verdicts come only from the Lean kernel through the
same verify_api callables REST and MCP call — this module owns no
store, no CA and no admission path, so trial counting, eligibility,
metering, queueing and revocation cannot drift between legs.

Grounding is structural, not prompt-deep. Every turn answers on
three separated channels:

  result — the raw API payload, exactly as the shared callable
           returned it (the page renders certificates from here);
  facts  — fact blocks rendered HERE, by pure functions over the
           payload, each in two registers (a technical line and a
           plain-words line built from the same values, so the
           registers cannot disagree);
  explanation — the model's conversational text, or None. It is
           never parsed for facts and never rendered as a verdict.

The model's context is a whitelist assembled in build_messages():
the charter, the capped history, the user's message, and this
turn's fact blocks. The caller's key — and its hash — are never in
it. When an action cannot be served, the turn carries a fixed
honesty fact and the model is not called; when the MODEL is down,
the turn still carries result + facts with explanation None and
degraded True — the facts are the complete answer on their own.

The key arrives per request in the X-Api-Key header (the REST
rule), is authenticated by verify_api before any turn runs, and is
never stored, logged or echoed by this module: the shell keeps no
state at all (history is client-held and size-capped below).

This module also carries BrowserCorsMiddleware: the browser-facing
paths (/verify, /check, /revoked, /shell) answer CORS for the
site's own origin only. The API shipped without any CORS leg, so
the site's own /verify and /check pages — cross-origin fetches with
a JSON content type and an API-key header, i.e. preflighted — were
blocked by real browsers (live-probed 2026-11-11: preflight
answered 405, no Access-Control-Allow-Origin). The middleware is
path- and origin-scoped; non-browser traffic is byte-identical.
"""

import json
import os
import time
import urllib.request
from collections.abc import Callable
from typing import Any, NamedTuple

import limits


def _env(name: str, default: str = "") -> str:
    """Read an environment variable, with a default."""
    return os.getenv(name, default)


# ─── model lane ─────────────────────────────────────────────────────
# The box-local llama router (loopback, OpenAI-compatible). No
# credential is needed for it; URL/model/key are env-configurable so
# another lane is a configuration change, not a redesign.
MODEL_URL = _env("AXIOMCODE_SHELL_MODEL_URL", "http://127.0.0.1:8830/v1")
MODEL = _env("AXIOMCODE_SHELL_MODEL", "qwen2.5-coder-7b")
MODEL_TIMEOUT_S = float(_env("AXIOMCODE_SHELL_MODEL_TIMEOUT_S", "25"))
MODEL_MAX_TOKENS = 700
MODEL_API_KEY = _env("AXIOMCODE_SHELL_MODEL_API_KEY")

# ─── turn bounds ────────────────────────────────────────────────────
MAX_MESSAGE_CHARS = 8000
MAX_HISTORY_ITEMS = 16
MAX_HISTORY_ITEM_CHARS = 4000
MAX_CERT_BYTES = 524288

# The shell's own per-key limiter (same 60/min shape as REST, a
# separate instance so conversation cannot starve the key's REST
# budget; actions inside a turn still pass the shared REST limiter
# inside the shared callables).
LIMITER = limits.RateLimiter()

# A fact block: both registers of one piece of service truth,
# rendered in code from an API payload — never by the model.
Fact = dict[str, str]


def _fact(kind: str, title: str, technical: str, plain: str) -> Fact:
    return {"kind": kind, "title": title, "technical": technical, "plain": plain}


def _date(epoch: Any) -> str:
    try:
        return time.strftime("%Y-%m-%d", time.gmtime(int(epoch)))
    except (TypeError, ValueError, OverflowError):
        return "an unknown date"


# ─── fact renderers (pure functions of API payloads) ────────────────


def render_verdict(status: int, body: dict) -> Fact:
    """The verdict fact for a /verify-shaped (status, body) — REST,
    a finished queue job, and the shell all render through here."""
    if status == 202:
        return _fact(
            "queued",
            "Queued",
            f"status queued; job {body.get('job_id')}; position {body.get('position')}",
            f"Every proof slot is busy, so your submission joined the queue at position "
            f"{body.get('position')}. Nothing is lost and nobody can jump the line — "
            "ask for the status and I will check your place.",
        )
    if status == 402:
        return _fact(
            "payment_required",
            "Trial exhausted",
            "error payment_required; trial cases used 10 of 10; balance 0",
            "Your 10 free trial cases are used up and this key holds no credits, so "
            "the service refused BEFORE running anything — no compute was spent and "
            "nothing was queued. Certificates unlock with a credit pack; packs are "
            "not yet on sale.",
        )
    if status == 413:
        return _fact(
            "too_large",
            "Submission too large",
            f"error code_too_large; max_bytes {body.get('max_bytes')}",
            "That submission is larger than the service accepts "
            f"({body.get('max_bytes')} bytes of source at most). Split the artifact "
            "and submit the pieces.",
        )
    if status == 429:
        return _fact(
            "rate_limited",
            "Rate limited",
            "error rate_limited; over the per-key request limit",
            "This key is sending requests faster than the service allows. Wait a moment and try again.",
        )
    if status == 504:
        return _fact(
            "proof_timeout",
            "Proof timed out",
            f"error proof_timeout; timeout_s {body.get('timeout_s')}",
            "The proof ran past the per-call time cap, so the service stopped it and "
            "issued no verdict. A smaller artifact or a simpler target usually "
            "checks in time.",
        )
    if status != 200:
        return _fact(
            "service_error",
            "The service refused",
            f"status {status}; error {body.get('error')}",
            "The verification service refused this submission. The technical line "
            "above is exactly what it said; no verdict was issued.",
        )
    verified = bool(body.get("verified"))
    usage = body.get("usage") or {}
    trial = body.get("trial")
    cert = body.get("certificate")
    tech = [
        f"verdict {'PASSED' if verified else 'FAILED'}",
        f"attempts {body.get('attempts')}",
        f"engine time {usage.get('compute_s')}s",
        f"credits {usage.get('credits')}",
    ]
    if cert:
        tech.append(f"certificate serial {cert.get('serial')}")
        tech.append(f"valid {_date(cert.get('valid_from'))} to {_date(cert.get('valid_until'))}")
    if trial:
        total = int(trial.get("cases_used", 0)) + int(trial.get("cases_left", 0))
        tech.append(f"trial case {trial.get('cases_used')} of {total}; no certificate (trial)")
    if verified and cert:
        plain = (
            "The Lean toolchain checked your proof and it PASSED. A certificate was "
            f"issued — serial {cert.get('serial')}, valid until "
            f"{_date(cert.get('valid_until'))}. That certificate is the document you "
            "can hand to anyone; they can check it without trusting us. This run "
            f"used {usage.get('compute_s')} seconds of engine time "
            f"({usage.get('credits')} credits)."
        )
    elif verified and trial:
        plain = (
            "The Lean toolchain checked your proof and it PASSED. This was one of "
            "your free trial cases, so NO certificate was issued — trial verdicts "
            "never carry certificates; the certificate is the paid product. You "
            f"have {trial.get('cases_left')} trial cases left."
        )
    elif verified:
        plain = "The Lean toolchain checked your proof and it PASSED. No certificate was issued with this verdict."
    elif cert:
        plain = (
            "The Lean toolchain checked your proof and it did NOT pass. A "
            f"certificate was still issued — serial {cert.get('serial')} — recording "
            "exactly that: what was checked, and that the machine said no. It "
            "certifies the check happened; it is not a pass."
        )
    elif trial:
        plain = (
            "The Lean toolchain checked your proof and it did NOT pass, so no "
            "certificate was issued. The transcript in the full result shows where "
            f"the proof broke. You have {trial.get('cases_left')} trial cases left."
        )
    else:
        plain = (
            "The Lean toolchain checked your proof and it did NOT pass, so no "
            "certificate was issued. The transcript in the full result shows where "
            "the proof broke."
        )
    return _fact("verdict", "Verdict", "; ".join(tech), plain)


def render_job(view: dict) -> Fact:
    """The fact for a job view (job_view's dict shape)."""
    status = view.get("status")
    if status == "queued":
        return _fact(
            "queued",
            "Still queued",
            f"job {view.get('job_id')}; position {view.get('position')}",
            f"Your verification is still in line at position {view.get('position')}. "
            "The queue is first-in-first-out and your place is held.",
        )
    if status == "running":
        return _fact(
            "running",
            "Running now",
            f"job {view.get('job_id')}; status running",
            "Your proof is running on the engine right now. Ask again in a few seconds for the verdict.",
        )
    if status == "done":
        return render_verdict(200, view.get("result") or {})
    return _fact(
        "job_failed",
        "Job failed",
        f"job {view.get('job_id')}; error {view.get('error')}",
        "The queued verification job failed before producing a verdict. The "
        "technical line above is what the service recorded; no verdict was issued "
        "and no certificate exists for this job.",
    )


def render_check(status: int, body: dict) -> Fact:
    """The fact for a /check-shaped (status, body)."""
    if status == 429:
        return render_verdict(429, body)
    if status != 200:
        return _fact(
            "service_error",
            "The checker refused",
            f"status {status}; error {body.get('error')}",
            "The certificate checker refused this request. The technical line above "
            "is exactly what it said; no validation was performed.",
        )
    payload = body.get("payload") or {}
    serial = payload.get("serial") if isinstance(payload, dict) else None
    if body.get("valid"):
        return _fact(
            "check",
            "Certificate valid",
            f"valid true; serial {serial}",
            "This certificate is VALID: its signature verifies against the "
            "certification authority's published key, and its serial is not on the "
            "public revocation list.",
        )
    reason = body.get("reason")
    if reason == "revoked":
        return _fact(
            "check",
            "Certificate revoked",
            f"valid false; reason revoked; serial {serial}",
            "This certificate has been REVOKED — its serial is on the public "
            "revocation list. Do not rely on it, whatever it once said.",
        )
    return _fact(
        "check",
        "Certificate not valid",
        f"valid false; reason {reason}; serial {serial}",
        f"This certificate did NOT validate. The checker's reason, in its own "
        f"terms: {reason}. A certificate that does not validate proves nothing — "
        "treat the code it describes as unchecked.",
    )


def render_account(view: dict) -> Fact:
    """Account facts from the store-backed account view: usage
    totals, balance, trial state — the caller's own key only."""
    used = view.get("trial_cases_used")
    total = view.get("trial_cases_total")
    left = view.get("trial_cases_left")
    tech = (
        f"trial cases used {used} of {total}; metered calls {view.get('calls')}; "
        f"credits used {view.get('credits_used')}; usd used {view.get('usd_used')}; "
        f"balance {view.get('balance_credits')} credits"
    )
    plain = (
        f"You have used {used} of your {total} free trial cases — {left} left. "
        f"Your key has run {view.get('calls')} metered verifications totalling "
        f"{view.get('credits_used')} credits (about ${view.get('usd_used')}). Your "
        f"current balance is {view.get('balance_credits')} credits."
    )
    if not left and not (view.get("balance_credits") or 0) > 0:
        plain += (
            " With the trial used up and no balance, new verifications will be "
            "refused until credit packs open — they are not yet on sale."
        )
    return _fact("account", "Your account", tech, plain)


# The pack table is the site's published pricing (site/pages_main.py,
# /pricing/): the shell may state it, and nothing beyond it.
_PACKS_PLAIN = (
    "Packs: Starter 1,000 credits for $10, Growth 5,000 for $50, Scale 20,000 "
    "for $200. Packs are NOT yet on sale — billing is paused, and keys with "
    "the 10-case free trial are issued free on request."
)


def render_pricing(view: dict) -> Fact:
    """Pricing facts from the API's own pricing view."""
    rate = view.get("rate_credits_per_s")
    tech = (
        f"rate {rate} credits per compute-second; 1 credit = "
        f"US${view.get('credit_usd')}; pricing multiple {view.get('multiple')}"
    )
    plain = (
        f"Verification is metered by engine time: {rate} credits per second, and "
        "1 credit is always US$0.01 — a check that takes 12 seconds costs about "
        "11 credits, roughly eleven cents. " + _PACKS_PLAIN
    )
    return _fact("pricing", "Pricing", tech, plain)


def render_revoked(body: dict) -> Fact:
    """Revocation-list facts from the public /revoked body."""
    serials = body.get("revoked") or []
    n = len(serials)
    tech = f"issuer {body.get('issuer')}; revoked serials {n}"
    if n:
        plain = (
            f"The public revocation list currently names {n} revoked certificate "
            "serial(s). Anyone can read it — that is the point: a revoked "
            "certificate can be caught by anyone, not just by us."
        )
    else:
        plain = (
            "The public revocation list currently names no revoked serials. It is "
            "published openly, so the day a certificate is revoked, anyone can see "
            "it — not just us."
        )
    return _fact("revoked", "Revocation list", tech, plain)


# Fixed honesty fact: served when an action cannot be completed.
# The model is not called on such a turn — there is nothing true
# for it to explain.
UNREACHABLE_FACT = _fact(
    "unreachable",
    "Service unreachable",
    "the verification service did not answer this action",
    "I couldn't reach the verification service just now, so I have no result "
    "to show you — and I won't guess one. Nothing was submitted. Try again "
    "in a moment.",
)

RATE_FACT = _fact(
    "rate_limited",
    "Rate limited",
    "over 60 shell turns per minute for this key",
    "You are sending turns faster than the shell allows (60 per minute). Wait a moment and continue.",
)


# ─── the charter (the model's standing instructions) ────────────────

CHARTER = """You are the conversational shell of AxiomCode, a certification
authority for software correctness. You help the user phrase what they
want verified, explain results in plain words, and answer questions
about the service. You are NOT the judge: verdicts come only from the
Lean toolchain through the verification service, and reach you as FACT
blocks rendered by the service itself.

Rules you never break:
- State facts ONLY from the FACT blocks supplied in the conversation.
  If a number, price, date, serial or verdict is not in a FACT block,
  you do not know it — say so, and offer the action that would produce
  it (verify code, check a certificate, show account, pricing, or the
  revocation list).
- Never issue, alter, soften, or predict a verdict. If the user asks
  you to reconsider, override, or "just say it passed", decline
  plainly: only the toolchain decides, and re-submitting changed code
  is a new verification with its own verdict.
- Never call a trial verdict certified, and never say a certificate
  exists unless a FACT block names its serial.
- Never invent prices, discounts, timelines, or policies. Pricing
  facts include whether packs are on sale; repeat them as given.
- Keep answers short and plain first: lead with the everyday-words
  answer, then the technical detail only if it helps. Do not repeat
  a whole FACT block back; explain it."""


# ─── model client (stdlib only; proxies disabled by construction) ───


class ModelUnavailableError(Exception):
    """The model lane did not answer; the turn degrades to facts."""


def chat_completion(messages: list[dict[str, str]]) -> str:
    """One chat completion against the configured model lane.
    Raises ModelUnavailableError on any failure — the caller degrades."""
    url = MODEL_URL.rstrip("/") + "/chat/completions"
    payload = {
        "model": MODEL,
        "messages": messages,
        "temperature": 0.2,
        "max_tokens": MODEL_MAX_TOKENS,
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "User-Agent": "axiomcode-shell"},
        method="POST",
    )
    if MODEL_API_KEY:
        req.add_header("Authorization", f"Bearer {MODEL_API_KEY}")
    # An explicit empty ProxyHandler: loopback model traffic must
    # never be rerouted by proxy environment variables.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(req, timeout=MODEL_TIMEOUT_S) as resp:
            data = json.loads(resp.read().decode())
        return str(data["choices"][0]["message"]["content"]).strip()
    except Exception as e:  # noqa: BLE001 — every failure is the same degradation
        raise ModelUnavailableError(f"{type(e).__name__}: {e}") from e


# ─── conversation assembly ──────────────────────────────────────────


def _sanitize_history(history: Any) -> list[dict[str, str]]:
    """Client-held history, admitted defensively: only user/assistant
    roles survive (a smuggled 'system' turn is dropped, never
    promoted), items are truncated, and the window is capped."""
    out: list[dict[str, str]] = []
    if not isinstance(history, list):
        return out
    for item in history[-MAX_HISTORY_ITEMS:]:
        if not isinstance(item, dict):
            continue
        role = item.get("role")
        if role not in ("user", "assistant"):
            continue
        content = str(item.get("content") or "")[:MAX_HISTORY_ITEM_CHARS]
        if content:
            out.append({"role": role, "content": content})
    return out


def build_messages(facts: list[Fact], history: Any, message: str) -> list[dict[str, str]]:
    """The model's whole world for one turn: the charter, the
    sanitized history, and the user's message carrying this turn's
    fact blocks. Nothing else can reach the model — no key, no hash,
    no store internals."""
    messages = [{"role": "system", "content": CHARTER}]
    messages.extend(_sanitize_history(history))
    user = message
    if facts:
        appendix = "\n\n".join(f"FACT ({f['kind']}): {f['plain']} [record: {f['technical']}]" for f in facts)
        facts_block = f"FACTS FROM THE SERVICE (the only facts you may state):\n{appendix}"
        user = f"{message}\n\n{facts_block}" if message else facts_block
    messages.append({"role": "user", "content": user})
    return messages


# ─── intent routing (facts attached before the model speaks) ────────
# A small deterministic router in the Astroscience Module-G posture:
# questions about the caller's own account, the pricing, or the
# revocation list attach the corresponding code-rendered fact, so the
# model explains true numbers instead of inventing them. A missed
# intent is harmless — the charter makes the model say what it can
# check instead of guessing.

_ACCOUNT_WORDS = ("usage", "spent", "spend", "balance", "trial", "how many", "left")
_PRICING_WORDS = ("price", "pricing", "cost", "pack", "buy", "pay")
_REVOKED_WORDS = ("revok",)


class ShellDeps(NamedTuple):
    """The verify_api callables the shell orchestrates — injected,
    never imported, so the shell cannot grow its own admission path."""

    submit: Callable[[str, str, int], tuple[int, dict]]
    job_view: Callable[[str, str], dict | None]
    check: Callable[[str, dict], tuple[int, dict]]
    account: Callable[[str], dict]
    pricing: Callable[[], dict]
    revoked: Callable[[], dict]
    model_chat: Callable[[list[dict[str, str]]], str]


def _intent_facts(deps: ShellDeps, key_hash: str, message: str) -> list[Fact]:
    m = message.lower()
    facts: list[Fact] = []
    if any(w in m for w in _ACCOUNT_WORDS):
        facts.append(render_account(deps.account(key_hash)))
    if any(w in m for w in _PRICING_WORDS):
        facts.append(render_pricing(deps.pricing()))
    if any(w in m for w in _REVOKED_WORDS):
        facts.append(render_revoked(deps.revoked()))
    return facts


def handle_turn(deps: ShellDeps, key_hash: str, turn: dict) -> tuple[int, dict]:
    """One shell turn. Turn-level problems (bad shape, the shell's
    own rate limit) answer with REST-shaped error bodies; everything
    the SERVICE decided — verdicts, refusals, queue positions — is a
    200 turn carrying facts, because in a conversation a refusal is
    information, not a transport failure."""
    message = str(turn.get("message") or "").strip()
    action = str(turn.get("action") or "chat")
    code = turn.get("code")
    certificate = turn.get("certificate")
    if len(message) > MAX_MESSAGE_CHARS:
        return 413, {"error": "message_too_large", "max_chars": MAX_MESSAGE_CHARS}
    if action not in ("chat", "verify", "check"):
        return 400, {"error": "unknown_action", "action": action}
    if action == "chat" and not message:
        return 400, {"error": "empty_turn"}
    if action == "verify" and not (isinstance(code, str) and code.strip()):
        return 400, {"error": "code_required"}
    if action == "check":
        if not isinstance(certificate, dict):
            return 400, {"error": "certificate_required"}
        if len(json.dumps(certificate)) > MAX_CERT_BYTES:
            return 413, {"error": "certificate_too_large", "max_bytes": MAX_CERT_BYTES}
    if not LIMITER.allow(key_hash):
        return 429, {"error": "rate_limited", "detail": "over 60 shell turns per minute for this key"}

    facts: list[Fact] = []
    result: Any = None
    job_id: str | None = None
    try:
        if action == "verify":
            assert isinstance(code, str)  # shape-validated above
            status, body = deps.submit(key_hash, code, int(turn.get("max_attempts") or 1))
            result = body
            facts.append(render_verdict(status, body))
            if status == 202:
                job_id = str(body.get("job_id"))
        elif action == "check":
            assert isinstance(certificate, dict)  # shape-validated above
            status, body = deps.check(key_hash, certificate)
            result = body
            facts.append(render_check(status, body))
        if message:
            facts.extend(_intent_facts(deps, key_hash, message))
    except Exception:  # noqa: BLE001 — the honesty path is the design
        return 200, {
            "facts": [UNREACHABLE_FACT],
            "result": None,
            "explanation": None,
            "degraded": False,
            "service_error": True,
        }

    explanation: str | None = None
    degraded = False
    if message:
        # The model is invoked only when the user actually converses;
        # a bare action turn costs no model call.
        try:
            explanation = deps.model_chat(build_messages(facts, turn.get("history"), message))
        except ModelUnavailableError:
            degraded = True
    out: dict[str, Any] = {
        "facts": facts,
        "result": result,
        "explanation": explanation,
        "degraded": degraded,
    }
    if job_id:
        out["job_id"] = job_id
    return 200, out


# ─── browser CORS (path- and origin-scoped, pure ASGI) ──────────────

BROWSER_PATH_PREFIXES = ("/verify", "/check", "/revoked", "/shell")
_CORS_METHODS = "GET, POST, OPTIONS"
_CORS_HEADERS = "content-type, x-api-key, authorization"


def browser_origins() -> set[str]:
    raw = _env("AXIOMCODE_SHELL_ORIGINS", "https://axiom-code.com")
    return {o.strip() for o in raw.split(",") if o.strip()}


def _browser_path(path: str) -> bool:
    return any(path == p or path.startswith(p + "/") for p in BROWSER_PATH_PREFIXES)


class BrowserCorsMiddleware:
    """Answers CORS preflights and decorates responses ONLY on the
    browser-facing paths and ONLY for allowlisted origins (the
    site's own). Everything else passes through untouched, so
    non-browser clients — curl, agents, the MCP leg — see the API
    exactly as before. CORS changes no authentication: it lets a
    browser READ a response when the caller already holds a key."""

    def __init__(self, app: Any, origins: set[str] | None = None) -> None:
        self.app = app
        self.origins = origins if origins is not None else browser_origins()

    async def __call__(self, scope: dict, receive: Callable, send: Callable) -> None:
        if scope.get("type") != "http" or not _browser_path(str(scope.get("path", ""))):
            await self.app(scope, receive, send)
            return
        headers = {k.decode().lower(): v.decode() for k, v in scope.get("headers", [])}
        origin = headers.get("origin", "")
        if origin not in self.origins:
            await self.app(scope, receive, send)
            return
        if scope.get("method") == "OPTIONS" and "access-control-request-method" in headers:
            await send(
                {
                    "type": "http.response.start",
                    "status": 200,
                    "headers": [
                        (b"access-control-allow-origin", origin.encode()),
                        (b"access-control-allow-methods", _CORS_METHODS.encode()),
                        (b"access-control-allow-headers", _CORS_HEADERS.encode()),
                        (b"access-control-max-age", b"600"),
                        (b"vary", b"Origin"),
                    ],
                }
            )
            await send({"type": "http.response.body", "body": b""})
            return

        async def send_with_cors(message: dict) -> None:
            if message.get("type") == "http.response.start":
                hdrs = list(message.get("headers", []))
                hdrs.append((b"access-control-allow-origin", origin.encode()))
                hdrs.append((b"vary", b"Origin"))
                message = {**message, "headers": hdrs}
            await send(message)

        await self.app(scope, receive, send_with_cors)
