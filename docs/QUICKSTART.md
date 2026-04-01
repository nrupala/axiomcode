# AxiomCode — Quickstart Guide

> **Get from zero to verified code in 5 minutes.**

---

## 1. Install

```bash
# Clone the repository
git clone https://github.com/your-org/axiomcode.git
cd axiomcode

# Install dependencies
pip install -e ".[all]"
```

## 2. Set Up Your LLM

### Option A: Local (Recommended — No API Key Needed)

```bash
# Make sure Ollama is running
ollama serve

# Pull a code-capable model
ollama pull qwen2.5-coder:14b
```

### Option B: Cloud (OpenAI)

```bash
export OPENAI_API_KEY="sk-..."
```

### Option C: Cloud (Anthropic)

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

## 3. Your First Verified Algorithm

```bash
# Quick generate
axiomcode "implement binary search on a sorted array"

# Interactive guided mode
axiomcode guide

# Browse examples
axiomcode examples
```

## 4. View the Proof

```bash
# 2D port graph view
axiomcode visualize binary_search --mode 2d

# Force-directed graph
axiomcode visualize binary_search --mode force

# 3D spatial layout
axiomcode visualize binary_search --mode 3d
```

## 5. Use the Generated Code

```python
# Python
from axiomcode_binary_search import binary_search

result = binary_search([1, 3, 5, 7, 9], 5)
print(result)  # 2 (index of 5)
```

```c
// C
#include "binary_search.h"

int main() {
    int arr[] = {1, 3, 5, 7, 9};
    int idx = binary_search(arr, 5, 5);
    return 0;
}
```

## 6. Publish

```bash
# To PyPI
axiomcode publish binary_search --pypi

# To GitHub Releases
axiomcode publish binary_search --github
```

## Next Steps

- `axiomcode walkthrough` — Interactive tutorial
- `axiomcode help` — Full help & FAQ
- `axiomcode models` — List available LLMs
- Visit [axiom-code.com](https://axiom-code.com) for docs
