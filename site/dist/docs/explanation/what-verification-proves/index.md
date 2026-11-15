> Canonical: https://axiom-code.com/docs/explanation/what-verification-proves/ · Type: Explanation · Audience: All audiences · Role packs: Guest · Users · Regulators · Version: Docs set 2026-11-14 · Last verified: 2026-11-14 · Source: Certificate Policy; How It Works (gate-verified copy)

# What verification proves

A PASSED verdict makes one claim, stated exactly: the submitted artefact compiled under the stated toolchain, and the Lean kernel accepted its proofs.

## Why that claim is strong

- **The kernel is the judge.** Lean's kernel is a small, conservative checker. A proof the kernel accepts is not an opinion, a test sample, or a reviewer's impression — it is a machine-checked derivation.

- **The claim is about exact bytes.** The artefact hash binds the verdict to the precise submission. There is no drift between "what was checked" and "what the certificate describes".

- **The claim names its toolchain.** Verification is relative to the checker; the certificate records which toolchain ran, so the claim can be re-examined when toolchains change.

- **The claim is signed and revocable.** The CA stakes its name on the record — and can publicly withdraw it if the ground shifts (a toolchain defect, a mis-issuance), which is what makes the signature worth more than the JSON.

## Why certificates bind fields, not vibes

Each bound field answers an attack on the claim: the hash answers "different code"; the toolchain answers "checked by what?"; the validity window answers "is this still fresh?"; the serial answers "has it been withdrawn?"; the signature answers "who says so?". Remove a field and the corresponding doubt returns. That is why a certificate is a record, not a badge — and why checking one is a mechanical act any relying party can perform ([first certificate check](/docs/start/first-certificate-check/)).

## The honest boundary

The claim is narrow on purpose. Its complement — everything a PASSED verdict does *not* say — has its own page: [what verification does not prove](/docs/explanation/what-it-does-not-prove/). Read both before relying on either.
