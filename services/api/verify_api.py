"""AxiomCode verification API prototype.

POST /verify {code} -> {verified, attempts, certificate}
POST /check  {certificate} -> {valid, payload}

The certificate is an HMAC-signed attestation binding:
  code hash + verified verdict + toolchain version + timestamp.
Anyone holding the cert can confirm *what* was checked and *what* the
machine said — without trusting the server's word for it.
"""

import hashlib
import os
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, "/home/hatch/workspace/axiomcode/repo")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import certs
from billing import meter
from fastapi import FastAPI
from pydantic import BaseModel

from core.prover import iterative_proof_search, lean_version

SECRET = os.environ.get("AXIOMCODE_CERT_SECRET", "dev-secret-change-me").encode()
TOOLCHAIN = "leanprover/lean4:v4.35.0-rc3"
METER_LOG = os.environ.get("AXIOMCODE_METER_LOG", "/home/hatch/workspace/axiomcode/api-prototype/meter.jsonl")

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


class UsageRequest(BaseModel):
    key_id: str


@app.post("/verify")
def verify(req: VerifyRequest):
    proj = Path(tempfile.mkdtemp(prefix="ax-api-"))
    (proj / "lean-toolchain").write_text(TOOLCHAIN)
    (proj / "lakefile.lean").write_text(
        "import Lake\nopen Lake DSL\npackage v where\nlean_lib V where\n  roots := #[`V]\n"
    )
    src = proj / "V.lean"

    def writer(code: str) -> Path:
        src.write_text(code)
        return src

    t0 = time.time()
    verified, final_code, attempts, log = iterative_proof_search(
        writer,
        proj,
        req.code,
        None,
        "none",
        max_attempts=req.max_attempts,
        use_pantograph=False,
    )
    compute_s = time.time() - t0
    code_sha = hashlib.sha256(req.code.encode()).hexdigest()
    # REST callers are metered under a per-request key; key auth lives on MCP.
    usage = meter(METER_LOG, "rest-anonymous", code_sha, verified, compute_s)
    cert = certs.issue(
        {
            "code_sha256": code_sha,
            "verified": verified,
            "attempts": attempts,
            "toolchain": TOOLCHAIN,
            "lean_version": lean_version(),
            "key_id": "rest-anonymous",
        }
    )
    return {
        "verified": verified,
        "attempts": attempts,
        "certificate": cert,
        "usage": usage,
    }


@app.post("/check")
def check(req: CheckRequest):
    return certs.check(req.certificate)


@app.get("/revoked")
def revoked():
    return {"issuer": certs.ISSUER, "revoked": sorted(certs.revoked_serials())}
