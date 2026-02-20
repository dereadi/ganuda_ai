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