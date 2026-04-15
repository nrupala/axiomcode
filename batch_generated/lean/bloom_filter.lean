import Mathlib
import Aesop



/-- implement a bloom filter with multiple hash functions, prove it never produces false negatives and has bounded false positive rate -/
theorem bloom_filter_correct (l : List Nat) (x : Nat) :
  Sorted l → (bloom_filter l x = some i ↔ l[i]! = x) := by sorry