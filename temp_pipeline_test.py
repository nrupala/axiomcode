from cli import _parse_spec, run_proof

raw = '''```lean
import Mathlib
import Aesop

/-- Binary search specification -/
theorem binary_search_correct : True := by sorry
```'''

spec = _parse_spec(raw, 'implement binary search', 123.4, 'local')
print('Spec imports:', spec.imports)
print('Spec theorem:', spec.theorem)
proof = run_proof(spec)
print('Proof theorem:', proof.theorem_name)
print('Proof tactics:', proof.tactics)
print('Proof hash:', proof.proof_hash)
