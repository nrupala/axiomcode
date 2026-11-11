import json

from build import API_BASE, page

# ---------- ask (interactive shell UI) ----------
page(
    "/ask/",
    "Ask AxiomCode",
    "Talk to AxiomCode: chat or speak with the shell, submit Lean 4 code for a real machine-checked verdict, check a certificate, and hear the results in plain words. The assistant explains; the service decides.",
    """<section class="block"><div class="wrap"><div class="prose">
<h1 class="pt">Ask AxiomCode</h1>
<p class="sub">Talk to the service &mdash; by typing, or by voice. Ask what a certificate means, have your code checked, check a certificate, see your usage.</p>
<div class="note"><strong>Who decides what:</strong> the assistant explains, but it cannot issue, change, soften, or predict a verdict. Every verdict on this page comes from the same verification service as the API &mdash; rendered from the service&rsquo;s own response, never from the assistant&rsquo;s words. When the service cannot answer, this page says so instead of guessing.</div>
<label class="fl" for="apikey">API key</label>
<input type="text" id="apikey" placeholder="your API key" autocomplete="off">
<p style="color:var(--mut);font-size:14.5px;margin:6px 0 0">No key yet? Email <a href="mailto:hello@axiom-code.com">hello@axiom-code.com</a> &mdash; keys with 10 free trial verifications are issued free. Your key is sent only to the AxiomCode API. It is not stored unless you tick the box, and then only in this tab&rsquo;s session storage.<br>
<label style="font-weight:400"><input type="checkbox" id="remember"> Remember my key for this tab session</label></p>

<div id="log" style="margin-top:26px"></div>

<label class="fl" for="msg">Your message</label>
<input type="text" id="msg" placeholder="e.g. what does a certificate actually prove?" autocomplete="off">
<p style="margin-top:14px">
<button class="go" id="send">Send</button>
<button class="go" id="mic" style="background:#fff;color:var(--navy);border:1px solid var(--line);display:none">&#127908; Speak instead</button>
<label style="font-weight:400;margin-left:10px"><input type="checkbox" id="speak"> Read replies aloud</label>
</p>
<p id="voicenote" style="color:var(--mut);font-size:14.5px"></p>

<label class="fl" for="code">Lean 4 code to verify</label>
<textarea class="codebox" id="code" spellcheck="false" style="min-height:150px">theorem add_comm_nat (a b : Nat) : a + b = b + a := by
  exact Nat.add_comm a b</textarea>
<p style="margin-top:14px"><button class="go" id="verify">Verify this code</button></p>

<details style="margin-top:22px">
<summary style="font-weight:700;cursor:pointer">Check a certificate instead</summary>
<label class="fl" for="cert">Certificate JSON</label>
<textarea class="codebox" id="cert" spellcheck="false" style="min-height:120px" placeholder='{"serial": "&hellip;", &hellip;}'></textarea>
<p style="margin-top:14px"><button class="go" id="check">Check this certificate</button></p>
</details>

<p style="color:var(--mut);font-size:15px;margin-top:26px">Prefer forms? The <a href="/verify/">web verifier</a> and <a href="/check/">certificate checker</a> do one job each. Prefer code? The <a href="/docs/api/">REST API and MCP</a> are the same service in machine shape.</p>
</div></div></section>
<script>
var API = """
    + json.dumps(API_BASE)
    + """;
var log = document.getElementById('log');
var history = [];
var keyInput = document.getElementById('apikey');
if (sessionStorage.getItem('axkey')) { keyInput.value = sessionStorage.getItem('axkey'); document.getElementById('remember').checked = true; }
document.getElementById('remember').addEventListener('change', function(){
  if (this.checked) sessionStorage.setItem('axkey', keyInput.value.trim());
  else sessionStorage.removeItem('axkey');
});
keyInput.addEventListener('change', function(){
  if (document.getElementById('remember').checked) sessionStorage.setItem('axkey', keyInput.value.trim());
});
function key(){ return keyInput.value.trim(); }
function bubble(cls, text){
  var d = document.createElement('div');
  d.style.margin = '14px 0';
  if (cls === 'user') { d.style.textAlign = 'right'; }
  var p = document.createElement('p');
  p.textContent = text;
  p.style.display = 'inline-block';
  p.style.margin = '0';
  p.style.padding = '10px 16px';
  p.style.borderRadius = '12px';
  p.style.maxWidth = '85%';
  p.style.textAlign = 'left';
  p.style.whiteSpace = 'pre-wrap';
  p.style.background = cls === 'user' ? 'var(--goldsoft)' : 'var(--wash)';
  p.style.border = '1px solid var(--line)';
  d.appendChild(p);
  log.appendChild(d);
  return d;
}
function factCard(f){
  var d = document.createElement('div');
  d.className = 'result show';
  var h = document.createElement('p');
  var b = document.createElement('span');
  b.className = 'badge ' + (f.kind === 'verdict' || f.kind === 'check' ? '' : 'b-warn');
  if (f.kind === 'verdict') {
    var passed = f.technical.indexOf('PASSED') >= 0;
    b.className = 'badge ' + (passed ? 'b-pass' : 'b-fail');
    b.textContent = passed ? 'PASSED' : 'FAILED';
  } else if (f.kind === 'check') {
    var ok = f.plain.indexOf('is VALID') >= 0;
    var rev = f.plain.indexOf('REVOKED') >= 0;
    b.className = 'badge ' + (rev ? 'b-fail' : ok ? 'b-pass' : 'b-warn');
    b.textContent = rev ? 'REVOKED' : ok ? 'VALID' : 'NOT VALID';
  } else { b.textContent = f.title.toUpperCase(); }
  h.appendChild(b);
  var plain = document.createElement('p');
  plain.textContent = f.plain;
  var tech = document.createElement('p');
  tech.style.color = 'var(--mut)';
  tech.style.fontSize = '13.5px';
  tech.style.fontFamily = 'var(--mono)';
  tech.textContent = f.technical;
  d.appendChild(h); d.appendChild(plain); d.appendChild(tech);
  log.appendChild(d);
  return d;
}
function certBlock(cert){
  if (!cert) return;
  var d = document.createElement('div');
  d.className = 'result show';
  var h = document.createElement('p');
  var s = document.createElement('strong');
  s.textContent = 'Certificate';
  h.appendChild(s);
  var pre = document.createElement('pre');
  pre.className = 'code';
  pre.textContent = JSON.stringify(cert, null, 2);
  d.appendChild(h); d.appendChild(pre);
  log.appendChild(d);
}
function speak(text){
  if (!document.getElementById('speak').checked) return;
  if (!('speechSynthesis' in window)) return;
  try { speechSynthesis.speak(new SpeechSynthesisUtterance(text)); } catch (e) {}
}
function speakTurn(body){
  var parts = [];
  (body.facts || []).forEach(function(f){ parts.push(f.plain); });
  if (body.explanation) parts.push(body.explanation);
  if (parts.length) speak(parts.join(' '));
}
function showTurn(body){
  (body.facts || []).forEach(factCard);
  if (body.result && body.result.certificate) certBlock(body.result.certificate);
  if (body.degraded) bubble('note', 'The explanation assistant is unavailable right now \\u2014 the service facts above are complete without it.');
  if (body.explanation) { bubble('assistant', body.explanation); history.push({role: 'assistant', content: body.explanation}); }
  speakTurn(body);
}
function showError(title, msg){
  factCard({kind: 'error', title: title, technical: title, plain: msg});
}
function headers(){ return {'Content-Type': 'application/json', 'X-Api-Key': key()}; }
function pollJob(jobId){
  var tries = 0;
  var iv = setInterval(function(){
    tries++;
    fetch(API + '/shell/jobs/' + encodeURIComponent(jobId), {headers: headers()})
    .then(function(r){ return r.json().then(function(j){ return {status: r.status, j: j}; }); })
    .then(function(x){
      if (x.status !== 200) { clearInterval(iv); return; }
      var st = x.j.job && x.j.job.status;
      if (st === 'done') {
        clearInterval(iv);
        factCard(x.j.fact);
        if (x.j.job.result && x.j.job.result.certificate) certBlock(x.j.job.result.certificate);
        speak(x.j.fact.plain);
      } else if (st === 'failed') { clearInterval(iv); factCard(x.j.fact); }
      else if (tries > 100) { clearInterval(iv); showError('STILL QUEUED', 'The queue is long. Your job id is ' + jobId + ' \\u2014 it stays yours and checkable with your key.'); }
    })
    .catch(function(){ /* transient; keep polling */ });
  }, 3000);
}
function sendTurn(payload, userText){
  if (!key()) { alert('Enter your API key first. No key yet? Email hello@axiom-code.com and we will issue one free.'); return; }
  if (userText) { bubble('user', userText); history.push({role: 'user', content: userText}); }
  payload.history = history.slice(-16);
  fetch(API + '/shell/turn', {method: 'POST', headers: headers(), body: JSON.stringify(payload)})
  .then(function(r){ return r.json().then(function(j){ return {status: r.status, j: j}; }); })
  .then(function(x){
    if (x.status === 401) { showError('INVALID KEY', 'That API key was not accepted. Check it, or email hello@axiom-code.com for a key.'); return; }
    if (x.status === 429) { showError('RATE LIMITED', 'Over 60 shell turns per minute for this key. Wait a moment and continue.'); return; }
    if (x.status !== 200) { showError('ERROR ' + x.status, (x.j && x.j.error) ? String(x.j.error) : 'The shell refused that turn.'); return; }
    showTurn(x.j);
    if (x.j.job_id) pollJob(x.j.job_id);
  })
  .catch(function(){
    showError('API UNREACHABLE', 'The AxiomCode API did not answer, so there is no result to show \\u2014 and nothing was submitted. Try again in a moment; if it persists, email hello@axiom-code.com.');
  });
}
document.getElementById('send').addEventListener('click', function(){
  var msg = document.getElementById('msg').value.trim();
  if (!msg) return;
  document.getElementById('msg').value = '';
  sendTurn({action: 'chat', message: msg}, msg);
});
document.getElementById('msg').addEventListener('keydown', function(e){
  if (e.key === 'Enter') document.getElementById('send').click();
});
document.getElementById('verify').addEventListener('click', function(){
  var code = document.getElementById('code').value;
  if (!code.trim()) { alert('Paste some Lean 4 code first.'); return; }
  sendTurn({action: 'verify', code: code, message: ''}, 'Please verify the code in the box.');
});
document.getElementById('check').addEventListener('click', function(){
  var raw = document.getElementById('cert').value.trim();
  if (!raw) { alert('Paste a certificate JSON first.'); return; }
  var cert; try { cert = JSON.parse(raw); } catch (e) { alert('That is not valid JSON.'); return; }
  sendTurn({action: 'check', certificate: cert, message: ''}, 'Please check the certificate I pasted.');
});
var SR = window.SpeechRecognition || window.webkitSpeechRecognition;
var micBtn = document.getElementById('mic');
if (SR) {
  micBtn.style.display = '';
  document.getElementById('voicenote').textContent = 'Voice input uses your browser\\u2019s speech recognition \\u2014 in Chrome, audio is processed by Google. It fills the message box; you review and press Send. Typing never leaves this page except to the AxiomCode API.';
  micBtn.addEventListener('click', function(){
    var rec = new SR();
    rec.lang = 'en-US';
    rec.interimResults = false;
    micBtn.textContent = 'Listening\\u2026';
    rec.onresult = function(ev){
      document.getElementById('msg').value = ev.results[0][0].transcript;
      micBtn.innerHTML = '&#127908; Speak instead';
    };
    rec.onerror = function(){ micBtn.innerHTML = '&#127908; Speak instead'; };
    rec.onend = function(){ micBtn.innerHTML = '&#127908; Speak instead'; };
    try { rec.start(); } catch (e) { micBtn.innerHTML = '&#127908; Speak instead'; }
  });
} else {
  document.getElementById('voicenote').textContent = 'Voice input is not available in this browser \\u2014 typing works exactly the same.';
}
</script>
""",
)
