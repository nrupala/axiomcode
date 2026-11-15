> Canonical: https://axiom-code.com/docs/explanation/certificate-trust-model/ · Type: Explanation · Audience: Relying parties, regulators · Role packs: Regulators · Users · Version: Docs set 2026-11-14 · Last verified: 2026-11-14 · Source: Certificate Policy & CPS; practice page §§4–6

# Certificate trust model

The model is borrowed from the web's certificate authorities and narrowed: you are asked to trust a key, a public record, and a published practice — each of which you can inspect without us.

## What you rely on

- **The CA key.** Certificates are signed by the production CA key (ID `c731a5036812339d`). The public half is published at the API's `/.well-known/axiomcode-keys.json`; signature checking needs no account and no trust in this website.

- **The revocation list.** Public, current, and the only authority on whether a serial still stands.

- **The append-only record.** Issuance practice, findings, incidents, and graduations are recorded in the [changelog](/changelog/), which does not rewrite itself.

- **The published practice.** Gates, soak, and certificate rules are stated on the [practice page](/practice/) and in the [Certificate Policy](/paperwork/certificate-policy/) — the CA can be caught breaking its own stated rules, in public.

## What you are not asked to trust

- **Our AI.** Models explain; they never judge. No verdict depends on a model's say-so.

- **Our website.** The checker runs in your browser against keys fetched from the API; the offline path (keys + revocation list + the artefact hash) needs this site not at all.

- **An external auditor's word.** None exists: **no external third-party audit of AxiomCode has been performed**, and the assurance case does not pretend otherwise. What exists is a first-party release gate, a public record, and artefacts you can check yourself.

## The organizing risk

A CA has one existential failure: **mis-issuance** — saying "verified" when it isn't. The whole practice (boolean verdicts, NO VERDICT asymmetry, public revocation, 90-day expiry) is organized around making mis-issuance hard to do and impossible to hide.
