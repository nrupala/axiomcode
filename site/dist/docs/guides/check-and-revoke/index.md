> Canonical: https://axiom-code.com/docs/guides/check-and-revoke/ · Type: Guide · Audience: Users, relying parties · Role packs: Users · Regulators · Version: Docs set 2026-11-14 · Last verified: 2026-11-14 · Source: Certificate Policy & CPS; practice page §5

# Check & revoke

Certificates are short-lived, checkable by anyone, and revocable in public. This guide covers the lifecycle from the relying party's side; the governing document is the [Certificate Policy & CPS](/paperwork/certificate-policy/).

## Checking

- Paste the certificate JSON into [/check/](/check/): the signature is verified in your browser against the published [CA public keys](https://api.axiom-code.com/.well-known/axiomcode-keys.json).

- Confirm the validity window: certificates are valid for **90 days** from issue.

- Confirm the serial is absent from the [public revocation list](https://api.axiom-code.com/revoked) (the checker does this for you).

- Confirm the `artifact_hash` matches the artefact in front of you.

## Renewal is re-verification

There is no extension stamp. When a certificate approaches expiry, submit the artefact again: a fresh verification runs and a fresh certificate is issued on the new result, with a new validity window.

## Revocation

- A certificate is revoked when its verdict can no longer be stood behind — for example, a toolchain defect that invalidates the check it records.

- Revocation is **public and permanent**: the serial goes on the revocation list, an incident note is published in the [changelog](/changelog/), and affected artefacts are re-verified at our expense.

- There is no silent un-verification: a revoked certificate remains visible as revoked, with its history intact.
