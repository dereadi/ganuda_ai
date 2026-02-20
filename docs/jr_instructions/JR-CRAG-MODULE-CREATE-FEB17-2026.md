# Jr Instruction: CRAG Module — Corrective Retrieval

**Kanban**: #1770
**Priority**: 8
**Assigned Jr**: Software Engineer Jr.
**use_rlm**: false
**Sprint**: RC-2026-02E

## Context

After the Grafana-on-bluefin false memory contamination (Feb 17 2026, KB: KB-GRAFANA-BLUEFIN-FALSE-MEMORY-CONTAMINATION-FEB17-2026.md), we need a Corrective RAG (CRAG) phase that explicitly searches for contradiction/correction evidence after primary retrieval.

**Pipeline position**: After cross-encoder reranking, before sufficiency assessment.

The module searches for:
1. **Internal contradictions** among retrieved results (using memory_consensus_analyzer.py)
2. **Sentinel/correction memories** — sacred high-temp memories that negate or correct claims about entities found in the query and primary results

Reference: Yan et al. (2024) "Corrective Retrieval Augmented Generation"

## Step 1: Create the CRAG module

Create `/ganuda/lib/rag_crag.py`

```python
"""
RAG CRAG (Corrective Retrieval Augmented Generation) — Cherokee AI Federation

Self-evaluation retrieval loop that detects contradictions in retrieved
memories and explicitly searches for correction/sentinel evidence.

Motivated by the Grafana-on-bluefin false memory contamination (Feb 17 2026):
16,820 false alert records at temp 95 poisoned RAG until a sentinel memory
at temp 98 was stored. CRAG ensures correction memories are ALWAYS surfaced
when contradictions or corrections exist about referenced entities.

Kanban #1770 — RC-2026-02E
Pipeline: pgvector → Phase 0 logging → Phase 1 ripple → Phase 2b rerank → **CRAG** → sufficiency → inject

Reference: Yan et al. (2024) 'Corrective Retrieval Augmented Generation'
"""

import os
import logging
import psycopg2
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

# Import entity extraction from consensus analyzer
try:
    from lib.memory_consensus_analyzer import extract_facts, find_disagreements
except ImportError:
    # Fallback: define minimal extract_facts if consensus analyzer unavailable
    import re

    def extract_facts(content):
        facts = {}
        content_lower = content.lower()
        patterns = [
            (r'(?:port\s+|:|^)(\d{4,5})\b', 'port'),
            (r'(?:service|systemd)[:\s]+([a-z][\w.-]+\.service)', 'service'),
            (r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', 'ip'),
            (r'\b(redfin|bluefin|greenfin|bmasass|sasass|sasass2)\b', 'node'),
        ]
        for pattern, fact_type in patterns:
            matches = re.findall(pattern, content_lower)
            if matches:
                facts.setdefault(fact_type, []).extend(matches)
        return facts

    def find_disagreements(memory_group):
        return {'consensus_facts': {}, 'uncertain_facts': {}, 'contradictions': [], 'group_agreement': 1.0}


# Correction-language patterns for identifying sentinel/correction memories
CORRECTION_PATTERNS = [
    '%correction%',
    '%false belief%',
    '%false positive%',
    '%not running%',
    '%never deployed%',
    '%removed from%',
    '%deprecated%',
    '%contamination%',
]


def evaluate_retrieval(question: str, primary_results: list, db_config: dict) -> dict:
    """
    CRAG self-evaluation: check retrieved results for internal contradictions
    and search for correction/sentinel memories about referenced entities.

    Args:
        question: original query string
        primary_results: list of (id, content, temp, score) tuples from primary retrieval
        db_config: database connection config dict

    Returns:
        dict with:
            - verdict: 'CONSISTENT' | 'CONTRADICTIONS_FOUND' | 'CORRECTIONS_FOUND'
            - contradictions: list of contradiction tuples from disagreement analysis
            - corrections: list of (id, content, temp) correction memory tuples
            - correction_text: formatted string for injection into context (or empty)
    """
    result = {
        'verdict': 'CONSISTENT',
        'contradictions': [],
        'corrections': [],
        'correction_text': '',
    }

    if not primary_results or len(primary_results) < 1:
        return result

    # --- Step 1: Internal disagreement check among retrieved results ---
    if len(primary_results) >= 2:
        memory_group = [
            {'id': r[0], 'original_content': r[1]}
            for r in primary_results
        ]
        disagreement = find_disagreements(memory_group)

        if disagreement['contradictions']:
            result['verdict'] = 'CONTRADICTIONS_FOUND'
            result['contradictions'] = disagreement['contradictions']
            logger.info(
                "[CRAG] %d internal contradictions in retrieved results",
                len(disagreement['contradictions']),
            )

    # --- Step 2: Extract key entities from question + primary results ---
    entities = set()

    # Entities from the question itself
    q_facts = extract_facts(question)
    for ftype, values in q_facts.items():
        if ftype in ('node', 'service', 'port', 'ip'):
            entities.update(values)

    # Entities from top 3 primary results
    for r in primary_results[:3]:
        r_facts = extract_facts(r[1])
        for ftype, values in r_facts.items():
            if ftype in ('node', 'service', 'port', 'ip'):
                entities.update(values)

    entities = list(entities)[:8]  # cap to keep query fast

    if not entities:
        return result

    # --- Step 3: Search for sentinel/correction memories ---
    try:
        conn = psycopg2.connect(**db_config, connect_timeout=5)
        cur = conn.cursor()
        primary_ids = [r[0] for r in primary_results]

        # Build entity ILIKE conditions
        entity_conditions = " OR ".join(
            ["original_content ILIKE %s"] * len(entities)
        )
        entity_params = [f'%{e}%' for e in entities]

        # Build correction-language conditions
        correction_conditions = " OR ".join(
            ["original_content ILIKE %s"] * len(CORRECTION_PATTERNS)
        )
        correction_params = list(CORRECTION_PATTERNS)

        # Two-tier query:
        # Tier 1 (sacred sentinels, temp >= 90) OR
        # Tier 2 (correction language, temp >= 80)
        query = f"""
            SELECT id, original_content, temperature_score,
                CASE WHEN sacred_pattern = true THEN 2 ELSE 1 END as tier
            FROM thermal_memory_archive
            WHERE id != ALL(%s)
            AND ({entity_conditions})
            AND (
                (sacred_pattern = true AND temperature_score >= 90)
                OR
                (temperature_score >= 80 AND ({correction_conditions}))
            )
            ORDER BY tier DESC, temperature_score DESC
            LIMIT 5
        """
        params = [primary_ids] + entity_params + correction_params
        cur.execute(query, params)

        sentinels = cur.fetchall()
        conn.close()

        if sentinels:
            result['verdict'] = 'CORRECTIONS_FOUND'
            result['corrections'] = [
                (row[0], row[1], row[2]) for row in sentinels
            ]

            parts = ["\n--- CORRECTIVE EVIDENCE DETECTED (CRAG) ---"]
            for mem_id, content, temp, tier in sentinels:
                tier_label = "sacred sentinel" if tier == 2 else "correction"
                parts.append(
                    f"\n[Correction #{mem_id} | temp={temp:.0f} | {tier_label}]"
                )
                truncated = content[:500] if len(content) > 500 else content
                parts.append(truncated)
            parts.append("--- END CORRECTIVE EVIDENCE ---")
            result['correction_text'] = "\n".join(parts)

            logger.info(
                "[CRAG] Found %d correction memories for entities: %s",
                len(sentinels),
                entities[:3],
            )

    except Exception as e:
        logger.warning("[CRAG] Correction search failed (non-fatal): %s", e)

    return result
```

## Notes

- Non-fatal: all operations wrapped in try/except, returns empty result on failure
- Uses `connect_timeout=5` to avoid blocking the pipeline on DB issues
- Two-tier sentinel search: sacred sentinels (tier 2, temp >= 90) prioritized over correction-language memories (tier 1, temp >= 80)
- Entity extraction limited to infrastructure-relevant types (node, service, port, ip) to reduce false matches
- Cap at 8 entities and 5 correction results to bound query time
- Correction text truncated at 500 chars per memory to prevent context bloat
- `find_disagreements()` reuses the Jane Street Track 2 uncertain-position pattern (ported to memory domain)
