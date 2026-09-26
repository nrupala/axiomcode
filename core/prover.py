"""AxiomCode — proof engine.

Two layers, matching the documented architecture:

1. **Pantograph (M2M API)** — machine-to-machine interaction with Lean 4 for
   proof checking and tactic execution, when the ``pantograph`` package is
   installed. Optional: the core pipeline stays dependency-free without it.
2. **Iterative proof search with self-correction** — when a Lean build fails,
   the compiler's error output is fed back to the LLM with a repair prompt and
   the corrected spec is rebuilt, up to ``max_attempts``. This is the loop the
   architecture documents; ``lake build`` alone was never the whole engine.

Goedel-Prover style automation is supported by serving a prover model
(e.g. a Goedel-Prover checkpoint) on llama.cpp / vLLM and selecting it as
the repair backend via AXIOMCODE_LLM_BACKEND / AXIOMCODE_LLM_MODEL.
"""

from __future__ import annotations

import shutil
import subprocess
import textwrap
from pathlib import Path
from typing import Callable


# ─── Lean toolchain detection ────────────────────────────────────────────────

def lean_available(lean_bin: str = "lean", lake_bin: str = "lake") -> bool:
    return shutil.which(lean_bin) is not None and shutil.which(lake_bin) is not None


def lean_version(lean_bin: str = "lean") -> str:
    try:
        out = subprocess.run([lean_bin, "--version"], capture_output=True, text=True, timeout=30)
        return out.stdout.strip().splitlines()[0] if out.returncode == 0 else ""
    except (FileNotFoundError, subprocess.SubprocessError):
        return ""


def pantograph_available() -> bool:
    try:
        import pantograph  # noqa: F401
        return True
    except ImportError:
        return False


# ─── Lake build ──────────────────────────────────────────────────────────────

def lake_build(project_dir: str | Path, lake_bin: str = "lake", timeout: int = 300) -> tuple[bool, str]:
    """Run `lake build` in the Lean project. Returns (success, combined log)."""
    try:
        result = subprocess.run(
            [lake_bin, "build"], cwd=str(project_dir),
            capture_output=True, text=True, timeout=timeout,
        )
    except FileNotFoundError:
        return False, f"TOOLCHAIN_MISSING: {lake_bin} not found"
    log = (result.stdout or "") + ("\n" + result.stderr if result.stderr else "")
    return result.returncode == 0, log.strip()


# ─── Pantograph checking ─────────────────────────────────────────────────────

def check_with_pantograph(lean_code: str, project_dir: str | Path | None = None) -> tuple[bool, str]:
    """Typecheck Lean code through Pantograph's M2M API.

    Returns (ok, message). Raises RuntimeError if pantograph is not installed.
    """
    try:
        from pantograph import Server
    except ImportError as e:
        raise RuntimeError(
            "Pantograph is not installed. Install it for M2M proof interaction "
            "(`pip install pantograph`), or rely on the lake-build loop."
        ) from e

    project_dir = str(project_dir) if project_dir else "."
    server = Server(project_path=project_dir)
    try:
        unit = server.load_sorry(lean_code)
    except Exception as e:  # noqa: BLE001 — surface the prover's own error
        return False, f"pantograph load failed: {e}"
    goals = list(unit.goals)
    if goals:
        return False, f"pantograph: {len(goals)} unsolved goal(s) remain"
    return True, "pantograph: no unsolved goals"


# ─── Self-correction loop ────────────────────────────────────────────────────

import re as _re

def has_sorry(lean_code: str) -> bool:
    """Detect unfinished proofs. `sorry`/`admit` typecheck, so a bare
    `lake build` success is NOT sufficient for verified status."""
    code = _re.sub(r"--.*$", "", lean_code, flags=_re.MULTILINE)  # strip line comments
    return bool(_re.search(r"\b(sorry|admit)\b", code))


REPAIR_PROMPT = textwrap.dedent("""\
    You are repairing a Lean 4 formal specification that failed to compile.
    Return ONLY the corrected Lean 4 code inside a single ```lean fenced block.
    Do not use `sorry` or `admit` anywhere — every proof must be complete.
    Keep the same theorem names and statement shapes; fix only what the errors require.

    FAILED LEAN CODE:
    {code}

    LEAN COMPILER ERRORS:
    {errors}

    CORRECTED LEAN CODE:
    """)


def repair_with_llm(
    lean_code: str,
    error_log: str,
    llm_fn: Callable[[str, str], str],
    model: str,
) -> str:
    """Ask the LLM to repair Lean code that failed to build. Returns raw text."""
    prompt = REPAIR_PROMPT.format(code=lean_code[:12000], errors=error_log[:8000])
    return llm_fn(model, prompt)


def extract_lean_block(raw: str) -> str:
    """Pull the ```lean fenced block out of an LLM response."""
    code = raw.strip()
    if "```lean" in code:
        code = code.split("```lean", 1)[1].split("```", 1)[0].strip()
    elif "```" in code:
        code = code.split("```", 1)[1].split("```", 1)[0].strip()
    return code


def iterative_proof_search(
    write_spec_fn: Callable[[str], Path],
    project_dir: str | Path,
    initial_code: str,
    llm_fn: Callable[[str, str], str] | None,
    model: str,
    max_attempts: int = 3,
    lake_bin: str = "lake",
    use_pantograph: bool = True,
) -> tuple[bool, str, int, str]:
    """Build → on failure, LLM-repair → rebuild, up to ``max_attempts``.

    Returns (verified, final_code, attempts_used, log).
    """
    code = initial_code
    log = ""
    attempts = 0
    for attempt in range(1, max_attempts + 1):
        attempts = attempt
        write_spec_fn(code)
        ok, build_log = lake_build(project_dir, lake_bin)
        log = build_log
        if ok:
            # A build that still contains sorry/admit is NOT a verified proof:
            # sorry typechecks, so this scan is the actual verification gate.
            if has_sorry(code):
                log += "\nbuild succeeded but undischarged sorry/admit remain"
                ok = False
            elif use_pantograph and pantograph_available():
                pok, pmsg = check_with_pantograph(code, project_dir)
                log += f"\n{pmsg}"
                if pok:
                    return True, code, attempts, log
            else:
                return True, code, attempts, log
        if llm_fn is None or attempt == max_attempts:
            break
        try:
            repaired = extract_lean_block(repair_with_llm(code, build_log, llm_fn, model))
        except Exception as e:  # noqa: BLE001 — repair failure ends the loop
            log += f"\nrepair attempt failed: {e}"
            break
        if not repaired or repaired == code:
            log += "\nrepair produced no changes; stopping"
            break
        code = repaired
    return False, code, attempts, log
