# Jr Instruction: Consensus Disagreement Detection for Memory Consolidation

**Kanban**: #1802
**Priority**: 8 (Wave 1)
**Assigned Jr**: Software Engineer Jr.
**use_rlm**: false
**Sprint**: RC-2026-02E

## Context

The memory consolidation daemon currently uses naive keyword overlap to group similar memories, then extracts common words as a "pattern." It has no contradiction detection — it can consolidate memories that disagree with each other into a single "pattern" that represents neither accurately.

We have 88K+ thermal memories. Known contradictions exist (port numbers, service names, schema columns). The uncertain position enumerator from the Jane Street puzzle showed that analyzing WHERE solutions disagree reveals the real targets for improvement.

**Source**: `/ganuda/experiments/jane-street/track2_permutation/uncertain_position_enumerator.py` (find_uncertain_positions, lines 153-184)

**Bug fix**: The existing daemon references a `thermal_memory` table that does not exist. The actual table is `thermal_memory_archive`. This instruction fixes that.

## Step 1: Create the memory consensus analyzer module

Create `/ganuda/lib/memory_consensus_analyzer.py`

```python
#!/usr/bin/env python3
"""
Memory Consensus Analyzer — Disagreement Detection for Thermal Memory

Ported from Jane Street Track 2 uncertain_position_enumerator.py.
Instead of finding uncertain POSITIONS in a permutation, we find
uncertain FACTS across groups of similar memories.

Council Vote #a4d8a110e3f06fb8

For Seven Generations - Cherokee AI Federation
"""

import re
import json
import hashlib
from collections import Counter
from typing import List, Dict, Tuple, Optional


# === Entity extraction (lightweight, no NLP deps) ===

# Patterns that capture factual claims in our thermal memories
FACT_PATTERNS = [
    # Port assignments: "port 8090", "8090:", ":8090"
    (r'(?:port\s+|:|^)(\d{4,5})\b', 'port'),
    # Service names: "service: foo.service", "systemd: foo"
    (r'(?:service|systemd)[:\s]+([a-z][\w.-]+\.service)', 'service'),
    # IP addresses
    (r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', 'ip'),
    # Node names from our fleet
    (r'\b(redfin|bluefin|greenfin|bmasass|sasass|sasass2|goldfin|silverfin|eaglefin|owlfin)\b', 'node'),
    # Column/table names: "column: foo", "table: foo"
    (r'(?:column|table|schema)[:\s]+[`"\']?(\w+)[`"\']?', 'schema'),
    # Status values
    (r'(?:status|state)[:\s]+[`"\']?(\w+)[`"\']?', 'status'),
    # Boolean claims
    (r'\b(NOT|never|always|deprecated|removed|live|deployed|active|disabled)\b', 'assertion'),
]


def extract_facts(content: str) -> Dict[str, List[str]]:
    """Extract factual claims from a memory's content.

    Returns dict mapping fact_type -> list of values found.
    Example: {'port': ['8090', '8092'], 'node': ['bluefin'], 'service': ['vlm-bluefin.service']}
    """
    facts = {}
    content_lower = content.lower()
    for pattern, fact_type in FACT_PATTERNS:
        matches = re.findall(pattern, content_lower)
        if matches:
            facts.setdefault(fact_type, []).extend(matches)
    return facts


def find_disagreements(memory_group: List[Dict]) -> Dict:
    """Find where a group of similar memories disagree on facts.

    Ported from uncertain_position_enumerator.find_uncertain_positions().

    Args:
        memory_group: list of dicts with at least 'id' and 'content' keys

    Returns:
        {
            'consensus_facts': {fact_type: {value: agreement_pct, ...}},
            'uncertain_facts': {fact_type: {value: agreement_pct, ...}},
            'contradictions': [(fact_type, value_a, count_a, value_b, count_b), ...],
            'group_agreement': float  # overall agreement score 0.0-1.0
        }
    """
    n = len(memory_group)
    if n < 2:
        return {
            'consensus_facts': {},
            'uncertain_facts': {},
            'contradictions': [],
            'group_agreement': 1.0
        }

    # Extract facts from each memory
    all_facts = []
    for mem in memory_group:
        content = mem.get('content') or mem.get('original_content', '')
        all_facts.append(extract_facts(content))

    # For each fact_type, compute agreement across memories
    consensus = {}
    uncertain = {}
    contradictions = []

    # Collect all fact types seen
    all_types = set()
    for facts in all_facts:
        all_types.update(facts.keys())

    total_facts = 0
    agreed_facts = 0

    for ftype in all_types:
        # Collect all values for this fact type across memories
        values_per_memory = []
        for facts in all_facts:
            values_per_memory.append(set(facts.get(ftype, [])))

        # Flatten all values seen
        all_values = Counter()
        for vals in values_per_memory:
            for v in vals:
                all_values[v] += 1

        for value, count in all_values.items():
            agreement = count / n
            total_facts += 1

            if agreement >= 0.7:
                # Consensus: 70%+ of memories agree
                consensus.setdefault(ftype, {})[value] = agreement
                agreed_facts += 1
            else:
                # Uncertain: less than 70% agree
                uncertain.setdefault(ftype, {})[value] = agreement

        # Check for contradictions: same fact type, different values, both >20%
        if len(all_values) >= 2:
            top_two = all_values.most_common(2)
            if top_two[1][1] / n >= 0.2:  # Second value in 20%+ of memories
                contradictions.append((
                    ftype,
                    top_two[0][0], top_two[0][1],
                    top_two[1][0], top_two[1][1]
                ))

    group_agreement = agreed_facts / max(total_facts, 1)

    return {
        'consensus_facts': consensus,
        'uncertain_facts': uncertain,
        'contradictions': contradictions,
        'group_agreement': group_agreement
    }


def consolidate_with_disagreement(memory_group: List[Dict], disagreement: Dict) -> Dict:
    """Create a consolidated memory that respects disagreements.

    High-agreement facts are stated as consensus.
    Low-agreement facts are flagged as uncertain.
    Contradictions are explicitly noted.

    Returns:
        {
            'content': str,  # consolidated text
            'confidence': str,  # HIGH / MEDIUM / LOW
            'metadata': dict  # disagreement details for storage
        }
    """
    parts = []
    n = len(memory_group)
    parts.append(f"Consolidated from {n} memories.")

    # State consensus facts
    if disagreement['consensus_facts']:
        consensus_items = []
        for ftype, values in disagreement['consensus_facts'].items():
            for value, pct in values.items():
                consensus_items.append(f"{ftype}={value} ({pct:.0%})")
        if consensus_items:
            parts.append(f"Consensus: {'; '.join(consensus_items[:10])}")

    # Flag contradictions
    if disagreement['contradictions']:
        contra_items = []
        for ftype, val_a, cnt_a, val_b, cnt_b in disagreement['contradictions']:
            contra_items.append(
                f"{ftype}: '{val_a}' ({cnt_a}/{n}) vs '{val_b}' ({cnt_b}/{n})"
            )
        parts.append(f"CONTRADICTIONS: {'; '.join(contra_items)}")

    # Include representative content from highest-agreement memory
    # (use first memory as representative for now)
    representative = memory_group[0].get('content') or memory_group[0].get('original_content', '')
    if len(representative) > 500:
        representative = representative[:500] + '...'
    parts.append(f"Representative: {representative}")

    content = ' | '.join(parts)

    # Confidence based on agreement and contradictions
    if disagreement['group_agreement'] >= 0.8 and not disagreement['contradictions']:
        confidence = 'HIGH'
    elif disagreement['contradictions']:
        confidence = 'LOW'
    else:
        confidence = 'MEDIUM'

    metadata = {
        'consolidation_version': 'disagreement-aware-v1',
        'source_count': n,
        'source_ids': [m.get('id') for m in memory_group],
        'group_agreement': disagreement['group_agreement'],
        'consensus_facts': disagreement['consensus_facts'],
        'uncertain_facts': disagreement['uncertain_facts'],
        'contradiction_count': len(disagreement['contradictions']),
        'contradictions': [
            {'type': c[0], 'value_a': c[1], 'count_a': c[2], 'value_b': c[3], 'count_b': c[4]}
            for c in disagreement['contradictions']
        ],
        'confidence': confidence
    }

    return {
        'content': content,
        'confidence': confidence,
        'metadata': metadata
    }
```

## Step 2: Update memory_consolidation_daemon.py

This step fixes the non-existent `thermal_memory` table reference AND integrates disagreement detection.

File: `/ganuda/daemons/memory_consolidation_daemon.py`

<<<<<<< SEARCH
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
    'password': os.environ.get('CHEROKEE_DB_PASS', '')
}
=======
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
>>>>>>> REPLACE

File: `/ganuda/daemons/memory_consolidation_daemon.py`

<<<<<<< SEARCH
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
=======
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
>>>>>>> REPLACE

File: `/ganuda/daemons/memory_consolidation_daemon.py`

<<<<<<< SEARCH
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
=======
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
>>>>>>> REPLACE

File: `/ganuda/daemons/memory_consolidation_daemon.py`

<<<<<<< SEARCH
        print(f"[Consolidation] Cycle complete: {consolidated_count} semantic memories created")
=======
        print(f"[Consolidation] Cycle complete: {consolidated_count} memories consolidated"
              f" (method: {'disagreement-aware' if USE_DISAGREEMENT_AWARE else 'naive'})")
>>>>>>> REPLACE

## Verification

After deployment, check consolidation logs for:
1. `[!] contradictions detected` lines — these are the disagreements the system found
2. New entries in `thermal_memory_archive` with `metadata->>'consolidation_version' = 'disagreement-aware-v1'`
3. Query: `SELECT id, original_content, metadata->>'confidence' as confidence, metadata->>'contradiction_count' as contradictions FROM thermal_memory_archive WHERE metadata->>'consolidation_version' = 'disagreement-aware-v1' ORDER BY id DESC LIMIT 20;`

## Rollback

Set `USE_DISAGREEMENT_AWARE = False` in memory_consolidation_daemon.py to revert to naive keyword consolidation.
