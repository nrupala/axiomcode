> Canonical: https://axiom-code.com/docs/mcp/ · Type: Reference · Audience: Developers, agent builders · Role packs: Developers · Version: Docs set 2026-11-14 · Last verified: 2026-11-14 · Source: Hosted MCP service record (slice 1); repository MCP server

# MCP — hosted & local

Two MCP contracts exist, and they are not the same surface: the hosted endpoint (seven tools) and the local server in the repository (two tools). Both reach the same engine.

## Hosted MCP

Endpoint: `https://api.axiom-code.com/mcp/` — the trailing slash is canonical. Authentication: the same API key as REST. Semantics: the same queue and the same trial (first 10 cases per key: verdicts and usage, no certificates).

| Tool | What it does |
| --- | --- | --- |
| verify | Submit a Lean 4 artefact — the MCP form of POST /verify. Returns the verdict, artefact hash, and usage record, or a queued job. |
| job_status | Poll a queued job — the MCP form of GET /verify/jobs/{id}. |
| check_certificate | Check a certificate — the MCP form of POST /check. |
| revoked | The public revocation list. |
| health | Service health. |
| usage_report | Usage records for the calling key — the reconciliation view (see reconcile metering). |
| pricing | The current pricing and billing state, as published on the pricing page. |

Lifecycle: the hosted endpoint is **live and in soak** with the REST API — see the [status page](/status/) for the current record.

## Local MCP

An MCP server also ships in the [AxiomCode repository](https://github.com/nrupala/axiomcode) for local use over stdio. It exposes two tools — `verify` and `check_certificate` — and calls the hosted API with your key. It is a client-side convenience with its own, smaller contract; it is not a local verification engine, and it issues nothing locally.

## Which one do you want?

- Agent platform that can call a remote endpoint: **hosted** (all seven tools).

- Desktop agent client that speaks stdio MCP: **local** (verify + check, zero hosting).

- No agent at all: the [REST API](/docs/api/) is the same service with the simplest contract.
