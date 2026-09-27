from build import *

# ---------- docs (humans) ----------
page("/docs/", "Documentation",
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
<p>Submit this in the <a href="/verify/">web verifier</a>: the engine compiles it, the proof checks, the verdict is <span class="badge b-pass">PASSED</span>.</p>

<h2 id="verdicts">Reading verdicts</h2>
<table class="spec">
<tr><th>Verdict</th><th>Meaning</th><th>Certificate?</th></tr>
<tr><td><span class="badge b-pass">PASSED</span></td><td>The toolchain compiled the artifact and the proof checked.</td><td>Yes (paid only)</td></tr>
<tr><td><span class="badge b-fail">FAILED</span></td><td>The proof does not check. The transcript shows why.</td><td>No</td></tr>
<tr><td><span class="badge b-warn">INCOMPLETE</span></td><td>Doesn&rsquo;t compile yet, or the target is vacuous. Fix and resubmit.</td><td>No</td></tr>
</table>
<p>Every verdict ships with the engine transcript and the exact compute time you were charged for.</p>

<h2 id="certificates">Certificates</h2>
<p>A certificate is a signed JSON document. Fields are defined in the <a href="/paperwork/certificate-policy/">Certificate Policy</a>. Validate any certificate at <a href="/check/">/check</a> &mdash; no account required. Possible outcomes: <span class="badge b-pass">VALID</span>, <span class="badge b-fail">REVOKED</span>, <span class="badge b-warn">EXPIRED</span>.</p>

<h2 id="scope">Scope &amp; limits</h2>
<ul>
<li><strong>Language:</strong> Lean 4 only, today.</li>
<li><strong>What &ldquo;verified&rdquo; means:</strong> the submitted artifact compiled under the stated toolchain and its proofs checked. Nothing about intent, deployment, or the rest of your system.</li>
<li><strong>Validity:</strong> 90 days from issuance. Re-verify after changes.</li>
<li><strong>Revocation:</strong> if we discover a toolchain or engine defect that undermines a verdict, the certificate is revoked publicly. There is no silent un-verification.</li>
</ul>
</div></div></section>
""")

# ---------- docs/api (agents) ----------
page("/docs/api/", "REST & MCP API",
     "AxiomCode API for applications and AI agents: REST endpoints, MCP tools, authentication, metering, and machine-readable discovery.",
"""<section class="block"><div class="wrap"><div class="prose">
<h1 class="pt">REST &amp; MCP API</h1>
<p class="sub">Built for agents first. Humans welcome.</p>
<div class="docnav"><strong>Machine-readable:</strong> &nbsp;<a href="/llms.txt">llms.txt</a> &middot; <a href="/.well-known/axiomcode.json">/.well-known/axiomcode.json</a> &middot; <a href="/docs/api/openapi.json">OpenAPI (JSON)</a></div>

<h2>Base URL</h2>
<p><code class="inline">https://api.axiom-code.com</code></p>

<h2>Authentication</h2>
<p>Paid endpoints take an API key in the <code class="inline">X-API-Key</code> header. Keys are issued after any credit purchase. Trial endpoints take an email address and are limited to 10 verifications with no certificates.</p>

<h2>REST endpoints</h2>
<table class="spec">
<tr><th>Method &amp; path</th><th>Auth</th><th>What it does</th></tr>
<tr><td><code class="inline">POST /v1/trial/verify</code></td><td>email</td><td>Verify a Lean artifact. Returns verdict + transcript. No certificate. 10 lifetime uses per email.</td></tr>
<tr><td><code class="inline">POST /v1/verify</code></td><td>API key</td><td>Verify and, on pass, issue a signed certificate. Metered by compute time.</td></tr>
<tr><td><code class="inline">GET /v1/check?serial=...</code></td><td>none</td><td>Certificate status: VALID / REVOKED / EXPIRED, with reason.</td></tr>
<tr><td><code class="inline">GET /v1/revoked</code></td><td>none</td><td>The public revocation list.</td></tr>
<tr><td><code class="inline">GET /v1/account</code></td><td>API key</td><td>Credit balance and usage report.</td></tr>
</table>

<h3>Example: trial verification</h3>
<pre class="code">curl -X POST https://api.axiom-code.com/v1/trial/verify \\
  -H 'Content-Type: application/json' \\
  -d '{"email":"you@example.com",
       "code":"theorem add_comm_nat (a b : Nat) : a + b = b + a := by\\n  exact Nat.add_comm a b"}'
# {"verdict":"PASSED","compute_seconds":11.8,"credits_charged":0,
#  "trial_remaining":9,"certificate":null,
#  "note":"Trial verdicts carry no certificate."}</pre>

<h2>MCP server</h2>
<p>Endpoint: <code class="inline">https://api.axiom-code.com/mcp</code> (streamable HTTP). Tools:</p>
<table class="spec">
<tr><th>Tool</th><th>What it does</th></tr>
<tr><td><code class="inline">verify</code></td><td>Submit a Lean artifact; returns verdict, transcript, and (paid) certificate.</td></tr>
<tr><td><code class="inline">check_certificate</code></td><td>Validate a certificate by serial.</td></tr>
<tr><td><code class="inline">pricing</code></td><td>Current credit price and pack list.</td></tr>
<tr><td><code class="inline">usage_report</code></td><td>Metered usage for your API key.</td></tr>
</table>
<div class="note blue"><strong>Agent pattern:</strong> after your coding agent finishes a safety-critical function, have it write the Lean spec and call <code class="inline">verify</code>. Ship the certificate with the code &mdash; your user can check it without trusting your agent.</div>

<h2>Metering</h2>
<p>Compute time is metered at 0.9 credits/second (1 credit = US$0.01). Every response includes <code class="inline">compute_seconds</code> and <code class="inline">credits_charged</code>. Meter records are append-only and tamper-evident; your <code class="inline">usage_report</code> always reconciles.</p>

<h2>Rate limits &amp; abuse</h2>
<ul>
<li>Trial: 10 verifications per email, lifetime; 1 concurrent request.</li>
<li>Paid: 5 concurrent verifications per key by default; contact us for more.</li>
<li>Submissions are capped at 2 MB of source; engine time is capped per call.</li>
<li>We may suspend keys used to probe the engine adversarially or to resell trial access. See the <a href="/paperwork/terms/">Terms</a>.</li>
</ul>
</div></div></section>
""")

# ---------- verify (trial UI) ----------
page("/verify/", "Verify \u2014 free trial",
     "Try AxiomCode free: submit a Lean 4 specification, get a real machine-checked verdict and proof transcript. 10 free verifications; trial verdicts carry no certificate.",
"""<section class="block"><div class="wrap"><div class="prose">
<h1 class="pt">Verify &mdash; free trial</h1>
<p class="sub">10 free verifications. Real verdicts, real transcripts. <strong>No certificates on trial</strong> &mdash; the certificate is the product, and it ships with paid verification.</p>
<div class="note">The verification backend is being connected to this page as part of the launch rollout. If the button reports the API as unreachable, the engine isn&rsquo;t wired yet &mdash; check back shortly or email <a href="mailto:hello@axiom-code.com">hello@axiom-code.com</a>.</div>
<label class="fl" for="email">Email (counts your 10 trial uses)</label>
<input type="email" id="email" placeholder="you@example.com" autocomplete="email">
<label class="fl" for="code">Lean 4 code</label>
<textarea class="codebox" id="code" spellcheck="false">theorem add_comm_nat (a b : Nat) : a + b = b + a := by
  exact Nat.add_comm a b</textarea>
<p style="margin-top:18px"><button class="go" id="go">Run verification</button></p>
<div class="result" id="result"></div>
<p style="color:var(--mut);font-size:15px">A <span class="badge b-pass">PASSED</span> trial verdict proves the engine works. To get the <strong>signed certificate</strong> &mdash; the thing you can hand to an auditor, a customer, or a counterparty &mdash; <a href="/pricing/">buy credits</a>.</p>
</div></div></section>
<script>
var API = %s;
document.getElementById('go').addEventListener('click', function(){
  var btn = this, res = document.getElementById('result');
  var email = document.getElementById('email').value.trim();
  var code = document.getElementById('code').value;
  if (!email || email.indexOf('@') < 0) { alert('Enter your email so we can count your 10 trial uses.'); return; }
  if (!code.trim()) { alert('Paste some Lean 4 code first.'); return; }
  btn.disabled = true; btn.textContent = 'Verifying\u2026';
  res.className = 'result show'; res.innerHTML = '<p>Running the Lean toolchain against your artifact\u2026</p>';
  fetch(API + '/v1/trial/verify', {method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({email: email, code: code})})
  .then(function(r){ return r.json().then(function(j){ return {ok: r.ok, j: j}; }); })
  .then(function(x){
    btn.disabled = false; btn.textContent = 'Run verification';
    if (!x.ok) { res.innerHTML = '<p><span class="badge b-fail">ERROR</span></p><pre class="code">' + JSON.stringify(x.j, null, 2) + '</pre>'; return; }
    var j = x.j;
    var badge = j.verdict === 'PASSED' ? 'b-pass' : (j.verdict === 'FAILED' ? 'b-fail' : 'b-warn');
    res.innerHTML = '<p><span class="badge ' + badge + '">' + j.verdict + '</span></p>'
      + '<p style="color:var(--mut);font-size:15px">Engine time: ' + j.compute_seconds + 's &middot; trial uses remaining: ' + j.trial_remaining + ' &middot; no certificate (trial)</p>'
      + '<pre class="code">' + (j.transcript || 'no transcript') + '</pre>'
      + (j.verdict === 'PASSED' ? '<p><a class="cta" href="/pricing/">Get this certified &rarr;</a></p>' : '');
  })
  .catch(function(e){
    btn.disabled = false; btn.textContent = 'Run verification';
    res.innerHTML = '<p><span class="badge b-warn">API UNREACHABLE</span></p><p style="color:var(--mut)">The verification backend is not connected yet. Your code is fine &mdash; the wiring is still being rolled out. Try again shortly.</p>';
  });
});
</script>
""" % json.dumps(API_BASE))

# ---------- check (cert validation UI) ----------
page("/check/", "Check a certificate",
     "Validate an AxiomCode certificate: paste the certificate JSON and get VALID, REVOKED, or EXPIRED with the reason. No account needed.",
"""<section class="block"><div class="wrap"><div class="prose">
<h1 class="pt">Check a certificate</h1>
<p class="sub">No account needed. Paste the certificate JSON &mdash; we&rsquo;ll tell you if it&rsquo;s <span class="badge b-pass">VALID</span>, <span class="badge b-fail">REVOKED</span>, or <span class="badge b-warn">EXPIRED</span>, and why.</p>
<label class="fl" for="cert">Certificate JSON</label>
<textarea class="codebox" id="cert" spellcheck="false" placeholder='{"serial": "AX-2026-000001", ...}'></textarea>
<p style="margin-top:18px"><button class="go" id="go2">Check certificate</button></p>
<div class="result" id="result2"></div>
<div class="note blue" style="margin-top:24px"><strong>Don&rsquo;t trust our AI &mdash; verify our proof.</strong> A certificate is only as good as its checkability. This page, the <a href="/docs/api/">API</a>, and the published revocation list are how you hold us accountable.</div>
</div></div></section>
<script>
var API2 = %s;
document.getElementById('go2').addEventListener('click', function(){
  var btn = this, res = document.getElementById('result2');
  var raw = document.getElementById('cert').value.trim();
  if (!raw) { alert('Paste a certificate JSON first.'); return; }
  var cert; try { cert = JSON.parse(raw); }
  catch(e){ alert('That is not valid JSON.'); return; }
  btn.disabled = true; btn.textContent = 'Checking\u2026';
  res.className = 'result show'; res.innerHTML = '<p>Consulting the revocation list\u2026</p>';
  var serial = cert.serial || '';
  fetch(API2 + '/v1/check?serial=' + encodeURIComponent(serial))
  .then(function(r){ return r.json().then(function(j){ return {ok: r.ok, j: j}; }); })
  .then(function(x){
    btn.disabled = false; btn.textContent = 'Check certificate';
    var j = x.j || {};
    var st = (j.status || 'UNKNOWN').toUpperCase();
    var badge = st === 'VALID' ? 'b-pass' : (st === 'REVOKED' ? 'b-fail' : 'b-warn');
    res.innerHTML = '<p><span class="badge ' + badge + '">' + st + '</span></p>'
      + '<pre class="code">' + JSON.stringify(j, null, 2) + '</pre>';
  })
  .catch(function(e){
    btn.disabled = false; btn.textContent = 'Check certificate';
    res.innerHTML = '<p><span class="badge b-warn">API UNREACHABLE</span></p><p style="color:var(--mut)">The checker backend is not connected yet. Try again shortly.</p>';
  });
});
</script>
""" % json.dumps(API_BASE))
