import json

from build import API_BASE, page

# ---------- docs (humans) ----------
page(
    "/docs/",
    "Documentation",
    "AxiomCode documentation for humans: writing verifiable Lean 4 specifications, reading verdicts and certificates, and understanding verification scope.",
    """<section class="block"><div class="wrap"><div class="prose">
<h1 class="pt">Documentation</h1>
<p class="sub">For humans. Agents: see the <a href="/docs/api/">API reference</a> and <a href="/llms.txt">llms.txt</a>.</p>

<div class="docnav"><strong>On this page:</strong> &nbsp;<a href="#writing">Writing verifiable specs</a> &middot; <a href="#verdicts">Reading verdicts</a> &middot; <a href="#certificates">Certificates</a> &middot; <a href="#scope">Scope &amp; limits</a></div>

<h2 id="writing">Writing verifiable specifications</h2>
<p>AxiomCode checks <strong>Lean 4</strong> artifacts. The unit of verification is one submission: a Lean source file (plus its declared dependencies) with an explicit target the engine should build.</p>
<h3>What verifies cleanly</h3>
<ul>
<li>Explicit <code class="inline">theorem</code> / <code class="inline">def</code> targets with complete proofs.</li>
<li>Statements that say what you mean: name the preconditions, name the postconditions.</li>
<li>Self-contained developments, or ones whose dependencies you declare.</li>
</ul>
<h3>What gets rejected</h3>
<ul>
<li><code class="inline">sorry</code> and <code class="inline">admit</code> &mdash; placeholders are not proofs. The engine refuses them and tells you exactly where.</li>
<li>Targets that build nothing (vacuous builds).</li>
<li>Anything that doesn&rsquo;t compile: you get <span class="badge b-warn">INCOMPLETE</span> with the compiler log, not a pass.</li>
</ul>
<div class="note blue"><strong>Customer responsibility:</strong> the certificate binds the artifact you submitted. It does not certify that your specification captures your intent, or that the deployed system matches the artifact. Writing a faithful spec is your job; checking the proof is ours.</div>

<h3>Minimal example</h3>
<pre class="code">-- A tiny, honest spec: addition commutes on naturals.
theorem add_comm_nat (a b : Nat) : a + b = b + a := by
  exact Nat.add_comm a b</pre>
<p>Submit this through the <a href="/docs/api/">API</a> or the <a href="/verify/">web verifier</a> with your API key: the engine compiles it, the proof checks, the verdict is <span class="badge b-pass">PASSED</span>.</p>

<h2 id="verdicts">Reading verdicts</h2>
<table class="spec">
<tr><th>Verdict</th><th>Meaning</th><th>Certificate?</th></tr>
<tr><td><span class="badge b-pass">PASSED</span></td><td>The toolchain compiled the artifact and the proof checked.</td><td>Yes (paid only)</td></tr>
<tr><td><span class="badge b-fail">FAILED</span></td><td>The proof does not check. The transcript shows why.</td><td>No</td></tr>
<tr><td><span class="badge b-warn">INCOMPLETE</span></td><td>Doesn&rsquo;t compile yet, or the target is vacuous. Fix and resubmit.</td><td>No</td></tr>
</table>
<p>Every verdict response carries its usage record &mdash; the exact compute time and what you were charged. Paid passes also carry the signed certificate.</p>

<h2 id="certificates">Certificates</h2>
<p>A certificate is a signed JSON document. Fields are defined in the <a href="/paperwork/certificate-policy/">Certificate Policy</a>. Anyone can check a certificate&rsquo;s serial against the <a href="/check/">public revocation list</a>; full signature validation runs offline against the CA&rsquo;s published keys, or through the <a href="/check/">certificate checker</a> with an API key. Possible outcomes: <span class="badge b-pass">VALID</span>, <span class="badge b-fail">REVOKED</span>, <span class="badge b-warn">EXPIRED</span>.</p>

<h2 id="scope">Scope &amp; limits</h2>
<ul>
<li><strong>Language:</strong> Lean 4 only, today.</li>
<li><strong>What &ldquo;verified&rdquo; means:</strong> the certificate credentials the code &mdash; our assessment that the submitted artifact was built to its specification, as mechanically checked. We hold no responsibility beyond this assessment. Nothing about intent, deployment, or the rest of your system.</li>
<li><strong>Validity:</strong> 90 days from issuance. Re-verify after changes.</li>
<li><strong>Revocation:</strong> if we discover a toolchain or engine defect that undermines a verdict, the certificate is revoked publicly. There is no silent un-verification.</li>
</ul>
</div></div></section>
""",
)

# ---------- docs/api (agents) ----------
page(
    "/docs/api/",
    "REST & MCP API",
    "AxiomCode API for applications and AI agents: REST endpoints, authentication, the verification queue, metering, and machine-readable discovery.",
    """<section class="block"><div class="wrap"><div class="prose">
<h1 class="pt">REST API</h1>
<p class="sub">Built for agents first. Humans welcome.</p>
<div class="docnav"><strong>Machine-readable:</strong> &nbsp;<a href="/llms.txt">llms.txt</a> &middot; <a href="/.well-known/axiomcode.json">/.well-known/axiomcode.json</a> &middot; <a href="/docs/api/openapi.json">OpenAPI (JSON)</a></div>

<h2>Base URL</h2>
<p><code class="inline">https://api.axiom-code.com</code> &mdash; live.</p>

<h2>Authentication</h2>
<p>Every non-public endpoint takes an API key in the <code class="inline">X-API-Key</code> header (or <code class="inline">Authorization: Bearer &hellip;</code>). Your identity <em>is</em> the key &mdash; the service stores only its SHA-256 hash, and request bodies carry no identity. Keys are issued on request during the initial opening: email <a href="mailto:hello@axiom-code.com">hello@axiom-code.com</a>. <strong>The first 10 verification cases on a new key are a free trial</strong>: real verdicts and usage records, but never a certificate. Certificates unlock when the key holds paid credits (credit packs are not yet on sale &mdash; billing is paused while the opening completes).</p>

<h2>REST endpoints</h2>
<table class="spec">
<tr><th>Method &amp; path</th><th>Auth</th><th>What it does</th></tr>
<tr><td><code class="inline">POST /verify</code></td><td>API key</td><td>Verify a Lean artifact: <code class="inline">{"code": "&hellip;"}</code>. Returns the verdict, attempts, usage record, and &mdash; on a paid pass &mdash; the signed certificate. When every proof slot is busy, answers <code class="inline">202</code> with a queue position instead (see below). Answers <code class="inline">402</code> when the trial is exhausted and the key holds no credits &mdash; before any compute runs.</td></tr>
<tr><td><code class="inline">GET /verify/jobs/{job_id}</code></td><td>API key</td><td>Your queued job&rsquo;s position, or its finished result. Only the submitting key can read a job &mdash; any other key gets <code class="inline">404</code>.</td></tr>
<tr><td><code class="inline">POST /check</code></td><td>API key</td><td>Validate a certificate: <code class="inline">{"certificate": {&hellip;}}</code>. Recomputes the signature against the CA key and consults the revocation list.</td></tr>
<tr><td><code class="inline">POST /shell/turn</code></td><td>API key</td><td>One interactive-shell turn for the <a href="/ask/">Ask page</a>: an optional action (<code class="inline">verify</code> / <code class="inline">check</code>) plus conversation. Answers with facts rendered in code from the service&rsquo;s own responses, and an optional explanation &mdash; verdicts are never the model&rsquo;s.</td></tr>
<tr><td><code class="inline">GET /shell/jobs/{job_id}</code></td><td>API key</td><td>The shell&rsquo;s polling read for a queued job: the same owner-only view as <code class="inline">GET /verify/jobs/{job_id}</code>, plus the rendered fact block.</td></tr>
<tr><td><code class="inline">GET /revoked</code></td><td>public</td><td>The public revocation list: issuer + revoked serials.</td></tr>
<tr><td><code class="inline">GET /.well-known/axiomcode-keys.json</code></td><td>public</td><td>The CA&rsquo;s published public keys &mdash; validate certificates offline, without trusting this server.</td></tr>
<tr><td><code class="inline">GET /health</code></td><td>public</td><td>Service health.</td></tr>
</table>

<h3>Example: verification</h3>
<pre class="code">curl -X POST https://api.axiom-code.com/verify \\
  -H 'X-Api-Key: YOUR_KEY' -H 'Content-Type: application/json' \\
  -d '{"code":"theorem add_comm_nat (a b : Nat) : a + b = b + a := by\\n  exact Nat.add_comm a b"}'
# {"verified":true,"attempts":1,"certificate":null,
#  "usage":{"compute_s":11.8,"rate_credits_per_s":0.9,"credits":0,"usd":0},
#  "trial":{"cases_used":1,"cases_left":9,"certificates":"unlock with a credit pack"}}</pre>

<h2>The queue</h2>
<p>Proofs run in a bounded number of slots. When they are all busy, <code class="inline">POST /verify</code> does not fail and does not pile on &mdash; your request joins a <strong>durable first-in-first-out queue</strong> and the response says so: <code class="inline">202 {"status":"queued","job_id":"&hellip;","position":N}</code>. Poll <code class="inline">GET /verify/jobs/{job_id}</code> for the position and, when it finishes, the same result an inline run would have returned. One queue for everyone, in arrival order &mdash; there is no priority lane. A key that cannot pay never takes a place in line: eligibility is decided before admission.</p>

<h2>MCP server</h2>
<p>An MCP server (<code class="inline">verify</code>, <code class="inline">check_certificate</code>) ships in the <a href="https://github.com/nrupala/axiomcode">AxiomCode repository</a> and runs locally against this API. <strong>A hosted MCP endpoint is also live</strong> on the API host at <code class="inline">/mcp</code> &mdash; the same keys, the same durable queue, the same trial rules; agents may call either transport.</p>
<div class="note blue"><strong>Agent pattern:</strong> after your coding agent finishes a safety-critical function, have it write the Lean spec and call <code class="inline">POST /verify</code>. Ship the certificate with the code &mdash; your user can check it without trusting your agent.</div>

<h2>Metering</h2>
<p>Compute time is metered at 0.9 credits/second (1 credit = US$0.01). Every verdict response includes its usage record &mdash; <code class="inline">compute_s</code>, <code class="inline">rate_credits_per_s</code>, <code class="inline">credits</code>, <code class="inline">usd</code> &mdash; and meter records are append-only in a hash-chained audit log, so your bill always reconciles.</p>

<h2>Rate limits &amp; abuse</h2>
<ul>
<li>60 requests per minute per key; up to 2 proofs in flight per key &mdash; beyond that, requests queue (above) rather than fail.</li>
<li>Submissions are capped at 256 KB of source; proof wall-clock is capped per call.</li>
<li>We may suspend keys used to probe the engine adversarially or to multiply trials. See the <a href="/paperwork/terms/">Terms</a>.</li>
</ul>
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
