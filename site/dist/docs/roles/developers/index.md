> Canonical: https://axiom-code.com/docs/roles/developers/ · Type: Role pack · Audience: Integrators, agent builders · Role packs: Developers · Version: Docs set 2026-11-14 · Last verified: 2026-11-14 · Source: Live OpenAPI; MCP reference; schema references

# Developers pack

For integrators and agent builders: contracts first, then the operational feeds your integration should consume.

## Contracts

- [REST API](/docs/api/) — the reference; the [live OpenAPI document](https://api.axiom-code.com/openapi.json) is the contract of record.

- [MCP](/docs/mcp/) — hosted (seven tools) and local (two tools) are separate contracts; pick deliberately.

- [Verdicts & errors](/docs/reference/verdicts-and-errors/) — every outcome, its code, and its effect.

- [Keys & limits](/docs/reference/keys-and-limits/) — the key contract and the service limits.

- [Integrate an agent](/docs/guides/integrate-an-agent/) — outcome-to-behaviour mapping for agent callers.

## Feeds to build against

- [status.json](/status.json) ([schema](/docs/reference/status-schema/)) — poll it instead of scraping pages; respect `as_of`.

- [changelog.json](/changelog.json) / [RSS](/changelog.rss.xml) ([schema](/docs/reference/changelog-schema/)) — the append-only record of what changed.

- [Service record](/.well-known/axiomcode.json) and [llms.txt](/llms.txt) — machine-readable orientation for agents.

## Versioning posture

The live OpenAPI document carries the API's version and is the contract of record; this documentation set is versioned as a whole (see the meta block on every page) and its status/pricing facts are generated from the same canonical sources as the service's own status surfaces, under CI drift checks. Breaking contract changes are changelog events, never silent edits.
