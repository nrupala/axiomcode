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
        "id": "2026-11-15-verification-reports-quarantine-fixed",
        "date": "2026-11-15",
        "title": "Verification report added — the index quarantine, re-proved against the fixed code",
        "category": "Added",
        "surfaces": ["Website", "Verification reports"],
        "body": (
            '<p>The <a href="/verifications/">verification reports</a> register gains the '
            "fixed-code quarantine report — the re-proof the quarantine report&rsquo;s own "
            "boundary called for. The "
            '<a href="/verifications/harness-trace-quarantine-fixed/">fixed-code index '
            "quarantine report</a>: proved in Lean 4, against the index code as fixed, that "
            "every entry at or after a ledger chain&rsquo;s first failure is quarantined by "
            "position, whatever its recorded sequence number claims; that the verified rows "
            "are exactly the entries the chain walk checked, and the build&rsquo;s "
            "trusted-row count exactly that depth; that a broken index chain now makes the "
            "query refuse and serve no rows, in every query mode, where the code as first "
            "built warned and served anyway; and that on an intact index the query answers "
            "with exactly the rows its filters admit — with its boundary stated on the "
            "report itself (the query path&rsquo;s load-error refusal is read from the "
            "code but not modelled; the detection results carry the same named "
            "no-collision assumption as the chain reports; a consistently rewritten index "
            "is, to this law, an intact one; and the query path&rsquo;s final recheck is "
            "proved vacuous). For the code as it now stands, this report supersedes the "
            "earlier quarantine report&rsquo;s characterization of the status rule; that "
            "report is unchanged and stands as the record of the law as proved against "
            "the code as it then stood. The chain report&rsquo;s boundary note on what "
            "the verdict feeds now also points to the two quarantine reports as that "
            "property&rsquo;s own published records.</p>"
        ),
        "effect": "Anyone can now read the harness's index law in its strong form — "
        "quarantine by position, unconditional — alongside the record of the weaker form "
        "it replaced and the case that forced the fix.",
        "evidence": [
            {"label": "Verification reports", "url": "https://axiom-code.com/verifications/"},
            {
                "label": "Fixed-code index quarantine report",
                "url": "https://axiom-code.com/verifications/harness-trace-quarantine-fixed/",
            },
        ],
        "refs": [],
        "disposition": "Live on the site; the register grows by completed records only.",
    },
    {
        "id": "2026-11-15-verification-reports-quarantine",
        "date": "2026-11-15",
        "title": "Verification report added — the trace-ledger index quarantine, proved",
        "category": "Added",
        "surfaces": ["Website", "Verification reports"],
        "body": (
            '<p>The <a href="/verifications/">verification reports</a> register gains the '
            "quarantine report, the third law of the harness proof round. The "
            '<a href="/verifications/harness-trace-quarantine/">index quarantine report</a>: '
            "proved in Lean 4 that the verified part of a broken ledger is exactly the part "
            "of its chain that verifies, with the split at the first failing entry; that a "
            "trusted-only query never returns a quarantined row; that superseding an entry "
            "never deletes it; and that the index&rsquo;s own hash chain detects alteration "
            "at exactly its position — with its boundary stated on the report itself (the "
            "status rule reads each entry&rsquo;s own recorded sequence number, and the "
            "proof states the one case — a duplicated or regressed sequence number at or "
            "beyond the break, reachable only in a hand-crafted ledger file — where an "
            "entry is marked verified without being chain-checked; a query over a broken "
            "index chain warns and still serves; quarantine is re-derived on every build "
            "rather than held as a state; and the step from altered content to a differing "
            "recomputation carries a named no-collision assumption). Both gaps were found "
            "by the proof itself; fixing the code first and then re-proving has since been "
            "ruled, and follows as a separate step whose report will join the register when "
            "it closes — this report stands as the record of the law as proved against the "
            "code as it then stood.</p>"
        ),
        "effect": "Anyone can now read the harness's index law as proved — including the "
        "one case the proof found where the code's status rule trusts a sequence number "
        "the chain walk never reached.",
        "evidence": [
            {"label": "Verification reports", "url": "https://axiom-code.com/verifications/"},
            {
                "label": "Index quarantine report",
                "url": "https://axiom-code.com/verifications/harness-trace-quarantine/",
            },
        ],
        "refs": [],
        "disposition": "Live on the site; the register grows by completed records only.",
    },
    {
        "id": "2026-11-14-verification-reports-chain-anchored",
        "date": "2026-11-14",
        "title": "Two verification reports added — the trace-ledger chain, proved, and its anchoring, proved",
        "category": "Added",
        "surfaces": ["Website", "Verification reports"],
        "body": (
            '<p>The <a href="/verifications/">verification reports</a> register gains two reports, '
            "completing the chain law the first report named as a separate step. The "
            '<a href="/verifications/harness-trace-chain/">chain immutability report</a>: proved in '
            "Lean 4 that an entry whose content no longer matches its stored hash, or a broken link, "
            "fails verification at exactly the first failing entry, and that a pass means every check "
            "holds along the whole chain — with its boundary stated on the report itself (detection "
            "within a ledger as presented; a wholesale rewrite, honestly re-chained, would pass the "
            "chain alone; the hash function itself is not proved, and the step from altered content "
            "to a differing recomputation carries a named no-collision assumption). The "
            '<a href="/verifications/harness-trace-chain-anchored/">anchored chain report</a>: the '
            "harness&rsquo;s answer to that boundary — anchor records of the chain head, held in "
            "custody outside the ledger — proved to detect a rewritten anchored prefix, to refuse "
            "new anchors over a changed prefix, never to pass an unanchored ledger, and to state "
            "the un-anchored tail exactly, with its own boundary stated on the report (detection is "
            "proved given an authentic anchor record; that the custody copies sit outside the "
            "ledger writer&rsquo;s reach is an assumption about the world, not a theorem; one "
            "component hypothesis remains named and unproved; no signing is claimed). The "
            "gatekeeper report&rsquo;s boundary note is updated to point at both reports; its own "
            "proof and boundary are unchanged.</p>"
        ),
        "effect": "Anyone can now read the harness's ledger proofs as one chain of reports — "
        "gatekeeper, chain, anchored chain — each stating exactly what it established and where "
        "it stops.",
        "evidence": [
            {"label": "Verification reports", "url": "https://axiom-code.com/verifications/"},
            {
                "label": "Chain immutability report",
                "url": "https://axiom-code.com/verifications/harness-trace-chain/",
            },
            {
                "label": "Anchored chain report",
                "url": "https://axiom-code.com/verifications/harness-trace-chain-anchored/",
            },
        ],
        "refs": [],
        "disposition": "Live on the site; the register grows by completed records only.",
    },
    {
        "id": "2026-11-14-verification-reports",
        "date": "2026-11-14",
        "title": "Verification reports published — our own products, proven and bounded in public",
        "category": "Added",
        "surfaces": ["Website", "Verification reports"],
        "body": (
            "<p>AxiomCode&rsquo;s trust case is proof by our own products: every product we build "
            "is verified — through the release gate, and for deterministic cores by Lean 4 proof — "
            'and the reports are now published in a dedicated <a href="/verifications/">verification '
            "reports</a> register. Every report states what was proven and what was not proven, in "
            "plain words; a report without the second statement does not appear. The register is "
            "generated from a canonical source, and CI drift checks fail when any rendering "
            "disagrees with it. The first report is our own agent harness&rsquo;s trace-ledger "
            "gatekeeper: proved in Lean 4 to refuse blank or unregistered origins by name, to "
            "leave the ledger untouched on refusal, and to refuse everything when its registry "
            "is empty — with its boundary stated on the report itself (registration is membership, "
            "not signing; the proof covers a model of the code, not the running program; the hash "
            "chain&rsquo;s own law is a separate step, in progress and not claimed). Further "
            "reports are added as their records complete; work in progress is not pre-published.</p>"
        ),
        "effect": "Anyone can read exactly what our verification of our own products established — "
        "and where each proof stops.",
        "evidence": [
            {"label": "Verification reports", "url": "https://axiom-code.com/verifications/"},
            {
                "label": "First report: trace-ledger gatekeeper",
                "url": "https://axiom-code.com/verifications/harness-trace-gatekeeper/",
            },
        ],
        "refs": [],
        "disposition": "Live on the site; the register grows by completed records only.",
    },
    {
        "id": "2026-11-14-p2-redesign-docs",
        "date": "2026-11-14",
        "title": "Website redesign (P2) and the AppDocStudio documentation rebuild",
        "category": "Changed",
        "surfaces": ["Website", "Documentation", "Home", "Status", "About", "Contact"],
        "body": (
            "<p>The website was redesigned and the documentation rebuilt to the house documentation "
            "standard. The home page now carries an interactive artefact loop that runs the real "
            "trial on the visitor&rsquo;s own API key (no shared demo key exists), with availability "
            'and lifecycle chips generated from the canonical status source. The <a href="/status/">status '
            'page</a> presents all fourteen surfaces in one table. The <a href="/docs/">documentation</a> '
            "is now Di&aacute;taxis-first — tutorials, guides, reference, explanation — with seven role "
            "packs (Guest, Users, Developers, Maintainers, Regulators, Admins, Ops); the Maintainers pack "
            "is published as an evidence-on-request boundary, its structure public and its internals not. "
            "Every docs page carries its audience, type, version, last-verified date, source artefact, and "
            'a Markdown mirror. New <a href="/about/">About</a> and <a href="/contact/">Contact</a> pages '
            "replace the placeholder routes that previously returned the home page. The REST API "
            "reference now names the live OpenAPI document as the contract of record. No service "
            "behaviour changed: this entry records presentation and documentation only, and the "
            "graduations scheduled for 16 and 18 November remain pending gate decisions.</p>"
        ),
        "effect": "Visitors, relying parties, and agents read the same generated facts in a "
        "documentation set shaped for their role; nothing about the service, its verdicts, or its "
        "billing state changed.",
        "evidence": [
            {"label": "Home", "url": "https://axiom-code.com/"},
            {"label": "Documentation", "url": "https://axiom-code.com/docs/"},
            {"label": "Status", "url": "https://axiom-code.com/status/"},
            {"label": "About", "url": "https://axiom-code.com/about/"},
            {"label": "Contact", "url": "https://axiom-code.com/contact/"},
        ],
        "refs": [],
        "disposition": "Live on the site; the contact form's receiving endpoint is a named open "
        "item (the house per-site form pipeline is not yet wired for this domain) — the form "
        "degrades to a pre-addressed email rather than failing silently.",
    },
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
