import status_data
from build import SITE, page

# ---------- blog ----------
page(
    "/blog/",
    "Blog",
    "The AxiomCode blog: verification-as-evidence, certification practice, and honest notes on building a CA for software correctness.",
    """<section class="block"><div class="wrap"><div class="prose">
<h1 class="pt">Blog</h1>
<p class="sub">Notes on verification-as-evidence and building a certification authority for software.</p>
<div class="card" style="margin-top:24px">
<div class="kicker">26 September 2026</div>
<h3 style="margin-top:0"><a href="/blog/dont-trust-our-ai/">Don&rsquo;t trust our AI &mdash; verify our proof</a></h3>
<p>Why we built a certification authority for software correctness, why the trial gives you everything except the certificate, and why mis-issuance &mdash; saying &ldquo;verified&rdquo; when it isn&rsquo;t &mdash; is the one risk we organize the whole company around.</p>
</div>
</div></div></section>
""",
)

page(
    "/blog/dont-trust-our-ai/",
    "Don\u2019t trust our AI \u2014 verify our proof",
    "Launch essay: why AxiomCode is a certification authority for software correctness, why verification-as-evidence beats verification-as-opinion, and why the certificate is never free.",
    """<section class="block"><div class="wrap"><div class="prose">
<div class="kicker">26 September 2026 &middot; Launch</div>
<h1 class="pt">Don&rsquo;t trust our AI &mdash; verify our proof</h1>
<p class="sub">Why we built a certification authority for software correctness.</p>
<div class="note"><strong>Status note, 12 November 2026:</strong> this article was written before the public opening (9 November 2026), and product facts in it have since changed. Current service status lives on the <a href="/status/">status page</a>; every change since the opening is recorded in the <a href="/changelog/">changelog</a>.</div>

<p>AI writes code now. A lot of it. And the industry&rsquo;s answer to &ldquo;is it right?&rdquo; is still, essentially, vibes: code review (opinion), tests (samples), audits (expensive snapshots). All useful. None of them evidence.</p>

<p>We started AxiomCode with a different premise: <strong>correctness should be certifiable the way identity is.</strong> When you visit your bank, you don&rsquo;t read the bank&rsquo;s audit report &mdash; your browser checks a certificate issued by an authority whose entire business is not lying about identity. Software needs the same thing for correctness: a party whose business is not lying about verification.</p>

<h2>Verification-as-evidence, not verification-as-opinion</h2>
<p>An AI code reviewer gives you an opinion. AxiomCode gives you evidence: the artifact hash, the toolchain that ran, the transcript of the check, sealed under our signature. You don&rsquo;t have to believe us &mdash; or our AI. Re-run the check yourself. The certificate tells you exactly what was verified and how.</p>

<h2>The trial gives you everything except the certificate</h2>
<p>Try us free: 10 verifications, real verdicts, real transcripts. But no certificates. That isn&rsquo;t stinginess &mdash; it&rsquo;s the business model working as designed. A certificate says <em>we stake our name on this verdict</em>. Staking our name costs real money: the compute, the operations, the insurance, the revocation infrastructure, the people who answer when something goes wrong. We only stake it inside a commercial relationship where those costs are covered. A free certificate would be a souvenir. Ours is a trust instrument.</p>

<h2>The one risk we organize around</h2>
<p>A certification authority has exactly one existential risk: <strong>mis-issuance</strong> &mdash; saying &ldquo;verified&rdquo; when it isn&rsquo;t. Everything about the design flows from that: the engine rejects <code class="inline">sorry</code>, <code class="inline">admit</code>, vacuous builds, and broken proofs loudly. Certificates expire in 90 days so evidence stays fresh. And if our toolchain is ever wrong, we revoke publicly &mdash; there is no silent un-verification. Like TLS, but for correctness.</p>

<h2>Who it&rsquo;s for</h2>
<p>Whoever has to <em>prove</em> correctness to a third party: regulated teams facing auditors, fintech and smart-contract builders moving money, agent builders whose agents ship code, procurement teams who want &ldquo;certified correct&rdquo; as a deliverable. If you&rsquo;re that person, <a href="/verify/">run your first verification free</a>. Don&rsquo;t trust our AI &mdash; verify our proof.</p>
</div></div></section>
""",
    {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": "Don\u2019t trust our AI \u2014 verify our proof",
        "datePublished": "2026-09-26",
        "author": {"@type": "Organization", "name": "AxiomCode"},
    },
)

# ---------- machine-readable extras (written by runner) ----------
WELLKNOWN = {
    "service": "AxiomCode",
    "status": "live",
    "description": "Certification authority for software correctness. Machine-checked proofs, signed certificates.",
    "note": "Live since 2026-11-09: the API at https://api.axiom-code.com is open (POST /verify, POST /check, GET /verify/jobs/{job_id}); the revocation list (GET /revoked) and CA public keys (GET /.well-known/axiomcode-keys.json) are public. The first 10 verification cases per API key are a free trial (no certificates). Credit packs are not yet on sale: billing is paused under the owner's readiness-arming rule, with the Stripe webhook and Payment Links deactivated until pack sales open. A hosted MCP endpoint is live at https://api.axiom-code.com/mcp/ (the same API key, the same queue, seven tools: verify, job_status, check_certificate, revoked, health, usage_report, pricing); the MCP server also ships in the repository for local use.",
    "homepage": SITE,
    "llms_txt": SITE + "/llms.txt",
    "docs": SITE + "/docs/api/",
    "api_base": "https://api.axiom-code.com",
    "revocation_list": "https://api.axiom-code.com/revoked",
    "ca_public_keys": "https://api.axiom-code.com/.well-known/axiomcode-keys.json",
    "certificate_checker": SITE + "/check/",
    "pricing": SITE + "/pricing/",
    "trial": {"verifications_per_api_key": 10, "certificates": False},
    "billing": "paused — credit packs not yet on sale",
    "contact": "hello@axiom-code.com",
}

# Status section — generated from the canonical status source (status_data.py).
WELLKNOWN["status_page"] = SITE + "/status/"
WELLKNOWN["status_json"] = SITE + "/status.json"
WELLKNOWN["changelog"] = SITE + "/changelog/"
WELLKNOWN["practice"] = SITE + "/practice/"
WELLKNOWN["status_as_of"] = status_data.STATUS_META["as_of"]
WELLKNOWN["surfaces"] = status_data.wellknown_surfaces()

_LLMS_HEAD = """# AxiomCode

> The certification authority for software correctness. Don't trust our AI — verify our proof.

AxiomCode verifies Lean 4 software specifications with a real toolchain and issues
signed, revocable, independently verifiable certificates binding the artifact hash,
verdict, toolchain, issuer, serial, and validity window.

"""

_LLMS_TAIL = """## For agents

- API docs: https://axiom-code.com/docs/api/
- Machine-readable service info: https://axiom-code.com/.well-known/axiomcode.json
- Status (human): https://axiom-code.com/status/
- Status (machine): https://axiom-code.com/status.json
- Changelog & service record: https://axiom-code.com/changelog/
- Practice (gates, soak, certificates, error reporting): https://axiom-code.com/practice/
- REST base (live): https://api.axiom-code.com
- Verify: POST /verify with an API key (X-Api-Key header), body {"code": "..."}.
  When every proof slot is busy the answer is 202 {"status":"queued","job_id":...,
  "position":N}; poll GET /verify/jobs/{job_id} with the same key for the result.
- Check a certificate: POST /check with an API key, body {"certificate": {...}}.
- Revocation list (public, no auth): GET /revoked
- CA public keys (public, no auth): GET /.well-known/axiomcode-keys.json
- MCP: a hosted endpoint is live at https://api.axiom-code.com/mcp/ (the same
  API key, the same queue; tools: verify, job_status, check_certificate,
  revoked, health, usage_report, pricing). A server also ships in the
  AxiomCode repository (github.com/nrupala/axiomcode) for local use.

## Trial

The first 10 verification cases per API key are free: POST /verify with a new key.
Trial verdicts include the verdict and the usage record but NEVER a certificate.
Certificates are issued to paying customers only (credit packs from $10 when sales
open; 1 credit = $0.01; metered at 0.9 credits/sec of engine compute time). API keys
are issued on request: hello@axiom-code.com.

## Scope (honest)

Today: Lean 4 only. A PASSED verdict means the submitted artifact compiled under the
stated toolchain and its proofs checked. It does not certify intent, deployment, or
the rest of the system. Certificates are valid 90 days and revocable. Mis-issuance
is handled by public revocation — see the Certificate Policy.

## Paperwork

- Terms: https://axiom-code.com/paperwork/terms/
- Privacy: https://axiom-code.com/paperwork/privacy/
- Certificate Policy & CPS: https://axiom-code.com/paperwork/certificate-policy/
- Refunds: https://axiom-code.com/paperwork/refunds/
- Security & disclosure: https://axiom-code.com/paperwork/security/
"""

# llms.txt = static head + generated status section + static tail.
LLMS_TXT = _LLMS_HEAD + status_data.llms_status_section() + "\n" + _LLMS_TAIL

# ---------- release log ----------
# Moved to pages_status.py (P1): /releases/ is now an alias of /changelog/,
# whose entries are migrated in changelog_data.py.
