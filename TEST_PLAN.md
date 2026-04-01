# AxiomCode — Test Plan

> **Version:** 0.1.0  
> **Date:** 2026-03-31  
> **Status:** Active  
> **Domain:** axiom-code.com

---

## 1. Test Philosophy

AxiomCode follows a **zero-trust testing model**: every component is tested in isolation, every output is independently verifiable, and no external dependency is trusted without validation.

### Principles
- **No external test dependencies** — only `pytest` (stdlib-compatible test runner)
- **Deterministic** — tests produce identical results on every run
- **Fast** — full suite completes in under 10 seconds
- **Isolated** — no test affects another; clean state per test
- **Comprehensive** — unit, integration, security, and end-to-end coverage

---

## 2. Test Categories

### 2.1 Unit Tests (`tests/test_core.py`)

| Module | Test Class | Tests | Coverage |
|--------|-----------|-------|----------|
| Spec Generator | `TestSpecGenerator` | 4 | Spec creation, parsing, backend registration |
| Security | `TestSecurity` | 9 | Key management, certificates, HMAC, hashing, audit log, sandbox, rate limiter |
| Visualization | `TestVisualization` | 2 | Graph data generation, HTML rendering |
| CLI | `TestCLI` | 1 | Command registration |
| Versioning | `TestVersioning` | 9 | Version tracking, migration, backup, validation |
| Licensing | `TestLicensing` | 12 | Key pairs, license issue/verify, tamper detection, expiration, revocation, hardware fingerprint |

**Total: 37 tests**

### 2.2 Integration Tests (Planned: `tests/test_integration.py`)

| Test | Description | Status |
|------|-------------|--------|
| `test_full_pipeline_local` | NL → Spec → Proof → C → Python → Certificate (local model) | Pending Ollama |
| `test_full_pipeline_openai` | NL → Spec → Proof → C → Python → Certificate (OpenAI) | Pending API key |
| `test_visualization_serve` | Start visualization server, verify HTML response | Pending |
| `test_certificate_roundtrip` | Create cert, save, load, verify signature | Ready |
| `test_key_store_roundtrip` | Create key, save, load with passphrase | Ready |
| `test_audit_log_chain` | Write entries, verify chain integrity, detect tampering | Ready |
| `test_persistence_store` | Create, update, delete records with history | Ready |
| `test_algorithm_registry` | Register, search, list algorithms | Ready |

### 2.3 Security Tests (Planned: `tests/test_security.py`)

| Test | Description | Status |
|------|-------------|--------|
| `test_encryption_decryption` | Encrypt data, decrypt, verify plaintext matches | Ready |
| `test_key_derivation_deterministic` | Same passphrase + salt = same key | Ready |
| `test_certificate_tamper_detection` | Modify cert fields, verify fails | Ready |
| `test_hmac_constant_time` | Verify HMAC uses constant-time comparison | Ready |
| `test_audit_log_tamper_detection` | Modify log entry, verify_integrity returns False | Ready |
| `test_sandbox_isolation` | Sandbox cannot access host filesystem | Ready |
| `test_rate_limiting` | Verify tokens deplete and refill | Ready |
| `test_secure_channel_integrity` | Tamper with encrypted data, detect MAC failure | Ready |

### 2.4 End-to-End Tests (Planned: `tests/test_e2e.py`)

| Test | Description | Prerequisites |
|------|-------------|---------------|
| `test_e2e_binary_search` | Generate verified binary search, verify certificate | Ollama + Lean 4 |
| `test_e2e_insertion_sort` | Generate verified insertion sort, verify certificate | Ollama + Lean 4 |
| `test_e2e_gcd` | Generate verified GCD, verify certificate | Ollama + Lean 4 |
| `test_e2e_publish_dry_run` | Run publish in dry-run mode, verify artifacts exist | Generated artifacts |
| `test_e2e_verify_all` | Run verify on all generated algorithms | Generated artifacts |

### 2.5 Performance Tests (Planned: `tests/test_performance.py`)

| Test | Target | Threshold |
|------|--------|-----------|
| `test_spec_generation_latency` | NL → Spec generation | < 30s (local), < 5s (cloud) |
| `test_proof_verification_latency` | Lean proof verification | < 60s |
| `test_code_extraction_latency` | Lean → C extraction | < 10s |
| `test_memory_usage` | Peak memory during generation | < 512MB |
| `test_cache_hit_rate` | LLM cache effectiveness | > 50% on repeated calls |

### 2.6 CLI Tests (Planned: `tests/test_cli.py`)

| Test | Command | Expected |
|------|---------|----------|
| `test_cli_no_args` | `python cli.py` | Prints help |
| `test_cli_help` | `python cli.py help` | Prints full help + FAQ |
| `test_cli_examples` | `python cli.py examples` | Lists 6 examples |
| `test_cli_models` | `python cli.py models` | Lists 4 backends + local models |
| `test_cli_guide` | `python cli.py guide` | Starts interactive mode |
| `test_cli_walkthrough` | `python cli.py walkthrough` | Prints tutorial |
| `test_cli_key_create` | `python cli.py key create test` | Creates encrypted key |
| `test_cli_key_list` | `python cli.py key list` | Lists existing keys |
| `test_cli_audit` | `python cli.py audit` | Shows audit log |
| `test_cli_verify_missing` | `python cli.py verify nonexistent` | Exits with error |
| `test_cli_visualize_missing` | `python cli.py visualize nonexistent` | Exits with error |
| `test_cli_license_keygen` | `python cli.py license keygen` | Generates root key pair |
| `test_cli_license_issue` | `python cli.py license issue` | Issues license |
| `test_cli_license_verify` | `python cli.py license verify` | Verifies license |
| `test_cli_version_show` | `python cli.py version show` | Shows current version |

---

## 3. Test Execution

### Run All Tests
```bash
cd D:\axiomcode
python -m pytest tests/ -v
```

### Run by Category
```bash
# Unit tests only
python -m pytest tests/test_core.py -v

# With coverage (when coverage.py is available)
python -m pytest tests/ --cov=cli --cov=core --cov-report=term-missing

# Fast tests only (skip slow/external)
python -m pytest tests/ -v -k "not e2e and not performance"

# Security tests only
python -m pytest tests/test_core.py::TestSecurity -v

# Licensing tests only
python -m pytest tests/test_core.py::TestLicensing -v
```

### CI/CD Pipeline (GitHub Actions)
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11", "3.12"]
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - name: Install dependencies
        run: pip install pytest cffi
      - name: Run tests
        run: python -m pytest tests/ -v --tb=short
      - name: Security audit
        run: python -m pytest tests/test_core.py::TestSecurity -v
```

---

## 4. Test Data

### Test Fixtures
All test data is generated programmatically. No external files required.

| Fixture | Purpose | Location |
|---------|---------|----------|
| `KeyPair.generate()` | Test cryptographic keys | In-memory |
| `ProofCertificate()` | Test certificate signing | In-memory |
| `SecureSandbox()` | Test isolated execution | Temp directory |
| `AuditLog()` | Test tamper-evident logging | Temp file |
| `LLMCache()` | Test response caching | Temp directory |
| `DataStore()` | Test persistence layer | Temp directory |
| `LicenseManager()` | Test licensing system | In-memory |

### Mock LLM Responses
For testing without external services:
```python
# Mock Ollama response
MOCK_SPEC_RESPONSE = """```lean
import Mathlib
import Aesop

/-- Binary search on a sorted list. -/
theorem binary_search_correct : True := by sorry
```"""
```

---

## 5. Security Test Matrix

| Threat | Test | Mitigation |
|--------|------|------------|
| Key theft | `test_keystore_roundtrip` | Encrypted at rest, PBKDF2-derived |
| Certificate forgery | `test_certificate_tamper` | HMAC signature verification |
| Binary tampering | `test_binary_signature_verify` | Hash-based integrity check |
| Audit log tampering | `test_audit_log_integrity` | Hash-chained entries |
| Data interception | `test_secure_channel` | Encrypted transport with MAC |
| Resource exhaustion | `test_rate_limiter` | Token bucket rate limiting |
| Code injection | `test_secure_sandbox` | Isolated subprocess, restricted env |
| Replay attack | `test_certificate_timestamp` | Timestamps in certificates |
| License forgery | `test_license_tamper_detection` | HMAC-signed licenses |
| Hardware spoofing | `test_hardware_fingerprint` | Multi-factor hardware binding |

---

## 6. Coverage Targets

| Component | Target | Current |
|-----------|--------|---------|
| `cli.py` | 80% | ~60% (CLI commands need integration tests) |
| `core/security.py` | 95% | ~90% |
| `core/versioning.py` | 90% | ~85% |
| `core/licensing.py` | 95% | ~90% |
| `core/persistence.py` | 90% | ~80% |
| **Overall** | **85%** | **~75%** |

---

## 7. Known Gaps

| Gap | Priority | Plan |
|-----|----------|------|
| No Ollama response in CI | High | Mock HTTP responses for CI |
| No Lean 4 in CI | High | Skip proof tests when Lean not available |
| No end-to-end pipeline test | Medium | Requires Ollama + Lean 4 setup |
| No performance benchmarks | Medium | Add timing assertions |
| No fuzz testing | Low | Add property-based tests with hypothesis |
| No cross-platform tests | Medium | Test on Linux, macOS, Windows CI |

---

## 8. Test Results

### Current Run (2026-03-31)
```
tests/test_core.py::TestSpecGenerator (4 tests) — ALL PASSED
tests/test_core.py::TestSecurity (9 tests) — ALL PASSED
tests/test_core.py::TestVisualization (2 tests) — ALL PASSED
tests/test_core.py::TestCLI (1 test) — ALL PASSED
tests/test_core.py::TestVersioning (9 tests) — ALL PASSED
tests/test_core.py::TestLicensing (12 tests) — ALL PASSED

37 passed in ~6s
```

---

## 9. Release Checklist

Before each release:

- [ ] All tests pass (`python -m pytest tests/ -v`)
- [ ] No security vulnerabilities in dependencies (only cffi)
- [ ] Audit log integrity verified
- [ ] Proof certificates valid for all shipped algorithms
- [ ] CLI help text up to date
- [ ] README.md reflects current state
- [ ] Version bumped in `pyproject.toml`
- [ ] CHANGELOG.md updated
- [ ] Domain axiom-code.com DNS configured
- [ ] GitHub repository created and pushed
- [ ] GitHub Pages published
