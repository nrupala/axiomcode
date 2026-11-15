"""Status, changelog, and practice pages — rendered from the canonical
sources (status_data.py, changelog_data.py), never hand-maintained copies."""

import html

import changelog_data
import status_data
from build import page

_MONTHS = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]


def _fmt_date(iso):
    if not iso:
        return "—"
    y, m, d = iso.split("-")
    return f"{int(d)} {_MONTHS[int(m) - 1]} {y}"


_AV_CLASS = {"live": "av-live", "paused": "av-paused", "unavailable": "av-unavail"}
_LC_CLASS = {
    "live": "lc-live",
    "paused": "lc-paused",
    "in_soak": "lc-soak",
    "in_design": "lc-design",
    "not_built": "lc-notbuilt",
}


def _chip(kind, value):
    if kind == "availability":
        return f'<span class="chip {_AV_CLASS[value]}">{status_data.AVAILABILITY_LABELS[value]}</span>'
    return f'<span class="chip {_LC_CLASS[value]}">{status_data.LIFECYCLE_LABELS[value]}</span>'


def _evidence_links(evidence):
    if not evidence:
        return "—"
    return " · ".join(f'<a href="{e["url"]}">{html.escape(e["label"])}</a>' for e in evidence)


# ---------- /status/ ----------
def _evidence(sid, label):
    s = next(x for x in status_data.SURFACES if x["surface_id"] == sid)
    for e in s["evidence"]:
        if e["label"] == label:
            return e
    return None


def _health_cards():
    specs = [
        ("rest_api", "Health", "API health", "Health endpoint — public, no key."),
        ("rest_api", "OpenAPI", "OpenAPI", "The live contract of record, served by the API itself."),
        (
            "certificate_checker",
            "CA public keys",
            "CA public keys",
            "Production CA key ID c731a5036812339d — verify any certificate offline.",
        ),
        (
            "certificate_checker",
            "Revocation list",
            "Revocation list",
            "Public, no key — the current revocation state of every certificate.",
        ),
    ]
    cards = []
    for sid, label, title, note in specs:
        e = _evidence(sid, label)
        if e is None:
            continue
        cards.append(
            f'<div class="card"><h3>{title}</h3><p>{note}</p>'
            f'<p class="go"><a href="{e["url"]}">{html.escape(e["url"].replace("https://", ""))}</a></p></div>'
        )
    return "".join(cards)


def _status_body():
    meta = status_data.STATUS_META
    rows = []
    for s in status_data.SURFACES:
        since = _fmt_date(s["public_since"])
        if s["graduates_on"]:
            since += f"<small>Graduation decision: {_fmt_date(s['graduates_on'])}</small>"
        notes = html.escape(s["summary"])
        for lim in s["known_limits"]:
            notes += f"<small>Known limit: {html.escape(lim)}</small>"
        notes += f"<small>Evidence: {_evidence_links(s['evidence'])}</small>"
        url = html.escape(s["canonical_url"].replace("https://", ""))
        rows.append(
            "<tr>"
            f"<td><strong>{html.escape(s['name'])}</strong><small>{url}</small></td>"
            f"<td>{_chip('availability', s['availability'])}</td>"
            f"<td>{_chip('lifecycle', s['lifecycle'])}</td>"
            f"<td>{since}</td>"
            f"<td>{notes}</td>"
            "</tr>"
        )
    scheduled = [s for s in status_data.SURFACES if s["graduates_on"]]
    sched_html = "".join(
        f'<div class="card"><h3>{html.escape(s["name"])}</h3>'
        f"<p>Graduation decision scheduled {_fmt_date(s['graduates_on'])}. A scheduled date is a "
        "plan, not a result: graduation requires a recorded gate decision, entered in the "
        "changelog when it happens.</p></div>"
        for s in scheduled
    )
    recent = [e for e in changelog_data.ENTRIES if e["category"] in ("Status", "Added", "Finding")][:4]
    recent_html = "".join(
        f'<li>{_fmt_date(e["date"])} — <a href="/changelog/#{e["id"]}">{html.escape(e["title"])}</a></li>'
        for e in recent
    )
    return f"""<section class="pagehead"><div class="wrap">
<h1>Status</h1>
<p>Every surface, one page, generated from the canonical status source — including what is paused, in soak, in design, or not built. If a surface is not listed here, it does not exist.</p>
<p class="asof">Last verified {_fmt_date(meta["as_of"])} ({meta["timezone"]}) &middot; Machine-readable: <a href="/status.json">status.json</a> &middot; <a href="/.well-known/axiomcode.json">service record</a> &middot; <a href="/llms.txt">llms.txt</a></p>
</div></section>

<section class="block" style="padding-top:26px"><div class="wrap">
<div class="kicker">Health evidence</div>
<h2>Check it yourself</h2>
<div class="cards">{"".join(_health_cards())}</div>

<h2 style="margin-top:52px">All surfaces</h2>
<div class="tablewrap"><table class="status">
<tr><th style="width:20%">Surface</th><th>Availability</th><th>Lifecycle</th><th style="width:16%">Since / transition</th><th>Notes &amp; known limits</th></tr>
{"".join(rows)}
</table></div>

<h2 style="margin-top:52px">Scheduled transitions</h2>
<div class="cards">{sched_html}</div>

<div class="honest"><h3>How to read this page</h3>
<p><strong>Availability</strong> says whether you can use the surface now. <strong>Lifecycle</strong> says where it stands in its release process. A surface can be <em>live</em> and <em>in soak</em> at once: usable today, still inside its post-release observation window, with graduation a recorded gate decision — never a date passing quietly.</p>
<p>This page, <a href="/status.json">status.json</a>, the service record, and the llms.txt status section are all generated from one source; CI drift checks fail the build when any rendering disagrees with it.</p></div>

<h2 style="margin-top:52px">Recent status changes</h2>
<ul>{recent_html}</ul>
<p>Full record: <a href="/changelog/">Changelog &amp; service record</a>.</p>
</div></section>
"""


page(
    "/status/",
    "Status",
    "AxiomCode service status: every surface's availability and lifecycle — live, paused, in soak, in design, not built — generated from one canonical source.",
    _status_body(),
)


# ---------- /changelog/ ----------
def _entry_html(e):
    refs = ""
    if e["refs"]:
        refs = f'<p style="margin-bottom:0"><strong>Refs:</strong> {", ".join(html.escape(r) for r in e["refs"])}</p>'
    ev = ""
    if e["evidence"]:
        ev = f'<p style="margin-bottom:0"><strong>Evidence:</strong> {_evidence_links(e["evidence"])}</p>'
    return f"""<div class="card" id="{e["id"]}" style="margin-top:20px">
<div class="kicker">{_fmt_date(e["date"])} &middot; {html.escape(e["category"])} &middot; {html.escape(", ".join(e["surfaces"]))}</div>
<h3 style="margin-top:0">{html.escape(e["title"])}</h3>
{e["body"]}
<p><strong>Effect:</strong> {html.escape(e["effect"])}</p>
{ev}{refs}
<p style="margin-bottom:0"><strong>Disposition:</strong> {html.escape(e["disposition"])}</p>
</div>"""


page(
    "/changelog/",
    "Changelog & service record",
    "The AxiomCode changelog and service record: launches, changes, findings, fixes, incidents, and graduations — append-only, no silent edits.",
    f"""<section class="block"><div class="wrap"><div class="prose">
<h1 class="pt">Changelog &amp; service record</h1>
<p class="sub">What changed, when, and what it means for relying parties.</p>
<div class="note">Entries are append-only. A correction to an entry is a new entry — the original
remains readable. Scheduled transitions (for example, a graduation date) are listed on the
<a href="/status/">status page</a> and are recorded here only when they happen. Machine-readable:
<a href="/changelog.json">changelog.json</a> &middot; <a href="/changelog.rss.xml">RSS</a>.</div>
{"".join(_entry_html(e) for e in changelog_data.ENTRIES)}
</div></div></section>
""",
)


# ---------- /releases/ alias ----------
page(
    "/releases/",
    "Release log",
    "The AxiomCode release log is now the Changelog & service record.",
    """<section class="block"><div class="wrap"><div class="prose">
<h1 class="pt">Release log</h1>
<p class="sub">This page has moved.</p>
<div class="note">The release log is now the <a href="/changelog/"><strong>Changelog &amp; service
record</strong></a> — every entry, including the ones that used to live here, is recorded there.
Current service state is on the <a href="/status/"><strong>status page</strong></a>.</div>
<script>window.location.replace("/changelog/");</script>
</div></div></section>
""",
)


# ---------- /practice/ ----------
def _practice_limits():
    items = []
    for s in status_data.SURFACES:
        for lim in s["known_limits"]:
            items.append(f"<li><strong>{html.escape(s['name'])}:</strong> {html.escape(lim)}</li>")
    return "".join(items)


_REPORT_URL = "https://github.com/nrupala/axiomcode/issues/new?template=bug_report.md"

page(
    "/practice/",
    "Practice",
    "How AxiomCode runs its practice: release gates, release-candidate soak, certificate semantics and lifecycle, assurance limits, findings, and how to report an error.",
    f"""<section class="block"><div class="wrap"><div class="prose">
<h1 class="pt">Practice</h1>
<p class="sub">How this certification authority builds, gates, issues, revokes, supports, and corrects — stated plainly enough to be checked.</p>

<h2>1. What a verdict is</h2>
<p>A verdict is boolean: <strong>PASSED</strong> or <strong>FAILED</strong>. The Lean toolchain compiles the submitted artefact and the kernel checks its proofs; there is no third verdict. A request that ends before a verdict — payment required (trial used up and no credit balance), a proof that runs past its time limit, a concurrency, rate, or size refusal, or a queued job that fails — is a <strong>NO VERDICT</strong> error outcome, not a verdict, and produces no certificate. The trial (10 cases per API key) returns verdicts and usage records but never a certificate. A completed <em>paid</em> verification receives a signed certificate recording the verdict — PASSED or FAILED. A FAILED certificate attests the failure; it never implies a pass. The full semantics are in the <a href="/paperwork/certificate-policy/">Certificate Policy</a> (§4.2).</p>

<h2>2. How a release is certified</h2>
<p>No change reaches production on a lane's say-so. Each release declares its pathways in <a href="https://github.com/nrupala/axiomcode/blob/main/gate.yaml">gate.yaml</a>, is assessed against the <a href="https://github.com/nrupala/axiomcode/blob/main/docs/THREAT-MODEL.md">threat model</a> and a coverage ledger, and must pass CI, independent gate probes, and a judgment differential before merge. Deployment follows the recorded gate verdict, and the deployed surface is read back live afterwards — merged is not live. Findings are recorded with IDs (F-AX-*) and closed only on post-deploy evidence.</p>

<h2>3. Release-candidate soak</h2>
<p>A release that passes the gate enters production as a release candidate and <strong>soaks</strong>: it serves real traffic while its evidence is watched. &ldquo;In soak&rdquo; on the <a href="/status/">status page</a> means exactly that — live, but not yet graduated. A residual is a known, named imperfection carried openly in the soak (for example, Ask's explanation latency). A date alone never graduates a release: graduation is a recorded gate decision, entered in the <a href="/changelog/">changelog</a> when it happens. Current soaks and their scheduled decision dates are on the <a href="/status/">status page</a>.</p>

<h2>4. Independent assurance — and its limits</h2>
<p>Stated plainly: the release-gate probes behind our releases are <strong>first-party assurance evidence</strong> — an internal gate, run independently of the build lanes, but not an outside audit. <strong>No external firm has audited or validated this product end-to-end, and no external third-party audit has been performed.</strong> Gemini's recorded role (2026-11-09) was market and strategy assessment, never technical certification. DeepSeek has not checked the production service. What you can verify yourself: the <a href="https://github.com/nrupala/axiomcode/blob/main/gate.yaml">gate declaration</a>, the <a href="https://github.com/nrupala/axiomcode/blob/main/docs/THREAT-MODEL.md">threat model</a>, the public revocation list, and every certificate — each is independently checkable against the published CA keys. Our trust case is proof by our own products: the verification reports on our own products — each stating what was proven and what was not proven — are published in the <a href="/verifications/">verification reports</a> register.</p>

<h2>5. Certificate lifecycle</h2>
<p>Certificates are issued on completed paid verifications, are valid for <strong>90 days</strong>, and bind the artefact hash, verdict, toolchain, issuer, serial, and validity window under the CA's signature. Renewal is <strong>re-verification</strong>: submit again and a fresh certificate is issued on the new result. A certificate is revoked when its verdict can no longer be stood behind — for example a toolchain defect that invalidates it — and revocation is public: the serial goes on the <a href="https://api.axiom-code.com/revoked">public revocation list</a>, an incident note is published in the <a href="/changelog/">changelog</a>, and affected artefacts are re-verified at our expense. Check any certificate at <a href="/check/">/check/</a> or offline against the <a href="https://api.axiom-code.com/.well-known/axiomcode-keys.json">CA public keys</a>.</p>

<h2>6. CA operations</h2>
<p>The production CA key (key ID <code class="inline">c731a5036812339d</code>) signs every certificate. As the <a href="/paperwork/certificate-policy/">Certificate Policy</a> states, CA keys are held in a restricted directory (mode 0600), issuance and revocation are recorded in a tamper-evident append-only log, and every CA touch is logged. Key rollover, when it happens, is published here and in the changelog before the new key signs. The public half of the CA is fully open: <a href="https://api.axiom-code.com/.well-known/axiomcode-keys.json">keys</a> and <a href="https://api.axiom-code.com/revoked">revocations</a>.</p>

<h2>7. Findings and incidents</h2>
<p>Every escaped defect receives a finding ID (F-AX-*), a severity and scope, a public changelog entry, a fix, a regression guard, and closure evidence — the worked example is <a href="/changelog/#2026-11-11-f-ax-10">F-AX-10</a>, the browser-submission defect that escaped the public flip and was closed on post-deploy probes. Incidents do not rewrite history: the status page shows the current state, and the changelog preserves the sequence.</p>

<h2>8. Support and error reporting</h2>
<p>Product errors land in the product's own issue tracker — AxiomCode's GitHub Issues — where they are triaged and worked. Reporting is <strong>user-initiated only</strong>: there is no silent telemetry, and we never attach your submitted code or certificate content unless you explicitly choose to include it.</p>
<p><a href="{_REPORT_URL}"><strong>Report an error</strong></a> — the form asks for: the surface (web, REST, MCP, Ask), the date and time, what you expected, what actually happened, and an artefact hash or certificate serial where relevant. The acknowledgement you receive names the issue number. <strong>Security vulnerabilities do not use the public form</strong> — use the disclosure route on the <a href="/paperwork/security/">Security page</a> (security@axiom-code.com). Support email: <a href="mailto:hello@axiom-code.com">hello@axiom-code.com</a>.</p>

<h2>9. Documentation control</h2>
<p>Documentation is a product surface, held to the house documentation standard (Diátaxis structure; role packs for Guest, Users, Developers, Maintainers, Regulators, Admins, and Ops). The role-pack documentation rebuild landed on 14 November 2026 as part of the approved website redesign: the <a href="/docs/">documentation home</a> is Diátaxis-first, every docs page carries its audience, type, version, last-verified date, source artefact, and a Markdown mirror, and the Maintainers pack is published as an evidence-on-request boundary — its structure is public, its internals are not. Status, lifecycle, pricing, and endpoint facts in the documentation derive from the same canonical sources as this page, and CI drift checks fail when renderings disagree.</p>

<h2>10. Known limitations</h2>
<ul>{_practice_limits()}</ul>
<p>Current state of every surface: <a href="/status/">/status/</a>.</p>

<h2>Evidence index</h2>
<table class="spec">
<tr><th>Artefact</th><th>What it proves</th></tr>
<tr><td><a href="https://github.com/nrupala/axiomcode/blob/main/gate.yaml">Gate declaration (gate.yaml)</a></td><td>Declared pathways for each release</td></tr>
<tr><td><a href="https://github.com/nrupala/axiomcode/blob/main/docs/THREAT-MODEL.md">Threat model</a></td><td>The threats each pathway is assessed against</td></tr>
<tr><td><a href="https://github.com/nrupala/axiomcode/blob/main/docs/COVERAGE-LEDGER.json">Coverage ledger</a></td><td>What the gate actually covered</td></tr>
<tr><td><a href="/paperwork/certificate-policy/">Certificate Policy &amp; CPS</a></td><td>Issuance, validity, revocation, and CA control rules</td></tr>
<tr><td><a href="/status.json">Status JSON</a></td><td>Current availability and lifecycle of every surface</td></tr>
<tr><td><a href="https://api.axiom-code.com/revoked">Revocation list</a> · <a href="https://api.axiom-code.com/.well-known/axiomcode-keys.json">CA keys</a></td><td>Public, independently checkable CA state</td></tr>
<tr><td><a href="/changelog.json">Changelog JSON</a> · <a href="/changelog.rss.xml">RSS</a></td><td>The append-only service record, machine-readable</td></tr>
<tr><td><a href="/verifications/">Verification reports</a> · <a href="/verifications.json">JSON</a></td><td>What our verification of our own products proved — and what it did not</td></tr>
</table>
</div></div></section>
""",
)
