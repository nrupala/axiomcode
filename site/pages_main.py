from build import *

# ---------- landing ----------
ORG_JSONLD = {
    "@context": "https://schema.org",
    "@type": "Organization",
    "name": "AxiomCode",
    "url": SITE,
    "description": "The certification authority for software correctness. Machine-checked proofs, signed certificates, independently verifiable.",
    "email": "hello@axiom-code.com",
}

page("/", "Software correctness, certified",
     "AxiomCode is the certification authority for software correctness. Submit a specification, get a machine-checked proof and a signed certificate anyone can verify.",
f"""<div class="hero"><div class="wrap">
<h1>{HERO_LINE}</h1>
<p class="lede">{TAGLINE} Submit your specification. Our engine compiles it, checks the proof mechanically, and issues a signed certificate &mdash; binding your code hash, the verification result, and our identity &mdash; that anyone can re-check without trusting us.</p>
<div class="row">
<a class="btn btn-gold" href="/verify/">Verify something free</a>
<a class="btn btn-ghost" href="/how-it-works/">How it works</a>
</div>
<p class="trustline">10 free trial verifications &middot; no certificate until you pay &middot; certificates valid 90 days, revocable, publicly checkable</p>
</div></div>

<section class="block"><div class="wrap"><div class="prose">
<div class="kicker">The problem</div>
<h2>AI writes code. Nobody can prove it&rsquo;s right.</h2>
<p>Code review is opinion. Tests are samples. Audits are expensive snapshots. When software has to be <em>right</em> &mdash; money movement, access control, safety logic, smart contracts &mdash; &ldquo;looks good to me&rdquo; is not evidence. AxiomCode sells <strong>verification-as-evidence</strong>: a mechanical proof, checked by a real toolchain, sealed into a certificate you can hand to a regulator, a customer, or a counterparty.</p>
</div>
<div class="cards">
<div class="card"><span class="num">1</span><h3>Submit</h3><p>Send a Lean 4 specification through the web UI, the REST API, or the MCP server &mdash; the way your agent already talks to tools.</p></div>
<div class="card"><span class="num">2</span><h3>We check it mechanically</h3><p>The engine compiles your spec with the real Lean toolchain and checks the proof. Vacuous builds, <code class="inline">sorry</code>, <code class="inline">admit</code>, and broken proofs are rejected &mdash; loudly.</p></div>
<div class="card"><span class="num">3</span><h3>You get a certificate</h3><p>A signed certificate binding your artifact hash, the verdict, the toolchain, the issuer, and a validity window. Anyone can re-verify it without trusting us.</p></div>
</div>
</div></section>

<section class="block" style="background:var(--wash)"><div class="wrap"><div class="prose">
<div class="kicker">The guarantee</div>
<h2>Our honesty is structural, not promised.</h2>
<p>A certificate authority lives or dies on one thing: never saying &ldquo;verified&rdquo; when it isn&rsquo;t. So we built the incentives into the system:</p>
</div>
<div class="cards">
<div class="card"><h3>Mis-issuance is the existential risk</h3><p>Every certificate carries a serial number, issuer identity, and validity window. If our toolchain is ever wrong, we revoke &mdash; publicly, through a published revocation list. Like TLS, but for correctness.</p></div>
<div class="card"><h3>Expiry drives re-verification</h3><p>Certificates last 90 days. Software changes; proofs should be re-run. Renewal is the business model, the same way TLS renewal is.</p></div>
<div class="card"><h3>You don&rsquo;t have to trust us</h3><p>The certificate binds the artifact hash and the proof transcript. Re-run the check yourself with the published toolchain. &ldquo;Don&rsquo;t trust our AI &mdash; verify our proof&rdquo; isn&rsquo;t a slogan; it&rsquo;s the architecture.</p></div>
</div>
</div></section>

<section class="block"><div class="wrap"><div class="prose">
<div class="kicker">Who it&rsquo;s for</div>
<h2>Whoever has to <em>prove</em> it&rsquo;s correct.</h2>
<p>The buyer isn&rsquo;t whoever writes the code. It&rsquo;s whoever must demonstrate correctness to a third party:</p>
<ul>
<li><strong>Regulated software teams</strong> &mdash; hand a certificate to the auditor instead of a test report.</li>
<li><strong>Fintech &amp; smart contracts</strong> &mdash; money logic with a machine-checked proof attached.</li>
<li><strong>AI agent builders</strong> &mdash; agents that ship code can now ship the proof too. Call us from your agent over MCP.</li>
<li><strong>Procurement &amp; contracts</strong> &mdash; &ldquo;certified correct&rdquo; as a deliverable, checkable by the buyer.</li>
</ul>
<p><a class="cta" href="/pricing/">See pricing</a></p>
</div></div></section>

<section class="block" style="background:var(--wash)"><div class="wrap"><div class="prose">
<div class="kicker">Honest scope</div>
<h2>What we certify today &mdash; and what we don&rsquo;t.</h2>
<p>Today the engine verifies <strong>Lean 4 specifications</strong>: it compiles the artifact you submit and checks the proof the toolchain actually ran. The certificate says exactly what was checked &mdash; the artifact hash, the toolchain version, the verdict &mdash; and nothing more. We do not claim your whole system is correct, your spec matches your intent, or your deployment matches the artifact. Read the <a href="/paperwork/certificate-policy/">Certificate Policy</a> for the precise meaning of every field.</p>
<div class="note">Verification is evidence, not opinion. The evidence is bounded, and we publish the bounds.</div>
</div></div></section>
""", ORG_JSONLD)

# ---------- how it works ----------
page("/how-it-works/", "How it works",
     "How AxiomCode verification works: submit a Lean 4 specification, the engine compiles and checks the proof, and you receive a signed, revocable, independently verifiable certificate.",
"""<section class="block"><div class="wrap"><div class="prose">
<h1 class="pt">How it works</h1>
<p class="sub">Three steps. Every one of them checkable.</p>

<h2>1. Submit the artifact</h2>
<p>Paste Lean 4 code into the <a href="/verify/">web verifier</a>, <code class="inline">POST</code> it to the REST API, or call the <code class="inline">verify</code> tool on our MCP server. What you submit is hashed (SHA-256) the moment it arrives &mdash; that hash becomes part of the certificate, so the verdict can never drift away from the code it describes.</p>

<h2>2. The engine checks the proof &mdash; for real</h2>
<p>The verification engine runs the actual Lean toolchain (<code class="inline">lake build</code>) against your artifact in an isolated project. It is deliberately adversarial toward sloppy proofs:</p>
<ul>
<li><strong>Vacuous builds rejected.</strong> A target that compiles nothing is not a proof of anything.</li>
<li><strong><code class="inline">sorry</code> and <code class="inline">admit</code> rejected.</strong> Placeholders are not proofs.</li>
<li><strong>Broken proofs rejected.</strong> If the toolchain reports an error, the verdict is <span class="badge b-fail">FAILED</span>, with the log attached.</li>
<li><strong>Unfinished work reported honestly.</strong> Something that doesn&rsquo;t compile yet gets <span class="badge b-warn">INCOMPLETE</span> &mdash; never a pass.</li>
</ul>
<p>A pass means one thing: the toolchain compiled your artifact and the proof checked. The full transcript ships with the verdict.</p>

<h2>3. The certificate seals the evidence</h2>
<p>On <span class="badge b-pass">PASSED</span>, the certification authority issues a signed certificate containing:</p>
<table class="spec">
<tr><th>Field</th><th>Meaning</th></tr>
<tr><td><code class="inline">artifact_sha256</code></td><td>Hash of exactly the code that was checked</td></tr>
<tr><td><code class="inline">verdict</code></td><td>PASSED, with the toolchain transcript reference</td></tr>
<tr><td><code class="inline">toolchain</code></td><td>Lean / lake versions that ran the check</td></tr>
<tr><td><code class="inline">issuer</code></td><td>AxiomCode CA</td></tr>
<tr><td><code class="inline">serial</code></td><td>Unique serial number</td></tr>
<tr><td><code class="inline">validity</code></td><td>90-day window (notBefore / notAfter)</td></tr>
<tr><td><code class="inline">signature</code></td><td>CA signature over all of the above</td></tr>
</table>
<div class="sealbox">
<p style="margin-top:0"><strong>Check any certificate, no account needed:</strong> paste it into the <a href="/check/">certificate checker</a>. You&rsquo;ll get <span class="badge b-pass">VALID</span>, <span class="badge b-fail">REVOKED</span>, or <span class="badge b-warn">EXPIRED</span> &mdash; with the reason. Revocation is published, not hidden: if a toolchain bug ever invalidates a verdict, the serial goes on the public revocation list.</p>
</div>

<h2>Interfaces</h2>
<ul>
<li><strong>Humans:</strong> the <a href="/verify/">web verifier</a> and <a href="/check/">certificate checker</a>.</li>
<li><strong>Applications:</strong> the <a href="/docs/api/">REST API</a> with API-key auth and metering.</li>
<li><strong>Agents:</strong> the <a href="/docs/api/">MCP server</a> &mdash; <code class="inline">verify</code>, <code class="inline">check_certificate</code>, <code class="inline">pricing</code>, <code class="inline">usage_report</code>. Plus <a href="/llms.txt">llms.txt</a> and <a href="/.well-known/axiomcode.json">machine-readable service info</a>.</li>
</ul>
</div></div></section>
""")

# ---------- pricing ----------
PRODUCT_JSONLD = {
    "@context": "https://schema.org",
    "@type": "Product",
    "name": "AxiomCode verification credits",
    "description": "Credits for machine-checked software verification with signed certificates. 1 credit = US$0.01.",
    "brand": {"@type": "Brand", "name": "AxiomCode"},
    "offers": [
        {"@type": "Offer", "name": "Trial", "price": "0", "priceCurrency": "USD",
         "description": "10 free verifications. Verdicts only, no certificates."},
        {"@type": "Offer", "name": "Starter", "price": "10", "priceCurrency": "USD",
         "description": "1,000 credits. Certificates included."},
        {"@type": "Offer", "name": "Growth", "price": "50", "priceCurrency": "USD",
         "description": "5,000 credits. Certificates included."},
        {"@type": "Offer", "name": "Scale", "price": "200", "priceCurrency": "USD",
         "description": "20,000 credits. Certificates included."},
    ],
}

page("/pricing/", "Pricing",
     "AxiomCode pricing: 10 free trial verifications (no certificates), then credit packs. 1 credit = $0.01. Certificates are issued to paying customers only.",
"""<section class="block"><div class="wrap"><div class="prose">
<h1 class="pt">Pricing</h1>
<p class="sub">The trial proves the engine. The certificate is the product.</p>
<div class="note">Our pricing covers the full cost of running the service &mdash; infrastructure, compute, operations, support, and insurance &mdash; plus a standard margin. One credit is always <strong>US$0.01</strong>. Verification consumes credits by compute time; the certificate itself is included with every paid verification.</div>
</div>
<div class="ptable">
<div class="plan">
<h3>Trial</h3><div class="price">$0</div><div class="per">no card required</div>
<ul>
<li>10 verifications</li>
<li>Full verdict + proof transcript</li>
<li><strong>No certificates</strong> &mdash; trial verdicts are not certifiable</li>
<li>Rate-limited, fair use</li>
</ul>
<p><a class="cta" href="/verify/">Start verifying</a></p>
</div>
<div class="plan">
<h3>Starter</h3><div class="price">$10</div><div class="per">1,000 credits, never expire</div>
<ul>
<li>Roughly 30&ndash;100 typical verifications</li>
<li><strong>Signed certificates</strong> on every pass</li>
<li>REST API + API key</li>
<li>Certificate checker + revocation list</li>
</ul>
<p><button class="cta paddle-buy" data-pack="starter" style="border:0;cursor:pointer">Buy Starter</button></p>
</div>
<div class="plan hot">
<h3>Growth</h3><div class="price">$50</div><div class="per">5,000 credits, never expire</div>
<ul>
<li>Roughly 150&ndash;500 typical verifications</li>
<li><strong>Signed certificates</strong> on every pass</li>
<li>REST API + MCP server access</li>
<li>Usage reports &amp; audit log</li>
</ul>
<p><button class="cta paddle-buy" data-pack="growth" style="border:0;cursor:pointer">Buy Growth</button></p>
</div>
<div class="plan">
<h3>Scale</h3><div class="price">$200</div><div class="per">20,000 credits, never expire</div>
<ul>
<li>Roughly 600&ndash;2,000 typical verifications</li>
<li><strong>Signed certificates</strong> on every pass</li>
<li>Everything in Growth</li>
<li>Priority verification queue</li>
</ul>
<p><button class="cta paddle-buy" data-pack="scale" style="border:0;cursor:pointer">Buy Scale</button></p>
</div>
</div>
<div class="wrap"><div class="prose" style="margin-top:36px">
<h2>How metering works</h2>
<p>Each verification is metered by compute time at <strong>0.9 credits/second</strong> (about $0.009/s). A small spec that checks in 12 seconds costs ~11 credits &mdash; eleven cents. You see the exact charge with every verdict, and your <a href="/docs/api/">usage report</a> itemizes all of it. Credits never expire. Unused credits are refundable within 14 days &mdash; see the <a href="/paperwork/refunds/">Refund Policy</a>.</p>
<h2>Why the trial has no certificates</h2>
<p>The trial exists so you can evaluate the engine: real verdicts, real transcripts, real evidence. But a certificate is a trust instrument &mdash; it says AxiomCode stakes its name on this verdict. We only stake our name in a commercial relationship, where the full cost of standing behind the verdict is covered. That boundary is what keeps the certificates meaningful.</p>
<div class="faq">
<details><summary>What counts as a &ldquo;typical verification&rdquo;?</summary><p>A Lean 4 spec that compiles and checks in 10&ndash;60 seconds of engine time. Very large developments cost proportionally more; the meter is compute time, so you always pay for what you used.</p></details>
<details><summary>Do certificates really expire?</summary><p>Yes &mdash; 90 days, like TLS. Software changes and toolchains move on; re-verification keeps the evidence fresh. Renewal pricing is the same credit meter.</p></details>
<details><summary>What if a certificate was wrongly issued?</summary><p>We revoke it publicly and say so. Mis-issuance handling is documented in the <a href="/paperwork/certificate-policy/">Certificate Policy</a> &mdash; it&rsquo;s the core of the trust model.</p></details>
</div>
</div></div>
</section>
<script src="https://cdn.paddle.com/paddle/v2/paddle.js"></script>
<script>
var PRICE_IDS = %s;
if (window.Paddle && %d) { Paddle.Setup({vendor: %d}); }
document.querySelectorAll('.paddle-buy').forEach(function(b){
  b.addEventListener('click', function(){
    var pid = PRICE_IDS[b.getAttribute('data-pack')];
    if (!pid || !window.Paddle) { alert('Checkout opens when products are live. Email hello@axiom-code.com and we will set you up.'); return; }
    Paddle.Checkout.open({items:[{priceId: pid, quantity: 1}]});
  });
});
</script>
""" % (json.dumps(PRICE_IDS), PADDLE_VENDOR, PADDLE_VENDOR), PRODUCT_JSONLD)
