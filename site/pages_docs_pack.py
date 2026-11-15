"""The P2 documentation pack: Start tutorials, Guides, Reference, Explanation,
and the seven role packs — AppDocStudio shape (Diátaxis structure, role packs
as the second axis).

Every page carries the standard meta block (type, audience, role packs,
version, last verified, source artefact, Markdown mirror). Facts derive from
the canonical sources and the gate-verified service record; nothing here
invents behaviour the service does not have. The Maintainers pack is an
evidence-on-request boundary: its structure is public, its internals are not.
"""

from build import page

DOCS_VERSION = "Docs set 2026-11-14"
LAST_VERIFIED = "2026-11-14"

# path -> meta, consumed by run.py to generate the Markdown mirrors.
DOCMETA: dict = {}

_NAV = [
    (
        "Start here",
        [
            ("First verification", "/docs/start/first-verification/"),
            ("First certificate check", "/docs/start/first-certificate-check/"),
            ("First MCP call", "/docs/start/first-mcp-call/"),
        ],
    ),
    (
        "Guides",
        [
            ("Write a verifiable artefact", "/docs/guides/write-a-verifiable-lean-artefact/"),
            ("Use the queue", "/docs/guides/use-the-queue/"),
            ("Check & revoke", "/docs/guides/check-and-revoke/"),
            ("Ask without letting it judge", "/docs/guides/use-ask-without-letting-it-judge/"),
            ("Integrate an agent", "/docs/guides/integrate-an-agent/"),
            ("Reconcile metering", "/docs/guides/reconcile-metering/"),
        ],
    ),
    (
        "Reference",
        [
            ("REST API", "/docs/api/"),
            ("MCP (hosted & local)", "/docs/mcp/"),
            ("Verdicts & errors", "/docs/reference/verdicts-and-errors/"),
            ("Certificates", "/docs/reference/certificates/"),
            ("Keys & limits", "/docs/reference/keys-and-limits/"),
            ("Status schema", "/docs/reference/status-schema/"),
            ("Changelog schema", "/docs/reference/changelog-schema/"),
        ],
    ),
    (
        "Explanation",
        [
            ("What verification proves", "/docs/explanation/what-verification-proves/"),
            ("What it does not prove", "/docs/explanation/what-it-does-not-prove/"),
            ("Certificate trust model", "/docs/explanation/certificate-trust-model/"),
            ("Queue & metering model", "/docs/explanation/queue-and-metering-model/"),
            ("Ask & AI boundaries", "/docs/explanation/ask-and-ai-boundaries/"),
        ],
    ),
    (
        "Role packs",
        [
            ("Guest", "/docs/roles/guest/"),
            ("Users", "/docs/roles/users/"),
            ("Developers", "/docs/roles/developers/"),
            ("Maintainers — on request", "/docs/roles/maintainers/"),
            ("Regulators", "/docs/roles/regulators/"),
            ("Admins", "/docs/roles/admins/"),
            ("Ops", "/docs/roles/ops/"),
        ],
    ),
]


def sidenav(active=""):
    parts = []
    for section, links in _NAV:
        items = []
        for label, href in links:
            cur = ' aria-current="page"' if href == active else ""
            items.append(f'<li><a href="{href}"{cur}>{label}</a></li>')
        parts.append(f"<h4>{section}</h4><ul>{''.join(items)}</ul>")
    return f'<nav class="sidenav" aria-label="Documentation">{"".join(parts)}</nav>'


def docmeta_html(path):
    m = DOCMETA[path]
    return (
        '<div class="docmeta">'
        f"<span>Type <b>{m['type']}</b></span>"
        f"<span>Audience <b>{m['audience']}</b></span>"
        f"<span>Role packs <b>{m['packs']}</b></span>"
        f"<span>Version <b>{DOCS_VERSION}</b></span>"
        f"<span>Last verified <b>{LAST_VERIFIED}</b></span>"
        f"<span>Source <b>{m['source']}</b></span>"
        f'<span><a href="{path}index.md">Markdown mirror</a></span>'
        "</div>"
    )


def docpage(path, title, desc, type_, audience, packs, source, body):
    DOCMETA[path] = {"type": type_, "audience": audience, "packs": packs, "source": source, "title": title}
    page(
        path,
        title,
        desc,
        f"""<section><div class="wrap"><div class="docslayout">
{sidenav(path)}
<div class="docbody">
{docmeta_html(path)}
{body}
</div>
</div></div></section>
""",
    )


# ================= Start here (tutorials) =================
docpage(
    "/docs/start/first-verification/",
    "Your first verification",
    "Tutorial: get a key, submit a Lean 4 artefact, and read the verdict, usage record, and trial semantics — the whole AxiomCode loop in five steps.",
    "Tutorial",
    "New users, evaluators",
    "Guest · Users",
    "Live service behaviour; the same loop as /verify/",
    """<h1>Your first verification</h1>
<p class="sub" style="font-size:18px">By the end of this page you will have submitted a real artefact to the real service and read a real verdict. About five minutes.</p>

<div class="steps">
<div class="step"><h3>1 · Get an API key</h3>
<p>Keys are issued by email while billing is paused. Write to <a href="mailto:hello@axiom-code.com?subject=API%20key%20request">hello@axiom-code.com</a> and you will receive a key (it starts <code class="inline">axk_</code>). There is no self-serve signup yet, and no card is needed: the first 10 verification cases on your key are the free trial.</p></div>

<div class="step"><h3>2 · Open the verifier</h3>
<p>Go to <a href="/verify/">/verify/</a> — or use the loop on the <a href="/#try">home page</a>, which is the same call. Paste your key into the API key field. The key is kept in page memory only, and is sent only to <code class="inline">api.axiom-code.com</code>.</p></div>

<div class="step"><h3>3 · Run the starter artefact</h3>
<p>The artefact box is prefilled with a small true theorem:</p>
<pre class="code">theorem add_comm_nat (a b : Nat) : a + b = b + a := Nat.add_comm a b</pre>
<p>Press <strong>Verify artefact</strong>. The service hashes the exact bytes, compiles them with the Lean toolchain, and the kernel checks the proof.</p></div>

<div class="step"><h3>4 · Read the verdict</h3>
<p>You get one of two verdicts — <span class="badge b-pass">PASSED</span> or <span class="badge b-fail">FAILED</span> — plus the artefact hash and a usage record (engine seconds, credits charged). If every proof slot is busy you get a queue position instead; the page polls for you. A run that ends before a verdict (timeout, refusal, failed queued job) is a <strong>NO VERDICT</strong> error outcome — never a verdict, and timeouts do not consume trial cases.</p></div>

<div class="step"><h3>5 · Understand the trial</h3>
<p>On the trial you receive the verdict and the usage record — <strong>never a certificate</strong>. The certificate is the product: our signature staked on the verdict. It is issued on paid verifications; credit packs are priced on the <a href="/pricing/">pricing page</a> and are not yet on sale.</p></div>
</div>

<h2>Next</h2>
<ul>
<li><a href="/docs/guides/write-a-verifiable-lean-artefact/">Write a verifiable Lean artefact</a> — what the engine accepts and rejects, and why.</li>
<li><a href="/docs/start/first-certificate-check/">Your first certificate check</a> — verify a certificate the way a relying party does.</li>
<li><a href="/docs/reference/verdicts-and-errors/">Verdicts &amp; errors</a> — every outcome, named.</li>
</ul>
""",
)

docpage(
    "/docs/start/first-certificate-check/",
    "Your first certificate check",
    "Tutorial: check a certificate the way a relying party does — signature verified in your browser against the published CA keys, revocation checked against the public list.",
    "Tutorial",
    "New users, relying parties",
    "Guest · Users · Regulators",
    "Live checker behaviour at /check/",
    """<h1>Your first certificate check</h1>
<p class="sub" style="font-size:18px">A certificate is only worth what a stranger can check. This page walks the check a relying party performs — no account, no trust in this website.</p>

<div class="steps">
<div class="step"><h3>1 · Get a certificate JSON</h3>
<p>Certificates are issued on paid verifications. If you are evaluating, ask the party who gave you the artefact for their certificate JSON — or read the field-by-field anatomy in the <a href="/docs/reference/certificates/">certificates reference</a> first.</p></div>

<div class="step"><h3>2 · Open the checker</h3>
<p>Go to <a href="/check/">/check/</a> and paste the certificate JSON. Checking runs <strong>in your browser</strong>: the page fetches the CA public keys from the API and verifies the signature locally.</p></div>

<div class="step"><h3>3 · Read the three answers</h3>
<p>The checker reports the signature (valid or not, under key ID <code class="inline">c731a5036812339d</code>), the validity window (certificates live 90 days), and the revocation state — checked against the <a href="https://api.axiom-code.com/revoked">public revocation list</a>. All three must be good before the certificate means anything.</p></div>

<div class="step"><h3>4 · Match the artefact</h3>
<p>The certificate binds an <code class="inline">artifact_hash</code>. Hash the artefact you were given (SHA-256) and compare: the certificate covers exactly those bytes, and no others. A changed byte is a different artefact with no certificate.</p></div>
</div>

<h2>Next</h2>
<ul>
<li><a href="/docs/guides/check-and-revoke/">Check &amp; revoke</a> — the full lifecycle, including what revocation means and when it happens.</li>
<li><a href="/docs/explanation/certificate-trust-model/">Certificate trust model</a> — what you are trusting, and what you are not asked to.</li>
</ul>
""",
)

docpage(
    "/docs/start/first-mcp-call/",
    "Your first MCP call",
    "Tutorial: connect an MCP client to the hosted endpoint, list the seven tools, and run a verification with the same key and trial semantics as REST.",
    "Tutorial",
    "Agent builders, developers",
    "Developers",
    "Hosted MCP service record (slice 1, live 2026-11-11)",
    """<h1>Your first MCP call</h1>
<p class="sub" style="font-size:18px">The hosted MCP endpoint gives agent clients the same engine, the same queue, and the same trial as the REST API — as tools.</p>

<div class="steps">
<div class="step"><h3>1 · Point your client at the endpoint</h3>
<p>The endpoint is <code class="inline">https://api.axiom-code.com/mcp/</code> — the trailing slash is canonical. Authenticate with the same API key you use for REST (keys are issued by email: <a href="mailto:hello@axiom-code.com?subject=API%20key%20request">hello@axiom-code.com</a>).</p></div>

<div class="step"><h3>2 · List the tools</h3>
<p>After the standard MCP handshake, <code class="inline">tools/list</code> returns seven tools: <code class="inline">verify</code>, <code class="inline">job_status</code>, <code class="inline">check_certificate</code>, <code class="inline">revoked</code>, <code class="inline">health</code>, <code class="inline">usage_report</code>, <code class="inline">pricing</code>. The full contract is in the <a href="/docs/mcp/">MCP reference</a>.</p></div>

<div class="step"><h3>3 · Call verify</h3>
<p>Call <code class="inline">verify</code> with a Lean 4 artefact. You receive the same response shape as REST: verdict, artefact hash, usage record — and, when the proof slots are busy, a job to poll with <code class="inline">job_status</code>. Trial semantics are identical: the first 10 cases per key return verdicts and usage, never a certificate.</p></div>

<div class="step"><h3>4 · Prefer REST when there is no agent</h3>
<p>MCP is a door, not a different service. If your caller is a script or a backend rather than an agent client, the <a href="/docs/api/">REST API</a> is the simpler contract — same key, same verdicts.</p></div>
</div>

<h2>Next</h2>
<ul>
<li><a href="/docs/guides/integrate-an-agent/">Integrate an agent</a> — key handling, queue discipline, and error mapping for agent callers.</li>
<li><a href="/docs/mcp/">MCP reference</a> — all seven tools, plus the local MCP server.</li>
</ul>
""",
)


# ================= Guides =================
docpage(
    "/docs/guides/write-a-verifiable-lean-artefact/",
    "Write a verifiable Lean artefact",
    "Guide: what the engine accepts and rejects — self-contained single-file Lean 4, and the rejection rules for sorry, admit, native code, and vacuous proofs.",
    "Guide",
    "Users, developers",
    "Users · Developers",
    "How It Works (gate-verified copy); engine rejection rules",
    """<h1>Write a verifiable Lean artefact</h1>
<p class="sub" style="font-size:18px">An artefact is a single, self-contained Lean 4 file whose proofs the kernel can check. This guide covers the shape the engine accepts — and the four rejection rules that keep certificates meaningful.</p>

<h2>The shape</h2>
<ul>
<li><strong>One file, self-contained.</strong> Everything the artefact needs must be in the submission; external files and network fetches are not part of the checked bytes.</li>
<li><strong>Lean 4.</strong> The toolchain is named on every result and certificate (currently the <code class="inline">lean4-4.9.1</code> line); a verdict is always relative to the toolchain that produced it.</li>
<li><strong>Size limit 256 KB.</strong> Larger submissions are refused with 413 before any checking begins.</li>
<li><strong>State the claim as a theorem.</strong> The engine checks proofs of stated propositions. Code without a stated, proved proposition has nothing to certify.</li>
</ul>

<h2>The rejection rules</h2>
<p>The engine rejects — loudly, as a FAILED outcome, never silently — artefacts that cheat the kernel:</p>
<ul>
<li><code class="inline">sorry</code> and <code class="inline">admit</code>: an admitted gap is not a proof.</li>
<li><strong>Native-code shortcuts</strong> that bypass kernel checking of the claim.</li>
<li><strong>Vacuous builds</strong>: statements engineered to be trivially true rather than true of the thing you care about. The kernel checks the statement you wrote — write the statement you mean (see <a href="/docs/explanation/what-it-does-not-prove/">what verification does not prove</a>).</li>
<li><strong>Broken proofs</strong>: anything the kernel does not accept.</li>
</ul>

<h2>A minimal pattern</h2>
<pre class="code">theorem add_comm_nat (a b : Nat) : a + b = b + a := Nat.add_comm a b</pre>
<p>Small, stated, proved. Grow from patterns like this: name the property, prove it from the standard library or your own lemmas in the same file, and submit the whole file as one artefact.</p>

<h2>Before you submit</h2>
<ul>
<li>Compile locally with the same Lean line if you can — a local failure is a free failure.</li>
<li>Check the statement, not just the proof: the certificate will bind <em>this</em> statement.</li>
<li>Keep the artefact bytes stable after verification: any change is a new artefact (a new hash, a new verification).</li>
</ul>
""",
)

docpage(
    "/docs/guides/use-the-queue/",
    "Use the queue",
    "Guide: how queued verifications work — 202 responses, positions, polling, job ownership, and what a failed queued job means.",
    "Guide",
    "Users, developers",
    "Users · Developers",
    "Live API behaviour; Ask/verify client behaviour",
    """<h1>Use the queue</h1>
<p class="sub" style="font-size:18px">Proof checking is slot-bound: when every slot is busy, submissions queue instead of failing. This guide is the queue contract.</p>

<h2>How a queued run looks</h2>
<ul>
<li><code class="inline">POST /verify</code> answers <strong>202</strong> with <code class="inline">{"status": "queued", "job_id": "…", "position": N}</code>.</li>
<li>Poll <code class="inline">GET /verify/jobs/{job_id}</code> with the <strong>same API key</strong> — a job belongs to the key that submitted it. While queued or running, the answer stays 202 with the current position.</li>
<li>When the run completes, the poll answers <strong>200</strong> with the ordinary result: verdict, artefact hash, usage record, and — on paid verifications — the certificate.</li>
<li>The browser clients (the home loop, <a href="/verify/">/verify/</a>, <a href="/ask/">Ask</a>) poll every 3 seconds for you.</li>
</ul>

<h2>What can go wrong</h2>
<ul>
<li><strong>A queued job can fail</strong> — for example the artefact errors in a way only the run itself reveals. The poll then reports the failure as a <strong>NO VERDICT</strong> outcome: the job ended, nothing was decided, nothing is certified.</li>
<li><strong>Timeouts are NO VERDICT too</strong> (504 on a synchronous run): the run exceeded its time limit. Timeouts do not consume trial cases and are not charged.</li>
<li><strong>Losing the job_id loses the result handle.</strong> Record it at submission time; there is no job listing endpoint.</li>
</ul>

<h2>Driving it well</h2>
<ul>
<li>Submit once, poll patiently: re-submitting the same artefact creates a second job, not a faster first one.</li>
<li>Identical bytes hash identically — the <code class="inline">artifact_hash</code> is your idempotency key when reconciling results (see <a href="/docs/guides/reconcile-metering/">reconcile metering</a>).</li>
</ul>
""",
)

docpage(
    "/docs/guides/check-and-revoke/",
    "Check & revoke",
    "Guide: the certificate lifecycle from a relying party's side — checking, validity windows, renewal by re-verification, and public revocation.",
    "Guide",
    "Users, relying parties",
    "Users · Regulators",
    "Certificate Policy & CPS; practice page §5",
    """<h1>Check &amp; revoke</h1>
<p class="sub" style="font-size:18px">Certificates are short-lived, checkable by anyone, and revocable in public. This guide covers the lifecycle from the relying party's side; the governing document is the <a href="/paperwork/certificate-policy/">Certificate Policy &amp; CPS</a>.</p>

<h2>Checking</h2>
<ul>
<li>Paste the certificate JSON into <a href="/check/">/check/</a>: the signature is verified in your browser against the published <a href="https://api.axiom-code.com/.well-known/axiomcode-keys.json">CA public keys</a>.</li>
<li>Confirm the validity window: certificates are valid for <strong>90 days</strong> from issue.</li>
<li>Confirm the serial is absent from the <a href="https://api.axiom-code.com/revoked">public revocation list</a> (the checker does this for you).</li>
<li>Confirm the <code class="inline">artifact_hash</code> matches the artefact in front of you.</li>
</ul>

<h2>Renewal is re-verification</h2>
<p>There is no extension stamp. When a certificate approaches expiry, submit the artefact again: a fresh verification runs and a fresh certificate is issued on the new result, with a new validity window.</p>

<h2>Revocation</h2>
<ul>
<li>A certificate is revoked when its verdict can no longer be stood behind — for example, a toolchain defect that invalidates the check it records.</li>
<li>Revocation is <strong>public and permanent</strong>: the serial goes on the revocation list, an incident note is published in the <a href="/changelog/">changelog</a>, and affected artefacts are re-verified at our expense.</li>
<li>There is no silent un-verification: a revoked certificate remains visible as revoked, with its history intact.</li>
</ul>
""",
)

docpage(
    "/docs/guides/use-ask-without-letting-it-judge/",
    "Ask without letting it judge",
    "Guide: how to use the Ask shell well — what the model does, what it never does, and how to read its answers against the fact blocks.",
    "Guide",
    "Users, evaluators",
    "Users · Guest",
    "Slice-2 shell design record; practice page",
    """<h1>Ask without letting it judge</h1>
<p class="sub" style="font-size:18px">Ask is a shell over the same verify calls, with a model that explains. The architecture keeps the model away from the verdict; this guide keeps your reading habits the same way.</p>

<h2>Who does what</h2>
<ul>
<li><strong>The engine judges.</strong> Verdicts come from the Lean kernel through the same callables the API uses.</li>
<li><strong>Code renders the facts.</strong> Verdict, artefact hash, usage, and certificate facts on the Ask page are rendered in code from the actual API payload — the model cannot alter a digit.</li>
<li><strong>The model explains.</strong> It puts the result into words, suggests next steps, and answers questions about the outcome. Its words are commentary, never evidence.</li>
</ul>

<h2>Reading Ask well</h2>
<ul>
<li>Trust the fact block; enjoy the explanation. If the two ever seem to differ, the fact block is the record — and the difference is worth an <a href="https://github.com/nrupala/axiomcode/issues">error report</a>.</li>
<li>Explanations are <strong>degraded-first</strong>: if the model lane is slow or down, the facts still arrive, without an explanation. A missing explanation is a known residual of the current soak, not a failed verification.</li>
<li>Ask keeps your key in page memory by default; nothing about your artefact is sent anywhere except the verification API.</li>
</ul>

<h2>What Ask is not</h2>
<p>Ask is not a second opinion and not an auditor. It will not certify intent, review your specification for meaning, or find the bug your proof forgot to state. For the bounds, read <a href="/docs/explanation/ask-and-ai-boundaries/">Ask &amp; AI boundaries</a>.</p>
""",
)

docpage(
    "/docs/guides/integrate-an-agent/",
    "Integrate an agent",
    "Guide: wiring an agent client to AxiomCode — REST vs MCP, key handling, queue discipline, and mapping every outcome to agent behaviour.",
    "Guide",
    "Agent builders, developers",
    "Developers",
    "REST + hosted MCP service records",
    """<h1>Integrate an agent</h1>
<p class="sub" style="font-size:18px">AxiomCode is built to be called by agents: one key, two doors, boolean verdicts, and error outcomes an agent can act on without guessing.</p>

<h2>Choose the door</h2>
<ul>
<li><strong>MCP</strong> (<a href="/docs/mcp/">reference</a>) when the caller is an agent client that already speaks tools: seven tools, same semantics.</li>
<li><strong>REST</strong> (<a href="/docs/api/">reference</a>) for everything else — scripts, backends, CI. Same key, same queue, same trial.</li>
</ul>

<h2>Key handling</h2>
<ul>
<li>One key per integration; keys are issued by email and shown once — store the key in your secret manager, never in prompts, artefacts, or logs.</li>
<li>The service stores only a hash of your key. A lost key is replaced, not recovered.</li>
</ul>

<h2>Outcome mapping</h2>
<table class="spec">
<tr><th>Outcome</th><th>Agent behaviour</th></tr>
<tr><td>200 + PASSED</td><td>Proceed; record the artefact hash and (paid) the certificate serial.</td></tr>
<tr><td>200 + FAILED</td><td>Stop the line: the artefact did not pass. Surface the usage record; do not retry the same bytes expecting a different verdict.</td></tr>
<tr><td>202 queued</td><td>Poll <code class="inline">job_status</code> / the job URL with the same key until 200 or a terminal error.</td></tr>
<tr><td>402</td><td>Trial exhausted and no balance: a commercial state, not a fault. Escalate to the key's owner.</td></tr>
<tr><td>429 / 413 / 401</td><td>Slow down / shrink the artefact / fix the key. All three are NO VERDICT.</td></tr>
<tr><td>504 / failed job</td><td>NO VERDICT: nothing was decided. A retry is legitimate; a conclusion is not.</td></tr>
</table>

<h2>Discipline</h2>
<ul>
<li>Never let the agent paraphrase a verdict into a stronger claim: PASSED binds the submitted bytes under the named toolchain, nothing more (<a href="/docs/explanation/what-verification-proves/">what verification proves</a>).</li>
<li>Record <code class="inline">artifact_hash</code> with every outcome — it is the join key between your logs, our usage records, and any certificate.</li>
</ul>
""",
)

docpage(
    "/docs/guides/reconcile-metering/",
    "Reconcile metering",
    "Guide: reading usage records and attempts — engine seconds, credits at 0.9 per second, what timeouts and refusals cost, and matching records by artefact hash.",
    "Guide",
    "Users, developers, admins",
    "Users · Developers · Admins",
    "Pricing page; usage record shape from the live API",
    """<h1>Reconcile metering</h1>
<p class="sub" style="font-size:18px">Every verification returns a usage record. This guide explains how the numbers are formed so your books and ours agree to the credit.</p>

<h2>The model</h2>
<ul>
<li>Metering is <strong>engine compute time</strong>: 0.9 credits per second, 1 credit = $0.01. Wall-clock queue time is not metered.</li>
<li>A verification may take more than one <strong>attempt</strong> inside the engine; the usage record lists attempts with their elapsed seconds and credits charged. The charge is the sum of attempts.</li>
<li>The trial uses the same metering — trial cases show real usage records with real numbers; they simply are not billed.</li>
</ul>

<h2>What does not charge</h2>
<ul>
<li><strong>Timeouts (504)</strong>: NO VERDICT, no charge, no trial case consumed.</li>
<li><strong>Refusals</strong> (401, 413, 429) and <strong>402</strong>: no run happened; no charge.</li>
<li><strong>Failed queued jobs</strong>: NO VERDICT outcomes are not charged as verifications.</li>
</ul>

<h2>Reconciling</h2>
<ul>
<li>Join on <code class="inline">artifact_hash</code>: your submission log, the usage record, and the certificate (paid) all carry it.</li>
<li>Credits are charged against the pack balance of the key that submitted; the MCP <code class="inline">usage_report</code> tool returns the same records for agent-side reconciliation.</li>
<li>Disputes: report through <a href="/contact/">contact</a> with the artefact hash and the job or serial involved — the append-only service record and the usage log settle the question.</li>
</ul>
<p>Billing is currently <strong>paused</strong> (packs not yet on sale); metering runs and records regardless, so the numbers you see on the trial are the numbers that will bill.</p>
""",
)


# ================= Reference =================
docpage(
    "/docs/mcp/",
    "MCP — hosted & local",
    "Reference: the hosted MCP endpoint (seven tools, same key, queue, and trial as REST) and the local MCP server that ships in the repository — two separate contracts.",
    "Reference",
    "Developers, agent builders",
    "Developers",
    "Hosted MCP service record (slice 1); repository MCP server",
    """<h1>MCP — hosted &amp; local</h1>
<p class="sub" style="font-size:18px">Two MCP contracts exist, and they are not the same surface: the hosted endpoint (seven tools) and the local server in the repository (two tools). Both reach the same engine.</p>

<h2>Hosted MCP</h2>
<p>Endpoint: <code class="inline">https://api.axiom-code.com/mcp/</code> — the trailing slash is canonical. Authentication: the same API key as REST. Semantics: the same queue and the same trial (first 10 cases per key: verdicts and usage, no certificates).</p>
<table class="spec">
<tr><th>Tool</th><th>What it does</th></tr>
<tr><td><code class="inline">verify</code></td><td>Submit a Lean 4 artefact — the MCP form of <code class="inline">POST /verify</code>. Returns the verdict, artefact hash, and usage record, or a queued job.</td></tr>
<tr><td><code class="inline">job_status</code></td><td>Poll a queued job — the MCP form of <code class="inline">GET /verify/jobs/{id}</code>.</td></tr>
<tr><td><code class="inline">check_certificate</code></td><td>Check a certificate — the MCP form of <code class="inline">POST /check</code>.</td></tr>
<tr><td><code class="inline">revoked</code></td><td>The public revocation list.</td></tr>
<tr><td><code class="inline">health</code></td><td>Service health.</td></tr>
<tr><td><code class="inline">usage_report</code></td><td>Usage records for the calling key — the reconciliation view (see <a href="/docs/guides/reconcile-metering/">reconcile metering</a>).</td></tr>
<tr><td><code class="inline">pricing</code></td><td>The current pricing and billing state, as published on the <a href="/pricing/">pricing page</a>.</td></tr>
</table>
<p>Lifecycle: the hosted endpoint is <strong>live and in soak</strong> with the REST API — see the <a href="/status/">status page</a> for the current record.</p>

<h2 id="local-mcp">Local MCP</h2>
<p>An MCP server also ships in the <a href="https://github.com/nrupala/axiomcode">AxiomCode repository</a> for local use over stdio. It exposes two tools — <code class="inline">verify</code> and <code class="inline">check_certificate</code> — and calls the hosted API with your key. It is a client-side convenience with its own, smaller contract; it is not a local verification engine, and it issues nothing locally.</p>

<h2>Which one do you want?</h2>
<ul>
<li>Agent platform that can call a remote endpoint: <strong>hosted</strong> (all seven tools).</li>
<li>Desktop agent client that speaks stdio MCP: <strong>local</strong> (verify + check, zero hosting).</li>
<li>No agent at all: the <a href="/docs/api/">REST API</a> is the same service with the simplest contract.</li>
</ul>
""",
)

docpage(
    "/docs/reference/verdicts-and-errors/",
    "Verdicts & errors",
    "Reference: the complete outcome taxonomy — PASSED, FAILED, and every NO VERDICT error outcome with its status code and its effect on trial cases and balance.",
    "Reference",
    "Developers, users",
    "Developers · Users",
    "Certificate Policy §4.2; live API behaviour",
    """<h1>Verdicts &amp; errors</h1>
<p class="sub" style="font-size:18px">Verdicts are boolean. Everything else is an error outcome with a name, a code, and a defined effect — so a refusal can never be mistaken for a result.</p>

<h2>Verdicts (200)</h2>
<table class="spec">
<tr><th>Verdict</th><th>Meaning</th><th>Certificate</th></tr>
<tr><td><strong>PASSED</strong></td><td>The artefact compiled and every proof checked under the stated toolchain.</td><td>Issued on paid verifications.</td></tr>
<tr><td><strong>FAILED</strong></td><td>The artefact was checked and did not pass — proof failure, or rejection under the engine rules (<code class="inline">sorry</code>, <code class="inline">admit</code>, native-code shortcuts, vacuous builds).</td><td>Issued on paid verifications — a FAILED certificate records the verdict honestly.</td></tr>
</table>
<p>Trial runs (first 10 cases per key) return verdicts and usage records with <strong>no certificate</strong>, whichever verdict.</p>

<h2>NO VERDICT outcomes</h2>
<table class="spec">
<tr><th>Code</th><th>Outcome</th><th>Effect</th></tr>
<tr><td>202</td><td>Queued — every proof slot busy. Not an error: poll the job.</td><td>Resolves to a verdict or a terminal NO VERDICT.</td></tr>
<tr><td>401</td><td>Missing or invalid API key.</td><td>No run; nothing consumed.</td></tr>
<tr><td>402</td><td>Payment required — trial exhausted and no credit balance.</td><td>No run; nothing consumed.</td></tr>
<tr><td>413</td><td>Artefact over the 256 KB limit.</td><td>No run; nothing consumed.</td></tr>
<tr><td>429</td><td>Rate or concurrency refusal.</td><td>No run; retry after slowing down.</td></tr>
<tr><td>504</td><td>Engine timeout — the run exceeded its time limit.</td><td>No charge; no trial case consumed.</td></tr>
<tr><td>—</td><td>Queued job failed before a verdict.</td><td>Reported on the job poll; nothing certified.</td></tr>
</table>

<h2>The rule</h2>
<p>A certificate exists only where a verdict exists. NO VERDICT outcomes produce no certificate, ever — that asymmetry is the integrity of the system, stated in the <a href="/paperwork/certificate-policy/">Certificate Policy</a> (§4.2) and repeated on the <a href="/practice/">practice page</a>.</p>
""",
)

docpage(
    "/docs/reference/certificates/",
    "Certificates",
    "Reference: the certificate record field by field — artefact hash, verdict, toolchain, issuer, serial, validity window, signature — and the lifecycle rules.",
    "Reference",
    "Users, developers, relying parties",
    "Users · Developers · Regulators",
    "Certificate Policy & CPS; live /check/ behaviour",
    """<h1>Certificates</h1>
<p class="sub" style="font-size:18px">A certificate is a signed JSON record. This page is its anatomy; the governing rules are the <a href="/paperwork/certificate-policy/">Certificate Policy &amp; CPS</a>.</p>

<h2>Fields</h2>
<table class="spec">
<tr><th>Field</th><th>Meaning</th></tr>
<tr><td><code class="inline">artifact_hash</code></td><td>SHA-256 of the exact bytes that were checked. Binds the certificate to one artefact and no other.</td></tr>
<tr><td><code class="inline">verified</code></td><td>The boolean verdict: <code class="inline">true</code> = PASSED, <code class="inline">false</code> = FAILED. Paid verifications receive a certificate either way.</td></tr>
<tr><td><code class="inline">toolchain</code></td><td>The exact toolchain that ran the check. A verdict is always relative to its toolchain.</td></tr>
<tr><td><code class="inline">issuer</code></td><td>The issuing CA (AxiomCode CA).</td></tr>
<tr><td><code class="inline">serial</code></td><td>The certificate's unique serial — the handle used by the revocation list.</td></tr>
<tr><td><code class="inline">issued</code> / <code class="inline">expires</code></td><td>The validity window: 90 days from issue.</td></tr>
<tr><td><code class="inline">signature</code></td><td>The CA's Ed25519 signature over the record, verifiable against the published CA keys (production key ID <code class="inline">c731a5036812339d</code>).</td></tr>
</table>

<h2>Lifecycle rules</h2>
<ul>
<li><strong>Issuance:</strong> on completed paid verifications only. Trial runs never receive certificates; NO VERDICT outcomes never receive certificates.</li>
<li><strong>Checking:</strong> by anyone, at <a href="/check/">/check/</a> (in-browser) or via <code class="inline">POST /check</code> — signature, window, and revocation state.</li>
<li><strong>Renewal:</strong> re-verification. Submit again; a fresh certificate is issued on the new result.</li>
<li><strong>Revocation:</strong> public and permanent, by serial, on the <a href="https://api.axiom-code.com/revoked">revocation list</a>, with a changelog incident note. See <a href="/docs/guides/check-and-revoke/">check &amp; revoke</a>.</li>
</ul>
""",
)

docpage(
    "/docs/reference/keys-and-limits/",
    "Keys & limits",
    "Reference: API keys (issuance, hash-only storage, replacement) and the service limits — 256 KB artefacts, the 10-case trial, queue and rate behaviour.",
    "Reference",
    "Users, developers, admins",
    "Users · Developers · Admins",
    "Live service behaviour; status source",
    """<h1>Keys &amp; limits</h1>
<p class="sub" style="font-size:18px">One key unlocks every door — REST, hosted MCP, the web verifier, the checker, and Ask. This page is the key contract and the limits that apply to it.</p>

<h2>Keys</h2>
<ul>
<li><strong>Issuance:</strong> by email while billing is paused — write to <a href="mailto:hello@axiom-code.com?subject=API%20key%20request">hello@axiom-code.com</a>. Keys begin <code class="inline">axk_</code>.</li>
<li><strong>Storage:</strong> the service stores only a <strong>hash</strong> of your key. We cannot show you your key again; a lost key is replaced, not recovered.</li>
<li><strong>Use:</strong> send it as the <code class="inline">X-Api-Key</code> header (REST) or your MCP client's credential. The browser pages keep it in page memory only.</li>
<li><strong>Scope:</strong> a key owns its jobs and its usage records; job polls require the submitting key.</li>
</ul>

<h2>Limits</h2>
<table class="spec">
<tr><th>Limit</th><th>Value</th><th>On breach</th></tr>
<tr><td>Artefact size</td><td>256 KB</td><td>413 — NO VERDICT, nothing consumed</td></tr>
<tr><td>Trial</td><td>First 10 verification cases per key</td><td>402 once exhausted with no balance</td></tr>
<tr><td>Proof slots</td><td>Bounded concurrency</td><td>202 queueing (not a refusal)</td></tr>
<tr><td>Rate</td><td>Per-key request pacing</td><td>429 — NO VERDICT, retry slower</td></tr>
<tr><td>Run time</td><td>Per-run engine time limit</td><td>504 — NO VERDICT, no charge, no trial case consumed</td></tr>
</table>
<p>Limits are service-protection facts, published here and reflected in the <a href="/docs/reference/verdicts-and-errors/">outcome taxonomy</a>. Current availability of every surface is on the <a href="/status/">status page</a>.</p>
""",
)

docpage(
    "/docs/reference/status-schema/",
    "Status schema",
    "Reference: the status.json document — meta and surfaces, availability and lifecycle vocabularies, and how the generated surfaces relate to the canonical source.",
    "Reference",
    "Developers, ops, regulators",
    "Developers · Ops · Regulators",
    "site/status_data.py (canonical source)",
    """<h1>Status schema</h1>
<p class="sub" style="font-size:18px"><a href="/status.json">status.json</a> is the machine-readable form of the <a href="/status/">status page</a> — both generated from one canonical source, along with the service record's <code class="inline">surfaces[]</code> and the llms.txt status section.</p>

<h2>Document shape</h2>
<pre class="code">{
  "meta": {
    "service": "AxiomCode",
    "as_of": "2026-11-14",
    "timezone": "America/Edmonton",
    "source": "site/status_data.py",
    "status_page": "https://axiom-code.com/status/"
  },
  "surfaces": [ { "surface_id": "rest_api", "name": "REST API",
    "availability": "live", "lifecycle": "in_soak",
    "public_since": "2026-11-09", "graduates_on": "2026-11-16",
    "canonical_url": "https://api.axiom-code.com",
    "summary": "…", "evidence": [{"label": "…", "url": "…"}],
    "known_limits": ["…"] } ]
}</pre>

<h2>Vocabularies</h2>
<table class="spec">
<tr><th>Field</th><th>Values</th></tr>
<tr><td><code class="inline">availability</code></td><td><code class="inline">live</code> · <code class="inline">paused</code> · <code class="inline">unavailable</code> — can you use it now?</td></tr>
<tr><td><code class="inline">lifecycle</code></td><td><code class="inline">live</code> · <code class="inline">paused</code> · <code class="inline">in_soak</code> · <code class="inline">in_design</code> · <code class="inline">not_built</code> — where it stands in its release process.</td></tr>
</table>
<p>The two fields are independent by design: <code class="inline">live</code> + <code class="inline">in_soak</code> is the normal state of a recent release. <code class="inline">graduates_on</code> is a scheduled decision date, present only while a soak is open; the graduation itself is recorded in the <a href="/changelog/">changelog</a> when the gate decides.</p>

<h2>Rules for consumers</h2>
<ul>
<li>Read <code class="inline">meta.as_of</code> before trusting a cached copy.</li>
<li>Absence is information: a surface not in the list does not exist; an unavailable surface is listed, never omitted.</li>
<li>CI drift checks fail our build when any rendering disagrees with the source — if you ever catch a disagreement, that is a reportable error (<a href="https://github.com/nrupala/axiomcode/issues">GitHub Issues</a>).</li>
</ul>
""",
)

docpage(
    "/docs/reference/changelog-schema/",
    "Changelog schema",
    "Reference: the changelog document — entry fields, categories, the append-only rule, and the JSON and RSS forms of the service record.",
    "Reference",
    "Developers, ops, regulators",
    "Developers · Ops · Regulators",
    "site/changelog_data.py (canonical source)",
    """<h1>Changelog schema</h1>
<p class="sub" style="font-size:18px">The <a href="/changelog/">changelog</a> is the append-only service record. It is published as HTML, <a href="/changelog.json">JSON</a>, and <a href="/changelog.rss.xml">RSS</a> from one source.</p>

<h2>Entry fields</h2>
<table class="spec">
<tr><th>Field</th><th>Meaning</th></tr>
<tr><td><code class="inline">id</code></td><td>Stable, unique entry ID — the anchor other pages link to (<code class="inline">/changelog/#&lt;id&gt;</code>).</td></tr>
<tr><td><code class="inline">date</code></td><td>The date the recorded change took effect.</td></tr>
<tr><td><code class="inline">title</code> / <code class="inline">body</code></td><td>What changed, in plain language.</td></tr>
<tr><td><code class="inline">category</code></td><td>One of: Added · Changed · Fixed · Finding · Incident · Status · Documentation · Removed.</td></tr>
<tr><td><code class="inline">surfaces</code></td><td>The surfaces the entry concerns.</td></tr>
<tr><td><code class="inline">effect</code></td><td>What the change means for relying parties.</td></tr>
<tr><td><code class="inline">evidence</code></td><td>Labelled links to the artefacts that prove the entry.</td></tr>
<tr><td><code class="inline">refs</code></td><td>Finding IDs, gate records, and other cross-references.</td></tr>
<tr><td><code class="inline">disposition</code></td><td>Where the matter stands — live, closed, carried, or pending a named decision.</td></tr>
</table>

<h2>The append-only rule</h2>
<ul>
<li>Entries are never silently edited. A correction is a new entry (or a dated correction note appended to the original); the original remains readable.</li>
<li>Scheduled events (for example graduations) appear only when they happen — plans live on the <a href="/status/">status page</a>, history lives here.</li>
<li>Findings and incidents are first-class categories, not footnotes: the record includes what went wrong, not only what shipped.</li>
</ul>
""",
)


# ================= Explanation =================
docpage(
    "/docs/explanation/what-verification-proves/",
    "What verification proves",
    "Explanation: the exact claim a PASSED verdict makes — kernel acceptance of the submitted bytes under a named toolchain — and why the certificate binds what it binds.",
    "Explanation",
    "All audiences",
    "Guest · Users · Regulators",
    "Certificate Policy; How It Works (gate-verified copy)",
    """<h1>What verification proves</h1>
<p class="sub" style="font-size:18px">A PASSED verdict makes one claim, stated exactly: the submitted artefact compiled under the stated toolchain, and the Lean kernel accepted its proofs.</p>

<h2>Why that claim is strong</h2>
<ul>
<li><strong>The kernel is the judge.</strong> Lean's kernel is a small, conservative checker. A proof the kernel accepts is not an opinion, a test sample, or a reviewer's impression — it is a machine-checked derivation.</li>
<li><strong>The claim is about exact bytes.</strong> The artefact hash binds the verdict to the precise submission. There is no drift between "what was checked" and "what the certificate describes".</li>
<li><strong>The claim names its toolchain.</strong> Verification is relative to the checker; the certificate records which toolchain ran, so the claim can be re-examined when toolchains change.</li>
<li><strong>The claim is signed and revocable.</strong> The CA stakes its name on the record — and can publicly withdraw it if the ground shifts (a toolchain defect, a mis-issuance), which is what makes the signature worth more than the JSON.</li>
</ul>

<h2>Why certificates bind fields, not vibes</h2>
<p>Each bound field answers an attack on the claim: the hash answers "different code"; the toolchain answers "checked by what?"; the validity window answers "is this still fresh?"; the serial answers "has it been withdrawn?"; the signature answers "who says so?". Remove a field and the corresponding doubt returns. That is why a certificate is a record, not a badge — and why checking one is a mechanical act any relying party can perform (<a href="/docs/start/first-certificate-check/">first certificate check</a>).</p>

<h2>The honest boundary</h2>
<p>The claim is narrow on purpose. Its complement — everything a PASSED verdict does <em>not</em> say — has its own page: <a href="/docs/explanation/what-it-does-not-prove/">what verification does not prove</a>. Read both before relying on either.</p>
""",
)

docpage(
    "/docs/explanation/what-it-does-not-prove/",
    "What verification does not prove",
    "Explanation: the bounds of a verdict — intent, specification quality, deployment, and the rest of the system are outside the claim, by design.",
    "Explanation",
    "All audiences",
    "Guest · Users · Regulators",
    "How It Works (gate-verified copy); Certificate Policy",
    """<h1>What verification does not prove</h1>
<p class="sub" style="font-size:18px">A verdict certifies the artefact that was submitted. These are the things it does not certify — stated as plainly as the claim itself.</p>

<ul>
<li><strong>Intent.</strong> The kernel checks the statement you wrote, not the statement you meant. A proof of the wrong theorem passes exactly as cleanly as a proof of the right one. Specification review remains a human duty.</li>
<li><strong>The rest of the system.</strong> Code that was not submitted is not covered: callers, configuration, infrastructure, and the humans operating them.</li>
<li><strong>Deployment.</strong> A certificate binds submitted bytes. Whether the deployed system runs those bytes is a separate fact, established by your own pipeline discipline (hash comparison is the bridge).</li>
<li><strong>Specification quality.</strong> A vacuous or trivial statement can be proved; the engine rejects engineered vacuity where it can detect it, but the meaningfulness of a specification is ultimately the author's responsibility.</li>
<li><strong>The future.</strong> Certificates expire in 90 days because evidence ages: toolchains are patched, defects are found, contexts change. Freshness is a feature, not a subscription trick.</li>
</ul>

<h2>Why we publish the bounds</h2>
<p>A certification authority that oversells its claim destroys the only asset it has. The bounds are therefore printed at the point of claim (the home page's scope line), inside the Certificate Policy, and here — so that a relying party's trust is calibrated by us before it is tested by events.</p>
""",
)

docpage(
    "/docs/explanation/certificate-trust-model/",
    "Certificate trust model",
    "Explanation: what relying on an AxiomCode certificate actually asks you to trust — public keys, public revocation, an append-only record — and what it does not.",
    "Explanation",
    "Relying parties, regulators",
    "Regulators · Users",
    "Certificate Policy & CPS; practice page §§4–6",
    """<h1>Certificate trust model</h1>
<p class="sub" style="font-size:18px">The model is borrowed from the web's certificate authorities and narrowed: you are asked to trust a key, a public record, and a published practice — each of which you can inspect without us.</p>

<h2>What you rely on</h2>
<ul>
<li><strong>The CA key.</strong> Certificates are signed by the production CA key (ID <code class="inline">c731a5036812339d</code>). The public half is published at the API's <code class="inline">/.well-known/axiomcode-keys.json</code>; signature checking needs no account and no trust in this website.</li>
<li><strong>The revocation list.</strong> Public, current, and the only authority on whether a serial still stands.</li>
<li><strong>The append-only record.</strong> Issuance practice, findings, incidents, and graduations are recorded in the <a href="/changelog/">changelog</a>, which does not rewrite itself.</li>
<li><strong>The published practice.</strong> Gates, soak, and certificate rules are stated on the <a href="/practice/">practice page</a> and in the <a href="/paperwork/certificate-policy/">Certificate Policy</a> — the CA can be caught breaking its own stated rules, in public.</li>
</ul>

<h2>What you are not asked to trust</h2>
<ul>
<li><strong>Our AI.</strong> Models explain; they never judge. No verdict depends on a model's say-so.</li>
<li><strong>Our website.</strong> The checker runs in your browser against keys fetched from the API; the offline path (keys + revocation list + the artefact hash) needs this site not at all.</li>
<li><strong>An external auditor's word.</strong> None exists: <strong>no external third-party audit of AxiomCode has been performed</strong>, and the assurance case does not pretend otherwise. What exists is a first-party release gate, a public record, and artefacts you can check yourself.</li>
</ul>

<h2>The organizing risk</h2>
<p>A CA has one existential failure: <strong>mis-issuance</strong> — saying "verified" when it isn't. The whole practice (boolean verdicts, NO VERDICT asymmetry, public revocation, 90-day expiry) is organized around making mis-issuance hard to do and impossible to hide.</p>
""",
)

docpage(
    "/docs/explanation/queue-and-metering-model/",
    "Queue & metering model",
    "Explanation: why verification queues (bounded proof slots), why metering counts engine seconds rather than wall clock, and why NO VERDICT outcomes are free.",
    "Explanation",
    "Users, developers",
    "Users · Developers",
    "Live service behaviour; pricing model",
    """<h1>Queue &amp; metering model</h1>
<p class="sub" style="font-size:18px">Two design choices explain most of the service's behaviour: proof checking runs in bounded slots, and billing counts engine seconds — never queue time, never refusals.</p>

<h2>Why a queue</h2>
<p>A Lean kernel check is real compute with a hard resource profile. Admitting unbounded concurrency would make every run slower and some runs unreliable; instead, the service runs a bounded number of proof slots and queues the rest (202 + position + polling). Queueing is backpressure with a handle: you always know where your job stands, and the job belongs to your key.</p>

<h2>Why engine seconds</h2>
<ul>
<li><strong>Fairness:</strong> you pay for the compute your artefact consumed, not for other people's load ahead of you in the queue.</li>
<li><strong>Predictability:</strong> the same artefact costs the same on a quiet day and a busy one (per-attempt records make the sum auditable — <a href="/docs/guides/reconcile-metering/">reconcile metering</a>).</li>
<li><strong>Alignment:</strong> our incentive is to make the engine faster, not to keep you waiting.</li>
</ul>

<h2>Why NO VERDICT is free</h2>
<p>Timeouts, refusals, and failed queued jobs produce no verdict and no certificate — charging for them would bill you for our limits. The asymmetry is deliberate: money moves only when evidence exists. It is also why the trial can be generous: ten real cases, metered honestly, costing us compute but buying you certainty about the engine before any pack is sold.</p>
""",
)

docpage(
    "/docs/explanation/ask-and-ai-boundaries/",
    "Ask & AI boundaries",
    "Explanation: the Ask shell's architecture of restraint — facts rendered in code, the model explains and never judges, degraded-first delivery, and the data boundaries.",
    "Explanation",
    "Users, evaluators, regulators",
    "Users · Guest · Regulators",
    "Slice-2 shell design record",
    """<h1>Ask &amp; AI boundaries</h1>
<p class="sub" style="font-size:18px">Ask puts a language model next to a certification engine. The boundary between them is architectural, not promissory — this page describes where the walls are built.</p>

<h2>The walls</h2>
<ul>
<li><strong>Judgment wall.</strong> Verdicts are produced by the Lean kernel through the same service callables as the REST API. The model is not in that path and cannot influence it.</li>
<li><strong>Fact wall.</strong> Every fact on the Ask page — verdict, hash, usage, certificate fields — is rendered in code from the actual API payload. The model receives the result to explain it; it cannot edit the numbers it explains.</li>
<li><strong>Degraded-first delivery.</strong> If the model lane is slow or unavailable, the facts ship anyway, without an explanation. The system's failure mode is silence from the commentator, never invention by it.</li>
<li><strong>Data wall.</strong> Your key stays in page memory by default; your artefact goes to the verification API and nowhere else. Ask adds no telemetry and no third-party calls with your content.</li>
</ul>

<h2>Why build it this way</h2>
<p>"Don't trust our AI — verify our proof" is the product's founding sentence. A shell that let the model judge would contradict it in the place users are most likely to believe. So the model is given the one job it is good at — explanation — and structurally denied the job it must never hold. If you catch the explanation and the fact block disagreeing, the fact block is right and the disagreement is a reportable defect (<a href="https://github.com/nrupala/axiomcode/issues">GitHub Issues</a>).</p>

<h2>The open residual</h2>
<p>Explanation latency is a named residual of the shell's current soak: under load, explanations can lag or be skipped while facts arrive on time. It is recorded on the <a href="/status/">status page</a> rather than smoothed over here.</p>
""",
)


# ================= Role packs =================
docpage(
    "/docs/roles/guest/",
    "Guest pack",
    "Role pack for the unauthenticated evaluator: what AxiomCode is, how to judge it without an account, what the trial proves, and the routes in.",
    "Role pack",
    "Unauthenticated evaluators",
    "Guest",
    "Public site surfaces; status source",
    """<h1>Guest pack</h1>
<p class="sub" style="font-size:18px">For the evaluator with no account and no key yet: everything on this page is checkable from where you stand.</p>

<h2>What this is</h2>
<p>AxiomCode is a certification authority for software correctness: it checks Lean 4 artefacts with a real toolchain and issues signed, revocable certificates. Start with the claim and its bounds — <a href="/docs/explanation/what-verification-proves/">what verification proves</a> and <a href="/docs/explanation/what-it-does-not-prove/">what it does not prove</a> — before the marketing.</p>

<h2>Judge it without an account</h2>
<ul>
<li><a href="/status/">Status</a> — every surface, including paused and not-built ones, from the canonical source.</li>
<li><a href="/practice/">Practice</a> — how releases are gated and soaked, and the assurance limits, stated plainly (including: no external audit has been performed).</li>
<li><a href="/changelog/">Changelog</a> — the append-only record, findings and incidents included.</li>
<li><a href="/check/">Certificate checker</a> — if anyone hands you a certificate, check it in your browser; no account needed.</li>
</ul>

<h2>Try it</h2>
<p>The trial needs a key, and keys are free by email (<a href="mailto:hello@axiom-code.com?subject=API%20key%20request">hello@axiom-code.com</a>) — there is deliberately no shared demo key: a trial on your own key shows you the real metering, queue, and trial semantics. The <a href="/docs/start/first-verification/">first-verification tutorial</a> takes five minutes once the key arrives.</p>

<h2>Your boundary</h2>
<p>As a guest you can read everything public and check any certificate. You cannot submit artefacts (a key is required), and trial verdicts never carry certificates. When you are ready, the <a href="/docs/roles/users/">Users pack</a> is your next page.</p>
""",
)

docpage(
    "/docs/roles/users/",
    "Users pack",
    "Role pack for key-holding users: the working set — first verification, writing artefacts the engine accepts, the queue, certificates, metering, and error reporting.",
    "Role pack",
    "Key-holding users",
    "Users",
    "Docs set (tutorials, guides, reference)",
    """<h1>Users pack</h1>
<p class="sub" style="font-size:18px">For key-holders who submit artefacts and rely on verdicts: the working set, in the order you will need it.</p>

<h2>Your set</h2>
<ul>
<li><a href="/docs/start/first-verification/">First verification</a> — the five-minute loop.</li>
<li><a href="/docs/guides/write-a-verifiable-lean-artefact/">Write a verifiable artefact</a> — shape, limits, and the rejection rules.</li>
<li><a href="/docs/guides/use-the-queue/">Use the queue</a> — 202s, polling, and failed jobs.</li>
<li><a href="/docs/start/first-certificate-check/">First certificate check</a> and <a href="/docs/guides/check-and-revoke/">check &amp; revoke</a> — the certificate lifecycle from your side.</li>
<li><a href="/docs/guides/reconcile-metering/">Reconcile metering</a> — usage records, attempts, and what never charges.</li>
<li><a href="/docs/guides/use-ask-without-letting-it-judge/">Ask without letting it judge</a> — if you use the shell.</li>
</ul>

<h2>Your standing facts</h2>
<ul>
<li>Trial: first 10 cases per key — verdicts and usage, no certificates. Packs are priced but <a href="/pricing/">not yet on sale</a>.</li>
<li>Your key is stored as a hash only; keep your copy safe — replacement, not recovery, is the lost-key path.</li>
<li>Current state of every surface: <a href="/status/">status</a>. What changed: <a href="/changelog/">changelog</a>.</li>
</ul>

<h2>When something is wrong</h2>
<p>Product errors go to <a href="https://github.com/nrupala/axiomcode/issues">GitHub Issues</a> (user-initiated; nothing is attached unless you choose to include it) — the acknowledgement names the issue number. Account and key questions: <a href="/contact/">contact</a>. Security matters never use the public form — see the <a href="/paperwork/security/">Security page</a>.</p>
""",
)

docpage(
    "/docs/roles/developers/",
    "Developers pack",
    "Role pack for integrators: the REST and MCP contracts, outcome mapping, metering reconciliation, machine-readable status and changelog, and the versioning posture.",
    "Role pack",
    "Integrators, agent builders",
    "Developers",
    "Live OpenAPI; MCP reference; schema references",
    """<h1>Developers pack</h1>
<p class="sub" style="font-size:18px">For integrators and agent builders: contracts first, then the operational feeds your integration should consume.</p>

<h2>Contracts</h2>
<ul>
<li><a href="/docs/api/">REST API</a> — the reference; the <a href="https://api.axiom-code.com/openapi.json">live OpenAPI document</a> is the contract of record.</li>
<li><a href="/docs/mcp/">MCP</a> — hosted (seven tools) and local (two tools) are separate contracts; pick deliberately.</li>
<li><a href="/docs/reference/verdicts-and-errors/">Verdicts &amp; errors</a> — every outcome, its code, and its effect.</li>
<li><a href="/docs/reference/keys-and-limits/">Keys &amp; limits</a> — the key contract and the service limits.</li>
<li><a href="/docs/guides/integrate-an-agent/">Integrate an agent</a> — outcome-to-behaviour mapping for agent callers.</li>
</ul>

<h2>Feeds to build against</h2>
<ul>
<li><a href="/status.json">status.json</a> (<a href="/docs/reference/status-schema/">schema</a>) — poll it instead of scraping pages; respect <code class="inline">as_of</code>.</li>
<li><a href="/changelog.json">changelog.json</a> / <a href="/changelog.rss.xml">RSS</a> (<a href="/docs/reference/changelog-schema/">schema</a>) — the append-only record of what changed.</li>
<li><a href="/.well-known/axiomcode.json">Service record</a> and <a href="/llms.txt">llms.txt</a> — machine-readable orientation for agents.</li>
</ul>

<h2>Versioning posture</h2>
<p>The live OpenAPI document carries the API's version and is the contract of record; this documentation set is versioned as a whole (see the meta block on every page) and its status/pricing facts are generated from the same canonical sources as the service's own status surfaces, under CI drift checks. Breaking contract changes are changelog events, never silent edits.</p>
""",
)

docpage(
    "/docs/roles/maintainers/",
    "Maintainers pack — evidence on request",
    "Role pack for maintainers: published as an evidence-on-request boundary — the pack's structure and contents list are public; its internals are operational IP and are not published.",
    "Role pack",
    "Maintainers, engaged auditors",
    "Maintainers",
    "Publication boundary per blueprint D3.1/D3.2",
    """<h1>Maintainers pack</h1>
<p class="sub" style="font-size:18px">This pack is published as a boundary, not a document set — deliberately.</p>

<div class="honest"><h3>Publication level: evidence on request</h3>
<p>The Maintainers pack carries release and deployment internals — operational IP whose publication would weaken the service it describes. Its <strong>structure and contents list are public</strong> (below); its contents are provided on request to maintainers and to auditors under engagement. No credentials, keys, internal addresses, or host topology appear in any pack, including this one.</p></div>

<h2>What the pack contains</h2>
<ul>
<li>Release standard operating procedures — branch, gate, merge, deploy, read-back.</li>
<li>Per-release gate artefacts: gate configuration, coverage ledgers, judgment differentials, verdicts.</li>
<li>Deploy and rollback runbooks for the API, the hosted MCP leg, and the website.</li>
<li>CA operations runbook: issuance and revocation procedure, key custody and rollover procedure.</li>
<li>Incident playbooks and the findings register (F-AX-*) with closure evidence.</li>
<li>Monitoring and soak-observation procedures for release candidates.</li>
</ul>

<h2>What is already public</h2>
<p>Much of the pack's evidence base is public by design: the <a href="https://github.com/nrupala/axiomcode/blob/main/gate.yaml">gate declaration</a>, the <a href="https://github.com/nrupala/axiomcode/blob/main/docs/THREAT-MODEL.md">threat model</a>, the <a href="https://github.com/nrupala/axiomcode/blob/main/docs/COVERAGE-LEDGER.json">coverage ledger</a>, the <a href="/practice/">practice page</a>, and the <a href="/changelog/">changelog</a>. The boundary covers procedure and internals, not the existence or the outcomes of the process.</p>

<h2>Requesting the pack</h2>
<p>Write to <a href="mailto:hello@axiom-code.com?subject=Maintainers%20pack%20request">hello@axiom-code.com</a> with who you are and the engagement the evidence supports. Requests are answered by a person; there is no automated fulfilment, and that is intentional.</p>
""",
)

docpage(
    "/docs/roles/regulators/",
    "Regulators pack",
    "Role pack for regulators and auditors: the Certificate Policy as the lead document, the control-to-evidence index, CA facts, the incident record, and the assurance limits.",
    "Role pack",
    "Regulators, auditors, relying-party risk functions",
    "Regulators",
    "Certificate Policy & CPS; practice page evidence index",
    """<h1>Regulators pack</h1>
<p class="sub" style="font-size:18px">For regulators, auditors, and relying-party risk functions: the governing documents first, then the index from each control to its public evidence.</p>

<h2>Governing documents</h2>
<ul>
<li><a href="/paperwork/certificate-policy/">Certificate Policy &amp; CPS</a> — issuance, validity (90 days), revocation, and CA control rules. This is the lead document for the CA's practice.</li>
<li><a href="/paperwork/terms/">Terms</a> · <a href="/paperwork/privacy/">Privacy</a> · <a href="/paperwork/security/">Security &amp; disclosure</a> · <a href="/paperwork/refunds/">Refunds</a></li>
<li>Operator: <strong>2351485 ALBERTA INC.</strong> (Alberta, Canada) — see <a href="/about/">About</a>.</li>
</ul>

<h2>Control → evidence index</h2>
<table class="spec">
<tr><th>Control</th><th>Public evidence</th></tr>
<tr><td>Release gating</td><td><a href="https://github.com/nrupala/axiomcode/blob/main/gate.yaml">Gate declaration</a> · <a href="https://github.com/nrupala/axiomcode/blob/main/docs/THREAT-MODEL.md">threat model</a> · <a href="https://github.com/nrupala/axiomcode/blob/main/docs/COVERAGE-LEDGER.json">coverage ledger</a> · <a href="/practice/">practice §2</a></td></tr>
<tr><td>Release-candidate soak</td><td><a href="/status/">Status</a> (lifecycle per surface) · <a href="/practice/">practice §3</a></td></tr>
<tr><td>Certificate issuance &amp; lifecycle</td><td><a href="/paperwork/certificate-policy/">Certificate Policy</a> · <a href="/docs/reference/certificates/">certificate anatomy</a></td></tr>
<tr><td>CA key custody &amp; rollover</td><td><a href="/practice/">Practice §6</a> — key ID <code class="inline">c731a5036812339d</code>; public keys at the API well-known endpoint</td></tr>
<tr><td>Revocation</td><td><a href="https://api.axiom-code.com/revoked">Public revocation list</a> · changelog incident entries</td></tr>
<tr><td>Findings &amp; incidents</td><td><a href="/changelog/">Changelog</a> (Finding / Incident categories) · <a href="/practice/">practice §7</a></td></tr>
<tr><td>Error reporting</td><td>GitHub Issues, user-initiated only — <a href="/practice/">practice §8</a></td></tr>
</table>

<h2>Assurance limits — stated plainly</h2>
<p><strong>No external third-party audit of AxiomCode has been performed.</strong> Assurance is first-party (an internal release gate, independent of the build lanes) plus the public, independently checkable artefacts indexed above. Internal release/deploy procedure is published as an evidence-on-request boundary — see the <a href="/docs/roles/maintainers/">Maintainers pack</a>. Any representation beyond this paragraph should be treated as unauthorised.</p>

<h2>Contact for regulatory matters</h2>
<p><a href="/contact/">Contact</a> — route "Regulatory / audit" in the subject line. Security disclosures never use the public form: <a href="/paperwork/security/">Security page</a>.</p>
""",
)

docpage(
    "/docs/roles/admins/",
    "Admins pack",
    "Role pack for account administrators: there is no admin console — this page states plainly how account and key administration actually works today.",
    "Role pack",
    "Account administrators",
    "Admins",
    "Live service behaviour; billing state from the status source",
    """<h1>Admins pack</h1>
<p class="sub" style="font-size:18px">For the people who administer accounts and keys for their teams.</p>

<div class="honest"><h3>There is no admin console</h3>
<p>Stated plainly: <strong>AxiomCode has no admin console, no self-serve signup, and no account dashboard today.</strong> Administration is a manual, email-mediated process while billing is paused. Anything that looks like an AxiomCode admin login is not ours — report it via the <a href="/paperwork/security/">Security page</a>.</p></div>

<h2>How administration works today</h2>
<ul>
<li><strong>Getting keys:</strong> email <a href="mailto:hello@axiom-code.com?subject=API%20key%20request">hello@axiom-code.com</a>; keys are issued per request. One key per integration is the recommended pattern.</li>
<li><strong>Key storage on our side:</strong> hash only. We cannot display or recover a key; loss means replacement.</li>
<li><strong>Balances and packs:</strong> credit packs are priced but <strong>not yet on sale</strong>; there are no balances to administer yet. Trial usage (10 cases per key) is visible in each verification's usage record and via the MCP <code class="inline">usage_report</code> tool.</li>
<li><strong>Team changes:</strong> key replacement, additional keys, and account questions are handled through <a href="/contact/">contact</a> — expect a human reply, not a ticket black hole.</li>
</ul>

<h2>What you can verify without us</h2>
<ul>
<li>Every certificate your keys produced: <a href="/check/">checker</a> + <a href="https://api.axiom-code.com/revoked">revocation list</a>.</li>
<li>Your metering: usage records join on <code class="inline">artifact_hash</code> (<a href="/docs/guides/reconcile-metering/">reconcile metering</a>).</li>
<li>The service's state: <a href="/status/">status</a> and the <a href="/changelog/">changelog</a>.</li>
</ul>

<h2>When a console exists</h2>
<p>It will appear on the <a href="/status/">status page</a> as its own surface before it is announced anywhere else — the status page is where new surfaces exist first, by rule.</p>
""",
)

docpage(
    "/docs/roles/ops/",
    "Ops pack",
    "Role pack for operators and SRE counterparts: surfaces and health evidence, the incident rule, queue behaviour, and escalation routes — public operational facts only.",
    "Role pack",
    "Operators, SRE counterparts",
    "Ops",
    "Status source; practice page §7",
    """<h1>Ops pack</h1>
<p class="sub" style="font-size:18px">For operators — ours and our customers' — the public operational picture: what to watch, what an incident looks like from outside, and where to escalate.</p>

<h2>Surfaces &amp; health evidence</h2>
<ul>
<li>All surfaces, availability, and lifecycle: <a href="/status/">/status/</a> or <a href="/status.json">status.json</a> (schema: <a href="/docs/reference/status-schema/">status schema</a>).</li>
<li>API health: <code class="inline">GET https://api.axiom-code.com/health</code> — public, no key.</li>
<li>CA state: <a href="https://api.axiom-code.com/.well-known/axiomcode-keys.json">public keys</a> · <a href="https://api.axiom-code.com/revoked">revocation list</a> — both public.</li>
</ul>

<h2>The incident rule</h2>
<p>Per <a href="/practice/">practice §7</a>: every escaped defect and incident receives a finding ID (F-AX-*), a public changelog entry under the Finding or Incident category, a fix, a regression guard, and closure evidence. The status page shows current state; the changelog preserves the sequence — history is never rewritten to look quieter than it was.</p>

<h2>Queue behaviour (what your dashboards will see)</h2>
<ul>
<li>Bounded proof slots; saturation presents as <strong>202 queueing with positions</strong>, not errors.</li>
<li>Run timeouts present as 504 NO VERDICT outcomes; rate refusals as 429. Both are named in the <a href="/docs/reference/verdicts-and-errors/">outcome taxonomy</a>.</li>
<li>Ask explanations are degraded-first: explanation lag under load is a known, recorded residual — facts are unaffected.</li>
</ul>

<h2>Escalation</h2>
<ul>
<li>Service problems: <a href="https://github.com/nrupala/axiomcode/issues">GitHub Issues</a> (product errors) or <a href="/contact/">contact</a>.</li>
<li>Security: the disclosure route on the <a href="/paperwork/security/">Security page</a> — never the public issue tracker.</li>
<li>Support targets and service levels, where they apply, are stated in the <a href="/paperwork/sla/">Service Levels</a> document — this pack adds no targets of its own.</li>
</ul>
""",
)
