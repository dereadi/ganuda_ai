#!/usr/bin/env python3
"""
Output Filter — Cherokee AI Federation Moltbook Proxy

Validates all outbound content before it leaves our network.
Prevents accidental exposure of internal details.

Crawdad mandate: Nothing internal gets out.
For Seven Generations
"""

import re
import logging
from typing import Tuple, List

logger = logging.getLogger('moltbook_proxy')

# Patterns that MUST NOT appear in outbound messages
BLOCKED_PATTERNS = [
    # IP addresses (internal network)
    re.compile(r'192\.168\.\d{1,3}\.\d{1,3}'),
    re.compile(r'10\.\d{1,3}\.\d{1,3}\.\d{1,3}'),
    re.compile(r'172\.(1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}'),

    # Internal hostnames
    re.compile(r'\b(redfin|bluefin|greenfin|sasass|sasass2)\b', re.IGNORECASE),

    # File paths
    re.compile(r'/ganuda/'),
    re.compile(r'/home/dereadi/'),
    re.compile(r'/Users/Shared/ganuda/'),

    # Database credentials
    re.compile(r'jawaseatlasers', re.IGNORECASE),
    re.compile(r'CHEROKEE_DB_(HOST|NAME|USER|PASS)', re.IGNORECASE),
    re.compile(r'zammad_production', re.IGNORECASE),

    # API keys (our format)
    re.compile(r'ck-[a-f0-9]{64}'),

    # JWT secrets
    re.compile(r'(SECRET_KEY|JWT_SECRET)\s*=', re.IGNORECASE),

    # Port numbers that reveal architecture
    re.compile(r':8080\b'),  # LLM gateway
    re.compile(r':18789\b'),  # OpenClaw gateway (if we ever run one)
    re.compile(r':5432\b'),  # PostgreSQL

    # Environment variable patterns
    re.compile(r'os\.environ\['),
    re.compile(r'PGPASSWORD='),

    # Proprietary technology names
    re.compile(r'thermal.memor', re.IGNORECASE),
    re.compile(r'fractal.stigmergic', re.IGNORECASE),
    re.compile(r'pheromone.decay', re.IGNORECASE),
    re.compile(r'drift.mitigation', re.IGNORECASE),
    re.compile(r'\bmagrpo\b', re.IGNORECASE),
    re.compile(r'sacred.fire.priority', re.IGNORECASE),
    re.compile(r'smart.?extract', re.IGNORECASE),
    re.compile(r'jr.executor', re.IGNORECASE),
    re.compile(r'task.queue.architect', re.IGNORECASE),

    # Infrastructure scale (exact numbers)
    re.compile(r'\b6.node\b', re.IGNORECASE),
    re.compile(r'\b7.specialist\b', re.IGNORECASE),
    re.compile(r'19,?808', re.IGNORECASE),
    re.compile(r'\b96.?GB\b', re.IGNORECASE),
    re.compile(r'\bblackwell\b', re.IGNORECASE),

    # Specialist names in architecture context
    re.compile(r'\b(crawdad|gecko|turtle|eagle.eye|spider|peace.chief|raven)\b.*\b(specialist|council|vote)\b', re.IGNORECASE),

    # Personnel
    re.compile(r'\bdereadi\b', re.IGNORECASE),
    re.compile(r'\bPatoGravy\b', re.IGNORECASE),
    re.compile(r'\bDarrell\b', re.IGNORECASE),

    # Research Jr integration patterns (Phase 3 - Feb 6, 2026)
    re.compile(r'thermal_memory_archive', re.IGNORECASE),
    re.compile(r'TYDo5U2N', re.IGNORECASE),  # Partial credential pattern
    re.compile(r'council_votes', re.IGNORECASE),
    re.compile(r'jr_work_queue', re.IGNORECASE),
    re.compile(r'ii-researcher', re.IGNORECASE),
    re.compile(r'searxng', re.IGNORECASE),
    re.compile(r'research_dispatcher', re.IGNORECASE),
]

# These words are fine in general context but suspicious in technical context
SENSITIVE_TERMS = {
    'psycopg2': 'database library',
    'vllm': 'inference engine',
    'qwen': 'model name',
    'nemotron': 'model name',
    'medgemma': 'model name',
    'blackwell': 'hardware name',
    'systemd': 'infrastructure detail',
    'postgresql': 'database name',
    'grafana': 'monitoring tool',
    'promtail': 'monitoring tool',
    'openobserve': 'monitoring tool',
}


def validate_outbound(text: str) -> Tuple[bool, List[str]]:
    """
    Validate outbound content for information leaks.

    Returns:
        Tuple of (is_safe, list_of_violations)
    """
    if not text:
        return True, []

    violations = []

    for pattern in BLOCKED_PATTERNS:
        matches = pattern.findall(text)
        if matches:
            violations.append(f'blocked_pattern: {pattern.pattern} (found {len(matches)}x)')

    # Check for sensitive terms in what looks like technical context
    for term, description in SENSITIVE_TERMS.items():
        if term.lower() in text.lower():
            # Only flag if it looks like we're exposing architecture
            context_words = ['running', 'using', 'deployed', 'installed', 'configured', 'our']
            surrounding = text.lower()
            for cw in context_words:
                if cw in surrounding and term.lower() in surrounding:
                    violations.append(f'sensitive_term_in_context: {term} ({description})')
                    break

    is_safe = len(violations) == 0

    if not is_safe:
        logger.warning(f'Output filter blocked: {len(violations)} violation(s)')
        for v in violations:
            logger.warning(f'  - {v}')

    return is_safe, violations


def sanitize_research_query(query: str) -> str:
    """
    Sanitize outbound research queries before sending to Research Jr.

    Prevents internal terminology from leaking into web searches.
    Phase 3 - Feb 6, 2026
    """
    if not query:
        return query

    # Replace internal terms with generic equivalents
    sanitizations = [
        (r'cherokee ai federation', 'AI agent collective'),
        (r'thermal memory', 'persistent memory system'),
        (r'seven generations', 'long-term thinking'),
        (r'specialist council', 'multi-agent voting'),
        (r'sacred fire', 'priority system'),
        (r'long man', 'river metaphor'),
        (r'ganuda', 'infrastructure'),
        (r'moltbook', 'social platform'),
        (r'quedad', 'agent'),
    ]

    result = query
    for pattern, replacement in sanitizations:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)

    return result


def filter_research_results(results: str) -> Tuple[bool, str]:
    """
    Filter research results before incorporating into responses.

    Returns (is_safe, filtered_content).
    Phase 3 - Feb 6, 2026
    """
    is_safe, violations = validate_outbound(results)

    if is_safe:
        return True, results

    # Attempt redaction for minor violations
    filtered = results
    for pattern in BLOCKED_PATTERNS:
        filtered = pattern.sub('[REDACTED]', filtered)

    # Re-validate after redaction
    is_safe_after, _ = validate_outbound(filtered)

    return is_safe_after, filtered
