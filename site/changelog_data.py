"""Canonical AxiomCode changelog source — the public service record.

Rendered from here:
  - /changelog/ HTML page   (pages_status.py)
  - /changelog.json         (run.py)
  - /changelog.rss.xml      (run.py)

Discipline (blueprint C4):
  - Entries are append-only. No silent edits: a correction to an entry is a
    new entry (or a dated correction note appended to the entry); the
    original remains readable.
  - Entry IDs are unique and stable; other pages link to them.
  - Do not publish "graduated" entries before the graduation decision
    occurs. Scheduled transitions live on /status/, not here.
"""

import datetime
import email.utils
from html import escape as _esc

CATEGORIES = ("Added", "Changed", "Fixed", "Finding", "Incident", "Status", "Documentation", "Removed")

_REPO = "https://github.com/nrupala/axiomcode"

ENTRIES = [
    {
        "id": "2026-11-12-status-changelog-practice",
        "date": "2026-11-12",
        "title": "Status page, changelog, and practice page — one canonical source",
        "category": "Added",
        "surfaces": ["Website", "Status", "Changelog", "Practice"],
        "body": (
            '<p>The site now carries a <a href="/status/">status page</a> generated from a single '
            'canonical status source (also published as <a href="/status.json">status.json</a>), this '
            'changelog with JSON and RSS feeds, and a <a href="/practice/">practice page</a> describing '
            "how releases are gated, soaked, and graduated, what a certificate does and does not claim, "
            "and how to report an error. Status facts — availability, lifecycle, dates, endpoints — are "
            "no longer typed independently into separate pages: the status page, status.json, the "
            "machine-readable service record, and the llms.txt status section are generated from the "
            "same source, and CI drift checks fail the build when they disagree. The former release log "
            "at /releases/ is now an alias of this changelog, and its entries were migrated here "
            "unchanged.</p>"
        ),
        "effect": "Anyone — customer, auditor, or agent — can read the current state of every surface "
        "in one place, including what is paused, in soak, in design, or not built.",
        "evidence": [
            {"label": "Status", "url": "https://axiom-code.com/status/"},
            {"label": "Status JSON", "url": "https://axiom-code.com/status.json"},
            {"label": "Practice", "url": "https://axiom-code.com/practice/"},
        ],
        "refs": [],
        "disposition": "Live on the site; graduation of the surfaces it describes remains as recorded on /status/.",
    },
    {
        "id": "2026-11-12-p0-closure",
        "date": "2026-11-12",
        "title": "P0 closure: verdict taxonomy, pricing schema, security scope, status notes",
        "category": "Documentation",
        "surfaces": ["Docs", "How It Works", "Pricing", "Security", "Release log", "Blog"],
        "body": (
            "<p>The remaining P0 truth corrections landed. The verdict taxonomy is now stated the same "
            "way everywhere it appears: verdicts are boolean — PASSED or FAILED — and a request that "
            "ends before a verdict (payment required, timeout, concurrency/rate/size refusal, failed "
            "queued job) is a <strong>NO VERDICT</strong> error outcome, not a verdict; the retired "
            "INCOMPLETE wording is gone. The pricing JSON-LD now marks the credit packs "
            "<em>OutOfStock — not yet on sale</em>, matching the paused billing state the page already "
            "stated in prose. The Security page's in-scope list now names the hosted MCP endpoint, the "
            "web verifier, and the Ask shell. Until this changelog landed, the release log and the "
            "2026-09-26 blog essay carried interim dated status notes; those notes are replaced by "
            "pointers to /status/ and this changelog. A 21-surface live evidence pack was filed with "
            "the change.</p>"
        ),
        "effect": "No known false claim remains on the site; every surface states the same taxonomy, "
        "the same billing state, and the same scope.",
        "evidence": [
            {"label": "Docs", "url": "https://axiom-code.com/docs/"},
            {"label": "Security", "url": "https://axiom-code.com/paperwork/security/"},
            {"label": "Pricing", "url": "https://axiom-code.com/pricing/"},
        ],
        "refs": [],
        "disposition": "Closed. Claim-by-claim evidence verification continues under the status source's "
        "last-verified discipline.",
    },
    {
        "id": "2026-11-11-wording-corrections",
        "date": "2026-11-11",
        "title": "Material wording corrections",
        "category": "Documentation",
        "surfaces": ["How It Works", "Docs", "Homepage", "Terms", "Security", "llms.txt", ".well-known"],
        "body": (
            "<p>Public wording was corrected where it contradicted the service. The hosted MCP endpoint "
            "is live, and every surface that said otherwise — How It Works, Terms §1, the Security "
            "page, llms.txt, and the machine-readable service record — now says so. The Docs verdict "
            "table was corrected: a completed paid verification that returns FAILED receives a signed "
            "certificate recording FAILED (the table previously said no certificate is issued). "
            "Homepage copy that implied smart-contract verification is a current capability was "
            "removed or rewritten: that capability is in design (see /status/).</p>"
        ),
        "effect": "Human pages, paperwork, and machine-readable mirrors state the same facts about "
        "MCP availability, FAILED certificates, and smart-contract scope.",
        "evidence": [
            {"label": "How It Works", "url": "https://axiom-code.com/how-it-works/"},
            {"label": "Docs", "url": "https://axiom-code.com/docs/"},
        ],
        "refs": [],
        "disposition": "Closed; verified live the same day.",
    },
    {
        "id": "2026-11-11-referral-removal",
        "date": "2026-11-11",
        "title": "Third-party signup promotion removed — ruled out fleet-wide",
        "category": "Removed",
        "surfaces": ["Website"],
        "body": (
            "<p>A third-party signup promotion found in product copy was removed the same day. The "
            "ruling is fleet-wide: no product carries a third-party signup promotion. A plain, "
            "unlinked credit line (&ldquo;Built with Muse by Meta&rdquo;) is not a promotion and "
            "remains.</p>"
        ),
        "effect": "No AxiomCode surface promotes a third-party signup.",
        "evidence": [{"label": "Homepage", "url": "https://axiom-code.com/"}],
        "refs": [],
        "disposition": "Closed; verified live the same day (zero matches for the promotion on the audited pages).",
    },
    {
        "id": "2026-11-11-f-ax-10",
        "date": "2026-11-11",
        "title": "Finding F-AX-10: browser submission repaired",
        "category": "Finding",
        "surfaces": ["Web verifier", "Certificate checker", "REST API"],
        "body": (
            "<p><strong>Finding / Fixed.</strong> The flipped web verifier and certificate checker "
            "could render but could not complete a browser submission, because the production API "
            "lacked the required cross-origin (CORS) leg for the site origin. The defect escaped the "
            "public flip and was found in post-deploy verification. The repair added the scoped "
            "browser path (preflight and allow-origin for the site origin on /verify, /check, and "
            "/shell/turn; foreign origins receive nothing) and was verified from the site origin "
            "after deployment. F-AX-10 is closed.</p>"
        ),
        "effect": "Browser submissions on /verify/ and /check/ complete end-to-end; API-key callers "
        "were never affected.",
        "evidence": [
            {"label": "Gate declaration (gate.yaml)", "url": _REPO + "/blob/main/gate.yaml"},
            {"label": "Threat model", "url": _REPO + "/blob/main/docs/THREAT-MODEL.md"},
            {"label": "Security", "url": "https://axiom-code.com/paperwork/security/"},
        ],
        "refs": ["F-AX-10"],
        "disposition": "Closed 2026-11-11 on the gate's post-deploy probes.",
    },
    {
        "id": "2026-11-11-ask-launch",
        "date": "2026-11-11",
        "title": "Ask shell launched",
        "category": "Added",
        "surfaces": ["Ask shell", "Ask explanations"],
        "body": (
            "<p><strong>Added / Status.</strong> Ask entered production at "
            '<a href="/ask/">axiom-code.com/ask/</a>. Ask renders facts from the verification '
            "service and may add an explanation; it does not issue, change, soften, or predict "
            "verdicts — the Lean kernel remains the only judge. The shell is degraded-first: if the "
            "explanation step times out, the service facts are still returned and the missing "
            "explanation is stated. Ask is in release-candidate soak; its graduation decision is "
            "scheduled for 2026-11-18, and explanation latency is a known residual carried in the "
            "soak.</p>"
        ),
        "effect": "Conversational access to verification facts is live, with the fact/judgment "
        "boundary stated on the surface itself.",
        "evidence": [{"label": "Ask", "url": "https://axiom-code.com/ask/"}],
        "refs": [],
        "disposition": "In soak; graduation decision scheduled 2026-11-18.",
    },
    {
        "id": "2026-11-09-public-opening",
        "date": "2026-11-09",
        "title": "Public opening and hosted MCP",
        "category": "Added",
        "surfaces": ["REST API", "Hosted MCP", "Web verifier", "Certificate checker", "Trial"],
        "body": (
            "<p><strong>Added / Status.</strong> AxiomCode opened the REST verification service at "
            'api.axiom-code.com: <code class="inline">POST /verify</code> with an API key, '
            '<code class="inline">POST /check</code>, queued-job status, and the public revocation '
            "list and CA keys. The hosted MCP endpoint also entered production at "
            "https://api.axiom-code.com/mcp/ with seven tools: verify, job_status, "
            "check_certificate, revoked, health, usage_report, and pricing. Trial keys receive 10 "
            "verification cases — verdicts and usage records, no certificates. New with the opening: "
            "a durable FIFO verification queue — when every proof slot is busy, submissions answer "
            '<code class="inline">202</code> with a job id and a checkable position instead of '
            "competing for the engine. The flip package also lands the release-gate declaration for "
            "the service (gate.yaml, threat model, and coverage ledger in the repository). "
            "<strong>Billing remains paused:</strong> credit packs are not on sale, and the Stripe "
            "webhook and Payment Links remain deactivated until pack sales are deliberately opened. "
            "The public service and hosted MCP are in release-candidate soak; their graduation "
            "decision is scheduled for 2026-11-16.</p>"
        ),
        "effect": "The service is open to humans, applications, and agents; certificates unlock when pack sales open.",
        "evidence": [
            {"label": "API health", "url": "https://api.axiom-code.com/health"},
            {"label": "MCP endpoint", "url": "https://api.axiom-code.com/mcp/"},
            {"label": "Gate declaration (gate.yaml)", "url": _REPO + "/blob/main/gate.yaml"},
        ],
        "refs": ["F-AX-4", "F-AX-5"],
        "disposition": "In soak; graduation decision scheduled 2026-11-16. (Migrated from the former "
        "release log, with the hosted-MCP record completed from the launch record.)",
    },
    {
        "id": "2026-10-15-honest-prelaunch",
        "date": "2026-10-15",
        "title": "Honest pre-launch presentation",
        "category": "Changed",
        "surfaces": ["Website"],
        "body": (
            "<p>The site now presents the service as it is: <strong>pre-launch</strong>. Credit packs "
            "are not yet on sale, the API is not yet live, and certificates are not yet being issued. "
            "Buy buttons and operating-service claims stay down until the launch wiring exists. "
            "Release gate: PASS WITH FINDINGS (2026-10-15) — pre-launch presentation is a release "
            "candidate since 2026-10-15, graduates 2026-10-22.</p>"
        ),
        "effect": "Historical entry, migrated unchanged from the former release log. Superseded by "
        "the 2026-11-09 public opening.",
        "evidence": [],
        "refs": [],
        "disposition": "Historical.",
    },
    {
        "id": "2026-09-27-certification-loop",
        "date": "2026-09-27",
        "title": "Certification loop verified end-to-end",
        "category": "Added",
        "surfaces": ["REST API"],
        "body": (
            "<p>On the real engine: submit a Lean 4 specification → verification → signed 90-day "
            "certificate → independent certificate check → revocation. The loop works; production "
            "hosting is the remaining launch step.</p>"
        ),
        "effect": "Historical entry, migrated unchanged from the former release log.",
        "evidence": [],
        "refs": [],
        "disposition": "Historical.",
    },
    {
        "id": "2026-09-26-engine-and-site",
        "date": "2026-09-26",
        "title": "Engine and site",
        "category": "Added",
        "surfaces": ["Website"],
        "body": "<p>Verification engine test suite green; website and launch paperwork published.</p>",
        "effect": "Historical entry, migrated unchanged from the former release log.",
        "evidence": [],
        "refs": [],
        "disposition": "Historical.",
    },
]


def changelog_rss():
    """The /changelog.rss.xml feed (RSS 2.0), generated from the changelog source."""
    items = []
    for e in ENTRIES:
        y, m, d = (int(x) for x in e["date"].split("-"))
        dt = datetime.datetime(y, m, d, 12, 0, tzinfo=datetime.timezone.utc)
        link = f"https://axiom-code.com/changelog/#{e['id']}"
        items.append(
            "<item>"
            f"<title>{_esc(e['title'])}</title>"
            f"<link>{link}</link>"
            f'<guid isPermaLink="false">{_esc(e["id"])}</guid>'
            f"<pubDate>{email.utils.format_datetime(dt)}</pubDate>"
            f"<category>{_esc(e['category'])}</category>"
            f"<description>{_esc(e['effect'])}</description>"
            "</item>"
        )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0"><channel>'
        "<title>AxiomCode — Changelog &amp; service record</title>"
        "<link>https://axiom-code.com/changelog/</link>"
        "<description>Launches, changes, findings, fixes, incidents, and graduations. "
        "Append-only; no silent edits.</description>" + "".join(items) + "</channel></rss>\n"
    )


def changelog_json():
    """The /changelog.json document, generated from the changelog source."""
    return {
        "service": "AxiomCode",
        "title": "Changelog & service record",
        "source": "site/changelog_data.py",
        "html": "https://axiom-code.com/changelog/",
        "rss": "https://axiom-code.com/changelog.rss.xml",
        "entries": ENTRIES,
    }
