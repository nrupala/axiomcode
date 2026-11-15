> Canonical: https://axiom-code.com/docs/start/first-mcp-call/ · Type: Tutorial · Audience: Agent builders, developers · Role packs: Developers · Version: Docs set 2026-11-14 · Last verified: 2026-11-14 · Source: Hosted MCP service record (slice 1, live 2026-11-11)

# Your first MCP call

The hosted MCP endpoint gives agent clients the same engine, the same queue, and the same trial as the REST API — as tools.

### 1 · Point your client at the endpoint

The endpoint is `https://api.axiom-code.com/mcp/` — the trailing slash is canonical. Authenticate with the same API key you use for REST (keys are issued by email: [hello@axiom-code.com](mailto:hello@axiom-code.com?subject=API%20key%20request)).

### 2 · List the tools

After the standard MCP handshake, `tools/list` returns seven tools: `verify`, `job_status`, `check_certificate`, `revoked`, `health`, `usage_report`, `pricing`. The full contract is in the [MCP reference](/docs/mcp/).

### 3 · Call verify

Call `verify` with a Lean 4 artefact. You receive the same response shape as REST: verdict, artefact hash, usage record — and, when the proof slots are busy, a job to poll with `job_status`. Trial semantics are identical: the first 10 cases per key return verdicts and usage, never a certificate.

### 4 · Prefer REST when there is no agent

MCP is a door, not a different service. If your caller is a script or a backend rather than an agent client, the [REST API](/docs/api/) is the simpler contract — same key, same verdicts.

## Next

- [Integrate an agent](/docs/guides/integrate-an-agent/) — key handling, queue discipline, and error mapping for agent callers.

- [MCP reference](/docs/mcp/) — all seven tools, plus the local MCP server.
