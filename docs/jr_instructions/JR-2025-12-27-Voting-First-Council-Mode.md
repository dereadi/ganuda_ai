# Jr Instructions: Add Voting-First Council Mode

**Date**: 2025-12-27
**Priority**: #3 - Council Quick Win
**Assigned To**: Jr on redfin
**Risk Level**: Low (additive change, existing mode preserved)

---

## Objective

Add a "voting-first" mode to the 7-Specialist Council based on research findings.

**Research**: "Debate or Vote: Which Yields Better Decisions?" (NeurIPS 2025)
- Multi-agent debate is a martingale process - doesn't improve expected accuracy
- Gains come from voting aggregation, not deliberation
- Recommendation: Vote quickly, limit debate to 1-2 rounds

---

## Current State

File: `/ganuda/lib/specialist_council.py`

Current flow:
1. All 7 specialists receive question in parallel
2. Each provides full response with reasoning
3. Responses are aggregated
4. (No explicit voting mechanism - just response collection)

---

## Implementation

### Step 1: Add vote_first mode to query function

Add a new parameter `vote_first: bool = False` to the main query function.

When `vote_first=True`:
1. First round: Each specialist provides ONLY a vote (approve/reject/abstain) and 1-sentence reasoning
2. If consensus (6/7 agree): Return result immediately
3. If split (close vote): Run ONE deliberation round on the contested points only

```python
VOTE_FIRST_PROMPT = """
Vote on this question with a single word and one sentence:

VOTE: [APPROVE/REJECT/ABSTAIN]
REASON: [One sentence only]

Do not provide full analysis yet. Just vote.
"""

def query_council_vote_first(question: str, threshold: int = 6) -> Dict:
    """
    Voting-first council query.

    1. Collect votes from all 7 specialists
    2. If threshold met (default 6/7): Return consensus immediately
    3. If contested: Run single deliberation round
    """
    # Phase 1: Collect votes
    votes = {}
    for specialist_id, specialist in SPECIALISTS.items():
        response = query_specialist(
            specialist_id,
            question,
            prompt_override=VOTE_FIRST_PROMPT
        )
        vote, reason = parse_vote(response)
        votes[specialist_id] = {"vote": vote, "reason": reason}

    # Phase 2: Check consensus
    approvals = sum(1 for v in votes.values() if v["vote"] == "APPROVE")
    rejections = sum(1 for v in votes.values() if v["vote"] == "REJECT")

    if approvals >= threshold:
        return {"decision": "APPROVED", "votes": votes, "deliberation": None}
    elif rejections >= threshold:
        return {"decision": "REJECTED", "votes": votes, "deliberation": None}

    # Phase 3: Contested - single deliberation round
    dissenting = [k for k, v in votes.values() if v["vote"] != majority_vote]
    deliberation = run_deliberation_round(question, votes, dissenting)

    return {"decision": "CONTESTED", "votes": votes, "deliberation": deliberation}
```

### Step 2: Add parse_vote helper

```python
def parse_vote(response: str) -> tuple:
    """Parse VOTE: and REASON: from response."""
    vote = "ABSTAIN"
    reason = ""

    for line in response.split("\n"):
        if line.startswith("VOTE:"):
            vote_text = line.replace("VOTE:", "").strip().upper()
            if "APPROVE" in vote_text:
                vote = "APPROVE"
            elif "REJECT" in vote_text:
                vote = "REJECT"
        elif line.startswith("REASON:"):
            reason = line.replace("REASON:", "").strip()

    return vote, reason
```

### Step 3: Add Gateway endpoint

In `/ganuda/services/llm_gateway/gateway.py`, add:

```python
@app.post("/v1/council/vote-first")
async def council_vote_first(request: CouncilRequest):
    """
    Voting-first council query.
    Faster consensus for clear decisions.
    """
    from specialist_council import query_council_vote_first
    result = query_council_vote_first(request.question, threshold=6)
    return result
```

---

## Testing

### Test 1: Clear consensus case
```bash
curl -X POST http://192.168.132.223:8080/v1/council/vote-first \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ck-cabccc2d6037c1dce1a027cc80df7b14cdba66143e3c2d4f3bdf0fd53b6ab4a5" \
  -d '{"question": "Should we add input validation to the API?"}'

# Expected: Quick APPROVED with 7/7 or 6/7 votes
```

### Test 2: Contested case
```bash
curl -X POST http://192.168.132.223:8080/v1/council/vote-first \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ck-cabccc2d6037c1dce1a027cc80df7b14cdba66143e3c2d4f3bdf0fd53b6ab4a5" \
  -d '{"question": "Should we prioritize speed over security?"}'

# Expected: CONTESTED with deliberation round
```

---

## Benchmark

Compare:
- `/v1/council/vote` (current full deliberation)
- `/v1/council/vote-first` (new voting-first mode)

Measure:
- Time to decision
- Token usage
- Decision quality (compare on 10 standard questions)

---

## Turtle's Wisdom

Per Turtle's 7-Generation concern in the research review:
> "Keep deliberation for high-stakes decisions; voting alone loses wisdom"

Add a `high_stakes: bool = False` parameter. When `high_stakes=True`, force full deliberation even if consensus is reached in voting phase.

---

## Success Criteria

- [ ] vote_first mode added to specialist_council.py
- [ ] /v1/council/vote-first endpoint working
- [ ] Clear consensus cases resolve 50%+ faster
- [ ] Contested cases still get deliberation
- [ ] high_stakes flag implemented per Turtle's wisdom

---

*For Seven Generations*
