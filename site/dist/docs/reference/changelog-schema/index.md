> Canonical: https://axiom-code.com/docs/reference/changelog-schema/ · Type: Reference · Audience: Developers, ops, regulators · Role packs: Developers · Ops · Regulators · Version: Docs set 2026-11-14 · Last verified: 2026-11-14 · Source: site/changelog_data.py (canonical source)

# Changelog schema

The [changelog](/changelog/) is the append-only service record. It is published as HTML, [JSON](/changelog.json), and [RSS](/changelog.rss.xml) from one source.

## Entry fields

| Field | Meaning |
| --- | --- | --- |
| id | Stable, unique entry ID — the anchor other pages link to (/changelog/#). |
| date | The date the recorded change took effect. |
| title / body | What changed, in plain language. |
| category | One of: Added · Changed · Fixed · Finding · Incident · Status · Documentation · Removed. |
| surfaces | The surfaces the entry concerns. |
| effect | What the change means for relying parties. |
| evidence | Labelled links to the artefacts that prove the entry. |
| refs | Finding IDs, gate records, and other cross-references. |
| disposition | Where the matter stands — live, closed, carried, or pending a named decision. |

## The append-only rule

- Entries are never silently edited. A correction is a new entry (or a dated correction note appended to the original); the original remains readable.

- Scheduled events (for example graduations) appear only when they happen — plans live on the [status page](/status/), history lives here.

- Findings and incidents are first-class categories, not footnotes: the record includes what went wrong, not only what shipped.
