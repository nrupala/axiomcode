from build import *

# ---------- blog ----------
page("/blog/", "Blog",
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
""")

page("/blog/dont-trust-our-ai/", "Don\u2019t trust our AI \u2014 verify our proof",
     "Launch essay: why AxiomCode is a certification authority for software correctness, why verification-as-evidence beats verification-as-opinion, and why the certificate is never free.",
"""<section class="block"><div class="wrap"><div class="prose">
<div class="kicker">26 September 2026 &middot; Launch</div>
<h1 class="pt">Don&rsquo;t trust our AI &mdash; verify our proof</h1>
<p class="sub">Why we built a certification authority for software correctness.</p>

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
})

# ---------- machine-readable extras (written by runner) ----------
WELLKNOWN = {
    "service": "AxiomCode",
    "description": "Certification authority for software correctness. Machine-checked proofs, signed certificates.",
    "homepage": SITE,
    "api_base": API_BASE,
    "mcp": API_BASE + "/mcp",
    "llms_txt": SITE + "/llms.txt",
    "docs": SITE + "/docs/api/",
    "certificate_checker": SITE + "/check/",
    "revocation_list": API_BASE + "/v1/revoked",
    "ca_public_keys": SITE + "/.well-known/axiomcode-keys.json",
    "pricing": SITE + "/pricing/",
    "trial": {"verifications": 10, "certificates": False},
    "contact": "hello@axiom-code.com",
}

LLMS_TXT = """# AxiomCode

> The certification authority for software correctness. Don't trust our AI — verify our proof.

AxiomCode verifies Lean 4 software specifications with a real toolchain and issues
signed, revocable, independently verifiable certificates binding the artifact hash,
verdict, toolchain, issuer, serial, and validity window.

## For agents

- API docs: https://axiom-code.com/docs/api/
- Machine-readable service info: https://axiom-code.com/.well-known/axiomcode.json
- REST base: https://api.axiom-code.com
- MCP server: https://api.axiom-code.com/mcp with tools: verify, check_certificate, pricing, usage_report
- Check any certificate (no auth): GET https://api.axiom-code.com/v1/check?serial=...
- Revocation list: https://api.axiom-code.com/v1/revoked

## Trial

10 free verifications per email via POST /v1/trial/verify. Trial verdicts include the
verdict and transcript but NEVER a certificate. Certificates are issued to paying
customers only (credit packs from $10; 1 credit = $0.01; metered at 0.9 credits/sec
of engine compute time).

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
