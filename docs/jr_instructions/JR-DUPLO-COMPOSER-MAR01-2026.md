# JR Instruction: Duplo Composer (Enzyme Assembly)

**Task**: DUPLO-COMPOSER-001
**Title**: Create Duplo Composer — Enzyme Assembly System
**Priority**: 2
**Assigned Jr**: Software Engineer Jr.

## Context

The Composer assembles an LLM + tool set + context profile into a callable "enzyme" — a function that catalyzes a specific reaction. Duplos are NOT agents. They don't wander, plan, or accumulate state. They are called, they catalyze, they return.

Depends on: `lib/duplo/registry.py` (must exist first)

## Files

Create `lib/duplo/composer.py`

```python
"""
Duplo Composer — Enzyme Assembly
Cherokee AI Federation — The Living Cell Architecture

Assembles an LLM backend + tool set + context profile (YAML) into a
callable enzyme. The enzyme is a function, not an object. It takes
a substrate (input), catalyzes a reaction (LLM + tools), and returns
a product (output).

The Composer reads:
  - A context profile YAML (the enzyme's active site)
  - A tool set from the registry (the amino acids)
  - Epigenetic modifiers from the DB (environmental adjustments)

Usage:
    from lib.duplo.composer import compose_enzyme

    enzyme = compose_enzyme("crawdad_scan")
    result = enzyme(substrate="Review this code for SQL injection vulnerabilities")
    # result = {"product": "...", "tools_used": [...], "tokens": {...}}
"""

import os
import yaml
import json
import time
import logging
import requests
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime

logger = logging.getLogger("duplo.composer")

# LLM backends — same as specialist_council.py
BACKENDS = {
    "qwen": {
        "url": "http://localhost:8000/v1/chat/completions",
        "model": os.environ.get("VLLM_MODEL", "/ganuda/models/qwen2.5-72b-instruct-awq"),
        "timeout": 60,
    },
    "deepseek": {
        "url": "http://192.168.132.21:8800/v1/chat/completions",
        "model": "mlx-community/DeepSeek-R1-Distill-Qwen-32B-4bit",
        "timeout": 120,
    },
    "vlm": {
        "url": "http://192.168.132.222:8092/v1/chat/completions",
        "model": "Qwen2-VL-7B-Instruct-AWQ",
        "timeout": 30,
    },
}

PROFILES_DIR = os.path.join(os.path.dirname(__file__), "context_profiles")


def _load_profile(profile_name: str) -> dict:
    """Load a YAML context profile from disk."""
    path = os.path.join(PROFILES_DIR, f"{profile_name}.yaml")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Context profile not found: {path}")
    with open(path, "r") as f:
        return yaml.safe_load(f)


def _load_active_modifiers(target: str) -> list:
    """
    Load active epigenetic modifiers for a target from the DB.
    Returns list of modifier dicts. Silently returns [] on DB failure.
    """
    try:
        from lib.ganuda_db import get_connection
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT condition_name, modifier_type, modifier_value
                FROM epigenetic_modifiers
                WHERE active = TRUE
                  AND (target = %s OR target = '*')
                  AND (expires_at IS NULL OR expires_at > NOW())
                ORDER BY modifier_id
            """, (target,))
            rows = cur.fetchall()
            return [
                {"condition": r[0], "type": r[1], "value": json.loads(r[2]) if isinstance(r[2], str) else r[2]}
                for r in rows
            ]
        finally:
            conn.close()
    except Exception as e:
        logger.debug(f"Could not load modifiers for {target}: {e}")
        return []


def _apply_modifiers(profile: dict, modifiers: list) -> dict:
    """
    Apply epigenetic modifiers to a profile. Returns modified copy.

    Modifier types:
      - weight: multiply temperature or max_tokens by a factor
      - inject: append text to the system prompt
      - suppress: set active=false (enzyme won't fire)
      - amplify: lower temperature (more focused/aggressive)
    """
    p = dict(profile)
    p["system_prompt"] = p.get("system_prompt", "")

    for mod in modifiers:
        mtype = mod["type"]
        mval = mod["value"]

        if mtype == "inject":
            inject_text = mval.get("text", "")
            if inject_text:
                p["system_prompt"] += f"\n\n## Environmental Modifier: {mod['condition']}\n{inject_text}"

        elif mtype == "amplify":
            factor = mval.get("factor", 0.7)
            p["temperature"] = round(p.get("temperature", 0.3) * factor, 2)

        elif mtype == "weight":
            factor = mval.get("factor", 1.0)
            p["max_tokens"] = int(p.get("max_tokens", 512) * factor)

        elif mtype == "suppress":
            p["_suppressed"] = True

    return p


def _log_usage(profile_name: str, caller_id: str, substrate: str,
               product: str, tools_used: list, input_tokens: int,
               output_tokens: int, model: str, latency_ms: int,
               success: bool, error_msg: str = None,
               modifiers: list = None):
    """Log enzyme invocation to duplo_usage_log and token_ledger."""
    try:
        from lib.ganuda_db import get_connection
        conn = get_connection()
        try:
            cur = conn.cursor()
            # Usage log
            cur.execute("""
                INSERT INTO duplo_usage_log
                (profile_name, caller_id, substrate, product, tools_used,
                 input_tokens, output_tokens, model_used, latency_ms,
                 success, error_message, modifiers)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                profile_name, caller_id,
                (substrate or "")[:2000], (product or "")[:2000],
                tools_used, input_tokens, output_tokens, model,
                latency_ms, success, error_msg,
                json.dumps([m.get("condition", "") for m in (modifiers or [])]),
            ))
            # Token ledger (ATP accounting)
            cur.execute("""
                INSERT INTO token_ledger
                (model, caller_id, call_type, input_tokens, output_tokens,
                 latency_ms, metadata)
                VALUES (%s, %s, 'duplo_enzyme', %s, %s, %s, %s)
            """, (
                model, caller_id, input_tokens, output_tokens, latency_ms,
                json.dumps({"profile": profile_name, "tools": tools_used}),
            ))
            conn.commit()
        finally:
            conn.close()
    except Exception as e:
        logger.warning(f"Failed to log enzyme usage: {e}")


def compose_enzyme(
    profile_name: str,
    caller_id: str = "unknown",
    override_model: str = None,
    override_tools: List[str] = None,
) -> Callable:
    """
    Compose a Duplo enzyme from a context profile.

    Returns a callable: enzyme(substrate: str) -> dict

    The returned dict contains:
      - product: str — the LLM's output
      - tools_used: list — which tools were invoked
      - tokens: dict — {input, output, total}
      - latency_ms: int
      - modifiers: list — active modifiers at invocation time
    """
    from lib.duplo.registry import build_federation_registry

    # Load profile
    profile = _load_profile(profile_name)
    registry = build_federation_registry()

    # Resolve backend
    model_key = override_model or profile.get("default_model", "qwen")
    backend = BACKENDS.get(model_key)
    if not backend:
        raise ValueError(f"Unknown backend: {model_key}")

    # Resolve tool set
    tool_names = override_tools or profile.get("tool_set", [])
    tool_set = registry.get_tool_set(tool_names) if tool_names else {}

    def enzyme(substrate: str, **kwargs) -> dict:
        """Execute the enzyme reaction."""
        start = time.time()

        # Load modifiers at invocation time (not composition time)
        modifiers = _load_active_modifiers(profile_name)
        active_profile = _apply_modifiers(profile, modifiers)

        # Check suppression
        if active_profile.get("_suppressed"):
            return {
                "product": None,
                "tools_used": [],
                "tokens": {"input": 0, "output": 0, "total": 0},
                "latency_ms": 0,
                "modifiers": modifiers,
                "suppressed": True,
            }

        system_prompt = active_profile.get("system_prompt", "")
        max_tokens = active_profile.get("max_tokens", 512)
        temperature = active_profile.get("temperature", 0.3)

        # Build tool descriptions for the system prompt
        if tool_set:
            tool_desc = "\n\nAvailable tools:\n"
            for tname in tool_names:
                spec = registry.get_spec(tname)
                if spec:
                    tool_desc += f"- {tname}: {spec.description}\n"
            system_prompt += tool_desc

        # Call LLM
        payload = {
            "model": backend["model"],
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": substrate},
            ],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        error_msg = None
        product = None
        input_tokens = 0
        output_tokens = 0
        success = True
        tools_actually_used = []

        try:
            resp = requests.post(
                backend["url"], json=payload, timeout=backend["timeout"]
            )
            resp.raise_for_status()
            data = resp.json()

            product = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            input_tokens = usage.get("prompt_tokens", 0)
            output_tokens = usage.get("completion_tokens", 0)

        except Exception as e:
            error_msg = str(e)[:500]
            success = False
            logger.error(f"Enzyme {profile_name} failed: {e}")

        latency_ms = int((time.time() - start) * 1000)

        # Log to DB (usage + ATP ledger)
        _log_usage(
            profile_name=profile_name,
            caller_id=caller_id,
            substrate=substrate,
            product=product,
            tools_used=tools_actually_used,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            model=backend["model"],
            latency_ms=latency_ms,
            success=success,
            error_msg=error_msg,
            modifiers=modifiers,
        )

        return {
            "product": product,
            "tools_used": tools_actually_used,
            "tokens": {
                "input": input_tokens,
                "output": output_tokens,
                "total": input_tokens + output_tokens,
            },
            "latency_ms": latency_ms,
            "modifiers": [m["condition"] for m in modifiers],
            "success": success,
            "error": error_msg,
        }

    return enzyme
```

## Verification

1. Create a test profile `lib/duplo/context_profiles/test_echo.yaml` with minimal config
2. `python3 -c "from lib.duplo.composer import compose_enzyme; e = compose_enzyme('test_echo'); print(type(e))"` — should return `<class 'function'>`
3. If vLLM is running: `python3 -c "from lib.duplo.composer import compose_enzyme; e = compose_enzyme('test_echo', caller_id='test'); r = e('Say hello'); print(r['product'][:100], r['tokens'])"` — should return LLM output + token counts
