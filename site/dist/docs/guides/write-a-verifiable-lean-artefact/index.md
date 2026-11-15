> Canonical: https://axiom-code.com/docs/guides/write-a-verifiable-lean-artefact/ · Type: Guide · Audience: Users, developers · Role packs: Users · Developers · Version: Docs set 2026-11-14 · Last verified: 2026-11-14 · Source: How It Works (gate-verified copy); engine rejection rules

# Write a verifiable Lean artefact

An artefact is a single, self-contained Lean 4 file whose proofs the kernel can check. This guide covers the shape the engine accepts — and the four rejection rules that keep certificates meaningful.

## The shape

- **One file, self-contained.** Everything the artefact needs must be in the submission; external files and network fetches are not part of the checked bytes.

- **Lean 4.** The toolchain is named on every result and certificate (currently the `lean4-4.9.1` line); a verdict is always relative to the toolchain that produced it.

- **Size limit 256 KB.** Larger submissions are refused with 413 before any checking begins.

- **State the claim as a theorem.** The engine checks proofs of stated propositions. Code without a stated, proved proposition has nothing to certify.

## The rejection rules

The engine rejects — loudly, as a FAILED outcome, never silently — artefacts that cheat the kernel:

- `sorry` and `admit`: an admitted gap is not a proof.

- **Native-code shortcuts** that bypass kernel checking of the claim.

- **Vacuous builds**: statements engineered to be trivially true rather than true of the thing you care about. The kernel checks the statement you wrote — write the statement you mean (see [what verification does not prove](/docs/explanation/what-it-does-not-prove/)).

- **Broken proofs**: anything the kernel does not accept.

## A minimal pattern

```
theorem add_comm_nat (a b : Nat) : a + b = b + a := Nat.add_comm a b
```

Small, stated, proved. Grow from patterns like this: name the property, prove it from the standard library or your own lemmas in the same file, and submit the whole file as one artefact.

## Before you submit

- Compile locally with the same Lean line if you can — a local failure is a free failure.

- Check the statement, not just the proof: the certificate will bind *this* statement.

- Keep the artefact bytes stable after verification: any change is a new artefact (a new hash, a new verification).
