> Canonical: https://axiom-code.com/docs/start/first-verification/ · Type: Tutorial · Audience: New users, evaluators · Role packs: Guest · Users · Version: Docs set 2026-11-14 · Last verified: 2026-11-14 · Source: Live service behaviour; the same loop as /verify/

# Your first verification

By the end of this page you will have submitted a real artefact to the real service and read a real verdict. About five minutes.

### 1 · Get an API key

Keys are issued by email while billing is paused. Write to [hello@axiom-code.com](mailto:hello@axiom-code.com?subject=API%20key%20request) and you will receive a key (it starts `axk_`). There is no self-serve signup yet, and no card is needed: the first 10 verification cases on your key are the free trial.

### 2 · Open the verifier

Go to [/verify/](/verify/) — or use the loop on the [home page](/#try), which is the same call. Paste your key into the API key field. The key is kept in page memory only, and is sent only to `api.axiom-code.com`.

### 3 · Run the starter artefact

The artefact box is prefilled with a small true theorem:

```
theorem add_comm_nat (a b : Nat) : a + b = b + a := Nat.add_comm a b
```

Press **Verify artefact**. The service hashes the exact bytes, compiles them with the Lean toolchain, and the kernel checks the proof.

### 4 · Read the verdict

You get one of two verdicts — PASSED or FAILED — plus the artefact hash and a usage record (engine seconds, credits charged). If every proof slot is busy you get a queue position instead; the page polls for you. A run that ends before a verdict (timeout, refusal, failed queued job) is a **NO VERDICT** error outcome — never a verdict, and timeouts do not consume trial cases.

### 5 · Understand the trial

On the trial you receive the verdict and the usage record — **never a certificate**. The certificate is the product: our signature staked on the verdict. It is issued on paid verifications; credit packs are priced on the [pricing page](/pricing/) and are not yet on sale.

## Next

- [Write a verifiable Lean artefact](/docs/guides/write-a-verifiable-lean-artefact/) — what the engine accepts and rejects, and why.

- [Your first certificate check](/docs/start/first-certificate-check/) — verify a certificate the way a relying party does.

- [Verdicts & errors](/docs/reference/verdicts-and-errors/) — every outcome, named.
