"""Canonical AxiomCode verification-reports source — the single source of
truth for every published verification report on axiom-code.com.

Rendered or checked from here (never typed independently elsewhere):
  - /verifications/ index and /verifications/<report_id>/ pages
    (pages_verifications.py)
  - /verifications.json                          (run.py)

The register exists under the Trust Doctrine (2026-11-14): AxiomCode's
trust case is proof by our own products. Every product we build is
verified — through the release gate, and for deterministic cores by
Lean 4 proof — and the reports are published here.

Rules:
  - Every entry states WHAT WAS PROVEN and WHAT WAS NOT PROVEN, in plain
    words. The boundary is part of the report, not a footnote.
  - An entry without a `not_proven` field — or with an empty one — does
    not render. The page generator skips it and the drift checks fail:
    a report that claims without bounding is not published here.
  - Only completed reports appear. Work in progress is not
    pre-published; a report is added when its underlying record exists
    and is complete.
  - Public rendering carries the law, the verdict, and the boundary —
    never internal file paths, host addresses, or topology.
"""

REPORTS_META = {
    "service": "AxiomCode",
    "as_of": "2026-11-14",
    "timezone": "America/Edmonton",
    "source": "site/verifications_data.py",
    "index_page": "https://axiom-code.com/verifications/",
}

KIND_LABELS = {
    "gate_verdict": "Release-gate verdict",
    "lean_proof": "Lean 4 proof",
    "both": "Gate verdict + Lean 4 proof",
}

VERDICT_LABELS = {
    "proven": "Proven",
    "passed": "Passed",
    "passed_with_findings": "Passed with findings",
    "failed": "Failed",
}

REPORTS = [
    {
        "report_id": "harness-trace-gatekeeper",
        "subject": "Agent harness — trace-ledger gatekeeper",
        "date": "2026-11-14",
        "kind": "lean_proof",
        "verdict": "proven",
        "summary": (
            "The gatekeeper that decides what may be appended to our agent harness's trace "
            "ledger must refuse any entry whose stated origin is blank or unregistered for "
            "its lane — and a refusal must leave the ledger untouched. Proved in Lean 4 "
            "against the strengthened code, including the fail-closed case: an empty or "
            "unreadable registry refuses everything."
        ),
        "method": (
            "Lean 4 formal proof (toolchain v4.22.0), checked by the Lean kernel. The proof "
            "compiles with no placeholder steps (no sorry, no admit) and depends on no axioms "
            "beyond Lean's core three. The subject of the proof is the gatekeeper's append-path "
            "decision logic, modelled step for step from the code as built."
        ),
        "context": (
            "This law was first proved on 2026-11-14 in a weaker form: an entry needed only a "
            "non-blank origin. Comparing the claim against the code showed the weaker form was "
            "all the code enforced, so the code was strengthened first — origins must now be "
            "registered per lane, fail-closed — and the stronger law was then proved against "
            "the strengthened code. Both proofs stand; this report states the current, "
            "stronger law."
        ),
        "proven": [
            "A blank origin is refused, by name. An entry whose stated origin (its provenance) "
            "is empty or all whitespace is turned away, and the refusal carries the reason.",
            "An unregistered origin is refused, by name. An entry whose stated origin is not "
            "on the registered list for its lane is turned away with a refusal that names the "
            "origin and the lane. Registration for a different lane does not count.",
            "Acceptance means a registered origin. Every entry the gatekeeper accepts carries "
            "an origin string that is registered for its lane — and therefore non-blank.",
            "A refusal leaves the ledger untouched. When the gatekeeper refuses, no append "
            "happens: the ledger's state after the refusal is exactly what it was before.",
            "An empty or unreadable registry refuses everything. If the registered-origin "
            "list is empty — or cannot be loaded at all — every candidate entry is refused. "
            "The gate fails closed.",
        ],
        "not_proven": [
            "Membership is not signing. The proof establishes that an accepted entry's origin "
            "string is on the registered list. It does not establish that the named origin "
            "actually wrote the entry: there is no signature anywhere in this append path, no "
            "key, and no check that would catch a caller simply claiming a registered string.",
            "The proof is about a model of the code, not the running code itself. The model "
            "mirrors the gatekeeper's decision logic step for step, and the correspondence is "
            "documented and reviewed — but it is not itself machine-checked. A proof of the "
            "model is not a proof of the running program.",
            "Writing and storage sit outside the proof. The 'ledger untouched' result covers "
            "refusals, where nothing is written. A failure during the write itself — for "
            "example a storage error part-way through an append — could leave a partial "
            "record; neither the code nor the proof rules that out.",
            "Concurrency sits outside the proof. The gatekeeper takes no lock; two writers "
            "appending at the same moment are not covered by these theorems.",
            "The module's own path is what is covered. The ledger is a file, and the proof "
            "covers appends that go through the gatekeeper. It cannot prevent other code from "
            "writing to the file directly: 'appends only through the gatekeeper' is a property "
            "of the module's own paths, not a boundary the proof enforces.",
            "The hash chain is a separate law, not claimed here. That a later edit to a "
            "recorded entry is detected by the chain is a different property, whose proof step "
            "is in progress. The chain is hash-linked; it is not signed.",
        ],
    },
]


def renderable(report):
    """A report renders only if it bounds its own claim: every required
    field present, and `not_proven` a non-empty list of non-empty strings.
    The generator renders renderable reports only; the drift checks fail
    the build when any source entry is not renderable."""
    if not report.get("report_id") or not report.get("subject"):
        return False
    if report.get("kind") not in KIND_LABELS or report.get("verdict") not in VERDICT_LABELS:
        return False
    if not report.get("date") or not report.get("summary") or not report.get("method"):
        return False
    proven = report.get("proven")
    if not proven or not all(isinstance(p, str) and p.strip() for p in proven):
        return False
    not_proven = report.get("not_proven")
    if not not_proven or not all(isinstance(p, str) and p.strip() for p in not_proven):
        return False
    return True


def verifications_json():
    """The /verifications.json document, generated from the canonical source."""
    return {"meta": dict(REPORTS_META), "reports": REPORTS}
