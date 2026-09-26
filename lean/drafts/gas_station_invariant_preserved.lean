import Mathlib
import Aesop

structure GasStation where

def gas_station_refuel (station : GasStation) (amount : Nat) : GasStation :=

/--  -/
theorem gas_station_invariant_preserved : ∀ s : GasStation, ∀ amount : Nat, (gas_station_refuel s amount).invariant :=
  sorry

theorem algorithm_correctness : ∀ s : GasStation, ∀ amount : Nat, (gas_station_refuel s amount).fuelAmount ≤ (gas_station_refuel s amount).maxFuelCapacity :=
  by
    intros s amount
    apply gas_station_invariant_preserved