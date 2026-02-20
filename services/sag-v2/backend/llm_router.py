"""
SAG v2 — Pluggable LLM Router
================================
Supports: vLLM (local), OpenAI, Anthropic, Azure OpenAI.
Selected via LLM_PROVIDER env var.

All providers implement the same interface: chat(messages, tools) -> response
"""

import os
import sys
import json
import logging
from typing import Optional

import httpx

sys.path.insert(0, '/ganuda/lib')
try:
    from secrets_loader import get_secret
except ImportError:
    get_secret = None

logger = logging.getLogger('sag-v2.llm_router')


def _secret(key: str, default: str = "") -> str:
    if get_secret:
        try:
            return get_secret(key)
        except RuntimeError:
            pass
    return os.environ.get(key, default)


class LLMRouter:
    """Routes LLM requests to the configured provider."""

    def __init__(self):
        self.provider = os.environ.get("LLM_PROVIDER", "vllm").lower()
        self.model = os.environ.get("LLM_MODEL", "")
        self.base_url = os.environ.get("LLM_BASE_URL", "")
        self.api_key = _secret("LLM_API_KEY", "not-needed")
        self._configure()

    def _configure(self):
        if self.provider == "vllm":
            self.base_url = self.base_url or "http://localhost:8000/v1"
            self.model = self.model or os.environ.get('VLLM_MODEL', '/ganuda/models/qwen2.5-72b-instruct-awq')
        elif self.provider == "openai":
            self.base_url = self.base_url or "https://api.openai.com/v1"
            self.model = self.model or "gpt-4o"
            self.api_key = self.api_key or _secret("OPENAI_API_KEY")
        elif self.provider == "anthropic":
            self.base_url = self.base_url or "https://api.anthropic.com"
            self.model = self.model or "claude-sonnet-4-5-20250929"
            self.api_key = self.api_key or _secret("ANTHROPIC_API_KEY")
        elif self.provider == "azure":
            self.model = self.model or "gpt-4o"
            self.api_key = self.api_key or _secret("AZURE_OPENAI_API_KEY")
        logger.info("LLM Router: provider=%s model=%s base_url=%s", self.provider, self.model, self.base_url)

    async def chat(self, messages: list, tools: Optional[list] = None, system: str = "") -> dict:
        """Send chat completion request. Returns OpenAI-format response."""
        if self.provider in ("vllm", "openai", "azure"):
            return await self._openai_compatible(messages, tools, system)
        elif self.provider == "anthropic":
            return await self._anthropic_chat(messages, tools, system)
        else:
            return {"error": f"Unknown provider: {self.provider}"}

    async def _openai_compatible(self, messages: list, tools: Optional[list], system: str) -> dict:
        """OpenAI-compatible API (works with vLLM, OpenAI, Azure)."""
        headers = {"Content-Type": "application/json"}
        if self.api_key and self.api_key != "not-needed":
            headers["Authorization"] = f"Bearer {self.api_key}"

        # Prepend system message if provided
        full_messages = messages.copy()
        if system:
            full_messages.insert(0, {"role": "system", "content": system})

        payload = {
            "model": self.model,
            "messages": full_messages,
            "max_tokens": 4096,
            "temperature": 0.3,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        url = f"{self.base_url}/chat/completions"
        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                resp = await client.post(url, headers=headers, json=payload)
                resp.raise_for_status()
                return resp.json()
            except httpx.HTTPStatusError as e:
                logger.error("LLM error: %s %s", e.response.status_code, e.response.text[:300])
                return {"error": f"LLM HTTP {e.response.status_code}", "detail": e.response.text[:300]}
            except httpx.RequestError as e:
                logger.error("LLM request failed: %s", e)
                return {"error": str(e)}

    async def _anthropic_chat(self, messages: list, tools: Optional[list], system: str) -> dict:
        """Anthropic Messages API — converts to/from OpenAI format."""
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
        }

        # Convert OpenAI tool format to Anthropic format
        anthropic_tools = []
        if tools:
            for t in tools:
                func = t.get("function", t)
                anthropic_tools.append({
                    "name": func.get("name", ""),
                    "description": func.get("description", ""),
                    "input_schema": func.get("parameters", {}),
                })

        payload = {
            "model": self.model,
            "max_tokens": 4096,
            "messages": messages,
        }
        if system:
            payload["system"] = system
        if anthropic_tools:
            payload["tools"] = anthropic_tools

        url = f"{self.base_url}/v1/messages"
        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                resp = await client.post(url, headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()
                # Convert Anthropic response to OpenAI format
                return self._anthropic_to_openai(data)
            except httpx.HTTPStatusError as e:
                return {"error": f"Anthropic HTTP {e.response.status_code}", "detail": e.response.text[:300]}
            except httpx.RequestError as e:
                return {"error": str(e)}

    def _anthropic_to_openai(self, data: dict) -> dict:
        """Convert Anthropic Messages response to OpenAI format."""
        content_blocks = data.get("content", [])
        text_parts = []
        tool_calls = []
        for i, block in enumerate(content_blocks):
            if block.get("type") == "text":
                text_parts.append(block["text"])
            elif block.get("type") == "tool_use":
                tool_calls.append({
                    "id": block.get("id", f"call_{i}"),
                    "type": "function",
                    "function": {
                        "name": block["name"],
                        "arguments": json.dumps(block.get("input", {})),
                    },
                })

        message = {"role": "assistant", "content": "\n".join(text_parts) if text_parts else None}
        if tool_calls:
            message["tool_calls"] = tool_calls
        return {"choices": [{"message": message, "finish_reason": data.get("stop_reason", "stop")}]}

    def get_info(self) -> dict:
        return {"provider": self.provider, "model": self.model, "base_url": self.base_url}