import Mathlib
import Aesop

structure MonteCarloPiConfig where

def in_unit_circle (x y : Float) : Bool :=

def monte_carlo_pi (config : MonteCarloPiConfig) : Float := 

/--  -/
theorem monte_carlo_pi_correctness : ∀ (config : MonteCarloPiConfig), 
  |monte_carlo_pi config - π| ≤ 2 * sqrt ((π / 4) * (1 - π / 4) / config.num_samples.toFloat) := by sorry