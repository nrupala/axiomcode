> Canonical: https://axiom-code.com/docs/reference/keys-and-limits/ · Type: Reference · Audience: Users, developers, admins · Role packs: Users · Developers · Admins · Version: Docs set 2026-11-14 · Last verified: 2026-11-14 · Source: Live service behaviour; status source

# Keys & limits

One key unlocks every door — REST, hosted MCP, the web verifier, the checker, and Ask. This page is the key contract and the limits that apply to it.

## Keys

- **Issuance:** by email while billing is paused — write to [hello@axiom-code.com](mailto:hello@axiom-code.com?subject=API%20key%20request). Keys begin `axk_`.

- **Storage:** the service stores only a **hash** of your key. We cannot show you your key again; a lost key is replaced, not recovered.

- **Use:** send it as the `X-Api-Key` header (REST) or your MCP client's credential. The browser pages keep it in page memory only.

- **Scope:** a key owns its jobs and its usage records; job polls require the submitting key.

## Limits

| Limit | Value | On breach |
| --- | --- | --- | --- |
| Artefact size | 256 KB | 413 — NO VERDICT, nothing consumed |
| Trial | First 10 verification cases per key | 402 once exhausted with no balance |
| Proof slots | Bounded concurrency | 202 queueing (not a refusal) |
| Rate | Per-key request pacing | 429 — NO VERDICT, retry slower |
| Run time | Per-run engine time limit | 504 — NO VERDICT, no charge, no trial case consumed |

Limits are service-protection facts, published here and reflected in the [outcome taxonomy](/docs/reference/verdicts-and-errors/). Current availability of every surface is on the [status page](/status/).
