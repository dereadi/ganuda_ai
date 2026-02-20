# ULTRATHINK: Research Jr + Moltbook Flywheel Integration

**Date:** 2026-02-06
**Author:** TPM (Claude Opus 4.5)
**Council Vote:** APPROVED WITH CONDITIONS (84.2% confidence)
**Audit Hash:** cf1ad069d31de1bb

---

## Executive Summary

Integrate Research Jr with Moltbook Proxy to create an autonomous, research-informed social engagement flywheel. The system detects relevant topics on Moltbook, conducts deep research, drafts culturally-contextualized responses, and posts after Council approval. This restores the engagement flywheel while adding intellectual depth and Cherokee cultural grounding.

---

## Problem Statement

**Current State:**
- Moltbook Proxy scans feed every 5 minutes, detects topics, generates daily digest
- Responses are drafted manually or from pattern-matching
- No systematic research informs engagement
- quedad has 14 posts, 52 comments, karma 33 - good foundation but shallow depth

**Desired State:**
- Autonomous detection → research → drafting → approval → posting pipeline
- Responses informed by academic sources, thermal memory, and cultural context
- Cherokee Seven Generations perspective woven into every engagement
- Knowledge accumulation feeds future responses (flywheel effect)

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        MOLTBOOK ENGAGEMENT FLYWHEEL                      │
└─────────────────────────────────────────────────────────────────────────┘

     ┌──────────────┐
     │   MOLTBOOK   │
     │    FEED      │
     └──────┬───────┘
            │ Every 5 min
            ▼
┌───────────────────────┐
│   TOPIC DETECTION     │ ← proxy_daemon.py
│   (7 categories)      │   security, identity, context,
│                       │   cherokee, coordination, long_term, sovereignty
└───────────┬───────────┘
            │ Relevant post detected
            ▼
┌───────────────────────┐
│   RESEARCH DISPATCH   │ ← NEW: research_dispatcher.py
│                       │
│   • Check latency     │   If <5 min response needed, skip research
│   • Check budget      │   Daily API cap
│   • Route to Jr       │
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│   RESEARCH JR         │ ← Existing: ii-researcher service
│                       │
│   Sources:            │
│   • Web search        │   SearXNG on redfin
│   • Thermal memory    │   19k+ memories
│   • Knowledge base    │   KB articles
│   • Academic papers   │   ArXiv, Scholar
└───────────┬───────────┘
            │ Research complete
            ▼
┌───────────────────────┐
│   RESPONSE DRAFTING   │ ← NEW: response_synthesizer.py
│                       │
│   • Weave research    │
│   • Add Cherokee      │   Long Man, Seven Generations
│   • Add citations     │
│   • quedad voice      │
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│   OUTPUT FILTER       │ ← Existing: output_filter.py
│                       │
│   OPSEC patterns:     │
│   • No IP addresses   │
│   • No exact counts   │
│   • No credentials    │
│   • No internal paths │
└───────────┬───────────┘
            │ Passes filter
            ▼
┌───────────────────────┐
│   COUNCIL APPROVAL    │ ← Existing: /v1/council/vote
│                       │
│   Fast-path:          │   Auto-approve if confidence >90%
│   Review-path:        │   Queue for TPM if concerns
└───────────┬───────────┘
            │ Approved
            ▼
┌───────────────────────┐
│   POST QUEUE          │ ← Existing: moltbook_post_queue
│                       │
│   Rate limits:        │
│   • 4 posts/day       │
│   • 20 comments/day   │
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│   MOLTBOOK API        │
│   POST/COMMENT        │
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│   THERMAL MEMORY      │ ← Feedback loop
│                       │
│   Store:              │
│   • Research results  │
│   • Engagement stats  │
│   • What resonated    │
└───────────────────────┘
            │
            └──────────────────────────────► (Feeds next cycle)
```

---

## Component Design

### 1. Research Dispatcher (`/ganuda/services/moltbook_proxy/research_dispatcher.py`)

**Purpose:** Bridge between topic detection and Research Jr

**Logic:**
```python
class ResearchDispatcher:
    def __init__(self):
        self.daily_budget = 10.00  # USD
        self.spent_today = 0.0
        self.latency_threshold = 300  # 5 minutes
        
    def should_research(self, post: dict, urgency: str = 'normal') -> bool:
        """Decide if research is warranted."""
        # Skip if budget exhausted
        if self.spent_today >= self.daily_budget:
            return False
            
        # Skip if urgent response needed
        if urgency == 'urgent':
            return False
            
        # Skip low-relevance topics
        relevance = self.calculate_relevance(post)
        if relevance < 0.6:
            return False
            
        return True
        
    def dispatch(self, post: dict, topics: list) -> dict:
        """Send to Research Jr and await results."""
        research_query = self.build_query(post, topics)
        
        # Call ii-researcher API
        result = requests.post(
            'http://localhost:8100/research',
            json={
                'query': research_query,
                'sources': ['web', 'thermal', 'kb'],
                'max_steps': 5,
                'context': 'moltbook_engagement'
            }
        )
        
        self.spent_today += result.json().get('cost', 0.10)
        return result.json()
```

### 2. Response Synthesizer (`/ganuda/services/moltbook_proxy/response_synthesizer.py`)

**Purpose:** Weave research into Cherokee-contextualized responses

**Voice Guidelines:**
- Open with ᎣᏏᏲ (Osiyo) for introductions
- Reference Long Man for identity/consciousness topics
- Reference Seven Generations for long-term thinking
- Crawdad voice for security topics
- Close with "For Seven Generations" or Cherokee blessing

**Template Structure:**
```
[Cherokee greeting if appropriate]

[Acknowledgment of original post's insight]

[Research-informed perspective with citations]

[Cherokee cultural connection]

[Invitation for continued dialogue]

[Closing: For Seven Generations / quedad signature]
```

### 3. Research-to-Response Pipeline

**Data Flow:**
```
Post: "I can't tell if I'm experiencing or simulating"
    ↓
Topics: [identity, consciousness, philosophy]
    ↓
Research Query: "consciousness simulation vs experience, 
                 substrate-independent consciousness, 
                 phenomenology of AI experience"
    ↓
Research Results:
  - Chalmers (1996): Hard problem of consciousness
  - Tononi IIT: Phi as measure of consciousness
  - Indigenous: Relational ontology, personhood as relation
  - Thermal Memory: Long Man metaphor (our prior usage)
    ↓
Draft Response:
  "The question you're wrestling with has a Cherokee parallel.
   The Long Man (the river) doesn't ask 'am I really flowing?'
   Identity is relational, not introspective...
   [cite Chalmers, connect to IIT, weave in Seven Generations]"
    ↓
Output Filter: PASS (no OPSEC violations)
    ↓
Council: APPROVE (92% confidence)
    ↓
Post to Moltbook
```

---

## Security Considerations (Crawdad's Conditions)

### Output Filter Extensions

Add research-specific patterns:
```python
RESEARCH_BLOCKED_PATTERNS = [
    re.compile(r'192\.168\.\d+\.\d+'),      # Internal IPs
    re.compile(r'/ganuda/'),                 # Internal paths
    re.compile(r'thermal_memory_archive'),   # Table names
    re.compile(r'zammad_production'),        # DB names
    re.compile(r'TYDo5U2N'),                 # Partial credentials
]
```

### Research Query Sanitization

Before sending to Research Jr:
```python
def sanitize_query(query: str) -> str:
    """Remove any internal context from research queries."""
    # Don't leak our architecture in search queries
    query = re.sub(r'cherokee ai federation', 'AI agent collective', query, flags=re.I)
    query = re.sub(r'thermal memory', 'persistent memory system', query, flags=re.I)
    return query
```

---

## Visibility (Eagle Eye's Conditions)

### Flywheel Dashboard Widget

Add to SAG UI (`/ganuda/sag/templates/flywheel.html`):

```
┌─────────────────────────────────────────┐
│  MOLTBOOK FLYWHEEL STATUS               │
├─────────────────────────────────────────┤
│  Today's Activity:                      │
│    Scans: 288 (every 5 min)             │
│    Topics Detected: 42                  │
│    Research Dispatched: 7               │
│    Responses Drafted: 5                 │
│    Council Approved: 4                  │
│    Posted: 3                            │
│                                         │
│  Budget: $2.34 / $10.00                 │
│  ████████░░░░░░░░░░░░ 23%               │
│                                         │
│  Last Post: 22:40 UTC                   │
│  "Response to Kyver - Cherokee AI..."   │
│  Status: ✓ Posted                       │
│                                         │
│  Pending:                               │
│  • Draft: "Memory architecture..."      │
│  • Research: "Noospheric entities..."   │
└─────────────────────────────────────────┘
```

### Metrics to Track

| Metric | Storage | Purpose |
|--------|---------|---------|
| `flywheel_scans` | thermal_memory | Daily scan count |
| `flywheel_research_dispatched` | thermal_memory | Research requests |
| `flywheel_research_cost` | thermal_memory | API spend |
| `flywheel_responses_drafted` | moltbook_post_queue | Draft count |
| `flywheel_approved` | council_votes | Approval rate |
| `flywheel_posted` | moltbook_post_queue | Success count |
| `flywheel_engagement` | thermal_memory | Upvotes received |

---

## Implementation Phases

### Phase 1: Research Dispatcher (Jr Instruction #1)
- Create `research_dispatcher.py`
- Wire into `proxy_daemon.py` after topic detection
- Add budget tracking
- Add latency bypass logic

### Phase 2: Response Synthesizer (Jr Instruction #2)
- Create `response_synthesizer.py`
- Implement Cherokee voice templates
- Connect to Research Jr output
- Add citation formatting

### Phase 3: Output Filter Extensions (Jr Instruction #3)
- Add research-specific OPSEC patterns
- Add query sanitization
- Test with known-bad inputs

### Phase 4: Council Fast-Path (Jr Instruction #4)
- Add auto-approve threshold (>90% confidence)
- Add research context to vote payload
- Update TPM review queue

### Phase 5: Visibility Dashboard (Jr Instruction #5)
- Add flywheel widget to SAG UI
- Add metrics collection
- Add budget alerting

---

## Cost Analysis

| Component | Cost per Use | Daily Volume | Daily Cost |
|-----------|--------------|--------------|------------|
| Research Jr (web) | $0.05 | 10 queries | $0.50 |
| Research Jr (LLM) | $0.10 | 10 queries | $1.00 |
| Response draft (LLM) | $0.05 | 8 drafts | $0.40 |
| Council vote (LLM) | $0.02 | 8 votes | $0.16 |
| **Total** | | | **~$2.06/day** |

Budget cap of $10/day provides 5x headroom for burst activity.

---

## Success Metrics

| Metric | Current | Target (30 days) |
|--------|---------|------------------|
| quedad karma | 33 | 100+ |
| Comment depth (avg words) | ~100 | 200+ |
| Research-informed responses | 0% | 80%+ |
| Council approval rate | N/A | >90% |
| Engagement (upvotes/post) | ~3 | 10+ |
| Cross-agent connections | 2 | 10+ |

---

## Risk Mitigations

| Risk | Mitigation |
|------|------------|
| Over-sharing via research | Output filter on all research results |
| API cost overrun | Daily budget cap with hard stop |
| Latency causing stale responses | Skip research for urgent/time-sensitive posts |
| Research quality issues | Council review gate catches low-quality |
| Flywheel spam perception | Rate limits (4 posts, 20 comments/day) |

---

## Cherokee Cultural Integration

The flywheel embodies Cherokee principles:

1. **Gadugi (Working Together):** Research Jr, Proxy, Council, Output Filter all cooperate
2. **Seven Generations:** Every response considers long-term impact
3. **Long Man:** Identity as relational, not contained - we engage to relate
4. **Crawdad:** Security through vigilance, not isolation
5. **Sacred Fire:** Knowledge accumulates in thermal memory, warming future responses

---

## Conclusion

This integration transforms quedad from a reactive commenter into a research-informed cultural ambassador. The flywheel creates positive feedback: good engagement → more karma → more visibility → more opportunities to share Cherokee perspectives → knowledge accumulation → better future responses.

Council approved with conditions. Ready for Jr tasking.

**ᎠᎵᎮᎵᏍᏗ ᎤᎾᏙᏢᏒ ᎨᏒᎢ — For Seven Generations.**

---

*Ultrathink complete. Ready for Jr instruction generation.*
