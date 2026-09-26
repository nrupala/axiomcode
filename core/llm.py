"""AxiomCode — LLM backend layer.

One OpenAI-compatible HTTP layer serves every chat backend, so the same
code path drives:

- **llama.cpp** server — the primary local backend (default ``http://localhost:8080``)
- **vLLM** — the production inference-serving standard big agents run on
  (default ``http://localhost:8000``)
- **Ollama** — kept as a compatibility alias (default ``http://localhost:11434``)
- **Mistral / OpenAI** — vendor APIs, which are OpenAI-compatible endpoints

Anthropic keeps its native messages API (it is not OpenAI-compatible).

Zero third-party dependencies: pure stdlib HTTP. No per-server SDKs.

Environment overrides:
    AXIOMCODE_LLM_BACKEND   backend name (default: local -> llama.cpp)
    AXIOMCODE_LLM_MODEL     model name (default: server default)
    AXIOMCODE_LLM_BASE_URL  override the backend's base URL
    AXIOMCODE_LLM_API_KEY   bearer token for secured servers
    MISTRAL_API_KEY / OPENAI_API_KEY / ANTHROPIC_API_KEY as usual
"""

from __future__ import annotations

import hashlib
import json
import os
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from pathlib import Path

# ─── Tiny file cache (shared by all backends) ────────────────────────────────


class LLMCache:
    """On-disk cache for LLM responses: same prompt + model = no second call."""

    def __init__(self, cache_dir: str | Path = ".axiomcode/cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _key(self, model: str, prompt: str) -> str:
        return hashlib.sha256(f"{model}::{prompt}".encode()).hexdigest()

    def get(self, model: str, prompt: str) -> str | None:
        path = self.cache_dir / f"{self._key(model, prompt)}.json"
        if path.exists():
            try:
                cached = json.loads(path.read_text(encoding="utf-8"))["response"]
            except (json.JSONDecodeError, KeyError, OSError):
                return None
            return cached if isinstance(cached, str) else None
        return None

    def put(self, model: str, prompt: str, response: str) -> None:
        path = self.cache_dir / f"{self._key(model, prompt)}.json"
        try:
            path.write_text(json.dumps({"response": response}), encoding="utf-8")
        except OSError:
            pass


_llm_cache = LLMCache()


# ─── OpenAI-compatible chat core ─────────────────────────────────────────────


def openai_compat_chat(
    model: str,
    prompt: str,
    base_url: str,
    api_key: str | None = None,
    cache_ns: str = "compat",
    temperature: float = 0.2,
    max_tokens: int = 4096,
    timeout: int = 180,
    retries: int = 3,
) -> str:
    """POST an OpenAI-style chat completion request. Works against llama.cpp
    server, vLLM, Ollama, Mistral, OpenAI, LM Studio — anything speaking the
    ``/v1/chat/completions`` dialect."""
    base_url = (os.environ.get("AXIOMCODE_LLM_BASE_URL") or base_url).rstrip("/")
    key = api_key or os.environ.get("AXIOMCODE_LLM_API_KEY", "")
    cache_key = f"{cache_ns}/{base_url}/{model}"

    cached = _llm_cache.get(cache_key, prompt)
    if cached:
        return cached

    payload = json.dumps(
        {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
    ).encode("utf-8")

    last_err: Exception | None = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(
                f"{base_url}/v1/chat/completions",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            if key:
                req.add_header("Authorization", f"Bearer {key}")
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            result = _extract_content(data)
            _llm_cache.put(cache_key, prompt, result)
            return result
        except Exception as e:  # noqa: BLE001 — retry then report
            last_err = e
            time.sleep(2**attempt)
    raise RuntimeError(
        f"LLM backend failed after {retries} attempts ({base_url}): {last_err}\n"
        f"Fix: serve a model on {base_url} (llama.cpp: `llama-server -m model.gguf`; "
        f"vLLM: `vllm serve model`), or set AXIOMCODE_LLM_BASE_URL."
    )


def _extract_content(data: dict) -> str:
    """Pull assistant text out of the several shapes /v1/chat/completions takes."""
    if not isinstance(data, dict):
        return ""
    choices = data.get("choices", [])
    result = ""
    if choices:
        first = choices[0]
        msg = first.get("message")
        if isinstance(msg, dict):
            result = msg.get("content", "") or ""
        elif isinstance(first.get("content"), list):
            result = first["content"][0].get("text", "")
        else:
            result = first.get("text", "") or ""
    return result or data.get("response", "") or ""


# ─── Backend presets ─────────────────────────────────────────────────────────


def _env_or(name: str, default: str) -> str:
    return os.environ.get(name, default)


def llamacpp_generate(model: str, prompt: str, base_url: str | None = None) -> str:
    """llama.cpp server — the primary local backend."""
    return openai_compat_chat(
        model,
        prompt,
        base_url or _env_or("AXIOMCODE_LLAMACPP_URL", "http://localhost:8080"),
        cache_ns="llamacpp",
    )


def vllm_generate(model: str, prompt: str, base_url: str | None = None) -> str:
    """vLLM — the production serving stack large agents run on."""
    return openai_compat_chat(
        model,
        prompt,
        base_url or _env_or("AXIOMCODE_VLLM_URL", "http://localhost:8000"),
        cache_ns="vllm",
    )


def ollama_generate(model: str, prompt: str, base_url: str | None = None) -> str:
    """Ollama via its OpenAI-compatible endpoint (kept for compatibility)."""
    return openai_compat_chat(
        model,
        prompt,
        base_url or _env_or("AXIOMCODE_OLLAMA_URL", "http://localhost:11434"),
        cache_ns="ollama",
    )


def mistral_generate(model: str, prompt: str, base_url: str | None = None) -> str:
    """Mistral API (OpenAI-compatible)."""
    key = os.environ.get("MISTRAL_API_KEY", "")
    if not key:
        raise RuntimeError("Set MISTRAL_API_KEY environment variable")
    return openai_compat_chat(
        model,
        prompt,
        base_url or "https://api.mistral.ai",
        api_key=key,
        cache_ns="mistral",
    )


def openai_generate(model: str, prompt: str, api_key: str | None = None) -> str:
    """OpenAI API via HTTP (no SDK)."""
    key = api_key or os.environ.get("OPENAI_API_KEY", "")
    if not key:
        raise RuntimeError("Set OPENAI_API_KEY environment variable")
    return openai_compat_chat(
        model,
        prompt,
        "https://api.openai.com",
        api_key=key,
        cache_ns="openai",
    )


def anthropic_generate(model: str, prompt: str, api_key: str | None = None) -> str:
    """Anthropic API via HTTP (no SDK). Native messages API."""
    import http.client

    key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
    if not key:
        raise RuntimeError("Set ANTHROPIC_API_KEY environment variable")

    cache_key = f"anthropic/{model}"
    cached = _llm_cache.get(cache_key, prompt)
    if cached:
        return cached

    body = json.dumps(
        {
            "model": model,
            "max_tokens": 4096,
            "messages": [{"role": "user", "content": prompt}],
        }
    ).encode("utf-8")
    conn = http.client.HTTPSConnection("api.anthropic.com", 443, timeout=120)
    try:
        conn.request(
            "POST",
            "/v1/messages",
            body=body,
            headers={
                "Content-Type": "application/json",
                "x-api-key": key,
                "anthropic-version": "2023-06-01",
            },
        )
        resp = conn.getresponse()
        data = json.loads(resp.read().decode("utf-8"))
        result = data["content"][0]["text"]
        if not isinstance(result, str):
            raise RuntimeError(f"Unexpected Anthropic response shape: {data!r}"[:200])
        _llm_cache.put(cache_key, prompt, result)
        return result
    finally:
        conn.close()


# ─── Backend registry ────────────────────────────────────────────────────────

# name -> (default model, generate function, human description)
BACKENDS: dict[str, tuple[str, Callable[[str, str], str], str]] = {
    "local": ("default", llamacpp_generate, "llama.cpp server (local-first, default)"),
    "llama.cpp": ("default", llamacpp_generate, "llama.cpp server (local-first)"),
    "llamacpp": ("default", llamacpp_generate, "llama.cpp server (alias)"),
    "vllm": ("default", vllm_generate, "vLLM server (production serving)"),
    "ollama": ("qwen2.5-coder:7b", ollama_generate, "Ollama (compatibility)"),
    "mistral": ("mistral-large-latest", mistral_generate, "Mistral API"),
    "openai": ("gpt-4o", openai_generate, "OpenAI API"),
    "anthropic": ("claude-sonnet-4-20250514", anthropic_generate, "Anthropic API"),
    "claude": ("claude-sonnet-4-20250514", anthropic_generate, "Anthropic API (alias)"),
}


def resolve_backend(name: str | None = None) -> tuple[str, str, Callable[[str, str], str]]:
    """Resolve a backend name to (name, model, generate_fn), honoring env overrides."""
    name = (name or os.environ.get("AXIOMCODE_LLM_BACKEND") or "local").lower()
    if name not in BACKENDS:
        name = "local"
    default_model, gen_fn, _desc = BACKENDS[name]
    model = os.environ.get("AXIOMCODE_LLM_MODEL") or default_model
    return name, model, gen_fn


def list_backends() -> list[tuple[str, str, str]]:
    """(name, default model, description) for the `models` command."""
    seen: dict[str, tuple[str, str, str]] = {}
    for bname, (model, _fn, desc) in BACKENDS.items():
        seen.setdefault(desc, (bname, model, desc))
    return sorted(seen.values())
