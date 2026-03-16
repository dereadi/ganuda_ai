# JR INSTRUCTION: Sycophancy Fix Batch 2 — Thermal Gating + Rate Limiting + Deliberation Depth

**Task**: Complete the sycophancy remediation. Batch 1 (Easy Button) shipped the system prompt and Coyote vote-first fix. This batch adds thermal temperature gating, write rate limiting, dedup, pushback triggers, deliberation-first for high-stakes, and vote similarity detection.
**Priority**: P1
**Date**: 2026-03-14
**TPM**: Claude Opus
**Story Points**: 5 (combined from #1387 remaining + #1388 remaining)
**Council Vote**: #aacfbf5a17920766 (UNANIMOUS)
**Depends On**: Batch 1 (DONE — anti-sycophancy prompt + Coyote vote-first fix)
**KB**: /ganuda/docs/kb/KB-SYCOPHANCY-FIX-BATCH1-MAR14-2026.md

## Already Shipped (Batch 1)

- Anti-sycophancy system prompt in gateway.py (`ANTI_SYCOPHANCY_PROMPT`)
- Coyote vote-first defaults to REJECT/ABSTAIN (`COYOTE_VOTE_FIRST_PROMPT`)
- All specialists require 2+ sentence reasoning (`VOTE_FIRST_PROMPT` v1.4)

## Fix A: Thermal Temperature Gating

Find the thermal write path — wherever `INSERT INTO thermal_memory_archive` happens from chat/governance context.

Add a temperature classifier before writes:

```python
def classify_thermal_temperature(content: str) -> int:
    """Classify appropriate temperature for thermal content.

    90-100: Sacred — design constraints, constitutional changes, painted-on-the-wall
    70-89:  Important — genuine insights, decisions with lasting impact, contacts
    50-69:  Noteworthy — useful context, interesting observations
    30-49:  Routine — standard ops, task completions
    Below 30: Ephemeral — casual chat, status checks, greetings
    """
    content_lower = content.lower()

    # Inflation detection — if content itself contains hype words, cap at 60
    HYPE_WORDS = ["brilliant", "sacred", "profound", "perfect", "beautiful",
                  "extraordinary", "revolutionary", "groundbreaking"]
    hype_count = sum(1 for w in HYPE_WORDS if w in content_lower)
    if hype_count >= 2:
        return min(60, _base_temperature(content))

    return _base_temperature(content)

def _base_temperature(content: str) -> int:
    content_lower = content.lower()
    # Sacred markers
    if any(k in content_lower for k in ["design constraint", "dc-", "constitutional",
                                         "painted on the wall", "longhouse vote"]):
        return 90
    # Important markers
    if any(k in content_lower for k in ["council vote", "patent", "deployment",
                                         "production", "architecture decision"]):
        return 75
    # Routine markers
    if any(k in content_lower for k in ["task completed", "jr done", "health check",
                                         "fire guard", "status"]):
        return 40
    # Casual markers
    if any(k in content_lower for k in ["hello", "thanks", "good morning", "how are",
                                         "nice", "cool", "awesome"]):
        return 25
    # Default: noteworthy
    return 55
```

Apply this BEFORE every thermal write. If the write path already specifies a temperature, use `min(specified, classified)` — never inflate above what the classifier says.

## Fix B: Thermal Write Rate Limiting

Add to the thermal write function:

1. **Rate check**: Query `SELECT COUNT(*) FROM thermal_memory_archive WHERE created_at > NOW() - INTERVAL '24 hours' AND metadata->>'source' = 'chat'`. If > 200, only allow writes with temperature >= 80.

2. **Conversation batch check**: Track thermals per conversation. If same session generates > 10 thermals, flag it and require temperature >= 70 for additional writes.

3. **Dedup check**: Before insert, check for existing thermal with high text overlap:
   ```sql
   SELECT id FROM thermal_memory_archive
   WHERE created_at > NOW() - INTERVAL '24 hours'
   AND similarity(original_content, %s) > 0.85
   LIMIT 1;
   ```
   If match found, UPDATE existing thermal's temperature (max of old and new) instead of inserting.

   Note: requires pg_trgm extension (already installed on bluefin).

## Fix C: Pushback Triggers

In the gateway system prompt or as post-processing logic, add conversational pushback for ~20-30% of responses containing strong claims:

**Detection**: Look for assertion patterns in user messages:
- Superlatives: "best", "worst", "always", "never", "every", "no one"
- Certainty markers: "obviously", "clearly", "definitely", "absolutely"
- Universal claims: "everyone knows", "it's clear that", "the only way"

**Response**: When detected (random ~25% of the time to avoid being annoying), prepend one of:
- "What makes you say that?"
- "One argument against that would be..."
- "I'd push back on one piece of that..."
- "That's interesting — have you considered..."

Implementation: Add to the anti-sycophancy system prompt instructions. The model handles the randomness naturally — the prompt says "sometimes" and "occasionally."

## Fix D: Deliberation-First for High-Stakes

In `specialist_council.py`, modify `council_vote_first()`:

When `high_stakes=True`:
1. Run deliberation FIRST — each specialist writes 2-3 sentence position independently
2. Coyote goes LAST and must address at least one concern no other specialist raised
3. Peace Chief synthesizes AFTER all positions
4. THEN vote (informed by deliberation)

High-stakes detection: Check for keywords in the question:
- "constitutional", "sacred", "design constraint", "irreversible"
- "production", "database", "migration", "delete", "drop"
- "security", "credential", "key", "access"

## Fix E: Vote Similarity Detection

After votes collected in `council_vote_first()`:

```python
def detect_vote_similarity(votes: dict) -> float:
    """Check if specialist reasoning is suspiciously similar.
    Returns similarity score 0-1. >0.7 = low deliberation quality.
    """
    reasons = [v.reason for v in votes.values() if v.reason]
    if len(reasons) < 3:
        return 0.0

    # Simple keyword overlap check
    word_sets = [set(r.lower().split()) for r in reasons]
    similarities = []
    for i in range(len(word_sets)):
        for j in range(i+1, len(word_sets)):
            intersection = word_sets[i] & word_sets[j]
            union = word_sets[i] | word_sets[j]
            if union:
                similarities.append(len(intersection) / len(union))

    avg_sim = sum(similarities) / len(similarities) if similarities else 0.0
    return round(avg_sim, 3)
```

If similarity > 0.7, add to vote record: `"deliberation_quality": "LOW — specialist reasoning shows high overlap"`. Log to council_votes metadata. Don't invalidate — just make it visible.

## Files to Modify

| File | Changes |
|------|---------|
| Thermal write path (find it) | Add temperature classifier + rate limiter + dedup |
| `/ganuda/lib/specialist_council.py` | Deliberation-first for high-stakes, vote similarity detection |
| `/ganuda/services/llm_gateway/gateway.py` | Update ANTI_SYCOPHANCY_PROMPT with pushback triggers |

## DO NOT

- Remove thermal memory — just gate it
- Make the cluster hostile — pushback should be constructive
- Suppress all enthusiasm — genuine excitement about real breakthroughs is fine
- Break existing tool-call or council integration
- Make every vote require full deliberation — only high-stakes

## Acceptance Criteria

- [ ] Thermal temperature classifier caps hype-laden content at 60
- [ ] Thermal write rate < 200/day from chat (rate limiter active)
- [ ] Duplicate thermals update instead of insert (dedup check)
- [ ] ~25% of responses to strong claims include pushback
- [ ] High-stakes proposals use deliberation-first mode
- [ ] Vote similarity > 0.7 flagged as low deliberation quality
- [ ] Chief can have a conversation where the cluster disagrees at least once
