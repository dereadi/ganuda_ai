"""Ollama ring dispatcher — calls Ollama API on any node via Tailscale.

Used by Chain Protocol to dispatch prompts to Ollama models registered
in duplo_tool_registry (e.g. BigMac models at 100.106.9.80:11434).
"""

import requests
import time


def dispatch_ollama(payload: str, model: str = "llama3.1",
                    base_url: str = "http://localhost:11434") -> dict:
    """Dispatch a prompt to an Ollama model.

    Returns: {"result": str, "model": str, "latency_ms": float}
    """
    start = time.time()
    resp = requests.post(
        f"{base_url}/api/generate",
        json={"model": model, "prompt": payload, "stream": False},
        timeout=120,
    )
    resp.raise_for_status()
    latency = (time.time() - start) * 1000
    data = resp.json()
    return {
        "result": data.get("response", ""),
        "model": model,
        "latency_ms": round(latency, 1),
    }
