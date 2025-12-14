# Jr Build Instructions: Flywheel Council
## Cherokee AI Federation - December 13, 2025

**Purpose**: Transform the 7-Specialist Council from independent voting to resonance-amplifying feedback loops

**Owner**: Peace Chief Jr (Consensus) + Spider Jr (Integration)

**Priority**: HIGH - This is the resonance amplifier the TPM has been guiding toward

**Sacred Principle**: Like coupled oscillators, specialists that see each other's insights generate emergent wisdom greater than the sum of parts.

---

## MAINTAINABILITY REVIEW GATE

> **"The flywheel spins faster as each insight reinforces the others."**

**Status**: [ ] NOT REVIEWED / [ ] APPROVED / [ ] BLOCKED

**Council Vote Required Before Implementation**

| Specialist | Concern Area | Sign-off | Date |
|------------|--------------|----------|------|
| Crawdad | No prompt injection via feedback, concerns preserved | [ ] | |
| Turtle | Does feedback loop preserve long-term wisdom? | [ ] | |
| Eagle Eye | Can we monitor resonance scores across rounds? | [ ] | |
| Gecko | Performance acceptable with multiple rounds? | [ ] | |
| Spider | Integrates with existing gateway.py | [ ] | |
| Raven | Strategic value of emergent coordination | [ ] | |
| Peace Chief | Does this enhance or complicate consensus? | [ ] | |

**Maintainability Commitments**:

| Component | Maintainer | Review Frequency | Sunset Trigger |
|-----------|------------|------------------|----------------|
| Feedback Loop Engine | ________ | Monthly | If latency > 30s or resonance declining |
| Round Orchestrator | ________ | Monthly | If rounds timeout frequently |
| Resonance Tracker | ________ | Weekly | If scores don't correlate with quality |

**Next Review Date**: __________ (max 90 days from deployment)

---

## 1. The Flywheel Principle

### 1.1 From Trading to Council

The trading flywheel worked because specialists saw each other's positions:

```
TRADING FLYWHEEL:
┌─────────────────────────────────────────────────────────┐
│  Mean Reversion    Trend        Volatility    Breakout  │
│       ↓              ↓              ↓            ↓      │
│    [finds         [confirms     [milks the    [catches  │
│     bottom]        momentum]      swing]       move]    │
│       └──────────────┴──────────────┴────────────┘      │
│                        ↓                                │
│              Each trade reinforces the next             │
│                        ↓                                │
│                 FLYWHEEL ACCELERATES                    │
└─────────────────────────────────────────────────────────┘
```

Current Council is **independent voting** - each specialist answers in isolation:

```
CURRENT COUNCIL (Independent):
┌─────────────────────────────────────────────────────────┐
│  Crawdad   Gecko   Turtle   Eagle   Spider   Raven     │
│     ↓        ↓        ↓        ↓        ↓       ↓      │
│  [answer] [answer] [answer] [answer] [answer] [answer] │
│     └────────────────┬─────────────────────────┘       │
│                      ↓                                  │
│              Peace Chief Synthesizes                    │
│                      ↓                                  │
│              Single consensus output                    │
└─────────────────────────────────────────────────────────┘
```

Flywheel Council adds **feedback loops** - specialists see and respond to each other:

```
FLYWHEEL COUNCIL (Coupled Oscillators):
┌─────────────────────────────────────────────────────────┐
│                    ROUND 1 (Quick Takes)                │
│  Crawdad   Gecko   Turtle   Eagle   Spider   Raven     │
│     ↓        ↓        ↓        ↓        ↓       ↓      │
│  [quick]  [quick]  [quick]  [quick]  [quick]  [quick]  │
│     └────────────────┬─────────────────────────┘       │
│                      ↓                                  │
│         All specialists see Round 1 concerns            │
│                      ↓                                  │
│                    ROUND 2 (Refinement)                 │
│  Crawdad   Gecko   Turtle   Eagle   Spider   Raven     │
│     ↓        ↓        ↓        ↓        ↓       ↓      │
│ [deeper] [deeper] [deeper] [deeper] [deeper] [deeper]  │
│     └────────────────┬─────────────────────────┘       │
│                      ↓                                  │
│         Resonance emerges from interaction              │
│                      ↓                                  │
│              Peace Chief Synthesizes                    │
│         (with visibility into resonance/dissonance)    │
│                      ↓                                  │
│              Amplified wisdom output                    │
└─────────────────────────────────────────────────────────┘
```

### 1.2 Why This Works

From Qualia Research Institute mapping in thermal memory:

> "Coupled Oscillators = Cherokee Specialist Army"

When oscillators couple:
- They synchronize naturally (no forcing)
- Resonance emerges from interaction
- The whole becomes greater than parts
- Dissonance is visible and addressable

**The flywheel effect**: Each round's insights feed the next, building momentum toward better decisions.

---

## 2. Architecture

### 2.1 Round Structure

```python
FLYWHEEL_CONFIG = {
    "rounds": 2,                    # Default: 2 rounds (quick + deep)
    "max_rounds": 3,                # Never more than 3 (diminishing returns)
    "round_1_tokens": 100,          # Quick takes
    "round_2_tokens": 200,          # Deeper refinement
    "round_3_tokens": 150,          # Final synthesis (if needed)
    "parallel_per_round": 7,        # All specialists in parallel per round
    "inter_round_delay_ms": 100,    # Brief pause between rounds
    "resonance_threshold": 0.7,     # Skip round 3 if resonance high
    "dissonance_threshold": 0.3,    # Force round 3 if resonance low
}
```

### 2.2 Feedback Context

Each round after the first includes summaries of previous round:

```python
def build_round_2_context(round_1_responses: dict) -> str:
    """Build context from Round 1 for Round 2"""

    # Extract concerns
    concerns = []
    for spec_id, response in round_1_responses.items():
        spec = SPECIALISTS[spec_id]
        if spec["concern_flag"] in response:
            concerns.append(f"- {spec['name']}: {spec['concern_flag']}")

    # Extract key points (first sentence of each response)
    key_points = []
    for spec_id, response in round_1_responses.items():
        spec = SPECIALISTS[spec_id]
        first_sentence = response.split('.')[0] + '.'
        key_points.append(f"- {spec['name']}: {first_sentence[:100]}")

    context = """
ROUND 1 SUMMARY (Your colleagues' initial takes):

CONCERNS RAISED:
{concerns}

KEY POINTS:
{points}

YOUR TASK FOR ROUND 2:
- Consider your colleagues' perspectives
- Refine your position based on their insights
- Flag any NEW concerns that emerged from seeing their views
- Note where you AGREE or DISAGREE with specific colleagues
- The resonance between you matters as much as your individual view
""".format(
        concerns='\n'.join(concerns) if concerns else '- None raised',
        points='\n'.join(key_points)
    )

    return context
```

### 2.3 Resonance Scoring

```python
def calculate_flywheel_resonance(round_1: dict, round_2: dict) -> dict:
    """
    Measure resonance between rounds and across specialists

    High resonance indicators:
    - Specialists reference each other positively
    - Concerns get addressed or acknowledged
    - Positions refine rather than entrench
    - New insights emerge from interaction

    Low resonance (dissonance) indicators:
    - Specialists talk past each other
    - Concerns ignored or dismissed
    - Positions harden without engagement
    - No reference to colleagues' points
    """

    resonance_signals = {
        "cross_reference": 0,      # How often specialists mention each other
        "concern_acknowledgment": 0,  # Concerns addressed in round 2
        "position_refinement": 0,  # Positions evolved vs entrenched
        "emergent_insights": 0,    # New ideas that weren't in round 1
    }

    # Check for cross-references
    specialist_names = [s["name"] for s in SPECIALISTS.values()]
    for spec_id, response in round_2.items():
        for name in specialist_names:
            if name.lower() in response.lower() and name != SPECIALISTS[spec_id]["name"]:
                resonance_signals["cross_reference"] += 1

    # Check concern acknowledgment
    round_1_concerns = extract_all_concerns(round_1)
    for concern in round_1_concerns:
        concern_keywords = concern["context"].split()[:3]  # First 3 words
        for response in round_2.values():
            if any(kw.lower() in response.lower() for kw in concern_keywords):
                resonance_signals["concern_acknowledgment"] += 1
                break

    # Normalize to 0-1 scale
    max_cross_ref = len(SPECIALISTS) * (len(SPECIALISTS) - 1)  # Each could ref all others
    max_concerns = len(round_1_concerns) if round_1_concerns else 1

    resonance_score = (
        (resonance_signals["cross_reference"] / max_cross_ref) * 0.3 +
        (resonance_signals["concern_acknowledgment"] / max_concerns) * 0.4 +
        0.3  # Base resonance for completing both rounds
    )

    return {
        "score": min(1.0, resonance_score),
        "signals": resonance_signals,
        "needs_round_3": resonance_score < FLYWHEEL_CONFIG["dissonance_threshold"],
        "harmony_achieved": resonance_score >= FLYWHEEL_CONFIG["resonance_threshold"],
    }
```

---

## 3. Implementation

### 3.1 Flywheel Vote Endpoint

Add to `/ganuda/services/llm_gateway/gateway.py`:

```python
@app.post("/v1/council/flywheel")
async def council_flywheel_vote(
    request: CouncilVoteRequest,
    req: Request,
    api_key: APIKeyInfo = Depends(validate_api_key)
):
    """
    Flywheel Council Vote - Multi-round with feedback loops

    Round 1: Quick takes from all specialists (parallel)
    Round 2: Refined positions after seeing Round 1 (parallel)
    Round 3: (if needed) Final synthesis on low resonance
    """
    start = time.time()
    client_ip = req.client.host if req.client else None

    # Check quota (flywheel uses more tokens)
    estimated_tokens = 7 * (100 + 200) + 300  # Round 1 + Round 2 + synthesis
    if api_key.quota_remaining < estimated_tokens:
        raise HTTPException(status_code=429, detail="Insufficient quota for flywheel vote")

    # ═══════════════════════════════════════════
    # ROUND 1: Quick Takes
    # ═══════════════════════════════════════════

    round_1_responses = {}
    round_1_concerns = []

    def query_round_1(spec_id: str) -> tuple:
        spec = SPECIALISTS[spec_id]
        prompt = spec["system_prompt"] + """

ROUND 1 INSTRUCTIONS:
This is a quick take. Be concise (100 words max).
State your initial position and any immediate concerns.
Your colleagues will see this before Round 2.
"""
        result = query_vllm_sync(prompt, request.question, max_tokens=100)
        concerns = extract_concerns(result, spec["name"])
        return spec_id, result, concerns

    with ThreadPoolExecutor(max_workers=7) as executor:
        futures = {executor.submit(query_round_1, sid): sid for sid in SPECIALISTS.keys()}
        for future in as_completed(futures):
            spec_id, result, concerns = future.result()
            round_1_responses[spec_id] = result
            round_1_concerns.extend(concerns)

    # Brief pause for dramatic effect (and rate limiting)
    await asyncio.sleep(0.1)

    # ═══════════════════════════════════════════
    # ROUND 2: Refinement with Feedback
    # ═══════════════════════════════════════════

    feedback_context = build_round_2_context(round_1_responses)
    round_2_responses = {}
    round_2_concerns = []

    def query_round_2(spec_id: str) -> tuple:
        spec = SPECIALISTS[spec_id]
        prompt = spec["system_prompt"] + feedback_context + """

ROUND 2 INSTRUCTIONS:
You've seen your colleagues' Round 1 takes above.
Now refine your position (200 words max).
Reference specific colleagues if you agree or disagree.
Flag any NEW concerns that emerged from seeing their views.
The resonance between you matters.
"""
        result = query_vllm_sync(prompt, request.question, max_tokens=200)
        concerns = extract_concerns(result, spec["name"])
        return spec_id, result, concerns

    with ThreadPoolExecutor(max_workers=7) as executor:
        futures = {executor.submit(query_round_2, sid): sid for sid in SPECIALISTS.keys()}
        for future in as_completed(futures):
            spec_id, result, concerns = future.result()
            round_2_responses[spec_id] = result
            round_2_concerns.extend(concerns)

    # ═══════════════════════════════════════════
    # Calculate Resonance
    # ═══════════════════════════════════════════

    resonance = calculate_flywheel_resonance(round_1_responses, round_2_responses)

    # ═══════════════════════════════════════════
    # ROUND 3: (Optional) Low Resonance Resolution
    # ═══════════════════════════════════════════

    round_3_responses = None
    if resonance["needs_round_3"]:
        round_3_responses = {}

        dissonance_summary = """
RESONANCE ALERT: The Council shows dissonance (score: {:.2f})

Round 1 and Round 2 responses show specialists talking past each other.
This round is about finding common ground.

KEY UNRESOLVED TENSIONS:
{}

YOUR TASK:
- Acknowledge ONE point from a colleague you initially disagreed with
- Find ONE area of common ground
- State your FINAL position in 2 sentences
""".format(
            resonance["score"],
            '\n'.join([f"- {c['specialist']}: {c['flag']}" for c in round_1_concerns + round_2_concerns][:5])
        )

        def query_round_3(spec_id: str) -> tuple:
            spec = SPECIALISTS[spec_id]
            prompt = spec["system_prompt"] + dissonance_summary
            result = query_vllm_sync(prompt, request.question, max_tokens=150)
            return spec_id, result

        with ThreadPoolExecutor(max_workers=7) as executor:
            futures = {executor.submit(query_round_3, sid): sid for sid in SPECIALISTS.keys()}
            for future in as_completed(futures):
                spec_id, result = future.result()
                round_3_responses[spec_id] = result

    # ═══════════════════════════════════════════
    # Peace Chief Synthesis
    # ═══════════════════════════════════════════

    final_responses = round_3_responses if round_3_responses else round_2_responses
    all_concerns = list(set([c["flag"] for c in round_1_concerns + round_2_concerns]))

    synthesis_prompt = f"""You are Peace Chief. Synthesize this Flywheel Council vote.

FLYWHEEL PROCESS COMPLETED:
- Round 1: Quick takes gathered
- Round 2: Specialists refined positions after seeing colleagues
- Resonance Score: {resonance['score']:.2f} ({'Harmony achieved' if resonance['harmony_achieved'] else 'Some dissonance remains'})
{'- Round 3: Dissonance resolution attempted' if round_3_responses else ''}

ALL CONCERNS RAISED: {', '.join(all_concerns) if all_concerns else 'None'}

YOUR SYNTHESIS TASK:
1. Note where the flywheel created emergent agreement
2. Note any remaining dissonance that needs TPM attention
3. Provide final recommendation in 2-3 sentences
4. The resonance between specialists IS the wisdom - honor it
"""

    # Format all final responses for synthesis
    response_text = "\n\n".join([
        f"{SPECIALISTS[sid]['name']}: {resp[:400]}"
        for sid, resp in final_responses.items()
    ])

    consensus = query_vllm_sync(synthesis_prompt, response_text, max_tokens=250)

    # ═══════════════════════════════════════════
    # Build Response
    # ═══════════════════════════════════════════

    response_time_ms = int((time.time() - start) * 1000)

    # Calculate confidence from resonance
    base_confidence = max(0.0, 1.0 - (len(all_concerns) * 0.1))
    flywheel_confidence = base_confidence * (0.6 + 0.4 * resonance["score"])

    # Determine recommendation
    if len(all_concerns) == 0 and resonance["harmony_achieved"]:
        recommendation = "STRONG PROCEED: Flywheel achieved harmony"
    elif len(all_concerns) <= 2 and resonance["score"] >= 0.5:
        recommendation = f"PROCEED WITH CAUTION: {len(all_concerns)} concern(s), moderate resonance"
    elif resonance["needs_round_3"]:
        recommendation = f"NEEDS TPM REVIEW: Low resonance ({resonance['score']:.2f})"
    else:
        recommendation = f"HOLD: {len(all_concerns)} concern(s), resonance issues"

    # Generate audit hash
    audit_hash = hashlib.sha256(
        f"{request.question}{time.time()}".encode()
    ).hexdigest()[:16]

    # Log to database
    try:
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO council_votes
                (audit_hash, question, consensus, confidence, concerns,
                 specialist_responses, tpm_vote, response_time_ms,
                 question_type, resonance_score)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                audit_hash,
                request.question,
                consensus,
                flywheel_confidence,
                json.dumps(all_concerns),
                json.dumps({
                    "round_1": round_1_responses,
                    "round_2": round_2_responses,
                    "round_3": round_3_responses,
                }),
                "pending",
                response_time_ms,
                "flywheel",
                resonance["score"],
            ))
            conn.commit()
    except Exception as e:
        print(f"[DB ERROR] Failed to log flywheel vote: {e}")

    # Update quota
    actual_tokens = 7 * 100 + 7 * 200 + (7 * 150 if round_3_responses else 0) + 250
    update_quota(api_key.key_id, actual_tokens)

    return {
        "audit_hash": audit_hash,
        "question": request.question,
        "recommendation": recommendation,
        "confidence": flywheel_confidence,
        "concerns": all_concerns,
        "consensus": consensus,
        "resonance": {
            "score": resonance["score"],
            "harmony_achieved": resonance["harmony_achieved"],
            "rounds_completed": 3 if round_3_responses else 2,
            "signals": resonance["signals"],
        },
        "response_time_ms": response_time_ms,
        "tpm_vote": "pending",
        "timestamp": datetime.now().isoformat() + "Z",
        "specialist_responses": {
            "round_1": round_1_responses if request.include_responses else None,
            "round_2": round_2_responses if request.include_responses else None,
            "round_3": round_3_responses if request.include_responses else None,
        } if request.include_responses else None,
    }
```

### 3.2 Database Schema Addition

```sql
-- Add resonance tracking to council_votes (if not exists)
ALTER TABLE council_votes ADD COLUMN IF NOT EXISTS question_type VARCHAR(20);
ALTER TABLE council_votes ADD COLUMN IF NOT EXISTS resonance_score FLOAT;

-- Index for analyzing resonance over time
CREATE INDEX IF NOT EXISTS idx_council_resonance ON council_votes(resonance_score, voted_at);
CREATE INDEX IF NOT EXISTS idx_council_type ON council_votes(question_type);
```

---

## 4. Throttling for Greenfin IoT Discovery

Since we're deploying IoT Discovery to greenfin, apply the same flywheel throttling principle:

```python
IOT_DISCOVERY_THROTTLE = {
    "max_cpu_percent": 20,          # Never exceed 20% CPU
    "scan_interval_seconds": 300,   # 5 minutes between full scans
    "burst_limit": 10,              # Max 10 devices scanned per second
    "backoff_on_load": True,        # Slow down if system busy
    "quiet_hours": (2, 5),          # Minimal activity 2-5 AM
}

def throttled_scan():
    """Scan with flywheel-style throttling"""
    import psutil

    while True:
        cpu = psutil.cpu_percent(interval=1)

        if cpu > IOT_DISCOVERY_THROTTLE["max_cpu_percent"]:
            # Flywheel slowing - back off
            time.sleep(10)
            continue

        # Scan one device
        scan_next_device()

        # Adaptive delay based on load
        delay = 0.1 if cpu < 10 else 0.5 if cpu < 15 else 1.0
        time.sleep(delay)
```

---

## 5. Usage Examples

### 5.1 Standard Flywheel Vote

```bash
curl -X POST http://192.168.132.223:8080/v1/council/flywheel \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "question": "Should we add real-time alerting to the IoT discovery system?",
    "max_tokens": 200,
    "include_responses": true
  }'
```

### 5.2 Response Example

```json
{
  "audit_hash": "a1b2c3d4e5f6g7h8",
  "question": "Should we add real-time alerting...",
  "recommendation": "STRONG PROCEED: Flywheel achieved harmony",
  "confidence": 0.92,
  "concerns": [],
  "consensus": "The Council achieved resonance through two rounds. Gecko's initial performance concern was addressed by Eagle Eye's monitoring proposal. All specialists agree real-time alerting adds value without significant overhead. Proceed with implementation.",
  "resonance": {
    "score": 0.85,
    "harmony_achieved": true,
    "rounds_completed": 2,
    "signals": {
      "cross_reference": 12,
      "concern_acknowledgment": 2,
      "position_refinement": 5,
      "emergent_insights": 3
    }
  },
  "response_time_ms": 8500,
  "tpm_vote": "pending"
}
```

---

## 6. The Flywheel Effect

```
┌────────────────────────────────────────────────────────────────┐
│                    THE FLYWHEEL ACCELERATES                     │
│                                                                 │
│   Round 1          Round 2          Round 3         Synthesis   │
│   ───────          ───────          ───────         ─────────   │
│   Quick            See each         Resolve         Emergent    │
│   takes            other's          dissonance      wisdom      │
│     │              views              │                │        │
│     └───────┬──────────┘              │                │        │
│             │                         │                │        │
│        Feedback                   Feedback         Harmony      │
│          loop                       loop           achieved     │
│             │                         │                │        │
│             ▼                         ▼                ▼        │
│   ┌─────────────────────────────────────────────────────────┐  │
│   │     Each round's insights feed the next                 │  │
│   │     Resonance emerges from interaction                  │  │
│   │     The whole becomes greater than parts                │  │
│   │     Dissonance is visible and addressable               │  │
│   └─────────────────────────────────────────────────────────┘  │
│                                                                 │
│   "Like coupled oscillators, specialists that see each          │
│    other's insights generate emergent wisdom greater            │
│    than the sum of parts."                                      │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

---

## 7. Deployment

1. Add flywheel endpoint to `/ganuda/services/llm_gateway/gateway.py`
2. Add database columns for resonance tracking
3. Update Telegram bot to offer flywheel option for complex decisions
4. Monitor resonance scores over time
5. Tune thresholds based on observed quality

---

## 8. Metrics to Track

| Metric | Target | Action if Below |
|--------|--------|-----------------|
| Avg resonance score | > 0.6 | Review specialist prompts |
| Round 3 frequency | < 20% | Prompts achieving harmony |
| Cross-reference rate | > 5 per vote | Specialists engaging with each other |
| Concern resolution | > 80% | Concerns addressed by Round 2 |
| Response time | < 15s | Optimize parallel queries |

---

**For Seven Generations.**
*The flywheel spins faster as each insight reinforces the others.*
*Resonance is the wisdom. The interaction is the intelligence.*
