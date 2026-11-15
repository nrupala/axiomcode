> Canonical: https://axiom-code.com/docs/explanation/queue-and-metering-model/ · Type: Explanation · Audience: Users, developers · Role packs: Users · Developers · Version: Docs set 2026-11-14 · Last verified: 2026-11-14 · Source: Live service behaviour; pricing model

# Queue & metering model

Two design choices explain most of the service's behaviour: proof checking runs in bounded slots, and billing counts engine seconds — never queue time, never refusals.

## Why a queue

A Lean kernel check is real compute with a hard resource profile. Admitting unbounded concurrency would make every run slower and some runs unreliable; instead, the service runs a bounded number of proof slots and queues the rest (202 + position + polling). Queueing is backpressure with a handle: you always know where your job stands, and the job belongs to your key.

## Why engine seconds

- **Fairness:** you pay for the compute your artefact consumed, not for other people's load ahead of you in the queue.

- **Predictability:** the same artefact costs the same on a quiet day and a busy one (per-attempt records make the sum auditable — [reconcile metering](/docs/guides/reconcile-metering/)).

- **Alignment:** our incentive is to make the engine faster, not to keep you waiting.

## Why NO VERDICT is free

Timeouts, refusals, and failed queued jobs produce no verdict and no certificate — charging for them would bill you for our limits. The asymmetry is deliberate: money moves only when evidence exists. It is also why the trial can be generous: ten real cases, metered honestly, costing us compute but buying you certainty about the engine before any pack is sold.
