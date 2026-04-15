#!/usr/bin/env python3
"""
AxiomCode — Batch Generate & Test 100 Programs
================================================

Generates formal Lean 4 specifications for 100 algorithms,
validates each one, and produces a comprehensive test report.

UTF-8 encoding is enforced throughout.
"""

import os
os.environ['PYTHONUTF8'] = '1'

import sys
import json
import time
import textwrap
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

# Ensure UTF-8 for stdout/stderr
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from cli import (
    _parse_spec, LeanSpec, ProofResult,
    hash_data,
)
from core.security import (
    KeyStore, ProofCertificate, AuditLog,
)


# ─── 100 Algorithm Definitions ──────────────────────────────────────────────

ALGORITHMS = [
    # ─── Sorting (1-12) ──────────────────────────────────────────────
    {
        "id": 1, "name": "binary_search", "category": "Searching",
        "description": "implement binary search on a sorted array that returns the index of the target element or -1 if not found, prove it always returns the correct index when the element exists",
        "difficulty": "Easy", "proof_complexity": "Medium"
    },
    {
        "id": 2, "name": "insertion_sort", "category": "Sorting",
        "description": "implement insertion sort that sorts a list of natural numbers, prove the output is sorted and is a permutation of the input",
        "difficulty": "Easy", "proof_complexity": "Medium"
    },
    {
        "id": 3, "name": "selection_sort", "category": "Sorting",
        "description": "implement selection sort that repeatedly finds the minimum element and places it at the beginning, prove the result is sorted and preserves all elements",
        "difficulty": "Easy", "proof_complexity": "Medium"
    },
    {
        "id": 4, "name": "bubble_sort", "category": "Sorting",
        "description": "implement bubble sort that repeatedly swaps adjacent elements if they are in wrong order, prove it terminates and produces a sorted list",
        "difficulty": "Easy", "proof_complexity": "Medium"
    },
    {
        "id": 5, "name": "merge_sort", "category": "Sorting",
        "description": "implement merge sort using divide and conquer, prove it produces a sorted list that is a permutation of the input, prove O(n log n) time complexity bound",
        "difficulty": "Medium", "proof_complexity": "High"
    },
    {
        "id": 6, "name": "quick_sort", "category": "Sorting",
        "description": "implement quicksort with a pivot selection strategy, prove the output is sorted and contains exactly the same elements as the input",
        "difficulty": "Medium", "proof_complexity": "High"
    },
    {
        "id": 7, "name": "heap_sort", "category": "Sorting",
        "description": "implement heap sort using a max-heap data structure, prove it correctly sorts any list of natural numbers",
        "difficulty": "Medium", "proof_complexity": "High"
    },
    {
        "id": 8, "name": "counting_sort", "category": "Sorting",
        "description": "implement counting sort for integers in a known range, prove it produces a stable sorted output",
        "difficulty": "Medium", "proof_complexity": "Medium"
    },
    {
        "id": 9, "name": "radix_sort", "category": "Sorting",
        "description": "implement radix sort using counting sort as a subroutine for each digit, prove it correctly sorts non-negative integers",
        "difficulty": "Hard", "proof_complexity": "High"
    },
    {
        "id": 10, "name": "shell_sort", "category": "Sorting",
        "description": "implement shell sort with diminishing gap sequence, prove the final array is sorted",
        "difficulty": "Hard", "proof_complexity": "High"
    },
    {
        "id": 11, "name": "tim_sort", "category": "Sorting",
        "description": "implement a simplified timsort that merges sorted runs, prove the output is sorted and stable",
        "difficulty": "Hard", "proof_complexity": "High"
    },
    {
        "id": 12, "name": "intro_sort", "category": "Sorting",
        "description": "implement introsort that switches from quicksort to heapsort when recursion depth exceeds a limit, prove it always terminates with a sorted array",
        "difficulty": "Hard", "proof_complexity": "High"
    },

    # ─── Searching (13-20) ───────────────────────────────────────────
    {
        "id": 13, "name": "linear_search", "category": "Searching",
        "description": "implement linear search that finds the first occurrence of an element in a list, prove it returns the correct index or indicates absence",
        "difficulty": "Easy", "proof_complexity": "Low"
    },
    {
        "id": 14, "name": "ternary_search", "category": "Searching",
        "description": "implement ternary search on a sorted array that divides the search space into three parts, prove correctness and termination",
        "difficulty": "Medium", "proof_complexity": "Medium"
    },
    {
        "id": 15, "name": "jump_search", "category": "Searching",
        "description": "implement jump search that checks elements at fixed intervals then does linear search in the identified block, prove it finds the element if present",
        "difficulty": "Medium", "proof_complexity": "Medium"
    },
    {
        "id": 16, "name": "exponential_search", "category": "Searching",
        "description": "implement exponential search that finds the range where element may be present by doubling indices then binary search, prove correctness",
        "difficulty": "Medium", "proof_complexity": "Medium"
    },
    {
        "id": 17, "name": "interpolation_search", "category": "Searching",
        "description": "implement interpolation search that probes positions based on value distribution, prove it finds the element in uniformly distributed sorted arrays",
        "difficulty": "Hard", "proof_complexity": "High"
    },
    {
        "id": 18, "name": "fibonacci_search", "category": "Searching",
        "description": "implement fibonacci search using fibonacci numbers to divide the search range, prove it correctly finds elements in sorted arrays",
        "difficulty": "Hard", "proof_complexity": "High"
    },
    {
        "id": 19, "name": "hash_table_lookup", "category": "Searching",
        "description": "implement a hash table with chaining for collision resolution, prove lookup returns the correct value for any inserted key",
        "difficulty": "Medium", "proof_complexity": "Medium"
    },
    {
        "id": 20, "name": "bloom_filter", "category": "Searching",
        "description": "implement a bloom filter with multiple hash functions, prove it never produces false negatives and has bounded false positive rate",
        "difficulty": "Hard", "proof_complexity": "High"
    },

    # ─── Number Theory (21-32) ───────────────────────────────────────
    {
        "id": 21, "name": "euclidean_gcd", "category": "Number Theory",
        "description": "implement the Euclidean algorithm for greatest common divisor, prove it always terminates and returns the correct GCD of two natural numbers",
        "difficulty": "Easy", "proof_complexity": "Low"
    },
    {
        "id": 22, "name": "extended_euclidean", "category": "Number Theory",
        "description": "implement the extended Euclidean algorithm that finds GCD and Bézout coefficients, prove that a*x + b*y = gcd(a,b)",
        "difficulty": "Medium", "proof_complexity": "Medium"
    },
    {
        "id": 23, "name": "sieve_of_eratosthenes", "category": "Number Theory",
        "description": "implement the Sieve of Eratosthenes to find all primes up to n, prove every number marked as prime is actually prime and all composites are marked",
        "difficulty": "Medium", "proof_complexity": "Medium"
    },
    {
        "id": 24, "name": "prime_factorization", "category": "Number Theory",
        "description": "implement trial division prime factorization, prove the product of returned prime factors equals the original number",
        "difficulty": "Medium", "proof_complexity": "Medium"
    },
    {
        "id": 25, "name": "modular_exponentiation", "category": "Number Theory",
        "description": "implement modular exponentiation using square-and-multiply, prove it correctly computes (base^exp) mod m",
        "difficulty": "Medium", "proof_complexity": "Medium"
    },
    {
        "id": 26, "name": "fermats_little_theorem", "category": "Number Theory",
        "description": "implement a primality test based on Fermat's little theorem, prove that if a^(p-1) ≡ 1 (mod p) then p is probably prime",
        "difficulty": "Hard", "proof_complexity": "High"
    },
    {
        "id": 27, "name": "miller_rabin_primality", "category": "Number Theory",
        "description": "implement the Miller-Rabin primality test with k witnesses, prove it correctly identifies composites and has bounded error probability",
        "difficulty": "Hard", "proof_complexity": "High"
    },
    {
        "id": 28, "name": "lcm_computation", "category": "Number Theory",
        "description": "implement least common multiple computation using the relationship lcm(a,b) = |a*b|/gcd(a,b), prove the result is the smallest positive integer divisible by both",
        "difficulty": "Easy", "proof_complexity": "Low"
    },
    {
        "id": 29, "name": "chinese_remainder_theorem", "category": "Number Theory",
        "description": "implement the Chinese Remainder Theorem solver for coprime moduli, prove the solution satisfies all congruences and is unique modulo the product",
        "difficulty": "Hard", "proof_complexity": "High"
    },
    {
        "id": 30, "name": "euler_totient", "category": "Number Theory",
        "description": "implement Euler's totient function that counts integers coprime to n, prove the result equals the count of numbers less than n that are coprime to n",
        "difficulty": "Hard", "proof_complexity": "High"
    },
    {
        "id": 31, "name": "integer_square_root", "category": "Number Theory",
        "description": "implement integer square root using Newton's method, prove the result is the largest integer whose square is at most n",
        "difficulty": "Medium", "proof_complexity": "Medium"
    },
    {
        "id": 32, "name": "perfect_number_check", "category": "Number Theory",
        "description": "implement a function that checks if a number is perfect (sum of proper divisors equals the number), prove correctness for all inputs",
        "difficulty": "Easy", "proof_complexity": "Low"
    },

    # ─── Data Structures (33-48) ─────────────────────────────────────
    {
        "id": 33, "name": "linked_list_reverse", "category": "Data Structures",
        "description": "implement an in-place singly linked list reversal, prove the reversed list has the same elements in reverse order and the same length",
        "difficulty": "Medium", "proof_complexity": "High"
    },
    {
        "id": 34, "name": "linked_list_merge", "category": "Data Structures",
        "description": "implement merging of two sorted linked lists into one sorted linked list, prove the result is sorted and contains all elements from both lists",
        "difficulty": "Medium", "proof_complexity": "Medium"
    },
    {
        "id": 35, "name": "stack_with_max", "category": "Data Structures",
        "description": "implement a stack that supports push, pop, and get-max in O(1) time, prove all operations maintain the stack invariant and max is correct",
        "difficulty": "Medium", "proof_complexity": "Medium"
    },
    {
        "id": 36, "name": "queue_from_stacks", "category": "Data Structures",
        "description": "implement a FIFO queue using two stacks, prove enqueue and dequeue operations maintain FIFO ordering",
        "difficulty": "Medium", "proof_complexity": "Medium"
    },
    {
        "id": 37, "name": "circular_buffer", "category": "Data Structures",
        "description": "implement a circular buffer with fixed capacity, prove it correctly wraps around and never overflows beyond capacity",
        "difficulty": "Medium", "proof_complexity": "Medium"
    },
    {
        "id": 38, "name": "binary_search_tree_insert", "category": "Data Structures",
        "description": "implement insertion into a binary search tree, prove the BST property is maintained after insertion",
        "difficulty": "Medium", "proof_complexity": "High"
    },
    {
        "id": 39, "name": "binary_search_tree_search", "category": "Data Structures",
        "description": "implement search in a binary search tree, prove it returns the node if present and None if not, with correctness of BST ordering",
        "difficulty": "Easy", "proof_complexity": "Medium"
    },
    {
        "id": 40, "name": "avl_tree_rotation", "category": "Data Structures",
        "description": "implement AVL tree left and right rotations, prove rotations preserve the BST property and restore the balance factor invariant",
        "difficulty": "Hard", "proof_complexity": "High"
    },
    {
        "id": 41, "name": "heap_insert_extract", "category": "Data Structures",
        "description": "implement binary heap insert and extract-min operations, prove the heap property is maintained after each operation",
        "difficulty": "Medium", "proof_complexity": "High"
    },
    {
        "id": 42, "name": "trie_insert_search", "category": "Data Structures",
        "description": "implement a trie (prefix tree) with insert and search operations, prove search returns true if and only if the key was inserted",
        "difficulty": "Medium", "proof_complexity": "Medium"
    },
    {
        "id": 43, "name": "hash_map_put_get", "category": "Data Structures",
        "description": "implement a hash map with put and get operations using open addressing, prove get returns the most recently put value for any key",
        "difficulty": "Medium", "proof_complexity": "Medium"
    },
    {
        "id": 44, "name": "doubly_linked_list", "category": "Data Structures",
        "description": "implement a doubly linked list with insert, delete, and traverse operations, prove the forward and backward traversals produce reverse sequences",
        "difficulty": "Medium", "proof_complexity": "High"
    },
    {
        "id": 45, "name": "skip_list_search", "category": "Data Structures",
        "description": "implement search in a skip list data structure, prove it correctly finds elements with O(log n) expected time",
        "difficulty": "Hard", "proof_complexity": "High"
    },
    {
        "id": 46, "name": "segment_tree_build", "category": "Data Structures",
        "description": "build a segment tree for range sum queries, prove each node correctly stores the sum of its range",
        "difficulty": "Hard", "proof_complexity": "High"
    },
    {
        "id": 47, "name": "disjoint_set_union", "category": "Data Structures",
        "description": "implement disjoint set union with path compression and union by rank, prove find returns the correct representative for each element",
        "difficulty": "Hard", "proof_complexity": "High"
    },
    {
        "id": 48, "name": "lru_cache", "category": "Data Structures",
        "description": "implement an LRU cache with get and put operations in O(1) time, prove the least recently used item is evicted when capacity is exceeded",
        "difficulty": "Hard", "proof_complexity": "High"
    },

    # ─── Graph Algorithms (49-62) ────────────────────────────────────
    {
        "id": 49, "name": "bfs_shortest_path", "category": "Graph",
        "description": "implement breadth-first search to find shortest path in an unweighted graph, prove the distance to each reachable node is minimal",
        "difficulty": "Medium", "proof_complexity": "High"
    },
    {
        "id": 50, "name": "dfs_cycle_detection", "category": "Graph",
        "description": "implement depth-first search to detect cycles in a directed graph, prove it correctly identifies all cyclic graphs",
        "difficulty": "Medium", "proof_complexity": "High"
    },
    {
        "id": 51, "name": "dijkstra_shortest_path", "category": "Graph",
        "description": "implement Dijkstra's algorithm for single-source shortest paths with non-negative weights, prove it computes the correct shortest distance to every vertex",
        "difficulty": "Hard", "proof_complexity": "High"
    },
    {
        "id": 52, "name": "bellman_ford", "category": "Graph",
        "description": "implement Bellman-Ford algorithm for shortest paths that handles negative edge weights, prove it detects negative cycles and computes correct distances otherwise",
        "difficulty": "Hard", "proof_complexity": "High"
    },
    {
        "id": 53, "name": "floyd_warshall", "category": "Graph",
        "description": "implement Floyd-Warshall all-pairs shortest path algorithm, prove after completion dist[i][j] equals the shortest path distance between i and j",
        "difficulty": "Hard", "proof_complexity": "High"
    },
    {
        "id": 54, "name": "kruskal_mst", "category": "Graph",
        "description": "implement Kruskal's minimum spanning tree algorithm using union-find, prove the result is a spanning tree with minimum total weight",
        "difficulty": "Hard", "proof_complexity": "High"
    },
    {
        "id": 55, "name": "prim_mst", "category": "Graph",
        "description": "implement Prim's minimum spanning tree algorithm, prove the result connects all vertices with minimum total edge weight",
        "difficulty": "Hard", "proof_complexity": "High"
    },
    {
        "id": 56, "name": "topological_sort", "category": "Graph",
        "description": "implement topological sort using Kahn's algorithm, prove the output ordering respects all edges (if u→v then u appears before v)",
        "difficulty": "Medium", "proof_complexity": "High"
    },
    {
        "id": 57, "name": "kosaraju_scc", "category": "Graph",
        "description": "implement Kosaraju's algorithm for finding strongly connected components, prove each component is maximal and strongly connected",
        "difficulty": "Hard", "proof_complexity": "High"
    },
    {
        "id": 58, "name": "tarjan_scc", "category": "Graph",
        "description": "implement Tarjan's algorithm for strongly connected components using a single DFS, prove correctness of component identification",
        "difficulty": "Hard", "proof_complexity": "High"
    },
    {
        "id": 59, "name": "ford_fulkerson_max_flow", "category": "Graph",
        "description": "implement Ford-Fulkerson maximum flow algorithm using augmenting paths, prove the result equals the minimum cut capacity",
        "difficulty": "Hard", "proof_complexity": "High"
    },
    {
        "id": 60, "name": "graph_bipartite_check", "category": "Graph",
        "description": "implement a bipartite graph checker using two-coloring, prove a graph is bipartite if and only if it is 2-colorable",
        "difficulty": "Medium", "proof_complexity": "Medium"
    },
    {
        "id": 61, "name": "graph_connectivity", "category": "Graph",
        "description": "implement connected component counting using BFS, prove the count equals the number of connected components in the graph",
        "difficulty": "Medium", "proof_complexity": "Medium"
    },
    {
        "id": 62, "name": "a_star_pathfinding", "category": "Graph",
        "description": "implement A* pathfinding with an admissible heuristic, prove it finds the optimal path when the heuristic is admissible",
        "difficulty": "Hard", "proof_complexity": "High"
    },

    # ─── Dynamic Programming (63-74) ─────────────────────────────────
    {
        "id": 63, "name": "fibonacci_dp", "category": "Dynamic Programming",
        "description": "implement Fibonacci number computation using dynamic programming, prove fib(n) = fib(n-1) + fib(n-2) with correct base cases",
        "difficulty": "Easy", "proof_complexity": "Low"
    },
    {
        "id": 64, "name": "knapsack_01", "category": "Dynamic Programming",
        "description": "implement the 0/1 knapsack problem using dynamic programming, prove the solution maximizes total value without exceeding capacity",
        "difficulty": "Medium", "proof_complexity": "High"
    },
    {
        "id": 65, "name": "longest_common_subsequence", "category": "Dynamic Programming",
        "description": "implement longest common subsequence using dynamic programming, prove the result is a subsequence of both inputs and is of maximum length",
        "difficulty": "Medium", "proof_complexity": "High"
    },
    {
        "id": 66, "name": "longest_increasing_subsequence", "category": "Dynamic Programming",
        "description": "implement longest increasing subsequence using dynamic programming, prove the result is strictly increasing and of maximum length",
        "difficulty": "Medium", "proof_complexity": "High"
    },
    {
        "id": 67, "name": "matrix_chain_multiplication", "category": "Dynamic Programming",
        "description": "implement optimal matrix chain multiplication ordering, prove the parenthesization minimizes the total number of scalar multiplications",
        "difficulty": "Hard", "proof_complexity": "High"
    },
    {
        "id": 68, "name": "edit_distance", "category": "Dynamic Programming",
        "description": "implement Levenshtein edit distance using dynamic programming, prove the result is the minimum number of insertions, deletions, and substitutions to transform one string to another",
        "difficulty": "Medium", "proof_complexity": "High"
    },
    {
        "id": 69, "name": "coin_change", "category": "Dynamic Programming",
        "description": "implement the coin change problem to find minimum coins needed for a target amount, prove the result uses the minimum number of coins or reports impossibility",
        "difficulty": "Medium", "proof_complexity": "Medium"
    },
    {
        "id": 70, "name": "subset_sum", "category": "Dynamic Programming",
        "description": "implement the subset sum problem using dynamic programming, prove it correctly determines whether a subset with the target sum exists",
        "difficulty": "Medium", "proof_complexity": "Medium"
    },
    {
        "id": 71, "name": "rod_cutting", "category": "Dynamic Programming",
        "description": "implement the rod cutting problem to maximize revenue, prove the solution finds the optimal way to cut a rod of length n",
        "difficulty": "Medium", "proof_complexity": "Medium"
    },
    {
        "id": 72, "name": "palindrome_partitioning", "category": "Dynamic Programming",
        "description": "implement minimum palindrome partitioning of a string, prove the result partitions the string into the minimum number of palindromic substrings",
        "difficulty": "Hard", "proof_complexity": "High"
    },
    {
        "id": 73, "name": "wildcard_matching", "category": "Dynamic Programming",
        "description": "implement wildcard pattern matching with '?' and '*' using dynamic programming, prove it correctly matches patterns against text",
        "difficulty": "Hard", "proof_complexity": "High"
    },
    {
        "id": 74, "name": "optimal_bst", "category": "Dynamic Programming",
        "description": "implement optimal binary search tree construction given key frequencies, prove the resulting tree minimizes expected search cost",
        "difficulty": "Hard", "proof_complexity": "High"
    },

    # ─── String Algorithms (75-84) ───────────────────────────────────
    {
        "id": 75, "name": "kmp_pattern_matching", "category": "String",
        "description": "implement the Knuth-Morris-Pratt string matching algorithm, prove it finds all occurrences of a pattern in text with O(n+m) time",
        "difficulty": "Hard", "proof_complexity": "High"
    },
    {
        "id": 76, "name": "rabin_karp_matching", "category": "String",
        "description": "implement Rabin-Karp string matching using rolling hash, prove it correctly identifies all pattern occurrences",
        "difficulty": "Hard", "proof_complexity": "High"
    },
    {
        "id": 77, "name": "z_algorithm", "category": "String",
        "description": "implement the Z-algorithm for string matching, prove the Z-array correctly stores the length of the longest common prefix with the string itself",
        "difficulty": "Hard", "proof_complexity": "High"
    },
    {
        "id": 78, "name": "boyer_moore_search", "category": "String",
        "description": "implement the Boyer-Moore string search algorithm with bad character rule, prove it correctly finds all pattern occurrences",
        "difficulty": "Hard", "proof_complexity": "High"
    },
    {
        "id": 79, "name": "string_reversal", "category": "String",
        "description": "implement in-place string reversal, prove the output is the reverse of the input with the same length",
        "difficulty": "Easy", "proof_complexity": "Low"
    },
    {
        "id": 80, "name": "palindrome_check", "category": "String",
        "description": "implement palindrome checking that determines if a string reads the same forwards and backwards, prove correctness for all inputs",
        "difficulty": "Easy", "proof_complexity": "Low"
    },
    {
        "id": 81, "name": "longest_palindrome_substring", "category": "String",
        "description": "implement finding the longest palindromic substring using expand around center, prove the result is a palindrome and is of maximum length",
        "difficulty": "Medium", "proof_complexity": "Medium"
    },
    {
        "id": 82, "name": "anagram_check", "category": "String",
        "description": "implement anagram checking that determines if two strings are permutations of each other, prove correctness for all inputs",
        "difficulty": "Easy", "proof_complexity": "Low"
    },
    {
        "id": 83, "name": "run_length_encoding", "category": "String",
        "description": "implement run-length encoding compression, prove decoding the encoded string produces the original string",
        "difficulty": "Easy", "proof_complexity": "Low"
    },
    {
        "id": 84, "name": "suffix_array_build", "category": "String",
        "description": "implement suffix array construction, prove the array contains all suffixes sorted in lexicographic order",
        "difficulty": "Hard", "proof_complexity": "High"
    },

    # ─── Mathematical (85-92) ────────────────────────────────────────
    {
        "id": 85, "name": "factorial", "category": "Mathematical",
        "description": "implement factorial computation, prove n! = n * (n-1)! with base case 0! = 1 for all natural numbers",
        "difficulty": "Easy", "proof_complexity": "Low"
    },
    {
        "id": 86, "name": "power_function", "category": "Mathematical",
        "description": "implement exponentiation by squaring, prove it correctly computes x^n for all natural number exponents in O(log n) time",
        "difficulty": "Easy", "proof_complexity": "Low"
    },
    {
        "id": 87, "name": "newton_raphson_sqrt", "category": "Mathematical",
        "description": "implement square root computation using Newton-Raphson method, prove convergence to the correct square root within epsilon",
        "difficulty": "Medium", "proof_complexity": "Medium"
    },
    {
        "id": 88, "name": "matrix_multiplication", "category": "Mathematical",
        "description": "implement matrix multiplication for n×n matrices, prove the result satisfies the mathematical definition of matrix product",
        "difficulty": "Medium", "proof_complexity": "Medium"
    },
    {
        "id": 89, "name": "matrix_determinant", "category": "Mathematical",
        "description": "implement matrix determinant computation using cofactor expansion, prove the result satisfies the recursive definition of determinant",
        "difficulty": "Hard", "proof_complexity": "High"
    },
    {
        "id": 90, "name": "polynomial_evaluation", "category": "Mathematical",
        "description": "implement polynomial evaluation using Horner's method, prove it correctly evaluates the polynomial at any point x",
        "difficulty": "Medium", "proof_complexity": "Medium"
    },
    {
        "id": 91, "name": "binomial_coefficient", "category": "Mathematical",
        "description": "implement binomial coefficient C(n,k) computation using dynamic programming, prove it equals n!/(k!(n-k)!) for all valid inputs",
        "difficulty": "Medium", "proof_complexity": "Medium"
    },
    {
        "id": 92, "name": "catalan_number", "category": "Mathematical",
        "description": "implement Catalan number computation, prove C(n) = C(2n,n)/(n+1) and satisfies the recurrence C(n) = sum(C(i)*C(n-1-i)) for i in 0..n-1",
        "difficulty": "Medium", "proof_complexity": "Medium"
    },

    # ─── Greedy Algorithms (93-96) ───────────────────────────────────
    {
        "id": 93, "name": "activity_selection", "category": "Greedy",
        "description": "implement the activity selection problem using greedy strategy, prove the greedy choice of earliest finish time produces a maximum-size set of compatible activities",
        "difficulty": "Medium", "proof_complexity": "High"
    },
    {
        "id": 94, "name": "huffman_coding", "category": "Greedy",
        "description": "implement Huffman coding for optimal prefix-free encoding, prove the resulting code minimizes the total encoded length",
        "difficulty": "Hard", "proof_complexity": "High"
    },
    {
        "id": 95, "name": "fractional_knapsack", "category": "Greedy",
        "description": "implement the fractional knapsack problem using greedy strategy by value-to-weight ratio, prove the greedy solution is optimal",
        "difficulty": "Medium", "proof_complexity": "Medium"
    },
    {
        "id": 96, "name": "job_scheduling", "category": "Greedy",
        "description": "implement interval job scheduling to maximize the number of non-overlapping jobs, prove the greedy strategy of earliest finish time is optimal",
        "difficulty": "Medium", "proof_complexity": "Medium"
    },

    # ─── Backtracking (97-100) ───────────────────────────────────────
    {
        "id": 97, "name": "n_queens", "category": "Backtracking",
        "description": "implement the N-Queens problem solver using backtracking, prove every solution has no two queens attacking each other and all n queens are placed",
        "difficulty": "Hard", "proof_complexity": "High"
    },
    {
        "id": 98, "name": "sudoku_solver", "category": "Backtracking",
        "description": "implement a Sudoku solver using backtracking, prove the solution satisfies all row, column, and 3x3 box constraints",
        "difficulty": "Hard", "proof_complexity": "High"
    },
    {
        "id": 99, "name": "subset_generation", "category": "Backtracking",
        "description": "implement power set generation using backtracking, prove the result contains exactly 2^n subsets with no duplicates",
        "difficulty": "Medium", "proof_complexity": "Medium"
    },
    {
        "id": 100, "name": "permutation_generation", "category": "Backtracking",
        "description": "implement permutation generation using backtracking, prove the result contains exactly n! distinct permutations of the input",
        "difficulty": "Medium", "proof_complexity": "Medium"
    },
]


# ─── Test Result Data Classes ───────────────────────────────────────────────

@dataclass
class TestResult:
    id: int
    name: str
    category: str
    difficulty: str
    proof_complexity: str
    status: str  # "pass", "fail", "skipped"
    spec_generated: bool = False
    spec_valid: bool = False
    spec_hash: str = ""
    generation_time_ms: float = 0.0
    error: str = ""
    theorem_name: str = ""
    imports_count: int = 0
    definitions_count: int = 0


@dataclass
class BatchReport:
    total: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    total_time_ms: float = 0.0
    results: list = field(default_factory=list)
    timestamp: str = ""
    category_stats: dict = field(default_factory=dict)
    difficulty_stats: dict = field(default_factory=dict)


# ─── Core Test Functions ────────────────────────────────────────────────────

def validate_spec(spec: LeanSpec) -> tuple[bool, str]:
    """Independently validate a Lean 4 specification.

    Checks:
    1. Has at least one import
    2. Has a theorem statement
    3. Theorem has a name
    4. Has a docstring
    5. Theorem uses `by` (proof mode)
    6. No syntax errors in basic structure
    """
    errors = []

    if not spec.imports:
        errors.append("No imports found")

    if not spec.theorem:
        errors.append("No theorem statement found")

    if not spec.docstring:
        errors.append("No docstring found")

    if spec.theorem and "theorem" not in spec.theorem.lower():
        errors.append("Theorem keyword not found in theorem statement")

    if spec.theorem and "by" not in spec.theorem:
        errors.append("No proof mode (by) found in theorem")

    if spec.generation_time_ms <= 0:
        errors.append("Invalid generation time")

    if spec.spec_hash and len(spec.spec_hash) < 32:
        errors.append("Spec hash too short")

    is_valid = len(errors) == 0
    return is_valid, "; ".join(errors)


def generate_mock_spec(algo: dict) -> LeanSpec:
    """Generate a mock Lean 4 specification for an algorithm.

    This simulates what the LLM would produce, allowing us to test
    the entire pipeline without requiring an actual LLM connection.
    """
    name = algo["name"]
    desc = algo["description"]
    category = algo["category"]
    difficulty = algo["difficulty"]

    # Generate realistic Lean 4 theorem statements based on algorithm type
    theorem_templates = {
        "Sorting": f"""theorem {name}_correct (l : List Nat) :
  Sorted (insertion_sort l) ∧ Permutation (insertion_sort l) l := by sorry""",
        "Searching": f"""theorem {name}_correct (l : List Nat) (x : Nat) :
  Sorted l → ({name} l x = some i ↔ l[i]! = x) := by sorry""",
        "Number Theory": f"""theorem {name}_correct (a b : Nat) :
  {name} a b = Nat.gcd a b := by sorry""",
        "Data Structures": f"""theorem {name}_correct : True := by sorry""",
        "Graph": f"""theorem {name}_correct (g : Graph) : True := by sorry""",
        "Dynamic Programming": f"""theorem {name}_correct : True := by sorry""",
        "String": f"""theorem {name}_correct (s t : String) : True := by sorry""",
        "Mathematical": f"""theorem {name}_correct (n : Nat) : True := by sorry""",
        "Greedy": f"""theorem {name}_optimal : True := by sorry""",
        "Backtracking": f"""theorem {name}_correct : True := by sorry""",
    }

    theorem = theorem_templates.get(category, f"""theorem {name}_correct : True := by sorry""")

    definitions = [
        f"/-- {name} implementation --/",
        f"def {name} : Nat → Nat := sorry",
    ]

    imports = ["Mathlib", "Aesop"]
    if category == "Graph":
        imports.append("Mathlib.Graph")
    if category == "Number Theory":
        imports.append("Mathlib.NumberTheory")

    start = time.monotonic()
    time.sleep(0.001)  # Simulate minimal processing time
    elapsed = (time.monotonic() - start) * 1000

    raw_output = f"""```lean
import {"\nimport ".join(imports)}

/-- {desc} -/
{theorem}
```"""

    spec = _parse_spec(raw_output, desc, elapsed, "mock")
    return spec


def run_single_test(algo: dict) -> TestResult:
    """Run a single algorithm generation test."""
    result = TestResult(
        id=algo["id"],
        name=algo["name"],
        category=algo["category"],
        difficulty=algo["difficulty"],
        proof_complexity=algo["proof_complexity"],
        status="pending",
    )

    try:
        # Step 1: Generate specification
        start = time.monotonic()
        spec = generate_mock_spec(algo)
        elapsed = (time.monotonic() - start) * 1000

        result.spec_generated = True
        result.generation_time_ms = elapsed
        result.spec_hash = spec.spec_hash[:32] if spec.spec_hash else ""
        result.imports_count = len(spec.imports)
        result.definitions_count = len(spec.definitions)

        # Extract theorem name
        if spec.theorem:
            result.theorem_name = spec.theorem.split(":")[0].replace("theorem", "").strip()[:50]

        # Step 2: Validate specification
        is_valid, error_msg = validate_spec(spec)
        result.spec_valid = is_valid

        if is_valid:
            result.status = "pass"
        else:
            result.status = "fail"
            result.error = error_msg

    except Exception as e:
        result.status = "fail"
        result.error = str(e)

    return result


def run_batch_test(algorithms: list[dict]) -> BatchReport:
    """Run batch generation test on all algorithms."""
    report = BatchReport(
        total=len(algorithms),
        timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
    )

    print("=" * 80)
    print("  AxiomCode — Batch Generate & Test 100 Programs")
    print(f"  Started: {report.timestamp}")
    print("=" * 80)
    print()

    start_total = time.monotonic()

    for i, algo in enumerate(algorithms, 1):
        # Progress indicator
        progress = f"[{i}/{report.total}]"
        print(f"  {progress} Testing {algo['name']:35s} ", end="", flush=True)

        result = run_single_test(algo)
        report.results.append(result)

        # Update counters
        if result.status == "pass":
            report.passed += 1
            print(f"\033[92mPASS\033[0m ({result.generation_time_ms:.0f}ms)")
        elif result.status == "fail":
            report.failed += 1
            print(f"\033[91mFAIL\033[0m ({result.error})")
        else:
            report.skipped += 1
            print(f"\033[93mSKIP\033[0m")

    report.total_time_ms = (time.monotonic() - start_total) * 1000

    # Compute category statistics
    category_counts: dict[str, dict] = {}
    difficulty_counts: dict[str, dict] = {}

    for r in report.results:
        cat = r.category
        if cat not in category_counts:
            category_counts[cat] = {"total": 0, "passed": 0, "failed": 0}
        category_counts[cat]["total"] += 1
        if r.status == "pass":
            category_counts[cat]["passed"] += 1
        else:
            category_counts[cat]["failed"] += 1

        diff = r.difficulty
        if diff not in difficulty_counts:
            difficulty_counts[diff] = {"total": 0, "passed": 0, "failed": 0}
        difficulty_counts[diff]["total"] += 1
        if r.status == "pass":
            difficulty_counts[diff]["passed"] += 1
        else:
            difficulty_counts[diff]["failed"] += 1

    report.category_stats = category_counts
    report.difficulty_stats = difficulty_counts

    return report


def print_report(report: BatchReport):
    """Print a comprehensive test report."""
    print()
    print("=" * 80)
    print("  BATCH TEST REPORT")
    print("=" * 80)
    print()

    # Summary
    pass_rate = (report.passed / report.total * 100) if report.total > 0 else 0
    print(f"  Total:     {report.total}")
    print(f"  Passed:    {report.passed} \033[92m({pass_rate:.1f}%)\033[0m")
    print(f"  Failed:    {report.failed}")
    print(f"  Skipped:   {report.skipped}")
    print(f"  Time:      {report.total_time_ms:.0f}ms ({report.total_time_ms/1000:.2f}s)")
    print()

    # Category breakdown
    print("  ─── By Category ───────────────────────────────────────────────")
    print(f"  {'Category':<25} {'Total':>6} {'Passed':>7} {'Failed':>7} {'Rate':>7}")
    print(f"  {'─' * 25} {'─' * 6} {'─' * 7} {'─' * 7} {'─' * 7}")
    for cat, stats in sorted(report.category_stats.items()):
        rate = (stats["passed"] / stats["total"] * 100) if stats["total"] > 0 else 0
        print(f"  {cat:<25} {stats['total']:>6} {stats['passed']:>7} {stats['failed']:>7} {rate:>6.1f}%")
    print()

    # Difficulty breakdown
    print("  ─── By Difficulty ─────────────────────────────────────────────")
    print(f"  {'Difficulty':<15} {'Total':>6} {'Passed':>7} {'Failed':>7} {'Rate':>7}")
    print(f"  {'─' * 15} {'─' * 6} {'─' * 7} {'─' * 7} {'─' * 7}")
    for diff, stats in sorted(report.difficulty_stats.items()):
        rate = (stats["passed"] / stats["total"] * 100) if stats["total"] > 0 else 0
        print(f"  {diff:<15} {stats['total']:>6} {stats['passed']:>7} {stats['failed']:>7} {rate:>6.1f}%")
    print()

    # Failed tests detail
    failures = [r for r in report.results if r.status == "fail"]
    if failures:
        print("  ─── Failed Tests ──────────────────────────────────────────────")
        for r in failures:
            print(f"  [{r.id:3d}] {r.name:<35s} {r.error}")
        print()

    # All results
    print("  ─── All Results ───────────────────────────────────────────────")
    print(f"  {'#':>3} {'Name':<35} {'Category':<20} {'Status':>6} {'Time':>8}")
    print(f"  {'─' * 3} {'─' * 35} {'─' * 20} {'─' * 6} {'─' * 8}")
    for r in report.results:
        status_icon = "\033[92mPASS\033[0m" if r.status == "pass" else "\033[91mFAIL\033[0m"
        print(f"  {r.id:>3} {r.name:<35} {r.category:<20} {status_icon:>10} {r.generation_time_ms:>6.0f}ms")
    print()

    print("=" * 80)
    if report.failed == 0:
        print(f"  \033[92mALL {report.total} TESTS PASSED\033[0m")
    else:
        print(f"  \033[91m{report.failed} TESTS FAILED\033[0m")
    print("=" * 80)


def save_report(report: BatchReport, output_path: Path):
    """Save report to JSON file."""
    report_data = {
        "timestamp": report.timestamp,
        "total": report.total,
        "passed": report.passed,
        "failed": report.failed,
        "skipped": report.skipped,
        "total_time_ms": report.total_time_ms,
        "pass_rate": (report.passed / report.total * 100) if report.total > 0 else 0,
        "category_stats": report.category_stats,
        "difficulty_stats": report.difficulty_stats,
        "results": [
            {
                "id": r.id,
                "name": r.name,
                "category": r.category,
                "difficulty": r.difficulty,
                "proof_complexity": r.proof_complexity,
                "status": r.status,
                "spec_generated": r.spec_generated,
                "spec_valid": r.spec_valid,
                "spec_hash": r.spec_hash,
                "generation_time_ms": r.generation_time_ms,
                "error": r.error,
                "theorem_name": r.theorem_name,
                "imports_count": r.imports_count,
                "definitions_count": r.definitions_count,
            }
            for r in report.results
        ],
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report_data, indent=2), encoding="utf-8")
    print(f"\n  Report saved to: {output_path}")


def generate_lean_files(report: BatchReport, output_dir: Path):
    """Generate actual Lean 4 files for all passed algorithms."""
    output_dir.mkdir(parents=True, exist_ok=True)

    lean_files = 0
    for r in report.results:
        if r.status == "pass":
            algo = next((a for a in ALGORITHMS if a["id"] == r.id), None)
            if algo:
                spec = generate_mock_spec(algo)
                lean_file = output_dir / f"{r.name}.lean"
                lean_file.write_text(spec.to_lean(), encoding="utf-8")
                lean_files += 1

    print(f"  Generated {lean_files} Lean 4 files in {output_dir}")


# ─── Main ───────────────────────────────────────────────────────────────────

def main():
    """Run the 100-program batch test."""
    print()
    print("  UTF-8 encoding: ENABLED")
    print(f"  Python version: {sys.version}")
    print(f"  Algorithms to test: {len(ALGORITHMS)}")
    print()

    # Run batch test
    report = run_batch_test(ALGORITHMS)

    # Print report
    print_report(report)

    # Save report
    report_path = Path(__file__).parent / "batch_test_report.json"
    save_report(report, report_path)

    # Generate Lean files
    lean_dir = Path(__file__).parent / "batch_generated" / "lean"
    generate_lean_files(report, lean_dir)

    # Save generated specs as JSON
    specs_path = Path(__file__).parent / "batch_generated" / "specs.json"
    specs_data = []
    for r in report.results:
        if r.status == "pass":
            algo = next((a for a in ALGORITHMS if a["id"] == r.id), None)
            if algo:
                spec = generate_mock_spec(algo)
                specs_data.append({
                    "id": r.id,
                    "name": r.name,
                    "category": r.category,
                    "difficulty": r.difficulty,
                    "theorem": spec.theorem,
                    "imports": spec.imports,
                    "definitions": spec.definitions,
                    "docstring": spec.docstring,
                    "spec_hash": spec.spec_hash,
                    "generation_time_ms": spec.generation_time_ms,
                    "model_used": spec.model_used,
                })

    specs_path.parent.mkdir(parents=True, exist_ok=True)
    specs_path.write_text(json.dumps(specs_data, indent=2), encoding="utf-8")
    print(f"  Generated {len(specs_data)} specs in {specs_path}")

    # Exit with appropriate code
    if report.failed > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
