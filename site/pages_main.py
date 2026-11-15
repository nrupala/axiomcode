import datetime

import status_data
from build import HERO_LINE, SITE, page

_AV_CLASS = {"live": "av-live", "paused": "av-paused", "unavailable": "av-unavail"}
_LC_CLASS = {
    "live": "lc-live",
    "paused": "lc-paused",
    "in_soak": "lc-soak",
    "in_design": "lc-design",
    "not_built": "lc-notbuilt",
}


def _surf(sid):
    return next(s for s in status_data.SURFACES if s["surface_id"] == sid)


def _chips(key):
    """Availability + lifecycle chips for a surface, from the canonical source."""
    s = _surf(key)
    av = status_data.AVAILABILITY_LABELS[s["availability"]]
    lc = status_data.LIFECYCLE_LABELS[s["lifecycle"]]
    return (
        f'<span class="chip {_AV_CLASS[s["availability"]]}">{av}</span> '
        f'<span class="chip {_LC_CLASS[s["lifecycle"]]}">{lc}</span>'
    )


def _grad_line(key):
    s = _surf(key)
    d = s.get("graduates_on")
    if not d:
        return ""
    when = datetime.date.fromisoformat(d).strftime("%d %B %Y")
    return f' Gate graduation judged {when}, per <a href="/practice/">practice</a>.'


def _statusline():
    rest = _surf("rest_api")
    billing = _surf("billing")
    return (
        '<div class="statusline"><span>Service state</span>'
        f'<span class="chip {_AV_CLASS[rest["availability"]]}">REST API · '
        f"{status_data.AVAILABILITY_LABELS[rest['availability']]}</span>"
        f'<span class="chip {_LC_CLASS[rest["lifecycle"]]}">'
        f"{status_data.LIFECYCLE_LABELS[rest['lifecycle']]}</span>"
        f'<span class="chip {_AV_CLASS[billing["availability"]]}">Billing · '
        f"{status_data.AVAILABILITY_LABELS[billing['availability']]}</span>"
        "<span>Credit packs not yet on sale · API keys by email: "
        '<a href="mailto:hello@axiom-code.com" style="color:#cbd5e1">hello@axiom-code.com</a></span></div>'
    )


def _offer_cards():
    """Pricing strip rendered from the canonical offers (the pricing JSON-LD)."""
    cards = []
    for offer in PRODUCT_JSONLD["offers"]:
        name = offer["name"]
        first = offer["description"].split(".")[0]
        if offer["price"] == "0":
            cards.append(
                f"""<div class="plan"><h3>{name}</h3><div class="price">Free</div>
<div class="per">{first}</div>
<ul><li>Real verdicts and usage records</li><li>Full artefact loop, REST or MCP</li>
<li><strong>No certificate</strong> — the trial proves the engine, not your artefact</li></ul>
<a class="buy live" href="/verify/" style="cursor:pointer">Run the trial</a></div>"""
            )
        else:
            cards.append(
                f"""<div class="plan"><h3>{name}</h3><div class="price">${float(offer["price"]):,.0f}</div>
<div class="per">{first} · metered at 0.9 credits/sec</div>
<ul><li>Signed certificates on paid verifications</li><li>Same engine, same queue as the trial</li></ul>
<span class="buy">Not yet on sale</span></div>"""
            )
    return "\n".join(cards)


PRODUCT_JSONLD = {
    "@context": "https://schema.org",
    "@type": "Product",
    "name": "AxiomCode verification credits",
    "description": "Credits for machine-checked software verification with signed certificates. 1 credit = US$0.01.",
    "brand": {"@type": "Brand", "name": "AxiomCode"},
    "offers": [
        {
            "@type": "Offer",
            "name": "Trial",
            "price": "0",
            "priceCurrency": "USD",
            "availability": "https://schema.org/InStock",
            "description": "10 free verifications. Verdicts only, no certificates.",
        },
        {
            "@type": "Offer",
            "name": "Starter",
            "price": "10",
            "priceCurrency": "USD",
            "availability": "https://schema.org/OutOfStock",
            "description": "1,000 credits. Certificates included. Not yet on sale: billing is paused.",
        },
        {
            "@type": "Offer",
            "name": "Growth",
            "price": "50",
            "priceCurrency": "USD",
            "availability": "https://schema.org/OutOfStock",
            "description": "5,000 credits. Certificates included. Not yet on sale: billing is paused.",
        },
        {
            "@type": "Offer",
            "name": "Scale",
            "price": "200",
            "priceCurrency": "USD",
            "availability": "https://schema.org/OutOfStock",
            "description": "20,000 credits. Certificates included. Not yet on sale: billing is paused.",
        },
    ],
}


# ---------- landing ----------
ORG_JSONLD = {
    "@context": "https://schema.org",
    "@type": "Organization",
    "name": "AxiomCode",
    "url": SITE,
    "description": "The certification authority for software correctness. Machine-checked proofs, signed certificates, independently verifiable.",
    "email": "hello@axiom-code.com",
}

page(
    "/",
    "Certification Authority for Software Correctness",
    "AxiomCode verifies Lean 4 artefacts with a real toolchain and issues signed, revocable certificates. REST API and hosted MCP live; the trial is free — verdicts yes, certificates no.",
    f"""<section class="hero"><div class="wrap">
<div class="kicker">Certification authority for software correctness</div>
<h1>Verification as evidence, not verification as opinion.</h1>
<p class="lede">AxiomCode checks Lean 4 artefacts with a real toolchain — the Lean kernel is the only judge — and issues signed, revocable certificates that bind the artefact hash, the verdict, and the toolchain. {HERO_LINE}</p>
<p class="scope-line">Scope, stated at the point of claim: Lean 4 artefacts only, today. A PASSED verdict means the artefact&rsquo;s proofs checked under the stated toolchain — not that the software does what you intended. <a href="/docs/explanation/what-it-does-not-prove/" style="color:#cbd5e1">What verification does not prove</a>.</p>
<div class="row"><a class="btn btn-gold" href="/verify/">Run your first verification</a>
<a class="btn btn-ghost" href="/docs/">Read the docs</a></div>
{_statusline()}
<div class="trustline">Certificates bind artefact hash &middot; verdict &middot; toolchain &middot; issuer &middot; serial &middot; 90-day validity — independently checkable, publicly revocable.</div>
</div></section>

<section class="block alt"><div class="wrap">
<div class="kicker">One engine, three doors</div>
<h2>Same verdicts, same queue, same trial</h2>
<p style="color:var(--mut);max-width:44em">Every door reaches the same verification engine and the same certificate authority. Availability and lifecycle are stated separately on every surface — a surface can be live to use and still in its post-release soak.</p>
<div class="cards">
<div class="card cardflex"><div class="chips">{_chips("rest_api")}</div>
<h3>REST API</h3>
<p><code class="inline">POST /verify</code> with your API key; long runs queue and are polled at <code class="inline">GET /verify/jobs/{{id}}</code>.{_grad_line("rest_api")}</p>
<p class="go"><a href="/docs/api/">API reference &rarr;</a></p></div>
<div class="card cardflex"><div class="chips">{_chips("hosted_mcp")}</div>
<h3>Hosted MCP</h3>
<p>Seven tools at <code class="inline">/mcp/</code> for agent clients — same key, same queue, same trial semantics as REST.{_grad_line("hosted_mcp")}</p>
<p class="go"><a href="/docs/mcp/">MCP tools &rarr;</a></p></div>
<div class="card cardflex"><div class="chips">{_chips("ask_shell")}</div>
<h3>Ask AxiomCode</h3>
<p>A shell that orchestrates the same verify calls and explains the result. The facts are rendered in code; the model explains and never judges.{_grad_line("ask_shell")}</p>
<p class="go"><a href="/ask/">Open Ask &rarr;</a></p></div>
</div>
</div></section>

"""
    + """<section class="block" id="try"><div class="wrap">
<div class="kicker">Try it — live</div>
<h2>One loop: artefact in, evidence out</h2>
<p style="color:var(--mut);max-width:46em">This is the real service, not a recording. Paste <strong>your own API key</strong> and run the starter artefact, or replace it with your own Lean 4. The first 10 cases on a key are the trial: real verdicts and usage records, no certificate.</p>
<div class="loop">
<div class="pane"><h3>1 · Artefact in</h3><div class="body">
<label class="fl" for="hkey" style="margin-top:0">Your API key</label>
<input type="password" id="hkey" placeholder="axk_&hellip;" autocomplete="off">
<label class="fl" for="hcode">Lean 4 artefact</label>
<textarea class="codebox" id="hcode" style="min-height:140px" spellcheck="false">theorem add_comm_nat (a b : Nat) : a + b = b + a := Nat.add_comm a b</textarea>
<div style="margin-top:16px"><button class="go" id="hgo" type="button">Verify it &rarr;</button></div>
<p style="font-size:13.5px;color:var(--faint);margin:12px 0 0">Your key goes only to <code class="inline">api.axiom-code.com</code>, over HTTPS; this page never stores it. No key yet? <a href="mailto:hello@axiom-code.com?subject=API%20key%20request">Request one by email</a> — keys are free. Prefer the dedicated page? The same loop runs at <a href="/verify/">/verify/</a>.</p>
</div></div>
<div class="arrow" aria-hidden="true">&rarr;</div>
<div class="pane"><h3>2 · Evidence out</h3><div class="body" id="hresult" aria-live="polite">
<p style="color:var(--mut);margin:0">The verdict appears here — <strong>PASSED</strong> or <strong>FAILED</strong>, decided by the Lean kernel, with the artefact hash and the usage record. A run that ends before a verdict (payment required, timeout, refusal, failed queued job) is a <strong>NO VERDICT</strong> error outcome, never a verdict. On the trial, no certificate is attached — by design.</p>
</div></div>
</div>
<p style="color:var(--mut);font-size:15px;margin-top:18px">Driving an agent instead? The same call is one POST over <a href="/docs/api/">REST</a>, or seven tools over <a href="/docs/mcp/">hosted MCP</a>. First time here: the <a href="/docs/start/first-verification/">first-verification tutorial</a> walks the whole loop.</p>
</div></section>
<script>
const HAPI='https://api.axiom-code.com';
const h$ = id => document.getElementById(id);
function hesc(s){return String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
function hkv(k,v,plain){return '<dt>'+k+'</dt><dd'+(plain?' class="plain"':'')+'>'+v+'</dd>';}
function hShow(j){
  const ok = j.verified === true;
  let h = '<span class="badge '+(ok?'b-pass':'b-fail')+'">'+(ok?'PASSED':'FAILED')+'</span>';
  h += '<dl class="kv">';
  if (j.artifact_hash) h += hkv('Artefact (SHA-256)', hesc(j.artifact_hash));
  if (Array.isArray(j.attempts) && j.attempts.length){
    let secs=0, cred=0, seen=false;
    j.attempts.forEach(a=>{ if(typeof a.elapsed_seconds==='number'){secs+=a.elapsed_seconds;seen=true;} if(typeof a.credits_charged==='number'){cred+=a.credits_charged;} });
    if (seen) h += hkv('Engine time', secs.toFixed(2)+' s');
    h += hkv('Credits charged', String(Math.round(cred*100)/100));
  }
  if (j.trial) h += hkv('Trial', 'case '+j.trial.used+' of '+j.trial.limit+' — no certificate on the trial', true);
  if (j.job_id) h += hkv('Job', hesc(j.job_id));
  h += '</dl>';
  if (j.certificate){
    h += '<p style="margin:14px 0 6px"><strong>Signed certificate issued.</strong> Check it independently at <a href="/check/">/check/</a>.</p><pre class="code">'+hesc(JSON.stringify(j.certificate,null,2))+'</pre>';
  } else if (j.trial){
    h += '<p style="margin:14px 0 0;color:var(--mut)">Trial verdict — real verdict, real usage record, <strong>no certificate</strong>. Certificates are issued on paid verifications; packs are <a href="/pricing/">not yet on sale</a>.</p>';
  }
  h$('hresult').innerHTML = h;
}
function hErr(msg){ h$('hresult').innerHTML = '<span class="badge b-fail">NO VERDICT</span><p style="margin:12px 0 0">'+msg+'</p>'; }
async function hPoll(jobId, key){
  for (let i=0;i<40;i++){
    await new Promise(r=>setTimeout(r,3000));
    const r = await fetch(HAPI+'/verify/jobs/'+encodeURIComponent(jobId), {headers:{'X-Api-Key':key}});
    const j = await r.json().catch(()=>({}));
    if (r.status===200){ hShow(j); return; }
    if (r.status!==202){ hErr('The queued job ended without a verdict ('+r.status+'). Nothing was certified.'); return; }
    h$('hresult').innerHTML = '<span class="badge b-warn">QUEUED</span><p style="margin:12px 0 0">Still queued — position '+(j.position!=null?j.position:'…')+'. Polling every 3 seconds.</p>';
  }
  hErr('Still queued after two minutes. Poll <code class="inline">GET /verify/jobs/'+hesc(jobId)+'</code> with your key for the result.');
}
h$('hgo').addEventListener('click', async () => {
  const key = h$('hkey').value.trim(), code = h$('hcode').value;
  if (!key){ hErr('Paste your API key first — keys are free, by email: <a href="mailto:hello@axiom-code.com?subject=API%20key%20request">hello@axiom-code.com</a>. This loop runs on your own key; there is no shared demo key.'); return; }
  if (!code.trim()){ hErr('The artefact is empty — paste a Lean 4 artefact, or restore the starter example.'); return; }
  const btn = h$('hgo'); btn.disabled = true; btn.textContent = 'Verifying…';
  h$('hresult').innerHTML = '<p style="color:var(--mut);margin:0">Running the real toolchain…</p>';
  try {
    const r = await fetch(HAPI+'/verify', {method:'POST', headers:{'Content-Type':'application/json','X-Api-Key':key}, body: JSON.stringify({code})});
    const j = await r.json().catch(()=>({}));
    if (r.status===200){ hShow(j); }
    else if (r.status===202 && j.job_id){ h$('hresult').innerHTML = '<span class="badge b-warn">QUEUED</span><p style="margin:12px 0 0">Every proof slot is busy — job '+hesc(j.job_id)+' queued at position '+(j.position!=null?j.position:'…')+'. Polling…</p>'; hPoll(j.job_id, key); }
    else if (r.status===401){ hErr('That API key was not accepted (401). Check the key, or request a new one by email.'); }
    else if (r.status===402){ hErr('Payment required (402): this key is out of trial cases and has no credit balance. Packs are not yet on sale — see <a href="/pricing/">pricing</a>.'); }
    else if (r.status===413){ hErr('Artefact too large (413): the limit is 256 KB.'); }
    else if (r.status===429){ hErr('Rate limited (429): slow down and retry shortly.'); }
    else if (r.status===504){ hErr('The run timed out (504) — a NO VERDICT outcome: nothing was certified and trial cases are not consumed by timeouts.'); }
    else { hErr('The service answered '+r.status+' — a NO VERDICT outcome. Nothing was certified.'); }
  } catch(e){ hErr('Could not reach the API. Check your connection and retry — a NO VERDICT outcome; nothing was certified.'); }
  btn.disabled = false; btn.textContent = 'Verify it →';
});
</script>

"""
    + f"""<section class="block alt"><div class="wrap">
<div class="kicker">The seal</div>
<h2>What a certificate binds</h2>
<p style="color:var(--mut);max-width:44em">A certificate is a signed record, not a badge image. Anyone can check it — paste it into the <a href="/check/">public checker</a> and the signature, the validity window, and the revocation state are verified in your browser against our published CA keys.</p>
<div class="sealbox">
<pre class="code">{{
  "artifact_hash": "sha256:9f2c…e41a",
  "verified": true,
  "toolchain": "lean4-4.9.1 / axiomcode-0.3.0",
  "issuer": "AxiomCode CA",
  "serial": "AC-2026-000417",
  "issued": "2026-09-26", "expires": "2026-12-25",
  "signature": "ed25519:…"
}}</pre>
<div class="note" style="margin-bottom:0"><strong>Read the fields, not the logo.</strong> The hash binds the exact bytes that were checked; the toolchain names what checked them; the serial is how a certificate is revoked if the toolchain is ever found wrong. A certificate without these fields is a picture, not evidence.</div>
</div>
</div></section>

<section class="block"><div class="wrap">
<div class="kicker">Verdicts</div>
<h2>Two verdicts — and one non-verdict</h2>
<p style="color:var(--mut);max-width:44em">Verdicts are boolean. Anything that ends a run before a verdict exists is an error outcome with its own name, so a refusal can never be mistaken for a result.</p>
<div class="tablewrap"><table class="tax">
<tr><th style="width:16%">Outcome</th><th style="width:38%">What it means</th><th>Certificate?</th></tr>
<tr><td><span class="badge b-pass">PASSED</span></td><td>The artefact compiled and every proof checked under the stated toolchain.</td><td>Yes — on paid verifications. Trial runs return the verdict and usage record only.</td></tr>
<tr><td><span class="badge b-fail">FAILED</span></td><td>The artefact was checked and did not pass: a proof failed, or the artefact was rejected by the engine&rsquo;s rules.</td><td>Yes — on paid verifications. A FAILED certificate is evidence too: it records that the check ran and what it found.</td></tr>
<tr><td><span class="badge b-warn">NO VERDICT</span></td><td>No verdict exists: payment required (402), engine timeout (504), concurrency, rate, or size refusal, or a queued job that failed. The run ended before a verdict.</td><td>Never. Nothing was decided, so nothing is certified.</td></tr>
</table></div>
<p style="color:var(--mut);font-size:15px">The full taxonomy — every status code and what it does to your balance — is in the <a href="/docs/reference/verdicts-and-errors/">verdicts &amp; errors reference</a>.</p>
</div></section>

<section class="block alt"><div class="wrap">
<div class="kicker">Pricing</div>
<h2>Defined — and paused</h2>
<p style="color:var(--mut);max-width:44em">Metered at 0.9 credits per second of engine compute; 1 credit = $0.01. Credit packs are priced and published, and <strong>not yet on sale</strong>: billing stays paused until the service&rsquo;s pre-billing conditions close. The trial needs no card and no pack.</p>
<div class="ptable">
{_offer_cards()}
</div>
<p style="margin-top:18px"><a href="/pricing/">Full pricing — metering, refunds, and what a timeout costs &rarr;</a></p>
</div></section>

"""
    + """<section class="block"><div class="wrap"><div class="prose" style="max-width:76ch">
<div class="kicker">Questions</div>
<h2>Asked often</h2>
<div class="faq">
<details><summary>What exactly does a PASSED verdict claim?</summary><p>That the submitted artefact compiled under the stated Lean toolchain and its proofs checked — the kernel accepted them. It does not claim the specification says what you meant, that the deployed system matches the artefact, or anything about code that was not submitted. The bounds are stated on every certificate and in <a href="/docs/explanation/what-verification-proves/">what verification proves</a>.</p></details>
<details><summary>Why does the trial withhold the certificate?</summary><p>Because the certificate is the product: our signature staked on a verdict, with the revocation and record-keeping duties that follow. Trial runs give you the verdict and the usage record so you can judge the engine; the signature is issued inside a paid relationship.</p></details>
<details><summary>Can I check a certificate without an account?</summary><p>Yes. The <a href="/check/">checker</a> verifies the signature in your browser against the published CA keys, and the <a href="https://api.axiom-code.com/revoked">revocation list</a> is public. Checking never requires trust in this website.</p></details>
<details><summary>Which languages are supported?</summary><p>Lean 4, today. Smart-contract verification is in design and the offline verifier is not built — both are labelled as such on the <a href="/status/">status page</a>, not implied here.</p></details>
</div>
<div class="honest"><h3>Stated plainly</h3>
<p><strong>No external third-party audit of AxiomCode has been performed.</strong> The assurance case rests on the release gate, the soak, and the public record — read the <a href="/practice/">practice page</a> for exactly what that does and does not cover.</p>
<p>Found an error on this site or in the service? Report it on <a href="https://github.com/nrupala/axiomcode/issues">GitHub Issues</a> — user-initiated only; this site carries no telemetry and attaches nothing you did not choose to send.</p></div>
</div></div></section>
""",
    ORG_JSONLD,
)


# ---------- how it works ----------
page(
    "/how-it-works/",
    "How it works",
    "How AxiomCode verification works: submit a Lean 4 specification, the engine compiles and checks the proof, and you receive a signed, revocable, independently verifiable certificate.",
    """<section class="block"><div class="wrap"><div class="prose">
<h1 class="pt">How it works</h1>
<p class="sub">Three steps. Every one of them checkable.</p>

<h2>1. Submit the artifact</h2>
<p>Paste Lean 4 code into the <a href="/verify/">web verifier</a> or <code class="inline">POST</code> it to the REST API with your API key. What you submit is hashed (SHA-256) the moment it arrives &mdash; that hash becomes part of the certificate, so the verdict can never drift away from the code it describes. When every proof slot is busy, your submission joins a first-in-first-out queue and the response tells you your position &mdash; nobody jumps the line, and you can check your place at any time.</p>

<h2>2. The engine checks the proof &mdash; for real</h2>
<p>The verification engine runs the actual Lean toolchain (<code class="inline">lake build</code>) against your artifact in an isolated project. It is deliberately adversarial toward sloppy proofs:</p>
<ul>
<li><strong>Vacuous builds rejected.</strong> A target that compiles nothing is not a proof of anything.</li>
<li><strong><code class="inline">sorry</code> and <code class="inline">admit</code> rejected.</strong> Placeholders are not proofs.</li>
<li><strong>Broken proofs rejected.</strong> If the toolchain reports an error, the verdict is <span class="badge b-fail">FAILED</span>, with the log attached.</li>
<li><strong>Unfinished work reported honestly.</strong> A non-compiling or vacuous attempt that completes the proof run returns <span class="badge b-fail">FAILED</span> &mdash; never a pass. A request that ends before a verdict &mdash; payment required, a timeout, or a concurrency refusal &mdash; is reported as an error, not as a verdict.</li>
</ul>
<p>A pass means one thing: the toolchain compiled your artifact and the proof checked. The full transcript ships with the verdict.</p>

<h2>3. The certificate seals the evidence</h2>
<p>On <span class="badge b-pass">PASSED</span> &mdash; and on a FAILED paid verification too &mdash; the certification authority issues a signed certificate recording the verdict. The certificate credentials the code &mdash; our assessment that the artifact was built to its specification, as mechanically checked &mdash; and we hold no responsibility beyond this assessment. It contains:</p>
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
<p style="margin-top:0"><strong>Check any certificate:</strong> the revocation list and the CA&rsquo;s public keys are published openly, so anyone can validate a certificate offline against the published keys &mdash; no trust in our server required. With an API key, the <a href="/check/">certificate checker</a> does it in one call. You&rsquo;ll get <span class="badge b-pass">VALID</span>, <span class="badge b-fail">REVOKED</span>, or <span class="badge b-warn">EXPIRED</span> &mdash; with the reason. Revocation is published, not hidden: if a toolchain bug ever invalidates a verdict, the serial goes on the public revocation list.</p>
</div>

<h2>Interfaces</h2>
<ul>
<li><strong>Humans:</strong> the <a href="/verify/">web verifier</a>, the <a href="/check/">certificate checker</a>, and the <a href="/ask/">Ask shell</a> &mdash; chat and voice in front of the same service; the assistant explains, the service decides.</li>
<li><strong>Applications:</strong> the <a href="/docs/api/">REST API</a> with API-key auth and metering.</li>
<li><strong>Agents:</strong> the <a href="/docs/api/">REST API</a> is agent-shaped (one key, JSON in, signed evidence out). A hosted MCP endpoint is live at https://api.axiom-code.com/mcp/ &mdash; the same API key, the same queue, seven tools (verify, job_status, check_certificate, revoked, health, usage_report, pricing); an MCP server also ships in the AxiomCode repository for local use. Plus <a href="/llms.txt">llms.txt</a> and <a href="/.well-known/axiomcode.json">machine-readable service info</a>.</li>
</ul>
</div></div></section>
""",
)

# ---------- pricing ----------
page(
    "/pricing/",
    "Pricing",
    "AxiomCode pricing: 10 free trial verifications (no certificates), then credit packs. 1 credit = $0.01. Certificates are issued to paying customers only.",
    """<section class="block"><div class="wrap"><div class="prose">
<h1 class="pt">Pricing</h1>
<p class="sub">The trial proves the engine. The certificate is the product.</p>
<div class="note"><strong>Billing is paused:</strong> the service is live, but credit packs are <strong>not yet on sale</strong> &mdash; this page shows the pricing that will apply when pack sales open. Until then, API keys with the 10-verification trial are issued free on request. Our pricing covers the full cost of running the service &mdash; infrastructure, compute, operations, support, and insurance &mdash; plus a standard margin. One credit is always <strong>US$0.01</strong>. Verification consumes credits by compute time; the certificate itself is included with every paid verification.</div>
</div>
<div class="ptable">
<div class="plan">
<h3>Trial</h3><div class="price">$0</div><div class="per">no card required</div>
<ul>
<li>10 verifications per API key</li>
<li>Full verdict + usage record</li>
<li><strong>No certificates</strong> &mdash; trial verdicts are not certifiable</li>
<li>Rate-limited, fair use</li>
</ul>
<p><a class="cta" href="/verify/">Start verifying</a></p>
</div>
<div class="plan">
<h3>Starter</h3><div class="price">$10</div><div class="per">1,000 credits, never expire</div>
<ul>
<li>Roughly 30&ndash;100 typical verifications</li>
<li><strong>Signed certificates</strong> on every paid verdict &mdash; pass or fail</li>
<li>REST API + API key</li>
<li>Certificate checker + revocation list</li>
</ul>
<p><span class="cta" style="opacity:.55;cursor:default">Not yet on sale</span></p>
</div>
<div class="plan hot">
<h3>Growth</h3><div class="price">$50</div><div class="per">5,000 credits, never expire</div>
<ul>
<li>Roughly 150&ndash;500 typical verifications</li>
<li><strong>Signed certificates</strong> on every paid verdict &mdash; pass or fail</li>
<li>REST API access</li>
<li>Per-verification usage records &amp; audit log</li>
</ul>
<p><span class="cta" style="opacity:.55;cursor:default">Not yet on sale</span></p>
</div>
<div class="plan">
<h3>Scale</h3><div class="price">$200</div><div class="per">20,000 credits, never expire</div>
<ul>
<li>Roughly 600&ndash;2,000 typical verifications</li>
<li><strong>Signed certificates</strong> on every paid verdict &mdash; pass or fail</li>
<li>Everything in Growth</li>
<li>The same fair FIFO queue as everyone &mdash; nobody jumps the line</li>
</ul>
<p><span class="cta" style="opacity:.55;cursor:default">Not yet on sale</span></p>
</div>
</div>
<div class="wrap"><div class="prose" style="margin-top:36px">
<h2>How metering works</h2>
<p>Each verification is metered by compute time at <strong>0.9 credits/second</strong> (about $0.009/s). A small spec that checks in 12 seconds costs ~11 credits &mdash; eleven cents. Every verdict response carries its exact usage record &mdash; compute seconds, rate, credits, and US dollars &mdash; so your bill always reconciles. Credits never expire. Unused credits are refundable within 14 days &mdash; see the <a href="/paperwork/refunds/">Refund Policy</a>.</p>
<h2>Why the trial has no certificates</h2>
<p>The trial exists so you can evaluate the engine: real verdicts, real transcripts, real evidence. But a certificate is a trust instrument &mdash; it says AxiomCode stakes its name on this verdict. We only stake our name in a commercial relationship, where the full cost of standing behind the verdict is covered. That boundary is what keeps the certificates meaningful.</p>
<div class="faq">
<details><summary>What counts as a &ldquo;typical verification&rdquo;?</summary><p>A Lean 4 spec that compiles and checks in 10&ndash;60 seconds of engine time. Very large developments cost proportionally more; the meter is compute time, so you always pay for what you used.</p></details>
<details><summary>Do certificates really expire?</summary><p>Yes &mdash; 90 days, like TLS. Software changes and toolchains move on; re-verification keeps the evidence fresh. Renewal pricing is the same credit meter.</p></details>
<details><summary>What if a certificate was wrongly issued?</summary><p>We revoke it publicly and say so. Mis-issuance handling is documented in the <a href="/paperwork/certificate-policy/">Certificate Policy</a> &mdash; it&rsquo;s the core of the trust model.</p></details>
</div>
</div></div>
</section>
""",
    PRODUCT_JSONLD,
)
