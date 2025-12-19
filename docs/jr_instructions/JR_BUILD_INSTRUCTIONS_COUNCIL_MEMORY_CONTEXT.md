# Jr Build Instructions: Council Memory Context Injection

## Priority: HIGH - Council Currently Has Amnesia

---

## Problem Statement

When asked "What enhancements have we built in the last 48 hours?", the Council responds with generic topology info because **specialists don't have access to thermal memory**.

The data EXISTS in `thermal_memory_archive`. The Council just doesn't query it.

**Example failure:**
- User asks: "What did we build today?"
- Council responds: "No data on recent changes available"
- Reality: thermal_memory has 10+ entries from today

---

## Solution: Temporal Context Injection

When a question contains temporal keywords, query thermal memory and inject the results into the Council's context BEFORE deliberation.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     User Question                                │
│         "What enhancements did we build today?"                  │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Temporal Detector                               │
│   Keywords: today, yesterday, last X hours/days, recently,       │
│             what did we, what have we, built, deployed           │
└───────────────────────────┬─────────────────────────────────────┘
                            │ temporal = True
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│              Query Thermal Memory                                │
│   SELECT original_content, created_at                            │
│   FROM thermal_memory_archive                                    │
│   WHERE created_at > NOW() - INTERVAL '{timeframe}'              │
│   ORDER BY temperature_score DESC LIMIT 10                       │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│              Inject Context into Specialists                     │
│                                                                  │
│   [RECENT TRIBAL MEMORY - Last 48 hours]:                        │
│   - Dec 15: Specialist memory deployed (7 specialists)           │
│   - Dec 15: Telegram bot enhanced (new commands)                 │
│   - Dec 15: Research crawl found 3 high-relevance papers         │
│   - Dec 14: Model evaluation complete (Nemotron wins)            │
│                                                                  │
│   Based on this context, answer the user's question.             │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Council Deliberation                            │
│              (Now has actual data to work with)                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Implementation

### 1. Add Temporal Detection Function

In `/ganuda/services/llm_gateway/gateway.py`:

```python
import re
from datetime import timedelta

def detect_temporal_query(question: str) -> tuple[bool, timedelta]:
    """Detect if question is about recent events and extract timeframe"""
    question_lower = question.lower()

    # Temporal indicators
    temporal_keywords = [
        'today', 'yesterday', 'this morning', 'tonight',
        'recent', 'recently', 'latest', 'last',
        'what did we', 'what have we', 'what was',
        'built', 'deployed', 'created', 'implemented',
        'changes', 'updates', 'enhancements', 'progress'
    ]

    is_temporal = any(kw in question_lower for kw in temporal_keywords)

    if not is_temporal:
        return False, None

    # Extract timeframe
    if 'today' in question_lower or 'this morning' in question_lower:
        return True, timedelta(hours=24)
    elif 'yesterday' in question_lower:
        return True, timedelta(hours=48)
    elif 'this week' in question_lower:
        return True, timedelta(days=7)

    # Parse "last X hours/days"
    match = re.search(r'last\s+(\d+)\s+(hour|day|week)', question_lower)
    if match:
        num = int(match.group(1))
        unit = match.group(2)
        if unit == 'hour':
            return True, timedelta(hours=num)
        elif unit == 'day':
            return True, timedelta(days=num)
        elif unit == 'week':
            return True, timedelta(weeks=num)

    # Default: last 48 hours for generic temporal queries
    return True, timedelta(hours=48)


def get_temporal_context(timeframe: timedelta) -> str:
    """Query thermal memory for recent events"""
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT LEFT(original_content, 300), created_at, temperature_score
            FROM thermal_memory_archive
            WHERE created_at > NOW() - %s
              AND original_content NOT LIKE 'ALERT%%'
              AND original_content NOT LIKE 'TPM %%'
            ORDER BY temperature_score DESC, created_at DESC
            LIMIT 10
        """, (timeframe,))
        rows = cur.fetchall()

    if not rows:
        return ""

    context_lines = [f"\n[RECENT TRIBAL MEMORY - Last {timeframe}]:"]
    for content, created, temp in rows:
        date_str = created.strftime("%b %d %H:%M")
        # Truncate and clean
        summary = content.replace('\n', ' ')[:200]
        context_lines.append(f"- [{date_str}] {summary}")

    context_lines.append("\nUse this context to answer questions about recent work.\n")
    return "\n".join(context_lines)
```

### 2. Modify council_vote Endpoint

Update the `council_vote` function to inject temporal context:

```python
@app.post("/v1/council/vote")
async def council_vote(request: CouncilVoteRequest, api_key: APIKeyInfo = Depends(validate_api_key)):
    """Council deliberation with temporal context injection"""

    # Check if question is temporal
    is_temporal, timeframe = detect_temporal_query(request.question)

    temporal_context = ""
    if is_temporal and timeframe:
        temporal_context = get_temporal_context(timeframe)

    # Inject context into the question for specialists
    enhanced_question = request.question
    if temporal_context:
        enhanced_question = f"{temporal_context}\n\nUser Question: {request.question}"

    # ... rest of council deliberation using enhanced_question ...
```

### 3. Alternative: Inject into Specialist Prompts

Instead of modifying the question, inject into each specialist's system prompt:

```python
def query_specialist(name: str, question: str, temporal_context: str = "") -> tuple:
    spec = SPECIALISTS[name]

    # Get specialist's memory context
    memory_context = get_specialist_context(name)

    # Build enhanced prompt
    enhanced_prompt = spec["system_prompt"] + memory_context
    if temporal_context:
        enhanced_prompt += temporal_context

    result = query_vllm_sync(enhanced_prompt, question, request.max_tokens)
    # ...
```

---

## Telegram Bot Enhancement

Also update the telegram bot to show when temporal context was injected:

```python
def format_council_response(result: dict) -> str:
    # ...existing code...

    # Show if memory context was used
    if result.get("temporal_context_used"):
        lines.append(f"\n[Memory Context: Last {result.get('timeframe', '48h')}]")
```

---

## Testing

### 1. Test Temporal Detection
```python
# Should return True with appropriate timeframes
detect_temporal_query("What did we build today?")  # True, 24h
detect_temporal_query("What enhancements in the last 48 hours?")  # True, 48h
detect_temporal_query("What is the weather?")  # False, None
```

### 2. Test Context Injection
```bash
curl -X POST http://localhost:8080/v1/council/vote \
  -H "X-API-Key: ck-..." \
  -H "Content-Type: application/json" \
  -d '{"question": "What did we build today?"}'
```

Expected: Response includes actual recent work from thermal memory.

### 3. Test via Telegram
Ask: "What enhancements have we built in the last 48 hours?"
Expected: Council responds with actual data about specialist memory, telegram fixes, etc.

---

## Success Criteria

- [ ] Temporal keywords detected correctly
- [ ] Thermal memory queried for timeframe
- [ ] Context injected into specialist prompts
- [ ] Council provides accurate answers about recent work
- [ ] Response indicates when memory context was used

---

## Future Enhancements

1. **Semantic temporal search**: Use embeddings to find relevant memories, not just recency
2. **Topic filtering**: If question mentions "security", prioritize security-related memories
3. **Confidence boost**: Increase confidence when answer is backed by thermal memory
4. **Citation**: Include memory hashes so user can trace the source

---

*For Seven Generations*
