"""
Mermaid diagram generator for AxiomCode documentation.
Generates flowcharts and sequence diagrams as SVG/PNG.
"""

from __future__ import annotations

from pathlib import Path


MERMAID_ARCHITECTURE = """
```mermaid
graph TB
    subgraph User["User Interface"]
        CLI["CLI (typer)"]
        Web["Web UI (Flask)"]
        Guide["Guide Mode"]
        Viz["Visualizer (D3.js)"]
    end

    subgraph Core["Core Engine"]
        SG["Spec Generator\nNL → Lean 4"]
        PE["Proof Engine\nPantograph + Lean 4"]
        CE["Code Extractor\nlean --c + cffi"]
        V["Verifier\nIndependent check"]
    end

    subgraph LLM["LLM Backends"]
        Ollama["Ollama (local)\nqwen2.5-coder:14b"]
        Mistral["Mistral (local)\nmistral:7b"]
        OpenAI["OpenAI (cloud)\ngpt-4o"]
        Claude["Anthropic (cloud)\nclaude-sonnet-4"]
    end

    subgraph Output["Output Layer"]
        C["C Binary (.so/.dll)"]
        PY["Python Wheel (.whl)"]
        PV["Proof Visualization"]
        PyPI["PyPI Publish"]
        GH["GitHub Release"]
    end

    CLI --> SG
    Web --> SG
    Guide --> SG
    Viz --> PE

    SG --> Ollama
    SG --> Mistral
    SG --> OpenAI
    SG --> Claude

    SG --> PE
    PE --> CE
    PE --> V

    CE --> C
    CE --> PY
    PE --> PV

    PY --> PyPI
    C --> GH
```
"""

MERMAID_DATA_FLOW = """
```mermaid
sequenceDiagram
    participant U as User
    participant CLI as CLI
    participant SG as Spec Generator
    participant LLM as LLM Backend
    participant PE as Proof Engine
    participant Lean as Lean 4
    participant CE as Code Extractor
    participant Out as Output

    U->>CLI: "implement binary search"
    CLI->>SG: Generate spec
    SG->>LLM: Prompt (NL → Lean)
    LLM-->>SG: Lean theorem
    SG-->>CLI: LeanSpec

    CLI->>PE: Prove spec
    PE->>Lean: lake build
    Lean-->>PE: Proof ✓

    CLI->>CE: Extract code
    CE->>Lean: lean --c
    Lean-->>CE: C source
    CE->>CE: Compile .so
    CE->>CE: Generate cffi bindings
    CE-->>CLI: C binary + Python wheel

    CLI-->>U: ✓ Verified code ready
```
"""

MERMAID_PROOF_VIZ = """
```mermaid
graph LR
    subgraph Proof["Proof Term"]
        T1["rw [h1]"]
        T2["simp [bar]"]
        T3["induction n"]
        T4["constructor"]
        T5["exact base_case"]
        T6["exact inductive_step"]
        QED["QED ✓"]
    end

    subgraph Graph["Proof Graph"]
        N1["Node: rw"]
        N2["Node: simp"]
        N3["Node: induction"]
        N4["Node: constructor"]
        N5["Node: exact"]
        N6["Node: exact"]
        N7["Node: QED"]
    end

    T1 --> N1
    T2 --> N2
    T3 --> N3
    T4 --> N4
    T5 --> N5
    T6 --> N6
    QED --> N7

    N1 --> N2
    N2 --> N3
    N3 --> N4
    N4 --> N5
    N4 --> N6
    N5 --> N7
    N6 --> N7
```
"""


def generate_diagrams(output_dir: str = "docs/images"):
    """Generate Mermaid diagrams as markdown snippets for documentation."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    (out / "architecture.mmd").write_text(MERMAID_ARCHITECTURE)
    (out / "data_flow.mmd").write_text(MERMAID_DATA_FLOW)
    (out / "proof_viz.mmd").write_text(MERMAID_PROOF_VIZ)

    print(f"Diagrams generated in {output_dir}/")
    print("Render with: npx @mermaid-js/mermaid-cli -i docs/images/architecture.mmd -o docs/images/architecture.png")


if __name__ == "__main__":
    generate_diagrams()
