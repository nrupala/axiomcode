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

/-!
# AxiomCode — Verified Algorithms Library

Root module for the promoted algorithm entries (L2 library depth). Each
entry lives in `src/Algorithms/<Name>.lean` and is registered here by an
import; the lakefile's `AxiomCode` library roots include `Algorithms`, so
every module imported above is built and machine-checked by
`lake build AxiomCode`. Promotion follows `lean/PROMOTION.md`.
-/
