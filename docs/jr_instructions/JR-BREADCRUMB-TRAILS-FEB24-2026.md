# Jr Instruction: Breadcrumb Trails — Specialist Cross-Reference Graph

**Kanban**: #1887
**Priority**: 5
**Story Points**: 8
**use_rlm**: false
**assigned_jr**: Software Engineer Jr.

---

## Overview

Create a script that queries thermal_memory_archive for memories referencing specialist names (Deer, Turtle, Coyote, Raven, Bear, Owl, Spider) and builds a directed graph of which specialists referenced each other's work. Outputs a JSON report with specialist-to-specialist reference counts. Runs on redfin.

---

## Steps

### Step 1: Create the breadcrumb trails script

Create `/ganuda/scripts/breadcrumb_trails.py`

```python
#!/usr/bin/env python3
"""
Breadcrumb Trails — Specialist Cross-Reference Graph
Kanban #1887 - Cherokee AI Federation

Queries thermal_memory_archive for specialist name co-occurrences
and builds a directed reference graph showing how specialists
reference each other's work across the memory corpus.

Usage:
    python3 /ganuda/scripts/breadcrumb_trails.py

Output:
    /ganuda/reports/breadcrumb_trails.json

For Seven Generations
"""

import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone

import psycopg2
import psycopg2.extras

SPECIALISTS = ["Deer", "Turtle", "Coyote", "Raven", "Bear", "Owl", "Spider"]

DB_CONFIG = {
    "host": "192.168.132.222",
    "dbname": "zammad_production",
    "user": "claude",
    "password": os.environ.get("CHEROKEE_DB_PASS", ""),
}

REPORT_PATH = "/ganuda/reports/breadcrumb_trails.json"


def get_db_connection():
    """Connect to the federation database."""
    if not DB_CONFIG["password"]:
        print("ERROR: CHEROKEE_DB_PASS environment variable not set", file=sys.stderr)
        sys.exit(1)
    return psycopg2.connect(**DB_CONFIG)


def query_specialist_memories(conn, specialist):
    """Fetch memories that mention a given specialist by name."""
    sql = """
        SELECT id, original_content, created_at, source
        FROM thermal_memory_archive
        WHERE original_content ILIKE %s
        ORDER BY created_at DESC
    """
    pattern = f"%{specialist}%"
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(sql, (pattern,))
        return cur.fetchall()


def build_cross_reference_graph(conn):
    """Build a directed graph of specialist-to-specialist references.

    For each specialist S, find all memories mentioning S, then check
    which OTHER specialists appear in those same memories. This gives
    us a directed edge: other_specialist -> S (the other specialist's
    work was referenced in a memory about S).
    """
    graph = defaultdict(lambda: defaultdict(int))
    memory_counts = {}
    sample_memories = defaultdict(list)

    for specialist in SPECIALISTS:
        memories = query_specialist_memories(conn, specialist)
        memory_counts[specialist] = len(memories)
        print(f"  {specialist}: {len(memories)} memories found")

        for mem in memories:
            content = mem["original_content"] or ""
            content_lower = content.lower()

            for other in SPECIALISTS:
                if other == specialist:
                    continue
                if other.lower() in content_lower:
                    graph[specialist][other] += 1

                    # Keep up to 3 sample memory IDs per edge
                    edge_key = f"{specialist}->{other}"
                    if len(sample_memories[edge_key]) < 3:
                        sample_memories[edge_key].append(mem["id"])

    return graph, memory_counts, sample_memories


def compute_statistics(graph, memory_counts):
    """Compute summary statistics from the cross-reference graph."""
    total_edges = 0
    total_weight = 0
    strongest_edge = {"from": None, "to": None, "count": 0}

    for source, targets in graph.items():
        for target, count in targets.items():
            total_edges += 1
            total_weight += count
            if count > strongest_edge["count"]:
                strongest_edge = {"from": source, "to": target, "count": count}

    most_referenced = max(memory_counts, key=memory_counts.get) if memory_counts else None
    least_referenced = min(memory_counts, key=memory_counts.get) if memory_counts else None

    return {
        "total_edges": total_edges,
        "total_cross_references": total_weight,
        "strongest_connection": strongest_edge,
        "most_referenced_specialist": most_referenced,
        "least_referenced_specialist": least_referenced,
    }


def main():
    print("Breadcrumb Trails — Specialist Cross-Reference Graph")
    print("=" * 55)
    print()

    conn = get_db_connection()

    try:
        print("Querying thermal_memory_archive for specialist mentions...")
        graph, memory_counts, sample_memories = build_cross_reference_graph(conn)
        stats = compute_statistics(graph, memory_counts)

        # Build the report
        report = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "specialists": SPECIALISTS,
            "memory_counts": memory_counts,
            "cross_references": {
                source: dict(targets) for source, targets in graph.items()
            },
            "sample_memory_ids": dict(sample_memories),
            "statistics": stats,
        }

        # Ensure output directory exists
        os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)

        with open(REPORT_PATH, "w") as f:
            json.dump(report, f, indent=2, default=str)

        print()
        print(f"Report saved to {REPORT_PATH}")
        print()
        print("--- Summary ---")
        print(f"Total memories scanned across specialists: {sum(memory_counts.values())}")
        print(f"Cross-reference edges: {stats['total_edges']}")
        print(f"Total cross-references: {stats['total_cross_references']}")
        if stats["strongest_connection"]["from"]:
            sc = stats["strongest_connection"]
            print(f"Strongest connection: {sc['from']} <-> {sc['to']} ({sc['count']} refs)")
        print(f"Most referenced: {stats['most_referenced_specialist']} ({memory_counts.get(stats['most_referenced_specialist'], 0)})")
        print(f"Least referenced: {stats['least_referenced_specialist']} ({memory_counts.get(stats['least_referenced_specialist'], 0)})")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
```

---

## Verification

After execution, confirm:
1. Script runs without errors: `python3 /ganuda/scripts/breadcrumb_trails.py`
2. Report exists: `cat /ganuda/reports/breadcrumb_trails.json | python3 -m json.tool | head -30`
3. All 7 specialists appear in the output
4. Cross-reference counts are non-negative integers
