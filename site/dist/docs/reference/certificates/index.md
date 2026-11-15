> Canonical: https://axiom-code.com/docs/reference/certificates/ · Type: Reference · Audience: Users, developers, relying parties · Role packs: Users · Developers · Regulators · Version: Docs set 2026-11-14 · Last verified: 2026-11-14 · Source: Certificate Policy & CPS; live /check/ behaviour

# Certificates

A certificate is a signed JSON record. This page is its anatomy; the governing rules are the [Certificate Policy & CPS](/paperwork/certificate-policy/).

## Fields

| Field | Meaning |
| --- | --- | --- |
| artifact_hash | SHA-256 of the exact bytes that were checked. Binds the certificate to one artefact and no other. |
| verified | The boolean verdict: true = PASSED, false = FAILED. Paid verifications receive a certificate either way. |
| toolchain | The exact toolchain that ran the check. A verdict is always relative to its toolchain. |
| issuer | The issuing CA (AxiomCode CA). |
| serial | The certificate's unique serial — the handle used by the revocation list. |
| issued / expires | The validity window: 90 days from issue. |
| signature | The CA's Ed25519 signature over the record, verifiable against the published CA keys (production key ID c731a5036812339d). |

## Lifecycle rules

- **Issuance:** on completed paid verifications only. Trial runs never receive certificates; NO VERDICT outcomes never receive certificates.

- **Checking:** by anyone, at [/check/](/check/) (in-browser) or via `POST /check` — signature, window, and revocation state.

- **Renewal:** re-verification. Submit again; a fresh certificate is issued on the new result.

- **Revocation:** public and permanent, by serial, on the [revocation list](https://api.axiom-code.com/revoked), with a changelog incident note. See [check & revoke](/docs/guides/check-and-revoke/).
