import Algorithms.InsertionSort
import Algorithms.Gcd
import Algorithms.RangeSum
import Algorithms.Trie
import Algorithms.LruCache
import Algorithms.QuickSort
import Algorithms.CountingSort
import Algorithms.RadixSort
import Algorithms.QuickSelect
import Algorithms.RotatedSearch
import Algorithms.BubbleSort
import Algorithms.BinarySearch
import Algorithms.GasStation
import Algorithms.LargestRectangle
import Algorithms.ProductExceptSelf
import Algorithms.InsertInterval
import Algorithms.RainWater
import Algorithms.Spiral
import Algorithms.MaximalSquare
import Algorithms.Candy
import Algorithms.MergeIntervals
import Algorithms.PreviousPermutation
import Algorithms.Fibonacci
import Algorithms.Kadane
import Algorithms.JumpGame
import Algorithms.Graph
import Algorithms.TopologicalSort
import Algorithms.BellmanFord
import Algorithms.FloydWarshall

/-!
# AxiomCode — Verified Algorithms Library

Root module for the promoted algorithm entries (L2 library depth). Each
entry lives in `src/Algorithms/<Name>.lean` and is registered here by an
import; the lakefile's `AxiomCode` library roots include `Algorithms`, so
every module imported above is built and machine-checked by
`lake build AxiomCode`. Promotion follows `lean/PROMOTION.md`.
-/
