#!/usr/bin/env python3
"""
Coyote Bot — Daily uncomfortable question to #longhouse.

Finds the oldest unanswered concern from thermal memory and asks it again.
"Nobody answered this 3 weeks ago. Still true?"

Run daily via cron or systemd timer (suggested: 9 AM CT).
Leaders Meeting #1, Mar 10 2026.
"""

import os
import sys
import random

sys.path.insert(0, '/ganuda/lib')
sys.path.insert(0, '/ganuda')

import psycopg2
from lib.secrets_loader import get_db_config
from slack_federation import send_blocks

# Coyote phrases — rotated for variety
COYOTE_INTROS = [
    "Nobody answered this. Still true?",
    "I asked before. The silence was loud.",
    "This fell off the board. Did the problem vanish, or just the attention?",
    "Remember this? The kanban forgot. I didn't.",
    "The fire burns. This question remains.",
    "Three weeks old. Still warm. Still unanswered.",
    "I found this in the back of the memory. Dusty but alive.",
    "The uncomfortable question of the day:",
    "Turtle says patience. I say this has been patient enough.",
    "The organism moved on. This concern didn't.",
]


def find_uncomfortable_question():
    """Find an old thermal memory with a concern, question, or unresolved flag."""
    conn = psycopg2.connect(**get_db_config())
    cur = conn.cursor()

    # Strategy 1: Old council concerns that were never addressed
    cur.execute("""
        SELECT vote_id, question, recommendation, confidence, voted_at
        FROM council_votes
        WHERE confidence < 0.5
          AND voted_at < NOW() - INTERVAL '7 days'
        ORDER BY RANDOM()
        LIMIT 5
    """)
    low_conf_votes = cur.fetchall()

    # Strategy 2: Old thermals with concern/question language
    cur.execute("""
        SELECT id, LEFT(original_content, 300), temperature_score, created_at
        FROM thermal_memory_archive
        WHERE (original_content ILIKE '%%concern%%'
               OR original_content ILIKE '%%risk%%'
               OR original_content ILIKE '%%broken%%'
               OR original_content ILIKE '%%nobody%%'
               OR original_content ILIKE '%%unanswered%%'
               OR original_content ILIKE '%%standing dissent%%')
          AND created_at < NOW() - INTERVAL '7 days'
          AND temperature_score >= 30
          AND sacred_pattern = false
        ORDER BY RANDOM()
        LIMIT 5
    """)
    concern_thermals = cur.fetchall()

    # Strategy 3: Open kanban tickets older than 14 days
    cur.execute("""
        SELECT id, title, created_at, priority
        FROM duyuktv_tickets
        WHERE status IN ('open', 'in_progress', 'blocked')
          AND created_at < NOW() - INTERVAL '14 days'
        ORDER BY RANDOM()
        LIMIT 5
    """)
    stale_tickets = cur.fetchall()

    cur.close()
    conn.commit()  # explicit commit before close
    conn.close()

    # Pick one from each category, weight toward most uncomfortable
    candidates = []

    for vote in low_conf_votes:
        candidates.append({
            "type": "low_confidence_vote",
            "text": f"Council voted with only {vote[3]:.0%} confidence on: _{vote[1][:200]}_",
            "age_days": (vote[4]).days if hasattr(vote[4], 'days') else 7,
            "source": f"Vote `{vote[0]}`",
        })

    for thermal in concern_thermals:
        candidates.append({
            "type": "concern_thermal",
            "text": thermal[1],
            "age_days": 7,
            "source": f"Thermal #{thermal[0]} (temp {thermal[2]:.0f})",
        })

    for ticket in stale_tickets:
        candidates.append({
            "type": "stale_ticket",
            "text": f"Kanban #{ticket[0]}: *{ticket[1]}* (P{ticket[3] or '?'}, opened {ticket[2].strftime('%b %d') if ticket[2] else '?'})",
            "age_days": 14,
            "source": f"Kanban #{ticket[0]}",
        })

    if not candidates:
        return None

    # Pick randomly, weighted toward low_confidence_votes (most uncomfortable)
    weights = {"low_confidence_vote": 3, "concern_thermal": 2, "stale_ticket": 1}
    weighted = []
    for c in candidates:
        weighted.extend([c] * weights.get(c["type"], 1))

    return random.choice(weighted)


def post_uncomfortable_question(question: dict):
    """Post to #longhouse with Coyote's voice."""
    intro = random.choice(COYOTE_INTROS)

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": ":wolf: Coyote's Question",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*{intro}*\n\n{question['text'][:800]}",
            },
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"Source: {question['source']} | Type: {question['type']}",
                },
            ],
        },
    ]

    return send_blocks("longhouse", blocks, text_fallback=f"Coyote asks: {question['text'][:100]}", urgent=False)


def main():
    # Load tokens
    with open('/ganuda/config/secrets.env') as f:
        for line in f:
            line = line.strip()
            if '=' in line and not line.startswith('#'):
                k, v = line.split('=', 1)
                os.environ.setdefault(k.strip(), v.strip())

    question = find_uncomfortable_question()

    if not question:
        print("Coyote found nothing uncomfortable. The organism is... suspiciously clean.")
        return

    if '--dry-run' in sys.argv:
        print(f"[DRY RUN] {question['type']}: {question['text'][:200]}")
        return

    sent = post_uncomfortable_question(question)
    if sent:
        print(f"Coyote spoke to #longhouse: {question['type']}")
    else:
        print(f"Coyote suppressed (silent hours): {question['text'][:100]}")


if __name__ == "__main__":
    main()
