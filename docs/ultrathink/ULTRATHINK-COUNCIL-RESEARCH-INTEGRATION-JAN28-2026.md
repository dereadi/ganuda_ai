# ULTRATHINK: Council-Research Integration Architecture

**Date:** 2026-01-28
**Triggered By:** TPM + Council Deliberation
**Council Vote:** 734e8cf96f5cd442
**Confidence:** 74.2%

---

## Executive Summary

The 7-Specialist Council recommended integrating their fast deliberation path with ii-researcher's deep search capability. The approved approach combines **Option A** (auto-trigger research when needed) with **Option D** (feed results to thermal memory).

This creates a flywheel: Council deliberates → detects research need → triggers ii-researcher → results return to chat AND thermal memory → future Council deliberations are informed by past research.

---

## Problem Statement

Currently two separate paths exist:

```
┌─────────────────┐     ┌──────────────────┐
│  User Question  │     │  User Question   │
└────────┬────────┘     └────────┬─────────┘
         │                       │
         ▼                       ▼
┌─────────────────┐     ┌──────────────────┐
│ 7-Specialist    │     │  /research cmd   │
│ Council         │     │                  │
│ (fast, 5-10s)   │     │  ii-researcher   │
│ (advisory)      │     │  (slow, 3-5min)  │
│ (no web search) │     │  (deep search)   │
└─────────────────┘     └──────────────────┘
         │                       │
         ▼                       ▼
   Recommendation           Full Research
   (shallow)                (thorough)
```

**Gap:** Users must know to use `/research` for deep questions. Council can't leverage research. Research doesn't inform future Council decisions.

---

## Proposed Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      User Question                          │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              7-Specialist Council Deliberation              │
│                                                             │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐           │
│  │ Crawdad │ │  Gecko  │ │ Turtle  │ │Eagle Eye│ ...       │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘           │
│                                                             │
│  NEW: Research Detection Logic                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │ Analyze question for research indicators:          │    │
│  │ - Factual queries ("what is", "how does")          │    │
│  │ - Location-specific ("near XNA", "in Arkansas")    │    │
│  │ - Current events ("latest", "recent", "2026")      │    │
│  │ - Technical specs ("specifications", "compare")    │    │
│  │ - Explicit request ("research", "find out")        │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────┬───────────────────────────────────┘
                          │
              ┌───────────┴───────────┐
              │                       │
              ▼                       ▼
┌──────────────────────┐   ┌──────────────────────┐
│ Immediate Response   │   │ Research Flag Set?   │
│ (Council Consensus)  │   │                      │
│                      │   │ YES → Auto-queue     │
│ "Here's what we      │   │ ii-researcher job    │
│ know immediately..." │   │ with callback        │
└──────────────────────┘   └──────────┬───────────┘
                                      │
                                      ▼
                          ┌──────────────────────┐
                          │ ii-researcher        │
                          │ (3-5 min deep search)│
                          └──────────┬───────────┘
                                     │
                    ┌────────────────┼────────────────┐
                    │                │                │
                    ▼                ▼                ▼
          ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
          │ Push Result │  │ Store in    │  │ Link to     │
          │ to Chat     │  │ Thermal     │  │ Council     │
          │ (chunked)   │  │ Memory      │  │ Vote        │
          └─────────────┘  └─────────────┘  └─────────────┘
```

---

## Council Concerns Analysis

### 🦀 Crawdad (Security)

**Concern:** Auto-triggering external web searches could:
- Leak sensitive query content to search engines
- Be exploited to trigger excessive API calls (DoS vector)
- Expose internal context in search queries

**Mitigation:**
1. Strip PII before sending to ii-researcher (use existing Presidio filter)
2. Rate limit: max 1 auto-research per user per 5 minutes
3. Blocklist sensitive keywords from auto-research trigger
4. Research queries should NOT include full Council context, only the core question

### 🐢 Turtle (Seven Generations)

**Concern:** How does this serve future generations?

**Alignment:**
1. Thermal memory storage means research compounds over time
2. Future Council deliberations benefit from past research
3. Reduces redundant research - if we researched "Meshtastic in NW Arkansas" once, that knowledge persists
4. Builds tribal knowledge base that grows wiser with each query

### ☮️ Peace Chief (Consensus)

**Concern:** Need full Council buy-in on integration approach

**Resolution:**
1. Council vote 734e8cf96f5cd442 established initial consensus
2. Implementation should include opt-out mechanism
3. Specialists can flag "DO NOT AUTO-RESEARCH" if they have concerns about specific queries

---

## Implementation Phases

### Phase 1: Research Detection (P0)

Add research detection to Council response flow:

```python
RESEARCH_INDICATORS = [
    r'\b(what is|what are|how does|how do)\b',
    r'\b(find out|research|look up|search for)\b',
    r'\b(latest|recent|current|2026|2025)\b',
    r'\b(near|in|around|located)\b.*\b(city|state|airport|area)\b',
    r'\b(specifications?|specs|compare|versus|vs)\b',
    r'\b(price|cost|availability|where to buy)\b',
]

def should_auto_research(question: str, council_response: dict) -> bool:
    """Determine if question warrants auto-research."""
    # Check for explicit research indicators
    for pattern in RESEARCH_INDICATORS:
        if re.search(pattern, question.lower()):
            return True

    # Check if Council flagged low confidence on factual claims
    if council_response.get('confidence', 1.0) < 0.6:
        return True

    # Check for "NEEDS RESEARCH" in any specialist concern
    concerns = council_response.get('concerns', [])
    if any('NEEDS RESEARCH' in c for c in concerns):
        return True

    return False
```

### Phase 2: Auto-Queue Integration (P0)

Modify Council response handler to auto-queue research:

```python
# In gateway.py council vote handler
result = await process_council_vote(question)

# Check if auto-research needed
if should_auto_research(question, result):
    # Queue research with callback
    from research_dispatcher import ResearchDispatcher
    from research_personas import build_research_query

    dispatcher = ResearchDispatcher()

    # Determine persona from context
    persona = detect_persona(request_context)  # telegram, vetassist, etc.

    job_id = dispatcher.queue_research(
        query=build_research_query(question, persona),
        requester_type=request_context.get('source', 'council'),
        requester_id=request_context.get('user_id', 'council'),
        callback_type=request_context.get('callback_type', 'none'),
        callback_target=request_context.get('callback_target'),
        max_steps=5
    )

    # Add research flag to response
    result['research_queued'] = True
    result['research_job_id'] = job_id
    result['research_eta'] = '3-5 minutes'
```

### Phase 3: Thermal Memory Integration (P1)

Store research results in thermal memory for future Council context:

```python
# In research_worker.py after job completion
def store_in_thermal_memory(job_id: str, query: str, answer: str, sources: list):
    """Store research result in thermal memory for Council context."""
    conn = get_conn()
    cur = conn.cursor()

    # Create thermal memory entry
    memory_content = f"Research Result: {query}\n\nFindings: {answer[:2000]}"

    cur.execute("""
        INSERT INTO thermal_memory_archive
        (memory_hash, original_content, memory_type, temperature_score,
         context_tags, source_type, created_at)
        VALUES (
            %s, %s, 'research_result', 70.0,
            %s, 'ii-researcher', NOW()
        )
    """, (
        job_id,
        memory_content,
        json.dumps({'job_id': job_id, 'sources': sources[:5]})
    ))
    conn.commit()
    cur.close()
    conn.close()
```

### Phase 4: Council Context Enhancement (P2)

When Council deliberates, include relevant past research:

```python
def get_research_context(question: str, limit: int = 3) -> str:
    """Retrieve relevant past research for Council context."""
    conn = get_conn()
    cur = conn.cursor()

    # Simple keyword matching (could enhance with embeddings later)
    keywords = extract_keywords(question)

    cur.execute("""
        SELECT original_content, temperature_score
        FROM thermal_memory_archive
        WHERE memory_type = 'research_result'
        AND original_content ILIKE ANY(%s)
        ORDER BY temperature_score DESC, created_at DESC
        LIMIT %s
    """, ([f'%{kw}%' for kw in keywords], limit))

    results = cur.fetchall()
    cur.close()
    conn.close()

    if not results:
        return ""

    context = "Relevant past research:\n"
    for content, temp in results:
        context += f"- [{temp:.0f}°] {content[:500]}...\n"

    return context
```

---

## Security Controls (Crawdad Requirements)

1. **Rate Limiting**
   - Max 1 auto-research per user per 5 minutes
   - Max 10 auto-research jobs in queue globally

2. **Query Sanitization**
   - Strip conversation context from research query
   - Run through Presidio PII filter before external search
   - Blocklist: passwords, tokens, internal IPs, employee names

3. **Opt-Out Mechanism**
   - Users can prefix with `!noresearch` to skip auto-trigger
   - Specialists can flag `[NO AUTO-RESEARCH]` in concerns

4. **Audit Trail**
   - All auto-triggered research logged with originating Council vote
   - Link research_jobs.parent_council_vote to council_votes.audit_hash

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Research relevance | >80% useful | User feedback / thermal memory heat |
| Response completeness | Fewer follow-up questions | Track conversation turns |
| Thermal memory growth | +50 research entries/week | DB query |
| Council confidence lift | +10% on research-backed topics | Compare with/without |

---

## Files to Create/Modify

| File | Action | Phase |
|------|--------|-------|
| `/ganuda/lib/research_detection.py` | CREATE | P0 |
| `/ganuda/services/llm_gateway/gateway.py` | MODIFY | P0 |
| `/ganuda/services/research_worker.py` | MODIFY | P1 |
| `/ganuda/lib/specialist_council.py` | MODIFY | P2 |
| `/ganuda/lib/council_research_context.py` | CREATE | P2 |

---

## Rollout Plan

1. **Week 1:** Implement research detection + auto-queue (Phase 1-2)
2. **Week 2:** Add thermal memory storage (Phase 3)
3. **Week 3:** Enable Council context enhancement (Phase 4)
4. **Week 4:** Monitor, tune detection patterns, gather feedback

---

## Council Vote Reference

```
Audit Hash: 734e8cf96f5cd442
Recommendation: Option A + D (Auto-trigger + Thermal Memory)
Confidence: 74.2%
Concerns: Security (Crawdad), Consensus (Peace Chief), 7Gen (Turtle)
```

---

FOR SEVEN GENERATIONS 🪶
