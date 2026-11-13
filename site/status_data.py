"""Canonical AxiomCode status source — the single source of truth for every
public status fact on axiom-code.com.

Rendered or checked from here (never typed independently elsewhere):
  - /status/ page and /status.json            (pages_status.py, run.py)
  - .well-known/axiomcode.json status section (pages_blog.py)
  - llms.txt status section                   (pages_blog.py)
  - /practice/ known-limitations section      (pages_status.py)
  - pricing availability cross-check          (check_drift.py)

Rules (blueprint C1/C3):
  - `availability` and `lifecycle` are separate fields. A surface may be
    live + in_soak at the same time.
  - `graduates_on` is a SCHEDULED transition, never a completed claim.
    Graduation happens only through a recorded gate/owner decision, which
    is applied by editing this file and adding a changelog entry.
  - Every surface carries an owner and a last_verified_at date.
  - Non-built items are first-class records. Silence is not a status.
"""

STATUS_META = {
    "service": "AxiomCode",
    "as_of": "2026-11-12",
    "timezone": "America/Edmonton",
    "source": "site/status_data.py",
    "status_page": "https://axiom-code.com/status/",
}

AVAILABILITY_STATES = ("live", "paused", "unavailable")
LIFECYCLE_STATES = ("live", "paused", "in_soak", "in_design", "not_built")

AVAILABILITY_LABELS = {"live": "Live", "paused": "Paused", "unavailable": "Unavailable"}
LIFECYCLE_LABELS = {
    "live": "Live",
    "paused": "Paused",
    "in_soak": "In soak",
    "in_design": "In design",
    "not_built": "Not built",
}

_OWNER = "AxiomCode service owner"
_VERIFIED = "2026-11-12"

SURFACES = [
    {
        "surface_id": "rest_api",
        "name": "REST API",
        "availability": "live",
        "lifecycle": "in_soak",
        "public_since": "2026-11-09",
        "graduates_on": "2026-11-16",
        "canonical_url": "https://api.axiom-code.com",
        "summary": "The verification service: verify, certificate check, queued jobs, "
        "revocation list, CA keys, health.",
        "evidence": [
            {"label": "Health", "url": "https://api.axiom-code.com/health"},
            {"label": "OpenAPI", "url": "https://api.axiom-code.com/openapi.json"},
        ],
        "known_limits": [
            "In release-candidate soak as part of the 2026-11-09 public flip. Graduation is a recorded "
            "gate decision scheduled for 2026-11-16 — the date alone does not graduate it."
        ],
        "owner": _OWNER,
        "last_verified_at": _VERIFIED,
    },
    {
        "surface_id": "hosted_mcp",
        "name": "Hosted MCP",
        "availability": "live",
        "lifecycle": "in_soak",
        "public_since": "2026-11-09",
        "graduates_on": "2026-11-16",
        "canonical_url": "https://api.axiom-code.com/mcp/",
        "summary": "MCP endpoint for agents: same API key, same queue, seven tools "
        "(verify, job_status, check_certificate, revoked, health, usage_report, pricing).",
        "evidence": [
            {"label": "MCP endpoint", "url": "https://api.axiom-code.com/mcp/"},
            {"label": "API documentation", "url": "https://axiom-code.com/docs/api/"},
        ],
        "known_limits": [
            "In release-candidate soak with the public flip; graduation is a recorded gate decision "
            "scheduled for 2026-11-16."
        ],
        "owner": _OWNER,
        "last_verified_at": _VERIFIED,
    },
    {
        "surface_id": "local_mcp",
        "name": "Local MCP",
        "availability": "live",
        "lifecycle": "live",
        "public_since": None,
        "graduates_on": None,
        "canonical_url": "https://github.com/nrupala/axiomcode",
        "summary": "The MCP server also ships in the AxiomCode repository for local use, against the same API. "
        "Documented separately from the hosted endpoint.",
        "evidence": [{"label": "Repository", "url": "https://github.com/nrupala/axiomcode"}],
        "known_limits": [],
        "owner": _OWNER,
        "last_verified_at": _VERIFIED,
    },
    {
        "surface_id": "web_verifier",
        "name": "Web verifier",
        "availability": "live",
        "lifecycle": "in_soak",
        "public_since": "2026-11-09",
        "graduates_on": "2026-11-16",
        "canonical_url": "https://axiom-code.com/verify/",
        "summary": "Browser verification form on this site, backed by the live API.",
        "evidence": [{"label": "Web verifier", "url": "https://axiom-code.com/verify/"}],
        "known_limits": [
            "Browser submission was broken at the public flip (finding F-AX-10: the API lacked the "
            "cross-origin leg for the site origin) and was repaired and re-verified on 2026-11-11."
        ],
        "owner": _OWNER,
        "last_verified_at": _VERIFIED,
    },
    {
        "surface_id": "certificate_checker",
        "name": "Certificate checker",
        "availability": "live",
        "lifecycle": "in_soak",
        "public_since": "2026-11-09",
        "graduates_on": "2026-11-16",
        "canonical_url": "https://axiom-code.com/check/",
        "summary": "Browser certificate checker; the revocation list and CA public keys are public, "
        "so certificates can also be validated offline.",
        "evidence": [
            {"label": "Certificate checker", "url": "https://axiom-code.com/check/"},
            {"label": "Revocation list", "url": "https://api.axiom-code.com/revoked"},
            {"label": "CA public keys", "url": "https://api.axiom-code.com/.well-known/axiomcode-keys.json"},
        ],
        "known_limits": [
            "Browser submission was broken at the public flip (finding F-AX-10) and was repaired and "
            "re-verified on 2026-11-11."
        ],
        "owner": _OWNER,
        "last_verified_at": _VERIFIED,
    },
    {
        "surface_id": "ask_shell",
        "name": "Ask shell",
        "availability": "live",
        "lifecycle": "in_soak",
        "public_since": "2026-11-11",
        "graduates_on": "2026-11-18",
        "canonical_url": "https://axiom-code.com/ask/",
        "summary": "Conversational access to the service. Ask renders facts from service responses and "
        "may add an explanation; it does not issue, change, soften, or predict verdicts.",
        "evidence": [{"label": "Ask", "url": "https://axiom-code.com/ask/"}],
        "known_limits": ["In release-candidate soak; graduation is a recorded gate decision scheduled for 2026-11-18."],
        "owner": _OWNER,
        "last_verified_at": _VERIFIED,
    },
    {
        "surface_id": "ask_explanations",
        "name": "Ask explanations",
        "availability": "live",
        "lifecycle": "in_soak",
        "public_since": "2026-11-11",
        "graduates_on": "2026-11-18",
        "canonical_url": "https://axiom-code.com/ask/",
        "summary": "The explanation step of the Ask shell, layered over service facts.",
        "evidence": [{"label": "Ask", "url": "https://axiom-code.com/ask/"}],
        "known_limits": [
            "Degraded-first: the explanation step may time out under load. The service facts are still "
            "returned and the missing explanation is stated. Explanation latency is an open residual "
            "carried in the soak."
        ],
        "owner": _OWNER,
        "last_verified_at": _VERIFIED,
    },
    {
        "surface_id": "trial",
        "name": "Free trial",
        "availability": "live",
        "lifecycle": "live",
        "public_since": "2026-11-09",
        "graduates_on": None,
        "canonical_url": "https://axiom-code.com/pricing/",
        "summary": "The first 10 verification cases per API key are free: verdicts and usage records, "
        "never certificates.",
        "evidence": [{"label": "Pricing", "url": "https://axiom-code.com/pricing/"}],
        "known_limits": [],
        "owner": _OWNER,
        "last_verified_at": _VERIFIED,
    },
    {
        "surface_id": "billing",
        "name": "Billing / credit packs",
        "availability": "paused",
        "lifecycle": "paused",
        "public_since": None,
        "graduates_on": None,
        "canonical_url": "https://axiom-code.com/pricing/",
        "summary": "Credit packs are priced (US$10 / $50 / $200) but not on sale. The Stripe webhook and "
        "Payment Links are deactivated until pack sales are deliberately opened.",
        "evidence": [{"label": "Pricing", "url": "https://axiom-code.com/pricing/"}],
        "known_limits": ["No purchase path is open. Checkout answers 501 while billing is paused."],
        "owner": _OWNER,
        "last_verified_at": _VERIFIED,
    },
    {
        "surface_id": "paid_certificates",
        "name": "Paid certificates",
        "availability": "paused",
        "lifecycle": "paused",
        "public_since": None,
        "graduates_on": None,
        "canonical_url": "https://axiom-code.com/pricing/",
        "summary": "The rule is live in the service: a completed paid verification receives a signed "
        "certificate recording PASSED or FAILED. Certificates are not purchasable while billing is paused.",
        "evidence": [
            {"label": "Certificate Policy", "url": "https://axiom-code.com/paperwork/certificate-policy/"},
            {"label": "Pricing", "url": "https://axiom-code.com/pricing/"},
        ],
        "known_limits": ["Unlock when pack sales open; the trial never produces a certificate."],
        "owner": _OWNER,
        "last_verified_at": _VERIFIED,
    },
    {
        "surface_id": "smart_contract_verification",
        "name": "Smart-contract verification",
        "availability": "unavailable",
        "lifecycle": "in_design",
        "public_since": None,
        "graduates_on": None,
        "canonical_url": "https://axiom-code.com/status/",
        "summary": "Design complete 2026-11-11 (Solidity/EVM first, ingest at Yul IR, fixed property packs). "
        "Increment 0 — the feasibility spike — was approved on 2026-11-12 and is running.",
        "evidence": [{"label": "Status", "url": "https://axiom-code.com/status/"}],
        "known_limits": ["Not a current capability. Nothing on this site presents it as one."],
        "owner": _OWNER,
        "last_verified_at": _VERIFIED,
    },
    {
        "surface_id": "offline_verifier",
        "name": "Offline / air-gapped verifier",
        "availability": "unavailable",
        "lifecycle": "not_built",
        "public_since": None,
        "graduates_on": None,
        "canonical_url": "https://axiom-code.com/status/",
        "summary": "Running the verification engine itself offline or air-gapped, for enterprise use. "
        "Approved in the build queue; not built.",
        "evidence": [{"label": "Status", "url": "https://axiom-code.com/status/"}],
        "known_limits": [
            "Offline certificate validation IS available today (public CA keys and revocation list). "
            "Offline verification is a different capability and is not built."
        ],
        "owner": _OWNER,
        "last_verified_at": _VERIFIED,
    },
    {
        "surface_id": "l3_agent",
        "name": "L3 proof-generating agent",
        "availability": "unavailable",
        "lifecycle": "not_built",
        "public_since": None,
        "graduates_on": None,
        "canonical_url": "https://axiom-code.com/status/",
        "summary": "An agent that generates proofs for the kernel to judge. Approved in the build queue; "
        "not built. Ask explains and orchestrates existing service calls; it is not an L3 agent.",
        "evidence": [{"label": "Status", "url": "https://axiom-code.com/status/"}],
        "known_limits": [],
        "owner": _OWNER,
        "last_verified_at": _VERIFIED,
    },
    {
        "surface_id": "verified_library",
        "name": "Verified library (complete L2)",
        "availability": "unavailable",
        "lifecycle": "not_built",
        "public_since": None,
        "graduates_on": None,
        "canonical_url": "https://axiom-code.com/status/",
        "summary": "A complete L2 verified library. Partial L2 work exists in the repository; the "
        "complete library is not built and no completeness claim is made.",
        "evidence": [{"label": "Repository", "url": "https://github.com/nrupala/axiomcode"}],
        "known_limits": ["The verified library is incomplete."],
        "owner": _OWNER,
        "last_verified_at": _VERIFIED,
    },
]


def status_json():
    """The /status.json document, generated from the canonical source."""
    return {"meta": dict(STATUS_META), "surfaces": SURFACES}


def wellknown_surfaces():
    """Compact per-surface state for .well-known/axiomcode.json."""
    return [
        {
            "id": s["surface_id"],
            "name": s["name"],
            "availability": s["availability"],
            "lifecycle": s["lifecycle"],
            "public_since": s["public_since"],
            "graduates_on": s["graduates_on"],
            "url": s["canonical_url"],
        }
        for s in SURFACES
    ]


def llms_status_section():
    """The status section of llms.txt, generated from the canonical source."""
    lines = [
        "## Status (generated from the canonical status source)",
        "",
        "Full status: https://axiom-code.com/status/ — machine-readable: https://axiom-code.com/status.json",
        "Changelog & service record: https://axiom-code.com/changelog/",
        "How the practice runs (gates, soak, certificates, error reporting): https://axiom-code.com/practice/",
        "",
    ]
    for s in SURFACES:
        bits = [f"{s['name']}: {s['availability']} / {s['lifecycle']}"]
        if s["public_since"]:
            bits.append(f"public since {s['public_since']}")
        if s["graduates_on"]:
            bits.append(f"graduation decision scheduled {s['graduates_on']}")
        lines.append("- " + "; ".join(bits) + f" — {s['canonical_url']}")
    lines.append("")
    lines.append(
        "Availability and lifecycle are separate: a surface can be live and still in "
        "release-candidate soak. A scheduled graduation date is not a graduation — "
        "graduation is a recorded gate decision."
    )
    return "\n".join(lines) + "\n"
