"""Tests for the LLM backend layer (core/llm.py) and proof engine (core/prover.py).

Mostly pure unit tests — no network required. The TestBrokenCodeHonesty class
needs a real Lean toolchain on PATH (skipped otherwise)."""

import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.llm import (
    _extract_content,
    list_backends,
    llamacpp_generate,
    ollama_generate,
    resolve_backend,
    vllm_generate,
)
from core.prover import (
    _module_target_for,
    extract_lean_block,
    has_sorry,
    iterative_proof_search,
    lake_build,
)


class TestBackendRegistry:
    def test_llamacpp_is_default_local(self):
        name, model, fn = resolve_backend("local")
        assert name == "local"
        assert fn is llamacpp_generate

    def test_vllm_backend_resolves(self):
        name, model, fn = resolve_backend("vllm")
        assert fn is vllm_generate

    def test_ollama_kept_as_compat_alias(self):
        name, model, fn = resolve_backend("ollama")
        assert fn is ollama_generate

    def test_unknown_backend_falls_back_to_local(self):
        name, _model, _fn = resolve_backend("does-not-exist")
        assert name == "local"

    def test_env_override_backend(self, monkeypatch):
        monkeypatch.setenv("AXIOMCODE_LLM_BACKEND", "vllm")
        name, _model, _fn = resolve_backend(None)
        assert name == "vllm"

    def test_env_override_model(self, monkeypatch):
        monkeypatch.setenv("AXIOMCODE_LLM_MODEL", "my-model")
        _name, model, _fn = resolve_backend("local")
        assert model == "my-model"

    def test_list_backends_covers_llamacpp_and_vllm(self):
        names = [b[0] for b in list_backends()]
        assert any("llama" in n for n in names)
        assert "vllm" in names

    def test_no_per_server_sdk_imports(self):
        # The whole point: stdlib HTTP only.
        import core.llm as m

        src = open(m.__file__, encoding="utf-8").read()
        for sdk in ["import openai", "import anthropic", "import ollama", "import vllm"]:
            assert sdk not in src


class TestExtractContent:
    def test_openai_shape(self):
        d = {"choices": [{"message": {"content": "hello"}}]}
        assert _extract_content(d) == "hello"

    def test_legacy_text_shape(self):
        d = {"choices": [{"text": "world"}]}
        assert _extract_content(d) == "world"

    def test_empty(self):
        assert _extract_content({}) == ""


class TestHasSorry:
    def test_detects_sorry(self):
        assert has_sorry("theorem t : True := by sorry")

    def test_detects_admit(self):
        assert has_sorry("theorem t : True := by\n  admit")

    def test_clean_proof_passes(self):
        assert not has_sorry("theorem t : True := by\n  trivial")

    def test_comment_mention_ignored(self):
        assert not has_sorry("-- sorry about the delay\ntheorem t : True := by trivial")

    def test_sorry_in_identifier_not_matched(self):
        # word boundary: 'sorryful' is not sorry
        assert not has_sorry("theorem sorryful : True := by trivial")


class TestExtractLeanBlock:
    def test_lean_fence(self):
        raw = "some text\n```lean\ntheorem x := 1\n```\ntail"
        assert extract_lean_block(raw) == "theorem x := 1"

    def test_plain_fence(self):
        raw = "```\ntheorem y := 2\n```"
        assert extract_lean_block(raw) == "theorem y := 2"

    def test_no_fence_passthrough(self):
        assert extract_lean_block("theorem z := 3") == "theorem z := 3"


# ─── Prover honesty regression tests ─────────────────────────────────────────
# These lock in the fix for the vacuous-verification bug: a bare `lake build`
# exits 0 while building nothing on current Lake releases, so the prover must
# always pass an explicit module target and must reject "Nothing to build".


class TestModuleTargetDerivation:
    def test_src_prefix_stripped(self, tmp_path):
        proj = tmp_path / "proj"
        (proj / "src").mkdir(parents=True)
        f = proj / "src" / "Spec.lean"
        f.touch()
        assert _module_target_for(f, proj) == "Spec"

    def test_nested_module_dotted(self, tmp_path):
        proj = tmp_path / "proj"
        (proj / "src" / "Algorithms").mkdir(parents=True)
        f = proj / "src" / "Algorithms" / "Foo.lean"
        f.touch()
        assert _module_target_for(f, proj) == "Algorithms.Foo"

    def test_no_src_prefix_kept(self, tmp_path):
        proj = tmp_path / "proj"
        proj.mkdir()
        f = proj / "Top.lean"
        f.touch()
        assert _module_target_for(f, proj) == "Top"

    def test_outside_project_returns_none(self, tmp_path):
        proj = tmp_path / "proj"
        proj.mkdir()
        elsewhere = tmp_path / "other" / "X.lean"
        elsewhere.parent.mkdir()
        elsewhere.touch()
        assert _module_target_for(elsewhere, proj) is None


class TestVacuousBuildRejection:
    def _run(self, returncode, stdout):
        completed = subprocess.CompletedProcess(
            args=["lake", "build"],
            returncode=returncode,
            stdout=stdout,
            stderr="",
        )
        with patch("core.prover.subprocess.run", return_value=completed) as m:
            ok, log = lake_build("/tmp/fake-proj")
        return ok, log, m

    def test_nothing_to_build_is_failure(self):
        ok, log, m = self._run(0, "Nothing to build.\n")
        assert ok is False
        assert "BUILD_VACUOUS" in log
        # the bug: bare `lake build` with no target
        assert m.call_args[0][0] == ["lake", "build"]

    def test_nothing_to_build_case_insensitive(self):
        ok, log, _ = self._run(0, "warning: nothing to BUILD\n")
        assert ok is False
        assert "BUILD_VACUOUS" in log

    def test_real_success_passes(self):
        ok, log, m = self._run(0, "✔ [3/3] Built Spec\nBuild completed successfully.\n")
        assert ok is True
        assert "BUILD_VACUOUS" not in log

    def test_explicit_target_reaches_command(self):
        completed = subprocess.CompletedProcess(
            args=["lake", "build", "Spec"],
            returncode=0,
            stdout="✔ Built Spec\n",
            stderr="",
        )
        with patch("core.prover.subprocess.run", return_value=completed) as m:
            ok, _ = lake_build("/tmp/fake-proj", target="Spec")
        assert ok is True
        assert m.call_args[0][0] == ["lake", "build", "Spec"]

    def test_failed_build_is_failure(self):
        ok, _, _ = self._run(1, "error: unknown identifier `foo`\n")
        assert ok is False


class TestBrokenCodeHonesty:
    """End-to-end honesty: broken Lean must never report verified=True.

    Uses the real Lean toolchain in a scratch project (no Mathlib dep, so it
    is fast). Skipped when `lake` is unavailable.
    """

    @staticmethod
    def _scratch_project(tmp_path):
        proj = tmp_path / "proj"
        proj.mkdir()
        (proj / "lean-toolchain").write_text("leanprover/lean4:v4.35.0-rc3")
        (proj / "lakefile.lean").write_text(
            "import Lake\nopen Lake DSL\npackage e2e where\nlean_lib E2E where\n  roots := #[`E2E]\n"
        )
        return proj

    def test_broken_code_not_verified(self, tmp_path):
        import shutil

        if shutil.which("lake") is None:
            import pytest

            pytest.skip("lake not on PATH")
        proj = self._scratch_project(tmp_path)
        src = proj / "E2E.lean"

        def writer(code: str) -> Path:
            src.write_text(code)
            return src

        broken = "theorem two_plus_three : 2 + 3 = 5 := rfl_wrong_tactic\n"
        ok, _, attempts, _ = iterative_proof_search(
            writer,
            proj,
            broken,
            None,
            "none",
            max_attempts=1,
            use_pantograph=False,
        )
        assert ok is False
        assert attempts == 1

    def test_good_code_verified(self, tmp_path):
        import shutil

        if shutil.which("lake") is None:
            import pytest

            pytest.skip("lake not on PATH")
        proj = self._scratch_project(tmp_path)
        src = proj / "E2E.lean"

        def writer(code: str) -> Path:
            src.write_text(code)
            return src

        good = "theorem two_plus_three : 2 + 3 = 5 := rfl\n"
        ok, _, attempts, _ = iterative_proof_search(
            writer,
            proj,
            good,
            None,
            "none",
            max_attempts=1,
            use_pantograph=False,
        )
        assert ok is True
        assert attempts == 1

    def test_axiom_smuggling_not_verified(self, tmp_path):
        """P0 regression: `axiom sneaky : False` proving `1 = 2` must NOT verify.

        The false theorem builds cleanly and contains no sorry — only the
        axiom audit catches it. This is the exact mis-issuance exploit from
        the strengthen assessment.
        """
        import shutil

        if shutil.which("lake") is None:
            import pytest

            pytest.skip("lake not on PATH")
        proj = self._scratch_project(tmp_path)
        src = proj / "E2E.lean"

        def writer(code: str) -> Path:
            src.write_text(code)
            return src

        exploit = "axiom sneaky : False\ntheorem one_eq_two : (1 : Nat) = 2 := False.elim sneaky\n"
        ok, _, attempts, log = iterative_proof_search(
            writer,
            proj,
            exploit,
            None,
            "none",
            max_attempts=1,
            use_pantograph=False,
        )
        assert ok is False, f"axiom-smuggled false theorem verified as TRUE:\n{log}"
        assert "axiom" in log.lower()
        assert attempts == 1  # axiom failures are not LLM-repairable; loop ends honestly
