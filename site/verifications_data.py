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
            "over its rows; that chain is not proved by this report. That property has "
            "its own published reports in this register: the index quarantine proof, "
            "and the fixed-code index quarantine proof.",
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
    {
        "report_id": "harness-trace-quarantine-fixed",
        "subject": "Agent harness — trace-ledger index quarantine, fixed code",
        "date": "2026-11-15",
        "kind": "lean_proof",
        "verdict": "proven",
        "summary": (
            "When our agent harness builds its federated index over the trace "
            "ledgers, every ledger's chain is verified and each entry is marked "
            "verified or quarantined. The quarantine report in this register "
            "proved that law against the index code as first built — and found "
            "the one case where its status rule marked an entry verified "
            "without the chain walk having checked it. The code was then "
            "fixed: status is now assigned by each entry's position, and a "
            "query over a broken index chain is refused outright. This report "
            "is the re-proof against the fixed code, in Lean 4: every entry "
            "at or after the first chain failure is quarantined, whatever its "
            "recorded sequence number claims; the verified rows are exactly "
            "the entries the chain walk checked; and a broken index chain "
            "makes the query refuse and serve no rows, in every query mode."
        ),
        "method": (
            "Lean 4 formal proof (toolchain v4.22.0), checked by the Lean "
            "kernel. The proof composes the earlier quarantine proof in this "
            "register: its model is imported unmodified, the clauses the fix "
            "did not touch are carried over from it, and what the fix changed "
            "— the status rule and the query's refusal — is proved new. It "
            "compiles with no placeholder steps (no sorry, no admit) and "
            "depends on no axioms beyond Lean's core three; eight of its "
            "twenty-nine stated results depend on no axioms at all, including "
            "the refusal itself, which is pure control flow over the "
            "detection verdict. The subject is the fixed index build's "
            "decision logic — how each entry's chain status is assigned by "
            "position, what the build counts as trusted, and what a query "
            "does when the index's own chain is broken — modelled step for "
            "step from the fixed code."
        ),
        "context": (
            "The quarantine report in this register is this law's first "
            "proof. It proved the law in the form the code then had — status "
            "read off each entry's recorded sequence number — and stated the "
            "case that form exposed: an entry past a chain break whose "
            "recorded sequence number was duplicated or regressed could be "
            "marked verified without being checked. The ruling that followed "
            "was to fix the code first and then re-prove. The index now "
            "assigns status by position, and refuses to answer at all when "
            "its own chain is broken; this report is that re-proof. For the "
            "code as it now stands, it supersedes the earlier report's "
            "characterization of the status rule. The earlier report is not "
            "edited by this one: it stands as the accurate record of the law "
            "as proved against the code as it then stood — and its proof is "
            "what found the case this fix closed."
        ),
        "proven": [
            "Nothing at or after the break is marked verified — by position, "
            "unconditionally. When a ledger's chain fails, every entry at the "
            "first failing position and every entry after it is marked "
            "quarantined, whatever its recorded sequence number says. The status "
            "rule reads the entry's position and the verified depth only; the "
            "recorded sequence number is copied into the row as data and never "
            "consulted. This is the quarantine law in its originally stated "
            "form — the form the first proof could not establish against the "
            "code as first built.",
            "The verified rows are exactly the chain-checked prefix. Every entry "
            "up to the verified-through point passes every check the walk "
            "applies — sequence, identity, link, hash recomputation, and the "
            "ordering counters — against the state built from the entries before "
            "it, and is marked verified. The split sits exactly at the first "
            "failure, never earlier and never later; on a full pass the whole "
            "ledger is verified.",
            "The build's trusted-row count is the verified depth. The count is "
            "taken over the built rows' marks, and the marks are verified exactly "
            "at the positions up to the verified-through point — so the number "
            "the build reports as trusted is exactly the number of entries the "
            "chain walk checked, no more and no fewer.",
            "A broken index chain makes the query refuse. Before any query is "
            "answered, the index's own hash chain is checked; on a break, the "
            "query path refuses, by name, and serves no rows at all — in every "
            "query mode, because the check comes first and does not inspect the "
            "query's filters. Detection itself is as the earlier reports proved "
            "it: a break is the first failing row, named at its position.",
            "An intact index chain means the query answers normally. When the "
            "index's own chain verifies, the query returns exactly the rows its "
            "filters admit — no more, no fewer — and a trusted-only query over "
            "the built rows still returns no quarantined row, for every form of "
            "the query's other conditions.",
            "Resolution still never deletes. Every entry of every cleanly loaded "
            "ledger appears as exactly one row in the index. Marking an entry as "
            "superseded or tombstoned changes only that row's currency flag and "
            "records what superseded it; the row remains, the ledger itself is "
            "never modified by the index, and the two marks stay independent: "
            "an entry can be verified and no longer current at once.",
            "The harness's own test cases are theorems, in their fixed-code "
            "forms. The case the first proof found — a ledger broken at its "
            "second entry, a later entry's recorded sequence number regressed "
            "to 1: that entry is now quarantined by its position, the "
            "trusted-row count is exactly one, and a trusted-only query over "
            "that ledger can return only the first entry's row; the same "
            "theorem also evaluates the old rule over the same ledger and gets "
            "'verified', so the difference the fix makes is itself "
            "kernel-checked. One index row altered after the build: every query "
            "is refused. An untouched index: queries answer normally. And the "
            "earlier cases carry over — the rewritten second entry splits its "
            "ledger at one verified row; the tombstoned entry stays present, "
            "marked no longer current, and still verified; and when every "
            "ledger in a build verifies, every row any query returns is "
            "verified.",
        ],
        "not_proven": [
            "This report supersedes the earlier characterization — for the "
            "current code only. The quarantine report in this register "
            "characterized the status rule as it then stood; that rule no "
            "longer exists in the code, so for the code as it now stands that "
            "characterization is superseded by this one. Nothing in the earlier "
            "report is edited or withdrawn: it remains the accurate record of "
            "the law as proved against the code as it then stood.",
            "The query path has a second refusal, and it is not modelled. If "
            "the index file cannot be loaded or parsed at all, the query path "
            "also refuses — with an error, before any chain check — and serves "
            "no rows. That leg exists in the code, but this proof begins at "
            "the loaded rows, as the earlier proofs did; loading and parsing "
            "are outside the model, so the load-error refusal is a fact read "
            "from the code, not a theorem.",
            "SHA-256 itself is not proved. As in the chain report, the hash "
            "function is modelled as an abstract function, and the results "
            "that read 'altered content is detected' — for a ledger entry, "
            "and for a row of the index — rest on a named assumption: that "
            "the altered and original contents do not hash to the same value. "
            "Collision resistance is a standard, believed property of "
            "SHA-256; in this proof it enters only as that named assumption, "
            "discharged by nothing here.",
            "A consistently rewritten index is, to this law, an intact one. "
            "The refusal fires on a broken chain. An index file rewritten in "
            "full — every link and hash recomputed consistently — is not a "
            "break to the check, and no result here claims otherwise; that "
            "is the same boundary the chain report states for ledgers. What "
            "speaks to wholesale rewrites is the anchoring mechanism, a "
            "separate report in this register.",
            "The query path's final recheck is proved vacuous. After a "
            "trusted-only query answers, the code re-checks the returned rows "
            "and would fail the query if any were not verified. That recheck "
            "can never fire on the query's own output: the query's "
            "verified-only condition already admits only verified rows, so "
            "the recheck removes nothing and changes nothing. It is a dead "
            "leg in the code — present, and proved to have no effect.",
            "Quarantine is still re-derived on every build; it is not a "
            "state. The fix changed how status is assigned, not when: each "
            "build re-verifies every ledger and re-derives every status from "
            "the files as they then stand, so a repaired ledger is verified "
            "at the next build simply because it now verifies. And a ledger "
            "that fails to load at all still contributes no rows, exactly as "
            "the earlier report stated.",
            "The refusal is proved as a decision, not as text. What is "
            "proved is that no rows are served when the index's own chain "
            "breaks. The refusal's exact wording and its exit code are the "
            "program's surface — read from the code and exercised by the "
            "harness's own tests, not theorem content.",
            "The proof is about a model of the code, not the running code "
            "itself. The model mirrors the fixed build's decisions and the "
            "query path's decisions step for step, and the correspondence is "
            "documented and reviewed — but it is not itself machine-checked. "
            "A proof of the model is not a proof of the running program. "
            "Reading and writing the files, and anything that changes while "
            "a build or a query runs — concurrency included — sit outside "
            "the proof, as in the earlier reports.",
        ],
    },
    {
        "report_id": "harness-supervisor-fence",
        "subject": "Agent harness — run supervisor fence",
        "date": "2026-11-15",
        "kind": "lean_proof",
        "verdict": "proven",
        "summary": (
            "Our agent harness runs long work under a supervisor. The supervisor judges "
            "each run only from the artifacts the run leaves behind — its completion and "
            "failure markers, its heartbeat, its checkpoint — and when a run stalls it may "
            "resume it from that checkpoint, up to a declared maximum number of attempts: "
            "the fence. Past the fence the run is preserved and reported, never resumed "
            "again. Proved in Lean 4: a run is completed exactly when its own marker says "
            "so, a resume is launched only on a checkpoint that verifies exactly, and the "
            "fence is never crossed."
        ),
        "method": (
            "Lean 4 formal proof (toolchain v4.22.0), checked by the Lean kernel. The proof "
            "compiles with no placeholder steps (no sorry, no admit) and depends on no "
            "axioms beyond Lean's core three; ten of its stated results — including every "
            "planted test case below — depend on no axioms at all. The subject of the proof "
            "is the supervisor's classification and stall-response decision logic, modelled "
            "step for step from the code as built. One honesty note this register keeps: "
            "this proof needed no named assumptions at all. Elsewhere in this register a "
            "collision assumption is named wherever a hash is compared; here the "
            "checkpoint's hash is derived and carried, never compared against anything, "
            "so there is nothing for such an assumption to attach to."
        ),
        "context": (
            "The claim this report examines ran: the run supervisor never resumes beyond "
            "its declared fence. Checked against the code, the sentence is true — and "
            "narrower than the discipline the code actually keeps. The fence is one leg of "
            "a four-leg response to a stall — fence spent, no resume mechanism, checkpoint "
            "declined, exact resume — and it means anything only alongside the "
            "classification soundness and the artifact-only judgment that decide when a "
            "stall is real. One clause of the claim's original sketch, that once the "
            "fence is reached later passes change nothing at all, turned out false of "
            "the code; the law is stated and proved in the code's true forms instead, and "
            "the first item of the boundary list below carries that correction in full. "
            "This is the fourth law of the harness proof round. The supervisor's events "
            "are also mirrored into the trace ledger whose gatekeeper, chain, and "
            "quarantine laws are the earlier reports in this register; this proof's "
            "counts are over the supervisor's own event record, which is written first "
            "and unconditionally, and nothing in it turns on the mirror."
        ),
        "proven": [
            "Completion is sound, in both directions. Over a supervisor pass on an active "
            "run, the run is classified completed exactly when its completion marker is "
            "present, parses as an object, and its status says 'complete'. The completion "
            "check comes first: when the marker says complete, no other artifact is "
            "consulted for the verdict, and nothing else — no failure marker, no "
            "heartbeat state — can complete a run whose marker does not say so.",
            "A present-but-invalid completion marker fails the run — never completes it. "
            "If the marker file cannot be parsed, or parses to something that is not an "
            "object, the run is classified failed at that pass, with exactly the one "
            "failure record the code writes for it and no classification record before "
            "it. A marker that parses but says anything else — or says nothing — "
            "completes nothing and fails nothing by itself; judgment moves on to the "
            "failure marker and to stillness.",
            "The two markers are deliberately treated differently, and the proof keeps "
            "the difference. An unreadable completion marker fails the run, as the item "
            "above states; an unreadable failure marker is simply ignored — it neither "
            "fails nor completes the run, and judgment falls through to stillness, "
            "exactly as if the marker were absent. A readable failure marker that says "
            "'failed' does fail the run.",
            "A resume is exact. A resume is launched only when the run's checkpoint "
            "verifies in the same pass: the checkpoint state file present and parseable, "
            "its step recorded as a whole number, and every required component present "
            "in the code's sense — a missing key, an empty string, or an empty object "
            "counts as missing, while a value of 0, false, or an empty list counts as "
            "present. The launched resume carries the checkpoint's own step and the "
            "SHA-256 of the state file's bytes, computed at verification time in that "
            "same pass.",
            "An incomplete checkpoint is declined, and the run is preserved. When "
            "verification declines, the decline names what is missing, the run is marked "
            "preserved, and no resume is launched — not at that pass, and not at any "
            "later one, even if the checkpoint is afterwards repaired: preserved is a "
            "final state, and the code has no path back from it.",
            "The fence holds as a bound, exactly. Across any sequence of supervisor "
            "passes, the number of resumes launched for a run equals the growth of its "
            "attempt counter — no more, no fewer: the counter is moved in exactly one "
            "place, in the branch that launches the resume, by exactly one, and only "
            "from below the fence on an active run. The total therefore never exceeds "
            "the run's declared maximum, and every launched resume carries an attempt "
            "number at or below that maximum.",
            "At a final state, the supervisor is a fixed point. Once a run's status is "
            "completed, failed, or preserved, it is no longer acted on: every further "
            "pass leaves its registry record exactly as it stands, records no events "
            "for it, and appends nothing. The silence the fence promises holds in "
            "full — at the final state, which is where the code places it.",
            "The harness's own test cases are theorems. A run with a fresh heartbeat is "
            "judged running and its record unchanged; when its completion marker "
            "appears, the next pass completes it. A stalled run with a complete "
            "checkpoint is resumed exactly once, carrying the checkpoint's own step "
            "and hash. A checkpoint missing one named component is declined with that "
            "component named, the run preserved, and no resume launched. At a fence of "
            "two, repeated passes relaunch exactly twice and end with the run "
            "preserved, and a further pass adds nothing at all. A stalled run with no "
            "resume mechanism is escalated and preserved, never completed. And a "
            "readable failure marker fails its run.",
        ],
        "not_proven": [
            "The fence law as first sketched is not what is proved — because as "
            "sketched, it is false of the code. The sketch said that once the fence is "
            "reached, every further pass leaves the run's registry state and event "
            "count unchanged. The registry half holds — a pass that judges a run "
            "still running saves nothing — but a run whose attempts are spent is "
            "still active, and a later pass with a fresh heartbeat still records a "
            "classification event for it: the event record grows while no resume is "
            "possible. What is proved instead is the law in its true forms: the bound "
            "above, preservation at the first stalled pass that finds the fence spent, "
            "and total silence — events and registry alike — only once the run "
            "reaches a final state. This report does not claim the sketched form.",
            "Judging by artifacts alone has two halves, and only one of them is a "
            "theorem. What is proved: the modelled supervisor's every decision is a "
            "function of the declared inputs — the run's registered configuration, "
            "the two markers, the heartbeat's stillness, the checkpoint — and "
            "checkpoint verification reads the state file only through its step, its "
            "hash, and its required components. The other half — that the running "
            "code never consults process state: it records the launched process's "
            "identity at start and never reads it again, and no process inspection "
            "appears anywhere in it — is a fact read from the code and checked by "
            "search, not a theorem, and this report does not present it as one.",
            "The resume pin is derived, never compared. There is no stored pin "
            "anywhere for a resume to match against: the supervisor computes the pin "
            "from the checkpoint file inside the pass, and the resume reads that same "
            "computed value. The proof is of the derivation's exactness — that the "
            "launched step and hash are the file's own step and the hash of its bytes "
            "at that moment — not of agreement with any expectation recorded earlier.",
            "One planted case is named, not claimed. The harness's seventh supervisor "
            "case exercises the supervisor driving the mirrored trace ledger — the "
            "local event record and its mirror landing together. That composition is "
            "the subject of the gatekeeper and chain reports in this register, not of "
            "this one; this proof's counts are over the local record, and nothing in "
            "it turns on the mirror.",
            "A checkpoint file of the wrong shape can end the pass early, and that "
            "path is outside the proof. If the state file parses to something that is "
            "not an object, verification raises an error instead of declining, and "
            "the supervisor pass stops part-way. The model has no such case — in the "
            "model a parsed state file is always object-shaped — so the crash path "
            "is named here, not modelled, as with the crash paths named in the "
            "earlier reports.",
            "A truth value can pass as a step count. In the language the supervisor "
            "is written in, the JSON literal true satisfies the whole-number test, so "
            "a state file whose step is true would have that value carried as its "
            "pinned step. The model's step is a whole number or nothing and cannot "
            "represent the case. It is a margin at the data boundary; no clause of "
            "the law turns on it.",
            "Stillness is taken as a single number. The supervisor judges a run "
            "stalled by how long its heartbeat has been still, and the proof takes "
            "that stillness as given. How it is computed — from the heartbeat file's "
            "modification time, or from the run's start when no heartbeat exists, "
            "each measured against the pass's clock — is not modelled, and neither "
            "is the clock itself. The law governs what the supervisor does with the "
            "stillness it computes, not the computation.",
            "The artifacts' authorship is not covered. The supervisor classifies the "
            "bytes it finds: a completion marker written by something other than the "
            "run, a checkpoint file swapped between passes, a heartbeat touched by "
            "another process. The proof covers the classification of what is found, "
            "not who wrote it; that the artifacts are the run's own is an assumption "
            "about the world the supervisor runs in.",
            "The relaunch itself is outside the proof. The law governs the "
            "supervisor's bookkeeping — the resume event, the counter, the pin it "
            "carries. Whether the launched command actually restarts the run, and "
            "whether the restarted run resumes from the pinned step, is the resumed "
            "program's contract; it is exercised by the harness's own tests against "
            "the real supervisor, not by this model. That a supervisor pass itself "
            "always finishes is likewise not claimed: the model's pass is a total "
            "function, while the running pass can block on reading its files.",
            "The proof is about a model of the code, not the running code itself. "
            "The model mirrors the supervisor's classification and stall-response "
            "logic step for step, and the correspondence is documented and "
            "reviewed — but it is not itself machine-checked. A proof of the model "
            "is not a proof of the running program. Two supervisors running at once "
            "over the same registry and event records — concurrency — sit outside "
            "the proof, as in the earlier reports.",
        ],
    },
    {
        "report_id": "harness-resident-boundary",
        "subject": "Agent harness — resident boundary",
        "date": "2026-11-15",
        "kind": "lean_proof",
        "verdict": "proven",
        "summary": (
            "Our agent harness includes a resident service that is granted exactly one "
            "directory: it walks that directory, builds an index of what it finds, and "
            "answers searches and lookups from the index alone. Proved in Lean 4: a file "
            "is indexed only when its resolved real path lies inside the granted "
            "directory, no examined component of it is credential-shaped, and admitting "
            "it keeps the index within the grant's size cap; no symlink whose target "
            "leaves the grant is ever followed or indexed; a grant that is absent, "
            "malformed, or incomplete admits nothing at all; and every write an "
            "indexing run makes lands in the service's own state directory."
        ),
        "method": (
            "Lean 4 formal proof (toolchain v4.22.0), checked by the Lean kernel. The "
            "proof compiles with no placeholder steps (no sorry, no admit) and depends "
            "on no axioms beyond Lean's core three; of its seventy-three stated "
            "results, thirty-one depend on no axioms at all, and none depends on the "
            "axiom of choice. The subject of the proof is the resident service's "
            "boundary decisions, its indexing walk, and its read surface, modelled step "
            "for step from the code as built — including one branch of the code that "
            "can never fire, transcribed as written. This proof needed no named "
            "assumptions: no hash is compared anywhere in it, so there is nothing for "
            "a collision-style assumption to attach to. One provenance note this "
            "register keeps: the proof's first complete draft failed to compile on "
            "three points — a reserved word used as a name, and two small results the "
            "draft assumed which the core library does not carry — and was repaired "
            "without changing any statement, the missing results proved from what the "
            "core library does provide, before the final clean compile."
        ),
        "context": (
            "The claim this report examines ran: the resident service refuses "
            "everything outside its grant. Checked against the code, the sentence is "
            "true of resolved paths and false of named paths. Every admission decision "
            "turns on where a path resolves to — a file whose real location is outside "
            "the grant is never indexed. But a path named outside the grant whose "
            "target resolves inside it is admitted on its resolved path, and the "
            "boundary list below carries that finding in full: the code contains a "
            "refusal written for exactly that case which can never fire, and the "
            "service's own documentation states the rule the code does not keep. This "
            "is the fifth and last law of the harness proof round; the gatekeeper, "
            "chain, anchored-chain, quarantine, and supervisor-fence reports are the "
            "earlier entries in this register, and the resident service's own run "
            "events are mirrored into the trace ledger those reports cover."
        ),
        "proven": [
            "Admission is exact, in both directions. A candidate is admitted exactly "
            "when its resolved real path lies inside the granted directory, no "
            "examined component of it is credential-shaped, and — where a regular file "
            "is required — it is one. The tests run in the code's order: containment "
            "first, judged on the resolved path; then the credential test, over the "
            "path's components inside the grant together with the named path's final "
            "component when it differs; then the file-kind test. A credential-shaped "
            "path outside the grant is refused as outside: the boundary does not name "
            "what it will not look at.",
            "The credential exclusion is a computation, not an intention. Names are "
            "matched case-insensitively against the exclusion set — credential stores, "
            "environment files, files with credential, secret, or password in the "
            "name, private keys and key containers — and a refusal names the pattern "
            "that caught the file. Planted names resolve exactly as the code resolves "
            "them: an environment file, a credential-store directory in any casing, a "
            "private-key file, and a passwords file are each shapes; an ordinary "
            "document, a note, and a binary are not.",
            "No escaping symlink is followed or indexed. An index entry exists only "
            "at a resolved path inside the grant, so a link whose target lies outside "
            "is never indexed under its own name or any other. A directory whose "
            "resolved path lies outside is never kept for traversal. And a symlink "
            "directory is never traversed at all: refused as an escape when its target "
            "leaves the grant, recorded as not traversed when its target stays inside "
            "— its contents are indexed at their real place, or not at all.",
            "A grant that fails any check is no grant, and no grant admits nothing. A "
            "grant exists exactly when the record is well-formed, a path is present, "
            "the grant is attributed to a named granter, the size cap is a positive "
            "whole number, and the path resolves to a directory that exists — each "
            "defect, an unattributed grant and a misshapen cap among them, defeats the "
            "grant on its own. With no grant loaded, a run admits nothing, records "
            "nothing, and writes nothing: every entry point stops before any admission "
            "decision exists.",
            "The size cap is enforced whole. Admitted files are charged at their full "
            "size, and the running total is exactly the admitted files' total and "
            "never exceeds the cap. The file whose admission would cross the cap is "
            "refused whole — never partially admitted — the walk stops there, nothing "
            "further is admitted or recorded, and the index is marked partial.",
            "Writes are confined to the service's own state directory. Across any "
            "indexing run, the complete set of writes is five files — the index, its "
            "temporary sibling, the run report, the refusals log, and the service's "
            "own event record — each a direct child of the run's state directory, a "
            "placement the code checks before the walk begins. The read surface "
            "refuses writes outright: its write, delete, and update operations exist "
            "only to be refused, by name, every time.",
            "The read surface answers only from the index. A search returns index "
            "entries and nothing else: for any test of matching, its results are part "
            "of the index, never a fresh read of a source file. A lookup returns one "
            "index entry's recorded path and recorded extract; there is no other "
            "source of content on the surface. And because a refused file was never "
            "indexed, its content appears in no answer the surface gives.",
            "The harness's own test cases are theorems. A path outside the grant is "
            "refused by name; an escaping symlink is refused and never indexed; a "
            "credential-shaped file is refused with the pattern that caught it named; "
            "the cap stops the walk and marks the index partial; a search finds a "
            "planted phrase in an admitted file and returns nothing of a refused "
            "file's content; and across a full run in the standard arrangement — the "
            "state directory outside the granted tree — no write lands inside the "
            "grant.",
        ],
        "not_proven": [
            "'No writes inside the grant' is proved only in the standard arrangement, "
            "and is not claimed unconditionally. What holds without conditions is "
            "confinement: every write lands in the run's own state directory. The code "
            "expressly supports placing that state directory inside the granted tree; "
            "in that arrangement the run's writes are inside the grant — inside the "
            "service's own store, a subtree the walk always excludes from indexing. "
            "Only when neither the state directory nor the grant contains the other "
            "does no write land inside the granted tree, and this report claims the "
            "strong form only there.",
            "A lookup's boundary refusal fires only when a grant is passed. The "
            "lookup takes its grant optionally: with one, the boundary check runs "
            "first and a refusal is the whole answer, before the index is consulted; "
            "without one, the lookup is a pure search of the index by the path as "
            "given, and no boundary check runs at all. The unconditional form — every "
            "path outside the grant, or credential-shaped, refused by name before any "
            "lookup — is not the code, and is not claimed.",
            "One of the code's named refusals can never fire. The code carries a "
            "branch that refuses a path named outside the grant whose target resolves "
            "inside it — the refusal it names OUTSIDE-GRANT — with the reason written "
            "beside it: the named path is what was asked for, and it was not granted. "
            "The branch is unreachable: the containment test that guards it already "
            "counts a path as inside whenever its resolved path is inside, so the "
            "branch's condition is always false, and such a path is admitted on its "
            "resolved path. This is proved of the model, and was re-checked against "
            "the running service: the outside-named link into the grant is allowed, "
            "while a plainly outside path is refused and a link named inside that "
            "resolves outside is refused as an escape. The service's own documentation "
            "states the opposite rule — that a path outside that merely resolves "
            "inside is refused, because the named path is what must be granted. No fix "
            "is claimed in this report: whether the code or the documentation changes "
            "is a separate decision, and any fix will be proved in its turn, as the "
            "quarantine fix was. "
            "Correction, 2026-11-15: the Director ruled that the table follows "
            "the code. The README row — and the module docstring's matching "
            "gloss — now state the proved form: the refusal fires only when both "
            "the named path and its resolved path lie outside the grant. The "
            "unreachable branch has been removed from the code. Behaviour was "
            "re-verified unchanged (the resident selftest passes 10 of 10 and the "
            "empirical controls return the same verdicts as before), and the proof "
            "stands unmodified, because the decision it proves did not change.",
            "Path resolution is taken as given. The proof judges the paths the system "
            "reports: a candidate's named path and its resolved real path, a link's "
            "resolved target. What resolution itself returns — how links are "
            "followed, how a path is normalized — is the filesystem's answer, "
            "accepted as an input to every decision. The judgement is also of the tree "
            "at one instant: a path swapped between the boundary check and the read, "
            "or a tree changing while it is walked, is outside the proof.",
            "The boundary judges paths, not files. Two names for one file are two "
            "candidates: a name inside the grant whose other name lies outside is "
            "admitted on its inside path, because its resolved path is inside — no "
            "result here concerns a file's identity. A filesystem mounted inside the "
            "granted tree is inside by path; the boundary never tests where one "
            "filesystem ends and another begins. And containment compares name "
            "components exactly, so on a filesystem that treats differently-cased "
            "names as the same, spellings the proof judges different can name one "
            "directory. The running code shares each of these properties; the proof "
            "states them rather than repairing them.",
            "The exclusion matches names, never content. A credential kept under an "
            "innocent name is admitted, because the boundary judges what a file is "
            "called and where it resolves — by the code's design, which the proof "
            "preserves rather than improves. Nothing here establishes that an admitted "
            "file is harmless: only that its path is inside the grant, its name is "
            "not credential-shaped, and its size fits the cap.",
            "Four of the harness's own test cases are named, not claimed. That the "
            "index's stored hashes and extracts faithfully match the files is not "
            "proved: the model's entries carry no hash, and a stored extract is "
            "trusted, not judged. That a later run reuses exactly the unchanged "
            "entries is not proved: the model is the fresh run — though every "
            "admission check runs before any reuse in the code, so reuse changes no "
            "admission outcome. The mirroring of a run's events into the harness's "
            "trace ledger is the subject of the gatekeeper and chain reports, not "
            "this one. And that the service has no network surface is a fact read "
            "from its code and checked by search, not a theorem: the model has no "
            "notion of a network to state it over.",
            "The proof is about a model of the code, not the running code itself. "
            "The model mirrors the service's boundary, walk, and read surface "
            "decision for decision, in the code's own order — including the branch "
            "that can never fire, transcribed as written — and the correspondence is "
            "documented and reviewed, but it is not itself machine-checked. A proof "
            "of the model is not a proof of the running program. The service's error "
            "exits — a malformed stored index, a write failing part-way — are facts "
            "read from the code, not theorems; the model's surfaces never fail.",
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
