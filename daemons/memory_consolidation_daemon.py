#!/usr/bin/env python3
"""
A-MEM Memory Consolidation Daemon

Runs hourly to consolidate similar episodic memories into semantic memories.
Reference: arXiv:2502.12110 (A-MEM)

For Seven Generations - Cherokee AI Federation
"""

import os
import sys
import time
import json
import psycopg2
from datetime import datetime, timedelta
from typing import List, Dict

sys.path.insert(0, '/ganuda/lib')
from amem_types import MemoryType

DB_CONFIG = {
    'host': os.environ.get('CHEROKEE_DB_HOST', '192.168.132.222'),
    'database': os.environ.get('CHEROKEE_DB_NAME', 'zammad_production'),
    'user': os.environ.get('CHEROKEE_DB_USER', 'claude'),
    'password': os.environ.get('CHEROKEE_DB_PASS', 'jawaseatlasers2')
}

def get_similar_episodic_memories(conn, similarity_threshold: float = 0.8) -> List[List]:
    """Find groups of similar episodic memories for consolidation."""
    cur = conn.cursor()

    # Get recent episodic memories not yet consolidated
    cur.execute('''
        SELECT id, content, temperature, created_at
        FROM thermal_memory
        WHERE memory_type = 'episodic'
          AND consolidated_from IS NULL
          AND created_at > NOW() - INTERVAL '7 days'
        ORDER BY created_at DESC
        LIMIT 100
    ''')

    memories = cur.fetchall()
    cur.close()

    # Group similar memories (simple keyword matching for now)
    groups = []
    used = set()

    for i, mem1 in enumerate(memories):
        if mem1[0] in used:
            continue
        group = [mem1]
        for j, mem2 in enumerate(memories[i+1:], i+1):
            if mem2[0] in used:
                continue
            # Simple similarity: shared keywords
            words1 = set(str(mem1[1]).lower().split())
            words2 = set(str(mem2[1]).lower().split())
            overlap = len(words1 & words2) / max(len(words1 | words2), 1)
            if overlap >= similarity_threshold:
                group.append(mem2)
                used.add(mem2[0])
        if len(group) >= 3:  # Need at least 3 similar memories to consolidate
            groups.append(group)
            used.add(mem1[0])

    return groups

def consolidate_group(conn, group: List[tuple]) -> int:
    """Consolidate a group of episodic memories into one semantic memory."""
    cur = conn.cursor()

    # Extract common pattern
    contents = [str(m[1]) for m in group]
    ids = [m[0] for m in group]

    # Simple consolidation: find common phrases
    words = {}
    for content in contents:
        for word in content.lower().split():
            words[word] = words.get(word, 0) + 1

    common_words = [w for w, c in words.items() if c >= len(group) * 0.6]
    consolidated_content = f"Pattern from {len(group)} observations: {' '.join(common_words[:20])}"

    # Insert consolidated semantic memory
    cur.execute('''
        INSERT INTO thermal_memory
        (content, temperature, source, memory_type, consolidated_from, consolidation_count, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, NOW())
        RETURNING id
    ''', (
        consolidated_content,
        0.7,  # Medium temperature for consolidated memories
        'consolidation_daemon',
        'semantic',
        ids,
        len(group)
    ))

    new_id = cur.fetchone()[0]
    conn.commit()
    cur.close()

    return new_id

def run_consolidation():
    """Main consolidation cycle."""
    conn = psycopg2.connect(**DB_CONFIG)

    try:
        groups = get_similar_episodic_memories(conn)

        consolidated_count = 0
        for group in groups:
            try:
                new_id = consolidate_group(conn, group)
                consolidated_count += 1
                print(f"[Consolidation] Created semantic memory #{new_id} from {len(group)} episodic memories")
            except Exception as e:
                print(f"[Consolidation] Error consolidating group: {e}")
                conn.rollback()

        print(f"[Consolidation] Cycle complete: {consolidated_count} semantic memories created")

    finally:
        conn.close()

def main():
    print("[Consolidation Daemon] Starting...")
    print("[Consolidation Daemon] Cycle interval: 1 hour")

    while True:
        try:
            run_consolidation()
        except Exception as e:
            print(f"[Consolidation Daemon] Error: {e}")

        time.sleep(3600)  # 1 hour

if __name__ == "__main__":
    main()
