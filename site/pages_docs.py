import json

from build import API_BASE, page
from pages_docs_pack import DOCMETA, docmeta_html, sidenav

# ---------- docs home (Diátaxis-first) ----------
DOCMETA["/docs/"] = {
    "type": "Documentation home",
    "audience": "All",
    "packs": "All seven",
    "source": "Docs set; facts generated from canonical sources",
    "title": "Documentation",
}
page(
    "/docs/",
    "Documentation",
    "AxiomCode documentation: Diátaxis-first — tutorials, guides, reference, explanation — with role packs for Guest, Users, Developers, Maintainers, Regulators, Admins, and Ops.",
    f"""<section><div class="wrap"><div class="docslayout">
{sidenav("/docs/")}
<div class="docbody">
{docmeta_html("/docs/")}
<h1>Documentation</h1>
<p class="sub" style="font-size:18px">Organized the Diátaxis way: learn by doing in the tutorials, solve a task in the guides, look facts up in the reference, understand the system in the explanations. Role packs cut the same set by who you are.</p>

<div class="quad">
<div class="card"><h3>Tutorials</h3><p>Learning-oriented, step by step.</p>
<p class="go"><a href="/docs/start/first-verification/">First verification</a><br>
<a href="/docs/start/first-certificate-check/">First certificate check</a><br>
<a href="/docs/start/first-mcp-call/">First MCP call</a></p></div>
<div class="card"><h3>Guides</h3><p>Task-oriented, for working users.</p>
<p class="go"><a href="/docs/guides/write-a-verifiable-lean-artefact/">Write a verifiable artefact</a><br>
<a href="/docs/guides/use-the-queue/">Use the queue</a><br>
<a href="/docs/guides/integrate-an-agent/">Integrate an agent</a></p></div>
<div class="card"><h3>Reference</h3><p>Fact-oriented, complete and exact.</p>
<p class="go"><a href="/docs/api/">REST API</a><br>
<a href="/docs/mcp/">MCP (hosted &amp; local)</a><br>
<a href="/docs/reference/verdicts-and-errors/">Verdicts &amp; errors</a></p></div>
<div class="card"><h3>Explanation</h3><p>Understanding-oriented — the why.</p>
<p class="go"><a href="/docs/explanation/what-verification-proves/">What verification proves</a><br>
<a href="/docs/explanation/what-it-does-not-prove/">What it does not prove</a><br>
<a href="/docs/explanation/certificate-trust-model/">Certificate trust model</a></p></div>
</div>

<h2 style="margin-top:40px">Start in five minutes</h2>
<p style="color:var(--mut)">Keys are issued by email (free; the first 10 cases are the trial). Then: <a href="/docs/start/first-verification/">first verification</a> → <a href="/docs/guides/write-a-verifiable-lean-artefact/">write your own artefact</a> → <a href="/docs/start/first-certificate-check/">check a certificate like a relying party</a>.</p>

<h2 style="margin-top:40px">Role packs</h2>
<div class="roles">
<div class="role"><h3><a href="/docs/roles/guest/">Guest</a></h3><p>Unauthenticated evaluator — judge it before you join it.</p></div>
<div class="role"><h3><a href="/docs/roles/users/">Users</a></h3><p>Key-holders — the working set.</p></div>
<div class="role"><h3><a href="/docs/roles/developers/">Developers</a></h3><p>Integrators and agent builders.</p></div>
<div class="role"><h3><a href="/docs/roles/maintainers/">Maintainers</a></h3><p>Evidence on request — boundary published, internals not.</p></div>
<div class="role"><h3><a href="/docs/roles/regulators/">Regulators</a></h3><p>Policy first, control → evidence index.</p></div>
<div class="role"><h3><a href="/docs/roles/admins/">Admins</a></h3><p>Account administration as it actually works today.</p></div>
<div class="role"><h3><a href="/docs/roles/ops/">Ops</a></h3><p>Surfaces, health evidence, the incident rule.</p></div>
</div>

<div class="honest"><h3>About this documentation</h3>
<p>Every page carries its audience, Diátaxis type, version, last-verified date, source artefact, and a Markdown mirror (linked in the meta block). Status, lifecycle, and pricing facts are generated from the same canonical sources as the <a href="/status/">status page</a> and are covered by CI drift checks. The Maintainers pack is the one deliberate boundary: structure public, internals on request.</p>
<p>Documentation error? It is a product error — report it on <a href="https://github.com/nrupala/axiomcode/issues">GitHub Issues</a>, user-initiated only.</p></div>
</div>
</div></div></section>
""",
)

# ---------- docs/api (reference) ----------
DOCMETA["/docs/api/"] = {
    "type": "Reference",
    "audience": "Developers, agents",
    "packs": "Developers",
    "source": "Live OpenAPI (canonical) + service behaviour",
    "title": "API — machine-first docs",
}
page(
    "/docs/api/",
    "API — machine-first docs",
    "AxiomCode REST API reference: endpoints, request and response shapes, the queue, trial semantics, and error outcomes. The live OpenAPI document is the contract of record.",
    f"""<section><div class="wrap"><div class="docslayout">
{sidenav("/docs/api/")}
<div class="docbody">
{docmeta_html("/docs/api/")}
<h1>API — machine-first docs</h1>
<p class="sub" style="font-size:18px">Base: <code class="inline">{API_BASE}</code> &middot; Auth: <code class="inline">X-Api-Key</code> header on every call except the public endpoints.</p>
<div class="note"><strong>Contract of record:</strong> the live OpenAPI document at <a href="{API_BASE}/openapi.json"><code class="inline">{API_BASE}/openapi.json</code></a> (OpenAPI 3.1, served by the API itself) is canonical. This page is the human-readable rendering of the same contract; the summary JSON kept on this site for offline reading is labelled a summary and never overrides the live document.</div>
<table class="spec">
<tr><th>Endpoint</th><th>What</th></tr>
<tr><td><code class="inline">POST /verify</code></td><td>Submit a Lean artefact <code class="inline">{{"code": "..."}}</code>. 200 → verdict + usage (+ certificate when paid). 202 → queued, poll the job.</td></tr>
<tr><td><code class="inline">GET /verify/jobs/{{job_id}}</code></td><td>Poll a queued job (same key). 202 while queued/running; 200 with the result; a failed job reports a NO VERDICT outcome.</td></tr>
<tr><td><code class="inline">POST /check</code></td><td>Validate a certificate <code class="inline">{{"certificate": {{...}}}}</code> — signature, validity window, revocation.</td></tr>
<tr><td><code class="inline">GET /revoked</code></td><td>Public revocation list. No auth.</td></tr>
<tr><td><code class="inline">GET /.well-known/axiomcode-keys.json</code></td><td>CA public keys. No auth.</td></tr>
<tr><td><code class="inline">GET /health</code></td><td>Service health. No auth.</td></tr>
<tr><td><code class="inline">POST /shell/turn</code> · <code class="inline">GET /shell/jobs/{{job_id}}</code></td><td>The Ask shell's backend — orchestrates the same verify/check callables; the shell's facts are rendered in code from these payloads.</td></tr>
</table>
<p style="color:var(--mut);font-size:15px">Billing endpoints (<code class="inline">POST /billing/checkout</code>, <code class="inline">POST /billing/webhook</code>) exist in the route table and answer 501 while billing is paused.</p>
<h2>Rules of the road</h2>
<ul>
<li><strong>Verdicts are boolean</strong> — PASSED or FAILED. Errors are <a href="/docs/reference/verdicts-and-errors/">NO VERDICT outcomes</a> (401/402/413/429/504, failed jobs) and never carry certificates.</li>
<li><strong>Trial:</strong> the first 10 cases per key return verdicts + usage, never certificates. Certificates ride paid verifications (packs not yet on sale — <a href="/pricing/">pricing</a>).</li>
<li><strong>Queue:</strong> bounded proof slots; saturation answers 202 with a position. See <a href="/docs/guides/use-the-queue/">use the queue</a>.</li>
<li><strong>Metering:</strong> 0.9 credits per engine second; timeouts and refusals are free. See <a href="/docs/guides/reconcile-metering/">reconcile metering</a>.</li>
<li><strong>Limits:</strong> 256 KB artefacts; keys stored as hashes only. See <a href="/docs/reference/keys-and-limits/">keys &amp; limits</a>.</li>
<li><strong>MCP instead?</strong> The same service is exposed as seven tools at <code class="inline">{API_BASE}/mcp/</code> — see the <a href="/docs/mcp/">MCP reference</a>.</li>
</ul>
<pre class="code">curl -X POST {API_BASE}/verify \\
  -H "X-Api-Key: $AXIOMCODE_KEY" -H "Content-Type: application/json" \\
  -d '{{"code": "theorem t (a b : Nat) : a + b = b + a := Nat.add_comm a b"}}'

&rarr; {{"verified": true, "job_id": null, "artifact_hash": "sha256:…",
    "attempts": […], "usage": {{…}},
    "trial": {{"used": 1, "limit": 10}}, "certificate": null}}</pre>
</div>
</div></div></section>
""",
)

# ---------- verify (API-key UI) ----------
page(
    "/verify/",
    "Verify \u2014 free trial",
    "Run an AxiomCode verification: submit a Lean 4 specification with your API key and get a real machine-checked verdict. The first 10 cases on a new key are free; trial verdicts carry no certificate.",
    """<section class="block"><div class="wrap"><div class="prose">
<h1 class="pt">Verify</h1>
<p class="sub">The first <strong>10 verifications on a new API key are free</strong> &mdash; real verdicts, real usage records. <strong>No certificates on trial</strong> &mdash; the certificate is the product, and it ships with paid verification.</p>
<div class="note">You need an API key. Keys are issued free on request during the initial opening &mdash; email <a href="mailto:hello@axiom-code.com">hello@axiom-code.com</a> and we&rsquo;ll send one. Your key is sent only to the AxiomCode API from this page; it is never stored by the page.</div>
<label class="fl" for="apikey">API key</label>
<input type="text" id="apikey" placeholder="your API key" autocomplete="off">
<label class="fl" for="code">Lean 4 code</label>
<textarea class="codebox" id="code" spellcheck="false">theorem add_comm_nat (a b : Nat) : a + b = b + a := by
  exact Nat.add_comm a b</textarea>
<p style="margin-top:18px"><button class="go" id="go">Run verification</button></p>
<div class="result" id="result"></div>
<p style="color:var(--mut);font-size:15px">A <span class="badge b-pass">PASSED</span> trial verdict proves the engine works. To get the <strong>signed certificate</strong> &mdash; the thing you can hand to an auditor, a customer, or a counterparty &mdash; your key needs paid credits; see <a href="/pricing/">pricing</a> (packs open when billing is armed).</p>
</div></div></section>
<script>
var API = """
    + json.dumps(API_BASE)
    + """;
function esc(s){ return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;'); }
function showResult(res, j){
  var badge = j.verified ? 'b-pass' : 'b-fail';
  var word = j.verified ? 'PASSED' : 'FAILED';
  var h = '<p><span class="badge ' + badge + '">' + word + '</span></p>';
  var meta = [];
  if (j.attempts != null) meta.push('attempts: ' + j.attempts);
  if (j.usage) meta.push('engine time: ' + j.usage.compute_s + 's &middot; credits: ' + j.usage.credits);
  if (j.trial) meta.push('trial cases left: ' + j.trial.cases_left + ' &middot; no certificate (trial)');
  if (meta.length) h += '<p style="color:var(--mut);font-size:15px">' + meta.join(' &middot; ') + '</p>';
  if (j.certificate) h += '<p><strong>Certificate</strong></p><pre class="code">' + esc(JSON.stringify(j.certificate, null, 2)) + '</pre>';
  res.innerHTML = h;
}
function showError(res, title, msg){
  res.innerHTML = '<p><span class="badge b-warn">' + title + '</span></p><p style="color:var(--mut)">' + msg + '</p>';
}
document.getElementById('go').addEventListener('click', function(){
  var btn = this, res = document.getElementById('result');
  var key = document.getElementById('apikey').value.trim();
  var code = document.getElementById('code').value;
  if (!key) { alert('Enter your API key. No key yet? Email hello@axiom-code.com and we will issue one free.'); return; }
  if (!code.trim()) { alert('Paste some Lean 4 code first.'); return; }
  var headers = {'Content-Type':'application/json', 'X-Api-Key': key};
  btn.disabled = true; btn.textContent = 'Verifying\\u2026';
  res.className = 'result show'; res.innerHTML = '<p>Running the Lean toolchain against your artifact\\u2026</p>';
  function done(){ btn.disabled = false; btn.textContent = 'Run verification'; }
  fetch(API + '/verify', {method:'POST', headers: headers, body: JSON.stringify({code: code})})
  .then(function(r){ return r.json().then(function(j){ return {status: r.status, j: j}; }); })
  .then(function(x){
    if (x.status === 200) { done(); showResult(res, x.j); return; }
    if (x.status === 202) {
      var jobId = x.j.job_id;
      res.innerHTML = '<p><span class="badge b-warn">QUEUED</span></p><p style="color:var(--mut)">Every proof slot is busy. Your place in line: <strong>' + x.j.position + '</strong>. This page checks for you &mdash; leave it open.</p>';
      var tries = 0;
      var iv = setInterval(function(){
        tries++;
        fetch(API + '/verify/jobs/' + encodeURIComponent(jobId), {headers: headers})
        .then(function(r){ return r.json().then(function(j){ return {status: r.status, j: j}; }); })
        .then(function(y){
          if (y.j.status === 'done') { clearInterval(iv); done(); showResult(res, y.j.result || {}); }
          else if (y.j.status === 'failed') { clearInterval(iv); done(); showError(res, 'JOB FAILED', esc(y.j.error || 'the verification job failed')); }
          else if (y.j.status === 'queued') { res.innerHTML = '<p><span class="badge b-warn">QUEUED</span></p><p style="color:var(--mut)">Your place in line: <strong>' + y.j.position + '</strong>. Checking again in a few seconds\\u2026</p>'; }
          else if (y.j.status === 'running') { res.innerHTML = '<p><span class="badge b-warn">RUNNING</span></p><p style="color:var(--mut)">Your proof is running now\\u2026</p>'; }
          if (tries > 100) { clearInterval(iv); done(); showError(res, 'STILL QUEUED', 'The queue is long. Your job id is ' + esc(jobId) + ' &mdash; check it any time at GET /verify/jobs/' + esc(jobId) + ' with your key.'); }
        })
        .catch(function(){ /* transient; keep polling */ });
      }, 3000);
      return;
    }
    done();
    if (x.status === 401) showError(res, 'INVALID KEY', 'That API key was not accepted. Check it, or email hello@axiom-code.com for a key.');
    else if (x.status === 402) showError(res, 'TRIAL EXHAUSTED', 'Your 10 free trial cases are used and the key holds no credits. Certificates unlock with a credit pack &mdash; packs open when billing is armed.');
    else if (x.status === 413) showError(res, 'TOO LARGE', 'Submissions are capped at 256 KB of source.');
    else if (x.status === 429) showError(res, 'RATE LIMITED', 'Over 60 requests per minute for this key. Wait a moment and retry.');
    else if (x.status === 504) showError(res, 'PROOF TIMEOUT', 'The proof exceeded the per-call time cap. Split the artifact or simplify the target.');
    else showError(res, 'ERROR ' + x.status, esc(JSON.stringify(x.j)));
  })
  .catch(function(e){
    done();
    showError(res, 'API UNREACHABLE', 'The verification API did not answer. Try again in a moment; if it persists, email hello@axiom-code.com.');
  });
});
</script>
""",
)

# ---------- check (cert validation UI) ----------
page(
    "/check/",
    "Check a certificate",
    "Validate an AxiomCode certificate: anyone can check a serial against the public revocation list; full signature validation runs with an API key or offline against the published CA keys.",
    """<section class="block"><div class="wrap"><div class="prose">
<h1 class="pt">Check a certificate</h1>
<p class="sub">Paste the certificate JSON. Anyone can check its serial against the <strong>public revocation list</strong>; full signature validation runs with your API key &mdash; or offline, against the CA&rsquo;s <a href="https://api.axiom-code.com/.well-known/axiomcode-keys.json">published keys</a>, without trusting our server at all.</p>
<label class="fl" for="cert">Certificate JSON</label>
<textarea class="codebox" id="cert" spellcheck="false" placeholder='{"serial": "&hellip;", "payload": {&hellip;}, "signature": "&hellip;"}'></textarea>
<label class="fl" for="apikey2">API key (for full validation; optional for the revocation check)</label>
<input type="text" id="apikey2" placeholder="your API key" autocomplete="off">
<p style="margin-top:18px"><button class="go" id="go2">Check certificate</button></p>
<div class="result" id="result2"></div>
<div class="note blue" style="margin-top:24px"><strong>Don&rsquo;t trust our AI &mdash; verify our proof.</strong> A certificate is only as good as its checkability. This page, the <a href="/docs/api/">API</a>, and the published revocation list are how you hold us accountable.</div>
</div></div></section>
<script>
var API2 = """
    + json.dumps(API_BASE)
    + """;
function esc2(s){ return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;'); }
document.getElementById('go2').addEventListener('click', function(){
  var btn = this, res = document.getElementById('result2');
  var raw = document.getElementById('cert').value.trim();
  var key = document.getElementById('apikey2').value.trim();
  if (!raw) { alert('Paste a certificate JSON first.'); return; }
  var cert; try { cert = JSON.parse(raw); }
  catch(e){ alert('That is not valid JSON.'); return; }
  var serial = cert.serial || (cert.payload && cert.payload.serial) || '';
  btn.disabled = true; btn.textContent = 'Checking\\u2026';
  res.className = 'result show'; res.innerHTML = '<p>Consulting the public revocation list\\u2026</p>';
  function done(){ btn.disabled = false; btn.textContent = 'Check certificate'; }
  fetch(API2 + '/revoked')
  .then(function(r){ return r.json(); })
  .then(function(rev){
    var revoked = serial && (rev.revoked || []).indexOf(serial) >= 0;
    if (revoked) {
      done();
      res.innerHTML = '<p><span class="badge b-fail">REVOKED</span></p><p style="color:var(--mut)">Serial ' + esc2(serial) + ' is on the public revocation list. Do not rely on this certificate.</p>';
      return;
    }
    if (!key) {
      done();
      res.innerHTML = '<p><span class="badge b-pass">NOT REVOKED</span></p><p style="color:var(--mut)">Serial ' + esc2(serial || '(none found in the JSON)') + ' is not on the public revocation list. For full signature validation, add your API key above, or verify the signature offline against the published CA keys.</p>';
      return;
    }
    return fetch(API2 + '/check', {method:'POST', headers:{'Content-Type':'application/json','X-Api-Key': key}, body: JSON.stringify({certificate: cert})})
    .then(function(r){ return r.json().then(function(j){ return {status: r.status, j: j}; }); })
    .then(function(x){
      done();
      if (x.status === 401) { res.innerHTML = '<p><span class="badge b-warn">INVALID KEY</span></p><p style="color:var(--mut)">That API key was not accepted for full validation. The revocation check above is unaffected: this serial is not revoked.</p>'; return; }
      var j = x.j || {};
      if (j.valid) {
        res.innerHTML = '<p><span class="badge b-pass">VALID</span></p><p style="color:var(--mut)">The signature verifies against the CA key and the serial is not revoked.</p><pre class="code">' + esc2(JSON.stringify(j, null, 2)) + '</pre>';
      } else {
        var reason = (j.reason || 'invalid');
        var badge = reason === 'revoked' ? 'b-fail' : 'b-warn';
        var word = reason === 'revoked' ? 'REVOKED' : reason.toUpperCase();
        res.innerHTML = '<p><span class="badge ' + badge + '">' + esc2(word) + '</span></p><pre class="code">' + esc2(JSON.stringify(j, null, 2)) + '</pre>';
      }
    });
  })
  .catch(function(e){
    done();
    res.innerHTML = '<p><span class="badge b-warn">API UNREACHABLE</span></p><p style="color:var(--mut)">The checker backend did not answer. Try again shortly.</p>';
  });
});
</script>
""",
)
