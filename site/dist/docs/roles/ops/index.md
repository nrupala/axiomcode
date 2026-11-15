> Canonical: https://axiom-code.com/docs/roles/ops/ · Type: Role pack · Audience: Operators, SRE counterparts · Role packs: Ops · Version: Docs set 2026-11-14 · Last verified: 2026-11-14 · Source: Status source; practice page §7

# Ops pack

For operators — ours and our customers' — the public operational picture: what to watch, what an incident looks like from outside, and where to escalate.

## Surfaces & health evidence

- All surfaces, availability, and lifecycle: [/status/](/status/) or [status.json](/status.json) (schema: [status schema](/docs/reference/status-schema/)).

- API health: `GET https://api.axiom-code.com/health` — public, no key.

- CA state: [public keys](https://api.axiom-code.com/.well-known/axiomcode-keys.json) · [revocation list](https://api.axiom-code.com/revoked) — both public.

## The incident rule

Per [practice §7](/practice/): every escaped defect and incident receives a finding ID (F-AX-*), a public changelog entry under the Finding or Incident category, a fix, a regression guard, and closure evidence. The status page shows current state; the changelog preserves the sequence — history is never rewritten to look quieter than it was.

## Queue behaviour (what your dashboards will see)

- Bounded proof slots; saturation presents as **202 queueing with positions**, not errors.

- Run timeouts present as 504 NO VERDICT outcomes; rate refusals as 429. Both are named in the [outcome taxonomy](/docs/reference/verdicts-and-errors/).

- Ask explanations are degraded-first: explanation lag under load is a known, recorded residual — facts are unaffected.

## Escalation

- Service problems: [GitHub Issues](https://github.com/nrupala/axiomcode/issues) (product errors) or [contact](/contact/).

- Security: the disclosure route on the [Security page](/paperwork/security/) — never the public issue tracker.

- Support targets and service levels, where they apply, are stated in the [Service Levels](/paperwork/sla/) document — this pack adds no targets of its own.
