> Canonical: https://axiom-code.com/docs/guides/reconcile-metering/ · Type: Guide · Audience: Users, developers, admins · Role packs: Users · Developers · Admins · Version: Docs set 2026-11-14 · Last verified: 2026-11-14 · Source: Pricing page; usage record shape from the live API

# Reconcile metering

Every verification returns a usage record. This guide explains how the numbers are formed so your books and ours agree to the credit.

## The model

- Metering is **engine compute time**: 0.9 credits per second, 1 credit = $0.01. Wall-clock queue time is not metered.

- A verification may take more than one **attempt** inside the engine; the usage record lists attempts with their elapsed seconds and credits charged. The charge is the sum of attempts.

- The trial uses the same metering — trial cases show real usage records with real numbers; they simply are not billed.

## What does not charge

- **Timeouts (504)**: NO VERDICT, no charge, no trial case consumed.

- **Refusals** (401, 413, 429) and **402**: no run happened; no charge.

- **Failed queued jobs**: NO VERDICT outcomes are not charged as verifications.

## Reconciling

- Join on `artifact_hash`: your submission log, the usage record, and the certificate (paid) all carry it.

- Credits are charged against the pack balance of the key that submitted; the MCP `usage_report` tool returns the same records for agent-side reconciliation.

- Disputes: report through [contact](/contact/) with the artefact hash and the job or serial involved — the append-only service record and the usage log settle the question.

Billing is currently **paused** (packs not yet on sale); metering runs and records regardless, so the numbers you see on the trial are the numbers that will bill.
