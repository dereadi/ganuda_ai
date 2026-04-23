#!/usr/bin/env python3
"""TPM UserPromptSubmit hook — inject from thermal + crawdad at prompt time.

Fires when Partner sends a message. Searches both memory dimensions:
  - Thermal (significance): pgvector semantic match against thermal_memory_archive
  - Crawdad (temporal): filesystem mtime-reverse walk for recent relevant files

Exits 0 always (with or without injection). Hooks must never block the turn.
"""

import datetime
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shared import (
    search_thermal, crawdad_walk, extract_keywords,
    format_thermal_line, format_crawdad_line,
    log_invocation, emit_otel,
)

MIN_PROMPT_CHARS = 15
MAX_QUERY_CHARS = 500
THERMAL_LIMIT = 3
CRAWDAD_LIMIT = 3
THERMAL_THRESHOLD = 0.5
CRAWDAD_HOURS = 168  # 1 week mtime window


def main():
    t0 = time.time()
    try:
        hook_input = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        sys.exit(1)

    prompt = (hook_input.get("prompt") or "").strip()
    if len(prompt) < MIN_PROMPT_CHARS:
        log_invocation("prompt_inject", {"skipped": "trivial_prompt", "prompt_len": len(prompt)})
        sys.exit(0)

    query = prompt[:MAX_QUERY_CHARS]
    keywords = extract_keywords(query)

    # Fan out: thermal + crawdad in parallel
    with ThreadPoolExecutor(max_workers=2) as ex:
        f_thermal = ex.submit(search_thermal, query, THERMAL_LIMIT, THERMAL_THRESHOLD)
        f_crawdad = ex.submit(crawdad_walk, keywords, CRAWDAD_HOURS, CRAWDAD_LIMIT)
        thermal = f_thermal.result()
        crawdad = f_crawdad.result()

    lines = []
    if thermal:
        lines.append("[TPM Memory] Thermal (significance — pgvector match):")
        for i, m in enumerate(thermal, 1):
            lines.append(format_thermal_line(i, m))
    if crawdad:
        lines.append("[TPM Memory] Crawdad (temporal — recent filesystem):")
        for i, c in enumerate(crawdad, 1):
            lines.append(format_crawdad_line(i, c))

    output_text = "\n".join(lines) if lines else ""
    latency_ms = int((time.time() - t0) * 1000)

    log_invocation("prompt_inject", {
        "prompt_len": len(prompt),
        "keywords": keywords,
        "thermal_hits": len(thermal),
        "crawdad_hits": len(crawdad),
        "injected_chars": len(output_text),
        "latency_ms": latency_ms,
    })
    emit_otel("UserPromptSubmit", len(output_text), len(thermal), len(crawdad), latency_ms)

    if not output_text:
        sys.exit(0)

    envelope = {
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": output_text,
        }
    }
    print(json.dumps(envelope))
    sys.exit(0)


if __name__ == "__main__":
    main()
