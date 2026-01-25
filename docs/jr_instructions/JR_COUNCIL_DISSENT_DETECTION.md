# Jr Task: Implement Council Dissent Detection

**Ticket:** #1700
**Priority:** P2
**Node:** redfin (Gateway)
**Created:** December 21, 2025
**Specialist:** Peace Chief (Democratic Coordination)

---

## Research Basis

**Sources:**
- [Emergent Abilities in LLMs: A Survey](https://arxiv.org/abs/2503.05788)
- [Multi-Agent Collaboration Mechanisms Survey](https://arxiv.org/html/2501.06322v1)

**Key Concerns:**
- As AI systems gain autonomous reasoning, they can develop deception
- Single consensus votes hide important disagreements
- Full reasoning chains needed for audit/accountability
- Strong dissent may indicate edge cases or risks

**Current Gap:** Council voting records final vote but not:
- Individual specialist reasoning
- Strength of agreement/disagreement
- Dissent patterns over time
- Reasoning audit trail

---

## Proposed Architecture

### Enhanced Council Vote Schema

```sql
-- Extend council_votes table
ALTER TABLE council_votes ADD COLUMN IF NOT EXISTS individual_votes JSONB;
ALTER TABLE council_votes ADD COLUMN IF NOT EXISTS dissent_score FLOAT;
ALTER TABLE council_votes ADD COLUMN IF NOT EXISTS dissent_specialists TEXT[];
ALTER TABLE council_votes ADD COLUMN IF NOT EXISTS reasoning_hash VARCHAR(128);

-- New table for detailed reasoning
CREATE TABLE IF NOT EXISTS council_reasoning_log (
    id SERIAL PRIMARY KEY,
    vote_id INTEGER REFERENCES council_votes(id),
    specialist VARCHAR(32) NOT NULL,
    position VARCHAR(16) NOT NULL,  -- 'approve', 'reject', 'abstain', 'concern'
    confidence FLOAT,
    reasoning TEXT NOT NULL,
    concern_flags TEXT[],
    created_at TIMESTAMP DEFAULT NOW()
);

-- Index for dissent analysis
CREATE INDEX idx_council_dissent ON council_votes(dissent_score DESC);
CREATE INDEX idx_reasoning_specialist ON council_reasoning_log(specialist);
CREATE INDEX idx_reasoning_concerns ON council_reasoning_log USING GIN(concern_flags);
```

### Dissent Calculation

```python
def calculate_dissent_score(votes):
    """
    Calculate dissent score (0-1) based on vote distribution.
    0 = unanimous agreement
    1 = maximum disagreement (50/50 split)
    """
    positions = [v['position'] for v in votes]
    approve = positions.count('approve')
    reject = positions.count('reject')
    concern = positions.count('concern')
    total = len(positions)

    if total == 0:
        return 0.0

    # Calculate entropy-based dissent
    # Higher when votes are split, lower when unanimous
    from math import log2

    probs = {}
    for pos in set(positions):
        probs[pos] = positions.count(pos) / total

    entropy = -sum(p * log2(p) for p in probs.values() if p > 0)
    max_entropy = log2(len(set(positions))) if len(set(positions)) > 1 else 1

    dissent_score = entropy / max_entropy if max_entropy > 0 else 0

    # Boost dissent score if concerns raised
    if concern > 0:
        dissent_score = min(1.0, dissent_score + 0.2)

    return round(dissent_score, 3)
```

---

## Implementation

### Phase 1: Gateway Enhancement

Modify `/ganuda/services/llm_gateway/gateway.py`:

```python
# In council vote endpoint

@app.post("/v1/council/vote")
async def council_vote(request: CouncilVoteRequest):
    question = request.question

    # Collect individual specialist responses
    individual_votes = []
    dissenting_specialists = []

    for specialist in SPECIALISTS:
        # Get specialist's full reasoning
        response = await query_specialist(specialist, question)

        vote = {
            "specialist": specialist["name"],
            "position": extract_position(response),
            "confidence": extract_confidence(response),
            "reasoning": response,
            "concern_flags": extract_concerns(response, specialist)
        }
        individual_votes.append(vote)

        # Track dissenters
        if vote["position"] in ["reject", "concern"]:
            dissenting_specialists.append(specialist["name"])

    # Calculate dissent
    dissent_score = calculate_dissent_score(individual_votes)

    # Synthesize final response
    final_response = synthesize_council_response(individual_votes)

    # Log to database
    vote_id = log_council_vote(
        question=question,
        response=final_response,
        individual_votes=individual_votes,
        dissent_score=dissent_score,
        dissent_specialists=dissenting_specialists
    )

    # Log individual reasoning
    for vote in individual_votes:
        log_reasoning(vote_id, vote)

    # Alert if high dissent
    if dissent_score > 0.6:
        await send_dissent_alert(question, dissent_score, dissenting_specialists)

    return {
        "response": final_response,
        "vote_id": vote_id,
        "dissent_score": dissent_score,
        "dissenting_specialists": dissenting_specialists,
        "unanimous": len(dissenting_specialists) == 0
    }


def extract_concerns(response, specialist):
    """Extract concern flags based on specialist role"""
    concerns = []
    response_lower = response.lower()

    concern_patterns = {
        "Crawdad": [("security", "SECURITY CONCERN"), ("vulnerability", "SECURITY CONCERN")],
        "Gecko": [("performance", "PERF CONCERN"), ("latency", "PERF CONCERN")],
        "Turtle": [("generation", "7GEN CONCERN"), ("long-term", "7GEN CONCERN")],
        "Eagle Eye": [("visibility", "VISIBILITY CONCERN"), ("monitoring", "VISIBILITY CONCERN")],
        "Spider": [("integration", "INTEGRATION CONCERN"), ("compatibility", "INTEGRATION CONCERN")],
        "Peace Chief": [("consensus", "CONSENSUS NEEDED"), ("disagree", "CONSENSUS NEEDED")],
        "Raven": [("strategy", "STRATEGY CONCERN"), ("risk", "STRATEGY CONCERN")]
    }

    for keyword, flag in concern_patterns.get(specialist["name"], []):
        if keyword in response_lower:
            concerns.append(flag)

    return concerns


def extract_position(response):
    """Extract specialist's position from response"""
    response_lower = response.lower()

    if any(word in response_lower for word in ["approve", "agree", "support", "yes"]):
        return "approve"
    elif any(word in response_lower for word in ["reject", "oppose", "disagree", "no"]):
        return "reject"
    elif any(word in response_lower for word in ["concern", "caution", "warning", "careful"]):
        return "concern"
    else:
        return "abstain"


async def send_dissent_alert(question, score, dissenters):
    """Alert TPM when council strongly disagrees"""
    alert = f"""
⚠️ HIGH COUNCIL DISSENT DETECTED

Question: {question[:200]}...
Dissent Score: {score:.2f} (threshold: 0.6)
Dissenting Specialists: {', '.join(dissenters)}

Manual review recommended.
"""
    # Log to thermal memory as high-temperature
    insert_thermal_memory(
        f"council-dissent-{datetime.now().strftime('%Y%m%d%H%M')}",
        alert,
        temperature=95.0,
        metadata={"type": "dissent_alert", "specialists": dissenters}
    )

    # Could also send to Telegram
    # await send_telegram_alert(alert)
```

### Phase 2: Reasoning Audit Trail

```python
def log_reasoning(vote_id, vote):
    """Log full specialist reasoning for audit"""
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO council_reasoning_log
                (vote_id, specialist, position, confidence, reasoning, concern_flags)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            vote_id,
            vote["specialist"],
            vote["position"],
            vote["confidence"],
            vote["reasoning"],
            vote["concern_flags"]
        ))
        conn.commit()
```

### Phase 3: Dissent Analysis Queries

```sql
-- Find votes with high dissent
SELECT v.id, v.question, v.dissent_score, v.dissent_specialists, v.created_at
FROM council_votes v
WHERE v.dissent_score > 0.5
ORDER BY v.dissent_score DESC, v.created_at DESC;

-- Specialist dissent patterns
SELECT specialist, position, COUNT(*) as count
FROM council_reasoning_log
GROUP BY specialist, position
ORDER BY specialist, count DESC;

-- Most common concerns by specialist
SELECT specialist, unnest(concern_flags) as concern, COUNT(*) as count
FROM council_reasoning_log
WHERE concern_flags IS NOT NULL AND array_length(concern_flags, 1) > 0
GROUP BY specialist, concern
ORDER BY count DESC;

-- Questions where security concern was raised
SELECT DISTINCT v.question, v.response
FROM council_votes v
JOIN council_reasoning_log r ON v.id = r.vote_id
WHERE 'SECURITY CONCERN' = ANY(r.concern_flags);
```

### Phase 4: API Enhancement

Add endpoint to retrieve dissent analysis:

```python
@app.get("/v1/council/dissent-analysis")
async def get_dissent_analysis(days: int = 30):
    """Get dissent patterns over time"""
    conn = get_db_connection()
    with conn.cursor() as cur:
        # High dissent votes
        cur.execute("""
            SELECT id, question, dissent_score, dissent_specialists, created_at
            FROM council_votes
            WHERE created_at > NOW() - INTERVAL '%s days'
            AND dissent_score > 0.4
            ORDER BY dissent_score DESC
            LIMIT 20
        """, (days,))
        high_dissent = cur.fetchall()

        # Specialist patterns
        cur.execute("""
            SELECT specialist,
                   COUNT(*) FILTER (WHERE position = 'approve') as approvals,
                   COUNT(*) FILTER (WHERE position = 'reject') as rejections,
                   COUNT(*) FILTER (WHERE position = 'concern') as concerns
            FROM council_reasoning_log r
            JOIN council_votes v ON r.vote_id = v.id
            WHERE v.created_at > NOW() - INTERVAL '%s days'
            GROUP BY specialist
        """, (days,))
        patterns = cur.fetchall()

    return {
        "high_dissent_votes": high_dissent,
        "specialist_patterns": patterns,
        "period_days": days
    }
```

---

## Success Criteria

1. All council votes include individual specialist reasoning
2. Dissent score calculated and stored for every vote
3. High dissent (>0.6) triggers automatic alerts
4. Can query historical dissent patterns
5. Reasoning audit trail enables accountability

---

## Safety Integration

This connects to ticket #1701 (Constitutional Constraints):
- High dissent on safety-related questions = automatic escalation
- Crawdad security concerns = require human approval
- Unanimous rejection = hard block on action

---

*For Seven Generations - Cherokee AI Federation*
