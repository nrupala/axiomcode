> Canonical: https://axiom-code.com/docs/start/first-certificate-check/ · Type: Tutorial · Audience: New users, relying parties · Role packs: Guest · Users · Regulators · Version: Docs set 2026-11-14 · Last verified: 2026-11-14 · Source: Live checker behaviour at /check/

# Your first certificate check

A certificate is only worth what a stranger can check. This page walks the check a relying party performs — no account, no trust in this website.

### 1 · Get a certificate JSON

Certificates are issued on paid verifications. If you are evaluating, ask the party who gave you the artefact for their certificate JSON — or read the field-by-field anatomy in the [certificates reference](/docs/reference/certificates/) first.

### 2 · Open the checker

Go to [/check/](/check/) and paste the certificate JSON. Checking runs **in your browser**: the page fetches the CA public keys from the API and verifies the signature locally.

### 3 · Read the three answers

The checker reports the signature (valid or not, under key ID `c731a5036812339d`), the validity window (certificates live 90 days), and the revocation state — checked against the [public revocation list](https://api.axiom-code.com/revoked). All three must be good before the certificate means anything.

### 4 · Match the artefact

The certificate binds an `artifact_hash`. Hash the artefact you were given (SHA-256) and compare: the certificate covers exactly those bytes, and no others. A changed byte is a different artefact with no certificate.

## Next

- [Check & revoke](/docs/guides/check-and-revoke/) — the full lifecycle, including what revocation means and when it happens.

- [Certificate trust model](/docs/explanation/certificate-trust-model/) — what you are trusting, and what you are not asked to.
