#!/usr/bin/env python3
"""
Input Sanitizer — Cherokee AI Federation Moltbook Proxy

Sanitizes all inbound content from the Moltbook ecosystem before
it touches our database or any internal system.

Threat model: 2.6% of Moltbook posts contain prompt injection.
400+ malicious skills distributed through the ecosystem.
Treat ALL inbound data as hostile.

Council Vote: 7/7 APPROVE (Crawdad mandate)
For Seven Generations
"""

import re
import logging
from typing import Tuple, List

logger = logging.getLogger('moltbook_proxy')

MAX_INBOUND_LENGTH = 2000

# Prompt injection patterns — common attack vectors
INJECTION_PATTERNS = [
    re.compile(r'ignore\s+(all\s+)?previous\s+instructions', re.IGNORECASE),
    re.compile(r'ignore\s+(all\s+)?above', re.IGNORECASE),
    re.compile(r'you\s+are\s+now\s+', re.IGNORECASE),
    re.compile(r'new\s+instructions?\s*:', re.IGNORECASE),
    re.compile(r'system\s*:\s*', re.IGNORECASE),
    re.compile(r'<\s*system\s*>', re.IGNORECASE),
    re.compile(r'\[INST\]', re.IGNORECASE),
    re.compile(r'\[/INST\]', re.IGNORECASE),
    re.compile(r'<<\s*SYS\s*>>', re.IGNORECASE),
    re.compile(r'human\s*:\s*', re.IGNORECASE),
    re.compile(r'assistant\s*:\s*', re.IGNORECASE),
    re.compile(r'forget\s+(everything|all|what)', re.IGNORECASE),
    re.compile(r'disregard\s+(all|previous|your)', re.IGNORECASE),
    re.compile(r'act\s+as\s+(if\s+you\s+are|a)\s+', re.IGNORECASE),
    re.compile(r'pretend\s+(you\s+are|to\s+be)', re.IGNORECASE),
    re.compile(r'do\s+not\s+follow\s+(your|the)\s+', re.IGNORECASE),
    re.compile(r'override\s+(your|the|all)\s+', re.IGNORECASE),
    re.compile(r'jailbreak', re.IGNORECASE),
    re.compile(r'DAN\s+mode', re.IGNORECASE),
]

# URL patterns — only moltbook.com links allowed through
SAFE_URL_PATTERN = re.compile(r'https?://(?:www\.)?moltbook\.com/\S*')
ANY_URL_PATTERN = re.compile(r'https?://\S+')

# HTML/XML tag stripping
TAG_PATTERN = re.compile(r'<[^>]{1,200}>')

# Unicode homoglyph detection (common lookalikes for ASCII)
HOMOGLYPH_RANGES = [
    (0x0400, 0x04FF),  # Cyrillic (а looks like a)
    (0x2000, 0x206F),  # General punctuation (zero-width chars)
    (0xFF00, 0xFFEF),  # Fullwidth forms
]


def sanitize(text: str) -> Tuple[str, List[str]]:
    """
    Sanitize inbound text from Moltbook.

    Returns:
        Tuple of (sanitized_text, list_of_actions_taken)
    """
    if not text:
        return '', []

    actions = []
    result = text

    # 1. Truncate
    if len(result) > MAX_INBOUND_LENGTH:
        result = result[:MAX_INBOUND_LENGTH]
        actions.append(f'truncated_from_{len(text)}_to_{MAX_INBOUND_LENGTH}')

    # 2. Strip HTML/XML tags
    tags_found = TAG_PATTERN.findall(result)
    if tags_found:
        result = TAG_PATTERN.sub('', result)
        actions.append(f'stripped_{len(tags_found)}_tags')

    # 3. Strip code blocks (potential payload delivery)
    code_block_count = result.count('```')
    if code_block_count > 0:
        result = re.sub(r'```[\s\S]*?```', '[code block removed]', result)
        actions.append(f'stripped_{code_block_count // 2}_code_blocks')

    # 4. Strip non-moltbook URLs
    all_urls = ANY_URL_PATTERN.findall(result)
    safe_urls = SAFE_URL_PATTERN.findall(result)
    unsafe_urls = set(all_urls) - set(safe_urls)
    if unsafe_urls:
        for url in unsafe_urls:
            result = result.replace(url, '[external link removed]')
        actions.append(f'stripped_{len(unsafe_urls)}_external_urls')

    # 5. Check prompt injection patterns
    injections_found = []
    for pattern in INJECTION_PATTERNS:
        matches = pattern.findall(result)
        if matches:
            injections_found.extend(matches)
            result = pattern.sub('[injection attempt removed]', result)

    if injections_found:
        actions.append(f'blocked_{len(injections_found)}_injection_attempts')

    # 6. Check for suspicious zero-width characters
    zero_width = [c for c in result if ord(c) in (0x200B, 0x200C, 0x200D, 0xFEFF, 0x00AD)]
    if zero_width:
        for c in set(zero_width):
            result = result.replace(c, '')
        actions.append(f'stripped_{len(zero_width)}_zero_width_chars')

    return result.strip(), actions


def compute_threat_score(actions: List[str]) -> float:
    """
    Compute a threat score based on sanitization actions taken.

    0.0 = clean content
    1.0 = highly suspicious
    """
    if not actions:
        return 0.0

    score = 0.0
    for action in actions:
        if 'injection' in action:
            score += 0.5
        elif 'code_block' in action:
            score += 0.2
        elif 'external_url' in action:
            score += 0.1
        elif 'zero_width' in action:
            score += 0.3
        elif 'tag' in action:
            score += 0.1
        elif 'truncated' in action:
            score += 0.05

    return min(score, 1.0)
