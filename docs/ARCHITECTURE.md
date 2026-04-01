# AxiomCode — Architecture & Flowcharts

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                            USER INTERFACE                                │
│  ┌───────────┐  ┌────────────┐  ┌──────────┐  ┌────────────────────┐   │
│  │ CLI       │  │ Web UI     │  │ Guide    │  │ Visualizer         │   │
│  │ (typer)   │  │ (Flask)    │  │ Mode     │  │ (D3.js/Three.js)   │   │
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
│   ├── spec_generator.py     # NL → Lean 4 (Ollama/Mistral/OpenAI/Anthropic)
│   ├── proof_engine.py       # Pantograph + Lean 4 proof search
│   ├── code_extractor.py     # lean --c → C, cffi → Python
│   └── verifier.py           # Independent proof verification
│
├── visualize/                # Proof visualization
│   ├── port_graph.py         # 2D port graph (Incredible Proof Machine style)
│   ├── force_graph.py        # Force-directed dependency graph
│   ├── layout_3d.py          # 3D spatial layout
│   └── web/
│       └── app.py            # Flask web app with D3.js
│
├── lean/                     # Lean 4 project
│   ├── lakefile.lean         # Lake build config
│   └── src/
│       ├── Spec.lean         # Core specification definitions
│       ├── Tactics.lean      # Custom proof tactics
│       └── Algorithms/
│           └── insertion_sort.lean  # Example verified algorithm
│
├── libraries/                # Domain-specific verified libraries
│   ├── sorting/
│   ├── searching/
│   ├── data_structures/
│   └── numerical/
│
├── publish/                  # Publishing utilities
│   ├── pypi_upload.py        # PyPI upload
│   └── github_release.py     # GitHub release
│
├── docs/                     # Documentation
│   ├── QUICKSTART.md         # 5-minute quickstart
│   └── ARCHITECTURE.md       # This file
│
├── examples/                 # Example scripts
└── tests/                    # Test suite
```
