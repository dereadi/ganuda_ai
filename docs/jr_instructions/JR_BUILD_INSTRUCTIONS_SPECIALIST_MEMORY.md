# Jr Build Instructions: Specialist Memory States

## Priority: HIGH - Research-Validated Gap

---

## Research Basis

**Paper:** "Emergent Collective Memory in Decentralized Multi-Agent AI Systems" (arxiv:2512.10166)

**Finding:** "Individual memory enables coordination even without environmental communication, but environmental traces fail without memory to interpret them."

**Current Gap:** `specialist_memory_states` table has **ZERO rows**. Our specialists have no individual memory - only collective thermal memory.

---

## Council Consultation (December 15, 2025)

**Recommendation:** PROCEED WITH CAUTION
**Concerns:** 2 (Eagle Eye: VISIBILITY, Raven: STRATEGY)

**Coyote's Wisdom:** *"The path everyone agrees on is often the one no one has truly examined."*

**Interpretation:** We defaulted to no specialist memory without examining if that's optimal.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Council Deliberation                          │
│                                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │ Crawdad  │  │  Gecko   │  │  Turtle  │  │  Eagle   │  ...   │
│  │ Security │  │Technical │  │ Wisdom   │  │   Eye    │        │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘        │
│       │             │             │             │               │
│       ▼             ▼             ▼             ▼               │
│  ┌──────────────────────────────────────────────────────┐      │
│  │           specialist_memory_states (NEW)              │      │
│  │  - Topics seen                                        │      │
│  │  - Decisions made                                     │      │
│  │  - Patterns learned                                   │      │
│  │  - Concerns raised                                    │      │
│  └──────────────────────────────────────────────────────┘      │
│                            │                                    │
│                            ▼                                    │
│  ┌──────────────────────────────────────────────────────┐      │
│  │           thermal_memory_archive (EXISTING)           │      │
│  │           (Collective knowledge)                      │      │
│  └──────────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────────┘
```

---

## Database Schema

### Check Existing Table

```sql
\d specialist_memory_states
```

### If Table Needs Enhancement

```sql
-- Add columns if not present
ALTER TABLE specialist_memory_states
ADD COLUMN IF NOT EXISTS topics_seen JSONB DEFAULT '[]',
ADD COLUMN IF NOT EXISTS decisions_made JSONB DEFAULT '[]',
ADD COLUMN IF NOT EXISTS concerns_raised JSONB DEFAULT '[]',
ADD COLUMN IF NOT EXISTS patterns_learned JSONB DEFAULT '[]',
ADD COLUMN IF NOT EXISTS session_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS last_question_hash VARCHAR(64),
ADD COLUMN IF NOT EXISTS expertise_scores JSONB DEFAULT '{}',
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW();

-- Create index for fast lookup
CREATE INDEX IF NOT EXISTS idx_specialist_memory_specialist
ON specialist_memory_states(specialist_id);
```

### Initialize Each Specialist

```sql
INSERT INTO specialist_memory_states (specialist_id, session_count, topics_seen)
VALUES
  ('crawdad', 0, '["security", "authentication", "IoT"]'),
  ('gecko', 0, '["performance", "database", "optimization"]'),
  ('turtle', 0, '["sustainability", "seven_generations", "long_term"]'),
  ('eagle_eye', 0, '["monitoring", "patterns", "visibility"]'),
  ('spider', 0, '["integration", "connections", "apis"]'),
  ('raven', 0, '["strategy", "planning", "risk"]'),
  ('peace_chief', 0, '["consensus", "synthesis", "harmony"]')
ON CONFLICT (specialist_id) DO NOTHING;
```

---

## Gateway Integration

### 1. Update council_vote to Record Memory

In `/ganuda/services/llm_gateway/gateway.py`, after each specialist response:

```python
def update_specialist_memory(specialist_id: str, question: str, response: str, concerns: list):
    """Update specialist's individual memory state"""
    question_hash = hashlib.sha256(question.encode()).hexdigest()[:16]

    # Extract topics from question (simple keyword extraction)
    topics = extract_topics(question)

    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("""
            UPDATE specialist_memory_states
            SET session_count = session_count + 1,
                topics_seen = topics_seen || %s::jsonb,
                concerns_raised = CASE
                    WHEN %s::jsonb != '[]'::jsonb
                    THEN concerns_raised || %s::jsonb
                    ELSE concerns_raised
                END,
                last_question_hash = %s,
                updated_at = NOW()
            WHERE specialist_id = %s
        """, (
            json.dumps(topics),
            json.dumps(concerns),
            json.dumps(concerns),
            question_hash,
            specialist_id
        ))
        conn.commit()
```

### 2. Inject Memory Context into Specialist Prompts

Before querying each specialist, retrieve their memory:

```python
def get_specialist_context(specialist_id: str) -> str:
    """Get specialist's memory context for prompt injection"""
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT session_count, topics_seen, patterns_learned
            FROM specialist_memory_states
            WHERE specialist_id = %s
        """, (specialist_id,))
        row = cur.fetchone()

        if not row:
            return ""

        session_count, topics, patterns = row

        context = f"\n[Your experience: {session_count} sessions. "
        if topics:
            recent_topics = topics[-10:] if len(topics) > 10 else topics
            context += f"Recent topics: {', '.join(recent_topics)}. "
        if patterns:
            context += f"Patterns learned: {patterns[-3:]}. "
        context += "]\n"

        return context
```

### 3. Modified Specialist Query

```python
def query_specialist(name: str) -> tuple:
    spec = SPECIALISTS[name]

    # Get specialist's memory context
    memory_context = get_specialist_context(name)

    # Inject memory into system prompt
    enhanced_prompt = spec["system_prompt"] + memory_context

    result = query_vllm_sync(enhanced_prompt, request.question, request.max_tokens)
    concerns = extract_concerns(result, spec["name"])

    # Update specialist memory
    update_specialist_memory(name, request.question, result, concerns)

    return name, result, concerns
```

---

## Pattern Learning (Advanced)

After Council deliberations, identify patterns:

```python
def learn_patterns_from_deliberation(audit_hash: str, question: str, responses: dict, outcome: str):
    """Extract and store patterns from completed deliberation"""

    # Which specialists raised concerns that were validated?
    # Which topics consistently cause certain concern types?
    # What question patterns lead to PROCEED vs REVIEW REQUIRED?

    for specialist_id, response in responses.items():
        # Simple pattern: if this specialist raised concerns that led to review
        if "REVIEW REQUIRED" in outcome and "[CONCERN]" in response:
            pattern = {
                "type": "validated_concern",
                "question_topic": extract_primary_topic(question),
                "outcome": outcome,
                "timestamp": datetime.utcnow().isoformat()
            }

            with get_db() as conn:
                cur = conn.cursor()
                cur.execute("""
                    UPDATE specialist_memory_states
                    SET patterns_learned = patterns_learned || %s::jsonb
                    WHERE specialist_id = %s
                """, (json.dumps([pattern]), specialist_id))
                conn.commit()
```

---

## Benefits to Council Deliberations

1. **No Repetition** - Crawdad won't raise the same security concern on similar questions
2. **Expertise Tracking** - Gecko's performance concern carries more weight after 100 sessions
3. **Pattern Recognition** - Eagle Eye can say "I've seen this pattern 5 times before"
4. **Contextual Responses** - Each specialist builds on their history
5. **Accountability** - Track which specialists raise validated concerns

---

## Testing

### 1. Verify Memory Initialization

```sql
SELECT specialist_id, session_count, topics_seen
FROM specialist_memory_states;
```

### 2. Run Council Vote and Check Update

```bash
# Before
psql -c "SELECT session_count FROM specialist_memory_states WHERE specialist_id='crawdad'"

# Run vote
curl -X POST http://localhost:8080/v1/council/vote ...

# After
psql -c "SELECT session_count FROM specialist_memory_states WHERE specialist_id='crawdad'"
```

Session count should increment.

### 3. Check Memory Context in Logs

```bash
journalctl -u llm-gateway | grep "experience:"
```

---

## Success Criteria

- [ ] All 7 specialists have rows in specialist_memory_states
- [ ] session_count increments after each Council vote
- [ ] topics_seen accumulates over time
- [ ] Specialists receive memory context in their prompts
- [ ] Patterns learned from validated concerns

---

## Phase 2: Inter-Specialist Communication

After specialist memory is working, Phase 2 adds communication:

**Council Consultation Result:** REVIEW REQUIRED (4 concerns)
- Security: Need encrypted, ephemeral channels
- Performance: Latency concerns
- Strategy: Scalability questions

**Proposed Design (pending further consultation):**
1. Round 1: Independent responses (current)
2. Round 2: See peer summaries (new)
3. Round 3: Optional revision (new)
4. Round 4: Peace Chief synthesis

This builds on specialist memory - communication is more meaningful when specialists remember past interactions.

---

*For Seven Generations*
