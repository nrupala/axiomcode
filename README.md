# AxiomCode

> **Natural Language to Formally Verified Code**  
> **Domain:** axiom-code.com  
> **Version:** 0.1.0  
> **License:** MIT  
> **Dependencies:** Zero (pure Python stdlib + cffi)

[![Tests](https://github.com/nrupala/axiomcode/actions/workflows/tests.yml/badge.svg)](https://github.com/nrupala/axiomcode/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

---

## What Is AxiomCode?

AxiomCode converts **natural language descriptions** of algorithms into **mathematically proven-correct code** in Python and C. Every generated artifact comes with a cryptographic certificate of verification that can be independently audited.

```
Natural Language → Lean 4 Spec → Formal Proof → C Binary → Python Package
     (you describe)   (LLM)      (Lean 4)     (compiled)   (cffi binding)
```

## Why AxiomCode?

| Feature | AxiomCode | Copilot/Cursor | Traditional Verification |
|---------|-----------|----------------|------------------------|
| Correctness guarantee | **Mathematical proof** | Probabilistic guess | Manual (expert-only) |
| Learning curve | **Plain English** | Plain English | Years of expertise |
| Dependencies | **Zero** | Hundreds | Many |
| Security | **Zero-trust, signed** | Trust the model | Varies |
| Audit trail | **Tamper-evident log** | None | Manual |
| Certificates | **Cryptographic** | None | Paper-based |

## Quick Start

### Install

```bash
git clone https://github.com/nrupala/axiomcode.git
cd axiomcode
pip install -e ".[dev]"
```

### Generate Your First Verified Algorithm

```bash
# Quick generate
python cli.py "implement binary search on a sorted array"

# Interactive guided mode
python cli.py guide

# Browse examples
python cli.py examples
```

### View the Proof

```bash
# 2D port graph view
python cli.py visualize binary_search --mode 2d

# Force-directed graph
python cli.py visualize binary_search --mode force

# 3D spatial layout
python cli.py visualize binary_search --mode 3d
```

### Manage Licenses

```bash
# Generate root key pair (do this ONCE)
python cli.py license keygen

# Issue a license
python cli.py license issue --user user@example.com --name "User Name" --tier pro

# Verify a license
python cli.py license verify --license-file user_name.license.json

# Show available tiers
python cli.py license tiers
```

### Version Management

```bash
# Show current version
python cli.py version show

# Validate data integrity
python cli.py version validate

# View migration history
python cli.py version history
```

## Commands

| Command | Description |
|---------|-------------|
| `python cli.py "description"` | Generate verified code from NL |
| `python cli.py guide` | Interactive guided mode |
| `python cli.py examples` | Browse built-in examples |
| `python cli.py help` | Show full help and FAQ |
| `python cli.py walkthrough` | Step-by-step tutorial |
| `python cli.py models` | List available LLM backends |
| `python cli.py visualize <name>` | View proof visualization |
| `python cli.py publish <name>` | Publish to PyPI/GitHub |
| `python cli.py verify <name>` | Independently verify a proof |
| `python cli.py cert <name>` | Show proof certificate |
| `python cli.py key create <name>` | Create a signing key |
| `python cli.py key list` | List signing keys |
| `python cli.py audit` | Show audit log |
| `python cli.py version` | Version management |
| `python cli.py license` | License management |

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
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│              PROOF GENERATION ENGINE (Lean 4)               │
│   Pantograph (M2M API) + Goedel-Prover + Custom Tactics     │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│               SECURITY & CERTIFICATION LAYER                 │
│   Encrypted Key Store | Proof Certificates | Audit Log       │
│   Binary Signing | Secure Sandbox | Rate Limiter            │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│               PROOF VISUALIZATION ENGINE                     │
│   2D Port Graph | Force-Directed Graph | 3D Spatial Layout   │
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
│   Upgrade/Downgrade | Backup | Rollback | Data Integrity     │
└─────────────────────────────────────────────────────────────┘
```

## Security Model

- **Zero-trust**: Every output is independently verifiable
- **Zero-knowledge**: LLM prompts never contain sensitive data
- **Encrypted**: All artifacts are cryptographically signed
- **Auditable**: Tamper-evident audit log for compliance
- **No telemetry**: Zero data collection, zero tracking

## License Tiers

| Tier | Price | Features |
|------|-------|----------|
| **Community** | Free | Basic algorithms, 2D visualization, Local LLM only |
| **Pro** | $49/month | All algorithms, 3D visualization, Cloud LLMs, Publishing, Certificates |
| **Enterprise** | Custom | Everything, Multi-user, Compliance, Support, Custom algorithms |

## Documentation

- [FEATURES.md](FEATURES.md) — Comprehensive features and qualities
- [TEST_PLAN.md](TEST_PLAN.md) — Detailed test plan
- [PLAN.md](PLAN.md) — Project roadmap
- [docs/QUICKSTART.md](docs/QUICKSTART.md) — 5-minute quickstart
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — Architecture diagrams

## Development

```bash
# Run tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=cli --cov=core --cov-report=term-missing

# Lint
python -m ruff check .

# Type check
python -m mypy cli.py core/
```

## Requirements

- Python 3.10+
- cffi (only external dependency)
- Ollama (for local LLM) — optional
- Lean 4 (for proof verification) — optional

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

MIT License — see [LICENSE](LICENSE) file for details.

## Contact

- **Website:** [axiom-code.com](https://axiom-code.com)
- **GitHub:** [github.com/nrupala/axiomcode](https://github.com/nrupala/axiomcode)
- **Pages:** [nrupala.github.io/axiomcode](https://nrupala.github.io/axiomcode)
