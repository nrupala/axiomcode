<!--
Copyright (c) 2026 Nrupal Akolkar. All rights reserved.
Proprietary — see LICENSE. No license is granted.
-->

# Contributing to AxiomCode

AxiomCode is proprietary software (see LICENSE — no license is granted without
the copyright holder's prior written permission). Contributions happen by
arrangement with the owner, and every contribution follows the process below.

## PR-flow discipline (standing rule, 2026-10-05)

Direct pushes to `main` are retired. Every change lands through a pull request:

1. Branch off `main` (`git checkout -b <scope>/<short-description>`).
2. Open the PR as a **draft**.
3. Get all checks green (see below), then request review.
4. The **owner merges** — never merge your own PR, never push to `main` directly.
5. Every PR adds a `CHANGELOG.md` entry under `## [Unreleased]` and bumps the
   version (patch = fix/chore, minor = feature) in `pyproject.toml`.
6. Merge commits reference the PR number. Releases are tagged `vX.Y.Z` after
   merge (the `release` workflow builds and publishes on `v*` tags; the `pypi`
   workflow publishes to PyPI on release).

## Build and test

```bash
git clone https://github.com/nrupala/axiomcode.git
cd axiomcode
pip install -e ".[dev]"
```

Checks (all verified against `.github/workflows/`):

```bash
# Tests
python -m pytest tests/ -v --tb=short

# Lint (lint.yml)
ruff check .
ruff format --check .

# Type check (lint.yml / typecheck.yml)
mypy cli.py core/ --ignore-missing-imports

# Proof-honesty gate (tests.yml) — lean/src/ must contain no sorry/admit
grep -rEn '\b(sorry|admit)\b' lean/src/ --include='*.lean' && exit 1 || echo "proof-honesty gate: clean"
```

Every PR must pass lint, typecheck, tests, and the proof-honesty gate before review.

## License

By contributing, you agree your contributions are the proprietary property of
Nrupal Akolkar under the terms in LICENSE.
