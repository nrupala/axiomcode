import Spec
import Tactics

/-!
# AxiomCode — Verified LRU Cache

A formally verified LRU (least-recently-used) cache: insert with
eviction, the key-uniqueness invariant and its preservation, and the
fold-level correctness statement.

Promoted from
`lean/drafts/lru_cache.invariant_preserved_insert {key value} (cache.lean`
under the L2 promotion procedure (`lean/PROMOTION.md`). The draft's
shells are authored for real: the structure gains its fields
(`capacity`, and the entry list `cache`, most-recently-used first —
the field name is the draft's own, from its `cache.cache` references),
`empty` gains its body, and `insert` is the LRU discipline: remove any
old entry for the key, prepend the new entry, truncate to capacity
(the truncation is the eviction, and it is what keeps the size within
capacity even at capacity `0`). `insert` needs `DecidableEq Key` —
comparing keys is what an LRU insert *is* — which the draft's
unconstrained `{Key Value}` could not supply.

Statement 1 defect, recorded not silently repaired: as written, the
draft's `invariant_preserved_insert` states its proposition about the
*input* cache — `insert` appears nowhere in it — and with no hypothesis
it is **false as stated**: the cache `⟨2, [(k, v')]⟩` with `v' ≠ v`
refutes it (take `k' = k`, `v'`: both disjuncts fail). The theorem is
carried with the subject the name claims — the *result* of the insert —
in the draft's exact proposition shape, and the general preservation
theorem (`LRU_Cache.insert_keyUnique`: insert preserves the
key-uniqueness invariant) is proved alongside it.

Statement 2 is carried in the draft's own shape with the authoring the
shells force: `length`/`range` are `List.length`/`List.range`; the
fold's `keys[j]` / `values[j]` are `keys[j]!` / `values[j]!` (the
proof-carrying `getElem` cannot elaborate inside the fold lambda, whose
bound `j` carries no range proof; the `!` form needs the `Inhabited`
instances the theorem therefore carries). The theorem is named
`LRU_Cache.algorithm_correctness` — the draft's bare name is also the
range-sum draft's theorem name, and both are namespaced under their
structures (compare `RangeSumQuery.algorithm_correctness`).
-/

namespace AxiomCode

/-- An LRU (least-recently-used) cache: a capacity bound and the cached
entries, most-recently-used first. -/
structure LRU_Cache (Key : Type) (Value : Type) where
  capacity : Nat
  cache : List (Key × Value)
deriving DecidableEq, Repr

/-- The empty cache with the given capacity. -/
def LRU_Cache.empty {Key Value : Type} (capacity : Nat) : LRU_Cache Key Value :=
  ⟨capacity, []⟩

/-- Remove every entry for key `k` from an entry list. -/
def removeKey {Key Value : Type} [DecidableEq Key] (k : Key) :
    List (Key × Value) → List (Key × Value)
  | [] => []
  | (k', v') :: rest =>
    if k' = k then removeKey k rest else (k', v') :: removeKey k rest

/-- Insert `(k, v)`: any old entry for `k` is removed, the new entry goes
to the front (most recently used), and the result is truncated to the
capacity — the truncation is what evicts the least-recently-used entry,
and it keeps the size within capacity even at capacity `0`. -/
def LRU_Cache.insert {Key Value : Type} [DecidableEq Key]
    (c : LRU_Cache Key Value) (k : Key) (v : Value) : LRU_Cache Key Value :=
  ⟨c.capacity, ((k, v) :: removeKey k c.cache).take c.capacity⟩

/-- The cache invariant: each key carries at most one value. -/
def LRU_Cache.KeyUnique {Key Value : Type} (c : LRU_Cache Key Value) : Prop :=
  ∀ k v₁ v₂, (k, v₁) ∈ c.cache → (k, v₂) ∈ c.cache → v₁ = v₂

theorem mem_removeKey {Key Value : Type} [DecidableEq Key] {k : Key}
    {p : Key × Value} {es : List (Key × Value)} :
    p ∈ removeKey k es → p ∈ es ∧ p.1 ≠ k := by
  induction es with
  | nil => simp [removeKey]
  | cons e es ih =>
    obtain ⟨k', v'⟩ := e
    by_cases h : k' = k
    · have h1 : removeKey k ((k', v') :: es) = removeKey k es := by
        simp [removeKey, h]
      intro hmem
      rw [h1] at hmem
      obtain ⟨h2, h3⟩ := ih hmem
      exact ⟨List.Mem.tail _ h2, h3⟩
    · have h1 : removeKey k ((k', v') :: es)
          = (k', v') :: removeKey k es := by
        simp [removeKey, h]
      intro hmem
      rw [h1] at hmem
      cases hmem with
      | head es =>
        exact ⟨List.Mem.head es, by simpa using h⟩
      | tail _ hmem =>
        obtain ⟨h2, h3⟩ := ih hmem
        exact ⟨List.Mem.tail _ h2, h3⟩

/-- Every entry of an insert result is either the inserted pair or an old
entry whose key differs from the inserted key. -/
theorem insert_entries {Key Value : Type} [DecidableEq Key]
    (c : LRU_Cache Key Value) (k : Key) (v : Value) (p : Key × Value) :
    p ∈ (LRU_Cache.insert c k v).cache →
      p = (k, v) ∨ (p ∈ c.cache ∧ p.1 ≠ k) := by
  intro hmem
  have h1 : p ∈ (k, v) :: removeKey k c.cache :=
    List.mem_of_mem_take hmem
  cases h1 with
  | head _ => exact Or.inl rfl
  | tail _ h2 =>
    exact Or.inr (mem_removeKey h2)

/-- Insert preserves the key-uniqueness invariant. -/
theorem LRU_Cache.insert_keyUnique {Key Value : Type} [DecidableEq Key]
    (c : LRU_Cache Key Value) (k : Key) (v : Value)
    (h : c.KeyUnique) : (LRU_Cache.insert c k v).KeyUnique := by
  intro k₁ v₁ v₂ h1 h2
  rcases insert_entries c k v (k₁, v₁) h1 with he | ⟨hm1, hk1⟩
  · rcases insert_entries c k v (k₁, v₂) h2 with he2 | ⟨hm2, hk2⟩
    · have e1 : v₁ = v := congrArg Prod.snd he
      have e2 : v₂ = v := congrArg Prod.snd he2
      rw [e1, e2]
    · -- (k₁, v₂) is an old entry with key ≠ k, but he gives k₁ = k.
      exact absurd (congrArg Prod.fst he) hk2
  · rcases insert_entries c k v (k₁, v₂) h2 with he2 | ⟨hm2, hk2⟩
    · exact absurd (congrArg Prod.fst he2) hk1
    · exact h k₁ v₁ v₂ hm1 hm2

/-- The size of an insert result is within the cache's capacity. -/
theorem LRU_Cache.insert_length_le {Key Value : Type} [DecidableEq Key]
    (c : LRU_Cache Key Value) (k : Key) (v : Value) :
    (LRU_Cache.insert c k v).cache.length ≤ c.capacity := by
  show (((k, v) :: removeKey k c.cache).take c.capacity).length ≤ c.capacity
  rw [List.length_take]
  exact Nat.min_le_left _ _

/-- Insert does not change the capacity. -/
theorem LRU_Cache.insert_capacity {Key Value : Type} [DecidableEq Key]
    (c : LRU_Cache Key Value) (k : Key) (v : Value) :
    (LRU_Cache.insert c k v).capacity = c.capacity :=
  rfl

/-- The draft's first statement, with its subject repaired to the insert
result (see the module doc for the defect and the counterexample): after
inserting `(k, v)`, the only value stored at key `k` is `v`. -/
theorem LRU_Cache.invariant_preserved_insert {Key Value : Type} [DecidableEq Key]
    (cache : LRU_Cache Key Value) (k : Key) (v : Value) :
    (∀ k' v', (k', v') ∈ (LRU_Cache.insert cache k v).cache →
      k ≠ k' ∨ v = v') := by
  intro k' v' hmem
  rcases insert_entries cache k v (k', v') hmem with he | ⟨_, hk⟩
  · right
    have e : v' = v := congrArg Prod.snd he
    exact e.symm
  · left
    exact hk.symm

/-- The draft's second statement: folding the first `i` key/value pairs
into an empty cache yields a cache within capacity and with unique
keys, in the draft's own invariant shape. -/
theorem LRU_Cache.algorithm_correctness {Key Value : Type} [DecidableEq Key]
    [Inhabited Key] [Inhabited Value]
    (capacity : Nat) (keys : List Key) (values : List Value) :
    ∀ i, i < keys.length →
      let cache := List.foldl (fun acc j => LRU_Cache.insert acc keys[j]! values[j]!)
        (LRU_Cache.empty capacity) (List.range i)
      (∀ k v, (k, v) ∈ cache.cache →
        cache.cache.length ≤ capacity ∧
          (∀ k' v', (k', v') ∈ cache.cache → k ≠ k' ∨ v = v')) := by
  have key : ∀ i,
      (List.foldl (fun acc j => LRU_Cache.insert acc keys[j]! values[j]!)
        (LRU_Cache.empty capacity) (List.range i)).KeyUnique
      ∧ (List.foldl (fun acc j => LRU_Cache.insert acc keys[j]! values[j]!)
          (LRU_Cache.empty capacity) (List.range i)).cache.length ≤ capacity
      ∧ (List.foldl (fun acc j => LRU_Cache.insert acc keys[j]! values[j]!)
          (LRU_Cache.empty capacity) (List.range i)).capacity = capacity := by
    intro i
    induction i with
    | zero =>
      refine ⟨?_, ?_, rfl⟩
      · intro k v₁ v₂ h1 _
        simp [LRU_Cache.empty] at h1
      · simp [LRU_Cache.empty]
    | succ i ih =>
      obtain ⟨huniq, hlen, hcap⟩ := ih
      have hrange : List.range (i + 1) = List.range i ++ [i] :=
        List.range_succ
      have hfold : List.foldl
            (fun acc j => LRU_Cache.insert acc keys[j]! values[j]!)
            (LRU_Cache.empty capacity) (List.range (i + 1))
          = LRU_Cache.insert
              (List.foldl (fun acc j => LRU_Cache.insert acc keys[j]! values[j]!)
                (LRU_Cache.empty capacity) (List.range i))
              keys[i]! values[i]! := by
        rw [hrange, List.foldl_append, List.foldl_cons, List.foldl_nil]
      rw [hfold]
      refine ⟨?_, ?_, ?_⟩
      · exact LRU_Cache.insert_keyUnique _ _ _ huniq
      · have hle := LRU_Cache.insert_length_le
          (List.foldl (fun acc j => LRU_Cache.insert acc keys[j]! values[j]!)
            (LRU_Cache.empty capacity) (List.range i)) keys[i]! values[i]!
        rw [hcap] at hle
        exact hle
      · rw [LRU_Cache.insert_capacity, hcap]
  intro i _
  obtain ⟨huniq, hlen, _⟩ := key i
  show ∀ k v, (k, v) ∈ (List.foldl
        (fun acc j => LRU_Cache.insert acc keys[j]! values[j]!)
        (LRU_Cache.empty capacity) (List.range i)).cache →
      (List.foldl (fun acc j => LRU_Cache.insert acc keys[j]! values[j]!)
        (LRU_Cache.empty capacity) (List.range i)).cache.length ≤ capacity ∧
        (∀ k' v', (k', v') ∈ (List.foldl
          (fun acc j => LRU_Cache.insert acc keys[j]! values[j]!)
          (LRU_Cache.empty capacity) (List.range i)).cache →
            k ≠ k' ∨ v = v')
  intro k v hmem
  refine ⟨hlen, ?_⟩
  intro k' v' hmem'
  by_cases hkk : k = k'
  · right
    exact huniq k v v' hmem (hkk ▸ hmem')
  · left
    exact hkk

end AxiomCode
