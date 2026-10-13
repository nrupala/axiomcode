# Licensing — axiomcode

## Current position retained

Current licence record: **Proprietary licence (root LICENSE)**.

Existing proprietary licence is retained; no Apache interface carve-out is inferred.

The existing licence file remains the controlling licence record for this repository in this sweep. This document adds a common place to record that position and connects it to the standard product terms. It does not relicence prior releases and does not reduce rights granted by the existing licence.

## Standard product terms

`TERMS.md` contains the portfolio’s standard terms for an official packaged or supplied product: licensor **2351485 ALBERTA INC.**, liability capped at the product price paid, excluded indirect and consequential damages, user-environment responsibility, no absolute security guarantee, consumer-law preservation and severability, and Calgary, Alberta as the venue for litigation, mediation, or arbitration.

Those product terms supplement an official product supply only to the extent consistent with the repository licence and applicable law.

## Owner decision recorded for morning review

This repository is listed as a licence exception in the sweep report. The decision still required is whether the existing licence should remain, or whether a future, repository-specific change should adopt the proprietary-core + Apache-interface split in whole or in part.

## Access model — documentation only

Where `axiomcode` is supplied as a runnable product, its supported access modes are documented and governed according to need:

- **Human access:** the product’s user interface or other human-facing surface.
- **Machine access:** documented command-line, automation, or system-integration surfaces.
- **Agent access:** access by an authorized software agent, only where the product implements it.
- **Software access:** documented embedding, plug-in, library, or integration surfaces.
- **API access:** a documented programmatic interface, where provided.

Agent authorization, where implemented, uses a key-value record keyed by agent ID. The value contains only a hashed agent token, permitted scopes, expiry, and an enabled/disabled state. A human administrator enrolls, narrows, disables, or revokes an agent; the agent does not receive the human’s master credential. Agent activity is recorded in a tamper-evident, hash-chained audit log where the product provides one.

This section describes the portfolio access standard. It does not claim that every access mode is implemented in the current release.

