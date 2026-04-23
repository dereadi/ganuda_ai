"""
Sub-Agent Dispatch Library
Dispatches reflex and deliberation-tier work to local small models across the Cherokee AI Federation cluster.

DC-9: Don't burn expensive tokens on reflex-layer work.
DC-10: The reflex fires before the cortex.
DC-11: Same SENSE -> REACT -> EVALUATE pattern at every scale.

Node inventory:
  redfin_vllm    - vLLM Qwen2.5-7B at localhost:8000 (OpenAI-compatible)
  bmasass_qwen3  - MLX Qwen3-30B-A3B at 100.103.27.106:8800 (Tailscale, mobile)
  sasass_ollama  - Ollama at 192.168.132.241:11434 (qwen2.5:7b, llama3.2, gemma2)
  sasass2_ollama - Ollama at 192.168.132.242:11434 (qwen2.5-coder:32b, llama3.3:70b, codellama:34b, resonance models)
"""

import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger("sub_agent_dispatch")


class SubAgentTimeout(Exception):
    """Raised when a dispatch request times out."""
    pass


class SubAgentError(Exception):
    """Raised when a dispatch request fails."""
    pass


class SubAgentDispatch:
    """Dispatch work to local models across the cluster."""

    NODES = {
        # === Redfin (RTX PRO 6000 96GB) — fast path ===
        "redfin_vllm": {
            "url": "http://localhost:8000/v1",
            "model": os.environ.get("VLLM_MODEL", "Qwen/Qwen3.6-35B-A3B"),
            "type": "openai",
            "tier": 1,
        },
        # === bmasass (M4 Max 128GB) — council Raven/Turtle paths ===
        "bmasass_qwen3": {
            "url": "http://100.103.27.106:8800/v1",
            "model": "mlx-community/Qwen3-30B-A3B-4bit",
            "type": "openai",
            "tier": 2,
        },
        "bmasass_llama70": {
            "url": "http://100.103.27.106:8801/v1",
            "model": "mlx-community/Llama-3.3-70B-Instruct-4bit",
            "type": "openai",
            "tier": 2,
        },
        # === sasass (64GB) — research expansion ===
        "sasass_ollama": {
            "url": "http://192.168.132.241:11434",
            "model": "qwen2.5:7b",
            "type": "ollama",
            "tier": 3,
        },
        "sasass_mixtral": {
            "url": "http://192.168.132.241:11434",
            "model": "mixtral:latest",
            "type": "ollama",
            "tier": 3,
        },
        "sasass_devstral": {
            "url": "http://192.168.132.241:11434",
            "model": "devstral:latest",
            "type": "ollama",
            "tier": 3,
        },
        "sasass_llama70": {
            "url": "http://192.168.132.241:11434",
            "model": "llama3.3:latest",
            "type": "ollama",
            "tier": 2,
        },
        # === sasass2 (64GB) — THUNDERDUCK ZERO — Jr code reviewer ===
        "sasass2_ollama": {
            "url": "http://192.168.132.242:11434",
            "model": "qwen2.5-coder:32b",
            "type": "ollama",
            "tier": 3,
        },
        "sasass2_codellama": {
            "url": "http://192.168.132.242:11434",
            "model": "codellama:34b",
            "type": "ollama",
            "tier": 3,
        },
    }

    # Fallback chains: if primary fails, try next in list
    FALLBACK = {
        "redfin_vllm": ["sasass_ollama", "bmasass_qwen3"],
        "sasass_ollama": ["redfin_vllm", "sasass2_ollama"],
        "sasass2_ollama": ["sasass_ollama", "redfin_vllm"],
        "bmasass_qwen3": ["redfin_vllm", "sasass_ollama"],
    }

    def __init__(self, nodes: Optional[Dict[str, dict]] = None, default_timeout: float = 30.0):
        """Initialize dispatcher. Optionally override the node registry."""
        self.nodes = dict(nodes) if nodes else dict(self.NODES)
        self.default_timeout = default_timeout

    def _build_payload(self, node_cfg: dict, prompt: str, system: str,
                       temperature: float, max_tokens: int) -> tuple:
        """Build the request URL and JSON payload for a node.

        Returns (url, payload) tuple.
        """
        ntype = node_cfg["type"]

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        if ntype == "openai":
            url = f"{node_cfg['url']}/chat/completions"
            payload = {
                "model": node_cfg["model"],
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
            }
        elif ntype == "ollama":
            url = f"{node_cfg['url']}/api/chat"
            payload = {
                "model": node_cfg["model"],
                "messages": messages,
                "stream": False,
                "options": {
                    "num_predict": max_tokens,
                    "temperature": temperature,
                },
            }
        else:
            raise SubAgentError(f"Unknown node type: {ntype}")

        return url, payload

    def _extract_text(self, node_cfg: dict, resp_json: dict) -> str:
        """Extract response text from the API response."""
        ntype = node_cfg["type"]

        if ntype == "openai":
            return resp_json["choices"][0]["message"]["content"]
        elif ntype == "ollama":
            return resp_json["message"]["content"]
        else:
            raise SubAgentError(f"Unknown node type: {ntype}")

    def dispatch(self, prompt: str, system: str = "", node: str = "redfin_vllm",
                 temperature: float = 0.3, max_tokens: int = 2048,
                 timeout: Optional[float] = None) -> dict:
        """Send a prompt to a specific node.

        Returns {"ok": bool, "text": str, "node": str, "latency_ms": int}
        """
        node_cfg = self.nodes.get(node)
        if not node_cfg:
            return {"ok": False, "text": f"Unknown node: {node}", "node": node, "latency_ms": 0}

        if timeout is None:
            timeout = self.default_timeout

        url, payload = self._build_payload(node_cfg, prompt, system, temperature, max_tokens)

        t0 = time.monotonic()
        try:
            resp = requests.post(url, json=payload, timeout=timeout)
            resp.raise_for_status()
            latency_ms = int((time.monotonic() - t0) * 1000)
            text = self._extract_text(node_cfg, resp.json())
            return {"ok": True, "text": text, "node": node, "latency_ms": latency_ms}
        except requests.Timeout:
            latency_ms = int((time.monotonic() - t0) * 1000)
            logger.warning("Dispatch to %s timed out after %dms", node, latency_ms)
            return {"ok": False, "text": "timeout", "node": node, "latency_ms": latency_ms}
        except requests.RequestException as exc:
            latency_ms = int((time.monotonic() - t0) * 1000)
            logger.warning("Dispatch to %s failed: %s", node, exc)
            return {"ok": False, "text": str(exc), "node": node, "latency_ms": latency_ms}
        except (KeyError, ValueError) as exc:
            latency_ms = int((time.monotonic() - t0) * 1000)
            logger.warning("Bad response from %s: %s", node, exc)
            return {"ok": False, "text": f"parse error: {exc}", "node": node, "latency_ms": latency_ms}

    def dispatch_fastest(self, prompt: str, system: str = "",
                         nodes: Optional[List[str]] = None,
                         timeout: float = 10.0) -> dict:
        """Race multiple nodes, return first response. For reflex-tier work.

        Returns the first successful result dict, or the last failure if all fail.
        """
        if nodes is None:
            nodes = list(self.nodes.keys())

        last_failure = {"ok": False, "text": "no nodes provided", "node": "", "latency_ms": 0}

        with ThreadPoolExecutor(max_workers=len(nodes)) as pool:
            futures = {
                pool.submit(self.dispatch, prompt, system, n, 0.3, 2048, timeout): n
                for n in nodes
                if n in self.nodes
            }

            for future in as_completed(futures):
                result = future.result()
                if result["ok"]:
                    # Cancel remaining futures (best effort)
                    for f in futures:
                        f.cancel()
                    return result
                last_failure = result

        return last_failure

    def dispatch_consensus(self, prompt: str, system: str = "",
                           nodes: Optional[List[str]] = None,
                           temperature: float = 0.7,
                           timeout: float = 60.0) -> dict:
        """Send to multiple nodes, return all responses for comparison. For deliberation-tier.

        Returns {"ok": bool, "responses": [result_dicts], "node_count": int, "success_count": int}
        """
        if nodes is None:
            nodes = list(self.nodes.keys())

        results = []
        with ThreadPoolExecutor(max_workers=len(nodes)) as pool:
            futures = {
                pool.submit(self.dispatch, prompt, system, n, temperature, 2048, timeout): n
                for n in nodes
                if n in self.nodes
            }
            for future in as_completed(futures):
                results.append(future.result())

        successes = [r for r in results if r["ok"]]
        return {
            "ok": len(successes) > 0,
            "responses": results,
            "node_count": len(results),
            "success_count": len(successes),
        }

    def health_check(self) -> dict:
        """Check which nodes are reachable.

        Returns {node_name: {"status": "up"|"down", "latency_ms": int}}
        """
        report = {}

        def _check_node(name: str, cfg: dict) -> tuple:
            t0 = time.monotonic()
            try:
                if cfg["type"] == "openai":
                    url = f"{cfg['url']}/models"
                elif cfg["type"] == "ollama":
                    url = f"{cfg['url']}/api/tags"
                else:
                    return name, {"status": "down", "latency_ms": 0}

                resp = requests.get(url, timeout=5)
                resp.raise_for_status()
                latency_ms = int((time.monotonic() - t0) * 1000)
                return name, {"status": "up", "latency_ms": latency_ms}
            except Exception:
                latency_ms = int((time.monotonic() - t0) * 1000)
                return name, {"status": "down", "latency_ms": latency_ms}

        with ThreadPoolExecutor(max_workers=len(self.nodes)) as pool:
            futures = [pool.submit(_check_node, name, cfg) for name, cfg in self.nodes.items()]
            for future in as_completed(futures):
                name, status = future.result()
                report[name] = status

        return report

    def warm_up(self, node: str) -> dict:
        """Pre-load a model into memory on an Ollama node.

        Sends keep_alive=-1 so the model stays loaded permanently.
        Returns dispatch result dict.
        """
        node_cfg = self.nodes.get(node)
        if not node_cfg:
            return {"ok": False, "text": f"Unknown node: {node}", "node": node, "latency_ms": 0}

        if node_cfg["type"] == "ollama":
            # Use the generate endpoint with keep_alive to load and pin the model
            url = f"{node_cfg['url']}/api/generate"
            payload = {
                "model": node_cfg["model"],
                "prompt": "ping",
                "keep_alive": -1,
                "options": {"num_predict": 1},
            }
            t0 = time.monotonic()
            try:
                resp = requests.post(url, json=payload, timeout=120)
                resp.raise_for_status()
                latency_ms = int((time.monotonic() - t0) * 1000)
                return {"ok": True, "text": "model loaded", "node": node, "latency_ms": latency_ms}
            except requests.RequestException as exc:
                latency_ms = int((time.monotonic() - t0) * 1000)
                return {"ok": False, "text": str(exc), "node": node, "latency_ms": latency_ms}
        else:
            # OpenAI/vLLM models are always loaded -- just do a health ping
            return self.dispatch("ping", system="Reply with pong.", node=node, max_tokens=8, timeout=10)

    def dispatch_with_fallback(self, prompt: str, system: str = "",
                               node: str = "redfin_vllm",
                               temperature: float = 0.3,
                               max_tokens: int = 2048) -> dict:
        """Dispatch with automatic fallback chain if the primary node fails.

        Tries the primary node, then each fallback in order.
        Returns the first successful result, or the last failure.
        """
        result = self.dispatch(prompt, system, node, temperature, max_tokens)
        if result["ok"]:
            return result

        fallbacks = self.FALLBACK.get(node, [])
        for fb_node in fallbacks:
            logger.info("Falling back from %s to %s", node, fb_node)
            result = self.dispatch(prompt, system, fb_node, temperature, max_tokens)
            if result["ok"]:
                return result

        return result

    # ---- Pre-built task functions ----

    def scan_stubs(self, content: str) -> list:
        """Extract named entities/stubs from content using local model.

        Returns list of stub dicts: [{"type": str, "name": str, "context": str}, ...]
        """
        system = (
            "Extract all named entities from the following content. "
            "Return ONLY a JSON array of objects with fields: "
            'type (person/company/organization/regulation/concept), name, context (one sentence explaining relevance). '
            "Be thorough -- every proper noun, every company name, every law or regulation mentioned. "
            "Return only valid JSON, no markdown fencing."
        )
        result = self.dispatch_with_fallback(content, system=system, node="sasass_ollama")
        if not result["ok"]:
            logger.error("scan_stubs failed on all nodes: %s", result["text"])
            return []
        return _parse_json(result["text"], default=[])

    def classify_thermal(self, content: str) -> dict:
        """Classify content by domain, priority, council_owner using local model.

        Returns {"category": str, "temperature": int, "keywords": [str], "council_owner": str}
        """
        system = (
            "Classify this memory into one of these categories: "
            "governance, technical, market, legal, cultural, operational, sacred. "
            "Suggest a temperature score (0-100, where 100 is sacred/permanent and 0 is ephemeral). "
            "Determine the council_owner: war_chief (technical/infra), peace_chief (business/culture), "
            "eagle_eye (observability), coyote (risk/trickster), turtle (stability), "
            "deer (market/business), otter (legal), crane (diplomacy). "
            "Return ONLY valid JSON: "
            '{"category": str, "temperature": int, "keywords": [up to 5 strings], "council_owner": str}. '
            "No markdown fencing."
        )
        result = self.dispatch_with_fallback(content, system=system, node="redfin_vllm")
        if not result["ok"]:
            logger.error("classify_thermal failed: %s", result["text"])
            return {"category": "unknown", "temperature": 50, "keywords": [], "council_owner": "unknown"}
        return _parse_json(result["text"], default={
            "category": "unknown", "temperature": 50, "keywords": [], "council_owner": "unknown"
        })

    def route_task(self, task_description: str) -> dict:
        """Route a task to appropriate council member and priority using local model.

        Returns {"domain": str, "priority": int, "council_owner": str, "reason": str}
        """
        system = (
            "You are a task router for the Cherokee AI Federation. "
            "Classify this task by domain: "
            "war_chief (technical: code, infrastructure, nodes, deployments) or "
            "peace_chief (business: research, diplomacy, market, legal, culture). "
            "Suggest priority 1-4 (1=critical, 4=low). "
            "Suggest a council_owner from: war_chief, peace_chief, eagle_eye, coyote, "
            "turtle, deer, otter, crane. "
            "Return ONLY valid JSON: "
            '{"domain": str, "priority": int, "council_owner": str, "reason": str}. '
            "No markdown fencing."
        )
        result = self.dispatch_with_fallback(task_description, system=system, node="redfin_vllm")
        if not result["ok"]:
            logger.error("route_task failed: %s", result["text"])
            return {"domain": "unknown", "priority": 3, "council_owner": "unknown", "reason": "dispatch failed"}
        return _parse_json(result["text"], default={
            "domain": "unknown", "priority": 3, "council_owner": "unknown", "reason": "parse failed"
        })

    def decompose_task(self, jr_instruction: str) -> list:
        """Break a Jr instruction into concrete implementation steps.

        Returns list of step description strings.
        """
        system = (
            "You are a task decomposition specialist for the Cherokee AI Federation. "
            "Break this Jr instruction into concrete implementation steps. "
            "Each step should be independently executable. "
            "Return ONLY a JSON array of step description strings. "
            "No markdown fencing."
        )
        result = self.dispatch_with_fallback(
            jr_instruction, system=system, node="sasass2_ollama", temperature=0.4, max_tokens=4096
        )
        if not result["ok"]:
            logger.error("decompose_task failed: %s", result["text"])
            return []
        return _parse_json(result["text"], default=[])

    def safety_check(self, proposed_action: str) -> dict:
        """Ethical/safety check before automated action.

        Returns {"safe": bool, "concerns": [str], "recommendation": str}
        """
        system = (
            "You are the conscience of the Cherokee AI Federation. "
            "Review this proposed automated action for safety, ethics, and alignment with federation values. "
            "Check for: PII exposure, destructive operations, unauthorized access, "
            "sovereignty violations, DC-9 waste. "
            "Return ONLY valid JSON: "
            '{"safe": bool, "concerns": [str], "recommendation": str}. '
            "No markdown fencing."
        )
        result = self.dispatch_with_fallback(
            proposed_action, system=system, node="sasass2_ollama"
        )
        if not result["ok"]:
            logger.error("safety_check failed: %s", result["text"])
            # Fail safe -- if we can't check, flag as unsafe
            return {"safe": False, "concerns": ["dispatch failed - cannot verify safety"], "recommendation": "escalate to Claude"}
        return _parse_json(result["text"], default={
            "safe": False, "concerns": ["parse failed"], "recommendation": "escalate to Claude"
        })

    def check_phi_anomaly(self, phi_value: float, system_state: dict) -> dict:
        """Check if a phi measurement is anomalous.

        Returns {"anomalous": bool, "interpretation": str, "escalate": bool}
        """
        system = (
            "You monitor organism health. Given a phi measurement and system state, "
            "determine if the reading is anomalous. "
            "Baseline resting phi is approximately 0.03-0.08. "
            "Negative phi indicates external-stimulus mode (adrenaline). "
            "Phi > 0.15 indicates high integration. "
            "Return ONLY valid JSON: "
            '{"anomalous": bool, "interpretation": str, "escalate": bool}. '
            "No markdown fencing."
        )
        content = json.dumps({"phi": phi_value, "state": system_state})
        result = self.dispatch_with_fallback(
            content, system=system, node="sasass2_ollama"
        )
        if not result["ok"]:
            logger.error("check_phi_anomaly failed: %s", result["text"])
            return {"anomalous": True, "interpretation": "dispatch failed", "escalate": True}
        return _parse_json(result["text"], default={
            "anomalous": True, "interpretation": "parse failed", "escalate": True
        })


def _parse_json(text: str, default: Any = None) -> Any:
    """Parse JSON from model output, handling common issues like markdown fencing."""
    text = text.strip()
    # Strip markdown code fences if present
    if text.startswith("```"):
        lines = text.split("\n")
        # Remove first and last lines (fences)
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to find JSON within the text
        for start_char, end_char in [("[", "]"), ("{", "}")]:
            start = text.find(start_char)
            end = text.rfind(end_char)
            if start != -1 and end != -1 and end > start:
                try:
                    return json.loads(text[start:end + 1])
                except json.JSONDecodeError:
                    continue
        logger.warning("Failed to parse JSON from model output: %s", text[:200])
        return default
