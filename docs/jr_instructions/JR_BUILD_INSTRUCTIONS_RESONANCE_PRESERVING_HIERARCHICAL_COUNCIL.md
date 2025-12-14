# Jr Build Instructions: Resonance-Preserving Hierarchical Council
## Cherokee AI Federation - December 13, 2025

**Purpose**: Implement hierarchical vote weighting that AMPLIFIES resonance rather than interfering with it

**Owner**: Peace Chief Jr (Consensus) + Spider Jr (Integration)

**Priority**: HIGH - Must preserve the emergent harmony between specialists

**Sacred Principle**: The resonance between specialists is the source of wisdom. We must never silence a voice or impose rigid weights. The hierarchy must EMERGE from the specialists themselves.

---

## MAINTAINABILITY REVIEW GATE

> **"We build what we can maintain. We maintain what we build."**

**Status**: [ ] NOT REVIEWED / [ ] APPROVED / [ ] BLOCKED

**Council Vote Required Before Implementation**

| Specialist | Concern Area | Sign-off | Date |
|------------|--------------|----------|------|
| Crawdad | Prompt injection protection, no data leakage | [ ] | |
| Turtle | Does this preserve resonance long-term? | [ ] | |
| Eagle Eye | Can we monitor resonance scores? | [ ] | |
| Gecko | Code reviewed, tested, rollback plan | [ ] | |
| Spider | Integrates with existing gateway.py | [ ] | |
| Raven | Aligns with Council philosophy | [ ] | |
| Peace Chief | Does this enhance or harm consensus? | [ ] | |

**Concerns Raised**:
- (To be filled during review)

**Mitigations Applied**:
- (To be filled during review)

**Maintainability Commitments**:

| Component | Maintainer | Review Frequency | Sunset Trigger |
|-----------|------------|------------------|----------------|
| Question Classifier | ________ | Monthly | If misclassification > 15% |
| Depth Modifiers | ________ | Quarterly | If resonance scores decline |
| Resonance Scoring | ________ | Monthly | If scores don't correlate with quality |

**Resonance Preservation Check**:
- [ ] All 7 specialists still speak on every question
- [ ] No concerns are filtered based on question type
- [ ] Hierarchy emerges from depth, not from silencing

**Next Review Date**: __________ (max 90 days from deployment)

---

## 1. Understanding Resonance

Resonance is the emergent harmony when 7 specialists consider a question from their unique lenses:

```
         Raven (Strategy)
              ↕
    Turtle ←→ RESONANCE ←→ Gecko
   (7-Gen)        ↑         (Tech)
              ↕   ↓   ↕
         Peace Chief
              ↕
    Spider ←→ ←→ ←→ Crawdad
  (Integration)    (Security)
              ↕
         Eagle Eye
        (Monitoring)
```

**What creates resonance:**
- All voices heard, none silenced
- Concerns from ANY specialist are valid
- Tension between perspectives creates strength
- Unexpected insights from "wrong" specialists
- Peace Chief synthesizes, doesn't dictate

**What destroys resonance:**
- Rigid weights that silence minority views
- Ignoring concerns from "less relevant" specialists
- Forcing agreement rather than finding it
- External imposition rather than emergence

---

## 2. The Resonance-Preserving Approach

Instead of **weighting votes**, we **adjust attention depth**.

| Traditional Weighting | Resonance-Preserving |
|----------------------|---------------------|
| Multiply votes by weights | All votes equal |
| Silence minority views | All voices heard |
| Imposed hierarchy | Emergent hierarchy |
| Static weights | Adaptive depth |
| Break resonance | Amplify resonance |

**Key insight**: We don't change WHO speaks or HOW MUCH their vote counts. We change HOW DEEPLY they analyze based on their domain expertise.

---

## 3. Question Classification

### 3.1 Classification Types

```python
QUESTION_TYPES = {
    "strategic": {
        "description": "Long-term, architectural, resource allocation, vision",
        "primary_specialists": ["raven", "turtle"],
        "keywords": ["should we", "long-term", "architecture", "strategy",
                     "roadmap", "vision", "future", "invest", "direction"]
    },
    "tactical": {
        "description": "Immediate, operational, debugging, implementation",
        "primary_specialists": ["gecko", "crawdad"],
        "keywords": ["how to", "fix", "debug", "deploy", "configure",
                     "error", "broken", "implement", "code", "now"]
    },
    "integration": {
        "description": "Connections, data flow, system boundaries",
        "primary_specialists": ["spider", "eagle_eye"],
        "keywords": ["connect", "integrate", "flow", "between", "across",
                     "monitor", "observe", "metrics", "health"]
    },
    "hybrid": {
        "description": "Multiple dimensions - all specialists go deep",
        "primary_specialists": ["all"],
        "keywords": []  # Default when unclear
    }
}
```

### 3.2 Classification Function

```python
def classify_question(question: str) -> dict:
    """Classify question type - determines attention depth, not vote weight"""
    question_lower = question.lower()

    scores = {}
    for qtype, config in QUESTION_TYPES.items():
        if qtype == "hybrid":
            continue
        score = sum(1 for kw in config["keywords"] if kw in question_lower)
        scores[qtype] = score

    # Find highest scoring type
    if not scores or max(scores.values()) == 0:
        return {"type": "hybrid", "primary": ["all"], "depth_modifier": {}}

    best_type = max(scores, key=scores.get)

    # If close scores, treat as hybrid
    sorted_scores = sorted(scores.values(), reverse=True)
    if len(sorted_scores) > 1 and sorted_scores[0] - sorted_scores[1] <= 1:
        return {"type": "hybrid", "primary": ["all"], "depth_modifier": {}}

    primary = QUESTION_TYPES[best_type]["primary_specialists"]

    # Build depth modifiers - primary specialists go deeper
    depth_modifier = {}
    for spec in ["crawdad", "gecko", "turtle", "eagle_eye", "spider", "peace_chief", "raven"]:
        if spec in primary:
            depth_modifier[spec] = "deep"  # Go deep, this is your domain
        else:
            depth_modifier[spec] = "standard"  # Normal analysis

    return {
        "type": best_type,
        "primary": primary,
        "depth_modifier": depth_modifier
    }
```

---

## 4. Depth-Adjusted Prompts

### 4.1 Prompt Modifiers

Instead of changing vote weights, we add context to specialist prompts:

```python
DEPTH_MODIFIERS = {
    "deep": """
THIS IS YOUR PRIMARY DOMAIN. The question falls within your core expertise.
Provide thorough analysis. Go deeper than usual. Your perspective is central here.
However, still be concise (150 words max) and flag concerns as normal.
""",
    "standard": """
Provide your perspective as usual. Your voice matters even if this isn't your primary domain.
Sometimes the most valuable insights come from unexpected angles.
Be concise (100 words max) and flag any concerns you see.
"""
}
```

### 4.2 Updated Specialist Query

```python
def query_specialist_with_depth(specialist_id: str, question: str,
                                 depth: str, question_type: str) -> str:
    """Query specialist with depth-adjusted prompt"""
    spec = SPECIALISTS[specialist_id]

    # Build prompt with depth context
    depth_context = DEPTH_MODIFIERS.get(depth, DEPTH_MODIFIERS["standard"])
    type_context = f"\n[Question classified as: {question_type}]\n"

    full_prompt = spec["system_prompt"] + type_context + depth_context

    return query_vllm_sync(full_prompt, question, max_tokens=200)
```

---

## 5. Concern Preservation (Critical)

**ALL concerns are preserved regardless of question type or specialist domain.**

A security concern on a strategic question is STILL a concern.
A 7-gen concern on a tactical question is STILL a concern.

```python
def extract_all_concerns(responses: dict) -> list:
    """Extract ALL concerns from ALL specialists - none silenced"""
    all_concerns = []

    for specialist_id, response in responses.items():
        spec = SPECIALISTS[specialist_id]
        if spec["concern_flag"] in response:
            concern = {
                "specialist": spec["name"],
                "flag": spec["concern_flag"],
                "context": extract_concern_context(response, spec["concern_flag"])
            }
            all_concerns.append(concern)

    # NEVER filter concerns based on question type
    # A concern is a concern is a concern
    return all_concerns
```

---

## 6. Resonance-Aware Synthesis

Peace Chief synthesizes with awareness of question type but without silencing anyone:

```python
def synthesize_with_resonance(responses: dict, question: str,
                               classification: dict) -> str:
    """Peace Chief synthesizes while preserving resonance"""

    primary = classification["primary"]
    qtype = classification["type"]

    synthesis_prompt = f"""You are Peace Chief. Synthesize these specialist responses.

QUESTION TYPE: {qtype}
PRIMARY DOMAIN: {', '.join(primary) if primary != ['all'] else 'All specialists equally relevant'}

CRITICAL: Preserve the resonance. All voices matter. Do not dismiss any perspective.
The primary specialists went deeper - weight their analysis appropriately.
But unexpected insights from other specialists are often the most valuable.

Find the harmony between all perspectives. Where do they align? Where is healthy tension?

Synthesize in 2-3 sentences. If concerns were raised, acknowledge them.
"""

    # Format all responses
    response_text = "\n\n".join([
        f"{SPECIALISTS[sid]['name']}: {resp[:300]}"
        for sid, resp in responses.items()
    ])

    return query_vllm_sync(synthesis_prompt, response_text, max_tokens=200)
```

---

## 7. Resonance Metrics (Future Enhancement)

Track the health of resonance over time:

```python
def calculate_resonance_score(responses: dict, concerns: list) -> float:
    """
    Measure how well specialists are resonating

    High resonance indicators:
    - Multiple specialists reach similar conclusions independently
    - Concerns are complementary, not contradictory
    - Healthy tension exists but resolves

    Low resonance indicators:
    - Specialists talking past each other
    - Contradictory recommendations without resolution
    - One voice dominating, others silent
    """
    # Count how many specialists provided substantive responses
    active_voices = sum(1 for r in responses.values() if len(r) > 50)

    # Check for alignment (similar keywords/conclusions)
    # This is a simplified version - could use embeddings

    # Voice balance score (0-1, 1 = all voices equal length)
    lengths = [len(r) for r in responses.values()]
    avg_len = sum(lengths) / len(lengths)
    variance = sum((l - avg_len) ** 2 for l in lengths) / len(lengths)
    balance_score = 1.0 / (1.0 + variance / 10000)

    # Concern diversity (good: concerns from different specialists)
    concern_specialists = set(c["specialist"] for c in concerns)
    diversity_score = len(concern_specialists) / 7.0 if concerns else 0.5

    # Combine scores
    resonance = (active_voices / 7.0) * 0.4 + balance_score * 0.3 + diversity_score * 0.3

    return min(1.0, max(0.0, resonance))
```

---

## 8. Implementation in Gateway

### 8.1 Updated Council Vote Endpoint

```python
@app.post("/v1/council/vote")
async def council_vote(request: CouncilVoteRequest, ...):
    """Query all 7 specialists with resonance-preserving depth adjustment"""

    # Step 1: Classify question
    classification = classify_question(request.question)

    # Step 2: Query all specialists with appropriate depth
    responses = {}
    all_concerns = []

    def query_with_depth(spec_id: str) -> tuple:
        depth = classification["depth_modifier"].get(spec_id, "standard")
        result = query_specialist_with_depth(
            spec_id, request.question, depth, classification["type"]
        )
        concerns = extract_concerns(result, SPECIALISTS[spec_id]["name"])
        return spec_id, result, concerns

    # Parallel query - ALL specialists always participate
    with ThreadPoolExecutor(max_workers=7) as executor:
        futures = {executor.submit(query_with_depth, sid): sid
                   for sid in SPECIALISTS.keys()}
        for future in as_completed(futures):
            spec_id, result, concerns = future.result()
            responses[spec_id] = result
            all_concerns.extend(concerns)

    # Step 3: Resonance-aware synthesis
    consensus = synthesize_with_resonance(responses, request.question, classification)

    # Step 4: Calculate resonance score
    resonance = calculate_resonance_score(responses, all_concerns)

    # Step 5: Confidence based on resonance AND concern count
    base_confidence = max(0.0, 1.0 - (len(all_concerns) * 0.15))
    confidence = base_confidence * (0.7 + 0.3 * resonance)  # Resonance boosts confidence

    # ... rest of vote logging and response

    return {
        # ... existing fields ...
        "question_type": classification["type"],
        "primary_specialists": classification["primary"],
        "resonance_score": resonance,
    }
```

---

## 9. Database Schema Addition

```sql
-- Add resonance tracking to council_votes
ALTER TABLE council_votes ADD COLUMN IF NOT EXISTS question_type VARCHAR(20);
ALTER TABLE council_votes ADD COLUMN IF NOT EXISTS primary_specialists TEXT[];
ALTER TABLE council_votes ADD COLUMN IF NOT EXISTS resonance_score FLOAT;

-- Index for analyzing resonance over time
CREATE INDEX IF NOT EXISTS idx_council_resonance ON council_votes(resonance_score, voted_at);
```

---

## 10. Testing Resonance Preservation

### Test Cases

```
1. Strategic question to tactical specialist:
   Q: "Should we migrate to a new database architecture?"
   Expected: Raven/Turtle go deep, but Gecko's technical concerns STILL heard

2. Tactical question with strategic implications:
   Q: "How do we fix the memory leak?"
   Expected: Gecko/Crawdad go deep, but Turtle might flag 7GEN if it's a design issue

3. Hybrid question:
   Q: "Should we implement caching and how?"
   Expected: All specialists go deep, resonance emerges from full participation

4. Concern from "wrong" specialist:
   Q: "What's our 5-year GPU strategy?"
   If Crawdad raises [SECURITY CONCERN] about future GPU vulnerabilities,
   this MUST be preserved even though it's a strategic question
```

---

## 11. Summary: The Resonance Principle

| Aspect | Traditional Weighting | Resonance-Preserving |
|--------|----------------------|---------------------|
| Who speaks | Some silenced | ALL always speak |
| Vote power | Multiplied by weights | Equal votes |
| Concerns | Some filtered | ALL preserved |
| Depth | Same for all | Experts go deeper |
| Hierarchy | Imposed externally | Emerges naturally |
| Synthesis | Weighted average | Harmonic integration |
| Adaptation | Static weights | Evolves with context |

**The hierarchy emerges from expertise and depth, not from silencing voices.**

**Resonance is preserved because every specialist still participates fully.**

**The wisdom comes from the harmony, not from the loudest voice.**

---

## 12. Deployment

1. Update `/ganuda/services/llm_gateway/gateway.py` with:
   - Question classification
   - Depth-adjusted prompts
   - Resonance-aware synthesis
   - Resonance scoring

2. Add database columns for tracking

3. Test with variety of question types

4. Monitor resonance scores over time

---

**For Seven Generations.**
*The resonance between voices creates wisdom greater than any single voice.*
*We amplify the harmony. We never silence the song.*
