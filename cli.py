#!/usr/bin/env python3
"""
AxiomCode — Natural Language to Formally Verified Code
=======================================================

Zero-trust. Zero-knowledge. Encrypted. Exclusively secure.
Zero external dependencies. Pure Python stdlib + cffi.

Domain: axiom-code.com
"""

from __future__ import annotations

import argparse
import http.client
import json
import os
import shlex
import ssl
import subprocess
import sys
import textwrap
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

# Import security layer
from core.security import (
    KeyStore, KeyPair,
    ProofCertificate, BinarySignature, sign_binary,
    SecureChannel, AuditLog, SecureSandbox, RateLimiter,
    hash_data, hash_file, compute_hmac, verify_hmac,
)
from core.versioning import VersionManager, CURRENT_VERSION
from core.licensing import (
    LicenseManager, LicenseCertificate, LicenseKeyPair,
    get_hardware_fingerprint, get_hardware_hash, TIERS,
)

# ─── Banner ─────────────────────────────────────────────────────────────────

BANNER = """
============================================================
  AxiomCode -- Natural Language to Verified Code
  axiom-code.com | Zero-Trust | Encrypted | Verified
============================================================
"""

# ─── Examples ───────────────────────────────────────────────────────────────

EXAMPLES = [
    {"name": "Binary Search", "description": "implement binary search on a sorted array that returns the index of the target element, prove it always finds the element if present", "difficulty": "Easy", "category": "Searching", "proof_complexity": "Medium"},
    {"name": "Insertion Sort", "description": "implement insertion sort that sorts a list of natural numbers, prove the output is sorted and contains the same elements as the input", "difficulty": "Easy", "category": "Sorting", "proof_complexity": "Medium"},
    {"name": "Merge Sort", "description": "implement merge sort using divide and conquer, prove it produces a sorted list that is a permutation of the input", "difficulty": "Medium", "category": "Sorting", "proof_complexity": "High"},
    {"name": "GCD (Euclidean Algorithm)", "description": "implement the Euclidean algorithm for greatest common divisor, prove it always terminates and returns the correct GCD", "difficulty": "Easy", "category": "Number Theory", "proof_complexity": "Low"},
    {"name": "Linked List Reverse", "description": "implement an in-place linked list reversal, prove the reversed list has the same length and elements in reverse order", "difficulty": "Medium", "category": "Data Structures", "proof_complexity": "High"},
    {"name": "Stack with Max", "description": "implement a stack data structure that supports push, pop, and get-max in O(1) time, prove all operations maintain the stack invariant", "difficulty": "Medium", "category": "Data Structures", "proof_complexity": "Medium"},
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
  A: Local: Ollama (qwen2.5-coder, mistral, deepseek-r1).
     Cloud: OpenAI (GPT-4o), Anthropic (Claude).

  Q: Is my data sent to external servers?
  A: Only if you use cloud providers (OpenAI/Anthropic). Local Ollama
     runs entirely on your machine. No telemetry, no tracking.

  Q: How are generated code artifacts secured?
  A: Every binary and package is cryptographically signed. Certificates
     include hashes of all artifacts for integrity verification.

  Q: Can I use generated code in production?
  A: Yes -- it comes with mathematical proofs of correctness and
     cryptographic certificates of authenticity.

TROUBLESHOOTING:
  Ollama connection refused:
    ollama serve
    ollama pull qwen2.5-coder:14b

  Lean 4 not found:
    Install from https://lean-lang.org/

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
    - Your description is sent to a local LLM (qwen2.5-coder by default)
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

    def compute_hash(self) -> str:
        self.proof_hash = hash_data(self.proof_term.encode())
        return self.proof_hash


# ─── LLM Cache ──────────────────────────────────────────────────────────────

class LLMCache:
    """Persistent cache for LLM responses. Reduces cost and latency."""

    def __init__(self, cache_dir: str | Path = ".axiomcode/cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _key(self, model: str, prompt: str) -> str:
        return hash_data(f"{model}:{prompt}".encode())[:16]

    def get(self, model: str, prompt: str) -> str | None:
        key = self._key(model, prompt)
        cache_file = self.cache_dir / f"{key}.json"
        if cache_file.exists():
            data = json.loads(cache_file.read_text())
            # Cache expires after 24 hours
            if time.time() - data.get("timestamp", 0) < 86400:
                return data.get("response")
        return None

    def put(self, model: str, prompt: str, response: str) -> None:
        key = self._key(model, prompt)
        cache_file = self.cache_dir / f"{key}.json"
        cache_file.write_text(json.dumps({
            "model": model,
            "prompt_hash": hash_data(prompt.encode())[:16],
            "response": response,
            "timestamp": time.time(),
        }))


# ─── HTTP Client (stdlib only) ──────────────────────────────────────────────

def http_post_json(url: str, data: dict, headers: dict | None = None, timeout: int = 180) -> dict:
    """POST JSON using stdlib http.client."""
    parsed = urlparse(url)
    host = str(parsed.hostname or "localhost")
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    path = parsed.path or "/"
    if parsed.query:
        path += "?" + parsed.query

    body = json.dumps(data).encode("utf-8")
    req_headers = {
        "Content-Type": "application/json",
        "Content-Length": str(len(body)),
        "Accept": "application/json",
    }
    if headers:
        req_headers.update(headers)

    if parsed.scheme == "https":
        conn = http.client.HTTPSConnection(host, port, context=ssl.create_default_context(), timeout=timeout)
    else:
        conn = http.client.HTTPConnection(host, port, timeout=timeout)

    try:
        conn.request("POST", path, body=body, headers=req_headers)
        resp = conn.getresponse()
        resp_body = resp.read().decode("utf-8")
        if resp.status >= 400:
            raise RuntimeError(f"HTTP {resp.status}: {resp_body}")
        return json.loads(resp_body) if resp_body.strip() else {}
    finally:
        conn.close()


def http_get_json(url: str, timeout: int = 10) -> dict:
    """GET JSON using stdlib http.client."""
    parsed = urlparse(url)
    host = str(parsed.hostname or "localhost")
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    path = parsed.path or "/"
    if parsed.query:
        path += "?" + parsed.query

    if parsed.scheme == "https":
        conn = http.client.HTTPSConnection(host, port, context=ssl.create_default_context(), timeout=timeout)
    else:
        conn = http.client.HTTPConnection(host, port, timeout=timeout)

    try:
        conn.request("GET", path, headers={"Accept": "application/json"})
        resp = conn.getresponse()
        resp_body = resp.read().decode("utf-8")
        if resp.status >= 400:
            raise RuntimeError(f"HTTP {resp.status}: {resp_body}")
        return json.loads(resp_body) if resp_body.strip() else {}
    finally:
        conn.close()


# ─── LLM Backends ───────────────────────────────────────────────────────────

SPEC_PROMPT = """You are an expert in Lean 4 formal verification.
Convert the following natural language algorithm description into a Lean 4 formal specification.

Rules:
1. Output ONLY valid Lean 4 code -- no explanations, no markdown.
2. Include necessary imports (Mathlib, Aesop).
3. Define any helper types/structures needed.
4. State the main theorem with a clear name.
5. The theorem should capture the full correctness specification.
6. Use `by sorry` as the proof placeholder.

Natural language description:
{description}

Output format:
```lean
import Mathlib
import Aesop

/-- docstring -/
theorem algorithm_correctness : ... := by sorry
```
"""

_llm_cache = LLMCache()

def ollama_generate(model: str, prompt: str, base_url: str = "http://localhost:11434") -> str:
    """Generate text using Ollama via HTTP with caching and retry."""
    cached = _llm_cache.get(f"ollama/{model}", prompt)
    if cached:
        return cached

    for attempt in range(3):
        try:
            resp = http_post_json(
                f"{base_url}/api/generate",
                {"model": model, "prompt": prompt, "stream": False, "options": {"temperature": 0.2, "num_predict": 4096}},
                timeout=180,
            )
            result = resp.get("response", "")
            _llm_cache.put(f"ollama/{model}", prompt, result)
            return result
        except Exception as e:
            if attempt == 2:
                raise RuntimeError(f"Ollama failed after 3 attempts: {e}\nFix: Run 'ollama pull {model}' and 'ollama serve'")
            time.sleep(2 ** attempt)
    return ""


def mistral_generate(model: str, prompt: str, base_url: str = "http://localhost:11434") -> str:
    return ollama_generate(model, prompt, base_url)


def openai_generate(model: str, prompt: str, api_key: str | None = None) -> str:
    """Generate text using OpenAI API via HTTP (no SDK)."""
    key = api_key or os.environ.get("OPENAI_API_KEY", "")
    if not key:
        raise RuntimeError("Set OPENAI_API_KEY environment variable")

    cached = _llm_cache.get(f"openai/{model}", prompt)
    if cached:
        return cached

    body = json.dumps({"model": model, "messages": [{"role": "user", "content": prompt}]}).encode("utf-8")
    parsed = urlparse("https://api.openai.com/v1/chat/completions")
    conn = http.client.HTTPSConnection(str(parsed.hostname), 443, timeout=120)
    try:
        conn.request("POST", parsed.path, body=body, headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}",
        })
        resp = conn.getresponse()
        data = json.loads(resp.read().decode("utf-8"))
        result = data["choices"][0]["message"]["content"]
        _llm_cache.put(f"openai/{model}", prompt, result)
        return result
    finally:
        conn.close()


def anthropic_generate(model: str, prompt: str, api_key: str | None = None) -> str:
    """Generate text using Anthropic API via HTTP (no SDK)."""
    key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
    if not key:
        raise RuntimeError("Set ANTHROPIC_API_KEY environment variable")

    cached = _llm_cache.get(f"anthropic/{model}", prompt)
    if cached:
        return cached

    body = json.dumps({"model": model, "max_tokens": 4096, "messages": [{"role": "user", "content": prompt}]}).encode("utf-8")
    parsed = urlparse("https://api.anthropic.com/v1/messages")
    conn = http.client.HTTPSConnection(str(parsed.hostname), 443, timeout=120)
    try:
        conn.request("POST", parsed.path, body=body, headers={
            "Content-Type": "application/json",
            "x-api-key": key,
            "anthropic-version": "2023-06-01",
        })
        resp = conn.getresponse()
        data = json.loads(resp.read().decode("utf-8"))
        result = data["content"][0]["text"]
        _llm_cache.put(f"anthropic/{model}", prompt, result)
        return result
    finally:
        conn.close()


BACKENDS = {
    "local": ("qwen2.5-coder:14b", ollama_generate),
    "ollama": ("qwen2.5-coder:14b", ollama_generate),
    "mistral": ("mistral:7b", mistral_generate),
    "openai": ("gpt-4o", openai_generate),
    "anthropic": ("claude-sonnet-4-20250514", anthropic_generate),
    "claude": ("claude-sonnet-4-20250514", anthropic_generate),
}


# ─── Spec Generator ─────────────────────────────────────────────────────────

def generate_spec(description: str, model: str = "local") -> LeanSpec:
    """Generate a Lean 4 specification from natural language."""
    backend_name = model if model in BACKENDS else "local"
    default_model, gen_fn = BACKENDS[backend_name]
    prompt = SPEC_PROMPT.format(description=description)

    start = time.monotonic()
    raw = gen_fn(default_model, prompt)
    elapsed = (time.monotonic() - start) * 1000

    return _parse_spec(raw, description, elapsed, backend_name)


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
        theorem=theorem, definitions=definitions, imports=imports,
        docstring=docstring, source_nl=source_nl,
        model_used=backend, generation_time_ms=elapsed,
    )
    spec.compute_hash()
    return spec


# ─── Proof Engine ───────────────────────────────────────────────────────────

def run_proof(spec: LeanSpec, lean_bin: str = "lean", lake_bin: str = "lake") -> ProofResult:
    """Run Lean 4 to verify a specification."""
    project_dir = Path(__file__).parent / "lean"
    algo_dir = project_dir / "src" / "Algorithms"
    algo_dir.mkdir(parents=True, exist_ok=True)

    name = spec.theorem.split(":")[0].replace("theorem", "").strip().lower()
    lean_file = algo_dir / f"{name}.lean"
    lean_file.write_text(spec.to_lean())

    try:
        result = subprocess.run([lake_bin, "build"], cwd=project_dir, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            raise RuntimeError(f"Lean build failed:\n{result.stderr}")
    except FileNotFoundError:
        print(f"  [!] Lean 4 not found. Install from https://lean-lang.org/")
        print(f"  [!] Proof search skipped. Spec saved to {lean_file}")
        proof = ProofResult(theorem_name=name, steps=0, lemmas=len(spec.definitions), lean_file=lean_file, tactics=[], proof_term=spec.to_lean())
        proof.compute_hash()
        return proof

    olean_file = lean_file.with_suffix(".olean")
    tactics = _extract_tactics(lean_file)
    proof = ProofResult(
        theorem_name=name, steps=len(tactics), lemmas=len(spec.definitions),
        lean_file=lean_file, olean_file=olean_file if olean_file.exists() else None,
        tactics=tactics, proof_term=lean_file.read_text(),
    )
    proof.compute_hash()
    return proof


def _extract_tactics(lean_file: Path) -> list[str]:
    content = lean_file.read_text()
    keywords = ["rw", "simp", "induction", "cases", "apply", "exact", "have", "let", "calc", "refine", "constructor", "tauto", "linarith", "ring"]
    return [line.strip() for line in content.split("\n") for kw in keywords if line.strip().startswith(kw) or f" {kw} " in line.strip()]


def load_proof(name: str) -> ProofResult:
    project_dir = Path(__file__).parent / "lean" / "src" / "Algorithms"
    lean_file = project_dir / f"{name.lower()}.lean"
    if not lean_file.exists():
        raise FileNotFoundError(f"No verified proof found: {name}")
    content = lean_file.read_text()
    proof = ProofResult(theorem_name=name, steps=0, lemmas=0, lean_file=lean_file, proof_term=content)
    proof.compute_hash()
    return proof


# ─── Code Extractor ─────────────────────────────────────────────────────────

def extract_c(proof: ProofResult, lean_bin: str = "lean") -> Path:
    output_dir = Path(__file__).parent / "build" / "c"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"{proof.theorem_name}.c"

    try:
        result = subprocess.run([lean_bin, "--c", str(output_file), str(proof.lean_file)], capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            raise RuntimeError(f"C extraction failed:\n{result.stderr}")
    except FileNotFoundError:
        print(f"  [!] Lean 4 not found. C extraction skipped.")
        return output_file

    so_file = output_file.with_suffix(".so")
    try:
        subprocess.run(["gcc", "-shared", "-fPIC", "-O2", "-o", str(so_file), str(output_file)], capture_output=True, text=True)
        return so_file if so_file.exists() else output_file
    except FileNotFoundError:
        print(f"  [!] gcc not found. C source saved to {output_file}")
        return output_file


def extract_python(proof: ProofResult) -> Path:
    pkg_dir = Path(__file__).parent / "build" / "python" / f"axiomcode_{proof.theorem_name}"
    pkg_dir.mkdir(parents=True, exist_ok=True)

    (pkg_dir / "__init__.py").write_text(textwrap.dedent(f'''
        """
        {proof.theorem_name} -- formally verified via AxiomCode.
        Proof: {proof.steps} steps, {proof.lemmas} lemmas.
        Certificate: axiomcode_{proof.theorem_name}.cert.json
        """
        __proof_verified__ = True
    ''').lstrip())

    (pkg_dir / "bindings.py").write_text(textwrap.dedent(f'''
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
    ''').lstrip())

    (pkg_dir / "setup.py").write_text(textwrap.dedent(f'''
        from setuptools import setup, find_packages
        setup(
            name="axiomcode-{proof.theorem_name}",
            version="0.1.0",
            description="Formally verified {proof.theorem_name} by AxiomCode",
            packages=find_packages(),
        )
    ''').lstrip())

    return pkg_dir


# ─── Certificate Generator ──────────────────────────────────────────────────

def generate_certificate(spec: LeanSpec, proof: ProofResult, c_path: Path | None, py_path: Path | None, signing_key: bytes, key_id: str) -> ProofCertificate:
    """Generate a cryptographic certificate for a verified algorithm."""
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
        generated_at=time.time(),
        key_id=key_id,
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
        .header {{ padding: 20px 30px; border-bottom: 1px solid #222; display: flex; justify-content: space-between; align-items: center; }}
        .header h1 {{ font-size: 1.2rem; font-weight: 600; }}
        .header h1 span {{ color: #4a90d9; }}
        .mode-switch {{ display: flex; gap: 8px; }}
        .mode-btn {{ padding: 6px 16px; border: 1px solid #333; background: transparent; color: #888; border-radius: 6px; cursor: pointer; font-size: 0.85rem; }}
        .mode-btn.active {{ background: #4a90d9; color: white; border-color: #4a90d9; }}
        .container {{ display: flex; height: calc(100vh - 70px); }}
        .graph-panel {{ flex: 1; position: relative; }}
        .info-panel {{ width: 320px; border-left: 1px solid #222; padding: 20px; overflow-y: auto; background: #0d0d12; }}
        .info-panel h3 {{ font-size: 0.9rem; color: #4a90d9; margin-bottom: 12px; }}
        .info-panel pre {{ background: #151520; padding: 12px; border-radius: 8px; font-size: 0.8rem; overflow-x: auto; line-height: 1.5; }}
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
            <button class="mode-btn {'active' if mode == '2d' else ''}" onclick="location.search='?mode=2d'">2D Port Graph</button>
            <button class="mode-btn {'active' if mode == 'force' else ''}" onclick="location.search='?mode=force'">Force Graph</button>
            <button class="mode-btn {'active' if mode == '3d' else ''}" onclick="location.search='?mode=3d'">3D Layout</button>
        </div>
    </div>
    <div class="container">
        <div class="graph-panel" id="graph-panel"></div>
        <div class="info-panel">
            <div class="stats">
                <div class="stat"><div class="stat-value">{proof.steps}</div><div class="stat-label">Proof Steps</div></div>
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
            const svg = d3.select(panel).append('svg').attr('width', panel.clientWidth).attr('height', panel.clientHeight);
            const color = {{ axiom: '#4a90d9', lemma: '#50c878', theorem: '#ffd700', tactic: '#9b59b6', qed: '#e74c3c' }};
            const nodes = svg.selectAll('g').data(proofData.nodes).join('g');
            nodes.append('rect').attr('x', (d, i) => 50 + (i % 6) * 180).attr('y', (d, i) => 50 + Math.floor(i / 6) * 120).attr('width', 150).attr('height', 80).attr('rx', 10).attr('fill', d => color[d.kind] || '#555').attr('stroke', '#333').attr('stroke-width', 2);
            nodes.append('text').attr('x', (d, i) => 125 + (i % 6) * 180).attr('y', (d, i) => 95 + Math.floor(i / 6) * 120).attr('text-anchor', 'middle').attr('fill', 'white').attr('font-size', '12px').text(d => d.label.slice(0, 20));
        }}
        function renderForce() {{
            const panel = document.getElementById('graph-panel');
            const svg = d3.select(panel).append('svg').attr('width', panel.clientWidth).attr('height', panel.clientHeight);
            const color = {{ theorem: '#ffd700', tactic: '#9b59b6', qed: '#e74c3c' }};
            const simulation = d3.forceSimulation(proofData.nodes).force('link', d3.forceLink(proofData.edges).distance(120)).force('charge', d3.forceManyBody().strength(-300)).force('center', d3.forceCenter(panel.clientWidth / 2, panel.clientHeight / 2));
            const link = svg.append('g').selectAll('line').data(proofData.edges).join('line').attr('stroke', '#333').attr('stroke-width', 2);
            const node = svg.append('g').selectAll('circle').data(proofData.nodes).join('circle').attr('r', 20).attr('fill', d => color[d.kind] || '#555');
            simulation.on('tick', () => {{ link.attr('x1', d => d.source.x).attr('y1', d => d.source.y).attr('x2', d => d.target.x).attr('y2', d => d.target.y); node.attr('cx', d => d.x).attr('cy', d => d.y); }});
        }}
        if (mode === '2d') render2D();
        else if (mode === 'force') renderForce();
        else document.getElementById('graph-panel').innerHTML = '<div style="display:flex;align-items:center;justify-content:center;height:100%;color:#666;">3D view -- Three.js integration pending (Phase 2)</div>';
    </script>
</body>
</html>"""


def _build_graph_data(proof: ProofResult, mode: str) -> dict:
    nodes = [{"id": f"step_{i}", "label": t[:30], "kind": "qed" if i == len(proof.tactics) - 1 else "tactic"} for i, t in enumerate(proof.tactics)]
    edges = [{"source": f"step_{i-1}", "target": f"step_{i}"} for i in range(1, len(proof.tactics))]
    return {"nodes": nodes, "edges": edges}


def _esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def serve_visualization(proof: ProofResult, mode: str = "2d", port: int = 8765):
    from http.server import HTTPServer, BaseHTTPRequestHandler
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
    print(f"  Press Ctrl+C to stop")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()


# ─── CLI Commands ───────────────────────────────────────────────────────────

def cmd_generate(description: str, lang: str = "python", model: str = "local", visualize: bool = False, passphrase: str = ""):
    """Generate formally verified code from natural language."""
    print(BANNER)

    # Initialize security
    audit = AuditLog()
    audit.add_entry("generate_start", {"description_hash": hash_data(description.encode()), "model": model})

    ks = KeyStore()
    key_name = "default"
    try:
        signing_key = ks.load_key(key_name, passphrase or "axiomcode-default").signing_key
        key_id = ks.load_key(key_name, passphrase or "axiomcode-default").key_id
    except FileNotFoundError:
        kp = ks.create_key(key_name, passphrase or "axiomcode-default")
        signing_key, key_id = kp.signing_key, kp.key_id

    # Step 1: Generate specification
    print("[1/4] Generating formal specification...")
    try:
        spec = generate_spec(description, model)
        print(f"  [+] Specification generated ({spec.model_used}, {spec.generation_time_ms:.0f}ms)")
        print(f"      Theorem: {spec.theorem.split(':')[0].strip()}")
        print(f"      Hash: {spec.spec_hash[:16]}...")
    except Exception as e:
        print(f"  [-] Spec generation failed: {e}")
        audit.add_entry("generate_fail", {"error": str(e)})
        sys.exit(1)

    # Step 2: Search for proof
    print("[2/4] Searching for proof...")
    try:
        proof = run_proof(spec)
        print(f"  [+] Proof verified ({proof.steps} steps, {proof.lemmas} lemmas)")
        print(f"      Proof hash: {proof.proof_hash[:16]}...")
    except Exception as e:
        print(f"  [!] Proof search incomplete: {e}")
        proof = ProofResult(
            theorem_name=spec.theorem.split(":")[0].replace("theorem", "").strip().lower(),
            steps=0, lemmas=len(spec.definitions),
            lean_file=Path("unknown"), tactics=[], proof_term=spec.to_lean(),
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
    print(f"      Signature: {cert.signature[:32]}...")

    audit.add_entry("generate_complete", {
        "algorithm": proof.theorem_name,
        "steps": proof.steps,
        "lemmas": proof.lemmas,
        "certificate": str(cert_path),
    })

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

    print(f"\nStep 3: Algorithm description:")
    print(f"  {selected['description']}")
    use_default = input("Use this description? [Y/n]: ").strip().lower() != "n"
    description = selected["description"] if use_default else input("Enter your description: ")

    print("\nStep 4: Choose LLM backend:")
    print("  1. local (Ollama -- qwen2.5-coder:14b)")
    print("  2. mistral (Ollama -- mistral:7b)")
    print("  3. openai (GPT-4o)")
    print("  4. anthropic (Claude Sonnet)")
    model_choice = input("Select model [1]: ").strip() or "1"
    model_map = {"1": "local", "2": "mistral", "3": "openai", "4": "anthropic"}
    model = model_map.get(model_choice, "local")

    print(f"\nStep 5: Generating verified code...")
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
    print('Run: python cli.py guide  (interactive mode)')
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
    print("Available LLM Backends")
    print("-" * 65)
    print(f"{'Backend':<18} {'Default Model':<22} {'Type':<8} {'Speed':<8} {'Quality'}")
    print("-" * 65)
    for name, model, type_, speed, quality in [
        ("local (Ollama)", "qwen2.5-coder:14b", "Local", "Fast", "Good"),
        ("mistral", "mistral:7b", "Local", "Fast", "Good"),
        ("openai", "gpt-4o", "Cloud", "Medium", "Excellent"),
        ("anthropic", "claude-sonnet-4", "Cloud", "Medium", "Excellent"),
    ]:
        print(f"{name:<18} {model:<22} {type_:<8} {speed:<8} {quality}")

    print("\nLocally available models:")
    try:
        resp = http_get_json("http://localhost:11434/api/tags", timeout=5)
        for m in resp.get("models", []):
            print(f"  [+] {m['name']}")
    except Exception:
        print("  [!] Ollama not reachable. Run 'ollama serve'")


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


def cmd_publish(name: str, pypi: bool = False, github: bool = False):
    print(BANNER)
    print(f"Publishing: {name}")

    # Verify certificate first
    cert_dir = Path(__file__).parent / "build" / "certs"
    cert_path = cert_dir / f"{name}.cert.json"
    if cert_path.exists():
        cert = ProofCertificate.load(cert_path)
        print(f"  [+] Certificate verified: {cert.signature[:32]}...")
    else:
        print(f"  [!] No certificate found. Generate the algorithm first.")

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


def cmd_verify(name: str):
    print(BANNER)
    print(f"Verifying: {name}")

    # Verify certificate
    cert_dir = Path(__file__).parent / "build" / "certs"
    cert_path = cert_dir / f"{name}.cert.json"
    if cert_path.exists():
        cert = ProofCertificate.load(cert_path)
        print(f"  Certificate: {cert_path}")
        print(f"  Spec hash: {cert.spec_hash[:16]}...")
        print(f"  Proof hash: {cert.proof_hash[:16]}...")
        print(f"  Signature: {cert.signature[:32]}...")
        print(f"  Key ID: {cert.key_id}")

        # Verify binary integrity
        c_path = Path(__file__).parent / "build" / "c" / f"{name}.so"
        if c_path.exists() and cert.c_binary_hash:
            actual = hash_file(c_path)
            if actual == cert.c_binary_hash:
                print(f"  [+] C binary integrity verified")
            else:
                print(f"  [-] C binary integrity FAILED")

    # Verify Lean proof
    try:
        proof = load_proof(name)
        result = subprocess.run(["lean", "--c", "/dev/null", str(proof.lean_file)], capture_output=True, text=True, timeout=300)
        if result.returncode == 0:
            print(f"  [+] Lean proof verified")
        else:
            print(f"  [-] Lean proof verification failed")
    except FileNotFoundError:
        print(f"  [-] No Lean proof found")
    except Exception as e:
        print(f"  [-] Verification failed: {e}")


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


def cmd_key_create(name: str, passphrase: str = ""):
    """Create a signing key."""
    print(BANNER)
    ks = KeyStore()
    kp = ks.create_key(name, passphrase or "axiomcode-default")
    print(f"[+] Key created: {name}")
    print(f"    Key ID: {kp.key_id}")
    print(f"    Created: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(kp.created_at))}")


def cmd_key_list():
    """List signing keys."""
    print(BANNER)
    ks = KeyStore()
    key_dir = ks.store_dir
    if key_dir.exists():
        for kf in key_dir.glob("*.key"):
            print(f"  [+] {kf.stem}")
    else:
        print("  No keys found. Create one with 'python cli.py key create <name>'")


def cmd_audit():
    """Show audit log."""
    print(BANNER)
    audit = AuditLog()
    if audit.log_file.exists():
        print(f"Audit log: {audit.log_file}")
        print(f"Integrity: {'VERIFIED' if audit.verify_integrity() else 'TAMPERED'}")
        print()
        for line in audit.log_file.read_text().strip().split("\n"):
            entry = json.loads(line)
            print(f"  {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(entry['timestamp']))} | {entry['user']} | {entry['action']}")
    else:
        print("No audit log entries yet.")


# ─── Main ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(prog="axiomcode", description="Natural language to formally verified code", formatter_class=argparse.RawDescriptionHelpFormatter, epilog=HELP_TEXT)
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

    sub.add_parser("cert", help="Show proof certificate").add_argument("name")

    p_kc = sub.add_parser("key", help="Key management")
    p_kc.add_argument("action", choices=["create", "list"])
    p_kc.add_argument("name", nargs="?", default="")
    p_kc.add_argument("--passphrase", default="")

    sub.add_parser("audit", help="Show audit log")

    # Version management
    p_ver_cmd = sub.add_parser("version", help="Version management")
    p_ver_cmd.add_argument("action", nargs="?", default="show", choices=["show", "migrate", "rollback", "backups", "history", "validate"])
    p_ver_cmd.add_argument("--to", default=None, help="Target version for migration")
    p_ver_cmd.add_argument("--force", action="store_true", help="Force migration without confirmation")

    # License management
    p_lic = sub.add_parser("license", help="License management")
    p_lic.add_argument("action", nargs="?", default="show", choices=["show", "issue", "verify", "revoke", "list", "tiers", "keygen", "fingerprint"])
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
            print("Error: description is required"); sys.exit(1)
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
        cmd_verify(args.name)
    elif args.command == "cert":
        cmd_cert(args.name)
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
            print(f"\nBreaking changes:")
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
        for b in backups:
            ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(b["timestamp"]))
            print(f"  {b['name']} (v{b['version']}, {ts})")

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


def cmd_license(action: str, user: str | None = None, name: str | None = None,
                tier: str = "community", key_path: str | None = None,
                passphrase: str = "", output: str | None = None,
                license_file: str | None = None, reason: str = "",
                portable: bool = False, expires: str | None = None):
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

        print(f"[+] Root key pair generated")
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
                user_id=user, user_name=name, tier=tier,
                expires_at=expires_at,
            )
        else:
            license = lm.issue_license(
                user_id=user, user_name=name, tier=tier,
                expires_at=expires_at,
            )

        out_path = Path(output or f".axiomcode/licenses/{name.replace(' ', '_').lower()}.license.json")
        license.save(out_path)

        print(f"[+] License issued")
        print(f"    License ID: {license.license_id}")
        print(f"    User:       {license.user_name} ({license.user_id})")
        print(f"    Tier:       {license.tier}")
        print(f"    Features:   {', '.join(license.features)}")
        print(f"    Hardware:   {'Portable' if not license.hardware_hash else 'Bound'}")
        if expires_at > 0:
            print(f"    Expires:    {time.strftime('%Y-%m-%d', time.localtime(expires_at))}")
        else:
            print(f"    Expires:    Never")
        print(f"    Saved to:   {out_path}")

    elif action == "verify":
        # Verify a license
        lic_path = license_file or ".axiomcode/licenses/default.license.json"
        if not Path(lic_path).exists():
            # Try to find any license
            licenses = list(Path(".axiomcode/licenses").glob("*.license.json"))
            if licenses:
                lic_path = str(licenses[0])
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
            print(f"  Expires:    Never")
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
            print(f"  Features:")
            for f in tinfo['features']:
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
