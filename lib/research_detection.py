"""
Research Detection - Identify questions that need deep research.
Cherokee AI Federation - For Seven Generations
"""

import re
import time
from typing import Tuple
from collections import defaultdict

# Patterns that indicate research would be valuable
RESEARCH_INDICATORS = [
    # Factual queries
    (r'\b(what is|what are|what was)\b', 0.6),
    (r'\b(how does|how do|how did|how to)\b', 0.5),
    (r'\b(why does|why do|why did)\b', 0.4),

    # Explicit research requests
    (r'\b(find out|research|look up|search for|investigate)\b', 0.9),
    (r'\b(can you find|can you research|can you look)\b', 0.9),

    # Current/recent information
    (r'\b(latest|recent|current|new|2026|2025)\b', 0.7),
    (r'\b(today|this week|this month|this year)\b', 0.6),

    # Location-specific queries
    (r'\b(near|in|around|located|where)\b.*\b(city|town|state|airport|area|region)\b', 0.7),
    (r'\b(XNA|NWA|Bentonville|Fayetteville|Rogers|Arkansas)\b', 0.5),

    # Technical specifications
    (r'\b(specifications?|specs|features|capabilities)\b', 0.6),
    (r'\b(compare|comparison|versus|vs\.?|difference between)\b', 0.7),
    (r'\b(price|cost|pricing|how much)\b', 0.5),

    # Product/service queries
    (r'\b(where to buy|where can I get|availability)\b', 0.7),
    (r'\b(review|reviews|rating|ratings)\b', 0.6),
]

# Patterns that should NOT trigger auto-research
RESEARCH_BLOCKLIST = [
    r'\b(password|secret|token|key|credential)\b',
    r'\b(192\.168\.|10\.|172\.(1[6-9]|2[0-9]|3[01])\.)',  # Internal IPs
    r'\b(delete|drop|truncate|destroy|remove all)\b',  # Destructive
    r'!noresearch',  # Explicit opt-out
]

# Rate limiting: user_id -> last_auto_research_timestamp
_rate_limit_cache = defaultdict(float)
RATE_LIMIT_SECONDS = 300  # 5 minutes


def calculate_research_score(question: str) -> float:
    """Calculate how research-worthy a question is (0.0 to 1.0)."""
    question_lower = question.lower()

    # Check blocklist first
    for pattern in RESEARCH_BLOCKLIST:
        if re.search(pattern, question_lower):
            return 0.0

    # Accumulate score from indicators
    score = 0.0
    matches = 0

    for pattern, weight in RESEARCH_INDICATORS:
        if re.search(pattern, question_lower):
            score += weight
            matches += 1

    # Normalize: more matches = higher confidence, cap at 1.0
    if matches > 0:
        score = min(score / max(matches, 2), 1.0)

    return score


def should_auto_research(
    question: str,
    council_response: dict,
    threshold: float = 0.5
) -> Tuple[bool, float, str]:
    """
    Determine if question warrants auto-research.

    Returns:
        (should_research, confidence_score, reason)
    """
    # Calculate base score from question
    score = calculate_research_score(question)
    reason = "No research indicators"

    # Boost if Council had low confidence
    council_confidence = council_response.get('confidence', 1.0)
    if council_confidence < 0.6:
        score += 0.2
        reason = f"Low Council confidence ({council_confidence:.0%})"
    elif score > 0:
        reason = "Research indicators detected"

    # Boost if specialist flagged needs research
    concerns = council_response.get('concerns', [])
    if any('NEEDS RESEARCH' in str(c).upper() for c in concerns):
        score += 0.3
        reason = "Specialist flagged NEEDS RESEARCH"

    # Check for explicit no-research flag
    if any('NO AUTO-RESEARCH' in str(c).upper() for c in concerns):
        return (False, 0.0, "Specialist blocked auto-research")

    return (score >= threshold, min(score, 1.0), reason)


def check_rate_limit(user_id: str) -> bool:
    """Check if user can trigger auto-research (rate limited)."""
    now = time.time()
    last_research = _rate_limit_cache.get(user_id, 0)

    if now - last_research < RATE_LIMIT_SECONDS:
        return False

    _rate_limit_cache[user_id] = now
    return True


def extract_core_question(question: str) -> str:
    """Extract core question, stripping conversation context."""
    # Remove context headers
    if '[Recent conversation:' in question:
        # Find the actual question after context
        parts = question.split('asks:')
        if len(parts) > 1:
            return parts[-1].strip()

    # Remove system prefixes
    prefixes = ['Telegram user', 'User', 'Question:']
    for prefix in prefixes:
        if question.startswith(prefix):
            question = question.split(':', 1)[-1].strip()

    return question.strip()


# Self-test
if __name__ == "__main__":
    test_questions = [
        "What is the VA rating for tinnitus?",
        "Research meshtastic towers near XNA",
        "Restart the gateway service",
        "What are the latest PostgreSQL 17 features?",
        "Delete all user data !noresearch",
        "How does nftables compare to iptables?",
        "Check the disk space on bluefin",
    ]

    print("Research Detection Self-Test")
    print("=" * 50)
    for q in test_questions:
        score = calculate_research_score(q)
        indicator = "✓" if score >= 0.5 else "✗"
        print(f"[{score:.2f}] {indicator} {q[:50]}...")
    print("=" * 50)
    print("FOR SEVEN GENERATIONS")
