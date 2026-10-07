"""
AxiomCode Public Certificate Registry
======================================
Transparency-log model for issued certificates (per SPEC).

- Every issued certificate is published here, byte-identical to what was
  signed. The stored file is NEVER modified after publication — doing so
  would break its signature, and the registry refuses to serve tampered
  entries.
- Revocation is a separate, public, timestamped statement in
  `revocations.json`. Revoked certificates REMAIN VISIBLE with status
  "revoked" — revocation is public, never silent.
- Expired certificates remain visible with status "expired".
- The default view is active certificates only; the full log (including
  expired/revoked) is always available — like Certificate Transparency.
- `export_json()` produces a machine-readable registry snapshot that AI
  agents can fetch and verify without parsing images or PDFs: every entry
  carries the Ed25519 signature and public key needed to check it.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

from core.security import ProofCertificate

REGISTRY_FORMAT_VERSION = 1


class CertificateRegistry:
    """File-backed public registry of issued certificates."""

    def __init__(self, registry_dir: str | Path = "registry"):
        self.registry_dir = Path(registry_dir)
        self.certs_dir = self.registry_dir / "certs"
        self.certs_dir.mkdir(parents=True, exist_ok=True)
        self._revocations_file = self.registry_dir / "revocations.json"
        self._index_file = self.registry_dir / "index.json"

    # ── Revocation list ──────────────────────────────────────────────────

    def _load_revocations(self) -> dict:
        if not self._revocations_file.exists():
            return {}
        try:
            data = json.loads(self._revocations_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return {}
        return data if isinstance(data, dict) else {}

    def _save_revocations(self, revocations: dict) -> None:
        self._revocations_file.write_text(json.dumps(revocations, indent=2, sort_keys=True))

    def is_revoked(self, serial: str) -> bool:
        """Authoritative revocation check (registry list, not the cert file)."""
        return serial in self._load_revocations()

    def revocation_record(self, serial: str) -> dict | None:
        return self._load_revocations().get(serial)

    def revoke(self, serial: str, reason: str, user: str = "system") -> dict:
        """Publicly revoke a certificate. The certificate stays published and
        visible — only its status changes to "revoked". Never silent."""
        if not self._cert_path(serial).exists():
            raise KeyError(f"No such certificate in registry: {serial}")
        if not reason or not reason.strip():
            raise ValueError("Revocation requires a non-empty reason")
        revocations = self._load_revocations()
        if serial in revocations:
            raise ValueError(f"Certificate {serial} is already revoked")
        record = {
            "serial": serial,
            "reason": reason.strip(),
            "revoked_at": time.time(),
            "revoked_by": user,
        }
        revocations[serial] = record
        self._save_revocations(revocations)
        self._rebuild_index()
        return record

    # ── Publication ──────────────────────────────────────────────────────

    def _cert_path(self, serial: str) -> Path:
        safe = "".join(c for c in serial if c.isalnum() or c in "-_")
        if not safe or safe != serial:
            raise ValueError(f"Invalid serial number: {serial!r}")
        return self.certs_dir / f"{safe}.json"

    def publish(self, cert: ProofCertificate) -> str:
        """Publish a certificate to the public registry.

        Fail-closed: the certificate's Ed25519 signature must verify, it must
        carry a serial number, and the serial must not already be published.
        The stored file is byte-identical to the signed certificate.
        """
        if not cert.serial:
            raise ValueError("Cannot publish: certificate has no serial number")
        if not cert.signature:
            raise ValueError("Cannot publish: certificate is not signed")
        if not cert.verify():
            raise ValueError("Cannot publish: certificate signature invalid (tampered or forged)")
        path = self._cert_path(cert.serial)
        if path.exists():
            raise ValueError(f"Serial {cert.serial} is already published")
        path.write_text(cert.to_json())
        self._rebuild_index()
        return cert.serial

    def get(self, serial: str) -> ProofCertificate | None:
        path = self._cert_path(serial)
        if not path.exists():
            return None
        return ProofCertificate.load(path)

    # ── Status & views ───────────────────────────────────────────────────

    def status(self, serial: str, now: float | None = None) -> str:
        """Lifecycle status: active | expired | revoked | unknown.

        Revocation (registry list) is authoritative and overrides the
        certificate's own fields.
        """
        cert = self.get(serial)
        if cert is None:
            return "unknown"
        if self.is_revoked(serial):
            return "revoked"
        return cert.validity_status(now)

    def list_certificates(self, status_filter: str = "active", now: float | None = None) -> list[dict]:
        """Summary view. Default: active certificates only (the public
        storefront). status_filter="all" returns everything, including
        expired and revoked — the transparency log."""
        if status_filter not in ("active", "all"):
            raise ValueError("status_filter must be 'active' or 'all'")
        out = []
        for path in sorted(self.certs_dir.glob("*.json")):
            try:
                cert = ProofCertificate.load(path)
            except (ValueError, FileNotFoundError):
                continue
            st = self.status(cert.serial, now)
            if status_filter == "active" and st != "active":
                continue
            out.append(
                {
                    "serial": cert.serial,
                    "status": st,
                    "product_name": cert.product_name or cert.algorithm_name,
                    "artifact_version": cert.artifact_version,
                    "tier": cert.tier,
                    "owner": cert.owner,
                    "issued_at": cert.issued_at,
                    "expires_at": cert.expires_at,
                }
            )
        return out

    def _rebuild_index(self) -> None:
        index = {entry["serial"]: entry for entry in self.list_certificates(status_filter="all")}
        self._index_file.write_text(json.dumps(index, indent=2, sort_keys=True))

    # ── Machine-readable export (agent-verifiable) ───────────────────────

    def export_json(self, include_non_active: bool = True, now: float | None = None) -> str:
        """Export the registry as signed-JSON certificates in one document.

        Agents verify without parsing images: for each certificate the export
        carries the Ed25519 `signature` and `verify_key` needed to check it,
        plus the live `status`. This is the canonical machine-readable form
        of the SPEC's "agent-verifiable artifact identity".
        """
        certs = []
        for path in sorted(self.certs_dir.glob("*.json")):
            try:
                cert = ProofCertificate.load(path)
            except (ValueError, FileNotFoundError):
                continue
            st = self.status(cert.serial, now)
            if st != "active" and not include_non_active:
                continue
            certs.append(
                {
                    "serial": cert.serial,
                    "status": st,
                    "product_name": cert.product_name or cert.algorithm_name,
                    "artifact_version": cert.artifact_version,
                    "tier": cert.tier,
                    "owner": cert.owner,
                    "repo_or_website": cert.repo_or_website,
                    "verification_status": cert.verification_status,
                    "issued_at": cert.issued_at,
                    "expires_at": cert.expires_at,
                    "artifact_hash": cert.proof_hash,
                    "spec_hash": cert.spec_hash,
                    "signature": cert.signature,
                    "verify_key": cert.verify_key,
                    "key_id": cert.key_id,
                    "verify_url": cert.qr_payload,
                    "issuer": {
                        "name": cert.issuer_name,
                        "website": cert.issuer_website,
                        "contact": cert.issuer_contact,
                    },
                }
            )
        return json.dumps(
            {
                "registry": "AxiomCode Certificate Registry",
                "format_version": REGISTRY_FORMAT_VERSION,
                "exported_at": time.time(),
                "certificate_count": len(certs),
                "certificates": certs,
            },
            indent=2,
            sort_keys=True,
        )

    def verify_registry(self) -> tuple[bool, list[str]]:
        """Verify every published certificate's signature still checks out.

        Detects tampering with the registry store itself. Returns
        (ok, issues).
        """
        issues: list[str] = []
        for path in sorted(self.certs_dir.glob("*.json")):
            try:
                cert = ProofCertificate.load(path)
            except (ValueError, FileNotFoundError) as e:
                issues.append(f"{path.name}: unreadable ({e})")
                continue
            if not cert.signature:
                issues.append(f"{path.name} (serial {cert.serial}): not signed")
            elif not cert.verify():
                issues.append(f"{path.name} (serial {cert.serial}): SIGNATURE INVALID — registry tampered")
        return (len(issues) == 0), issues
