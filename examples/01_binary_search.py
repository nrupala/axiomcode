"""
Example 1: Binary Search — the simplest verified algorithm.

Run: axiomcode "implement binary search on a sorted array that returns the index of the target element"
"""

# What AxiomCode generates internally:
#
# import Mathlib
# import Aesop
#
# /-- Binary search on a sorted list. Returns the index of x if present, none otherwise. -/
# theorem binary_search_correct (l : List Nat) (x : Nat) :
#     Sorted l →
#     (binarySearch l x = some i ↔ l[i]! = x ∧ i < l.length) := by sorry
#
# After proof search completes:
# - C binary: build/c/binary_search.so
# - Python wheel: build/python/axiomcode_binary_search-0.1.0-py3-none-any.whl
#
# Usage in Python:
#   from axiomcode_binary_search import binary_search
#   idx = binary_search([1, 3, 5, 7, 9], 5)
#   print(idx)  # 2
