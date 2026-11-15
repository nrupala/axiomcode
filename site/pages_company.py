"""Company pages: /about/ and /contact/ (Memo A, ruled 2026-11-14).

About is the minimal factual page in the house standard shape. Contact uses
the standard house form pattern (name / email / subject / message, honeypot
and time-trap anti-spam). The house pattern's receiving handler is a per-site
Worker pipeline (Worker /contact -> KV -> Apps Script -> Sheet + Gmail);
axiom-code.com has no such handler yet, so the form degrades honestly to the
email route and the endpoint is carried as a named open item in the P2 report
— no endpoint is invented here.
"""

from build import page
from pages_main import _chips

page(
    "/about/",
    "About",
    "About AxiomCode: a certification authority for software correctness, operated by 2351485 ALBERTA INC. (Alberta, Canada). What it is, who operates it, and what it does not claim.",
    f"""<section class="pagehead"><div class="wrap">
<h1>About AxiomCode</h1>
<p>A certification authority for software correctness — verification as evidence, not verification as opinion.</p>
</div></section>

<section class="block" style="padding-top:26px"><div class="wrap"><div class="prose" style="max-width:76ch">
<h2>What it is</h2>
<p>AxiomCode checks Lean 4 artefacts with a real toolchain — the Lean kernel is the only judge — and issues signed, revocable certificates that bind the artefact hash, the verdict, and the toolchain. It exists because the industry's usual answers to "is this code right?" are opinions: review, tests, audits. AxiomCode's answer is a record a stranger can check.</p>

<h2>The operator</h2>
<p>AxiomCode is owned and operated by <strong>2351485 ALBERTA INC.</strong>, a corporation registered in Alberta, Canada, which is also the intellectual-property owner of record for the service. The service is run from Canada; contact routes are on the <a href="/contact/">contact page</a>.</p>

<h2>What it does — and does not do</h2>
<ul>
<li>Today: Lean 4 artefacts, via the <a href="/docs/api/">REST API</a>, the <a href="/docs/mcp/">hosted MCP</a> endpoint, the web verifier, and the <a href="/ask/">Ask shell</a>. Current state of every surface: <a href="/status/">status</a>.</li>
<li>A verdict certifies the submitted artefact under the named toolchain. It does not certify intent, deployment, or the rest of your system — <a href="/docs/explanation/what-it-does-not-prove/">what verification does not prove</a>.</li>
<li>Smart-contract verification is in design and the offline verifier is not built; both are labelled as such on the status page and are not sold or implied.</li>
</ul>

<h2>How it is run</h2>
<p>Releases pass a recorded gate verdict, deploy, and then soak in production as release candidates; graduation is a gate decision, never a date passing quietly. The practice — gates, soak, certificate lifecycle, findings, error reporting — is published on the <a href="/practice/">practice page</a>, and the service record is append-only in the <a href="/changelog/">changelog</a>. Stated plainly: <strong>no external third-party audit of AxiomCode has been performed</strong>; the assurance case is the gate, the soak, and the public record.</p>

<h2>Service state</h2>
<p>REST API {_chips("rest_api")} &middot; Hosted MCP {_chips("hosted_mcp")} &middot; Billing {_chips("billing")} — generated from the <a href="/status/">canonical status source</a>.</p>
</div></div></section>
""",
)

page(
    "/contact/",
    "Contact",
    "Contact AxiomCode: support and API keys, product errors, sales, regulatory and privacy routes — operated by 2351485 ALBERTA INC.",
    """<section class="pagehead"><div class="wrap">
<h1>Contact</h1>
<p>Pick the route that matches your matter — each one lands with the people who own it. AxiomCode is operated by <strong>2351485 ALBERTA INC.</strong> (Alberta, Canada).</p>
</div></section>

<section class="block" style="padding-top:26px"><div class="wrap">
<div class="cards">
<div class="card"><h3>Support &amp; API keys</h3>
<p>Keys are issued by email while billing is paused; support questions take the same route.</p>
<p class="go"><a href="mailto:hello@axiom-code.com">hello@axiom-code.com</a></p></div>
<div class="card"><h3>Product errors</h3>
<p>Errors in the site or the service go to the product's own issue tracker — user-initiated only, nothing attached unless you choose to include it.</p>
<p class="go"><a href="https://github.com/nrupala/axiomcode/issues">GitHub Issues &rarr;</a></p></div>
<div class="card"><h3>Security</h3>
<p>Vulnerabilities never use the public form or the issue tracker. Use the disclosure route.</p>
<p class="go"><a href="/paperwork/security/">Security &amp; disclosure &rarr;</a></p></div>
<div class="card"><h3>Certificate incidents</h3>
<p>A certificate you believe is wrong, revoked in error, or mis-issued: contact us with the serial.</p>
<p class="go"><a href="mailto:hello@axiom-code.com?subject=Certificate%20incident">hello@axiom-code.com</a></p></div>
</div>

<div class="prose" style="max-width:76ch;margin-top:44px">
<h2>Write to us</h2>
<p style="color:var(--mut)">The standard form: name, email, subject, message. If the form cannot deliver for any reason, it will tell you and hand you a pre-addressed email instead — your text is never lost silently.</p>
<form id="cform" novalidate>
<label class="fl" for="cname">Your name</label>
<input type="text" id="cname" autocomplete="name" required>
<label class="fl" for="cemail">Your email</label>
<input type="email" id="cemail" autocomplete="email" required>
<label class="fl" for="csubject">Subject</label>
<select id="csubject">
<option value="support">Support &amp; API keys</option>
<option value="sales">Sales &amp; credit packs</option>
<option value="regulatory">Regulatory &amp; audit</option>
<option value="privacy">Privacy</option>
<option value="other">Other</option>
</select>
<label class="fl" for="cmsg">Message</label>
<textarea class="plainbox" id="cmsg" required></textarea>
<div class="hp" aria-hidden="true"><label>Leave this field empty<input type="text" id="cweb" tabindex="-1" autocomplete="off"></label></div>
<input type="hidden" id="cts" value="">
<div style="margin-top:20px"><button class="go" id="cgo" type="submit">Send message</button></div>
<div class="result" id="cresult" aria-live="polite"></div>
</form>
<p style="font-size:14px;color:var(--faint)">We reply from the address you give us. Form submissions carry only the fields above — no tracking, no third-party processors beyond delivery.</p>
</div>
</div></section>
<script>
const c$ = id => document.getElementById(id);
c$('cts').value = String(Date.now());
function cShow(html, ok){
  const r = c$('cresult');
  r.innerHTML = html; r.classList.add('show');
  r.style.borderColor = ok ? 'var(--greenline)' : 'var(--redline)';
}
c$('cform').addEventListener('submit', async (ev) => {
  ev.preventDefault();
  const name = c$('cname').value.trim(), email = c$('cemail').value.trim(),
        subject = c$('csubject').value, msg = c$('cmsg').value.trim();
  if (c$('cweb').value){ cShow('<strong>Thank you.</strong> Your message has been received.', true); return; }
  if (Date.now() - Number(c$('cts').value || 0) < 3000){ cShow('<strong>Thank you.</strong> Your message has been received.', true); return; }
  if (!name || !email || !msg){ cShow('<strong>Not sent.</strong> Name, email, and a message are all required.', false); return; }
  const btn = c$('cgo'); btn.disabled = true; btn.textContent = 'Sending…';
  const mailto = 'mailto:hello@axiom-code.com?subject=' + encodeURIComponent('Contact: ' + subject)
    + '&body=' + encodeURIComponent(msg + '\\n\\n— ' + name + ' <' + email + '>');
  try {
    const r = await fetch('/contact', {method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({name, email, subject, message: msg, ts: c$('cts').value})});
    if (r.ok){ cShow('<strong>Sent.</strong> Thank you — we reply to the email address you gave us.', true); c$('cform').reset(); }
    else { throw new Error('send failed'); }
  } catch(e) {
    cShow('<strong>The form could not deliver just now.</strong> Your message is safe: <a href="' + mailto + '">send it by email instead</a> — it opens pre-addressed with your text included.', false);
  }
  btn.disabled = false; btn.textContent = 'Send message';
});
</script>
""",
)
