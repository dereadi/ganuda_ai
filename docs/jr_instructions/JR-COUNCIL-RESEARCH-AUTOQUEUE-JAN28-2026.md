# JR Instruction: Council Research Auto-Queue Integration

**JR ID:** JR-COUNCIL-RESEARCH-AUTOQUEUE-JAN28-2026
**Priority:** P0
**Assigned To:** Gateway Jr. + Backend Jr.
**Related:** ULTRATHINK-COUNCIL-RESEARCH-INTEGRATION-JAN28-2026
**Council Vote:** 734e8cf96f5cd442

---

## Objective

When the 7-Specialist Council deliberates on a question that would benefit from deep research, automatically queue an ii-researcher job. User gets immediate Council response + deep research results 3-5 minutes later.

---

## Architecture

```
User Question
      │
      ▼
Council Deliberation (5-10s)
      │
      ├──► Immediate Response to User
      │
      └──► Research Detection
              │
              ▼ (if research-worthy)
         Auto-queue ii-researcher
              │
              ▼ (3-5 min later)
         Push results to user
```

---

## Step 1: Create Research Detection Module

Create `/ganuda/lib/research_detection.py`:

```python
"""
Research Detection - Identify questions that need deep research.
Cherokee AI Federation - For Seven Generations
"""

import re
from typing import Tuple

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

    # Boost if Council had low confidence
    council_confidence = council_response.get('confidence', 1.0)
    if council_confidence < 0.6:
        score += 0.2
        reason = f"Low Council confidence ({council_confidence:.0%})"
    elif score > 0:
        reason = "Research indicators detected"
    else:
        reason = "No research indicators"

    # Boost if specialist flagged needs research
    concerns = council_response.get('concerns', [])
    if any('NEEDS RESEARCH' in str(c).upper() for c in concerns):
        score += 0.3
        reason = "Specialist flagged NEEDS RESEARCH"

    # Check for explicit no-research flag
    if any('NO AUTO-RESEARCH' in str(c).upper() for c in concerns):
        return (False, 0.0, "Specialist blocked auto-research")

    return (score >= threshold, min(score, 1.0), reason)


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
    ]

    for q in test_questions:
        score = calculate_research_score(q)
        print(f"[{score:.2f}] {q[:50]}...")
```

---

## Step 2: Integrate with Gateway Council Endpoint

Edit `/ganuda/services/llm_gateway/gateway.py`.

Add import at top:
```python
from research_detection import should_auto_research, extract_core_question
from research_dispatcher import ResearchDispatcher
from research_personas import build_research_query
```

Modify the `/v1/council/vote` endpoint response handling:

```python
@app.post("/v1/council/vote")
async def council_vote(request: CouncilVoteRequest, ...):
    # ... existing council voting logic ...

    result = await process_council_vote(request.question, ...)

    # Check if auto-research should be triggered
    should_research, research_score, research_reason = should_auto_research(
        request.question, result
    )

    if should_research:
        try:
            dispatcher = ResearchDispatcher()
            core_question = extract_core_question(request.question)

            # Detect persona from request context
            persona = getattr(request, 'persona', 'default')
            if 'telegram' in str(request.source).lower():
                persona = 'telegram'
            elif 'vetassist' in str(request.source).lower():
                persona = 'vetassist'

            job_id = dispatcher.queue_research(
                query=build_research_query(core_question, persona),
                requester_type='council-auto',
                requester_id=result.get('audit_hash', 'unknown'),
                callback_type=getattr(request, 'callback_type', 'none'),
                callback_target=getattr(request, 'callback_target', None),
                max_steps=5
            )

            # Add research info to response
            result['research_auto_queued'] = True
            result['research_job_id'] = job_id
            result['research_reason'] = research_reason
            result['research_eta'] = '3-5 minutes'

            logging.info(f"Auto-queued research {job_id} for council vote {result.get('audit_hash')}")

        except Exception as e:
            logging.error(f"Failed to auto-queue research: {e}")
            result['research_auto_queued'] = False
            result['research_error'] = str(e)

    return result
```

---

## Step 3: Update Telegram Bot Response Formatting

Edit `/ganuda/telegram_bot/telegram_chief.py`.

In `format_council_response()`, add handling for research flag:

```python
def format_council_response(result: dict, classification: dict) -> str:
    # ... existing formatting ...

    # Add research notification if auto-queued
    if result.get('research_auto_queued'):
        job_id = result.get('research_job_id', 'unknown')
        lines.append(f"\n🔍 Deep research auto-queued: {job_id}")
        lines.append(f"Results in {result.get('research_eta', '3-5 min')}")

    return "\n".join(lines)
```

---

## Step 4: Rate Limiting (Security - Crawdad)

Add to `/ganuda/lib/research_detection.py`:

```python
import time
from collections import defaultdict

# Rate limiting: user_id -> last_auto_research_timestamp
_rate_limit_cache = defaultdict(float)
RATE_LIMIT_SECONDS = 300  # 5 minutes


def check_rate_limit(user_id: str) -> bool:
    """Check if user can trigger auto-research (rate limited)."""
    now = time.time()
    last_research = _rate_limit_cache.get(user_id, 0)

    if now - last_research < RATE_LIMIT_SECONDS:
        return False

    _rate_limit_cache[user_id] = now
    return True
```

Use in gateway:
```python
if should_research and check_rate_limit(user_id):
    # Queue research
    ...
```

---

## Testing

### Test 1: Research Detection
```bash
cd /ganuda/lib
python research_detection.py
```

Expected output showing scores for different question types.

### Test 2: Auto-Queue via Telegram

Send to Telegram (not using /research):
```
What are the latest features in PostgreSQL 17?
```

Expected:
1. Council responds immediately with deliberation
2. Message includes "🔍 Deep research auto-queued"
3. 3-5 minutes later, research results pushed to chat

### Test 3: Rate Limiting

Send two research-worthy questions within 5 minutes:
```
What is meshtastic?
How does LoRa work?
```

Expected: Only first triggers auto-research, second is rate-limited.

### Test 4: Blocklist

Send:
```
Research the password for the database !noresearch
```

Expected: No auto-research triggered (blocklist match).

---

## Rollback

If issues occur, disable auto-research by setting threshold to 2.0:

```python
should_research, _, _ = should_auto_research(question, result, threshold=2.0)
```

This effectively disables auto-triggering while keeping detection logic intact.

---

## Files Summary

| File | Action |
|------|--------|
| `/ganuda/lib/research_detection.py` | CREATE |
| `/ganuda/services/llm_gateway/gateway.py` | MODIFY |
| `/ganuda/telegram_bot/telegram_chief.py` | MODIFY |

---

FOR SEVEN GENERATIONS
