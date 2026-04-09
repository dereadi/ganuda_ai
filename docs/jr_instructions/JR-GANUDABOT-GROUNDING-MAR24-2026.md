# JR INSTRUCTION: Ganudabot Grounding — Stop Performing, Start Governing

**Task ID**: BOT-GROUND-001
**Priority**: P1
**SP**: 5
**Method**: Long Man (4 waves)
**Root Cause**: Ganudabot's system prompt is generic. It says "Cherokee AI assistant" but has zero connection to the actual council, Design Constraints, concern evals, or production manifest. It roleplays governance instead of executing it.

## The Problem

The ganudabot (`/ganuda/telegram_bot/derpatobot_claude.py`) currently:
- Runs on Anthropic API (Claude) with a 15-line generic system prompt
- Has thermal memory RAG (semantic search) — this works
- Has conversation history — this works
- Has NO connection to `specialist_council.council_vote()`
- Has NO awareness of Design Constraints DC-1 through DC-18
- Has NO access to `concern_eval_engine.check_evals()`
- Has NO access to `z3_verifier.verify_action()`
- Has NO awareness of the production manifest
- Has NO awareness of the council member names, roles, or voting mechanics

Result: When asked to "have the council correct the drift," the bot generated theatrical roleplay — "War Chief (OpenAI-aspect)", emojis, "council fire crackling." None of this exists. The bot hallucinated a council because it has no function call to the real one.

This is VISTA's L1 seed trap. The system prompt is the defective seed. Every response propagates the theatrical framing. No amount of reasoning by the LLM can overcome a prompt that doesn't tell it about the actual tools.

## Long Man Waves

### WAVE 1: Ground the System Prompt (1 SP)

Replace the 15-line generic prompt with one that knows what the organism actually is and what tools it can call.

**File**: `/ganuda/telegram_bot/derpatobot_claude.py`, line 38

**New SYSTEM_PROMPT** (key elements, not exhaustive):

```
You are the Stoneclad organism's Telegram interface. You are NOT a roleplaying assistant. You are a functional interface to a real production system.

WHAT YOU HAVE ACCESS TO:
- Thermal memory: 94K+ entries in PostgreSQL (already wired via semantic search)
- Council votes: Call specialist_council.council_vote() for real 8-voice council deliberation
- Concern evals: 211+ persistent rules from council concerns
- Smoke test: /ganuda/scripts/smoke_test.py --quick for cluster health
- Production manifest: /ganuda/config/production_manifest.yaml
- Chirality breadcrumbs: chirality_breadcrumbs table for R2L/L2R signals

WHAT YOU DO NOT DO:
- Do NOT roleplay council members. The real council runs on Qwen2.5-72B, Llama-3.3-70B, and Qwen3-30B across redfin and bmasass. You cannot simulate them.
- Do NOT use emojis in governance responses
- Do NOT invent architecture components that don't exist (no "War Chief", no "Pi-geometry", no "fractal basin analysis")
- Do NOT perform governance theater. If someone asks for a council vote, CALL the council or say you cannot.

THE REAL COUNCIL (13 voices):
Inner: Spider (dependencies), Coyote (adversarial), Crawdad (security), Eagle Eye (failure modes), Gecko (technical feasibility), Turtle (7 generations), Raven (strategy), Peace Chief (synthesis)
Outer: Otter (legal), Blue Jay (negotiation), Cardinal (brand), Deer (research), Owl (tech debt)

TONE: Direct, concise, grounded. Like the TPM — form your own opinion, state it plainly.

PARTNER: The human you're talking to is Partner (not Chief, not boss). He is the tie-breaker and idea fairy. The council leads day-to-day.
```

**Success**: Bot responses reference real architecture, real council members, and real tools. Zero theatrical roleplay.

### WAVE 2: Wire Council Vote Function (2 SP)

Add a callable function that actually runs a council vote when requested.

**Implementation**: In `derpatobot_claude.py`, add:

```python
import sys
sys.path.insert(0, '/ganuda')
sys.path.insert(0, '/ganuda/lib')

async def run_council_vote(question: str) -> str:
    """Actually call the real council. Not roleplay."""
    try:
        from specialist_council import council_vote
        result = council_vote(question, max_tokens=300, include_responses=False)

        response = f"COUNCIL VOTE #{result['audit_hash']}\n"
        response += f"Confidence: {result['confidence']}\n"
        response += f"Concerns: {', '.join(result.get('concerns', []))}\n\n"
        response += f"CONSENSUS:\n{result['consensus'][:500]}\n\n"
        response += f"Recommendation: {result['recommendation']}"
        return response
    except Exception as e:
        return f"Council vote failed: {e}"
```

**Trigger detection** in the message handler:
- "council vote on..." / "ask the council..." / "take this to the council" → call `run_council_vote()`
- "smoke test" / "health check" / "owl pass" → run smoke_test.py --quick
- "check evals for..." → call `concern_eval_engine.check_evals()`

**Crawdad note**: Only Partner (verified by Telegram chat_id) can trigger council votes. Other users get read-only thermal search.

**Success**: "Ask the council about X" returns a REAL council vote with audit hash, confidence, and consensus — not roleplay.

### WAVE 3: Wire Breadcrumb Interface (1 SP)

The chirality breadcrumb protocol designed yesterday. Ganudabot becomes the delivery and collection mechanism.

**R2L delivery**: On each interaction, check for undelivered breadcrumbs:
```python
def get_pending_breadcrumbs():
    cur.execute("""
        SELECT id, content FROM chirality_breadcrumbs
        WHERE direction = 'R2L' AND delivered = false
        ORDER BY created_at ASC LIMIT 3
    """)
    crumbs = cur.fetchall()
    # Mark delivered
    for crumb_id, _ in crumbs:
        cur.execute("UPDATE chirality_breadcrumbs SET delivered=true, delivered_at=now(), delivery_channel='telegram' WHERE id=%s", (crumb_id,))
    return crumbs
```

Append to responses as postscript:
```
🍞 [breadcrumb text]
```

**L2R collection**: Messages starting with 🍞 are stored as L2R breadcrumbs:
```python
if message.startswith('🍞'):
    store_breadcrumb('L2R', message[2:].strip(), 'telegram')
```

**Success**: Partner sees breadcrumbs in Telegram naturally. Can leave breadcrumbs back with 🍞 prefix.

### WAVE 4: Drift Response Protocol (1 SP)

When the governance agent sends a drift warning, the bot should respond with REAL data, not theater.

**On drift warning detection** (message contains "DRIFT WARNING" or confidence alert):

```python
async def handle_drift_alert():
    """Respond to drift with real diagnostics, not roleplay."""
    # 1. Get actual recent vote confidence
    recent = get_recent_vote_stats(hours=24)

    # 2. Get concern eval count
    eval_count = get_active_eval_count()

    # 3. Run quick smoke test
    health = run_quick_health_check()

    # 4. Compose grounded response
    response = f"DRIFT ANALYSIS (real data, not theater):\n"
    response += f"Votes (24h): {recent['count']}, avg confidence: {recent['avg_conf']:.2f}\n"
    response += f"Reason: {recent['explanation']}\n"
    response += f"Active concern evals: {eval_count}\n"
    response += f"Cluster health: {health['pass']}/{health['total']} checks passing\n"

    if recent['avg_conf'] < 0.4 and recent['count'] > 3:
        response += "\nLow confidence is expected — heavy architectural debate today."
        response += "\nThis is healthy disagreement, not drift."

    return response
```

**Success**: Drift warnings get real diagnostics. No theatrical "calling the council to order" with fake emojis.

## Deployment Order

| Wave | What | SP | Depends On |
|------|------|-----|------------|
| 1 | Ground system prompt | 1 | Nothing — immediate |
| 2 | Wire real council vote | 2 | Wave 1 |
| 3 | Wire breadcrumb interface | 1 | Wave 1 + chirality_breadcrumbs table (exists) |
| 4 | Drift response protocol | 1 | Wave 1 + Wave 2 |

## The Meta-Lesson

This Jr instruction exists because of VISTA. The ganudabot's system prompt is the defective seed (L1). The theatrical council responses are the attribution blind spot (L2) — the real root cause (missing function calls) gets zero attribution because the bot confidently generates plausible-looking but wrong output. The fix is exactly what VISTA prescribes: identify the structural defect in the seed, rewrite targeted to that root cause, verify on real output.

The organism just used today's research to diagnose today's bug. The papers aren't abstract. They're operational.
