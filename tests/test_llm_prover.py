"""Tests for the LLM backend layer (core/llm.py) and proof engine (core/prover.py).

Pure unit tests — no network, no Lean toolchain required.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.llm import (
    _extract_content,
    list_backends,
    llamacpp_generate,
    ollama_generate,
    resolve_backend,
    vllm_generate,
)
from core.prover import extract_lean_block, has_sorry


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
