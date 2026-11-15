> Canonical: https://axiom-code.com/docs/roles/admins/ · Type: Role pack · Audience: Account administrators · Role packs: Admins · Version: Docs set 2026-11-14 · Last verified: 2026-11-14 · Source: Live service behaviour; billing state from the status source

# Admins pack

For the people who administer accounts and keys for their teams.

### There is no admin console

Stated plainly: **AxiomCode has no admin console, no self-serve signup, and no account dashboard today.** Administration is a manual, email-mediated process while billing is paused. Anything that looks like an AxiomCode admin login is not ours — report it via the [Security page](/paperwork/security/).

## How administration works today

- **Getting keys:** email [hello@axiom-code.com](mailto:hello@axiom-code.com?subject=API%20key%20request); keys are issued per request. One key per integration is the recommended pattern.

- **Key storage on our side:** hash only. We cannot display or recover a key; loss means replacement.

- **Balances and packs:** credit packs are priced but **not yet on sale**; there are no balances to administer yet. Trial usage (10 cases per key) is visible in each verification's usage record and via the MCP `usage_report` tool.

- **Team changes:** key replacement, additional keys, and account questions are handled through [contact](/contact/) — expect a human reply, not a ticket black hole.

## What you can verify without us

- Every certificate your keys produced: [checker](/check/) + [revocation list](https://api.axiom-code.com/revoked).

- Your metering: usage records join on `artifact_hash` ([reconcile metering](/docs/guides/reconcile-metering/)).

- The service's state: [status](/status/) and the [changelog](/changelog/).

## When a console exists

It will appear on the [status page](/status/) as its own surface before it is announced anywhere else — the status page is where new surfaces exist first, by rule.
