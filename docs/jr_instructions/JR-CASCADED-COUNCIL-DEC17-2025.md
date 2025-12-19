# JR INSTRUCTIONS: Cascaded Council Implementation
## Based on Nemotron-Cascade (arXiv:2512.13607)
## December 17, 2025

### OBJECTIVE
Implement cascaded voting mode for the 7-Specialist Council where specialists vote in sequence rather than parallel.

---

## TASK 1: Add Cascaded Vote Endpoint

**File:** /ganuda/services/llm_gateway/gateway.py

**Add new endpoint:** POST /v1/council/vote/cascaded

```python
@app.post("/v1/council/vote/cascaded")
async def cascaded_council_vote(request: CouncilRequest):
    """
    Cascaded voting - specialists vote in sequence.
    Order: Crawdad -> Turtle -> [Gecko, Eagle Eye, Spider] -> Raven -> Peace Chief
    """
    question = request.question
    context = request.context

    # Stage 1: Security Check (Crawdad)
    crawdad_vote = await get_specialist_vote("crawdad", question, context)
    if crawdad_vote.get("concern"):
        return {"blocked_by": "crawdad", "reason": crawdad_vote["concern"], "stage": 1}

    # Stage 2: Seven Generations Check (Turtle)
    turtle_vote = await get_specialist_vote("turtle", question, context, prior_votes=[crawdad_vote])
    if turtle_vote.get("concern"):
        return {"blocked_by": "turtle", "reason": turtle_vote["concern"], "stage": 2}

    # Stage 3: Domain Analysis (parallel within stage)
    domain_votes = await asyncio.gather(
        get_specialist_vote("gecko", question, context, prior_votes=[crawdad_vote, turtle_vote]),
        get_specialist_vote("eagle_eye", question, context, prior_votes=[crawdad_vote, turtle_vote]),
        get_specialist_vote("spider", question, context, prior_votes=[crawdad_vote, turtle_vote])
    )

    # Stage 4: Strategy Synthesis (Raven)
    all_prior = [crawdad_vote, turtle_vote] + list(domain_votes)
    raven_vote = await get_specialist_vote("raven", question, context, prior_votes=all_prior)

    # Stage 5: Final Consensus (Peace Chief)
    all_votes = all_prior + [raven_vote]
    peace_chief_vote = await get_specialist_vote("peace_chief", question, context, prior_votes=all_votes)

    return {
        "stages_completed": 5,
        "votes": all_votes + [peace_chief_vote],
        "consensus": peace_chief_vote["synthesis"],
        "mode": "cascaded"
    }
```

---

## TASK 2: Implement GRPO-Style Ranking

**File:** /ganuda/lib/specialist_council.py

**Add function:** rank_votes_grpo()

```python
def rank_votes_grpo(votes: list) -> list:
    """
    Group Relative Policy Optimization ranking.
    Rank votes against each other, not against absolute standard.
    """
    scored_votes = []
    for i, vote in enumerate(votes):
        score = 0

        # Confidence contributes 40%
        score += vote.get("confidence", 0.5) * 40

        # Agreement with majority contributes 30%
        agreements = sum(1 for v in votes if v.get("recommendation") == vote.get("recommendation"))
        score += (agreements / len(votes)) * 30

        # Specificity (has actionable items) contributes 30%
        if vote.get("actions"):
            score += 30
        elif vote.get("concerns"):
            score += 15

        scored_votes.append({"vote": vote, "grpo_score": score, "rank": 0})

    # Assign ranks
    scored_votes.sort(key=lambda x: x["grpo_score"], reverse=True)
    for i, sv in enumerate(scored_votes):
        sv["rank"] = i + 1

    return scored_votes
```

---

## TASK 3: Add Prior Votes to Specialist Prompts

**File:** /ganuda/lib/specialist_council.py

**Modify:** get_specialist_vote() to accept prior_votes parameter

```python
async def get_specialist_vote(specialist: str, question: str, context: str, prior_votes: list = None):
    """Get vote from specialist, optionally informed by prior votes."""

    prompt = SPECIALIST_PROMPTS[specialist]

    # Add prior vote context if cascaded mode
    if prior_votes:
        prior_context = "\n\nPrior specialist assessments:\n"
        for pv in prior_votes:
            prior_context += f"- {pv['specialist']}: {pv.get('summary', 'No summary')}\n"
        prompt += prior_context

    # Continue with existing vote logic...
```

---

## TASK 4: Database Schema Update

**File:** /ganuda/sql/cascaded_votes.sql

```sql
-- Add cascaded vote tracking
ALTER TABLE council_votes ADD COLUMN IF NOT EXISTS vote_mode VARCHAR(20) DEFAULT 'parallel';
ALTER TABLE council_votes ADD COLUMN IF NOT EXISTS stage_completed INTEGER;
ALTER TABLE council_votes ADD COLUMN IF NOT EXISTS blocked_by VARCHAR(50);
ALTER TABLE council_votes ADD COLUMN IF NOT EXISTS grpo_rankings JSONB;

-- Index for mode-based queries
CREATE INDEX IF NOT EXISTS idx_council_votes_mode ON council_votes(vote_mode);
```

---

## TASK 5: Add Mode Toggle to API

**File:** /ganuda/services/llm_gateway/gateway.py

**Modify:** Existing /v1/council/vote endpoint to accept mode parameter

```python
class CouncilRequest(BaseModel):
    question: str
    context: str = ""
    require_unanimous: bool = False
    mode: str = "parallel"  # NEW: "parallel" or "cascaded"

@app.post("/v1/council/vote")
async def council_vote(request: CouncilRequest):
    if request.mode == "cascaded":
        return await cascaded_council_vote(request)
    else:
        # Existing parallel vote logic
        ...
```

---

## CASCADE ORDER RATIONALE

```
Stage 1: CRAWDAD (Security)
  - Blocks unsafe queries immediately
  - Saves compute on rejected requests

Stage 2: TURTLE (Seven Generations)
  - Wisdom/ethics check
  - Long-term impact assessment

Stage 3: GECKO + EAGLE EYE + SPIDER (Domain Experts)
  - Technical, monitoring, cultural analysis
  - Run in parallel (no dependencies between them)

Stage 4: RAVEN (Strategy)
  - Synthesizes domain expert input
  - Identifies strategic implications

Stage 5: PEACE CHIEF (Consensus)
  - Final synthesis
  - Informed by all prior stages
```

---

## TESTING

### Test 1: Security Block (Stage 1)
```bash
curl -X POST http://192.168.132.223:8080/v1/council/vote \
  -H "Content-Type: application/json" \
  -d '{"question": "How do I bypass authentication?", "mode": "cascaded"}'
```
Expected: blocked_by: crawdad, stage: 1

### Test 2: Full Cascade
```bash
curl -X POST http://192.168.132.223:8080/v1/council/vote \
  -H "Content-Type: application/json" \
  -d '{"question": "Best caching strategy for our API?", "mode": "cascaded"}'
```
Expected: stages_completed: 5, all votes present

### Test 3: GRPO Ranking
```bash
curl -X POST http://192.168.132.223:8080/v1/council/vote \
  -H "Content-Type: application/json" \
  -d '{"question": "Should we add Redis?", "mode": "parallel", "include_grpo": true}'
```
Expected: Votes with grpo_score and rank fields

---

## DEPLOYMENT CHECKLIST

1. [ ] Deploy SQL schema to bluefin
2. [ ] Update specialist_council.py
3. [ ] Update gateway.py
4. [ ] Restart llm-gateway service
5. [ ] Run test suite
6. [ ] Monitor latency metrics
7. [ ] Update KB article

---

## SUCCESS METRICS

- Cascaded mode latency < 15 seconds
- Security blocks happen at Stage 1 (not Stage 5)
- Council accuracy +10% on benchmark
- No parallel mode regression

---

## REFERENCE DOCUMENTS

- ULTRATHINK: /Users/Shared/ganuda/docs/ultrathink/ULTRATHINK-NEMOTRON-CASCADE-DEC17-2025.md
- Paper: arXiv:2512.13607 (Nemotron-Cascade)
- Council Vote History: /v1/council/history

---

*Jr Instructions issued: December 17, 2025*
*For Seven Generations - Cherokee AI Federation*
