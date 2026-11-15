> Canonical: https://axiom-code.com/docs/roles/maintainers/ · Type: Role pack · Audience: Maintainers, engaged auditors · Role packs: Maintainers · Version: Docs set 2026-11-14 · Last verified: 2026-11-14 · Source: Publication boundary per blueprint D3.1/D3.2

# Maintainers pack

This pack is published as a boundary, not a document set — deliberately.

### Publication level: evidence on request

The Maintainers pack carries release and deployment internals — operational IP whose publication would weaken the service it describes. Its **structure and contents list are public** (below); its contents are provided on request to maintainers and to auditors under engagement. No credentials, keys, internal addresses, or host topology appear in any pack, including this one.

## What the pack contains

- Release standard operating procedures — branch, gate, merge, deploy, read-back.

- Per-release gate artefacts: gate configuration, coverage ledgers, judgment differentials, verdicts.

- Deploy and rollback runbooks for the API, the hosted MCP leg, and the website.

- CA operations runbook: issuance and revocation procedure, key custody and rollover procedure.

- Incident playbooks and the findings register (F-AX-*) with closure evidence.

- Monitoring and soak-observation procedures for release candidates.

## What is already public

Much of the pack's evidence base is public by design: the [gate declaration](https://github.com/nrupala/axiomcode/blob/main/gate.yaml), the [threat model](https://github.com/nrupala/axiomcode/blob/main/docs/THREAT-MODEL.md), the [coverage ledger](https://github.com/nrupala/axiomcode/blob/main/docs/COVERAGE-LEDGER.json), the [practice page](/practice/), and the [changelog](/changelog/). The boundary covers procedure and internals, not the existence or the outcomes of the process.

## Requesting the pack

Write to [hello@axiom-code.com](mailto:hello@axiom-code.com?subject=Maintainers%20pack%20request) with who you are and the engagement the evidence supports. Requests are answered by a person; there is no automated fulfilment, and that is intentional.
