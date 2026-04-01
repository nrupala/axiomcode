# AxiomCode — Project Plan

> **Domain:** axiom-code.com  
> **Mission:** Democratize formally verified software through natural language input.  
> **Current Version:** 0.1.0  
> **Status:** Phase 1 Complete

---

## Vision

A system where users describe algorithms in natural language, and the system generates **mathematically proven-correct code** (Python + C binaries) with **displayable, interactive geometric proof visualizations** and **cryptographic certificates of authenticity**.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     USER INTERFACE (CLI)                     │
│   Natural Language Input → Language Selection → Output       │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                 LLM SPECIFICATION ENGINE                     │
│   NL → Formal Specification (Lean 4 theorem statements)      │
│   Backends: Ollama (local), Mistral, OpenAI, Anthropic       │
│   Features: Caching, retry, rate limiting                    │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│              PROOF GENERATION ENGINE (Lean 4)               │
│   Pantograph (M2M API) + Goedel-Prover + Custom Tactics     │
│   Iterative proof search with self-correction                │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│               SECURITY & CERTIFICATION LAYER                 │
│   ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐   │
│   │ Encrypted   │  │ Proof        │  │ Tamper-Evident  │   │
│   │ Key Store   │  │ Certificates │  │ Audit Log       │   │
│   └─────────────┘  └──────────────┘  └─────────────────┘   │
│   ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐   │
│   │ Binary      │  │ Secure       │  │ Rate Limiter    │   │
│   │ Signing     │  │ Sandbox      │  │                 │   │
│   └─────────────┘  └──────────────┘  └─────────────────┘   │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│               PROOF VISUALIZATION ENGINE                     │
│   2D Port Graph | Force-Directed Graph | 3D Spatial Layout   │
│   Self-contained HTML with D3.js, served via stdlib HTTP     │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│               CODE EXTRACTION & COMPILATION                  │
│   C Binary: lean --c + gcc → .so/.dll                       │
│   Python: cffi bindings → pip-installable wheel             │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│               VERSION MANAGEMENT & PERSISTENCE               │
│   Upgrade: v1 → v2 → vN with automatic data migration       │
│   Downgrade: vN → v2 → v1 with data preservation            │
│   Backup: Automatic before every migration                  │
│   Rollback: One-command restore to previous state           │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                 BINARY PUBLISHING LAYER                      │
│   PyPI upload (Python wheel) + GitHub Releases (C binary)   │
└─────────────────────────────────────────────────────────────┘
```

---

## Technology Stack

| Component | Choice | Rationale |
|-----------|--------|-----------|
| Proof Assistant | **Lean 4** | Fast, built-in C compiler, active AI research |
| LLM Interface | **Pantograph** | Purpose-built M2M Lean 4 API |
| Automated Proving | **Goedel-Prover** | Open-source ATP, state-of-the-art for Lean 4 |
| LLM Backends | **Ollama, OpenAI, Anthropic** | Local + cloud, zero SDKs |
| Visualization | **D3.js (HTML)** | Interactive, browser-based, no server |
| C Compilation | **Lean 4 `lean --c`** | Native, no extraction layer |
| Python Bindings | **cffi** | Only external dependency |
| Security | **Python stdlib** | hashlib, hmac, secrets, ssl |
| HTTP | **http.client** | Zero dependency HTTP |
| CLI | **argparse** | Stdlib, no typer/rich needed |

---

## Phase Breakdown

### Phase 1: MVP — Complete ✅

**Delivered:**
- [x] NL → Lean 4 spec generation (4 LLM backends, zero SDKs)
- [x] Proof engine with Pantograph integration
- [x] C binary extraction via `lean --c`
- [x] Python package generation with cffi bindings
- [x] Cryptographic proof certificates (HMAC-signed)
- [x] Zero-trust security model (encrypted keys, audit log, sandbox)
- [x] Interactive proof visualization (2D/force-directed/3D)
- [x] LLM caching for reduced latency and cost
- [x] Rate limiting for API abuse prevention
- [x] 14 CLI commands (generate, guide, examples, help, walkthrough, models, visualize, publish, verify, cert, key create, key list, audit, version)
- [x] Zero external dependencies (pure stdlib + cffi)
- [x] Version management with upgrade/downgrade/rollback
- [x] Automatic backup before migrations
- [x] Tamper-evident audit log
- [x] 28 tests passing
- [x] Comprehensive documentation (FEATURES.md, TEST_PLAN.md, QUICKSTART.md, ARCHITECTURE.md)

### Phase 2: Domain-Specific Libraries (Months 3-6)

- [ ] Verified numerical methods library (matrix ops, integration)
- [ ] Verified cryptography primitives (SHA-256, AES structure)
- [ ] Verified data structures (trees, hash maps, graphs)
- [ ] 3D proof visualization with Three.js
- [ ] Domain-specific prompt templates
- [ ] Pre-built proof tactics per domain

### Phase 3: Scale (Months 6-12)

- [ ] Coq backend support
- [ ] Isabelle/HOL backend support
- [ ] Custom proof automation tactics (Z3/SMT integration)
- [ ] Graph algorithms verification
- [ ] Dynamic programming verification
- [ ] Concurrent algorithm verification
- [ ] Performance benchmarking suite

### Phase 4: Enterprise (Months 12+)

- [ ] Multi-user key management
- [ ] Team certificate verification
- [ ] Compliance reporting
- [ ] CI/CD integration (GitHub Actions)
- [ ] Web dashboard
- [ ] API server mode

---

## Project Structure

```
axiomcode/
├── cli.py                      # Entire system (~1200 lines, zero external deps)
├── core/
│   ├── __init__.py             # Security re-exports
│   ├── security.py             # Encryption, certs, audit, sandbox, rate limiting
│   └── versioning.py           # Version management, migration, backup, rollback
├── visualize/
│   └── __init__.py             # Visualization re-exports
├── publish/
│   └── __init__.py             # Publish re-exports
├── lean/
│   ├── lakefile.lean           # Lean 4 Lake project config
│   └── src/
│       ├── Spec.lean           # Core specification definitions
│       ├── Tactics.lean        # Custom proof tactics
│       └── Algorithms/
│           └── insertion_sort.lean  # Example verified algorithm
├── tests/
│   └── test_core.py            # 28 tests passing
├── docs/
│   ├── QUICKSTART.md           # 5-minute quickstart
│   ├── ARCHITECTURE.md         # Architecture diagrams and flowcharts
│   └── generate_diagrams.py    # Mermaid diagram generator
├── examples/
│   ├── 01_binary_search.py     # Binary search example
│   └── 02_gcd.py               # GCD example
├── FEATURES.md                 # Comprehensive features and qualities
├── TEST_PLAN.md                # Detailed test plan
├── PLAN.md                     # This file
├── README.md                   # Project overview
├── pyproject.toml              # Package config (1 dep: cffi)
└── .gitignore                  # Excludes keys, cache, build
```

---

## Key References

- **Pantograph**: https://github.com/stanford-centaur/PyPantograph
- **Goedel-Prover**: https://github.com/Goedel-LM/Goedel-Prover
- **Goedel-Code-Prover**: https://github.com/goedelcodeprover/Goedel-Code-Prover
- **Incredible Proof Machine**: https://incredible.pm/
- **Lean 4**: https://github.com/leanprover/lean4
- **GraphGPU**: https://github.com/drkameleon/GraphGPU

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 0.1.0 | 2026-03-31 | Initial release — all Phase 1 features |
