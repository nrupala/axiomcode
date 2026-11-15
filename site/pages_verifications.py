"""Verification reports pages — rendered from the canonical source
(verifications_data.py), never hand-maintained copies.

The register publishes AxiomCode's verification of its own products:
every report states what was proven and what was not proven. A source
entry without a `not_proven` field does not render (see
verifications_data.renderable); the drift checks fail on such an entry.
"""

import html

import verifications_data
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


_VERDICT_CLASS = {
    "proven": "b-pass",
    "passed": "b-pass",
    "passed_with_findings": "b-warn",
    "failed": "b-fail",
}


def _verdict_badge(verdict):
    label = verifications_data.VERDICT_LABELS[verdict]
    return f'<span class="badge {_VERDICT_CLASS[verdict]}">{label}</span>'


def _kind_chip(kind):
    return f'<span class="chip scope">{verifications_data.KIND_LABELS[kind]}</span>'


def _items(items):
    return "".join(f"<li>{html.escape(i)}</li>" for i in items)


_RENDERABLE = [r for r in verifications_data.REPORTS if verifications_data.renderable(r)]


# ---------- /verifications/ (index) ----------
def _index_cards():
    cards = []
    for r in _RENDERABLE:
        cards.append(
            f'<div class="card cardflex">'
            f'<div class="chips">{_kind_chip(r["kind"])}</div>'
            f"<h3>{html.escape(r['subject'])}</h3>"
            f"<p>{html.escape(r['summary'])}</p>"
            f"<p>{_verdict_badge(r['verdict'])} "
            f'<span style="color:var(--faint);font-size:14px">{_fmt_date(r["date"])}</span></p>'
            f'<p class="go"><a href="/verifications/{r["report_id"]}/">Read the report</a></p>'
            f"</div>"
        )
    return "".join(cards)


def _index_body():
    meta = verifications_data.REPORTS_META
    return f"""<section class="pagehead"><div class="wrap">
<h1>Verification reports</h1>
<p>AxiomCode&rsquo;s trust case is proof by our own products. Every product we build is verified &mdash; through the release gate, and for deterministic cores by Lean&nbsp;4 proof &mdash; and the reports are published here, in full: what the verification established, and where it stops.</p>
<p class="asof">Register as of {_fmt_date(meta["as_of"])} ({meta["timezone"]}) &middot; Machine-readable: <a href="/verifications.json">verifications.json</a> &middot; How the practice runs: <a href="/practice/">Practice</a></p>
</div></section>

<section class="block" style="padding-top:26px"><div class="wrap">
<div class="note"><strong>How to read these reports.</strong> Every report states two things: <strong>What was proven</strong> and <strong>What was not proven</strong> &mdash; in plain words, on the report itself. A report without the second statement does not appear in this register: a claim is only worth what its stated limits are worth. Reports are added when their underlying records are complete; work in progress is not pre-published.</div>

<div class="cards">{"".join(_index_cards())}</div>

<div class="honest"><h3>First-party reports, published on purpose</h3>
<p>These are our own verification reports on our own products &mdash; first-party assurance evidence, published so that anyone can read exactly what was established and what was not. They are not an external audit: <strong>no external firm has audited or validated this product end-to-end</strong> (see <a href="/practice/">Practice &sect;4</a>). Where a report rests on a formal proof, the judge is the Lean kernel, not a model&rsquo;s opinion &mdash; and the report says plainly where the proof&rsquo;s model stops and the running system begins.</p></div>
</div></section>
"""


page(
    "/verifications/",
    "Verification reports",
    "AxiomCode's published verification reports on its own products: every report states what was proven and what was not proven, in plain words.",
    _index_body(),
)


# ---------- /verifications/<report_id>/ (one page per report) ----------
def _report_body(r):
    context = ""
    if r.get("context"):
        context = f"""
<h2 style="margin-top:44px">How this report came to be</h2>
<p>{html.escape(r["context"])}</p>"""
    return f"""<section class="pagehead"><div class="wrap">
<p class="kicker">{_fmt_date(r["date"])} &middot; {html.escape(verifications_data.KIND_LABELS[r["kind"]])}</p>
<h1>{html.escape(r["subject"])}</h1>
<p>{html.escape(r["summary"])}</p>
<p style="margin-top:14px">{_verdict_badge(r["verdict"])} {_kind_chip(r["kind"])}</p>
</div></section>

<section class="block" style="padding-top:26px"><div class="wrap"><div class="prose">
<h2>What was proven</h2>
<ul>{_items(r["proven"])}</ul>

<h2 style="margin-top:44px">What was not proven</h2>
<ul>{_items(r["not_proven"])}</ul>

<h2 style="margin-top:44px">How it was verified</h2>
<p>{html.escape(r["method"])}</p>{context}

<p style="margin-top:44px"><a href="/verifications/">&larr; All verification reports</a> &middot; <a href="/practice/">How the practice runs</a></p>
</div></div></section>
"""


for _r in _RENDERABLE:
    page(
        f"/verifications/{_r['report_id']}/",
        _r["subject"],
        f"Verification report — {_r['subject']}. What was proven, and what was not proven, in plain words.",
        _report_body(_r),
    )
