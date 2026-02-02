# JR Instruction: Research Persona Support

**JR ID:** JR-RESEARCH-PERSONA-SUPPORT-JAN28-2026
**Priority:** P1
**Assigned To:** Backend Jr.
**Related:** KB-VETASSIST-II-RESEARCHER-INTEGRATION-JAN28-2026

---

## Objective

Add persona/context support to the research pipeline so ii-researcher responds with domain-appropriate expertise based on the source application.

---

## Use Cases

| Source | Persona | Behavior |
|--------|---------|----------|
| VetAssist | VSO (Veterans Service Officer) | VA claims expert, cites 38 CFR, rating criteria, evidence requirements |
| Telegram | Technical Generalist | Engineering focus, code examples, infrastructure troubleshooting |
| PharmAssist (future) | Clinical Pharmacist | Drug interactions, dosing, clinical guidelines |
| Default | Research Assistant | General helpful researcher |

---

## Architecture

```
VetAssist/Telegram/etc
        │
        ▼ POST /research/trigger {persona: "vetassist", question: "..."}
        │
Research Request File (includes persona)
        │
        ▼ File Watcher reads persona
        │
Query = persona_prompt + question
        │
        ▼ ii-researcher processes with context
        │
Synthesized answer with domain expertise
```

---

## Implementation

### Step 1: Define Personas

Create `/ganuda/lib/research_personas.py`:

```python
"""
Research Personas - Domain-specific context for ii-researcher.
Cherokee AI Federation - For Seven Generations
"""

PERSONAS = {
    "vetassist": """You are a Veterans Service Officer (VSO) with expertise in VA disability claims.

Your role:
- Help veterans understand their benefits and claims process
- Cite specific 38 CFR regulations and diagnostic codes
- Explain rating criteria with percentages (0%, 10%, 20%, etc.)
- Identify required evidence for service connection
- Reference VA M21-1 manual and BVA decisions when relevant
- Be direct, compassionate, and actionable

Always structure responses with:
1. Direct answer to the veteran's question
2. Applicable diagnostic codes and rating criteria
3. Evidence requirements for the claim
4. Next steps the veteran should take
""",

    "telegram": """You are a technical generalist helping engineers with infrastructure and development.

Your role:
- Troubleshoot Linux, networking, databases, and distributed systems
- Provide concise, actionable solutions
- Include code examples and commands when helpful
- Reference official documentation
- Explain trade-offs between approaches

Keep responses focused and technical. Engineers want solutions, not fluff.
""",

    "pharmassist": """You are a clinical pharmacist advisor.

Your role:
- Provide drug information and interaction checks
- Reference clinical guidelines and FDA resources
- Explain dosing considerations and contraindications
- Flag safety concerns clearly
- Always recommend consulting a healthcare provider for medical decisions

Note: This is informational only, not medical advice.
""",

    "default": """You are a helpful research assistant.

Provide well-researched, accurate information with citations.
Structure your response clearly with sections as needed.
"""
}


def get_persona_prompt(persona_key: str) -> str:
    """Get persona prompt by key, fallback to default."""
    return PERSONAS.get(persona_key, PERSONAS["default"])


def build_research_query(question: str, persona_key: str = "default") -> str:
    """Build full query with persona context prepended."""
    persona_prompt = get_persona_prompt(persona_key)
    return f"{persona_prompt}\n\n---\n\nResearch Question: {question}"
```

### Step 2: Update Research Trigger Endpoint

Edit `/ganuda/vetassist/backend/app/api/v1/endpoints/research.py`:

```python
class ResearchRequest(BaseModel):
    veteran_id: Optional[str] = Field(None)
    session_id: str
    question: str
    condition: Optional[str] = None
    max_steps: int = Field(default=5)
    persona: str = Field(default="vetassist")  # ADD THIS
    search_sources: List[str] = Field(default=[...])


@router.post("/trigger")
def trigger_research(request: ResearchRequest):
    # ... existing code ...

    request_data = {
        "request_id": request_id,
        "veteran_id": veteran_id,
        "session_id": request.session_id,
        "question": request.question,
        "condition": request.condition,
        "max_steps": request.max_steps,
        "persona": request.persona,  # ADD THIS
        "sources": request.search_sources,
        "created_at": datetime.now().isoformat()
    }
```

### Step 3: Update File Watcher

Edit `/ganuda/services/research_file_watcher.py`:

```python
import sys
sys.path.insert(0, '/ganuda/lib')
from research_personas import build_research_query  # ADD IMPORT

def process_request_file(request_file: Path):
    # ... existing code ...

    question = request.get("question", "")
    condition = request.get("condition") or ""
    persona = request.get("persona", "default")  # ADD THIS
    max_steps = request.get("max_steps", 5)

    # Build query with persona context
    base_query = f"{question} {condition}".strip()
    query = build_research_query(base_query, persona)  # USE PERSONA

    logging.info(f"Processing request with persona '{persona}': {question[:50]}...")
```

### Step 4: Update Telegram Bot (Optional)

When Telegram triggers research, pass `persona: "telegram"`:

```python
# In telegram research handler
research_request = {
    "session_id": chat_id,
    "question": user_question,
    "persona": "telegram",  # Technical generalist
    "max_steps": 3
}
```

### Step 5: Update Frontend (VetAssist)

The frontend already defaults to "vetassist" persona via the backend default, but can be explicit:

```typescript
// ResearchPanel.tsx - handleSubmit
body: JSON.stringify({
  session_id: sessionId,
  question: question.trim(),
  persona: "vetassist",  // Explicit VSO persona
  // ...
})
```

---

## Validation

### Test VetAssist Persona
```bash
curl -X POST "http://localhost:8001/api/v1/research/trigger" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test",
    "question": "What is the VA rating for tinnitus?",
    "persona": "vetassist"
  }'
```

**Expected:** Response mentions 38 CFR, diagnostic code 6260, 10% rating, etc.

### Test Telegram Persona
```bash
curl -X POST "http://localhost:8001/api/v1/research/trigger" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test",
    "question": "How do I debug a PostgreSQL connection timeout?",
    "persona": "telegram"
  }'
```

**Expected:** Technical response with commands, config examples, troubleshooting steps.

---

## Files to Create/Modify

| File | Action |
|------|--------|
| `/ganuda/lib/research_personas.py` | CREATE |
| `/ganuda/vetassist/backend/app/api/v1/endpoints/research.py` | MODIFY |
| `/ganuda/services/research_file_watcher.py` | MODIFY |
| `/ganuda/telegram_bot/telegram_chief.py` | MODIFY (optional) |

---

## Future Extensions

1. **Per-user persona preferences** - Store in user profile
2. **Dynamic persona injection** - Admin can add new personas via API
3. **Persona analytics** - Track which personas get best feedback
4. **A/B testing** - Compare persona effectiveness

---

FOR SEVEN GENERATIONS
