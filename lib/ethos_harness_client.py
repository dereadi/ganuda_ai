"""Harness client for the federation ethos service.

Council vote ratifying this build: 9625a058a103f582 (May 4 2026).

Usage:
    from lib.ethos_harness_client import enrich_with_ethos
    enriched_prompt = enrich_with_ethos("What is Subab?")

Behavior:
    - Calls /v1/ethos/scan against the federation ethos service
    - Retrieves up to top-K relevant ethos records for the user query
    - Formats them as a FEDERATION ETHOS REFERENCE section prepended to the prompt
    - Returns the enriched prompt (or the bare prompt if service is down)

Spider [INTEGRATION] requirement: harness MUST call this through HTTP, NEVER
import sqlite3 directly. This is the abstraction that lets Phase 2 swap the
backend (SQLite → PostgreSQL → SQLCipher) without harness changes.

Failure mode: if the service is unreachable, return the bare prompt. The
harness SHOULD log this and Eagle Eye monitoring should alert. NEVER block on
ethos-service availability.
"""
from __future__ import annotations

import logging
import os
from typing import Optional

import requests

logger = logging.getLogger("ethos_harness_client")

ETHOS_SERVICE_URL = os.environ.get(
    "ETHOS_SERVICE_URL", "http://127.0.0.1:8830"
)
DEFAULT_TIMEOUT_SEC = 2.0  # Federation-internal localhost; should be <100ms typical
DEFAULT_TOP_K = 5


def fetch_relevant_ethos(query: str, top_k: int = DEFAULT_TOP_K,
                         tenant: str = "cherokee_federation") -> list[dict]:
    """Return up to top_k ethos records relevant to the query (substring scan)."""
    try:
        r = requests.get(
            f"{ETHOS_SERVICE_URL}/v1/ethos/scan",
            params={"query": query, "limit": top_k, "tenant": tenant},
            timeout=DEFAULT_TIMEOUT_SEC,
        )
        r.raise_for_status()
        return r.json()
    except requests.RequestException as e:
        logger.warning(f"ethos service unreachable: {e}")
        return []


def format_ethos_block(records: list[dict]) -> str:
    """Render a list of ethos records as a system-prompt-friendly block."""
    if not records:
        return ""
    lines = ["--- FEDERATION ETHOS REFERENCE (canonical) ---"]
    for r in records:
        sacred_marker = " [SACRED]" if r.get("sacred_pattern") else ""
        lines.append(f"\n• {r['term']} ({r['category']}){sacred_marker}:")
        lines.append(f"  {r['definition']}")
        if r.get("context"):
            lines.append(f"  CONTEXT: {r['context'][:300]}")
    lines.append("\n--- END ETHOS REFERENCE ---")
    lines.append(
        "When responding, ground your answer in the ethos records above. "
        "If the records contain canonical definitions of terms in the user's "
        "query, use those definitions verbatim — do NOT invent alternative "
        "meanings. If a term is not in the records, say so explicitly."
    )
    return "\n".join(lines)


def enrich_with_ethos(prompt: str, top_k: int = DEFAULT_TOP_K,
                      mode: str = "prepend",
                      tenant: str = "cherokee_federation") -> str:
    """Enrich a user/system prompt with retrieved ethos records.

    mode='prepend' (default): ethos block is prepended to the prompt
    mode='append':            appended after the prompt
    mode='block':             returns just the ethos block (caller assembles)
    """
    records = fetch_relevant_ethos(prompt, top_k=top_k, tenant=tenant)
    block = format_ethos_block(records)
    if not block:
        return prompt
    if mode == "block":
        return block
    if mode == "append":
        return prompt + "\n\n" + block
    return block + "\n\n" + prompt


def health() -> dict:
    """Probe the ethos service health endpoint. Used by harness diagnostics."""
    try:
        r = requests.get(f"{ETHOS_SERVICE_URL}/v1/ethos/health", timeout=DEFAULT_TIMEOUT_SEC)
        r.raise_for_status()
        return r.json()
    except requests.RequestException as e:
        return {"status": "unreachable", "error": str(e)}
