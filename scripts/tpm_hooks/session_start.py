#!/usr/bin/env python3
"""TPM SessionStart hook — prime a fresh/resumed/post-compact session.

Fires at session start (source=startup), on resume, and immediately after
context compaction. Pulls:
  - Thermal: recent sacred-tier + working-continuity memories
  - Crawdad: most-recently-modified files under memory / kb / instruction dirs

Output channel is plain stdout (per NNM learning — SessionStart's
`hookSpecificOutput` shape is not schema-approved in current Claude Code).
"""

import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shared import (
    search_thermal, crawdad_walk,
    format_thermal_line, format_crawdad_line,
    log_invocation, emit_otel,
)

THERMAL_LIMIT = 5
CRAWDAD_LIMIT = 5
CRAWDAD_HOURS = 72  # 3-day recency window for session start

# Generic thermal query — pulls working-continuity memories even without
# a specific user prompt. Keywords tuned to surface operational discipline.
SESSION_THERMAL_QUERY = (
    "current partner directives recent decisions active kanban tickets "
    "federation standing directives sacred patterns"
)


def main():
    t0 = time.time()
    try:
        hook_input = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        sys.exit(1)

    source = hook_input.get("source", "startup")

    with ThreadPoolExecutor(max_workers=2) as ex:
        # Thermal: generic importance-ranked working-continuity search
        f_thermal = ex.submit(search_thermal, SESSION_THERMAL_QUERY, THERMAL_LIMIT, 0.3)
        # Crawdad: no keyword filter → just mtime-reverse recent
        f_crawdad = ex.submit(crawdad_walk, [], CRAWDAD_HOURS, CRAWDAD_LIMIT)
        thermal = f_thermal.result()
        crawdad = f_crawdad.result()

    header = f"[TPM SessionStart | source={source}] Working-continuity context:"
    parts = [header]
    if thermal:
        parts.append("[Thermal — significance axis]")
        for i, m in enumerate(thermal, 1):
            parts.append(format_thermal_line(i, m))
    if crawdad:
        parts.append("[Crawdad — temporal axis (most recently touched)]")
        for i, c in enumerate(crawdad, 1):
            parts.append(format_crawdad_line(i, c))

    if not thermal and not crawdad:
        parts.append("  (no matches returned — check embedding service + crawdad roots)")

    output_text = "\n".join(parts) + "\n"
    latency_ms = int((time.time() - t0) * 1000)

    log_invocation("session_start", {
        "source": source,
        "thermal_hits": len(thermal),
        "crawdad_hits": len(crawdad),
        "injected_chars": len(output_text),
        "latency_ms": latency_ms,
    })
    emit_otel("SessionStart", len(output_text), len(thermal), len(crawdad), latency_ms)

    # Plain stdout — SessionStart envelope not schema-approved
    sys.stdout.write(output_text)
    sys.exit(0)


if __name__ == "__main__":
    main()
