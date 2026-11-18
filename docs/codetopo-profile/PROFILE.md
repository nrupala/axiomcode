# Codetopo Profile — AxiomCode (nrupala/axiomcode)

**What this is.** The agent-facing map of this repository, generated with
Codetopo 0.9.1 (local engine) — topology, trust boundaries, money
surface — with the graph snapshot beside it (`snapshot.json`,
`stats.json`) as the measured evidence. Read the coverage note first:
it bounds everything this profile can claim.

- **Repo:** nrupala/axiomcode (public)
- **Commit profiled:** `edae09008c01161b478ce6c148075bb776b97afa` (main)
- **Engine:** codetopo 0.9.1 · index run 2026-11-18
- **Graph:** 131 files walked · 2,927 nodes · 11,055 edges · audit chain valid
- **Nodes by kind:** function 436 · method 483 · class 95 · variable 254 · module 131 · file 131 · doc 55 · external 1,341 · package 1
- **Edges by kind:** calls 4,190 · reads 3,632 · contains 1,585 · defines 777 · imports 457 · writes 414

## Coverage honesty — PARTIAL, stated plainly

Extracted at symbol level: the **Python** estate (76 `.py` — the API
service, CLI and tooling) and Markdown as Doc nodes. **Not extracted:
the Lean core — 163 `.lean` files (~716 KB), the formally verified
heart of the product, are invisible to this graph** because Codetopo
has no Lean extractor and Lean is not among the 16 languages in the
Director's extractor program (2026-11-18 ruling). HTML (59 files, the
site) is not parsed. Any claim below about `core/` or `lean/` rests on
the directory/docs read, not on graph evidence, and is marked as such.

## Topology

Natural-language → formally verified code (README; domain
axiom-code.com):

- `core/` + `lean/` — the Lean formal core (directory read, not
  graph): specifications, proofs, the verified kernel the product's
  claim rests on.
- `services/api/` — the Python API service (graph-extracted):
  `mcp_server.py` / `mcp_hosted.py` (the MCP surface), `proof_runner.py`
  (runs verification jobs), `jobqueue.py`, `limits.py` (rate/usage
  limits), `ca.py` + `certs.py` (the product's own certificate
  authority for verified-code certificates), `billing.py` +
  `stripe_billing.py` (see Money surface), `snapshot.py`, `shell.py`.
- `cli.py`, `config.py`, `cache.py`, `rate_limit.py` at the root —
  the local CLI and shared plumbing.
- `site/` + `publish/` — the public site and publication assets;
  `gate.yaml` — the repo's own release-gate configuration.

## Trust boundaries

- **The proof is the boundary:** code is trusted only when the Lean
  kernel checks it — `proof_runner.py` verdicts, not model confidence,
  decide what is "verified". The CA (`ca.py`) issues certificates
  bound to those verdicts; certificate trust chains to the CA's key
  custody (keys by name only; no key material in this repo or profile).
- **API boundary:** the hosted MCP/API surface is key-authenticated
  and rate-limited (`limits.py`, `rate_limit.py`); job execution is
  queued (`jobqueue.py`), not run in the request path.
- **Blast radius (graph-visible part):** `services/api/` concentrates
  the Python call edges; the Lean core's internal blast radius is not
  measurable until a Lean extractor exists — named here as an open
  leg, not glossed over.

## Money surface

AxiomCode is a paid product: `services/api/stripe_billing.py` +
`billing.py` wire Stripe billing for the API service (checkout taken
by Stripe; this code maps payment state to access). The product's own
Stripe account/keys are held as service secrets, by name only — none
appear in this profile. No card data touches this code.

## How an agent should approach

1. Read `README.md`, `PLAN.md` (the founding plan), `SECURITY.md`,
   then this profile — and remember the Lean core is *not* in the
   graph: read `core/` and `lean/` source directly.
2. Never describe a proof result you have not seen from the kernel /
   `proof_runner.py` output.
3. Query the graph for the Python service; treat `gate.yaml` as the
   repo's release contract.
4. Regenerate this profile at every release.

## Regeneration

`docs/codetopo-profile/refresh.sh` (in this pack) re-fetches the repo
at a named ref, re-runs the index, and rewrites `snapshot.json`,
`stats.json` and `verify.txt`.

## Standing-condition lines for this change

- Documentation at par: this pack is the documentation change, same PR;
  no behaviour changed.
- Release gate: NOT RUN for this profile PR · Guardian Mesh approval:
  NOT RUN. Merging is not "shipped"; the pack enters the gate queue in
  the Stage-1 evidence pack.
- OpenSSF Best Practices: no project registered for this repo on
  bestpractices.dev (checked 2026-11-18) — a named gap; this additive
  docs change does not degrade any criterion.
