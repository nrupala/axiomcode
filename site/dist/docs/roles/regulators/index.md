> Canonical: https://axiom-code.com/docs/roles/regulators/ · Type: Role pack · Audience: Regulators, auditors, relying-party risk functions · Role packs: Regulators · Version: Docs set 2026-11-14 · Last verified: 2026-11-14 · Source: Certificate Policy & CPS; practice page evidence index

# Regulators pack

For regulators, auditors, and relying-party risk functions: the governing documents first, then the index from each control to its public evidence.

## Governing documents

- [Certificate Policy & CPS](/paperwork/certificate-policy/) — issuance, validity (90 days), revocation, and CA control rules. This is the lead document for the CA's practice.

- [Terms](/paperwork/terms/) · [Privacy](/paperwork/privacy/) · [Security & disclosure](/paperwork/security/) · [Refunds](/paperwork/refunds/)

- Operator: **2351485 ALBERTA INC.** (Alberta, Canada) — see [About](/about/).

## Control → evidence index

| Control | Public evidence |
| --- | --- | --- |
| Release gating | Gate declaration · threat model · coverage ledger · practice §2 |
| Release-candidate soak | Status (lifecycle per surface) · practice §3 |
| Certificate issuance & lifecycle | Certificate Policy · certificate anatomy |
| CA key custody & rollover | Practice §6 — key ID c731a5036812339d; public keys at the API well-known endpoint |
| Revocation | Public revocation list · changelog incident entries |
| Findings & incidents | Changelog (Finding / Incident categories) · practice §7 |
| Error reporting | GitHub Issues, user-initiated only — practice §8 |

## Assurance limits — stated plainly

**No external third-party audit of AxiomCode has been performed.** Assurance is first-party (an internal release gate, independent of the build lanes) plus the public, independently checkable artefacts indexed above. Internal release/deploy procedure is published as an evidence-on-request boundary — see the [Maintainers pack](/docs/roles/maintainers/). Any representation beyond this paragraph should be treated as unauthorised.

## Contact for regulatory matters

[Contact](/contact/) — route "Regulatory / audit" in the subject line. Security disclosures never use the public form: [Security page](/paperwork/security/).
