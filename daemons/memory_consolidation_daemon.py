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
import hashlib
import psycopg2
from datetime import datetime, timedelta
from typing import List, Dict

sys.path.insert(0, '/ganuda/lib')
sys.path.insert(0, '/ganuda')

try:
    from amem_types import MemoryType
except ImportError:
    MemoryType = None  # Not critical for consolidation

from lib.memory_consensus_analyzer import find_disagreements, consolidate_with_disagreement

DB_CONFIG = {
    'host': os.environ.get('CHEROKEE_DB_HOST', '192.168.132.222'),
    'database': os.environ.get('CHEROKEE_DB_NAME', 'zammad_production'),
    'user': os.environ.get('CHEROKEE_DB_USER', 'claude'),
    'password': os.environ.get('CHEROKEE_DB_PASS', '')
}

USE_DISAGREEMENT_AWARE = True  # Feature flag: set False to revert to naive consolidation

def get_similar_episodic_memories(conn, similarity_threshold: float = 0.8) -> List[List]:
    """Find groups of similar memories for consolidation.

    Uses thermal_memory_archive (the actual table) with keyword overlap.
    Future: upgrade to embedding-based similarity via greenfin:8003.
    """
    cur = conn.cursor()

    # Get recent memories not yet consolidated (use metadata flag)
    cur.execute('''
        SELECT id, original_content, temperature_score, created_at
        FROM thermal_memory_archive
        WHERE created_at > NOW() - INTERVAL '7 days'
          AND (metadata IS NULL OR NOT (metadata ? 'consolidated_into'))
        ORDER BY created_at DESC
        LIMIT 200
    ''')

    memories = cur.fetchall()
    cur.close()

    # Group similar memories (keyword matching)
    groups = []
    used = set()

    for i, mem1 in enumerate(memories):
        if mem1[0] in used:
            continue
        group = [mem1]
        for j, mem2 in enumerate(memories[i+1:], i+1):
            if mem2[0] in used:
                continue
            words1 = set(str(mem1[1]).lower().split())
            words2 = set(str(mem2[1]).lower().split())
            overlap = len(words1 & words2) / max(len(words1 | words2), 1)
            if overlap >= similarity_threshold:
                group.append(mem2)
                used.add(mem2[0])
        if len(group) >= 3:
            groups.append(group)
            used.add(mem1[0])

    return groups

def consolidate_group_naive(conn, group: List[tuple]) -> int:
    """Original naive consolidation: common keyword extraction."""
    cur = conn.cursor()
    contents = [str(m[1]) for m in group]
    ids = [m[0] for m in group]

    words = {}
    for content in contents:
        for word in content.lower().split():
            words[word] = words.get(word, 0) + 1

    common_words = [w for w, c in words.items() if c >= len(group) * 0.6]
    consolidated_content = f"Pattern from {len(group)} observations: {' '.join(common_words[:20])}"

    memory_hash = hashlib.sha256(consolidated_content.encode()).hexdigest()

    cur.execute('''
        INSERT INTO thermal_memory_archive
        (original_content, temperature_score, memory_hash, metadata, created_at)
        VALUES (%s, %s, %s, %s, NOW())
        RETURNING id
    ''', (
        consolidated_content,
        70.0,
        memory_hash,
        json.dumps({
            'source': 'consolidation_daemon',
            'method': 'naive_keyword',
            'source_ids': ids,
            'source_count': len(group)
        })
    ))

    new_id = cur.fetchone()[0]

    # Mark source memories as consolidated
    for mid in ids:
        cur.execute('''
            UPDATE thermal_memory_archive
            SET metadata = COALESCE(metadata, '{}'::jsonb) || jsonb_build_object('consolidated_into', %s)
            WHERE id = %s
        ''', (new_id, mid))

    conn.commit()
    cur.close()
    return new_id


def consolidate_group_disagreement(conn, group: List[tuple]) -> int:
    """Disagreement-aware consolidation using consensus analysis.

    Ported from Jane Street Track 2 uncertain_position_enumerator.
    """
    cur = conn.cursor()
    ids = [m[0] for m in group]

    # Convert tuples to dicts for the analyzer
    memory_dicts = [
        {'id': m[0], 'original_content': str(m[1]), 'temperature_score': m[2]}
        for m in group
    ]

    # Find disagreements
    disagreement = find_disagreements(memory_dicts)

    # Create consolidated memory with disagreement awareness
    result = consolidate_with_disagreement(memory_dicts, disagreement)

    memory_hash = hashlib.sha256(result['content'].encode()).hexdigest()

    cur.execute('''
        INSERT INTO thermal_memory_archive
        (original_content, temperature_score, memory_hash, metadata, created_at)
        VALUES (%s, %s, %s, %s, NOW())
        RETURNING id
    ''', (
        result['content'],
        70.0,
        memory_hash,
        json.dumps(result['metadata'])
    ))

    new_id = cur.fetchone()[0]

    # Mark source memories as consolidated
    for mid in ids:
        cur.execute('''
            UPDATE thermal_memory_archive
            SET metadata = COALESCE(metadata, '{}'::jsonb) || jsonb_build_object('consolidated_into', %s)
            WHERE id = %s
        ''', (new_id, mid))

    conn.commit()
    cur.close()

    # Log contradictions if found
    if disagreement['contradictions']:
        print(f"  [!] {len(disagreement['contradictions'])} contradictions detected:")
        for c in disagreement['contradictions']:
            print(f"      {c[0]}: '{c[1]}' ({c[2]}x) vs '{c[3]}' ({c[4]}x)")

    return new_id


def consolidate_group(conn, group: List[tuple]) -> int:
    """Consolidate a group of memories. Dispatches based on feature flag."""
    if USE_DISAGREEMENT_AWARE:
        return consolidate_group_disagreement(conn, group)
    else:
        return consolidate_group_naive(conn, group)

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

        print(f"[Consolidation] Cycle complete: {consolidated_count} memories consolidated"
              f" (method: {'disagreement-aware' if USE_DISAGREEMENT_AWARE else 'naive'})")

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
