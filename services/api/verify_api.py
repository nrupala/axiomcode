"""AxiomCode verification API (production build).

POST /verify {code} -> {verified, attempts, certificate, usage}
POST /check  {certificate} -> {valid, ...}
GET  /revoked -> {issuer, revoked: [serial...]}
GET  /.well-known/axiomcode-keys.json -> published CA public keys

Certificates are Ed25519-signed attestations (ca.py, format v2)
binding: code hash + verified verdict + toolchain version + validity
window. Anyone holding the cert and the published public key can
confirm *what* was checked and *what* the machine said — without
trusting the server's word for it. All state (certificates,
revocations, meter, audit) lives in the durable store (store.py);
issuance / revocation / verification events land in its hash-chained
audit log.

Temp Lean projects are created under AXIOMCODE_WORK_ROOT (default:
system temp dir) and always removed after the verification finishes.
"""

import hashlib
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, "/home/hatch/workspace/axiomcode/repo")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import ca
from billing import meter
from core.prover import iterative_proof_search, lean_version
from fastapi import FastAPI
from pydantic import BaseModel
from store import Store

TOOLCHAIN = "leanprover/lean4:v4.35.0-rc3"
WORK_ROOT = os.environ.get("AXIOMCODE_WORK_ROOT", tempfile.gettempdir())

CA = ca.CA.load_or_create()
STORE = Store()

app = FastAPI(
    title="AxiomCode Verify",
    description="Verification-as-evidence: every verdict ships a signed certificate "
    "anyone can re-check without trusting us. Don't trust our AI — verify our proof.",
)


class VerifyRequest(BaseModel):
    code: str
    max_attempts: int = 1


class CheckRequest(BaseModel):
    certificate: dict


@app.post("/verify")
def verify(req: VerifyRequest):
    proj = Path(tempfile.mkdtemp(prefix="ax-api-", dir=WORK_ROOT))
    try:
        (proj / "lean-toolchain").write_text(TOOLCHAIN)
        (proj / "lakefile.lean").write_text(
            "import Lake\nopen Lake DSL\npackage v where\nlean_lib V where\n  roots := #[`V]\n"
        )
        src = proj / "V.lean"

        def writer(code: str) -> Path:
            src.write_text(code)
            return src

        t0 = time.time()
        verified, _final_code, attempts, _log = iterative_proof_search(
            writer,
            proj,
            req.code,
            None,
            "none",
            max_attempts=req.max_attempts,
            use_pantograph=False,
        )
        compute_s = time.time() - t0
    finally:
        shutil.rmtree(proj, ignore_errors=True)

    code_sha = hashlib.sha256(req.code.encode()).hexdigest()
    # REST callers are metered under a per-request key; key auth lives on MCP.
    usage = meter(STORE, "rest-anonymous", code_sha, verified, compute_s)
    cert = CA.issue(
        {
            "code_sha256": code_sha,
            "verified": verified,
            "attempts": attempts,
            "toolchain": TOOLCHAIN,
            "lean_version": lean_version(),
            "key_id": "rest-anonymous",
        }
    )
    STORE.record_cert(cert)
    return {
        "verified": verified,
        "attempts": attempts,
        "certificate": cert,
        "usage": usage,
    }


@app.post("/check")
def check(req: CheckRequest):
    result = ca.verify_certificate(req.certificate, ca=CA)
    serial = req.certificate.get("serial") if isinstance(req.certificate, dict) else None
    if result.get("valid") and serial and STORE.is_revoked(serial):
        result = {"valid": False, "reason": "revoked", "payload": req.certificate}
    STORE.append_audit(
        "verification",
        {
            "serial": serial,
            "valid": bool(result.get("valid")),
            "reason": result.get("reason"),
            "via": "rest",
        },
    )
    return result


@app.get("/revoked")
def revoked():
    return {"issuer": ca.ISSUER, "revoked": sorted(STORE.revoked_serials())}


@app.get("/.well-known/axiomcode-keys.json")
def ca_public_keys():
    return CA.public_keys_payload()
