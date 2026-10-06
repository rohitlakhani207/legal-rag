"""Minimal Ollama chat client (local, free). Any object with the same `chat` signature
can stand in for it, which is how tests run without a model."""

import time
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Protocol

import httpx

from app.config import get_settings


@dataclass
class ChatResult:
    content: str
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    duration_ms: float = 0.0


class LLM(Protocol):
    def chat(
        self,
        model: str,
        messages: list[dict[str, str]],
        *,
        format: dict | str | None = None,
        num_predict: int | None = None,
    ) -> ChatResult: ...


class OllamaError(RuntimeError):
    pass


class OllamaClient:
    def __init__(self, base_url: str, timeout_s: float = 600.0, num_ctx: int = 8192, keep_alive: str = "30m"):
        self.base_url = base_url.rstrip("/")
        self.num_ctx = num_ctx
        self.keep_alive = keep_alive
        self._client = httpx.Client(timeout=timeout_s)
        self._think_supported: dict[str, bool] = {}

    def chat(
        self,
        model: str,
        messages: list[dict[str, str]],
        *,
        format: dict | str | None = None,
        num_predict: int | None = None,
    ) -> ChatResult:
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": False,
            "keep_alive": self.keep_alive,
            # Deterministic decoding keeps evaluation runs comparable.
            "options": {"temperature": 0, "seed": 42, "num_ctx": self.num_ctx},
        }
        if num_predict:
            payload["options"]["num_predict"] = num_predict
        if format is not None:
            payload["format"] = format
        # Reasoning models (qwen3, deepseek-r1, ...) are far slower with thinking on.
        if self._think_supported.get(model, True):
            payload["think"] = False

        start = time.perf_counter()
        response = self._client.post(f"{self.base_url}/api/chat", json=payload)
        if response.status_code == 400 and "think" in response.text and "think" in payload:
            self._think_supported[model] = False
            payload.pop("think")
            response = self._client.post(f"{self.base_url}/api/chat", json=payload)
        if response.status_code == 404:
            raise OllamaError(f"Model {model!r} not found in Ollama. Run: ollama pull {model}")
        if response.is_error:
            raise OllamaError(f"Ollama error {response.status_code}: {response.text[:300]}")
        data = response.json()
        return ChatResult(
            content=data["message"]["content"].strip(),
            model=model,
            prompt_tokens=data.get("prompt_eval_count", 0),
            completion_tokens=data.get("eval_count", 0),
            duration_ms=(time.perf_counter() - start) * 1000,
        )

    def list_models(self) -> list[str]:
        response = self._client.get(f"{self.base_url}/api/tags", timeout=5)
        response.raise_for_status()
        return [m["name"] for m in response.json().get("models", [])]


@lru_cache
def get_llm() -> OllamaClient:
    s = get_settings()
    return OllamaClient(s.ollama_base_url, s.ollama_timeout_s, s.ollama_num_ctx, s.ollama_keep_alive)
