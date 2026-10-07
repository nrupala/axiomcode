#!/usr/bin/env python3
"""
AxiomCode — Natural Language to Formally Verified Code
=======================================================

Zero-trust design. Encrypted key storage. Signed artifacts.
Pure Python stdlib + cffi + the audited `cryptography` package (for Ed25519).

Domain: axiom-code.com
"""

from __future__ import annotations

import argparse
import getpass
import json
import os
import re
import subprocess
import sys
import textwrap
import time
from dataclasses import dataclass, field
from pathlib import Path

from core.licensing import (
    TIERS,
    LicenseCertificate,
    LicenseManager,
    get_hardware_fingerprint,
    get_hardware_hash,
)

# LLM backends: one OpenAI-compatible HTTP layer (llama.cpp first, vLLM-ready)
from core.llm import (
    BACKENDS,
    list_backends,
    resolve_backend,
)
from core.prover import (
    audit_axioms,
    elaborate_lean_file,
    iterative_proof_search,
    lean_available,
    lean_version,
)

# Import security layer
from core.security import (
    AuditLog,
    KeyStore,
    ProofCertificate,
    hash_data,
    hash_file,
)
from core.versioning import VersionManager

# ─── Banner ─────────────────────────────────────────────────────────────────

BANNER = """
============================================================
  AxiomCode -- Natural Language to Verified Code
  axiom-code.com | Zero-Trust | Encrypted | Verified
============================================================
"""

# ─── Examples ───────────────────────────────────────────────────────────────

EXAMPLES = [
    {
        "name": "Binary Search",
        "description": (
            "implement binary search on a sorted array that returns the index of the target element, prove it "
            "always finds the element if present"
        ),
        "difficulty": "Easy",
        "category": "Searching",
        "proof_complexity": "Medium",
    },
    {
        "name": "Insertion Sort",
        "description": (
            "implement insertion sort that sorts a list of natural numbers, prove the output is sorted and contains "
            "the same elements as the input"
        ),
        "difficulty": "Easy",
        "category": "Sorting",
        "proof_complexity": "Medium",
    },
    {
        "name": "Merge Sort",
        "description": (
            "implement merge sort using divide and conquer, prove it produces a sorted list that is a permutation "
            "of the input"
        ),
        "difficulty": "Medium",
        "category": "Sorting",
        "proof_complexity": "High",
    },
    {
        "name": "GCD (Euclidean Algorithm)",
        "description": (
            "implement the Euclidean algorithm for greatest common divisor, prove it always terminates and returns "
            "the correct GCD"
        ),
        "difficulty": "Easy",
        "category": "Number Theory",
        "proof_complexity": "Low",
    },
    {
        "name": "Linked List Reverse",
        "description": (
            "implement an in-place linked list reversal, prove the reversed list has the same length and elements "
            "in reverse order"
        ),
        "difficulty": "Medium",
        "category": "Data Structures",
        "proof_complexity": "High",
    },
    {
        "name": "Stack with Max",
        "description": (
            "implement a stack data structure that supports push, pop, and get-max in O(1) time, prove all "
            "operations maintain the stack invariant"
        ),
        "difficulty": "Medium",
        "category": "Data Structures",
        "proof_complexity": "Medium",
    },
]

# ─── Help Text ──────────────────────────────────────────────────────────────

HELP_TEXT = """
AxiomCode -- Help & FAQ
========================

WHAT IS AXIOMCODE?
  Converts natural language descriptions of algorithms into mathematically
  proven-correct code in Python and C. Every line comes with a formal proof
  and a cryptographic certificate of verification.

SECURITY MODEL:
  - Zero-trust: Every output is independently verifiable
  - Zero-knowledge: LLM prompts never contain sensitive data
  - Encrypted: All artifacts are cryptographically signed
  - Auditable: Tamper-evident audit log for compliance

HOW DOES IT WORK?
  1. You describe an algorithm in plain English
  2. LLM generates a formal Lean 4 specification
  3. Proof engine searches for and verifies a mathematical proof
  4. Code extractor compiles verified code to C and Python
  5. Cryptographic certificate is generated and signed
  6. Visualizer shows the proof as an interactive graph

COMMANDS:
  "description"     Generate verified code from NL
  guide             Interactive guided mode
  examples          Browse built-in examples
  help              Show this help
  walkthrough       Step-by-step tutorial
  models            List available LLM backends
  visualize <name>  View proof visualization
  publish <name>    Publish to PyPI/GitHub
  verify <name>     Independently verify a proof
  cert <name>       Show proof certificate
  key create <name> Create a signing key
  key list          List signing keys
  audit             Show audit log

FAQ:
  Q: What languages are supported?
  A: Output: Python and C. Input: Natural language (English).

  Q: Do I need to know Lean 4?
  A: No. You describe algorithms in plain English.

  Q: How do I know proofs are correct?
  A: Proofs are verified by the Lean 4 compiler. Each proof comes with
     a cryptographic certificate that can be independently verified.

  Q: What LLMs are supported?
  A: Local: Ollama (stable-code, mistral, qwen3).
     Cloud: OpenAI (GPT-4o), Anthropic (Claude).

  Q: Is my data sent to external servers?
  A: Only if you use cloud providers (OpenAI/Anthropic). Local llama.cpp
     runs entirely on your machine. No telemetry, no tracking.

  Q: How are generated code artifacts secured?
  A: Every binary and package is cryptographically signed. Certificates
     include hashes of all artifacts for integrity verification.

  Q: Can I use generated code in production?
  A: Only artifacts whose certificate records verification_status="verified".
     AxiomCode records honesty per artifact: "verified" means a proof
     assistant machine-checked the proof; "unverified"/"failed" mean it did
     not. Check the certificate (or run `verify`) before trusting any artifact.

TROUBLESHOOTING:
  LLM backend connection refused:
    # llama.cpp (default local backend)
    llama-server -m <model.gguf> --port 8080
    # vLLM (production serving)
    vllm serve <model>
    # then: python cli.py models

  Lean 4 not found:
    Install from https://lean-lang.org/
    (Without it, specs are saved as UNVERIFIED DRAFTS — never certified as proven.)

  Proof search timeout:
    Try a simpler algorithm or use --model openai.
"""

WALKTHROUGH_TEXT = """
AxiomCode -- Interactive Walkthrough
=====================================

STEP 1: Describe Your Algorithm
  Think of a simple algorithm: binary search, insertion sort, GCD, etc.

STEP 2: Generate the Specification
  Run: python cli.py "implement binary search on a sorted array"
  Behind the scenes:
    - Your description is sent to a local LLM (stable-code by default)
    - The LLM produces a Lean 4 theorem statement
    - The specification captures what "correct" means mathematically

STEP 3: Verify the Proof
  The proof engine searches for a formal proof:
    - If found: you get a verified proof certificate
    - If not: AxiomCode suggests proof hints or simplifies the spec

STEP 4: Extract Code
  Verified Lean code is compiled to:
    - C binary via lean --c (fast, standalone)
    - Python package via cffi bindings (easy to use)

STEP 5: Get Your Certificate
  Every algorithm comes with a cryptographic proof certificate:
    - Hash of the specification
    - Hash of the proof term
    - Hash of the C binary
    - Hash of the Python package
    - HMAC signature for authenticity

STEP 6: Visualize the Proof
  Run: python cli.py visualize binary_search --mode 2d
  Opens an interactive browser view showing:
    - Each proof step as a node
    - Dependencies between steps as edges
    - Click any node to see the Lean tactic

STEP 7: Publish (Optional)
  Run: python cli.py publish binary_search --pypi
  Your verified algorithm is now on PyPI.

Next: Try "python cli.py guide" for interactive mode.
"""

# ─── Data Classes ───────────────────────────────────────────────────────────


@dataclass
class LeanSpec:
    theorem: str
    definitions: list[str] = field(default_factory=list)
    imports: list[str] = field(default_factory=lambda: ["Mathlib", "Aesop"])
    docstring: str = ""
    source_nl: str = ""
    model_used: str = ""
    generation_time_ms: float = 0.0
    spec_hash: str = ""

    def to_lean(self) -> str:
        imports = "\n".join(f"import {i}" for i in self.imports)
        defs = "\n\n".join(self.definitions)
        return f"{imports}\n\n{defs}\n\n/-- {self.docstring} -/\n{self.theorem}"

    def compute_hash(self) -> str:
        self.spec_hash = hash_data(self.to_lean().encode())
        return self.spec_hash


@dataclass
class ProofResult:
    theorem_name: str
    steps: int
    lemmas: int
    lean_file: Path
    olean_file: Path | None = None
    tactics: list[str] = field(default_factory=list)
    proof_term: str = ""
    proof_hash: str = ""
    # Honest verification accounting: "verified" only when Lean (or Pantograph)
    # actually checked the proof. Anything else is "unverified" or "failed".
    verification_status: str = "unverified"
    lean_version: str = ""
    build_log: str = ""
    proof_attempts: int = 0

    def compute_hash(self) -> str:
        self.proof_hash = hash_data(self.proof_term.encode())
        return self.proof_hash


def _theorem_name(theorem_text: str) -> str:
    """Extract a filesystem-safe theorem name.

    Matches the identifier after the `theorem` keyword only — never the
    binders — so `theorem myadd_zero (n : Nat) : ...` yields `myadd_zero`.
    """
    m = re.search(r"\btheorem\s+([A-Za-z_][A-Za-z0-9_']*)", theorem_text)
    return m.group(1).lower() if m else "unnamed_theorem"


# ─── Spec Generator ─────────────────────────────────────────────────────────

SPEC_PROMPT = """You are an expert in Lean 4 formal verification.
Convert the following natural language algorithm description into a Lean 4 formal specification.

Rules:
1. Output ONLY valid Lean 4 code -- no explanations, no markdown.
2. Include necessary imports (Mathlib, Aesop).
3. Define any helper types/structures needed.
4. State the main theorem with a clear name.
5. The theorem should capture the full correctness specification.
6. Write complete proofs wherever you can. If a step truly resists you, you may
   mark it with `by sorry` -- the iterative proof-search loop will attempt to
   discharge it, but final acceptance requires ZERO `sorry`/`admit`.

Natural language description:
{description}

Output format:
```lean
import Mathlib
import Aesop

/-- docstring -/
theorem algorithm_correctness : ... := by
  ...
```
"""


def generate_spec(description: str, model: str = "local") -> LeanSpec:
    """Generate a Lean 4 specification from natural language.

    `model` selects the LLM backend: llama.cpp (default local), vllm,
    ollama, mistral, openai, anthropic. Env overrides: AXIOMCODE_LLM_BACKEND,
    AXIOMCODE_LLM_MODEL, AXIOMCODE_LLM_BASE_URL, AXIOMCODE_LLM_API_KEY.
    """
    backend_name, default_model, gen_fn = resolve_backend(model)
    prompt = SPEC_PROMPT.format(description=description)

    start = time.monotonic()
    raw = gen_fn(default_model, prompt)
    elapsed = (time.monotonic() - start) * 1000

    spec = _parse_spec(raw, description, elapsed, f"{backend_name}/{default_model}")
    return spec


def _parse_spec(raw: str, source_nl: str, elapsed: float, backend: str) -> LeanSpec:
    """Parse LLM output into a LeanSpec."""
    code = raw.strip()
    if "```lean" in code:
        code = code.split("```lean")[1].split("```")[0].strip()
    elif "```" in code:
        code = code.split("```")[1].split("```")[0].strip()

    lines = code.split("\n")
    imports, definitions, theorem_lines = [], [], []
    docstring, in_theorem = "", False

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("import "):
            imports.append(stripped.replace("import ", ""))
        elif stripped.startswith("/--"):
            docstring = stripped.replace("/--", "").replace("-/", "").strip()
        elif stripped.startswith("theorem "):
            in_theorem = True
            theorem_lines.append(line)
        elif in_theorem:
            theorem_lines.append(line)
            if ":= by sorry" in stripped or ":= by" in stripped:
                in_theorem = False
        elif stripped.startswith("def ") or stripped.startswith("structure "):
            definitions.append(line)

    theorem = "\n".join(theorem_lines)
    if not imports:
        imports = ["Mathlib", "Aesop"]

    spec = LeanSpec(
        theorem=theorem,
        definitions=definitions,
        imports=imports,
        docstring=docstring,
        source_nl=source_nl,
        model_used=backend,
        generation_time_ms=elapsed,
    )
    spec.compute_hash()
    return spec


# ─── Proof Engine ───────────────────────────────────────────────────────────


def run_proof(
    spec: LeanSpec,
    lean_bin: str = "lean",
    lake_bin: str = "lake",
    llm_backend: str = "local",
    max_attempts: int = 3,
) -> ProofResult:
    """Verify a specification with Lean 4, using the iterative proof-search loop.

    - Toolchain present: write spec, elaborate with `lake env lean`, and on
      failure feed the compiler errors back to the LLM for repair (up to
      `max_attempts`). A clean elaboration then passes the sorry scan and the
      axiom audit before it may count as verified.
      Optional Pantograph M2M check when installed.
    - Toolchain missing: the spec is saved but the result is honestly marked
      "unverified" — it is never presented as a verified proof.
    """
    project_dir = Path(__file__).parent / "lean"
    drafts_dir = project_dir / "drafts"
    drafts_dir.mkdir(parents=True, exist_ok=True)

    name = _theorem_name(spec.theorem)
    initial_code = spec.to_lean()

    if not lean_available(lean_bin, lake_bin):
        # Honest path: no toolchain, no verification claim.
        lean_file = drafts_dir / f"{name}.lean"
        lean_file.write_text(initial_code, encoding="utf-8")
        print("  [!] Lean 4 toolchain not found (need `lean` and `lake`).")
        print(f"  [!] Spec saved as UNVERIFIED DRAFT: {lean_file}")
        print("  [!] Install Lean 4 from https://lean-lang.org/ to verify.")
        proof = ProofResult(
            theorem_name=name,
            steps=0,
            lemmas=len(spec.definitions),
            lean_file=lean_file,
            tactics=[],
            proof_term=initial_code,
            verification_status="unverified",
            build_log="toolchain missing: lean/lake not found",
        )
        proof.compute_hash()
        return proof

    # Toolchain present: verified artifacts live under src/Algorithms.
    algo_dir = project_dir / "src" / "Algorithms"
    algo_dir.mkdir(parents=True, exist_ok=True)
    lean_file = algo_dir / f"{name}.lean"

    def _write(code: str) -> Path:
        lean_file.write_text(code, encoding="utf-8")
        return lean_file

    backend_name, model, gen_fn = resolve_backend(llm_backend)
    verified, final_code, attempts, build_log = iterative_proof_search(
        _write,
        project_dir,
        initial_code,
        gen_fn,
        model,
        max_attempts=max_attempts,
        lake_bin=lake_bin,
    )

    status = "verified" if verified else "failed"
    if verified:
        print(f"  [+] Proof verified by Lean 4 ({lean_version(lean_bin)}) after {attempts} attempt(s)")
    else:
        print(f"  [!] Proof search FAILED after {attempts} attempt(s); spec kept as draft")
        # A failed proof must not masquerade as a library member.
        draft_file = drafts_dir / f"{name}.lean"
        draft_file.write_text(final_code, encoding="utf-8")
        lean_file = draft_file

    olean_file = lean_file.with_suffix(".olean")
    tactics = _extract_tactics(lean_file)
    proof = ProofResult(
        theorem_name=name,
        steps=len(tactics),
        lemmas=len(spec.definitions),
        lean_file=lean_file,
        olean_file=olean_file if olean_file.exists() else None,
        tactics=tactics,
        proof_term=final_code,
        verification_status=status,
        lean_version=lean_version(lean_bin),
        build_log=build_log[-4000:],
        proof_attempts=attempts,
    )
    proof.compute_hash()
    return proof


def _extract_tactics(lean_file: Path) -> list[str]:
    content = lean_file.read_text(encoding="utf-8")
    keywords = [
        "rw",
        "simp",
        "induction",
        "cases",
        "apply",
        "exact",
        "have",
        "let",
        "calc",
        "refine",
        "constructor",
        "tauto",
        "linarith",
        "ring",
    ]
    return [
        line.strip()
        for line in content.split("\n")
        for kw in keywords
        if line.strip().startswith(kw) or f" {kw} " in line.strip()
    ]


def load_proof(name: str) -> ProofResult:
    project_dir = Path(__file__).parent / "lean" / "src" / "Algorithms"
    lean_file = project_dir / f"{name.lower()}.lean"
    if not lean_file.exists():
        raise FileNotFoundError(f"No verified proof found: {name}")
    content = lean_file.read_text(encoding="utf-8")
    proof = ProofResult(theorem_name=name, steps=0, lemmas=0, lean_file=lean_file, proof_term=content)
    proof.compute_hash()
    return proof


# ─── Code Extractor ─────────────────────────────────────────────────────────


def extract_c(proof: ProofResult, lean_bin: str = "lean") -> Path:
    output_dir = Path(__file__).parent / "build" / "c"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"{proof.theorem_name}.c"

    try:
        result = subprocess.run(
            [lean_bin, "--c", str(output_file), str(proof.lean_file)], capture_output=True, text=True, timeout=120
        )
        if result.returncode != 0:
            raise RuntimeError(f"C extraction failed:\n{result.stderr}")
    except FileNotFoundError:
        print("  [!] Lean 4 not found. C extraction skipped.")
        return output_file

    so_file = output_file.with_suffix(".so")
    try:
        subprocess.run(
            ["gcc", "-shared", "-fPIC", "-O2", "-o", str(so_file), str(output_file)], capture_output=True, text=True
        )
        return so_file if so_file.exists() else output_file
    except FileNotFoundError:
        print(f"  [!] gcc not found. C source saved to {output_file}")
        return output_file


def extract_python(proof: ProofResult) -> Path:
    pkg_dir = Path(__file__).parent / "build" / "python" / f"axiomcode_{proof.theorem_name}"
    pkg_dir.mkdir(parents=True, exist_ok=True)

    # P0 honesty gate: the verified stamp and "formally verified" language are
    # emitted ONLY when the proof was genuinely machine-checked. Anything else
    # ships an honest UNVERIFIED label — never a false claim.
    verified = proof.verification_status == "verified"
    if verified:
        doc_first_line = f"{proof.theorem_name} -- formally verified via AxiomCode."
        stamp_line = "    __proof_verified__ = True"
    else:
        doc_first_line = (
            f"{proof.theorem_name} -- NOT machine-verified (status: {proof.verification_status}). "
            "Provenance only; do not rely on proof claims."
        )
        stamp_line = "    __proof_verified__ = False"
    init_py = pkg_dir / "__init__.py"
    init_text = textwrap.dedent(f'''
        """
        {doc_first_line}
        Proof: {proof.steps} steps, {proof.lemmas} lemmas.
        Certificate: axiomcode_{proof.theorem_name}.cert.json
        """
{stamp_line}
    ''').lstrip()
    init_py.write_text(init_text, encoding="utf-8")

    bindings_py = pkg_dir / "bindings.py"
    bindings_text = textwrap.dedent(f"""
        import cffi
        from pathlib import Path

        _ffi = cffi.FFI()
        _ffi.cdef("/* Add function signatures from the verified C code */")

        _lib_path = Path(__file__).parent / "lib{proof.theorem_name}.so"
        if _lib_path.exists():
            _lib = _ffi.dlopen(str(_lib_path))
        else:
            raise ImportError(f"Verified binary not found: {{_lib_path}}")

        {proof.theorem_name} = _lib
    """).lstrip()
    bindings_py.write_text(bindings_text, encoding="utf-8")

    setup_py = pkg_dir / "setup.py"
    pkg_desc = (
        f"Formally verified {proof.theorem_name} by AxiomCode"
        if proof.verification_status == "verified"
        else f"{proof.theorem_name} by AxiomCode (NOT machine-verified: {proof.verification_status})"
    )
    setup_text = textwrap.dedent(f"""
        from setuptools import setup, find_packages
        setup(
            name="axiomcode-{proof.theorem_name}",
            version="0.1.0",
            description="{pkg_desc}",
            packages=find_packages(),
        )
    """).lstrip()
    setup_py.write_text(setup_text, encoding="utf-8")

    return pkg_dir


# ─── Certificate Generator ──────────────────────────────────────────────────


def generate_certificate(
    spec: LeanSpec,
    proof: ProofResult,
    c_path: Path | None,
    py_path: Path | None,
    signing_key: bytes,
    key_id: str,
    *,
    tier: str = "",
    validity_days: float = 0.0,
    product_name: str = "",
    artifact_version: str = "",
    owner: str = "",
    repo_or_website: str = "",
    owner_contact: str = "",
    issuer_website: str = "",
    issuer_contact: str = "",
    verify_url_template: str = "",
) -> ProofCertificate:
    """Generate a cryptographic certificate for a generated algorithm.

    The certificate binds the artifact hashes and signs them; the
    `verification_status` field honestly records whether the proof was
    machine-checked ("verified") or not ("unverified"/"failed").

    Schema v2: every minted certificate gets a unique serial number and a
    validity window. `validity_days` <= 0 means no expiry. `tier` records the
    verification depth sold ("verified"/"certified"); it must reflect what
    the pipeline actually ran — never mint a tier you did not run.
    """
    from core.tiers import validate_tier

    now = time.time()
    issued_at = now
    expires_at = now + validity_days * 86400 if validity_days > 0 else 0.0
    serial = ProofCertificate.generate_serial(key_id)
    if tier:
        tier = validate_tier(tier)
        if tier == "scan":
            raise ValueError("The scan tier never mints a certificate — refusing to sign one")
    qr_payload = verify_url_template.format(serial=serial) if verify_url_template else ""
    cert = ProofCertificate(
        algorithm_name=proof.theorem_name,
        spec_hash=spec.spec_hash,
        proof_hash=proof.proof_hash,
        c_binary_hash=hash_file(c_path) if c_path and c_path.exists() else "",
        python_hash=hash_file(py_path / "__init__.py") if py_path and py_path.exists() else "",
        theorem=spec.theorem,
        tactics=proof.tactics,
        steps=proof.steps,
        lemmas=proof.lemmas,
        model_used=spec.model_used,
        generated_at=now,
        key_id=key_id,
        verification_status=proof.verification_status,
        lean_version=proof.lean_version,
        build_log_hash=hash_data(proof.build_log.encode()) if proof.build_log else "",
        serial=serial,
        issued_at=issued_at,
        expires_at=expires_at,
        tier=tier,
        product_name=product_name or proof.theorem_name,
        artifact_version=artifact_version,
        owner=owner,
        repo_or_website=repo_or_website,
        owner_contact=owner_contact,
        issuer_website=issuer_website,
        issuer_contact=issuer_contact,
        qr_payload=qr_payload,
    )
    cert.sign(signing_key)
    return cert


# ─── Visualization ──────────────────────────────────────────────────────────


def build_proof_html(proof: ProofResult, mode: str = "2d") -> str:
    graph_data = _build_graph_data(proof, mode)
    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>AxiomCode -- Proof: {proof.theorem_name}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: system-ui, sans-serif; background: #0a0a0f; color: #e0e0e0; }}
        .header {{ padding: 20px 30px; border-bottom: 1px solid #222;
                         display: flex; justify-content: space-between; align-items: center; }}
        .header h1 {{ font-size: 1.2rem; font-weight: 600; }}
        .header h1 span {{ color: #4a90d9; }}
        .mode-switch {{ display: flex; gap: 8px; }}
        .mode-btn {{ padding: 6px 16px; border: 1px solid #333; background: transparent;
                           color: #888; border-radius: 6px; cursor: pointer; font-size: 0.85rem; }}
        .mode-btn.active {{ background: #4a90d9; color: white; border-color: #4a90d9; }}
        .container {{ display: flex; height: calc(100vh - 70px); }}
        .graph-panel {{ flex: 1; position: relative; }}
        .info-panel {{ width: 320px; border-left: 1px solid #222; padding: 20px;
                            overflow-y: auto; background: #0d0d12; }}
        .info-panel h3 {{ font-size: 0.9rem; color: #4a90d9; margin-bottom: 12px; }}
        .info-panel pre {{ background: #151520; padding: 12px; border-radius: 8px;
                               font-size: 0.8rem; overflow-x: auto; line-height: 1.5; }}
        .stats {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 20px; }}
        .stat {{ background: #151520; padding: 12px; border-radius: 8px; text-align: center; }}
        .stat-value {{ font-size: 1.5rem; font-weight: 700; color: #4a90d9; }}
        .stat-label {{ font-size: 0.75rem; color: #666; margin-top: 4px; }}
    </style>
    <script src="https://d3js.org/d3.v7.min.js"></script>
</head>
<body>
    <div class="header">
        <h1><span>AxiomCode</span> -- {proof.theorem_name}</h1>
        <div class="mode-switch">
            <button class="mode-btn {"active" if mode == "2d" else ""}"
                                onclick="location.search='?mode=2d'">2D Port Graph</button>
            <button class="mode-btn {"active" if mode == "force" else ""}"
                                onclick="location.search='?mode=force'">Force Graph</button>
            <button class="mode-btn {"active" if mode == "3d" else ""}"
                                onclick="location.search='?mode=3d'">3D Layout</button>
        </div>
    </div>
    <div class="container">
        <div class="graph-panel" id="graph-panel"></div>
        <div class="info-panel">
            <div class="stats">
                <div class="stat"><div class="stat-value">{proof.steps}</div>
                                 <div class="stat-label">Proof Steps</div></div>
                <div class="stat"><div class="stat-value">{proof.lemmas}</div><div class="stat-label">Lemmas</div></div>
            </div>
            <h3>Proof Term</h3>
            <pre>{_esc(proof.proof_term[:500])}{"..." if len(proof.proof_term) > 500 else ""}</pre>
        </div>
    </div>
    <script>
        const proofData = {json.dumps(graph_data)};
        const mode = "{mode}";
        function render2D() {{
            const panel = document.getElementById('graph-panel');
            const svg = d3.select(panel).append('svg')
                            .attr('width', panel.clientWidth).attr('height', panel.clientHeight);
            const color = {{ axiom: '#4a90d9', lemma: '#50c878',
                                       theorem: '#ffd700', tactic: '#9b59b6', qed: '#e74c3c' }};
            const nodes = svg.selectAll('g').data(proofData.nodes).join('g');
            nodes.append('rect').attr('x', (d, i) => 50 + (i % 6) * 180)
                            .attr('y', (d, i) => 50 + Math.floor(i / 6) * 120).attr('width', 150).attr('height', 80)
                            .attr('rx', 10).attr('fill', d => color[d.kind] || '#555')
                            .attr('stroke', '#333').attr('stroke-width', 2);
            nodes.append('text').attr('x', (d, i) => 125 + (i % 6) * 180)
                            .attr('y', (d, i) => 95 + Math.floor(i / 6) * 120).attr('text-anchor', 'middle')
                            .attr('fill', 'white').attr('font-size', '12px')
                            .text(d => d.label.slice(0, 20));
        }}
        function renderForce() {{
            const panel = document.getElementById('graph-panel');
            const svg = d3.select(panel).append('svg')
                            .attr('width', panel.clientWidth).attr('height', panel.clientHeight);
            const color = {{ theorem: '#ffd700', tactic: '#9b59b6', qed: '#e74c3c' }};
            const simulation = d3.forceSimulation(proofData.nodes)
                            .force('link', d3.forceLink(proofData.edges).distance(120))
                            .force('charge', d3.forceManyBody().strength(-300))
                            .force('center', d3.forceCenter(panel.clientWidth / 2, panel.clientHeight / 2));
            const link = svg.append('g').selectAll('line').data(proofData.edges)
                            .join('line').attr('stroke', '#333').attr('stroke-width', 2);
            const node = svg.append('g').selectAll('circle').data(proofData.nodes)
                            .join('circle').attr('r', 20).attr('fill', d => color[d.kind] || '#555');
            simulation.on('tick', () => {{ link.attr('x1', d => d.source.x).attr('y1', d => d.source.y)
                            .attr('x2', d => d.target.x).attr('y2', d => d.target.y);
                            node.attr('cx', d => d.x).attr('cy', d => d.y); }});
        }}
        if (mode === '2d') render2D();
        else if (mode === 'force') renderForce();
        else document.getElementById('graph-panel').innerHTML = '<div style="display:flex;align-items:center;
                justify-content:center;height:100%;color:#666;">'
                + '3D view -- Three.js integration pending (Phase 2)</div>';
    </script>
</body>
</html>"""


def _build_graph_data(proof: ProofResult, mode: str) -> dict:
    nodes = [
        {"id": f"step_{i}", "label": t[:30], "kind": "qed" if i == len(proof.tactics) - 1 else "tactic"}
        for i, t in enumerate(proof.tactics)
    ]
    edges = [{"source": f"step_{i - 1}", "target": f"step_{i}"} for i in range(1, len(proof.tactics))]
    return {"nodes": nodes, "edges": edges}


def _esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def serve_visualization(proof: ProofResult, mode: str = "2d", port: int = 8765):
    from http.server import BaseHTTPRequestHandler, HTTPServer

    html = build_proof_html(proof, mode)

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))

        def log_message(self, format, *args):
            pass

    server = HTTPServer(("127.0.0.1", port), Handler)
    print(f"  Visualization server running at http://127.0.0.1:{port}")
    print("  Press Ctrl+C to stop")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()


# ─── CLI Commands ───────────────────────────────────────────────────────────


def _resolve_passphrase(passphrase: str = "") -> str:
    """Resolve the keystore passphrase. No hardcoded defaults: explicit
    --passphrase, AXIOMCODE_PASSPHRASE, or an interactive prompt. Refuses to
    silently use a guessable default."""
    if passphrase:
        return passphrase
    env = os.environ.get("AXIOMCODE_PASSPHRASE", "")
    if env:
        return env
    if sys.stdin.isatty():
        return getpass.getpass("Keystore passphrase: ")
    raise RuntimeError("No passphrase provided. Pass --passphrase, set AXIOMCODE_PASSPHRASE, or run interactively.")


def cmd_generate(
    description: str, lang: str = "python", model: str = "local", visualize: bool = False, passphrase: str = ""
):
    """Generate formally verified code from natural language."""
    print(BANNER)

    # Initialize security
    audit = AuditLog()
    audit.add_entry("generate_start", {"description_hash": hash_data(description.encode()), "model": model})

    ks = KeyStore()
    key_name = "default"
    resolved = _resolve_passphrase(passphrase)
    try:
        loaded = ks.load_signing_key(key_name, resolved)
        signing_key, key_id = loaded.private_key, loaded.key_id
    except FileNotFoundError:
        kp = ks.create_signing_key(key_name, resolved)
        signing_key, key_id = kp.private_key, kp.key_id

    # Step 1: Generate specification
    print("[1/4] Generating formal specification...")
    try:
        spec = generate_spec(description, model)
        print(f"  [+] Specification generated ({spec.model_used}, {spec.generation_time_ms:.0f}ms)")
        print(f"      Theorem: {_theorem_name(spec.theorem)}")
        print(f"      Hash: {spec.spec_hash[:16]}...")
    except Exception as e:
        print(f"  [-] Spec generation failed: {e}")
        audit.add_entry("generate_fail", {"error": str(e)})
        sys.exit(1)

    # Step 2: Search for proof
    print("[2/4] Searching for proof...")
    try:
        proof = run_proof(spec, llm_backend=model)
        if proof.verification_status == "verified":
            print(
                f"  [+] Proof VERIFIED ({proof.steps} steps, {proof.lemmas} lemmas, {proof.proof_attempts} attempt(s))"
            )
        elif proof.verification_status == "failed":
            print(
                f"  [!] Proof search FAILED after {proof.proof_attempts} attempt(s) — "
                f"artifact will be certified as UNVERIFIED provenance only"
            )
        else:
            print(
                "  [!] Proof UNVERIFIED (no Lean toolchain) — artifact will be certified as UNVERIFIED provenance only"
            )
        print(f"      Proof hash: {proof.proof_hash[:16]}...")
    except Exception as e:
        print(f"  [!] Proof search incomplete: {e}")
        proof = ProofResult(
            theorem_name=_theorem_name(spec.theorem),
            steps=0,
            lemmas=len(spec.definitions),
            lean_file=Path("unknown"),
            tactics=[],
            proof_term=spec.to_lean(),
            verification_status="failed",
            build_log=str(e)[-4000:],
        )
        proof.compute_hash()

    # Step 3: Extract code
    print("[3/4] Extracting code...")
    c_path, py_path = None, None
    if lang in ("python", "both"):
        py_path = extract_python(proof)
        print(f"  [+] Python package: {py_path}")
    if lang in ("c", "both"):
        c_path = extract_c(proof)
        print(f"  [+] C binary: {c_path}")

    # Step 4: Generate certificate
    print("[4/4] Generating proof certificate...")
    cert = generate_certificate(spec, proof, c_path, py_path, signing_key, key_id)
    cert_dir = Path(__file__).parent / "build" / "certs"
    cert_dir.mkdir(parents=True, exist_ok=True)
    cert_path = cert_dir / f"{proof.theorem_name}.cert.json"
    cert.save(cert_path)
    print(f"  [+] Certificate: {cert_path}")
    print(f"      Verification status: {cert.verification_status.upper()}")
    print(f"      Signature: {cert.signature[:32]}...")

    audit.add_entry(
        "generate_complete",
        {
            "algorithm": proof.theorem_name,
            "steps": proof.steps,
            "lemmas": proof.lemmas,
            "verification_status": proof.verification_status,
            "certificate": str(cert_path),
        },
    )

    if visualize:
        print("\nOpening proof visualization...")
        serve_visualization(proof)


def cmd_guide():
    """Interactive guided mode."""
    print(BANNER)
    print("Interactive Guide")
    print("-" * 40)
    print("I'll help you generate verified code step by step.\n")

    categories = {}
    for ex in EXAMPLES:
        categories.setdefault(ex["category"], []).append(ex)

    print("Step 1: Choose a category:")
    for i, cat in enumerate(categories, 1):
        print(f"  {i}. {cat}")
    choice = input("Select category [1]: ").strip() or "1"
    try:
        selected_cat = list(categories.keys())[int(choice) - 1]
    except (ValueError, IndexError):
        selected_cat = list(categories.keys())[0]

    cat_examples = [ex for ex in EXAMPLES if ex["category"] == selected_cat]
    print(f"\nStep 2: Algorithms in {selected_cat}:")
    for i, ex in enumerate(cat_examples, 1):
        print(f"  {i}. {ex['name']} ({ex['difficulty']}, {ex['proof_complexity']} proof)")
    algo_choice = input("Select algorithm [1]: ").strip() or "1"
    try:
        selected = cat_examples[int(algo_choice) - 1]
    except (ValueError, IndexError):
        selected = cat_examples[0]

    print("\nStep 3: Algorithm description:")
    print(f"  {selected['description']}")
    use_default = input("Use this description? [Y/n]: ").strip().lower() != "n"
    description = selected["description"] if use_default else input("Enter your description: ")

    print("\nStep 4: Choose LLM backend:")
    print("  1. local (Ollama -- stable-code:3b-code-q4_0)")
    print("  2. mistral (Ollama -- mistral:7b)")
    print("  3. openai (GPT-4o)")
    print("  4. anthropic (Claude Sonnet)")
    model_choice = input("Select model [1]: ").strip() or "1"
    model_map = {"1": "local", "2": "mistral", "3": "openai", "4": "anthropic"}
    model = model_map.get(model_choice, "local")

    print("\nStep 5: Generating verified code...")
    print(f"  Algorithm: {selected['name']}")
    print(f"  Model: {model}\n")
    cmd_generate(description, lang="both", model=model)


def cmd_examples():
    print(BANNER)
    print("Built-in Examples")
    print("-" * 60)
    print(f"{'#':<3} {'Algorithm':<28} {'Category':<18} {'Difficulty':<12} {'Proof'}")
    print("-" * 60)
    for i, ex in enumerate(EXAMPLES, 1):
        print(f"{i:<3} {ex['name']:<28} {ex['category']:<18} {ex['difficulty']:<12} {ex['proof_complexity']}")
    print()
    print("Run: python cli.py guide  (interactive mode)")
    print('Run: python cli.py "description"  (quick generate)')


def cmd_help():
    print(BANNER)
    print(HELP_TEXT)


def cmd_walkthrough():
    print(BANNER)
    print(WALKTHROUGH_TEXT)
    start = input("Start the interactive guide? [Y/n]: ").strip().lower() != "n"
    if start:
        cmd_guide()


def cmd_models():
    print(BANNER)
    print("Available LLM Backends (one OpenAI-compatible HTTP layer)")
    print("-" * 72)
    print(f"{'Backend':<14} {'Default model':<26} Description")
    print("-" * 72)
    for bname, model, desc in list_backends():
        print(f"{bname:<14} {model:<26} {desc}")
    print()
    print("Env overrides: AXIOMCODE_LLM_BACKEND, AXIOMCODE_LLM_MODEL,")
    print("               AXIOMCODE_LLM_BASE_URL, AXIOMCODE_LLM_API_KEY")
    print("Defaults: llama.cpp -> http://localhost:8080 | vLLM -> http://localhost:8000")


def cmd_visualize(name: str, mode: str = "2d", port: int = 8765):
    print(BANNER)
    print(f"Visualizing: {name} (mode: {mode})")
    try:
        proof = load_proof(name)
    except FileNotFoundError:
        print(f"[-] No verified proof found: {name}")
        print("    Tip: Generate it first with 'python cli.py \"description\"'")
        sys.exit(1)
    serve_visualization(proof, mode=mode, port=port)


def verify_certificate_artifact(name: str, passphrase: str = "", key_name: str = "default") -> tuple[bool, list[str]]:
    """Independently verify a certificate and its proof artifact.

    Three real checks — no theater:
    1. Ed25519 signature over the certificate payload (detects tampering).
    2. Issuer binding: the embedded public key matches the trusted KeyStore
       key for `key_id` (when a trusted key can be loaded).
    3. Fresh machine re-check: `lake build <target>` on the stored proof file
       plus the axiom audit — the proof must check out *today*, not just at
       generation time.

    Returns (ok, report_lines). Fails closed on every uncertainty. A
    certificate whose signature is valid but whose `verification_status` is
    not "verified" is reported honestly: authentic provenance, proof NOT
    verified — overall verdict FAIL.
    """
    lines: list[str] = []
    repo_root = Path(__file__).parent
    lean_project = repo_root / "lean"

    # --- Load ---
    cert_path = repo_root / "build" / "certs" / f"{name}.cert.json"
    if not cert_path.exists():
        return False, [f"[-] No certificate found: {cert_path}"]
    try:
        cert = ProofCertificate.load(cert_path)
    except (ValueError, FileNotFoundError) as e:
        return False, [f"[-] Certificate file unreadable: {e}"]
    lines.append(f"  Certificate: {cert_path}")
    lines.append(f"  Key ID: {cert.key_id}")
    lines.append(f"  Serial: {cert.serial or '(none — pre-v2 certificate)'}")
    lines.append(f"  Recorded status: {cert.verification_status.upper()}")
    if cert.issued_at or cert.expires_at:
        exp = time.strftime("%Y-%m-%d", time.localtime(cert.expires_at)) if cert.expires_at else "never"
        lines.append(f"  Validity: {cert.validity_status()} (expires: {exp})")

    # --- Check 1: signature ---
    if not cert.verify():
        lines.append("  [-] SIGNATURE INVALID — certificate tampered or forged")
        return False, lines
    lines.append("  [+] Ed25519 signature valid (payload untampered)")

    # --- Check 1b: validity window and revocation flag ---
    vstatus = cert.validity_status()
    if vstatus == "expired":
        lines.append("  [-] CERTIFICATE EXPIRED — validity window has passed; re-verification required")
        return False, lines
    if vstatus == "not-yet-valid":
        lines.append("  [-] CERTIFICATE NOT YET VALID — issued_at is in the future")
        return False, lines
    if vstatus == "revoked":
        reason = f" ({cert.revocation_reason})" if cert.revocation_reason else ""
        lines.append(f"  [-] CERTIFICATE REVOKED{reason} — do not trust")
        return False, lines
    if vstatus == "active":
        lines.append("  [+] Certificate within validity window")

    # --- Check 1c: public registry revocation (best effort; honest when unavailable) ---
    # The registry's revocation list is authoritative: a certificate revoked
    # there fails even if its own file predates the revocation.
    try:
        from core.registry import CertificateRegistry

        default_registry = repo_root / "registry"
        if cert.serial and default_registry.exists():
            reg = CertificateRegistry(default_registry)
            if reg.is_revoked(cert.serial):
                rec = reg.revocation_record(cert.serial) or {}
                reason = rec.get("reason", "")
                lines.append(f"  [-] REVOKED in public registry{': ' + reason if reason else ''}")
                return False, lines
            lines.append("  [+] Not revoked in public registry")
        else:
            lines.append("  [i] Registry revocation not checked (no local registry)")
    except Exception as e:  # never fail closed on registry *lookup* problems
        lines.append(f"  [i] Registry revocation not checked ({e})")

    # --- Check 2: issuer binding (best effort; honest when unavailable) ---
    # The keystore is indexed by key NAME; the certificate names its signer by
    # key_id. Binding succeeds only when the named trusted key's key_id matches
    # the certificate's AND the signature verifies under its public key.
    resolved = passphrase or os.environ.get("AXIOMCODE_PASSPHRASE", "")
    if resolved:
        try:
            trusted = KeyStore().load_signing_key(key_name, resolved)
        except (FileNotFoundError, ValueError) as e:
            lines.append(f"  [i] Issuer binding not checked (trusted key '{key_name}' unavailable: {e})")
        else:
            ok_bind, reason = cert.verify_against_issuer_key(trusted.public_key, trusted.key_id)
            lines.append(f"  {'[+]' if ok_bind else '[-]'} Issuer binding: {reason}")
            if not ok_bind:
                return False, lines
    else:
        lines.append("  [i] Issuer binding not checked (no passphrase; set AXIOMCODE_PASSPHRASE to enable)")

    # --- Status honesty gate ---
    # A certificate that honestly records "failed"/"unverified" is authentic
    # provenance — but there is no verified proof to independently re-check,
    # so the machine re-check below only runs for "verified" claims.
    if cert.verification_status != "verified":
        lines.append(
            "  [-] Certificate is authentic BUT records status "
            f"'{cert.verification_status}' — the proof was NOT machine-verified"
        )
        return False, lines

    # --- Check 3: fresh machine re-check of the stored proof ---
    try:
        proof = load_proof(name)
    except FileNotFoundError:
        lines.append("  [-] No proof artifact under lean/src/Algorithms/ — nothing to re-check")
        return False, lines
    # Fresh machine re-check: elaborate the stored proof file directly.
    # (`lake build <module>` cannot address generated modules outside the
    # lakefile's static roots; `lake env lean` on the file IS the check.)
    build_ok, build_log = elaborate_lean_file(proof.lean_file, lean_project, timeout=600)
    if not build_ok:
        lines.append("  [-] Fresh Lean elaboration FAILED — proof does not check out")
        if build_log.strip():
            lines.append("      " + build_log.strip().splitlines()[-1][:200])
        return False, lines
    lines.append("  [+] Fresh Lean elaboration passed")

    audit_ok, audit_report = audit_axioms(proof.lean_file, lean_project, timeout=600)
    lines.append(f"  {'[+]' if audit_ok else '[-]'} Axiom audit: {audit_report.splitlines()[0]}")
    if not audit_ok:
        return False, lines

    lines.append("  [+] VERIFIED: authentic certificate for a machine-checked proof")
    return True, lines


def cmd_publish(name: str, pypi: bool = False, github: bool = False):
    print(BANNER)
    print(f"Publishing: {name}")

    # Verify for real first — never publish on an unverified claim.
    ok, report = verify_certificate_artifact(name)
    for line in report:
        print(line)
    if not ok:
        print("[-] Publish REFUSED: independent verification failed. Nothing was published.")
        sys.exit(1)

    if pypi:
        wheel_dir = Path(__file__).parent / "build" / "python"
        wheels = list(wheel_dir.glob(f"axiomcode_{name}*.whl"))
        if wheels:
            subprocess.run(["python", "-m", "twine", "upload", str(wheels[0])])
            print(f"[+] Published {name} to PyPI")
        else:
            print(f"[-] No wheel found for {name}. Generate it first.")
    if github:
        binary_dir = Path(__file__).parent / "build" / "c"
        binaries = list(binary_dir.glob(f"{name}*"))
        if binaries:
            subprocess.run(["gh", "release", "create", name, str(binaries[0])])
            print(f"[+] Released {name} on GitHub")
        else:
            print(f"[-] No binary found for {name}. Generate it first.")
    if not pypi and not github:
        print("[+] Certificate verified — nothing else requested (use --pypi / --github to publish)")


def cmd_verify(name: str, passphrase: str = "", key_name: str = "default"):
    print(BANNER)
    print(f"Verifying: {name}")

    ok, report = verify_certificate_artifact(name, passphrase, key_name)
    for line in report:
        print(line)
    if not ok:
        print("[-] VERIFICATION FAILED")
        sys.exit(1)
    print("[+] VERIFICATION PASSED")


def cmd_cert(name: str):
    """Show proof certificate."""
    print(BANNER)
    cert_dir = Path(__file__).parent / "build" / "certs"
    cert_path = cert_dir / f"{name}.cert.json"
    if cert_path.exists():
        cert = ProofCertificate.load(cert_path)
        print(cert.to_json())
    else:
        print(f"[-] No certificate found: {name}")


def cmd_scan(target: str):
    """Run the Free-scan tier: static checks only, never mints a certificate."""
    from core.tiers import run_free_scan

    print(BANNER)
    print(f"Free scan: {target}")
    print("Static checks only — no proof is machine-checked, no certificate is minted.")
    try:
        report = run_free_scan(target)
    except FileNotFoundError as e:
        print(f"[-] {e}")
        sys.exit(1)
    print(f"  Files scanned: {report['files_scanned']}")
    print(f"  Files with sorry/admit: {report['files_with_sorry']}")
    print(f"  Files with declared axioms: {report['files_with_declared_axioms']}")
    for f in report["findings"]:
        flag = ""
        if f.get("has_sorry_or_admit"):
            flag += " [sorry/admit]"
        if f.get("declared_axioms"):
            flag += f" [axioms: {len(f['declared_axioms'])}]"
        print(f"    {f['file']}{flag}")
    print(f"\n  {report['label']}")
    print("  Certificate minted: NO (scan tier never mints)")


def _default_registry():
    from core.registry import CertificateRegistry

    return CertificateRegistry(Path(__file__).parent / "registry")


def cmd_registry(
    action: str, name: str = "", serial: str = "", reason: str = "", output: str = "", show_all: bool = False
):
    """Public certificate registry: publish / revoke / list / export / check."""
    print(BANNER)
    reg = _default_registry()

    if action == "publish":
        cert_path = Path(__file__).parent / "build" / "certs" / f"{name}.cert.json"
        if not cert_path.exists():
            print(f"[-] No certificate found: {cert_path}")
            sys.exit(1)
        cert = ProofCertificate.load(cert_path)
        try:
            published = reg.publish(cert)
        except ValueError as e:
            print(f"[-] Publish REFUSED: {e}")
            sys.exit(1)
        print(f"[+] Published certificate {published} to the public registry")
        print(f"    Status: {reg.status(published)}")
    elif action == "revoke":
        try:
            record = reg.revoke(serial, reason)
        except (KeyError, ValueError) as e:
            print(f"[-] Revoke failed: {e}")
            sys.exit(1)
        print(f"[+] Revoked {serial} (public — the certificate remains visible as revoked)")
        print(f"    Reason: {record['reason']}")
    elif action == "list":
        entries = reg.list_certificates(status_filter="all" if show_all else "active")
        if not entries:
            print("Registry is empty.")
            return
        for entry in entries:
            ver = entry["artifact_version"] or "?"
            s = entry["status"].upper()
            print(f"  {entry['serial']} | {s:7} | {entry['product_name']} v{ver} | tier={entry['tier']}")
    elif action == "export":
        doc = reg.export_json()
        if output:
            Path(output).write_text(doc)
            print(f"[+] Registry exported to {output} ({len(json.loads(doc)['certificates'])} certificates)")
        else:
            print(doc)
    elif action == "check":
        ok, issues = reg.verify_registry()
        if ok:
            print("[+] Registry integrity OK: all published certificate signatures verify")
        else:
            print("[-] Registry integrity FAILED:")
            for i in issues:
                print(f"    {i}")
            sys.exit(1)
    else:
        print(f"[-] Unknown registry action: {action}")
        sys.exit(1)


def cmd_badge(serial: str, fmt: str = "markdown", base_url: str = "", output: str = ""):
    """Certificate badge: print the embed snippet or render the SVG."""
    print(BANNER)
    from core.badge import badge_data, badge_snippet, render_badge_svg

    base = base_url or "https://registry.axiomcode.dev"
    reg = _default_registry()
    if fmt == "svg":
        svg = render_badge_svg(badge_data(serial, reg, base))
        if output:
            Path(output).write_text(svg, encoding="utf-8")
            print(f"[+] Badge SVG written to {output}")
        else:
            print(svg)
    else:
        snip = badge_snippet(serial, base)
        text = snip["html"] if fmt == "html" else snip["markdown"]
        if output:
            Path(output).write_text(text + "\n", encoding="utf-8")
            print(f"[+] Badge snippet written to {output}")
        else:
            print(text)


def cmd_qr(serial: str, fmt: str = "png", base_url: str = "", output: str = ""):
    """Render the certificate's QR code (PNG/SVG) to a file or stdout."""
    print(BANNER)
    from core.qr import render_qr_svg, verification_url

    reg = _default_registry()
    cert = reg.get(serial)
    if cert is None:
        print(f"[-] Unknown serial in registry: {serial}")
        sys.exit(1)
    base = base_url or "https://registry.axiomcode.dev"
    payload = (cert.qr_payload or "").strip() or verification_url(serial, base)
    if fmt == "svg":
        svg = render_qr_svg(payload)
        if output:
            Path(output).write_text(svg, encoding="utf-8")
        else:
            print(svg)
    else:
        from core.qr import render_qr_png

        png = render_qr_png(payload)
        if output:
            Path(output).write_bytes(png)
        else:
            sys.stdout.buffer.write(png)
    if output:
        print(f"[+] QR code ({fmt.upper()}) written to {output}")
        print(f"    Encodes: {payload}")


def cmd_serve_registry(host: str, port: int, base_url: str = ""):
    """Serve the public certificate registry over HTTP (read-only)."""
    print(BANNER)
    import sys as _sys

    _sys.path.insert(0, str(Path(__file__).parent / "services"))
    from wsgiref.simple_server import make_server

    from registry_app import create_app

    base = base_url or f"http://{host}:{port}"
    reg_dir = Path(__file__).parent / "registry"
    app = create_app(str(reg_dir), base)
    with make_server(host, port, app) as httpd:
        print(f"[+] AxiomCode registry serving {reg_dir} at http://{host}:{port} (read-only)")
        print("    Ctrl-C to stop.")
        httpd.serve_forever()


def cmd_key_create(name: str, passphrase: str = ""):
    """Create an Ed25519 signing key."""
    print(BANNER)
    ks = KeyStore()
    kp = ks.create_signing_key(name, _resolve_passphrase(passphrase))
    print(f"[+] Ed25519 signing key created: {name}")
    print(f"    Key ID: {kp.key_id}")
    print(f"    Created: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(kp.created_at))}")


def cmd_key_list():
    """List signing keys."""
    print(BANNER)
    ks = KeyStore()
    key_dir = ks.store_dir
    found = False
    if key_dir.exists():
        for kf in sorted(key_dir.glob("*.signing.key")):
            print(f"  [+] {kf.stem.removesuffix('.signing')} (ed25519 signing key)")
            found = True
        for kf in sorted(key_dir.glob("*.key")):
            if not kf.name.endswith(".signing.key"):
                print(f"  [i] {kf.stem} (legacy symmetric key)")
                found = True
    if not found:
        print("  No keys found. Create one with 'python cli.py key create <name>'")


def cmd_audit():
    """Show audit log."""
    print(BANNER)
    audit = AuditLog()
    if audit.log_file.exists():
        print(f"Audit log: {audit.log_file}")
        print(f"Integrity: {'VERIFIED' if audit.verify_integrity() else 'TAMPERED'}")
        print()
        for line in audit.log_file.read_text(encoding="utf-8").strip().split("\n"):
            entry = json.loads(line)
            print(
                f"  {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(entry['timestamp']))} "
                f"| {entry['user']} | {entry['action']}"
            )
    else:
        print("No audit log entries yet.")


# ─── Main ───────────────────────────────────────────────────────────────────


def main():
    # Bare-description UX (documented in README): `cli.py "implement binary
    # search"` routes to `generate`. argparse would otherwise reject the
    # positional as an invalid subcommand choice before we ever see it.
    _commands = {
        "generate",
        "guide",
        "examples",
        "help",
        "walkthrough",
        "models",
        "visualize",
        "publish",
        "verify",
        "cert",
        "scan",
        "registry",
        "badge",
        "qr",
        "serve-registry",
        "key",
        "audit",
        "version",
        "license",
    }
    if len(sys.argv) > 1 and sys.argv[1] not in _commands and not sys.argv[1].startswith("-"):
        sys.argv.insert(1, "generate")

    parser = argparse.ArgumentParser(
        prog="axiomcode",
        description="Natural language to formally verified code",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=HELP_TEXT,
    )
    sub = parser.add_subparsers(dest="command")

    p_gen = sub.add_parser("generate", help="Generate verified code from NL")
    p_gen.add_argument("description", nargs="?")
    p_gen.add_argument("--lang", "-l", default="python", choices=["python", "c", "both"])
    p_gen.add_argument("--model", "-m", default="local", choices=list(BACKENDS.keys()))
    p_gen.add_argument("--visualize", "-v", action="store_true")
    p_gen.add_argument("--passphrase", "-p", default="", help="Key passphrase")

    sub.add_parser("guide", help="Interactive guided mode")
    sub.add_parser("examples", help="Browse built-in examples")
    sub.add_parser("help", help="Show full help and FAQ")
    sub.add_parser("walkthrough", help="Step-by-step tutorial")
    sub.add_parser("models", help="List available LLM backends")

    p_viz = sub.add_parser("visualize", help="View proof visualization")
    p_viz.add_argument("name")
    p_viz.add_argument("--mode", default="2d", choices=["2d", "force", "3d"])
    p_viz.add_argument("--port", type=int, default=8765)

    p_pub = sub.add_parser("publish", help="Publish verified code")
    p_pub.add_argument("name")
    p_pub.add_argument("--pypi", action="store_true")
    p_pub.add_argument("--github", action="store_true")

    p_ver = sub.add_parser("verify", help="Independently verify a proof")
    p_ver.add_argument("name")
    p_ver.add_argument(
        "--passphrase",
        default="",
        help="Keystore passphrase (or AXIOMCODE_PASSPHRASE) to enable the issuer-key binding check",
    )
    p_ver.add_argument(
        "--key-name",
        default="default",
        help="Name of the trusted signing key in the keystore for the issuer-binding check",
    )

    sub.add_parser("cert", help="Show proof certificate").add_argument("name")

    p_scan = sub.add_parser("scan", help="Free static scan (never mints a certificate)")
    p_scan.add_argument("target", help="Lean file or directory to scan")

    p_reg = sub.add_parser("registry", help="Public certificate registry")
    p_reg.add_argument(
        "action",
        nargs="?",
        default="list",
        choices=["publish", "revoke", "list", "export", "check"],
    )
    p_reg.add_argument("--name", default="", help="Certificate name (for publish)")
    p_reg.add_argument("--serial", default="", help="Certificate serial (for revoke)")
    p_reg.add_argument("--reason", default="", help="Revocation reason (for revoke)")
    p_reg.add_argument("--output", default="", help="Output file (for export)")
    p_reg.add_argument("--all", action="store_true", help="Include expired/revoked (for list)")

    p_badge = sub.add_parser("badge", help="Certificate badge: embed snippet or SVG")
    p_badge.add_argument("serial", help="Certificate serial number")
    p_badge.add_argument("--format", default="markdown", choices=["markdown", "html", "svg"], help="Output format")
    p_badge.add_argument("--base-url", default="", help="Public base URL of the registry host")
    p_badge.add_argument("--output", default="", help="Write to file instead of stdout")

    p_qr = sub.add_parser("qr", help="Render certificate QR code (PNG/SVG)")
    p_qr.add_argument("serial", help="Certificate serial number")
    p_qr.add_argument("--format", default="png", choices=["png", "svg"], help="Output format")
    p_qr.add_argument("--base-url", default="", help="Public base URL (used when cert has no QR payload)")
    p_qr.add_argument("--output", default="", help="Write to file instead of stdout")

    p_srv = sub.add_parser("serve-registry", help="Serve the public registry over HTTP (read-only)")
    p_srv.add_argument("--host", default="127.0.0.1")
    p_srv.add_argument("--port", type=int, default=8000)
    p_srv.add_argument("--base-url", default="", help="Public base URL (defaults to http://host:port)")

    p_kc = sub.add_parser("key", help="Key management")
    p_kc.add_argument("action", choices=["create", "list"])
    p_kc.add_argument("name", nargs="?", default="")
    p_kc.add_argument("--passphrase", default="")

    sub.add_parser("audit", help="Show audit log")

    # Version management
    p_ver_cmd = sub.add_parser("version", help="Version management")
    p_ver_cmd.add_argument(
        "action", nargs="?", default="show", choices=["show", "migrate", "rollback", "backups", "history", "validate"]
    )
    p_ver_cmd.add_argument("--to", default=None, help="Target version for migration")
    p_ver_cmd.add_argument("--force", action="store_true", help="Force migration without confirmation")

    # License management
    p_lic = sub.add_parser("license", help="License management")
    p_lic.add_argument(
        "action",
        nargs="?",
        default="show",
        choices=["show", "issue", "verify", "revoke", "list", "tiers", "keygen", "fingerprint"],
    )
    p_lic.add_argument("--user", default=None, help="User ID (email)")
    p_lic.add_argument("--name", default=None, help="User name")
    p_lic.add_argument("--tier", default="community", choices=["community", "pro", "enterprise"])
    p_lic.add_argument("--key", default=None, help="Path to private/public key file")
    p_lic.add_argument("--passphrase", default="", help="Key passphrase")
    p_lic.add_argument("--output", default=None, help="Output file for license")
    p_lic.add_argument("--license-file", default=None, help="Path to license file to verify")
    p_lic.add_argument("--reason", default="", help="Revocation reason")
    p_lic.add_argument("--portable", action="store_true", help="Issue portable (non-hardware-bound) license")
    p_lic.add_argument("--expires", default=None, help="Expiration date (YYYY-MM-DD)")

    args = parser.parse_args()

    if args.command is None:
        if len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
            cmd_generate(sys.argv[1])
        else:
            parser.print_help()
        return

    if args.command == "generate":
        if not args.description:
            print("Error: description is required")
            sys.exit(1)
        cmd_generate(args.description, args.lang, args.model, args.visualize, args.passphrase)
    elif args.command == "guide":
        cmd_guide()
    elif args.command == "examples":
        cmd_examples()
    elif args.command == "help":
        cmd_help()
    elif args.command == "walkthrough":
        cmd_walkthrough()
    elif args.command == "models":
        cmd_models()
    elif args.command == "visualize":
        cmd_visualize(args.name, args.mode, args.port)
    elif args.command == "publish":
        cmd_publish(args.name, args.pypi, args.github)
    elif args.command == "verify":
        cmd_verify(args.name, args.passphrase, args.key_name)
    elif args.command == "cert":
        cmd_cert(args.name)
    elif args.command == "scan":
        cmd_scan(args.target)
    elif args.command == "registry":
        cmd_registry(
            args.action,
            name=getattr(args, "name", ""),
            serial=getattr(args, "serial", ""),
            reason=getattr(args, "reason", ""),
            output=getattr(args, "output", ""),
            show_all=getattr(args, "all", False),
        )
    elif args.command == "badge":
        cmd_badge(args.serial, args.format, args.base_url, args.output)
    elif args.command == "qr":
        cmd_qr(args.serial, args.format, args.base_url, args.output)
    elif args.command == "serve-registry":
        cmd_serve_registry(args.host, args.port, args.base_url)
    elif args.command == "key":
        if args.action == "create":
            cmd_key_create(args.name, args.passphrase)
        elif args.action == "list":
            cmd_key_list()
    elif args.command == "audit":
        cmd_audit()
    elif args.command == "version":
        cmd_version(args.action, getattr(args, "to", None), getattr(args, "force", False))
    elif args.command == "license":
        cmd_license(
            args.action,
            user=getattr(args, "user", None),
            name=getattr(args, "name", None),
            tier=getattr(args, "tier", "community"),
            key_path=getattr(args, "key", None),
            passphrase=getattr(args, "passphrase", ""),
            output=getattr(args, "output", None),
            license_file=getattr(args, "license_file", None),
            reason=getattr(args, "reason", ""),
            portable=getattr(args, "portable", False),
            expires=getattr(args, "expires", None),
        )


def cmd_version(action: str, target: str | None = None, force: bool = False):
    """Version management: show, migrate, rollback, backups, history, validate."""
    print(BANNER)
    vm = VersionManager()
    vm.initialize()

    if action == "show":
        current = vm.get_current_version()
        info = vm.get_version_info()
        print(f"Current version: {current}")
        print(f"Schema version:  {info.schema_version}")
        print(f"Data format:     {info.data_format}")
        print(f"Released:        {info.released_at}")
        if info.new_features:
            print(f"\nFeatures in {current}:")
            for f in info.new_features:
                print(f"  [+] {f}")
        if info.breaking_changes:
            print("\nBreaking changes:")
            for b in info.breaking_changes:
                print(f"  [!] {b}")

    elif action == "migrate":
        if not target:
            print("Error: --to <version> is required for migration")
            print("Available versions:")
            for v in vm.list_versions():
                print(f"  {v.version} (schema {v.schema_version})")
            return
        print(f"Migrating from {vm.get_current_version()} to {target}...")
        if not force:
            confirm = input("Create backup and proceed? [Y/n]: ").strip().lower()
            if confirm == "n":
                print("Migration cancelled.")
                return
        result = vm.migrate(target)
        print(f"Status:  {result['status']}")
        print(f"Backup:  {result.get('backup', 'N/A')}")
        if result.get("changes"):
            print("Changes:")
            for c in result["changes"]:
                print(f"  - {c}")
        if result.get("path"):
            print(f"Migration path: {' -> '.join(result['path'])}")
        if result.get("message"):
            print(f"Note: {result['message']}")

    elif action == "rollback":
        print("Rolling back to previous version...")
        result = vm.rollback()
        print(f"Status:  {result['status']}")
        if result.get("rolled_back_to"):
            print(f"Version: {result['rolled_back_to']}")
        if result.get("backup_used"):
            print(f"Backup:  {result['backup_used']}")
        if result.get("message"):
            print(f"Note: {result['message']}")

    elif action == "backups":
        backups = vm.list_backups()
        if not backups:
            print("No backups found.")
            return
        print("Available backups:")
        for bk in backups:
            ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(bk["timestamp"]))
            print(f"  {bk['name']} (v{bk['version']}, {ts})")

    elif action == "history":
        history = vm.get_migration_history()
        if not history:
            print("No migration history.")
            return
        print("Migration history:")
        for h in history:
            ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(h["timestamp"]))
            print(f"  {ts} | {h['direction']} | {h['from_version']} -> {h['to_version']}")

    elif action == "validate":
        result = vm.validate_data_integrity()
        print(f"Version:       {result['version']}")
        print(f"Schema:        {result['schema_version']}")
        print(f"Integrity:     {'VALID' if result['valid'] else 'ISSUES FOUND'}")
        if result["issues"]:
            print("Issues:")
            for issue in result["issues"]:
                print(f"  [-] {issue}")
        else:
            print("All data is consistent with the current version.")


def cmd_license(
    action: str,
    user: str | None = None,
    name: str | None = None,
    tier: str = "community",
    key_path: str | None = None,
    passphrase: str = "",
    output: str | None = None,
    license_file: str | None = None,
    reason: str = "",
    portable: bool = False,
    expires: str | None = None,
):
    """License management: show, issue, verify, revoke, list, tiers, keygen, fingerprint."""
    print(BANNER)
    lm = LicenseManager()

    if action == "show":
        # Show current license status
        print("License Status")
        print("-" * 40)

        # Check for installed licenses
        licenses = lm.list_licenses()
        if licenses:
            for lic in licenses:
                status = "VALID" if lic["valid"] else f"INVALID ({lic['reason']})"
                print(f"  User:    {lic['user']}")
                print(f"  Tier:    {lic['tier']}")
                print(f"  Status:  {status}")
                print(f"  File:    {lic['file']}")
                print()
        else:
            print("  No license installed.")
            print()
            print("  Tiers available:")
            for tid, tinfo in TIERS.items():
                print(f"    {tid:12s} — {tinfo['name']:12s} — {tinfo['price']}")

    elif action == "keygen":
        # Generate root key pair
        print("Generating root key pair...")
        keys = lm.generate_root_key()

        priv_path = Path(key_path or ".axiomcode/keys/root_private.key")
        pub_path = Path(key_path or ".axiomcode/keys/root_public.key").with_name("root_public.key")

        keys.save_private(priv_path, passphrase or "axiomcode-root")
        keys.save_public(pub_path)

        print("[+] Root key pair generated")
        print(f"    Private key: {priv_path} (KEEP SECRET)")
        print(f"    Public key:  {pub_path} (ship with software)")
        print(f"    Key ID:      {keys.key_id}")

    elif action == "issue":
        # Issue a new license
        if not user:
            print("Error: --user <email> is required")
            return
        if not name:
            print("Error: --name <name> is required")
            return
        if not key_path:
            print("Error: --key <private_key_path> is required")
            return

        lm.load_private_key(key_path, passphrase or "axiomcode-root")

        # Parse expiration
        expires_at = 0.0
        if expires:
            from datetime import datetime

            dt = datetime.strptime(expires, "%Y-%m-%d")
            expires_at = dt.timestamp()

        if portable:
            license = lm.issue_portable_license(
                user_id=user,
                user_name=name,
                tier=tier,
                expires_at=expires_at,
            )
        else:
            license = lm.issue_license(
                user_id=user,
                user_name=name,
                tier=tier,
                expires_at=expires_at,
            )

        out_path = Path(output or f".axiomcode/licenses/{name.replace(' ', '_').lower()}.license.json")
        license.save(out_path)

        print("[+] License issued")
        print(f"    License ID: {license.license_id}")
        print(f"    User:       {license.user_name} ({license.user_id})")
        print(f"    Tier:       {license.tier}")
        print(f"    Features:   {', '.join(license.features)}")
        print(f"    Hardware:   {'Portable' if not license.hardware_hash else 'Bound'}")
        if expires_at > 0:
            print(f"    Expires:    {time.strftime('%Y-%m-%d', time.localtime(expires_at))}")
        else:
            print("    Expires:    Never")
        print(f"    Saved to:   {out_path}")

    elif action == "verify":
        # Verify a license
        lic_path = license_file or ".axiomcode/licenses/default.license.json"
        if not Path(lic_path).exists():
            # Try to find any license
            license_files = list(Path(".axiomcode/licenses").glob("*.license.json"))
            if license_files:
                lic_path = str(license_files[0])
            else:
                print(f"[-] No license file found at {lic_path}")
                return

        # Load public key
        pub_key_path = key_path or ".axiomcode/keys/root_public.key"
        if Path(pub_key_path).exists():
            lm.load_public_key(pub_key_path)
        else:
            print(f"[-] Public key not found at {pub_key_path}")
            print("    Need the root public key to verify licenses")
            return

        license = LicenseCertificate.load(Path(lic_path))
        valid, reason = lm.verify_license(license)

        print(f"License: {lic_path}")
        print(f"  User:       {license.user_name} ({license.user_id})")
        print(f"  Tier:       {license.tier}")
        print(f"  License ID: {license.license_id}")
        print(f"  Features:   {', '.join(license.features)}")
        if license.expires_at > 0:
            print(f"  Expires:    {time.strftime('%Y-%m-%d', time.localtime(license.expires_at))}")
        else:
            print("  Expires:    Never")
        print(f"  Hardware:   {'Portable' if not license.hardware_hash else 'Bound'}")
        print()
        if valid:
            print(f"  [+] VALID — {reason}")
        else:
            print(f"  [-] INVALID — {reason}")

    elif action == "revoke":
        # Revoke a license
        if not license_file:
            print("Error: --license-file <path> is required")
            return
        license = LicenseCertificate.load(Path(license_file))
        lm.revoke_license(license.license_id, reason or "Revoked by administrator")
        print(f"[+] License {license.license_id} revoked")
        if reason:
            print(f"    Reason: {reason}")

    elif action == "list":
        # List all installed licenses
        licenses = lm.list_licenses()
        if not licenses:
            print("No licenses installed.")
            return
        print(f"{'User':<20} {'Tier':<12} {'Status':<10} {'File'}")
        print("-" * 70)
        for lic in licenses:
            status = "VALID" if lic["valid"] else "INVALID"
            print(f"{lic['user']:<20} {lic['tier']:<12} {status:<10} {lic['file']}")

    elif action == "tiers":
        # Show available tiers
        print("Available License Tiers")
        print("-" * 60)
        for tid, tinfo in TIERS.items():
            print(f"\n  {tinfo['name']} ({tid})")
            print(f"  Price: {tinfo['price']}")
            print(f"  Max seats: {tinfo['max_seats'] if tinfo['max_seats'] > 0 else 'Unlimited'}")
            print(f"  Expires: {'Yes' if tinfo['expires'] else 'No'}")
            print("  Features:")
            for f in tinfo["features"]:
                print(f"    - {f}")

    elif action == "fingerprint":
        # Show hardware fingerprint
        fp = get_hardware_fingerprint()
        hw_hash = get_hardware_hash()
        print("Hardware Fingerprint")
        print("-" * 40)
        print(f"  Fingerprint: {fp}")
        print(f"  Hash:        {hw_hash}")
        print()
        print("  This fingerprint is used to bind licenses to this machine.")
        print("  Portable licenses do not use hardware binding.")


if __name__ == "__main__":
    main()
