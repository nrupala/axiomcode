> Canonical: https://axiom-code.com/docs/guides/use-the-queue/ · Type: Guide · Audience: Users, developers · Role packs: Users · Developers · Version: Docs set 2026-11-14 · Last verified: 2026-11-14 · Source: Live API behaviour; Ask/verify client behaviour

# Use the queue

Proof checking is slot-bound: when every slot is busy, submissions queue instead of failing. This guide is the queue contract.

## How a queued run looks

- `POST /verify` answers **202** with `{"status": "queued", "job_id": "…", "position": N}`.

- Poll `GET /verify/jobs/{job_id}` with the **same API key** — a job belongs to the key that submitted it. While queued or running, the answer stays 202 with the current position.

- When the run completes, the poll answers **200** with the ordinary result: verdict, artefact hash, usage record, and — on paid verifications — the certificate.

- The browser clients (the home loop, [/verify/](/verify/), [Ask](/ask/)) poll every 3 seconds for you.

## What can go wrong

- **A queued job can fail** — for example the artefact errors in a way only the run itself reveals. The poll then reports the failure as a **NO VERDICT** outcome: the job ended, nothing was decided, nothing is certified.

- **Timeouts are NO VERDICT too** (504 on a synchronous run): the run exceeded its time limit. Timeouts do not consume trial cases and are not charged.

- **Losing the job_id loses the result handle.** Record it at submission time; there is no job listing endpoint.

## Driving it well

- Submit once, poll patiently: re-submitting the same artefact creates a second job, not a faster first one.

- Identical bytes hash identically — the `artifact_hash` is your idempotency key when reconciling results (see [reconcile metering](/docs/guides/reconcile-metering/)).
