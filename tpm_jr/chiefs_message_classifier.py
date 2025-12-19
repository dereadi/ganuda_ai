#!/usr/bin/env python3
"""
Chiefs Message Classifier - Phase 1 of Chiefs Deliberation v2

Classifies incoming thermal memory messages to determine appropriate
deliberation depth before processing.

Reference: KB-CHIEFS-DELIBERATION-V2.md
"""

import re
import sys
import json
import logging
import requests
from typing import Dict, List, Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Message type keywords - order matters for priority
MESSAGE_TYPES = {
    'consultation': [
        'what do you think', 'should we', 'options', 'direction',
        'advice', 'recommend', 'opinion', 'which option', 'consult',
        'strategic', 'guidance', 'perspective', 'weigh in', 'your view',
        'tribal consultation', 'chiefs guidance', 'deliberate on',
        'option a', 'option b', 'option c'
    ],
    'escalation': [
        'blocked', 'stuck', 'need help', 'error', 'failed',
        'cannot proceed', 'requires guidance', 'escalating',
        'blocker', 'urgent help', 'critical issue', 'broken'
    ],
    'research': [
        'investigate', 'learn about', 'explore', 'find out',
        'research', 'discover', 'understand how', 'analyze',
        'study', 'examine', 'look into'
    ],
    'status_update': [
        'complete', 'done', 'finished', 'deployed', 'operational',
        'mission complete', 'status:', 'update:', 'progress:',
        'accomplished', 'delivered', 'shipped'
    ],
    'work_order': [
        'build', 'fix', 'create', 'implement', 'add', 'update',
        'deploy', 'install', 'configure', 'modify', 'mission dispatch',
        'write', 'develop', 'construct', 'make', 'generate',
        'deliverable:', 'objective:'
    ]
}

# Deliberation depth per type
DELIBERATION_DEPTH = {
    'consultation': 'full',      # 3 minds + synthesis, return wisdom
    'escalation': 'full',        # 3 minds + synthesis, may assign Jr
    'research': 'full',          # 3 minds + synthesis, assign research Jr
    'status_update': 'none',     # Archive only
    'work_order': 'medium'       # Quick review, assign Jr
}

# Action per type
MESSAGE_ACTIONS = {
    'consultation': 'deliberate_and_respond',
    'escalation': 'deliberate_and_respond',
    'research': 'deliberate_and_assign',
    'status_update': 'archive_only',
    'work_order': 'review_and_assign'
}


def classify_message(content: str, use_llm_fallback: bool = True) -> Dict:
    """
    Classify a thermal memory message by type.

    Args:
        content: The message content to classify
        use_llm_fallback: Whether to use LLM for ambiguous cases

    Returns:
        {
            'message_type': str,
            'confidence': float,
            'matched_keywords': list,
            'deliberation_depth': str,
            'action': str,
            'reasoning': str
        }
    """
    content_lower = content.lower()

    # Count keyword matches per type
    type_scores = {}
    type_matches = {}

    for msg_type, keywords in MESSAGE_TYPES.items():
        matches = []
        for keyword in keywords:
            if keyword in content_lower:
                matches.append(keyword)
        type_scores[msg_type] = len(matches)
        type_matches[msg_type] = matches

    # Find best match
    best_type = max(type_scores, key=type_scores.get)
    best_score = type_scores[best_type]
    total_matches = sum(type_scores.values())

    # Calculate confidence
    if total_matches == 0:
        confidence = 0.0
    elif best_score == total_matches:
        # All matches are for one type
        confidence = min(0.95, 0.5 + (best_score * 0.15))
    else:
        # Multiple types matched - confidence is proportion
        confidence = best_score / total_matches if total_matches > 0 else 0.0

    # Build reasoning
    if best_score > 0:
        reasoning = f"Matched {best_score} keywords for '{best_type}': {type_matches[best_type][:5]}"
    else:
        reasoning = "No keywords matched"

    # Check for ambiguity
    sorted_scores = sorted(type_scores.items(), key=lambda x: x[1], reverse=True)
    if len(sorted_scores) >= 2:
        first, second = sorted_scores[0], sorted_scores[1]
        if first[1] > 0 and second[1] > 0 and first[1] == second[1]:
            # Tie - use priority order (consultation > escalation > research > work_order > status)
            priority_order = ['consultation', 'escalation', 'research', 'work_order', 'status_update']
            for ptype in priority_order:
                if ptype in [first[0], second[0]]:
                    best_type = ptype
                    break
            reasoning += f" (tie-breaker applied, chose '{best_type}' by priority)"
            confidence *= 0.8  # Reduce confidence for tie

    # LLM fallback for low confidence
    if confidence < 0.6 and use_llm_fallback and best_score == 0:
        llm_result = classify_with_llm(content)
        if llm_result:
            return llm_result

    # Default to work_order if nothing matched
    if best_score == 0:
        best_type = 'work_order'
        confidence = 0.3
        reasoning = "No keywords matched, defaulting to work_order"

    return {
        'message_type': best_type,
        'confidence': round(confidence, 2),
        'matched_keywords': type_matches.get(best_type, []),
        'deliberation_depth': DELIBERATION_DEPTH[best_type],
        'action': MESSAGE_ACTIONS[best_type],
        'reasoning': reasoning
    }


def classify_with_llm(content: str) -> Optional[Dict]:
    """
    Use LLM fallback for ambiguous classification.
    Uses llama3.1:8b on sasass (192.168.132.51:11434)
    """
    prompt = f"""Classify this message into ONE of these types:
- consultation: Asking for opinion/guidance/advice
- work_order: Requesting work to be done (build, fix, create)
- status_update: Reporting completion or progress
- escalation: Reporting a blocker or need for help
- research: Requesting investigation or learning

Message:
{content[:1500]}

Respond with ONLY the type name (one word):"""

    try:
        # Try sasass first
        response = requests.post(
            'http://192.168.132.51:11434/api/generate',
            json={
                'model': 'llama3.1:8b',
                'prompt': prompt,
                'stream': False,
                'options': {'temperature': 0.3, 'num_predict': 20}
            },
            timeout=30
        )

        if response.status_code == 200:
            result = response.json().get('response', '').strip().lower()

            # Parse LLM response
            for msg_type in MESSAGE_TYPES.keys():
                if msg_type in result:
                    return {
                        'message_type': msg_type,
                        'confidence': 0.65,
                        'matched_keywords': [],
                        'deliberation_depth': DELIBERATION_DEPTH[msg_type],
                        'action': MESSAGE_ACTIONS[msg_type],
                        'reasoning': f"LLM classified as '{msg_type}'"
                    }
    except Exception as e:
        logger.warning(f"LLM fallback failed: {e}")

    return None


def classify_batch(messages: List[str]) -> List[Dict]:
    """Classify multiple messages."""
    return [classify_message(msg) for msg in messages]


def main():
    """CLI interface for testing."""
    if len(sys.argv) < 2:
        print("Usage: python chiefs_message_classifier.py <message>")
        print("       python chiefs_message_classifier.py --test")
        sys.exit(1)

    if sys.argv[1] == '--test':
        # Run test cases
        test_cases = [
            ("What do you think about adding dark mode?", "consultation"),
            ("Build a new API endpoint for metrics", "work_order"),
            ("Mission FARA-001 complete, all tests passing", "status_update"),
            ("Blocked on database connection, need help", "escalation"),
            ("Investigate how other systems handle caching", "research"),
            ("Should we go with Option A or Option B?", "consultation"),
            ("Deploy the new version to production", "work_order"),
            ("I'm stuck and cannot proceed without guidance", "escalation"),
        ]

        print("=" * 70)
        print("CHIEFS MESSAGE CLASSIFIER - TEST SUITE")
        print("=" * 70)

        passed = 0
        for message, expected in test_cases:
            result = classify_message(message, use_llm_fallback=False)
            status = "PASS" if result['message_type'] == expected else "FAIL"
            if status == "PASS":
                passed += 1

            print(f"\n{status}: '{message[:50]}...'")
            print(f"  Expected: {expected}")
            print(f"  Got: {result['message_type']} (conf: {result['confidence']})")
            print(f"  Reasoning: {result['reasoning']}")

        print("\n" + "=" * 70)
        print(f"Results: {passed}/{len(test_cases)} passed")
        print("=" * 70)
    else:
        # Classify single message
        message = ' '.join(sys.argv[1:])
        result = classify_message(message)

        print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
