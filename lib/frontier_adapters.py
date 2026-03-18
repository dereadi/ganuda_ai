"""
Frontier model adapters for the Consultation Ring.
====================================================
Created: 2026-03-14 (original)
Updated: 2026-03-18 — Task #1426: Consultation Ring interface alignment
Council Vote: a3ee2a8066e04490 (UNANIMOUS)
Patent Brief #7: Tokenized Air-Gap Proxy

Each adapter speaks a different provider API but returns a uniform
ConsultationResponse dataclass.

Adapters:
    AnthropicAdapter  — Claude models via api.anthropic.com (production-ready)
    OpenAIAdapter     — GPT models via api.openai.com (stub until key provisioned)
    GeminiAdapter     — Gemini models via generativelanguage.googleapis.com (stub)
    LocalAdapter      — Local models via SubAgentDispatch (no boundary crossing)

DC-9:  Local adapter uses cluster models — don't burn expensive tokens on reflex work.
DC-11: Same send() interface at every scale.
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from typing import Optional

import httpx

from lib.secrets_loader import get_secret

logger = logging.getLogger("consultation_ring.adapters")


@dataclass
class ConsultationResponse:
    """Standard response from any frontier adapter."""
    text: str
    model: str
    adapter: str
    token_count_in: int
    token_count_out: int
    latency_ms: int
    cost_estimate: float
    raw_response: dict = field(default_factory=dict)


class BaseAdapter:
    """Base class for all frontier adapters."""
    name: str = "base"

    def __init__(self, config: dict):
        self.config = config
        self.enabled = config.get("enabled", False)

    async def send(self, prompt: str, context: str = "", max_tokens: int = 4096) -> ConsultationResponse:
        raise NotImplementedError

    def is_available(self) -> bool:
        return self.enabled

    def _error_response(self, text: str, model: str, latency_ms: int = 0) -> ConsultationResponse:
        """Helper for building error/fallback responses."""
        return ConsultationResponse(
            text=text,
            model=model,
            adapter=self.name,
            token_count_in=0,
            token_count_out=0,
            latency_ms=latency_ms,
            cost_estimate=0.0,
            raw_response={},
        )


class AnthropicAdapter(BaseAdapter):
    """Anthropic Claude API adapter. Primary frontier. Production-ready."""
    name = "anthropic"

    API_URL = "https://api.anthropic.com/v1/messages"
    API_VERSION = "2023-06-01"

    # Pricing per 1M tokens (input/output)
    PRICING = {
        "claude-sonnet-4-6": {"input": 3.0, "output": 15.0},
        "claude-sonnet-4-20250514": {"input": 3.0, "output": 15.0},
        "claude-3-5-sonnet-20241022": {"input": 3.0, "output": 15.0},
        "claude-haiku-4-5-20251001": {"input": 0.80, "output": 4.0},
        "claude-opus-4-20250514": {"input": 15.0, "output": 75.0},
    }
    DEFAULT_PRICING = {"input": 3.0, "output": 15.0}

    def __init__(self, config: dict):
        super().__init__(config)
        self.model = config.get("model", "claude-sonnet-4-6")
        self.timeout = config.get("timeout", 120.0)

    def _estimate_cost(self, tokens_in: int, tokens_out: int) -> float:
        pricing = self.PRICING.get(self.model, self.DEFAULT_PRICING)
        return round(
            (tokens_in * pricing["input"] + tokens_out * pricing["output"]) / 1_000_000,
            6,
        )

    async def send(self, prompt: str, context: str = "", max_tokens: int = 4096) -> ConsultationResponse:
        """Send prompt to Anthropic Messages API."""
        if not self.enabled:
            return self._error_response("Anthropic adapter not enabled", self.model)

        try:
            api_key = get_secret("ANTHROPIC_API_KEY")
        except RuntimeError as exc:
            logger.error("Anthropic API key resolution failed: %s", exc)
            return self._error_response(f"API key error: {exc}", self.model)

        headers = {
            "x-api-key": api_key,
            "anthropic-version": self.API_VERSION,
            "content-type": "application/json",
        }

        # Build message — system goes in body top-level, context prepended to prompt
        user_content = f"{context}\n\n{prompt}" if context else prompt
        body = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": user_content}],
        }

        t0 = time.monotonic()
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(self.API_URL, headers=headers, json=body)

            latency_ms = int((time.monotonic() - t0) * 1000)

            # Rate limit — graceful, don't crash
            if resp.status_code == 429:
                logger.warning("Anthropic rate limited (429). Latency: %dms", latency_ms)
                return ConsultationResponse(
                    text="rate_limited",
                    model=self.model,
                    adapter=self.name,
                    token_count_in=0,
                    token_count_out=0,
                    latency_ms=latency_ms,
                    cost_estimate=0.0,
                    raw_response={"status_code": 429, "body": resp.text},
                )

            if resp.status_code != 200:
                logger.error("Anthropic API error %d: %s", resp.status_code, resp.text[:500])
                return ConsultationResponse(
                    text=f"api_error_{resp.status_code}",
                    model=self.model,
                    adapter=self.name,
                    token_count_in=0,
                    token_count_out=0,
                    latency_ms=latency_ms,
                    cost_estimate=0.0,
                    raw_response={"status_code": resp.status_code, "body": resp.text},
                )

            data = resp.json()

            # Extract text from content blocks
            text = ""
            for block in data.get("content", []):
                if block.get("type") == "text":
                    text += block["text"]

            usage = data.get("usage", {})
            tokens_in = usage.get("input_tokens", 0)
            tokens_out = usage.get("output_tokens", 0)

            return ConsultationResponse(
                text=text,
                model=data.get("model", self.model),
                adapter=self.name,
                token_count_in=tokens_in,
                token_count_out=tokens_out,
                latency_ms=latency_ms,
                cost_estimate=self._estimate_cost(tokens_in, tokens_out),
                raw_response=data,
            )

        except httpx.TimeoutException:
            latency_ms = int((time.monotonic() - t0) * 1000)
            logger.warning("Anthropic request timed out after %dms", latency_ms)
            return self._error_response("timeout", self.model, latency_ms)
        except httpx.HTTPError as exc:
            latency_ms = int((time.monotonic() - t0) * 1000)
            logger.error("Anthropic HTTP error: %s", exc)
            return self._error_response(f"http_error: {exc}", self.model, latency_ms)


class OpenAIAdapter(BaseAdapter):
    """OpenAI GPT adapter. Stub — enabled: false until key provisioned."""
    name = "openai"

    API_URL = "https://api.openai.com/v1/chat/completions"

    PRICING = {
        "gpt-4o": {"input": 2.50, "output": 10.0},
        "gpt-4o-mini": {"input": 0.15, "output": 0.60},
        "gpt-4-turbo": {"input": 10.0, "output": 30.0},
    }
    DEFAULT_PRICING = {"input": 2.50, "output": 10.0}

    def __init__(self, config: dict):
        super().__init__(config)
        self.model = config.get("model", "gpt-4o")
        self.timeout = config.get("timeout", 120.0)

    def _estimate_cost(self, tokens_in: int, tokens_out: int) -> float:
        pricing = self.PRICING.get(self.model, self.DEFAULT_PRICING)
        return round(
            (tokens_in * pricing["input"] + tokens_out * pricing["output"]) / 1_000_000,
            6,
        )

    async def send(self, prompt: str, context: str = "", max_tokens: int = 4096) -> ConsultationResponse:
        """Send prompt to OpenAI Chat Completions API."""
        if not self.enabled:
            return ConsultationResponse(
                text="OpenAI adapter not configured",
                model=self.model,
                adapter=self.name,
                token_count_in=0,
                token_count_out=0,
                latency_ms=0,
                cost_estimate=0.0,
                raw_response={},
            )

        try:
            api_key = get_secret("OPENAI_API_KEY")
        except RuntimeError as exc:
            logger.error("OpenAI API key resolution failed: %s", exc)
            return self._error_response(f"API key error: {exc}", self.model)

        messages = []
        if context:
            messages.append({"role": "system", "content": context})
        messages.append({"role": "user", "content": prompt})

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": messages,
        }

        t0 = time.monotonic()
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(self.API_URL, headers=headers, json=body)

            latency_ms = int((time.monotonic() - t0) * 1000)

            if resp.status_code == 429:
                logger.warning("OpenAI rate limited (429). Latency: %dms", latency_ms)
                return self._error_response("rate_limited", self.model, latency_ms)

            if resp.status_code != 200:
                logger.error("OpenAI API error %d: %s", resp.status_code, resp.text[:500])
                return self._error_response(f"api_error_{resp.status_code}", self.model, latency_ms)

            data = resp.json()
            text = data["choices"][0]["message"]["content"]

            usage = data.get("usage", {})
            tokens_in = usage.get("prompt_tokens", 0)
            tokens_out = usage.get("completion_tokens", 0)

            return ConsultationResponse(
                text=text,
                model=data.get("model", self.model),
                adapter=self.name,
                token_count_in=tokens_in,
                token_count_out=tokens_out,
                latency_ms=latency_ms,
                cost_estimate=self._estimate_cost(tokens_in, tokens_out),
                raw_response=data,
            )

        except httpx.TimeoutException:
            latency_ms = int((time.monotonic() - t0) * 1000)
            logger.warning("OpenAI request timed out after %dms", latency_ms)
            return self._error_response("timeout", self.model, latency_ms)
        except httpx.HTTPError as exc:
            latency_ms = int((time.monotonic() - t0) * 1000)
            logger.error("OpenAI HTTP error: %s", exc)
            return self._error_response(f"http_error: {exc}", self.model, latency_ms)


class GeminiAdapter(BaseAdapter):
    """Google Gemini adapter. Stub — enabled: false until key provisioned."""
    name = "gemini"

    API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"

    PRICING = {
        "gemini-2.5-flash": {"input": 0.15, "output": 0.60},
        "gemini-2.5-pro": {"input": 1.25, "output": 10.0},
        "gemini-2.0-flash": {"input": 0.075, "output": 0.30},
    }
    DEFAULT_PRICING = {"input": 0.15, "output": 0.60}

    def __init__(self, config: dict):
        super().__init__(config)
        self.model = config.get("model", "gemini-2.5-flash")
        self.timeout = config.get("timeout", 120.0)

    def _estimate_cost(self, tokens_in: int, tokens_out: int) -> float:
        pricing = self.PRICING.get(self.model, self.DEFAULT_PRICING)
        return round(
            (tokens_in * pricing["input"] + tokens_out * pricing["output"]) / 1_000_000,
            6,
        )

    async def send(self, prompt: str, context: str = "", max_tokens: int = 4096) -> ConsultationResponse:
        """Send prompt to Gemini generateContent API."""
        if not self.enabled:
            return ConsultationResponse(
                text="Gemini adapter not configured",
                model=self.model,
                adapter=self.name,
                token_count_in=0,
                token_count_out=0,
                latency_ms=0,
                cost_estimate=0.0,
                raw_response={},
            )

        try:
            api_key = get_secret("GEMINI_API_KEY")
        except RuntimeError as exc:
            logger.error("Gemini API key resolution failed: %s", exc)
            return self._error_response(f"API key error: {exc}", self.model)

        user_content = f"{context}\n\n{prompt}" if context else prompt
        url = f"{self.API_BASE}/{self.model}:generateContent?key={api_key}"

        body = {
            "contents": [{"parts": [{"text": user_content}], "role": "user"}],
            "generationConfig": {
                "maxOutputTokens": max_tokens,
            },
        }
        if context:
            body["systemInstruction"] = {"parts": [{"text": context}]}

        t0 = time.monotonic()
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(url, json=body)

            latency_ms = int((time.monotonic() - t0) * 1000)

            if resp.status_code == 429:
                logger.warning("Gemini rate limited (429). Latency: %dms", latency_ms)
                return self._error_response("rate_limited", self.model, latency_ms)

            if resp.status_code != 200:
                logger.error("Gemini API error %d: %s", resp.status_code, resp.text[:500])
                return self._error_response(f"api_error_{resp.status_code}", self.model, latency_ms)

            data = resp.json()

            candidates = data.get("candidates", [])
            if not candidates:
                return self._error_response("no_candidates", self.model, latency_ms)

            text = ""
            for part in candidates[0].get("content", {}).get("parts", []):
                text += part.get("text", "")

            usage = data.get("usageMetadata", {})
            tokens_in = usage.get("promptTokenCount", 0)
            tokens_out = usage.get("candidatesTokenCount", 0)

            return ConsultationResponse(
                text=text,
                model=self.model,
                adapter=self.name,
                token_count_in=tokens_in,
                token_count_out=tokens_out,
                latency_ms=latency_ms,
                cost_estimate=self._estimate_cost(tokens_in, tokens_out),
                raw_response=data,
            )

        except httpx.TimeoutException:
            latency_ms = int((time.monotonic() - t0) * 1000)
            logger.warning("Gemini request timed out after %dms", latency_ms)
            return self._error_response("timeout", self.model, latency_ms)
        except httpx.HTTPError as exc:
            latency_ms = int((time.monotonic() - t0) * 1000)
            logger.error("Gemini HTTP error: %s", exc)
            return self._error_response(f"http_error: {exc}", self.model, latency_ms)


class LocalAdapter(BaseAdapter):
    """Local model adapter via SubAgentDispatch. Different DNA without external API cost."""
    name = "local"

    # Model name → SubAgentDispatch node
    MODEL_NODES = {
        "local-qwen-72b": "redfin_vllm",
        "local-qwen3-30b": "bmasass_qwen3",
        "local-llama-70b": "sasass_llama70",
        "local-coder-32b": "sasass2_ollama",
    }

    def __init__(self, config: dict):
        super().__init__(config)
        self.node = config.get("node", "redfin_vllm")
        self.temperature = config.get("temperature", 0.3)
        self._dispatcher = None

    def _get_dispatcher(self):
        """Lazy-init SubAgentDispatch to avoid import-time side effects."""
        if self._dispatcher is None:
            from lib.sub_agent_dispatch import SubAgentDispatch
            self._dispatcher = SubAgentDispatch()
        return self._dispatcher

    def is_available(self) -> bool:
        """Local adapter is always available if enabled — no API key needed."""
        return self.enabled

    async def send(self, prompt: str, context: str = "", max_tokens: int = 4096) -> ConsultationResponse:
        """Send prompt to local cluster model via SubAgentDispatch.

        Wraps the synchronous dispatch() in run_in_executor to stay async.
        """
        if not self.enabled:
            return self._error_response("Local adapter not enabled", self.node)

        system = context if context else ""

        loop = asyncio.get_event_loop()
        dispatcher = self._get_dispatcher()

        result = await loop.run_in_executor(
            None,
            lambda: dispatcher.dispatch_with_fallback(
                prompt=prompt,
                system=system,
                node=self.node,
                temperature=self.temperature,
                max_tokens=max_tokens,
            ),
        )

        latency_ms = result.get("latency_ms", 0)
        actual_node = result.get("node", self.node)
        node_cfg = dispatcher.nodes.get(actual_node, {})
        model_name = node_cfg.get("model", actual_node)

        if result.get("ok"):
            return ConsultationResponse(
                text=result.get("text", ""),
                model=model_name,
                adapter=self.name,
                token_count_in=0,   # Local dispatch doesn't report token counts
                token_count_out=0,
                latency_ms=latency_ms,
                cost_estimate=0.0,  # No API cost for local models
                raw_response=result,
            )
        else:
            return ConsultationResponse(
                text=result.get("text", "dispatch_failed"),
                model=model_name,
                adapter=self.name,
                token_count_in=0,
                token_count_out=0,
                latency_ms=latency_ms,
                cost_estimate=0.0,
                raw_response=result,
            )


def get_adapter(provider: str, config: dict) -> BaseAdapter:
    """Factory function to get the right adapter.

    Args:
        provider: One of 'anthropic', 'openai', 'gemini', 'local'
        config: Adapter configuration dict. Common keys:
            enabled (bool): Whether the adapter is active
            model (str): Model identifier
            timeout (float): Request timeout in seconds
            node (str): For local adapter — target cluster node

    Returns:
        Initialized adapter instance.

    Raises:
        ValueError: If provider is not recognized.
    """
    adapters = {
        "anthropic": AnthropicAdapter,
        "openai": OpenAIAdapter,
        "gemini": GeminiAdapter,
        "local": LocalAdapter,
    }
    cls = adapters.get(provider)
    if not cls:
        raise ValueError(f"Unknown provider: {provider}")
    return cls(config)
