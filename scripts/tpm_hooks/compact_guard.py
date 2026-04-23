#!/usr/bin/env python3
"""TPM PreCompact hook — preserve operational discipline through compaction.

Fires right before context compression. Injects:
  - Cherokee operating rules (hard-coded, short)
  - High-temperature (>=75°C / sacred) thermal matches
  - Most-recently-touched memory files (crawdad)

The goal: after compaction, Partner + TPM don't lose sacred-pattern
discipline or recent decisions just because the context got squeezed.
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
CRAWDAD_LIMIT = 3
CRAWDAD_HOURS = 24  # last day


# Cherokee operating rules that must survive compaction.
# These are the distilled version of CLAUDE.md + MEMORY.md critical identity.
_CRITICAL_RULES = """[TPM Compact Guard] Operating rules preserved across context compaction:

- Write to /ganuda on linux nodes, /Users/Shared/ganuda on macOS. /tmp only for scratch.
- Scan thermal memory when in doubt — "everything we have done is in that memory."
- Use REAL Council, never simulate (feedback_simulated_vs_real_council).
- Multi-file Jr dispatches → TPM orchestration, not bundled Jr ticket (LMC-11 discipline).
- Shanz gate: new products default include Joe + Kenzie, exclude Shanz.
- Both memory dimensions matter: thermal (significance) + crawdad (temporal). Use both.
- Patents #1-7 are the sacred line for federation IP.
"""

COMPACT_THERMAL_QUERY = (
    "sacred patterns partner directives recent council decisions "
    "current in-progress work standing rules"
)


def main():
    t0 = time.time()
    try:
        hook_input = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        sys.exit(1)

    with ThreadPoolExecutor(max_workers=2) as ex:
        f_thermal = ex.submit(search_thermal, COMPACT_THERMAL_QUERY, THERMAL_LIMIT, 0.4)
        f_crawdad = ex.submit(crawdad_walk, [], CRAWDAD_HOURS, CRAWDAD_LIMIT)
        thermal = f_thermal.result()
        crawdad = f_crawdad.result()

    parts = [_CRITICAL_RULES]
    if thermal:
        parts.append("\n[Thermal — high-significance memories to preserve]")
        for i, m in enumerate(thermal, 1):
            parts.append(format_thermal_line(i, m))
    if crawdad:
        parts.append("\n[Crawdad — most-recently touched memory files]")
        for i, c in enumerate(crawdad, 1):
            parts.append(format_crawdad_line(i, c))

    output_text = "\n".join(parts) + "\n"
    latency_ms = int((time.time() - t0) * 1000)

    log_invocation("compact_guard", {
        "thermal_hits": len(thermal),
        "crawdad_hits": len(crawdad),
        "injected_chars": len(output_text),
        "latency_ms": latency_ms,
    })
    emit_otel("PreCompact", len(output_text), len(thermal), len(crawdad), latency_ms)

    # Plain stdout — PreCompact envelope also not schema-approved per NNM learning
    sys.stdout.write(output_text)
    sys.exit(0)


if __name__ == "__main__":
    main()
