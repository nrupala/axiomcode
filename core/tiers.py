"""
AxiomCode Verification Tiers
=============================
Precise, testable definitions of what each tier runs, what evidence it
produces, and what the certificate asserts. (Human-readable companion:
~/workspace/certification-authority/TIERS.md.)

- "scan" (Free): static checks only. Produces a report. NEVER mints a
  certificate. Output is labeled DRAFT / NOT VERIFIED.
- "verified": full generate → prove → verify pipeline with the axiom audit,
  minted as a schema-v2 Ed25519-signed certificate with a validity window.
- "certified": everything in "verified", plus the full proof trace
  (tactics + build log) preserved with the certificate, a longer validity
  window, and public-registry publication with re-verification on expiry.

The certificate's `tier` field records which tier was sold. A verifier MUST
refuse to mint a tier it did not actually run: `run_free_scan` below cannot
produce a certificate by construction (it never calls sign()).
"""

from __future__ import annotations

import hashlib
import time
from pathlib import Path

from core.prover import has_sorry

TIER_SCAN = "scan"
TIER_VERIFIED = "verified"
TIER_CERTIFIED = "certified"

ALL_TIERS = (TIER_SCAN, TIER_VERIFIED, TIER_CERTIFIED)

#: What each tier runs — the testable contract. `runs` names pipeline stages,
#: `evidence` names artifacts produced, `certificate` says whether a signed
#: certificate is minted and what it asserts.
TIER_DEFINITIONS: dict[str, dict] = {
    TIER_SCAN: {
        "name": "Free scan",
        "price_model": "free (lead generation)",
        "runs": [
            "sorry/admit scan over submitted Lean sources",
            "top-level declaration inventory (theorems/lemmas)",
            "declared-axiom surface scan (lines starting with 'axiom ')",
        ],
        "evidence": ["scan report (dict): per-file findings, counts, honest limitations"],
        "certificate": None,  # NEVER minted at this tier — by construction.
        "asserts": (
            "Nothing about correctness. The report lists static findings and "
            "states explicitly that no proof was machine-checked."
        ),
    },
    TIER_VERIFIED: {
        "name": "Verified",
        "price_model": "per-verification",
        "runs": [
            "full generate → prove → verify pipeline",
            "lake build on the proof target (explicit target; 'Nothing to build' is failure)",
            "sorry/admit gate",
            "axiom audit: #print axioms per theorem; fail closed outside Lean's standard axioms",
        ],
        "evidence": [
            "schema-v2 Ed25519-signed certificate",
            "validity window (issued_at / expires_at)",
            "artifact hash binding (spec/proof/binary)",
        ],
        "certificate": "minted; asserts the named artifact version machine-checked "
        "under the recorded Lean toolchain, with the recorded axiom set",
        "asserts": (
            "The artifact's proofs were machine-checked by the recorded Lean "
            "toolchain at issuance time, depending only on Lean's standard axioms. "
            "The signature attests to provenance and integrity — not to proofhood "
            "beyond what verification_status records."
        ),
    },
    TIER_CERTIFIED: {
        "name": "Certified",
        "price_model": "per-verification + re-verification on expiry (TLS-renewal model)",
        "runs": [
            "everything in the Verified tier",
            "full proof trace preservation (tactics + build log stored with the certificate)",
            "publication to the public certificate registry",
        ],
        "evidence": [
            "schema-v2 Ed25519-signed certificate with proof trace",
            "longer validity window",
            "public registry entry (transparency log)",
            "QR payload → live-status verification page",
        ],
        "certificate": "minted; asserts the Verified-tier claims plus traceability: "
        "any third party can re-check the exact proof from the preserved trace",
        "asserts": (
            "The Verified-tier claims, plus: the complete proof trace is preserved "
            "and published, so the verification is independently re-checkable without "
            "trusting the issuer."
        ),
    },
}


def validate_tier(tier: str) -> str:
    """Normalize and validate a tier name. Raises ValueError on unknown tiers."""
    t = (tier or "").strip().lower()
    if t not in ALL_TIERS:
        raise ValueError(f"Unknown tier {tier!r}; expected one of {ALL_TIERS}")
    return t


def run_free_scan(target: str | Path) -> dict:
    """Run the Free-scan tier over Lean sources.

    Static checks only — no proving, no signing, no certificate. The report
    is labeled DRAFT / NOT VERIFIED by construction: this function has no
    code path that mints a certificate.

    Returns a report dict with per-file findings.
    """
    target = Path(target)
    files: list[Path] = []
    if target.is_file():
        files = [target]
    elif target.is_dir():
        files = sorted(target.rglob("*.lean"))
    else:
        raise FileNotFoundError(f"Scan target not found: {target}")

    findings: list[dict] = []
    for f in files:
        try:
            code = f.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError) as e:
            findings.append({"file": str(f), "error": f"unreadable: {e}"})
            continue
        declared_axioms = [line.strip() for line in code.splitlines() if line.strip().startswith("axiom ")]
        findings.append(
            {
                "file": str(f),
                "sha256": hashlib.sha256(code.encode("utf-8")).hexdigest(),
                "has_sorry_or_admit": has_sorry(code),
                "declared_axioms": declared_axioms,
            }
        )

    return {
        "tier": TIER_SCAN,
        "label": "DRAFT — NOT VERIFIED. Static findings only; no proof was machine-checked.",
        "scanned_at": time.time(),
        "files_scanned": len(findings),
        "files_with_sorry": sum(1 for x in findings if x.get("has_sorry_or_admit")),
        "files_with_declared_axioms": sum(1 for x in findings if x.get("declared_axioms")),
        "findings": findings,
        "certificate_minted": False,  # invariant: the scan tier never mints
    }
