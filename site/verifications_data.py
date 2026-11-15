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
    "as_of": "2026-11-15",
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
            "recorded entry is detected by the chain is a different property, and this proof "
            "does not cover it. That property has its own published reports in this register: "
            "the chain immutability proof, and the anchored chain proof that answers the "
            "chain's own stated boundary. The chain is hash-linked; it is not signed.",
        ],
    },
    {
        "report_id": "harness-trace-chain",
        "subject": "Agent harness — trace-ledger hash chain",
        "date": "2026-11-14",
        "kind": "lean_proof",
        "verdict": "proven",
        "summary": (
            "Every entry in our agent harness's trace ledger is hash-linked to the entry "
            "before it: each entry's stored hash is computed over its own content and the "
            "hash it points back to. Proved in Lean 4: if any entry's content no longer "
            "matches its stored hash, or any link in the chain is broken, verification "
            "fails at exactly the first failing entry — and a pass means every check holds "
            "along the whole chain. The boundary is stated on the report: this proves "
            "detection of alteration in a ledger as presented, not protection against a "
            "wholesale rewrite."
        ),
        "method": (
            "Lean 4 formal proof (toolchain v4.22.0), checked by the Lean kernel. The "
            "proof compiles with no placeholder steps (no sorry, no admit) and depends on "
            "no axioms beyond Lean's core three; two of its results depend on no axioms at "
            "all. The subject of the proof is the chain-verification walk, modelled step "
            "for step from the code as built: the six checks each entry faces, their "
            "order, and the state threaded from entry to entry. The hash function is "
            "modelled abstractly — the proof is about the walk, not about SHA-256."
        ),
        "context": (
            "The gatekeeper report in this register names the hash chain as a separate "
            "law, not claimed there; this is that law's own report. The claim under "
            "examination described the ledger as a 'signed hash chain'. Checked against "
            "the code, the chain half is real — hash-linked, with unkeyed SHA-256 — and "
            "is proved here exactly as built. The signed half is not true of the code: "
            "nothing in the append or verification paths signs anything, and there is no "
            "key and no signature field. Signing was ruled a separate, later "
            "strengthening; this report does not claim it."
        ),
        "proven": [
            "Content tampering is detected at the entry. If an entry's stored hash does "
            "not recompute from its content as presented, verification fails at exactly "
            "that entry's position, named as a recomputation failure — provided the "
            "entries before it pass and its own sequence, identity, and link are in order.",
            "A broken link is detected at the entry. If an entry does not point back at "
            "the previous entry's stored hash — or, for the first entry, at the chain's "
            "starting value — verification fails at exactly its position, named as a "
            "link failure.",
            "A pass means the whole chain holds. Verification passes over a ledger "
            "exactly when every entry, at its position, passes every check: sequence, "
            "identity, link, hash recomputation, and the ordering counters all hold "
            "along the entire walk. The equivalence is proved in both directions.",
            "The first failure is the reported failure. If any entry's check fails, "
            "verification fails at or before that entry's position; and any failure "
            "verification reports is the first failing position, with every entry before "
            "it passing. No failing entry is silently passed over.",
            "The harness's own worked example is a theorem. In the harness's test suite, "
            "the second entry of a test ledger is rewritten in a copy of the file, its "
            "stored hash untouched, and verification is observed to break at position 2. "
            "That exact case — first entry intact, second entry's presented content "
            "differing from what its hash was computed over — is proved to fail at "
            "exactly position 2 with the recomputation reason.",
        ],
        "not_proven": [
            "A wholesale rewrite would pass. Every result here concerns a ledger as "
            "presented, checked against its own internal chain. A ledger rewritten in "
            "full — every entry replaced, every hash and link recomputed consistently — "
            "passes this verification completely, and no result here says otherwise, "
            "because none can: the chain is unkeyed, so anyone can recompute it, and "
            "verification has no reference outside the presented entries. The remedy is "
            "a reference held outside the ledger; that is the anchored chain report in "
            "this register, a separate mechanism with its own boundary.",
            "Verification cannot prove an entry was true when it was written. It proves "
            "a ledger was not altered after its entries were committed. A false entry, "
            "honestly committed, chains perfectly.",
            "SHA-256 itself is not proved. The hash function is modelled as an abstract "
            "function. The detection results rest on determinism alone — the same "
            "function, over the same input, at commit and at verification — except for "
            "one step: from 'the content was altered' to 'the recomputation differs'. "
            "That step assumes, for the pair of inputs involved, that their hashes do "
            "not collide. Collision resistance is a standard, believed property of "
            "SHA-256; in this proof it enters only as a named assumption, discharged by "
            "nothing here, and the content reading of the first result carries it.",
            "The proof is about a model of the code, not the running code itself. The "
            "model mirrors the verification walk and the hash construction step for "
            "step, and the correspondence is documented and reviewed — but it is not "
            "itself machine-checked. A proof of the model is not a proof of the running "
            "program.",
            "How an entry becomes the string the hash covers is not proved. The model "
            "takes each entry's canonical form as given. In the running code, one fixed "
            "serialization produces that form, identically at commit and at "
            "verification — a fact read from the code, and the reason the determinism "
            "results are about the real system at all. That two different entries could "
            "never serialize to the same string is not proved; a serialization "
            "collision would defeat the content check before the hash is consulted.",
            "Entries with missing or mistyped fields are outside the model. The "
            "model's entries have every field present and correctly typed, so such "
            "entries cannot be represented. In the running code a missing field makes "
            "verification fail — the detection reading is not weakened — but no theorem "
            "here is about them. The ordering counters are likewise modelled as plain "
            "whole numbers: the code's handling of negative or non-numeric counter "
            "values, which fails verification, cannot be represented in the model, and "
            "one counter check in the code reads a JSON true as the number 1, a case "
            "the model does not have.",
            "Loading the ledger is outside the proof. The theorems concern a list of "
            "entries already loaded. Reading the file and parsing it are not covered — "
            "including the path where a malformed line stops the load and the ledger "
            "is set aside on the parse error, without this verification ever running. "
            "A ledger changing while it is read is likewise outside.",
            "What is done with the verdict is not covered. How the harness's index "
            "uses the verdict — marking a broken ledger quarantined, deciding which "
            "entries count as verified, answering trusted-only queries — is separate "
            "code, not modelled here. The index also keeps its own separate hash chain "
            "over its rows; that chain is not proved by this report.",
            "Concurrency sits outside the proof. Verification runs over a loaded "
            "snapshot; entries appended while a verification runs, or two writers "
            "racing to append, are not covered by these theorems.",
        ],
    },
    {
        "report_id": "harness-trace-chain-anchored",
        "subject": "Agent harness — anchored trace-ledger chain",
        "date": "2026-11-14",
        "kind": "lean_proof",
        "verdict": "proven",
        "summary": (
            "The chain report in this register states its own boundary: a ledger "
            "rewritten in full, honestly re-chained, passes chain verification, because "
            "the chain has no reference outside itself. The harness's answer is "
            "anchoring: from time to time, the chain head — the entry count and the head "
            "hash at that moment — is recorded in custody outside the ledger. Proved in "
            "Lean 4: a rewritten anchored prefix is detected, a new anchor cannot be "
            "taken over a changed prefix, a ledger with no anchor never passes, and the "
            "entries beyond the latest anchor are counted and stated exactly."
        ),
        "method": (
            "Lean 4 formal proof (toolchain v4.22.0), checked by the Lean kernel. The "
            "proof composes the chain proof in this register: its model is imported "
            "unmodified, not restated, and the chain walk is not re-proved. It compiles "
            "with no placeholder steps (no sorry, no admit) and depends on no axioms "
            "beyond Lean's core three; seven of its thirteen stated results depend on "
            "no axioms at all. The subject is the anchoring decision logic — taking an "
            "anchor, and verifying a ledger against its latest anchor — modelled branch "
            "for branch from the code as built."
        ),
        "context": (
            "The remedy chosen for the chain's boundary was anchoring, not signing. A "
            "signing key kept beside the ledger would be readable by whatever could "
            "rewrite the ledger, so signing each entry would buy little inside one "
            "trust boundary while adding key custody. Anchor records are therefore "
            "plain records — an entry count and a head hash — each written to two "
            "custodies outside the ledger itself. Signing is deferred, with a named "
            "trigger: if these records are ever used as evidence for third parties, or "
            "kept between parties who do not trust each other, the anchors — not the "
            "entries — are what would be signed. That would be a code change first and "
            "a new proof second; nothing here claims it."
        ),
        "proven": [
            "Verified means the whole statement. A result of 'anchored-verified', with "
            "its stated tail count, holds exactly when: a latest anchor exists; the "
            "anchored prefix — the ledger's first entries up to the anchor's count — "
            "verifies; the head at that count equals the recorded head; the full chain "
            "verifies; and the tail count is the presented length minus the anchored "
            "count. The equivalence is proved, not just the safe direction.",
            "A rewritten anchored prefix is detected. If the head at the latest "
            "anchor's count differs from the recorded head — or the prefix no longer "
            "verifies, or the ledger is now shorter than its anchor — verification "
            "reports a mismatch. It never reports verified.",
            "Anchors cannot launder a rewrite. Taking a new anchor when the previously "
            "anchored prefix has changed is refused, and nothing is written: the "
            "anchor record is left exactly as it was. In the other direction, the "
            "record grows only over an intact prefix — a successful new anchor "
            "certifies that the previously anchored prefix still stood at the moment "
            "of anchoring.",
            "No anchor, no pass. A ledger with no anchor record returns 'unanchored' — a failure result, never a pass.",
            "The un-anchored tail is counted and stated exactly. A verified result "
            "carries the number of entries beyond the latest anchor, no more and no "
            "less. When that number is positive, the result names those entries as "
            "stale; a freshly taken anchor verifies with a tail of zero. 'Stale' is a "
            "stated count on a verified result — not a separate verdict, and "
            "staleness alone is not a failure.",
            "A break in the tail is named, not passed. If the anchored prefix matches "
            "but the chain breaks beyond it, the result is 'chain broken' — never a "
            "pass — carrying the same exact tail count; and the break is proved to lie "
            "beyond the anchored count, in the tail, since the prefix was just verified.",
        ],
        "not_proven": [
            "Detection is proved given an authentic anchor record. Every result here "
            "assumes the anchor record the verifier reads — its entry count and head "
            "hash — is the record that was actually taken, over the history that was "
            "actually committed. That the custody copies sit outside the ledger "
            "writer's reach — one an append-only record held apart from the ledger, "
            "one a copy delivered to the operator's own mailbox — is an assumption "
            "about the world, not a theorem. A writer who could also rewrite the "
            "custody copies could rewrite the anchor to match a rewritten ledger, and "
            "no theorem here says otherwise, because none can: the anchor is data, not "
            "a signature. What is proved is the comparison itself: if the anchor "
            "record is out of reach, the anchored prefix cannot be rewritten without "
            "detection.",
            "One component hypothesis remains named and unproved. Detection is proved "
            "at the comparison the code performs — a presented head that differs from "
            "the recorded head is caught. The further step, that altering an entry "
            "deep inside the prefix and honestly re-chaining the rest must change the "
            "head, rests on two properties of the real hash construction: its outputs "
            "are fixed-length, so a changed link value inside a hash input cannot be "
            "compensated by the entry content that follows it; and no recomputation "
            "along the way collides. The model treats hashes as arbitrary strings, "
            "where neither property is available, so the step is stated here as the "
            "hypothesis it is. The harness's own planted test observes the concrete "
            "behaviour; the theorem covers the comparison that behaviour feeds.",
            "Entries after the latest anchor are protected by the chain law alone "
            "until the next anchor. A wholesale rewrite of that tail alone, honestly "
            "re-chained, passes chain verification and the anchor comparison alike; "
            "it is caught when the next anchor is attempted over it — the rewritten "
            "tail has become part of the prefix-to-be, and the anchor is refused — or "
            "if it breaks the chain. How large the tail can grow is bounded only "
            "conditionally: it depends on the anchor step actually running after "
            "appends and succeeding. What holds unconditionally is that the tail's "
            "size is always counted and stated exactly.",
            "No signing is claimed. The anchor record is plain data in custody: "
            "nothing here establishes who took an anchor, and there is no key and no "
            "signature anywhere in the anchoring. Signing the anchors is a deferred "
            "strengthening with a named trigger, not part of this proof.",
            "The proof is about a model of the code, not the running code itself. The "
            "model mirrors the anchoring decisions branch for branch, and the "
            "correspondence is documented and reviewed — but it is not itself "
            "machine-checked. A proof of the model is not a proof of the running "
            "program.",
            "Custody itself is outside the proof. Writing and reading the custody "
            "records, their storage and placement, and the delivery of the second "
            "custody copy are operations, not theorems. A damaged or truncated "
            "custody record is a load error in the code and never reaches the "
            "decisions proved here; the same holds for an unreadable ledger. The "
            "second copy's failure handling — the anchor stands on the first custody, "
            "with the failed leg named — is code behaviour read and reported, not a "
            "theorem.",
            "Which records count as a ledger's anchors is outside the proof. The "
            "model takes a ledger's anchor sequence as given and proves facts about "
            "its latest record. The code's matching of records to ledgers — including "
            "its path handling — is not modelled; a fault there would be a selection "
            "failure, not a comparison failure, and is not covered.",
            "The verdicts are proved; their wording is not. The proof is about the "
            "states the verifier reports. The explanation text attached to each state "
            "— including the two different explanations under the one mismatch state — "
            "is presentation, checked by reading, not proved.",
            "Concurrency sits outside the proof. Two anchor-takings racing on one "
            "custody record, or an append racing an anchor, are runtime matters; the "
            "model decides over a snapshot.",
            "The chain proof's boundaries are inherited. This proof builds on the "
            "chain model unchanged, so its limits apply here too: the hash function "
            "itself is not proved, each entry's canonical form is taken as given, "
            "entries with missing or mistyped fields are outside the model, and "
            "loading a ledger is outside both proofs.",
        ],
    },
    {
        "report_id": "harness-trace-quarantine",
        "subject": "Agent harness — trace-ledger index quarantine",
        "date": "2026-11-15",
        "kind": "lean_proof",
        "verdict": "proven",
        "summary": (
            "When our agent harness builds its federated index over the trace ledgers, "
            "every ledger's chain is verified and each entry is marked verified or "
            "quarantined; queries can then be restricted to verified rows only. Proved "
            "in Lean 4: the verified part of a broken ledger is exactly the part of the "
            "chain that verifies, with the split at the first failing entry; a "
            "trusted-only query never returns a quarantined row; and marking an entry "
            "as superseded never deletes it. The boundary is stated on the report: the "
            "status rule reads each entry's own recorded sequence number, and the proof "
            "found — and states — the one case where that rule marks an entry verified "
            "without the chain walk having checked it."
        ),
        "method": (
            "Lean 4 formal proof (toolchain v4.22.0), checked by the Lean kernel. The "
            "proof composes the chain proof in this register: its model is imported "
            "unmodified, and the chain walk is not re-proved. It compiles with no "
            "placeholder steps (no sorry, no admit) and depends on no axioms beyond "
            "Lean's core three; six of its thirty stated results depend on no axioms "
            "at all. The subject is the index build's decision logic — how each "
            "entry's chain status is assigned, how superseded entries are resolved, "
            "what a trusted-only query returns, and the index's own hash chain over "
            "its rows — modelled step for step from the code as built."
        ),
        "context": (
            "The claim under examination ran: 'A ledger with a broken chain is "
            "quarantined and cannot re-enter the federated index until repaired.' "
            "Checked against the code, the mechanism differs from that sentence in two "
            "ways, and this report states the mechanism as it is. A broken ledger's "
            "entries do enter the index: the part of the chain that verifies is marked "
            "verified, the rest is marked quarantined, and the ledger is named in the "
            "build report with its break point. Exclusion happens later, at query "
            "time, and only for queries that ask for verified rows only. And there is "
            "no standing quarantine list to re-enter from: nothing about quarantine "
            "persists between builds — each build re-verifies every ledger and "
            "re-derives every status — so a repaired ledger is verified at the next "
            "build simply because it now verifies. The proof also found one place "
            "where the claim's spirit is breached even in the mechanism's own terms; "
            "that case is stated in the not-proven list below, not smoothed over."
        ),
        "proven": [
            "The verified part of a broken ledger is exactly the part that verifies. "
            "Every entry up to the chain's verified-through point passes every check "
            "the walk applies — sequence, identity, link, hash recomputation, and the "
            "ordering counters — against the state built from the entries before it, "
            "and is marked verified in the index. For any count up to that point, the "
            "ledger's first entries of that count both pass chain verification and "
            "are marked verified.",
            "The split falls exactly at the first failure. The verified-through point "
            "is the ledger's full length when nothing fails, and otherwise the "
            "position just before the first failing entry — never earlier, never "
            "later. The failing entry itself is marked quarantined whenever its "
            "recorded sequence number is its position, which covers every failure in "
            "its content, link, or counters, and sequence failures that skip forward.",
            "Whether a row is marked verified is characterized exactly. A row is "
            "marked verified exactly when its entry's recorded sequence number is at "
            "or below the verified-through point, and quarantined exactly when it is "
            "above. This is proved as an equivalence — the code's rule with nothing "
            "added and nothing removed — and it is the form in which the quarantine "
            "law is true; the boundary case it exposes is stated in the not-proven "
            "list.",
            "A trusted-only query returns no quarantined row. Whatever the query's "
            "other conditions admit, every row it returns is marked verified. The "
            "result is proved for every form of the query's time-window condition, "
            "because the verified-only condition is a separate conjunct of the query "
            "and does not depend on the others.",
            "Resolution never deletes. Every entry of every cleanly loaded ledger "
            "appears as exactly one row in the index. Marking an entry as superseded "
            "or tombstoned changes only that row's currency flag and records what "
            "superseded it; the row remains in the index, its chain status is "
            "untouched, and the ledger itself is never modified by the index. The two "
            "marks are independent: an entry can be verified and no longer current "
            "at once.",
            "The index's own chain detects alteration. The index hash-chains its "
            "rows in the same construction as the ledger chain. Verifying that chain "
            "passes exactly when every row's link and recomputation hold; a failure "
            "is the first failure, at its position; and a row whose content was "
            "altered after the index was written fails recomputation at exactly its "
            "position — under the named no-collision assumption described in the "
            "not-proven list, as in the chain report.",
            "The harness's own test cases are theorems. The test ledger whose second "
            "entry is rewritten: the first entry's row is verified, the rewritten "
            "entry's row and the following entry's row are quarantined, and a "
            "trusted-only query over that ledger can return only the first entry's "
            "row. The test where a tombstone supersedes an entry in a fully "
            "verifying ledger: the target's row is present, marked no longer "
            "current, naming the tombstone — and still marked verified. And when "
            "every ledger in a build verifies, every row any query returns is "
            "verified.",
        ],
        "not_proven": [
            "One case is marked verified without being chain-checked. The status "
            "rule compares each entry's own recorded sequence number against the "
            "verified-through point; it never looks at the entry's position. The "
            "chain walk stops at the first failure, so it never examines the "
            "sequence numbers at or beyond the break. An entry there whose recorded "
            "sequence number is duplicated or regressed — at or below the "
            "verified-through point — is therefore marked verified without ever "
            "having been checked, is counted in the build report's trusted-row "
            "count, and is served by trusted-only queries. Ledgers written by the "
            "harness's own append path cannot produce this: that path assigns each "
            "entry a sequence number equal to its position, so beyond the break the "
            "number is always above the point. A hand-crafted ledger file can "
            "produce it, because loading a ledger validates nothing about its "
            "sequence numbers. This gap was found by this proof, and it has since "
            "been ruled that the code be fixed first and the law then re-proved: "
            "the fix and its re-proof follow as a separate step, and that step's "
            "report will be added to this register when it closes. Nothing here "
            "pre-claims either. This report stands unchanged by the ruling — it is "
            "the accurate record of the law as proved against the code as it then "
            "stood.",
            "A broken index chain is detected, not refused. The query path checks "
            "the index's own chain before answering and, on a break, prints a "
            "warning — and still serves the results. Detection is proved exactly; "
            "no path in the code refuses to answer, so there is no refusal for a "
            "proof to establish. This behaviour was likewise found by this proof "
            "and is covered by the same ruling described above: the fix and its "
            "re-proof follow as a separate step, and this report records the "
            "behaviour as proved against the code as it then stood.",
            "SHA-256 itself is not proved. As in the chain report, the hash "
            "function is modelled as an abstract function, and the results that read "
            "'altered content is detected' — for a ledger entry, and for a row of "
            "the index — rest on a named assumption: that the altered and original "
            "contents do not hash to the same value. Collision resistance is a "
            "standard, believed property of SHA-256; in this proof it enters only "
            "as that named assumption, discharged by nothing here.",
            "Quarantine is re-derived on every build; it is not a state. Nothing "
            "persists between builds: each build re-verifies every ledger and "
            "re-derives every status from the files as they then stand. A ledger "
            "that fails to load at all — a file with a malformed line, for example "
            "— takes a stronger path than row-level quarantine: it is named in the "
            "build report with its load error and contributes no rows at all, not "
            "even the entries that were read before the bad line. The marking "
            "proved here applies to ledgers that load cleanly and then fail chain "
            "verification.",
            "The proof is about a model of the code, not the running code itself. "
            "The model mirrors the index build's decisions step for step, and the "
            "correspondence is documented and reviewed — but it is not itself "
            "machine-checked. A proof of the model is not a proof of the running "
            "program.",
            "Reading, writing, and timing sit outside the proof. Loading the "
            "ledger files, writing the index file, and anything that changes while "
            "a build runs are not covered; neither is concurrency — two builds at "
            "once, or a build racing an append. Some details are abstracted rather "
            "than modelled: the query's time-window condition is treated as an "
            "arbitrary test, which cannot weaken the exclusion result, since that "
            "result is proved for every such test; the build's final ordering of "
            "rows rearranges them without changing any row; a few row fields that "
            "no part of this law reads are omitted from the model; and the record "
            "of what supersedes an entry is modelled as naming its target, where "
            "the code asks only that a target be present — the one divergence, an "
            "empty-string target, cannot arise for real entry identities.",
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
