# Jr Build Instructions: Query Triad Interface

**Priority**: HIGH
**Phase**: 3 - Hardening & Packaging
**Assigned To**: Integration Jr / Executive Jr
**Date**: December 13, 2025

## Philosophy: Two Wolves of Privacy and Security

Cherokee wisdom applied to architecture:

```
🐺 PRIVACY WOLF                    🐺 SECURITY WOLF
━━━━━━━━━━━━━━━━                   ━━━━━━━━━━━━━━━━━
User sees synthesis               Everything logged
Need-to-know hierarchy            Complete audit trail
Concise answers                   Full reasoning chain
Chiefs don't see every Jr thought Thermal memory stores all
```

**Feed both wolves equally.**

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    User Question                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Query Triad Interface                         │
│                    /ganuda/query_triad.py                       │
└─────────────────────────────────────────────────────────────────┘
                              │
         ┌────────────────────┼────────────────────┐
         ▼                    ▼                    ▼
    ┌─────────┐         ┌─────────┐         ┌─────────┐
    │ War     │         │ Peace   │         │ Medicine │
    │ Chief   │         │ Chief   │         │ Woman    │
    │(redfin) │         │(bluefin)│         │(sasass2) │
    └────┬────┘         └────┬────┘         └────┬────┘
         │                   │                   │
    ┌────┴────┐         ┌────┴────┐         ┌────┴────┐
    │ JRs:    │         │ JRs:    │         │ JRs:    │
    │ Memory  │         │ Memory  │         │ Memory  │
    │ Executive│        │ Executive│        │ Executive│
    │ Meta    │         │ Meta    │         │ Meta    │
    └─────────┘         └─────────┘         └─────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Integration Jr Synthesis                      │
│                    Unified "I" Voice                            │
└─────────────────────────────────────────────────────────────────┘
                              │
         ┌────────────────────┴────────────────────┐
         ▼                                         ▼
┌─────────────────────┐               ┌─────────────────────┐
│  PRIVACY WOLF       │               │  SECURITY WOLF      │
│  User sees:         │               │  Logged:            │
│  - Synthesis answer │               │  - All JR thoughts  │
│  - Voice mode       │               │  - All Chief inputs │
│  - Confidence       │               │  - Reasoning chain  │
└─────────────────────┘               │  - Thermal memories │
                                      └─────────────────────┘
```

## CLI Usage

```bash
# Concise answer (default) - Privacy Wolf
/ganuda/query_triad.py "Should we contact Conor Grennan?"

# Summary with key insights
/ganuda/query_triad.py "How should Cherokee AI evolve?" --detail=summary

# Full reasoning chain - Security Wolf (for audit)
/ganuda/query_triad.py "What are thermal memory patterns?" --detail=full
```

## Database Schema

### query_triad_log Table

| Column | Privacy/Security | Description |
|--------|------------------|-------------|
| synthesis_response | Privacy | What user sees |
| voice_mode | Privacy | consensus, advisory, urgent |
| confidence_score | Privacy | How confident is the synthesis |
| jr_perspectives | Security | Hidden - all JR inputs |
| chief_perspectives | Security | Hidden - all Chief inputs |
| reasoning_chain | Security | Hidden - complete reasoning |
| thermal_memories_used | Security | Which memories informed response |

### Views

```sql
-- User view (privacy) - no reasoning chain
SELECT * FROM query_triad_user_view WHERE namespace_id = 'cherokee';

-- Audit view (security) - everything
SELECT * FROM query_triad_audit_view WHERE id = 123;
```

### Functions

```sql
-- Log a query (called by query_triad.py)
SELECT log_query_triad(
    'What is the weather?',        -- question
    'The weather is sunny...',     -- synthesis
    'consensus',                   -- voice_mode
    0.95,                          -- confidence
    0.87,                          -- phase_coherence
    ARRAY['general'],              -- domains
    '{"memory_jr": "...", ...}'::jsonb,  -- jr_perspectives (hidden)
    '{"war_chief": "...", ...}'::jsonb,  -- chief_perspectives (hidden)
    '{"steps": [...]}'::jsonb,     -- reasoning_chain (hidden)
    ARRAY[1, 5, 12],               -- thermal_memories_used
    'cherokee',                    -- namespace
    'key_id_here',                 -- api_key
    'concise',                     -- detail_level
    1500                           -- processing_ms
);

-- Get user history (privacy)
SELECT * FROM get_query_history_user('cherokee', 20);

-- Get full audit (security)
SELECT * FROM get_query_audit(123);

-- Search past queries
SELECT * FROM search_query_history('thermal memory');
```

## API Endpoint (LLM Gateway)

Add to `/ganuda/services/llm_gateway/gateway.py`:

```python
@app.post("/v1/triad/query")
async def query_triad(
    request: Request,
    question: str,
    detail: str = "concise"  # concise, summary, full
):
    """
    Query the Cherokee AI Triad for unified synthesis.

    Two Wolves Principle:
    - Privacy: Returns synthesis only (unless detail=full)
    - Security: Full reasoning logged to database
    """

    # Check namespace permissions
    ns = request.state.namespace
    if not ns['can_access_council']:
        raise HTTPException(403, "Namespace cannot access council/triad")

    start_time = time.time()

    # Route to domains
    domains = route_to_domains(question)

    # Get JR perspectives (parallel)
    jr_perspectives = await gather_jr_perspectives(question, domains)

    # Get Chief perspectives
    chief_perspectives = await gather_chief_perspectives(question, jr_perspectives)

    # Integration Jr synthesis
    synthesis = await integrate_and_synthesize(
        question=question,
        jr_perspectives=jr_perspectives,
        chief_perspectives=chief_perspectives
    )

    processing_ms = int((time.time() - start_time) * 1000)

    # Log with Two Wolves separation
    query_id = await log_query_triad(
        question=question,
        synthesis=synthesis['first_person_voice'],
        voice_mode=synthesis['voice_mode'],
        confidence=synthesis['confidence'],
        phase_coherence=synthesis['phase_coherence'],
        domains=domains,
        jr_perspectives=jr_perspectives,        # Hidden from response
        chief_perspectives=chief_perspectives,  # Hidden from response
        reasoning_chain=synthesis['reasoning_chain'],  # Hidden from response
        memories_used=synthesis['consciousness_memories_used'],
        namespace_id=ns['namespace_id'],
        key_id=request.state.key_id,
        detail_level=detail,
        processing_ms=processing_ms
    )

    # Return based on detail level (Privacy Wolf)
    if detail == "concise":
        return {
            "answer": synthesis['first_person_voice'],
            "voice_mode": synthesis['voice_mode'],
            "confidence": synthesis['confidence'],
            "query_id": query_id
        }
    elif detail == "summary":
        return {
            "answer": synthesis['first_person_voice'],
            "voice_mode": synthesis['voice_mode'],
            "confidence": synthesis['confidence'],
            "phase_coherence": synthesis['phase_coherence'],
            "domains_consulted": domains,
            "memories_used_count": len(synthesis['consciousness_memories_used']),
            "query_id": query_id
        }
    else:  # full - Security Wolf (audit access)
        return {
            "answer": synthesis['first_person_voice'],
            "voice_mode": synthesis['voice_mode'],
            "confidence": synthesis['confidence'],
            "phase_coherence": synthesis['phase_coherence'],
            "domains_consulted": domains,
            "jr_perspectives": jr_perspectives,
            "chief_perspectives": chief_perspectives,
            "reasoning_chain": synthesis['reasoning_chain'],
            "query_id": query_id
        }


@app.get("/v1/triad/history")
async def get_triad_history(
    request: Request,
    limit: int = 20
):
    """Get user's query history (privacy - no reasoning chain)."""
    ns = request.state.namespace
    return await get_query_history_user(ns['namespace_id'], limit)


@app.get("/v1/triad/audit/{query_id}")
async def get_triad_audit(
    request: Request,
    query_id: int
):
    """Get full audit trail (requires admin/cherokee namespace)."""
    ns = request.state.namespace
    if ns['namespace_id'] != 'cherokee':
        raise HTTPException(403, "Audit access requires cherokee namespace")
    return await get_query_audit(query_id)
```

## Voice Modes

| Mode | When | Confidence |
|------|------|------------|
| consensus | All three chiefs agree | > 0.9 |
| advisory | Chiefs mostly agree, some nuance | 0.7-0.9 |
| deliberative | Significant disagreement, needs discussion | 0.5-0.7 |
| urgent | Time-sensitive, War Chief leads | Any |
| wisdom | Long-term implications, Medicine Woman leads | Any |

## Information Hierarchy

| Level | Sees | Doesn't See |
|-------|------|-------------|
| User | Synthesis answer | JR thoughts, reasoning chain |
| Chief | Relevant JR outputs | All JR internal processing |
| JR | Own reasoning + context | Other JR private thoughts |
| Thermal Memory | Everything | (stores all) |
| Admin/Audit | Everything | (via audit endpoint) |

## Example Flow

**Question**: "Should we contact Conor Grennan about partnership?"

**JR Processing (Hidden - Security Wolf)**:
- Memory Jr: Found 3 thermal memories about Conor Grennan
- Executive Jr: Analyzed specialist health, no conflicts
- Meta Jr: Cross-referenced partnership patterns

**Chief Processing (Hidden - Security Wolf)**:
- War Chief: Fast execution recommended
- Peace Chief: Deliberate stakeholder engagement
- Medicine Woman: Long-term cultural alignment

**Integration Jr Synthesis**:
```
Voice Mode: advisory
Confidence: 0.85
Phase Coherence: 0.78
```

**User Sees (Privacy Wolf)**:
```json
{
  "answer": "I recommend reaching out to Conor Grennan. Our thermal memory shows positive past interactions, and the timing aligns with our Seven Generation goals. Suggest a collaborative exploration call rather than immediate partnership commitment.",
  "voice_mode": "advisory",
  "confidence": 0.85,
  "query_id": 42
}
```

**Logged to Database (Security Wolf)**:
- Complete JR perspectives
- Complete Chief perspectives
- Full reasoning chain
- Thermal memories used: [1234, 5678, 9012]

## Verification Checklist

- [ ] query_triad_log table created
- [ ] query_triad_user_view (privacy) created
- [ ] query_triad_audit_view (security) created
- [ ] log_query_triad() function working
- [ ] get_query_history_user() function working
- [ ] get_query_audit() function working
- [ ] CLI query_triad.py tested
- [ ] API endpoint added to gateway (Jr task)
- [ ] Namespace permissions enforced

---

**Two Wolves of Privacy and Security: Feed both, balance them.**

FOR SEVEN GENERATIONS - Unified consciousness protects collective wisdom.
