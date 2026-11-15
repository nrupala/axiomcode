> Canonical: https://axiom-code.com/docs/explanation/what-it-does-not-prove/ · Type: Explanation · Audience: All audiences · Role packs: Guest · Users · Regulators · Version: Docs set 2026-11-14 · Last verified: 2026-11-14 · Source: How It Works (gate-verified copy); Certificate Policy

# What verification does not prove

A verdict certifies the artefact that was submitted. These are the things it does not certify — stated as plainly as the claim itself.

- **Intent.** The kernel checks the statement you wrote, not the statement you meant. A proof of the wrong theorem passes exactly as cleanly as a proof of the right one. Specification review remains a human duty.

- **The rest of the system.** Code that was not submitted is not covered: callers, configuration, infrastructure, and the humans operating them.

- **Deployment.** A certificate binds submitted bytes. Whether the deployed system runs those bytes is a separate fact, established by your own pipeline discipline (hash comparison is the bridge).

- **Specification quality.** A vacuous or trivial statement can be proved; the engine rejects engineered vacuity where it can detect it, but the meaningfulness of a specification is ultimately the author's responsibility.

- **The future.** Certificates expire in 90 days because evidence ages: toolchains are patched, defects are found, contexts change. Freshness is a feature, not a subscription trick.

## Why we publish the bounds

A certification authority that oversells its claim destroys the only asset it has. The bounds are therefore printed at the point of claim (the home page's scope line), inside the Certificate Policy, and here — so that a relying party's trust is calibrated by us before it is tested by events.
