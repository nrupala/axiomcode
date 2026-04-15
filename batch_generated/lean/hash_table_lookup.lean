import Mathlib
import Aesop



/-- implement a hash table with chaining for collision resolution, prove lookup returns the correct value for any inserted key -/
theorem hash_table_lookup_correct (l : List Nat) (x : Nat) :
  Sorted l → (hash_table_lookup l x = some i ↔ l[i]! = x) := by sorry