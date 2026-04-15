import Mathlib
import Aesop



/-- implement Catalan number computation, prove C(n) = C(2n,n)/(n+1) and satisfies the recurrence C(n) = sum(C(i)*C(n-1-i)) for i in 0..n-1 -/
theorem catalan_number_correct (n : Nat) : True := by sorry