#!/usr/bin/env python3
"""
Frontier Adapters — Async HTTP adapters for external and local model APIs.

Patent Brief #7: Tokenized Air-Gap Proxy
Council Vote: a3ee2a8066e04490 (UNANIMOUS)

Each adapter speaks a different provider API but returns a uniform result dict:
    {"ok": bool, "text": str, "model": str, "provider": str, "latency_ms": int, "cost": float}

Adapters:
    AnthropicAdapter  — Claude models via api.anthropic.com
    OpenAIAdapter     — GPT models via api.openai.com
    GeminiAdapter     — Gemini models via generativelanguage.googleapis.com
    LocalAdapter      — Local models via SubAgentDispatch (no boundary crossing)
"""

import json
import logging
import time
from abc import ABC, abstractmethod
from typing import Optional

import httpx

logger = logging.getLogger("frontier_adapters")


class FrontierAdapter(ABC):
    """Base class for all frontier model adapters."""

    provider: str = ""
    default_model: str = ""
    enabled: bool = True

    @abstractmethod
    async def send(self, prompt: str, system: str = "", model: str = None,
                   max_tokens: int = 4096, temperature: float = 0.7,
                   timeout: float = 60.0) -> dict:
        """Send tokenized query to frontier model.

        Returns:
            {"ok": bool, "text": str, "model": str, "provider": str,
             "latency_ms": int, "cost": float, "error": str|None}
        """
        pass

    def _error_result(self, error: str, model: str, latency_ms: int = 0) -> dict:
        return {
            "ok": False, "text": "", "model": model or self.default_model,
            "provider": self.provider, "latency_ms": latency_ms,
            "cost": 0.0, "error": error,
        }


class AnthropicAdapter(FrontierAdapter):
    """Claude models via Anthropic Messages API."""

    provider = "anthropic"
    default_model = "claude-sonnet-4-6"

    # Approximate pricing per 1M tokens (input/output)
    PRICING = {
        "claude-sonnet-4-6": {"input": 3.0, "output": 15.0},
        "claude-haiku-4-5-20251001": {"input": 0.80, "output": 4.0},
    }

    def __init__(self, api_key: str, default_model: str = None):
        self.api_key = api_key
        if default_model:
            self.default_model = default_model

    def _estimate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        pricing = self.PRICING.get(model, {"input": 3.0, "output": 15.0})
        return (input_tokens * pricing["input"] + output_tokens * pricing["output"]) / 1_000_000

    async def send(self, prompt: str, system: str = "", model: str = None,
                   max_tokens: int = 4096, temperature: float = 0.7,
                   timeout: float = 60.0) -> dict:
        model = model or self.default_model
        t0 = time.monotonic()

        messages = [{"role": "user", "content": prompt}]
        body = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages,
        }
        if system:
            body["system"] = system

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    json=body, headers=headers,
                )
                latency_ms = int((time.monotonic() - t0) * 1000)

                if resp.status_code == 429:
                    return self._error_result("rate_limited", model, latency_ms)

                resp.raise_for_status()
                data = resp.json()

                text = ""
                for block in data.get("content", []):
                    if block.get("type") == "text":
                        text += block["text"]

                usage = data.get("usage", {})
                cost = self._estimate_cost(
                    model,
                    usage.get("input_tokens", 0),
                    usage.get("output_tokens", 0),
                )

                return {
                    "ok": True, "text": text, "model": model,
                    "provider": self.provider, "latency_ms": latency_ms,
                    "cost": cost, "error": None,
                }
        except httpx.TimeoutException:
            latency_ms = int((time.monotonic() - t0) * 1000)
            return self._error_result("timeout", model, latency_ms)
        except Exception as exc:
            latency_ms = int((time.monotonic() - t0) * 1000)
            logger.warning("AnthropicAdapter error: %s", exc)
            return self._error_result(str(exc), model, latency_ms)


class OpenAIAdapter(FrontierAdapter):
    """GPT models via OpenAI Chat Completions API."""

    provider = "openai"
    default_model = "gpt-4o"

    PRICING = {
        "gpt-4o": {"input": 2.50, "output": 10.0},
        "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    }

    def __init__(self, api_key: str, default_model: str = None):
        self.api_key = api_key
        if default_model:
            self.default_model = default_model

    def _estimate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        pricing = self.PRICING.get(model, {"input": 2.50, "output": 10.0})
        return (input_tokens * pricing["input"] + output_tokens * pricing["output"]) / 1_000_000

    async def send(self, prompt: str, system: str = "", model: str = None,
                   max_tokens: int = 4096, temperature: float = 0.7,
                   timeout: float = 60.0) -> dict:
        model = model or self.default_model
        t0 = time.monotonic()

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        body = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages,
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    json=body, headers=headers,
                )
                latency_ms = int((time.monotonic() - t0) * 1000)

                if resp.status_code == 429:
                    return self._error_result("rate_limited", model, latency_ms)

                resp.raise_for_status()
                data = resp.json()

                text = data["choices"][0]["message"]["content"]
                usage = data.get("usage", {})
                cost = self._estimate_cost(
                    model,
                    usage.get("prompt_tokens", 0),
                    usage.get("completion_tokens", 0),
                )

                return {
                    "ok": True, "text": text, "model": model,
                    "provider": self.provider, "latency_ms": latency_ms,
                    "cost": cost, "error": None,
                }
        except httpx.TimeoutException:
            latency_ms = int((time.monotonic() - t0) * 1000)
            return self._error_result("timeout", model, latency_ms)
        except Exception as exc:
            latency_ms = int((time.monotonic() - t0) * 1000)
            logger.warning("OpenAIAdapter error: %s", exc)
            return self._error_result(str(exc), model, latency_ms)


class GeminiAdapter(FrontierAdapter):
    """Gemini models via Google Generative Language API."""

    provider = "google"
    default_model = "gemini-2.5-flash"

    PRICING = {
        "gemini-2.5-flash": {"input": 0.15, "output": 0.60},
        "gemini-2.5-pro": {"input": 1.25, "output": 10.0},
        "gemini-2.0-flash": {"input": 0.075, "output": 0.30},
    }

    def __init__(self, api_key: str, default_model: str = None):
        self.api_key = api_key
        if default_model:
            self.default_model = default_model

    def _estimate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        pricing = self.PRICING.get(model, {"input": 0.075, "output": 0.30})
        return (input_tokens * pricing["input"] + output_tokens * pricing["output"]) / 1_000_000

    async def send(self, prompt: str, system: str = "", model: str = None,
                   max_tokens: int = 4096, temperature: float = 0.7,
                   timeout: float = 60.0) -> dict:
        model = model or self.default_model
        t0 = time.monotonic()

        contents = [{"parts": [{"text": prompt}], "role": "user"}]
        body = {
            "contents": contents,
            "generationConfig": {
                "maxOutputTokens": max_tokens,
                "temperature": temperature,
            },
        }
        if system:
            body["systemInstruction"] = {"parts": [{"text": system}]}

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}"

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.post(url, json=body)
                latency_ms = int((time.monotonic() - t0) * 1000)

                if resp.status_code == 429:
                    return self._error_result("rate_limited", model, latency_ms)

                resp.raise_for_status()
                data = resp.json()

                candidates = data.get("candidates", [])
                if not candidates:
                    return self._error_result("no_candidates", model, latency_ms)

                text = ""
                for part in candidates[0].get("content", {}).get("parts", []):
                    text += part.get("text", "")

                usage = data.get("usageMetadata", {})
                cost = self._estimate_cost(
                    model,
                    usage.get("promptTokenCount", 0),
                    usage.get("candidatesTokenCount", 0),
                )

                return {
                    "ok": True, "text": text, "model": model,
                    "provider": self.provider, "latency_ms": latency_ms,
                    "cost": cost, "error": None,
                }
        except httpx.TimeoutException:
            latency_ms = int((time.monotonic() - t0) * 1000)
            return self._error_result("timeout", model, latency_ms)
        except Exception as exc:
            latency_ms = int((time.monotonic() - t0) * 1000)
            logger.warning("GeminiAdapter error: %s", exc)
            return self._error_result(str(exc), model, latency_ms)


class LocalAdapter(FrontierAdapter):
    """Local models via SubAgentDispatch — no boundary crossing, different DNA."""

    provider = "local"
    default_model = "local-qwen-72b"

    # Model name → SubAgentDispatch node
    MODEL_NODES = {
        "local-qwen-72b": "redfin_vllm",
        "local-qwen3-30b": "bmasass_qwen3",
        "local-llama-70b": "sasass2_ollama",
    }

    def __init__(self):
        self._dispatcher = None

    def _get_dispatcher(self):
        if self._dispatcher is None:
            from lib.sub_agent_dispatch import SubAgentDispatch
            self._dispatcher = SubAgentDispatch()
        return self._dispatcher

    async def send(self, prompt: str, system: str = "", model: str = None,
                   max_tokens: int = 4096, temperature: float = 0.7,
                   timeout: float = 60.0) -> dict:
        model = model or self.default_model
        node = self.MODEL_NODES.get(model, "redfin_vllm")
        t0 = time.monotonic()

        try:
            dispatcher = self._get_dispatcher()
            result = dispatcher.dispatch_with_fallback(
                prompt, system=system, node=node,
                temperature=temperature, max_tokens=max_tokens,
            )
            latency_ms = int((time.monotonic() - t0) * 1000)

            if result["ok"]:
                return {
                    "ok": True, "text": result["text"], "model": model,
                    "provider": self.provider, "latency_ms": latency_ms,
                    "cost": 0.0, "error": None,
                }
            else:
                return self._error_result(result["text"], model, latency_ms)
        except Exception as exc:
            latency_ms = int((time.monotonic() - t0) * 1000)
            logger.warning("LocalAdapter error: %s", exc)
            return self._error_result(str(exc), model, latency_ms)


def get_adapters(config: dict) -> dict:
    """Build adapter instances from consultation_ring config section.

    Returns dict mapping provider name to adapter instance.
    Only returns adapters with valid API keys.
    """
    from lib.secrets_loader import get_secret

    adapters = {}

    # Anthropic (we have this key)
    if config.get("anthropic", {}).get("enabled", True):
        try:
            api_key = get_secret("ANTHROPIC_API_KEY")
            adapters["anthropic"] = AnthropicAdapter(
                api_key=api_key,
                default_model=config.get("anthropic", {}).get("model", "claude-sonnet-4-6"),
            )
        except RuntimeError:
            logger.warning("ANTHROPIC_API_KEY not found, Anthropic adapter disabled")

    # OpenAI
    if config.get("openai", {}).get("enabled", False):
        try:
            api_key = get_secret("OPENAI_API_KEY")
            adapters["openai"] = OpenAIAdapter(
                api_key=api_key,
                default_model=config.get("openai", {}).get("model", "gpt-4o"),
            )
        except RuntimeError:
            logger.info("OPENAI_API_KEY not found, OpenAI adapter disabled")

    # Gemini
    if config.get("gemini", {}).get("enabled", False):
        try:
            api_key = get_secret("GEMINI_API_KEY")
            adapters["google"] = GeminiAdapter(
                api_key=api_key,
                default_model=config.get("gemini", {}).get("model", "gemini-2.0-flash"),
            )
        except RuntimeError:
            logger.info("GEMINI_API_KEY not found, Gemini adapter disabled")

    # Local (always available)
    if config.get("local", {}).get("enabled", True):
        adapters["local"] = LocalAdapter()

    return adapters
