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

import re as _re
import shutil
import subprocess
import textwrap
from collections.abc import Callable
from pathlib import Path

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


def _module_target_for(lean_file: Path, project_dir: str | Path) -> str | None:
    """Derive a Lake module target (e.g. ``Algorithms.Foo``) from a written .lean path.

    Strips the project dir and a leading ``src/`` (the common ``srcDir``), turning
    path separators into dots. Returns None when the file is not under the project.
    """
    try:
        rel = Path(lean_file).resolve().relative_to(Path(project_dir).resolve())
    except ValueError:
        return None
    parts = list(rel.with_suffix("").parts)
    if parts and parts[0] == "src":
        parts = parts[1:]
    if not parts:
        return None
    return ".".join(parts)


def lake_build(
    project_dir: str | Path,
    lake_bin: str = "lake",
    timeout: int = 300,
    target: str | None = None,
) -> tuple[bool, str]:
    """Run `lake build [target]` in the Lean project. Returns (success, combined log).

    `target` names an explicit Lake target (e.g. a module like ``Algorithms.Foo``).
    A bare `lake build` builds nothing on current Lake releases ("Nothing to build")
    yet exits 0 — treating that as success would be a vacuous verification, so it is
    reported as failure.
    """
    cmd = [lake_bin, "build"] + ([target] if target else [])
    try:
        result = subprocess.run(
            cmd,
            cwd=str(project_dir),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except FileNotFoundError:
        return False, f"TOOLCHAIN_MISSING: {lake_bin} not found"
    log = (result.stdout or "") + ("\n" + result.stderr if result.stderr else "")
    log = log.strip()
    if result.returncode == 0 and "nothing to build" in log.lower():
        return False, log + "\nBUILD_VACUOUS: lake built no targets; pass an explicit target"
    return result.returncode == 0, log


# ─── Lean file elaboration ─────────────────────────────────────────────────────


def elaborate_lean_file(
    lean_file: str | Path,
    project_dir: str | Path,
    lake_bin: str = "lake",
    lean_bin: str = "lean",
    timeout: int = 300,
) -> tuple[bool, str]:
    """Elaborate a Lean file with `lake env lean`. Returns (success, combined log).

    This is the actual machine check: Lean elaborates the named file and the
    exit code reflects the result. It is used instead of `lake build <module>`
    because Lake can only build modules listed in the lakefile's static roots —
    generated proofs (dynamic names under `src/Algorithms/`) are unaddressable
    that way, and a bare `lake build` verifies nothing. Elaborating the file
    directly cannot be vacuous: a missing file is an error, and the named file
    is always the thing being checked.
    """
    lean_file = Path(lean_file)
    if not lean_file.is_file():
        return False, f"ELABORATION_MISSING: {lean_file} does not exist"
    if shutil.which(lake_bin) is None or shutil.which(lean_bin) is None:
        return False, f"TOOLCHAIN_MISSING: {lake_bin}/{lean_bin} not found"
    try:
        result = subprocess.run(
            [lake_bin, "env", lean_bin, str(lean_file)],
            cwd=str(project_dir),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.SubprocessError as e:
        return False, f"ELABORATION_ERROR: {e}"
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


def has_sorry(lean_code: str) -> bool:
    """Detect unfinished proofs. `sorry`/`admit` typecheck, so a bare
    `lake build` success is NOT sufficient for verified status."""
    code = _re.sub(r"--.*$", "", lean_code, flags=_re.MULTILINE)  # strip line comments
    return bool(_re.search(r"\b(sorry|admit)\b", code))


# ─── Axiom audit (P0 ship-blocker) ────────────────────────────────────────────
#
# `lake build` success + no `sorry` is NOT enough: a proof can smuggle
#     axiom sneaky : False
#     theorem one_eq_two : (1 : Nat) = 2 := False.elim sneaky
# which builds cleanly, contains no sorry, and would previously verify as TRUE.
# The only thing that catches it is inspecting which axioms each proven
# theorem actually depends on via `#print axioms`, and failing closed on
# anything outside Lean's own standard axiom set.

#: Axioms Lean 4 itself relies on. Anything else in a proof's dependency set
#: is user-smuggled (or an exotic dependency the pipeline cannot vouch for)
#: and fails verification. `sorryAx` is deliberately absent: a dependency on
#: it means an undischarged proof obligation survived somewhere.
ALLOWED_AXIOMS = frozenset({"propext", "Quot.sound", "funext", "Classical.choice"})


def _qualified_theorem_names(lean_code: str) -> list[str]:
    """Extract fully-qualified `theorem`/`lemma` names declared in Lean code.

    Tracks `namespace` blocks so `#print axioms` can address each declaration
    unambiguously. Note: Lean does NOT prefix declarations with the module
    name — a top-level `theorem foo` in module `E2E` is simply `foo`.
    """
    names: list[str] = []
    ns_stack: list[str] = []
    for line in lean_code.splitlines():
        m = _re.match(r"\s*namespace\s+([A-Za-z_][A-Za-z0-9_.']*)", line)
        if m:
            ns_stack.append(m.group(1))
            continue
        if _re.match(r"\s*end\b", line):
            if ns_stack:
                ns_stack.pop()
            continue
        m = _re.match(r"\s*(?:theorem|lemma)\s+([A-Za-z_][A-Za-z0-9_']*)", line)
        if m:
            names.append(".".join([*ns_stack, m.group(1)]))
    return names


def audit_axioms(
    lean_file: str | Path,
    project_dir: str | Path,
    lake_bin: str = "lake",
    lean_bin: str = "lean",
    timeout: int = 300,
) -> tuple[bool, str]:
    """Audit axiom dependencies of every proven theorem via `#print axioms`.

    The proof file is copied to a temporary sibling with `#print axioms`
    commands appended, then elaborated with `lake env lean` — no module
    imports needed, so this works for generated files outside the lakefile's
    static roots.

    FAILS CLOSED: any non-standard axiom, any unresolvable theorem name, a
    missing toolchain, or unparseable output → (False, reason). Never returns
    True on uncertainty — an unverifiable proof is not a verified proof.
    """
    if shutil.which(lake_bin) is None or shutil.which(lean_bin) is None:
        return False, "axiom audit: lean/lake toolchain not available"

    lean_file = Path(lean_file)
    try:
        code = lean_file.read_text(encoding="utf-8")
    except OSError as e:
        return False, f"axiom audit: cannot read {lean_file}: {e}"

    theorems = _qualified_theorem_names(code)
    if not theorems:
        return False, "axiom audit: no theorem/lemma declarations found to audit"

    audit_src = code + "\n" + "\n".join(f"#print axioms {t}" for t in theorems) + "\n"
    checker = lean_file.with_name(f"{lean_file.stem}.axiomaudit.lean")
    try:
        checker.write_text(audit_src, encoding="utf-8")
        result = subprocess.run(
            [lake_bin, "env", lean_bin, str(checker)],
            cwd=str(project_dir),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.SubprocessError as e:
        return False, f"axiom audit: checker run failed: {e}"
    finally:
        try:
            checker.unlink()
        except OSError:
            pass

    output = (result.stdout or "") + ("\n" + (result.stderr or ""))
    if result.returncode != 0:
        return False, "axiom audit: lean rejected the audit module:\n" + output.strip()[-2000:]

    deps: dict[str, set[str]] = {}
    for m in _re.finditer(r"'([^']+)' depends on axioms: \[(.*?)\]", output):
        deps[m.group(1)] = {a.strip() for a in m.group(2).split(",") if a.strip()}
    # Lean reports axiom-free theorems with a different sentence.
    for m in _re.finditer(r"'([^']+)' does not depend on any axioms", output):
        deps.setdefault(m.group(1), set())

    problems: list[str] = []
    for t in theorems:
        if t not in deps:
            problems.append(f"{t}: axiom dependencies could not be determined (unresolved name?)")
            continue
        extra = deps[t] - ALLOWED_AXIOMS
        if extra:
            problems.append(f"{t}: depends on non-standard axioms: {sorted(extra)}")
    if problems:
        return False, "axiom audit FAILED:\n" + "\n".join(f"  - {p}" for p in problems)

    summary = "; ".join(f"{t}: [{', '.join(sorted(a)) if a else 'no axioms'}]" for t, a in deps.items())
    return True, f"axiom audit passed: {summary}"


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
    lean_bin: str = "lean",
    use_pantograph: bool = True,
    build_timeout: int = 900,
) -> tuple[bool, str, int, str]:
    """Elaborate → on failure, LLM-repair → re-elaborate, up to ``max_attempts``.

    Each attempt elaborates the written spec with `lake env lean` (the actual
    machine check — unlike `lake build <module>`, which cannot address
    generated modules outside the lakefile's static roots). A successful
    elaboration then passes two further gates before it may count as
    verified: the `sorry`/`admit` scan and the axiom audit. The axiom audit is
    deliberately NOT repairable by the LLM — smuggled axioms are adversarial,
    not typos, so a failure here ends the loop honestly.
    Returns (verified, final_code, attempts_used, log).
    """
    code = initial_code
    log = ""
    attempts = 0
    for attempt in range(1, max_attempts + 1):
        attempts = attempt
        lean_file = write_spec_fn(code)
        ok, build_log = elaborate_lean_file(
            lean_file, project_dir, lake_bin=lake_bin, lean_bin=lean_bin, timeout=build_timeout
        )
        log = build_log
        if ok:
            # A build that still contains sorry/admit is NOT a verified proof:
            # sorry typechecks, so this scan is the actual verification gate.
            if has_sorry(code):
                log += "\nbuild succeeded but undischarged sorry/admit remain"
                ok = False
            else:
                # P0 gate: a clean build with no sorry can still smuggle
                # `axiom sneaky : False` and "prove" 1 = 2. Audit axiom
                # dependencies; fail closed on anything non-standard.
                audit_ok, audit_report = audit_axioms(
                    lean_file,
                    project_dir,
                    lake_bin=lake_bin,
                    lean_bin=lean_bin,
                    timeout=build_timeout,
                )
                log += f"\n{audit_report}"
                if not audit_ok:
                    ok = False
                    break
                if use_pantograph and pantograph_available():
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
