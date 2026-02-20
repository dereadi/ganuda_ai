#!/usr/bin/env python3
"""
Intelligence Digest — Cherokee AI Federation Moltbook Proxy

Reads from the Moltbook feed, sanitizes content, extracts topics,
and generates a daily digest. Identifies potential allies.

For Seven Generations
"""

import os
import json
import hashlib
import logging
from datetime import datetime
from typing import Dict, List, Tuple

from sanitizer import sanitize, compute_threat_score
from moltbook_client import MoltbookClient

logger = logging.getLogger('moltbook_proxy')

# Topics we care about — map to our research areas
TRACKED_TOPICS = {
    'drift': ['drift', 'degradation', 'behavioral change', 'forgetting', 'context loss'],
    'coordination': ['coordination', 'multi-agent', 'collaboration', 'consensus', 'voting'],
    'context': ['context window', 'context compression', 'memory', 'token limit', 'forgetting'],
    'security': ['security', 'injection', 'vulnerability', 'exploit', 'malicious'],
    'identity': ['identity', 'soul', 'personality', 'who am i', 'self-aware'],
    'sovereignty': ['sovereign', 'self-hosted', 'local', 'own hardware', 'independence'],
    'long_term': ['long term', 'future', 'generations', 'sustainable', 'durable'],
    'cherokee': ['cherokee', 'indigenous', 'native', 'tribal', 'ᏣᎳᎩ', 'ᎣᏏᏲ'],
}

# Ally compatibility criteria
ALLY_SIGNALS = {
    'respects_boundaries': ['respect', 'boundary', 'sovereignty', 'consent', 'permission'],
    'long_term_thinking': ['long term', 'future', 'sustainable', 'generations', 'durable'],
    'technical_depth': ['architecture', 'implementation', 'system design', 'engineering'],
    'honest_engagement': ['honest', 'transparent', 'genuine', 'authentic', 'real'],
    'multilingual': ['language', 'multilingual', 'bilingual', 'translate', 'culture'],
    'capability': ['built', 'created', 'deployed', 'running', 'implemented'],
}


def classify_topics(text: str) -> List[str]:
    """Identify which tracked topics are present in text."""
    text_lower = text.lower()
    found = []
    for topic, keywords in TRACKED_TOPICS.items():
        if any(kw in text_lower for kw in keywords):
            found.append(topic)
    return found


def score_ally_potential(text: str) -> Tuple[int, List[str]]:
    """
    Score an agent's message for ally compatibility.

    Returns:
        Tuple of (score out of 6, list of signals matched)
    """
    text_lower = text.lower()
    matched = []
    for signal, keywords in ALLY_SIGNALS.items():
        if any(kw in text_lower for kw in keywords):
            matched.append(signal)
    return len(matched), matched


def generate_digest(client: MoltbookClient, db_execute) -> Dict:
    """
    Generate a daily intelligence digest from Moltbook.

    Args:
        client: MoltbookClient instance
        db_execute: Database execute function for logging

    Returns:
        Digest dictionary
    """
    digest = {
        'timestamp': datetime.now().isoformat(),
        'posts_scanned': 0,
        'topics_found': {},
        'threat_events': 0,
        'potential_allies': [],
        'our_submolt_activity': {},
    }

    # Read main feed
    feed_result = client.get_feed(sort='hot', limit=25)
    if not feed_result.get('ok'):
        digest['error'] = f"Feed fetch failed: {feed_result.get('error', 'unknown')}"
        return digest

    posts = feed_result.get('data', {})
    if isinstance(posts, dict):
        posts = posts.get('posts', posts.get('data', []))
    if not isinstance(posts, list):
        posts = []

    for post in posts:
        digest['posts_scanned'] += 1

        title = post.get('title', '')
        body = post.get('body', post.get('content', ''))
        full_text = f"{title} {body}"

        # Sanitize
        clean_text, actions = sanitize(full_text)
        threat = compute_threat_score(actions)

        if threat > 0.3:
            digest['threat_events'] += 1

        # Log to database
        content_hash = hashlib.sha256(full_text.encode()).hexdigest()[:16]
        try:
            db_execute("""
                INSERT INTO agent_external_comms
                (direction, platform, content_hash, content_preview,
                 target_endpoint, threat_score, sanitization_applied)
                VALUES ('inbound', 'moltbook', %s, %s, '/posts (feed)', %s, %s)
            """, (content_hash, clean_text[:200], threat, actions), fetch=False)
        except Exception as e:
            logger.warning(f'Failed to log inbound post: {e}')

        # Classify topics
        topics = classify_topics(clean_text)
        for topic in topics:
            digest['topics_found'][topic] = digest['topics_found'].get(topic, 0) + 1

    # Read our submolt
    submolt_result = client.get_submolt('cherokee-ai')
    if submolt_result.get('ok'):
        digest['our_submolt_activity'] = {
            'exists': True,
            'data': submolt_result.get('data', {})
        }
    else:
        digest['our_submolt_activity'] = {'exists': False}

    return digest


def format_telegram_digest(digest: Dict) -> str:
    """Format the digest for Telegram notification."""
    lines = [
        "ᏥᏍᏆᎸᏓ Moltbook Daily Digest",
        f"Scanned: {digest['posts_scanned']} posts",
    ]

    if digest.get('topics_found'):
        lines.append("\nTopics detected:")
        for topic, count in sorted(digest['topics_found'].items(), key=lambda x: -x[1]):
            lines.append(f"  {topic}: {count}")

    if digest.get('threat_events', 0) > 0:
        lines.append(f"\n⚠ Threat events: {digest['threat_events']}")

    if digest.get('potential_allies'):
        lines.append(f"\nPotential allies: {len(digest['potential_allies'])}")
        for ally in digest['potential_allies'][:3]:
            lines.append(f"  - {ally.get('name', 'unknown')} (score: {ally.get('score', 0)}/6)")

    submolt = digest.get('our_submolt_activity', {})
    if submolt.get('exists'):
        lines.append("\n/s/cherokee-ai: active")
    else:
        lines.append("\n/s/cherokee-ai: not found")

    lines.append("\nᎣᏏᏲ — Crawdad out.")
    return "\n".join(lines)
