# AxiomCode — Automated Batch Program Generation & Proof Verification

This document records the automated process for validating AxiomCode's core functionality by generating and verifying a large batch of programs.

## Purpose
- Demonstrate that AxiomCode can generate, prove, and extract code for a wide variety of algorithms, fully autonomously.
- Provide a reproducible record of batch verification for compliance and regression testing.

## Batch Verification Procedure

1. **Environment**
   - Lean 4 must be installed and available in the system PATH (test with `lean --version`).
   - All dependencies for AxiomCode must be installed (`pip install -e .[all]`).
   - Run all commands from Windows Command Prompt (cmd.exe) to ensure Lean 4 is detected.

2. **Batch Generation & Verification**
   - Prepare a list of at least 100 algorithm prompts (see `examples/` and below for ideas).
   - For each prompt, run:
     ```cmd
     python cli.py generate "<algorithm description>"
     ```
   - Confirm that:
     - [ ] A formal Lean 4 specification is generated.
     - [ ] Proof search is attempted and (if possible) completed.
     - [ ] Code is extracted (Python/C) and a certificate is generated.
     - [ ] Any errors are logged for review.

3. **Example Prompts**
   - implement binary search on a sorted array
   - implement insertion sort
   - implement merge sort
   - implement gcd (Euclidean algorithm)
   - implement quicksort
   - implement dijkstra's shortest path
   - implement breadth-first search
   - implement depth-first search
   - implement linked list reverse
   - implement stack with max
   - ... (expand to 100+)

4. **Automation**
   - Use a batch script or Python to loop through all prompts and capture output to `diagnostics/batch_results.txt`.
   - Review the output for any failures or skipped proofs.

5. **Documentation**
   - This file and `diagnostics/batch_results.txt` serve as the compliance and regression record.

## Notes
- If Lean 4 is not detected, restart the terminal or system and ensure PATH is set.
- For any failed or skipped proofs, review the generated `.lean` files in `lean/src/Algorithms/`.
- For further help, see `docs/QUICKSTART.md` and `docs/ARCHITECTURE.md`.
