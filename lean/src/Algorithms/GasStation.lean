import Spec
import Tactics

/-!
# AxiomCode — Verified Gas Station (refuel invariant)

Promoted from `lean/drafts/gas_station_invariant_preserved.lean` under
the L2 promotion procedure (`lean/PROMOTION.md`). The draft's shells
are authored for real: the structure gains the fields its own
statements reference (`fuelAmount`, `maxFuelCapacity`), the
`.invariant` its first theorem names becomes the def
`GasStation.invariant` (fuel never exceeds capacity), and
`gas_station_refuel` gains its body: refuelling adds the amount,
capped at capacity.

Statement honesty: both draft statements are TRUE as intended once
the shells are authored, and both are carried in their exact shapes —
the invariant theorem under its draft name, and the draft's second
theorem (whose own proof in the draft is `apply
gas_station_invariant_preserved`) under `GasStation.algorithm_correctness`
(the bare name `algorithm_correctness` is shared by several drafts and
is namespaced under the structure, per the LRU precedent). Its proof
here is likewise the invariant theorem applied.
-/

namespace AxiomCode

/-- A fuel tank: the current fuel amount and the maximum capacity. -/
structure GasStation where
  fuelAmount : Nat
  maxFuelCapacity : Nat
deriving DecidableEq, Repr

/-- The tank invariant: fuel never exceeds capacity. -/
def GasStation.invariant (s : GasStation) : Prop :=
  s.fuelAmount ≤ s.maxFuelCapacity

/-- Refuel by `amount`, capped at the tank's capacity. -/
def gas_station_refuel (s : GasStation) (amount : Nat) : GasStation :=
  ⟨Nat.min (s.fuelAmount + amount) s.maxFuelCapacity, s.maxFuelCapacity⟩

/-- Refuelling preserves the invariant — unconditionally, since the
refuel caps at capacity. -/
theorem gas_station_invariant_preserved :
    ∀ s : GasStation, ∀ amount : Nat, (gas_station_refuel s amount).invariant := by
  intro s amount
  exact Nat.min_le_right _ _

/-- The draft's second theorem, in its exact shape: after a refuel the
fuel amount is within capacity. -/
theorem GasStation.algorithm_correctness :
    ∀ s : GasStation, ∀ amount : Nat,
      (gas_station_refuel s amount).fuelAmount ≤
        (gas_station_refuel s amount).maxFuelCapacity := by
  intro s amount
  exact gas_station_invariant_preserved s amount

end AxiomCode
