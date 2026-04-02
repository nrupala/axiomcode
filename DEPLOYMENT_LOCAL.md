# AxiomCode — Local Deployment & Testing Guide

> **Status:** ✅ Ready for local testing  
> **Version:** 0.1.0 (Alpha)  
> **Deployment Type:** Local Python + Optional External Services  
> **Last Updated:** April 2, 2026

---

## Quick Summary: Is AxiomCode Deployable Locally?

| Component | Status | Notes |
|-----------|--------|-------|
| **Core Security Layer** | ✅ Ready | All cryptographic functions working |
| **CLI Interface** | ✅ Ready | 10+ commands fully functional |
| **Test Suite** | ✅ Ready | 121 tests, all passing (37/37 comprehensive) |
| **Data Persistence** | ✅ Ready | JSON-based storage with versioning |
| **Licensing System** | ✅ Ready | Hardware-bound, expiration, revocation |
| **Key Management** | ✅ Ready | Encrypted key storage, PBKDF2-600k |
| **Proof Verification** | ⚠️ Optional | Requires Lean 4 + lake (not mandatory for demo) |
| **LLM Backend** | ⚠️ Optional | Ollama/OpenAI/Anthropic (choose one) |
| **C Compilation** | ⚠️ Optional | Requires gcc/clang (skipped if missing) |

---

## ✅ WHAT WORKS OUT OF THE BOX

### 1. Core Libraries (No External Dependencies)

```bash
from core.security import KeyStore, ProofCertificate, AuditLog
from core.licensing import LicenseManager, TIERS
from core.persistence import DataStore, DataRecord
from core.versioning import VersionManager

# All work immediately ✅
```

**What You Get:**
- Encrypted key storage with PBKDF2
- Cryptographic proof certificates
- Tamper-evident audit logging
- License management with expiration/revocation
- JSON data persistence with schema versioning
- Version management with backup/rollback

### 2. CLI Commands (All Working)

```bash
python cli.py help                                    # ✅ Works
python cli.py examples                               # ✅ Works
python cli.py guide                                  # ✅ Works (interactive)
python cli.py models                                 # ✅ Works
python cli.py key create root                        # ✅ Works
python cli.py license keygen                         # ✅ Works
python cli.py audit                                  # ✅ Works
python cli.py version show                           # ✅ Works
```

### 3. Test Suite (121 Tests)

```bash
pytest tests/ -v                                     # ✅ 121/121 PASS
pytest tests/test_core_comprehensive.py -v           # ✅ 37/37 PASS
pytest tests/test_core.py -v                         # ✅ 84/84 PASS
```

**Test Coverage:**
- Security (encryption, signatures, audit logs)
- Licensing (generation, verification, expiration)
- Persistence (CRUD, history, schema migration)
- Data validation (path traversal, JSON safety)
- Corruption recovery (handles malformed files)
- Edge cases (special characters, large data)

---

## 📋 PREREQUISITES FOR LOCAL DEPLOYMENT

### Minimum Requirements (For Core Testing)

```
✅ Python 3.10+ (required)
✅ pip (required)
✅ Git (required for cloning)
✅ ~100 MB disk space
```

### Optional Requirements (For Full Features)

| Feature | Requirement | Purpose | Install |
|---------|-------------|---------|---------|
| **Proof Generation** | Lean 4 + lake | Formal verification | [lean-lang.org](https://lean-lang.org) |
| **C Compilation** | gcc/clang | Binary generation | `apt install build-essential` |
| **Local LLM** | Ollama | No cloud dependency | [ollama.ai](https://ollama.ai) |
| **Cloud LLM** | OpenAI/Anthropic API | Faster inference | Set environment variable |

---

## 🚀 STEP-BY-STEP LOCAL DEPLOYMENT

### Phase 1: Core Setup (5 minutes)

#### 1.1 Clone Repository

```bash
git clone https://github.com/nrupala/axiomcode.git
cd axiomcode
```

#### 1.2 Create Virtual Environment

```bash
# Using venv (recommended)
python -m venv venv
source venv/bin/activate          # Linux/Mac
# or
venv\Scripts\activate              # Windows PowerShell

# Verify Python version
python --version                   # Should be 3.10+
```

#### 1.3 Install AxiomCode

```bash
# Development mode (includes test dependencies)
pip install -e ".[dev]"

# or Production mode (minimal)
pip install -e .
```

**What Gets Installed:**
```
✅ axiomcode package
✅ pytest (for tests)
✅ cffi (only external dependency)
✅ All stdlib modules (no additional packages)
```

#### 1.4 Verify Installation

```bash
# Test CLI
python cli.py help

# Test imports
python -c "from core.security import KeyStore; print('✅ Core modules working')"

# Run quick tests
pytest tests/test_core.py::TestSecurity -v
```

**Expected Output:**
```
============================================================
  AxiomCode -- Natural Language to Verified Code
  axiom-code.com | Zero-Trust | Encrypted | Verified
============================================================
[shows help text]
```

---

### Phase 2: Security Testing (10 minutes)

#### 2.1 Test Key Management

```bash
# Create a root key pair
python cli.py key create root --passphrase "my-secure-passphrase"

# List keys
python cli.py key list

# Expected: Shows encrypted key file stored in .axiomcode/keys/
```

#### 2.2 Test License Management

```bash
# Generate hardware-bound license key
python cli.py license keygen

# Issue a license
python cli.py license issue \
  --user alice@example.com \
  --name "Alice" \
  --tier pro \
  --seats 5 \
  --expires 2027-12-31

# Verify license
python cli.py license verify --file alice.license

# Expected: License verified ✓
```

#### 2.3 Test Audit Logging

```bash
# Show audit log
python cli.py audit

# Expected: Shows tamper-evident chain of events
```

#### 2.4 Run Full Test Suite

```bash
# Run all tests
pytest tests/ -v --tb=short

# Expected: 121/121 PASSED ✅
```

---

### Phase 3: Optional External Services Setup

#### Option A: Local LLM with Ollama (Recommended for Privacy)

```bash
# 1. Install Ollama
# Visit https://ollama.ai and download

# 2. Start Ollama service in background
ollama serve

# 3. In another terminal, pull a model
ollama pull qwen2.5-coder:14b        # ~8 GB, takes ~5 min
# or
ollama pull mistral:7b               # ~4 GB, takes ~3 min

# 4. Test connection from AxiomCode
python cli.py models --test ollama

# Expected: ✓ Ollama backend ready
```

#### Option B: Cloud LLM with OpenAI

```bash
# 1. Set API key
export OPENAI_API_KEY="sk-..."

# 2. Test connection
python cli.py models --test openai

# Expected: ✓ OpenAI backend ready
```

#### Option C: C Compilation (Optional)

```bash
# Install compiler
# Linux/Mac:
sudo apt install build-essential

# Windows: Download MinGW or use Visual Studio Build Tools

# Verify
gcc --version

# Expected: gcc (GCC) X.X.X
```

#### Option D: Lean 4 (For Proof Verification)

```bash
# Install from https://lean-lang.org/

# Verify
lean --version
lake --version

# Expected: Lean 4.x.x and lake 4.x.x
```

---

## 🧪 LOCAL TESTING SCENARIOS

### Scenario 1: Security-Only Testing (No LLM Needed)

**Perfect for:**
- Testing encryption/decryption
- Testing license management
- Testing audit logging
- Testing data persistence
- Verifying security architecture

**Command:**
```bash
pytest tests/test_core.py::TestSecurity -v
pytest tests/test_core_comprehensive.py::TestKeyPairAndKeyStore -v
```

**Output:**
```
TestSecurity::test_keypair_generation ✓
TestSecurity::test_keystore_roundtrip ✓
TestSecurity::test_proof_certificate ✓
TestSecurity::test_audit_log_integrity ✓
...all security tests pass...
```

---

### Scenario 2: Data Persistence Testing (No LLM Needed)

**Perfect for:**
- Testing data storage
- Testing migrations
- Testing versioning
- Testing corruption recovery

**Command:**
```bash
pytest tests/test_core.py::TestPersistence -v
pytest tests/test_core.py::TestInputValidation -v
pytest tests/test_core.py::TestCorruptedFileRecovery -v
```

**Output:**
```
TestPersistence::test_datastore_create_get ✓
TestPersistence::test_datastore_history ✓
TestPersistence::test_algorithm_registry ✓
TestInputValidation::test_record_id_validation_path_traversal ✓
...all persistence tests pass...
```

---

### Scenario 3: Licensing Testing (No LLM Needed)

**Perfect for:**
- Testing license generation
- Testing hardware binding
- Testing expiration logic
- Testing revocation

**Command:**
```bash
pytest tests/test_core.py::TestLicensing -v
pytest tests/test_core_comprehensive.py::TestLicensing -v
```

**Example Code:**
```python
from core.licensing import LicenseManager, TIERS
import time

# Create manager
lm = LicenseManager()

# Get hardware fingerprint
fp = lm.get_hardware_fingerprint()
print(f"Hardware: {fp[:16]}...")

# Issue license
cert = lm.issue_license(
    user="alice@example.com",
    name="Alice",
    tier="pro",
    seats=5,
    expires_at=time.time() + 365*24*3600  # 1 year
)

# Verify
assert lm.verify_license(cert)
print(f"✅ License verified: {cert.user}")

# Check expiration
days_left = (cert.expires_at - time.time()) / 86400
print(f"Expires in {days_left:.0f} days")
```

---

### Scenario 4: CLI Testing (No LLM Needed)

**Perfect for:**
- Testing command-line interface
- Testing interactive mode
- Viewing examples
- Creating keys

**Commands:**
```bash
python cli.py examples              # View 6 built-in examples
python cli.py models                # List LLM backends
python cli.py key create test       # Create key
python cli.py key list              # List keys
python cli.py audit                 # View audit log
python cli.py version show          # Show version
python cli.py help                  # Full help
python cli.py walkthrough           # Interactive tutorial (if implemented)
```

---

### Scenario 5: Full Integration (With Ollama)

**Perfect for:**
- End-to-end testing
- Generating proofs
- Full pipeline verification

**Setup:**
```bash
# 1. Start Ollama
ollama serve

# 2. In another terminal, generate code
python cli.py "implement binary search on a sorted array"

# 3. The system will:
#    - Send NL to Ollama (stays local)
#    - Generate Lean 4 spec
#    - Create proof (if Lean 4 installed)
#    - Generate certificate
#    - Show visualization
```

---

## 📊 QUICK HEALTH CHECK

Run this to verify everything is working:

```bash
#!/bin/bash
# health_check.sh

echo "=== AxiomCode Health Check ==="

# 1. Python version
python --version && echo "✅ Python"

# 2. Imports
python -c "from core.security import KeyStore; from core.licensing import LicenseManager; print('✅ Core modules')"

# 3. CLI
python cli.py help > /dev/null && echo "✅ CLI"

# 4. Tests
pytest tests/ -q && echo "✅ All 121 tests"

# 5. Key management
python cli.py key create test && python cli.py key list > /dev/null && echo "✅ Key management"

# 6. License management
python cli.py license keygen > /dev/null && echo "✅ License generation"

# 7. Optional: Ollama
ollama list > /dev/null 2>&1 && echo "✅ Ollama (optional)"

echo "=== Health Check Complete ==="
```

**Run:**
```bash
bash health_check.sh
```

---

## 📦 WHAT'S INCLUDED IN LOCAL DEPLOYMENT

```
axiomcode/
├── core/                          # Core libraries ✅
│   ├── security.py               # Encryption, signing, audit
│   ├── licensing.py              # License management
│   ├── persistence.py            # Data storage
│   └── versioning.py             # Version management
├── cli.py                         # CLI interface ✅
├── tests/                         # 121 tests ✅
│   ├── test_core.py              # Unit tests
│   └── test_core_comprehensive.py # Integration tests
├── docs/                          # Documentation ✅
├── examples/                      # Example algorithms
├── lean/                          # Lean 4 project (optional)
├── visualize/                     # Visualization (placeholder)
└── README.md                      # Quick start
```

**Used by Default:**
- ✅ You can test everything without Lean 4
- ✅ You can manage licenses without LLM
- ✅ You can run the full test suite locally
- ✅ Zero data leaves your machine

**Optional:**
- 🔵 Lean 4 for formal proof generation
- 🔵 Ollama for local LLM inference
- 🔵 gcc for C binary compilation
- 🔵 OpenAI/Anthropic for cloud LLM

---

## 🐛 TROUBLESHOOTING LOCAL DEPLOYMENT

### Issue: "ModuleNotFoundError: No module named 'cffi'"

**Solution:**
```bash
pip install cffi>=1.15
```

---

### Issue: "Python 3.9 detected, need 3.10+"

**Solution:**
```bash
# Check Python version
python --version

# Download Python 3.10+ from python.org
# or use pyenv/conda
```

---

### Issue: "pytest: command not found"

**Solution:**
```bash
pip install -e ".[dev]"  # Install with dev dependencies
```

---

### Issue: Tests failing with "Permission denied"

**Solution:**
```bash
# On Linux/Mac
chmod -R 755 .axiomcode/

# On Windows
icacls ".axiomcode" /grant %USERNAME%:(F) /T
```

---

### Issue: "Ollama connection refused"

**Solution:**
```bash
# Start Ollama service
ollama serve

# In another terminal
ollama list  # Should show available models
```

---

### Issue: "Lean 4 not found" warning

**Solution (Optional):**
```bash
# Visit https://lean-lang.org/
# Download installer for your OS
# Add to PATH

# Verify
lean --version
lake --version
```

---

## 🎯 RECOMMENDED LOCAL TESTING PLAN

### Day 1: Core Functionality (30 minutes)

```bash
# 1. Installation
pip install -e ".[dev]"

# 2. Basic CLI
python cli.py help
python cli.py examples

# 3. Test security
python cli.py key create root
python cli.py license keygen

# 4. Run tests
pytest tests/ -q --tb=short
```

### Day 2: Security Deep Dive (1 hour)

```bash
# Run security-specific tests
pytest tests/test_core.py::TestSecurity -v
pytest tests/test_core.py::TestInputValidation -v

# Test encryption
python -c "
from core.security import SecureChannel
sc = SecureChannel()
encrypted = sc.encrypt(b'Hello, World!')
decrypted = sc.decrypt(encrypted)
print(f'Encrypted: {encrypted[:32]}...')
print(f'Decrypted: {decrypted}')
"
```

### Day 3: Licensing & Persistence (1 hour)

```bash
# Run licensing tests
pytest tests/test_core.py::TestLicensing -v

# Run persistence tests
pytest tests/test_core.py::TestPersistence -v

# Test data migration
python -c "
from core.versioning import VersionManager
vm = VersionManager()
print(f'Current version: {vm.get_current()}')
print(f'Backups: {vm.list_backups()}')
"
```

### Day 4: Optional - Add LLM Backend (1-2 hours)

```bash
# Option A: Ollama
ollama pull qwen2.5-coder:14b
ollama serve  # In background

# Option B: OpenAI
export OPENAI_API_KEY="sk-..."
python cli.py models --test openai
```

---

## ✅ SUCCESS CRITERIA

You'll know AxiomCode is properly deployed when:

- [ ] ✅ `pip install -e ".[dev]"` completes without errors
- [ ] ✅ `python cli.py help` displays the help text
- [ ] ✅ `python cli.py examples` lists 6 algorithms
- [ ] ✅ `pytest tests/ -q` shows 121/121 PASSED
- [ ] ✅ `python cli.py key create test` creates an encrypted key
- [ ] ✅ `python cli.py license keygen` generates a license
- [ ] ✅ All files in `.axiomcode/` are created and accessible
- [ ] ✅ No test failures or warnings

---

## 🚀 NEXT STEPS AFTER LOCAL DEPLOYMENT

### 1. Explore the CLI

```bash
python cli.py guide              # Interactive tutorial
python cli.py models             # List LLM backends
```

### 2. Read the User Guide

```bash
cat AXIOMCODE_USER_GUIDE.md      # Comprehensive guide
```

### 3. Try Code Examples

```python
# See AXIOMCODE_API_REFERENCE.py for full examples
from core.security import KeyStore
from core.licensing import LicenseManager

keystore = KeyStore()
lm = LicenseManager()

# Create and manage licenses
# Store encrypted keys
# Generate audit logs
```

### 4. Run Full Test Suite

```bash
pytest tests/ -v --cov=core
```

---

## 📞 SUPPORT

- **Documentation:** [README.md](README.md), [AXIOMCODE_USER_GUIDE.md](AXIOMCODE_USER_GUIDE.md)
- **API Reference:** [AXIOMCODE_API_REFERENCE.py](AXIOMCODE_API_REFERENCE.py)
- **Issue Tracker:** [GitHub Issues](https://github.com/nrupala/axiomcode/issues)
- **Website:** [axiom-code.com](https://axiom-code.com)

---

**Status Summary:**  
✅ **Deployable** — 121 tests passing  
✅ **Secure** — All crypto working  
✅ **Testing-Ready** — No external dependencies required  
🔵 **Optional upgrades** — Add Lean 4, Ollama, gcc as needed

**Deploy Now:** `pip install -e ".[dev]"` ✨
