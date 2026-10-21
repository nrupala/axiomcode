# AxiomCode — Architecture & Flowcharts

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                            USER INTERFACE                                │
│  ┌───────────┐  ┌────────────┐  ┌──────────┐  ┌────────────────────┐   │
│  │ CLI       │  │ API Service│  │ Guide    │  │ Visualizer         │   │
│  │ (argparse)│  │ (FastAPI)  │  │ Mode     │  │ (D3.js)            │   │
│  └─────┬─────┘  └─────┬─────┘  └────┬─────┘  └─────────┬──────────┘   │
│        └──────────────┴─────────────┴───────────────────┘              │
│                              │                                          │
└──────────────────────────────┼──────────────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────────────┐
│                         CORE ENGINE                                      │
│                                                                          │
│  ┌────────────────────┐    ┌────────────────────┐                       │
│  │  Spec Generator    │───▶│  Proof Engine      │                       │
│  │                    │    │                    │                       │
│  │  NL → Lean 4       │    │  Pantograph +      │                       │
│  │  • Ollama (local)  │    │  Goedel-Prover     │                       │
│  │  • Mistral         │    │  Lean 4 compiler   │                       │
│  │  • OpenAI          │    │  Custom tactics    │                       │
│  │  • Anthropic       │    │                    │                       │
│  └────────────────────┘    └─────────┬──────────┘                       │
│                                      │                                   │
│                              ┌───────▼──────────┐                       │
│                              │  Code Extractor   │                       │
│                              │                   │                       │
│                              │  lean --c → .so   │                       │
│                              │  cffi → .whl      │                       │
│                              └───────┬───────────┘                       │
│                                      │                                   │
│                              ┌───────▼──────────┐                       │
│                              │  Verifier         │                       │
│                              │                   │                       │
│                              │  Independent      │                       │
│                              │  proof check      │                       │
│                              └───────────────────┘                       │
└──────────────────────────────────────┬───────────────────────────────────┘
                                       │
┌──────────────────────────────────────▼───────────────────────────────────┐
│                          OUTPUT LAYER                                     │
│                                                                           │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────────────────┐  │
│  │ C Binary     │  │ Python Wheel │  │ Proof Visualization (Web)     │  │
│  │ (.so/.dll)   │  │ (.whl)       │  │ • 2D Port Graph               │  │
│  │              │  │              │  │ • Force-Directed Graph        │  │
│  │ Fast         │  │ Easy import  │  │ • 3D Spatial Layout           │  │
│  └──────────────┘  └──────────────┘  └───────────────────────────────┘  │
│                                                                           │
│  ┌──────────────┐  ┌──────────────┐                                      │
│  │ PyPI Publish │  │ GitHub Rel.  │                                      │
│  │ twine upload │  │ gh release   │                                      │
│  └──────────────┘  └──────────────┘                                      │
└───────────────────────────────────────────────────────────────────────────┘
```

## Data Flow: NL → Verified Code

```
User Input                    LLM Backend              Lean 4 Engine
    │                             │                         │
    │  "implement binary          │                         │
    │   search on sorted          │                         │
    │   array"                    │                         │
    │────────────────────────────▶│                         │
    │                             │  Prompt: NL → Lean      │
    │                             │────────────────────────▶│
    │                             │                         │
    │                             │  Lean Spec:             │
    │                             │  theorem binary_search  │
    │                             │  ◀─────────────────────│
    │                             │                         │
    │  Spec ◀────────────────────│                         │
    │                             │                         │
    │                             │  Proof Search           │
    │                             │────────────────────────▶│
    │                             │                         │
    │                             │  Proof ✓                │
    │                             │  ◀─────────────────────│
    │                             │                         │
    │                             │  Code Extraction        │
    │                             │────────────────────────▶│
    │                             │                         │
    │  C Binary ◀────────────────│  .so file               │
    │  Python ◀──────────────────│  .whl file              │
    │                             │                         │
```

## Proof Visualization Pipeline

```
Proof Term                    Graph Builder              Web Renderer
    │                             │                         │
    │  theorem foo : ... :=       │                         │
    │    rw [h1]                  │                         │
    │    simp [bar]               │                         │
    │    induction n              │                         │
    │    ...                      │                         │
    │────────────────────────────▶│                         │
    │                             │  Nodes:                 │
    │                             │  • rw (tactic)          │
    │                             │  • simp (tactic)        │
    │                             │  • induction (tactic)   │
    │                             │  Edges: dependencies    │
    │                             │────────────────────────▶│
    │                             │                         │
    │                             │  SVG/Canvas/Three.js    │
    │                             │  Interactive graph      │
    │                             │  ◀─────────────────────│
    │                             │                         │
    │  Browser ◀─────────────────│  HTML + JS              │
    │                             │                         │
```

## Component Interactions

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   CLI       │────▶│   Core      │────▶│   Output    │
│             │     │             │     │             │
│ generate    │     │ spec_gen    │     │ C binary    │
│ guide       │     │ proof_eng   │     │ Python whl  │
│ visualize   │     │ extractor   │     │ Proof viz   │
│ publish     │     │ verifier    │     │ PyPI/GitHub │
│ help        │     │             │     │             │
│ examples    │     │             │     │             │
│ models      │     │             │     │             │
│ walkthrough │     │             │     │             │
│ verify      │     │             │     │             │
└─────────────┘     └─────────────┘     └─────────────┘
```

## LLM Backend Selection Flowchart

```
                    User Request
                        │
                        ▼
               ┌─────────────────┐
               │ --model flag?   │
               └────────┬────────┘
                        │
           ┌────────────┼────────────┐
           │            │            │
           ▼            ▼            ▼
       ┌──────┐    ┌────────┐   ┌────────┐
       │local │    │openai  │   │anthropic│
       └──┬───┘    └───┬────┘   └───┬────┘
          │            │            │
          ▼            ▼            ▼
   ┌────────────┐ ┌─────────┐ ┌──────────┐
   │ Ollama     │ │ GPT-4o  │ │ Claude   │
   │ qwen2.5    │ │ API key │ │ API key  │
   │ coder:14b  │ │         │ │          │
   └─────┬──────┘ └────┬────┘ └────┬─────┘
         │             │           │
         └─────────────┼───────────┘
                       │
                       ▼
               ┌───────────────┐
               │  Lean Spec    │
               │  Generated    │
               └───────────────┘
```

## Proof Search Flowchart

```
               Lean Spec
                   │
                   ▼
          ┌────────────────┐
          │ Write .lean    │
          │ file           │
          └───────┬────────┘
                  │
                  ▼
          ┌────────────────┐
          │ Run lake build │
          └───────┬────────┘
                  │
           ┌──────┴──────┐
           │             │
           ▼             ▼
      ┌────────┐    ┌────────┐
      │Success │    │Failure │
      │        │    │        │
      └───┬────┘    └───┬────┘
          │             │
          ▼             ▼
   ┌────────────┐ ┌──────────────┐
   │ Extract    │ │ Suggest      │
   │ tactics    │ │ hints /      │
   │ Build      │ │ simplify     │
   │ C + Python │ │ spec         │
   └────────────┘ └──────────────┘
```

## File Structure

```
axiomcode/
│
├── cli.py                    # Main CLI — all commands
├── pyproject.toml            # Package config
├── PLAN.md                   # Project roadmap
├── README.md                 # Project overview
│
├── core/                     # Core engine
│   ├── llm.py                # Six LLM backends, one OpenAI-compatible HTTP layer
│   ├── prover.py             # Iterative proof search + repair (Pantograph optional)
│   ├── security.py           # Certificates (Ed25519), key store, audit log, sandbox
│   ├── licensing.py          # Commercial licensing (root keypair, hardware binding)
│   ├── registry.py           # Certificate registry / transparency log
│   ├── persistence.py        # Data store + session history
│   ├── versioning.py         # Upgrade / rollback / migration
│   ├── tiers.py              # Scan / verified / certified tier contract
│   ├── badge.py              # Registry badges
│   └── qr.py                 # Certificate QR codes (segno)
│
├── lean/                     # Lean 4 project
│   ├── lakefile.lean         # Lake build config (Mathlib dependency)
│   ├── src/                  # The verified library (Spec.lean, Tactics.lean)
│   └── drafts/               # Unverified algorithm drafts (quarantined; CI-gated)
│
├── services/                 # Hosted surfaces
│   ├── api/                  # The CA service: REST + MCP, Ed25519 CA, Stripe billing
│   └── registry_app.py       # Read-only registry web app (WSGI)
│
├── publish/                  # Publishing utilities (package marker; CI drives releases)
│
├── docs/                     # Documentation
│   ├── QUICKSTART.md         # 5-minute quickstart
│   └── ARCHITECTURE.md       # This file
│
├── examples/                 # Example scripts
└── tests/                    # Test suite
```
