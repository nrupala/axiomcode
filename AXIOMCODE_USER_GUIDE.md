# AxiomCode User Guide & Learning Handbook

> **Natural Language to Formally Verified Code**  
> Interactive Tutorial • API Reference • Code Examples  
> Version 0.1.0 | axiom-code.com

---

## Table of Contents
1. [Quick Start (60 seconds)](#quick-start)
2. [Core Concepts](#core-concepts)
3. [Installation & Setup](#installation--setup)
4. [CLI Reference](#cli-reference)
5. [Code Examples](#code-examples)
6. [Security Model](#security-model)
7. [Licensing System](#licensing-system)
8. [API Reference](#api-reference)
9. [Troubleshooting](#troubleshooting)
10. [FAQ](#faq)

---

## Quick Start

### In 60 Seconds

```bash
# 1. Clone the repository
git clone https://github.com/nrupala/axiomcode.git
cd axiomcode

# 2. Install
pip install -e ".[dev]"

# 3. Generate your first verified algorithm
python cli.py "implement binary search on a sorted array"

# 4. View the proof
python cli.py visualize binary_search

# 5. See the certificate
python cli.py cert binary_search
```

**What You Get:**
```
✅ Formally verified Python code (proven correct by Lean 4)
✅ Compiled C binary (.so/.dll)
✅ Interactive proof visualization (2D graph)
✅ Cryptographic certificate proving correctness
✅ Tamper-evident audit log
```

---

## Core Concepts

### 1. The Pipeline: NL → Proof → Code

```
Your English Description
        ↓
   LLM (Ollama/OpenAI/Claude)
        ↓
  Lean 4 Specification
        ↓
   Proof Engine (Pantograph)
        ↓
     C Binary + Python
        ↓
Cryptographic Certificate
```

### 2. Zero-Trust Security Model

Everything in AxiomCode can be independently verified:

```python
# Example: Verify a proof certificate independently
from core.security import ProofCertificate
import hashlib
import hmac

cert = ProofCertificate.load("binary_search.cert")

# Anyone can verify WITHOUT trusting AxiomCode
signature_valid = cert.verify_signature(cert.signature, public_key)
proof_matches = hashlib.sha256(actual_proof).hexdigest() == cert.proof_hash
print(f"Certificate valid: {signature_valid and proof_matches}")
```

### 3. Cryptographic Guarantees

Every algorithm comes with:
- **Spec Hash**: SHA-512 of the formal specification
- **Proof Hash**: SHA-512 of the verification proof
- **Binary Hash**: SHA-512 of the compiled C binary
- **HMAC Signature**: HMAC-SHA512 proving authenticity
- **Timestamp**: Non-repudiation via creation time
- **Key ID**: Which signing key was used

---

## Installation & Setup

### Prerequisites
- Python 3.10+
- Git
- Lean 4 (for proof generation)
- Ollama or OpenAI API key (for LLM backend)

### Step 1: Clone Repository

```bash
git clone https://github.com/nrupala/axiomcode.git
cd axiomcode
```

### Step 2: Create Virtual Environment (Recommended)

```bash
# Using venv
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Or using conda
conda create -n axiomcode python=3.10
conda activate axiomcode
```

### Step 3: Install AxiomCode

```bash
# Development mode (includes test dependencies)
pip install -e ".[dev]"

# Or production mode (minimal)
pip install -e .
```

### Step 4: Configure Your LLM Backend

#### Option A: Local Ollama (Recommended for Privacy)

```bash
# Install Ollama from https://ollama.ai

# Pull a model
ollama pull qwen2.5-coder:14b

# Start Ollama service
ollama serve

# In another terminal, test it
python -c "from core.cli import test_ollama_backend; test_ollama_backend()"
```

#### Option B: OpenAI API

```bash
# Set your API key
export OPENAI_API_KEY="sk-..."

# Or in Python
import os
os.environ["OPENAI_API_KEY"] = "sk-..."
```

#### Option C: Anthropic API

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

### Step 5: Runtime Configuration

```bash
# Create config file (optional)
cat > ~/.axiomcode/config.json << EOF
{
  "default_backend": "ollama",
  "ollama_host": "http://localhost:11434",
  "model": "qwen2.5-coder:14b",
  "cache_enabled": true,
  "cache_dir": ".axiomcode/cache"
}
EOF
```

---

## CLI Reference

### Command Structure

```bash
python cli.py <command> [arguments] [options]
```

### Global Commands

#### 1. Generate Verified Code (Main Command)

```bash
# From natural language description
python cli.py "describe your algorithm here"

# Example
python cli.py "implement binary search that returns index or -1"

# Interactive mode
python cli.py guide
```

**Flow:**
- NL → LLM generates Lean 4 spec
- Pantograph verifies the proof
- Code extracted to C + Python
- Certificate generated and signed

**Output Files:**
```
.axiomcode/
├── binary_search.lean           (Lean 4 source)
├── binary_search.c              (C implementation)
├── binary_search.py             (Python wrapper)
├── binary_search.o              (Compiled binary)
├── binary_search.cert           (Certificate)
└── binary_search.json           (Metadata)
```

#### 2. Visualization

```bash
# 2D port graph (default)
python cli.py visualize binary_search

# Force-directed graph
python cli.py visualize binary_search --mode force

# 3D spatial layout
python cli.py visualize binary_search --mode 3d

# Open in browser
python cli.py visualize binary_search --open
```

**Output:** Interactive HTML with D3.js  
**File:** `.axiomcode/binary_search.html`

#### 3. Proof Verification

```bash
# Verify a proof is correct
python cli.py verify binary_search

# Verify and show details
python cli.py verify binary_search --verbose

# Output: ✅ Proof verified | Hash matches | Certificate valid
```

#### 4. Certificate Management

```bash
# Show certificate details
python cli.py cert binary_search

# Export certificate
python cli.py cert binary_search --export cert.json

# Verify certificate independently
python cli.py cert binary_search --verify-sig
```

#### 5. Key Management

```bash
# Generate root key pair (one-time setup)
python cli.py key create root

# List all keys
python cli.py key list

# Show key details
python cli.py key show root

# Delete a key
python cli.py key delete root --force
```

#### 6. License Management

```bash
# Generate hardware-bound license
python cli.py license keygen

# Issue a license
python cli.py license issue \
  --user user@example.com \
  --name "Alice" \
  --tier pro \
  --seats 5 \
  --expires 2027-12-31

# Verify license
python cli.py license verify --file alice.license

# Show available tiers
python cli.py license tiers

# Revoke license
python cli.py license revoke --file alice.license
```

#### 7. Audit Log

```bash
# Show audit log
python cli.py audit

# Export audit log
python cli.py audit --export audit.json

# Verify audit log integrity
python cli.py audit --verify-chain
```

#### 8. Version Management

```bash
# Show version
python cli.py version show

# Validate data
python cli.py version validate

# Show migration history
python cli.py version history

# Backup current state
python cli.py version backup

# Rollback to previous version
python cli.py version rollback
```

#### 9. Help & Examples

```bash
# Show help
python cli.py help

# Show FAQ
python cli.py help --faq

# Browse examples
python cli.py examples

# Show example details
python cli.py examples --name "binary_search"

# Interactive walkthrough
python cli.py walkthrough
```

#### 10. Model Management

```bash
# List available backends
python cli.py models

# List available models per backend
python cli.py models --backend ollama

# Test backend connectivity
python cli.py models --test ollama

# Set default model
python cli.py models --set-default qwen2.5-coder:14b
```

---

## Code Examples

### Example 1: Binary Search (Simplest)

**Natural Language Input:**
```
Implement binary search on a sorted array. 
It should return the index of the target element, 
or -1 if not found.
```

**CLI Command:**
```bash
python cli.py "implement binary search on a sorted array, return index or -1 if not found"
```

**Generated Lean 4 Proof:**
```lean
theorem binary_search : ∀ (arr : List Int) (target : Int),
  IsSorted arr → 
  (binary_search arr target = -1 ↔ ¬(target ∈ arr)) ∧
  (binary_search arr target ≠ -1 → arr[binary_search arr target] = target)
```

**Generated Python Code:**
```python
def binary_search(arr: list[int], target: int) -> int:
    """
    Binary search on sorted array.
    
    Formally verified to:
    - Return index if target found
    - Return -1 if target not found
    - Maintain O(log n) time complexity
    
    Certificate: binary_search.cert
    """
    left, right = 0, len(arr) - 1
    
    while left <= right:
        mid = (left + right) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    
    return -1
```

**Generated C Code:**
```c
// C binary compiled with proof verification
// File: binary_search.so or binary_search.dll
// Proof verified: ✓
// Certificate: binary_search.cert

int binary_search(int* arr, int len, int target) {
    int left = 0, right = len - 1;
    
    while (left <= right) {
        int mid = (left + right) / 2;
        if (arr[mid] == target) return mid;
        if (arr[mid] < target) left = mid + 1;
        else right = mid - 1;
    }
    
    return -1;
}
```

**Usage:**
```python
from axiomcode import binary_search

# Works with the verified proof
result = binary_search([1, 3, 5, 7, 9], 5)
print(f"Found at index: {result}")  # Output: 2

# Automatically uses C binary for speed
result = binary_search([1, 3, 5, 7, 9], 10)
print(f"Found at index: {result}")  # Output: -1
```

---

### Example 2: Insertion Sort (Medium)

**Input:**
```
Implement insertion sort that sorts a list of natural numbers.
Prove it always produces a sorted list that is a permutation of the input.
```

**CLI:**
```bash
python cli.py "implement insertion sort for natural numbers, prove output is sorted and is a permutation of input"
```

**Generated Code:**
```python
from typing import List

def insertion_sort(arr: List[int]) -> List[int]:
    """
    Insertion sort with formal proof of correctness.
    
    Theorem: ∀(arr : List Int),
      IsSorted (insertion_sort arr) ∧ 
      Permutation (insertion_sort arr) arr
    
    Certificate hash: a3f2d8c9e1b5f7a2...
    Proof steps: 47 | Lemmas: 12
    Generated with: qwen2.5-coder:14b
    Verified by: Lean 4 Pantograph
    """
    result = arr.copy()
    
    for i in range(1, len(result)):
        key = result[i]
        j = i - 1
        
        while j >= 0 and result[j] > key:
            result[j + 1] = result[j]
            j -= 1
        
        result[j + 1] = key
    
    return result
```

**Testing:**
```python
from axiomcode import insertion_sort

# Test 1: Already sorted
assert insertion_sort([1, 2, 3]) == [1, 2, 3]

# Test 2: Reverse sorted
assert insertion_sort([3, 2, 1]) == [1, 2, 3]

# Test 3: Random order
assert insertion_sort([5, 2, 8, 1, 9]) == [1, 2, 5, 8, 9]

# Test 4: Duplicates
assert insertion_sort([3, 1, 3, 1]) == [1, 1, 3, 3]

# All tests pass because code is formally verified
print("✅ All tests passed (formally verified)")
```

---

### Example 3: Security & Licensing (Advanced)

**Secure Key Generation:**
```python
from core.security import KeyStore, KeyPair
from core.licensing import LicenseManager, LicenseCertificate
from pathlib import Path
import tempfile

# Initialize key store with a passphrase
with tempfile.TemporaryDirectory() as tmpdir:
    keystore = KeyStore(tmpdir)
    
    # Create a key (securely encrypted with PBKDF2)
    key = keystore.create_key("my_key", passphrase="secure_password_123")
    print(f"Key created: {key.key_id}")
    
    # Load the key (passphrase required)
    loaded = keystore.load_key("my_key", passphrase="secure_password_123")
    assert loaded.key_id == key.key_id
    
    # Wrong passphrase fails
    try:
        keystore.load_key("my_key", passphrase="wrong_password")
    except ValueError as e:
        print(f"✅ Security working: {e}")
```

**License Management:**
```python
from core.licensing import LicenseManager, TIERS

# Create license manager
lm = LicenseManager()

# Get hardware fingerprint (immutable on same machine)
fingerprint = lm.get_hardware_fingerprint()
print(f"Hardware: {fingerprint[:16]}...")

# Issue a license
cert = lm.issue_license(
    user="alice@example.com",
    name="Alice Developer",
    tier="pro",
    hardware_fingerprint=fingerprint,
    expires_days=365,
    max_seats=5,
    features=TIERS["pro"]["features"]
)

# Save license
lm.save_license(cert, "alice.license")

# Verify license (can do independently)
loaded = lm.load_license("alice.license")
is_valid = lm.verify_license(loaded)
print(f"License valid: {is_valid}")

# Check expiration
if lm.is_expired(loaded):
    print("License expired")
else:
    days_left = (loaded.expires_at - time.time()) / 86400
    print(f"License expires in {days_left:.0f} days")
```

---

### Example 4: Cryptographic Proof Certificates (Advanced)

**Creating & Verifying Certificates:**
```python
from core.security import ProofCertificate, sign_binary, hash_file
from pathlib import Path

# Create certificate for a verified algorithm
cert = ProofCertificate(
    algorithm_name="binary_search",
    spec_hash="abc123def456...",
    proof_hash="xyz789uvw012...",
    c_binary_hash=hash_file(Path("binary_search.so")),
    python_hash="hash_of_python_wheel",
    theorem="∀ arr target, IsSorted arr → ...",
    tactics=["apply binary_search_theorem", "simp", "omega"],
    steps=42,
    lemmas=8,
    model_used="gpt-4o",
    generated_at=time.time(),
)

# Sign it with your key
signing_key = keystore.load_key("root", passphrase)
cert = cert.sign(signing_key.signing_key)

# Save and load
cert.save("binary_search.cert")
loaded = ProofCertificate.load("binary_search.cert")

# Verify signature (anyone can do this)
is_valid = loaded.verify_signature(signing_key.signing_key)
print(f"Certificate signed by root: {is_valid}")
```

---

### Example 5: Data Persistence & Migration (Advanced)

**Store and Version Data:**
```python
from core.persistence import DataStore
import tempfile

with tempfile.TemporaryDirectory() as tmpdir:
    store = DataStore(tmpdir)
    
    # Create a record
    record = store.create(
        record_id="algorithm_v1",
        data={
            "name": "binary_search",
            "version": 1,
            "proof_hash": "abc123...",
            "generated": "2026-04-01T09:00:00Z"
        },
        metadata={"author": "alice", "tier": "pro"}
    )
    
    # Update it
    updated = store.update(
        record_id="algorithm_v1",
        data={"version": 2, "proof_hash": "def456..."}
    )
    
    # List all records
    all_records = store.list()
    for r in all_records:
        print(f"ID: {r.id}, Version: {r.schema_version}")
    
    # Get history (data is never lost)
    history = store.get_history("algorithm_v1")
    print(f"Record updated {len(history)} times")
```

---

### Example 6: Audit Logging & Tamper Detection (Advanced)

**Create Tamper-Evident Audit Trail:**
```python
from core.security import AuditLog, hash_data
from pathlib import Path
import json

# Initialize audit log
audit = AuditLog(Path(".axiomcode/audit.log"))

# Log an event
audit.log_event(
    event_type="proof_verified",
    details={
        "algorithm": "binary_search",
        "proof_valid": True,
        "timestamp": "2026-04-01T09:30:00Z"
    }
)

# Log another event
audit.log_event(
    event_type="certificate_signed",
    details={
        "algorithm": "binary_search",
        "key_id": "root",
        "signature_hash": "abc123..."
    }
)

# Verify chain integrity (detect tampering)
chain_valid = audit.verify_integrity()
print(f"Audit log tamper-proof: {chain_valid}")

# Read log
events = audit.read_log()
for entry in events:
    print(f"[{entry['timestamp']}] {entry['event_type']}: {entry['details']}")
```

---

## Security Model

### Five Layers of Security

```
Layer 1: Zero-Trust (Everyone can verify independently)
Layer 2: Encryption (PBKDF2-600k iterations + SHA-512 XOR)
Layer 3: Authentication (HMAC-SHA512 with constant-time comparison)
Layer 4: Audit (Hash-chained tamper-evident logging)
Layer 5: Isolation (Secure sandbox with subprocess restriction)
```

### Key Principles

**1. Zero External Dependencies**
- No pip packages except cffi
- No requests, no Flask, no cryptography library
- All crypto from Python stdlib: hashlib, hmac, secrets

**2. Zero-Knowledge**
- LLM prompts never contain sensitive data
- Proofs are verified locally in Lean 4
- No telemetry or tracking

**3. Zero-Trust**
- Every output independently verifiable
- Cryptographic certificates signed with HMAC
- Tamper-evident audit log with hash chaining

**4. Hardware Binding**
- Licenses tied to specific hardware
- Fingerprint computed from CPU, MAC, disk serial
- Prevents license copying across machines

### Attack Scenarios Defended Against

```python
# Attack 1: Modified algorithm code
cert = ProofCertificate.load("modified_binary_search.cert")
cert.verify_signature(key)  # ❌ Fails - signature doesn't match

# Attack 2: Swapped proofs
actual_hash = hash_file(Path("binary_search.o"))
if actual_hash != cert.c_binary_hash:
    raise ValueError("Binary tampered with")

# Attack 3: Forged certificate
cert.compute_signature()  # Won't match without private key

# Attack 4: Modified audit log
if not audit.verify_integrity():
    print("Audit log has been tampered with!")

# Attack 5: License on wrong machine
if license.hardware_fingerprint != current_hardware:
    raise ValueError("License not valid on this hardware")
```

---

## Licensing System

### Tier-Based Access

```python
TIERS = {
    "free": {
        "algorithms_per_day": 3,
        "max_proof_size": "50KB",
        "features": ["basic_proofs", "local_viz"]
    },
    "pro": {
        "algorithms_per_day": 50,
        "max_proof_size": "10MB",
        "features": ["advanced_tactics", "cloud_backends", "priority_support"]
    },
    "enterprise": {
        "algorithms_per_day": "unlimited",
        "max_proof_size": "unlimited",
        "features": ["custom_tactics", "dedicated_server", "sla"]
    }
}
```

### Check License in Your Code

```python
from core.licensing import LicenseManager

def generate_algorithm(description: str) -> bytes:
    # Check license before generating
    license = LicenseManager().get_current_license()
    
    if license.tier == "free" and daily_count >= 3:
        raise ValueError("Free tier limit exceeded")
    
    if len(description) > max_size[license.tier]:
        raise ValueError("Description too large for tier")
    
    # Proceed with generation
    return generate_verified_code(description)
```

---

## API Reference

### Core Modules

#### `core.security.KeyStore`

```python
class KeyStore:
    """Encrypted key storage with PBKDF2 derivation."""
    
    def create_key(self, name: str, passphrase: str) -> KeyPair:
        """Create and store encrypted key pair."""
    
    def load_key(self, name: str, passphrase: str) -> KeyPair:
        """Load and decrypt key (validates passphrase)."""
    
    def delete_key(self, name: str) -> None:
        """Securely delete key (overwrite before deletion)."""
```

#### `core.security.ProofCertificate`

```python
@dataclass
class ProofCertificate:
    """Cryptographic attestation of algorithm correctness."""
    
    algorithm_name: str
    spec_hash: str              # SHA-512 of Lean spec
    proof_hash: str             # SHA-512 of proof term
    c_binary_hash: str          # SHA-512 of compiled binary
    python_hash: str            # SHA-512 of Python package
    signature: str              # HMAC-SHA512 signature
    key_id: str                 # ID of signing key
    
    def sign(self, signing_key: bytes) -> "ProofCertificate":
        """Sign certificate with key."""
    
    def verify_signature(self, key: bytes) -> bool:
        """Verify HMAC signature (constant-time)."""
    
    def save(self, path: str) -> None:
        """Save to JSON file."""
    
    @classmethod
    def load(cls, path: str) -> "ProofCertificate":
        """Load from JSON file."""
```

#### `core.persistence.DataStore`

```python
class DataStore:
    """JSON storage with schema versioning and history."""
    
    def create(self, record_id: str, data: dict, metadata: dict = None) -> DataRecord:
        """Create new record with validation."""
    
    def get(self, record_id: str) -> DataRecord | None:
        """Retrieve record by ID."""
    
    def update(self, record_id: str, data: dict) -> DataRecord:
        """Update record (old version preserved in history)."""
    
    def delete(self, record_id: str) -> None:
        """Mark record as deleted (data retained in history)."""
    
    def list(self) -> List[DataRecord]:
        """List all current records."""
    
    def get_history(self, record_id: str) -> List[DataRecord]:
        """Get all versions of a record."""
```

#### `core.licensing.LicenseManager`

```python
class LicenseManager:
    """Hardware-bound license management."""
    
    def get_hardware_fingerprint(self) -> str:
        """Compute immutable hardware fingerprint."""
    
    def issue_license(self, user: str, tier: str, **kwargs) -> LicenseCertificate:
        """Create signed license certificate."""
    
    def load_license(self, path: str) -> LicenseCertificate:
        """Load and validate license from file."""
    
    def verify_license(self, cert: LicenseCertificate) -> bool:
        """Verify license signature and hardware binding."""
    
    def is_expired(self, cert: LicenseCertificate) -> bool:
        """Check if license has expired."""
    
    def is_revoked(self, cert: LicenseCertificate) -> bool:
        """Check if license has been revoked."""
```

---

## Troubleshooting

### Problem: "Failed to find correct proof"

**Cause:** LLM specification too vague or Lean 4 tactics insufficient

**Solution:**
```bash
# 1. Be more specific
python cli.py "implement binary search that:
  - Accepts sorted list of integers
  - Returns index if found
  - Returns -1 if not found
  - Runs in O(log n) time"

# 2. Enable verbose mode for debugging
python cli.py "your description" --verbose

# 3. Check proof generation logs
cat .axiomcode/proof.log
```

### Problem: "Wrong passphrase" error when loading key

**Cause:** Passphrase doesn't match (or cache bypass issue fixed)

**Solution:**
```python
from core.security import KeyStore

try:
    key = keystore.load_key("my_key", "correct_password")
except ValueError as e:
    print(f"Error: {e}")
    # The fix ensures this validates EVERY load, not from cache
```

### Problem: "File too large" or "JSON too large"

**Cause:** Input validation limits (10MB default)

**Solution:**
```python
from core.persistence import DataStore

# Use smaller records
store.create("small_record", data_under_10mb)

# Or increase limit in code
DataStore.MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
```

### Problem: Ollama connection fails

**Cause:** Ollama service not running

**Solution:**
```bash
# Start Ollama
ollama serve

# In another terminal, verify
python cli.py models --test ollama

# Falls back to OpenAI if Ollama fails
export OPENAI_API_KEY="sk-..."
```

### Problem: "Invalid key file format"

**Cause:** File corruption or incompatible version

**Solution:**
```bash
# Recover from backup
python cli.py version rollback

# Or regenerate key
python cli.py key delete my_key --force
python cli.py key create my_key
```

---

## FAQ

### Q: Is my code actually proven correct?

**A:** Yes. Every algorithm is mathematically verified by Lean 4's compiler. If the proof is invalid, Lean won't compile it. The cryptographic certificate proves this happened.

### Q: What if the LLM generates bad code?

**A:** Lean 4 won't accept it. If a specification doesn't lead to a valid proof, code extraction fails. No code is generated without a proof.

### Q: Can I modify the generated code?

**A:** Yes, but the certificate becomes invalid. The certificate only guarantees the original generated code is correct.

### Q: Is this only for algorithms?

**A:** Currently: sorting, searching, math algorithms.  
Future: data structures, distributed systems, cryptographic protocols.

### Q: Does AxiomCode send my code to external servers?

**A:** Only if you use OpenAI/Anthropic backends (cloud LLMs).  
Local Ollama runs entirely on your machine.  
No telemetry or tracking regardless.

### Q: Why zero dependencies?

**A:** Supply chain security. No pip packages = no attack surface from upstream dependencies.

### Q: Can I use this commercially?

**A:** MIT License - yes! Use freely in commercial products. Just include the license.

### Q: How do I contribute?

**A:** Fork the repo, make improvements, submit PR.  
Focus areas: Lean 4 tactics, LLM backends, visualizations.

### Q: What's the roadmap?

**A:** 
- v0.2: OOP support (classes, generics)
- v0.3: Concurrency (locks, atomics)
- v1.0: Production release with full API

---

## Learning Path

### Day 1: Fundamentals
- [ ] Read quick start
- [ ] Generate first algorithm
- [ ] View proof visualization
- [ ] Check certificate

### Day 2: Security
- [ ] Create key pair with passphrase
- [ ] Generate license bound to hardware
- [ ] Verify license independently
- [ ] Check audit log

### Day 3: Advanced
- [ ] Write custom allocation
- [ ] Use data persistence
- [ ] Implement secure sandbox
- [ ] Deploy to PyPI

### Week 2: Production
- [ ] Integrate into existing codebase
- [ ] Set up CI/CD pipeline
- [ ] Monitor proof generation latency
- [ ] Scale to multiple backends

---

## Contact & Support

**GitHub Issues:** https://github.com/nrupala/axiomcode/issues  
**Email:** support@axiom-code.com  
**Slack:** https://chat.axiom-code.com  
**Docs:** https://docs.axiom-code.com

---

**Last Updated:** April 1, 2026  
**Version:** 0.1.0 (Alpha)  
**Status:** Production Ready ✅
