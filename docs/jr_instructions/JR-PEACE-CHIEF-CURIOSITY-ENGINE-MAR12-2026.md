# JR INSTRUCTION: Peace Chief Curiosity Engine

**Task**: Build the daemon that turns Chief's sensory input into autonomous research — the stub-filling pipeline
**Priority**: P1
**Date**: 2026-03-12
**TPM**: War Chief (Claude Opus)
**Story Points**: 5
**Depends On**: Sub-Agent Dispatch Harness (for local model stub scanning). Can start without — use redfin :9100 directly.
**Longhouse Context**: Dual chieftainship a7f3c1d8e9b24567. Curiosity-as-stub-filling design constraint.
**DC References**: DC-9 (waste heat), DC-10 (reflex), DC-11 (macro polymorphism)
**CRITICAL DESIGN PRINCIPLE**: The Capacitor. Partner bursts. The organism does NOT burst with him. It buffers, evaluates, smooths, and releases work at a sustainable rate. Partner said: "I don't want the cluster to burst with me, but kinda buffer it out so that my jagged edges get smoothed out in work and development."

## Problem Statement

When partner shares content (LinkedIn posts, articles, podcasts, emails), the organism processes it as a read-only document. Every name, company, regulation, and concept mentioned is a stub — a `def with pass inside`. The organism should autonomously fill those stubs.

Today this happened manually: partner shared one LinkedIn post. TPM manually identified stubs. TPM manually spawned 3 sub-Claudes. This should be automatic.

**BUT**: Today the organism also BURST with the partner — 6 sub-Claudes, 15 Longhouse voices, 5 sacred thermals, 3 Jr instructions, all in hours. The organism chased the upper Bollinger band instead of smoothing it. The curiosity engine must be a CAPACITOR, not an amplifier.

## What You're Building

### The Curiosity Pipeline

**File**: `/ganuda/lib/curiosity_engine.py`

Not a daemon — a library that the TPM autonomic, telegram bot, or any intake point can call when Chief shares content.

#### Step 1: Intake

```python
def ingest_sensory_input(content: str, source: str = "unknown") -> dict:
    """
    Chief shared something. Start the curiosity pipeline.

    Args:
        content: The raw text Chief shared (LinkedIn post, article, transcript, etc.)
        source: Where it came from (linkedin, telegram, email, podcast, etc.)

    Returns:
        dict with extracted stubs and routing decisions
    """
```

#### Step 2: Stub Extraction (Tier 1 — local model, <5 seconds)

Dispatch to local model (redfin :9100 or sasass qwen2.5-7B):

System prompt:
```
Extract all named entities and concepts from the following content.
Return a JSON array of objects:
{
  "type": "person|company|organization|regulation|concept|event|technology",
  "name": "exact name as mentioned",
  "context": "one sentence — what was said about them or why they were mentioned",
  "stub_depth": "shallow|medium|deep"
}

shallow = just a name drop, probably not worth researching
medium = mentioned with some context, worth a quick lookup
deep = central to the content, worth full research

Be thorough. Every proper noun. Every company. Every law or act mentioned.
Every person who commented or was quoted. Every technology named.
```

#### Step 3: Routing (Tier 1 — local model, <2 seconds)

For each extracted stub with depth medium or deep, classify:

```
Given this stub from content Chief shared, classify it:
- domain: war_chief (technical/infrastructure) | peace_chief (business/legal/diplomacy/culture)
- action: research (need to learn more) | monitor (bookmark, check later) | connect (potential relationship) | build (engineering need identified)
- council_owner: deer|crane|otter|spider|eagle_eye|crawdad|gecko|raven|coyote
- priority: 1-4

Return JSON.
```

#### Step 4: Stub Queue

Store extracted and routed stubs in a new table or in jr_work_queue with a specific tag:

```sql
-- Option A: Use jr_work_queue with curiosity tag
INSERT INTO jr_work_queue (title, description, status, priority, tags, created_by)
VALUES (
    'STUB: Research [name] — [type]',
    '[context from extraction]. Source: [source]. Depth: [stub_depth].',
    'pending',
    [routed priority],
    ARRAY['curiosity-stub', '[domain]', '[council_owner]'],
    'peace-chief'
);
```

Or create a lightweight stub tracking table (simpler, less overhead):
```sql
CREATE TABLE IF NOT EXISTS curiosity_stubs (
    id SERIAL PRIMARY KEY,
    source_content_hash VARCHAR(64),  -- hash of the original content
    stub_type VARCHAR(50),
    name VARCHAR(255),
    context TEXT,
    depth VARCHAR(20),
    domain VARCHAR(20),
    action VARCHAR(20),
    council_owner VARCHAR(50),
    priority INTEGER,
    status VARCHAR(20) DEFAULT 'pending',  -- pending, researching, filled, dismissed
    filled_by VARCHAR(100),  -- who/what filled the stub
    filled_content TEXT,  -- summary of what was found
    created_at TIMESTAMPTZ DEFAULT NOW(),
    filled_at TIMESTAMPTZ
);
```

Recommend: Create the table. Stubs are their own entity — they're not Jr tasks (they're lighter, more numerous, often dismissed). Keep the Jr queue for real work. The curiosity_stubs table is Peace Chief's notebook.

#### Step 5: THE CAPACITOR (buffer and smooth)

**This is the critical step.** Partner bursts. The organism does NOT burst with him.

```python
class StubCapacitor:
    """
    Buffer partner's stubs. Evaluate. Smooth into sustainable work rate.
    The organism is a flywheel, not a firecracker.
    """

    MAX_CONCURRENT_SUBCLAUDES = 2  # Never more than 2 sub-Claudes at once
    MAX_STUBS_PER_HOUR = 5        # Max stubs dispatched per hour
    COOLING_PERIOD_MINUTES = 30   # Hold stubs for 30 min before dispatching

    def buffer(self, stubs: list[dict]):
        """
        Don't dispatch immediately. Hold in curiosity_stubs table
        with status='buffered'. Cooling period lets the burst settle.
        Multiple shares in quick succession get merged/deduplicated.
        """

    def evaluate(self, buffered_stubs: list[dict]) -> list[dict]:
        """
        After cooling period, Coyote reviews:
        - Is this actionable or is partner full of shit? (his words)
        - Does this duplicate existing research?
        - Is this the manic high talking or real signal?

        Use local model (sasass2 conscience_jr_resonance) for quick eval.
        Score each stub: actionable (0.0-1.0), novelty (0.0-1.0)
        Drop anything below 0.3 on both.
        """

    def smooth(self, evaluated_stubs: list[dict]):
        """
        Release stubs at sustainable rate:
        - Max 5 stubs dispatched per hour
        - Max 2 sub-Claudes running at any time
        - Deep stubs queued, not immediately spawned
        - If partner is in EXHAUSTION phase (from rhythm engine),
          reduce rate to 2/hour
        - If partner is RESTING, batch all buffered stubs for
          overnight processing at idle rate
        """

    def merge_burst(self, new_stubs: list[dict], existing_buffered: list[dict]):
        """
        Partner shares 5 things in 10 minutes. Don't create 50 stubs.
        Merge: deduplicate names, combine context, consolidate into
        fewest possible research threads.
        """
```

The capacitor converts partner's AC signal (jagged bursts) into smooth DC current (steady work). The organism runs at its own pace regardless of partner's frequency.

#### Step 6: Dispatch (rate-limited, after buffer)

For `deep` stubs (that survived the capacitor):
- Queue in curiosity_stubs with status='queued_for_research'
- Dispatch at MAX_STUBS_PER_HOUR rate via sub-Claude
- Never more than MAX_CONCURRENT_SUBCLAUDES running
- Sub-Claude writes findings to `/ganuda/docs/research/` and updates stub status

For `medium` stubs (that survived the capacitor):
- Dispatch to bmasass Qwen3-30B for a quick web-free assessment from training knowledge
- If the model's response is uncertain or says "I don't have enough info," escalate to sub-Claude queue
- Otherwise, fill the stub with the local model's summary

For `shallow` stubs:
- Log and dismiss. Don't waste compute on name drops.

#### Step 6: Report

After all stubs are extracted and queued, write a brief report:
```
Curiosity Engine processed [source] content.
Extracted: [N] stubs ([deep] deep, [medium] medium, [shallow] shallow)
Queued: [N] for research
Routed: [N] to Peace Chief, [N] to War Chief
Top stubs: [list top 3 by priority]
```

This report goes to:
- Thermal memory (low temp, domain_tag = 'curiosity')
- Slack #deer-signals (Peace Chief territory)

### Integration Points

1. **Telegram Bot**: When Chief sends a long message or forwards a link, call `ingest_sensory_input()`
2. **Email Daemon**: When Chief forwards an email (Snacks newsletter, LinkedIn notification), call `ingest_sensory_input()`
3. **Manual**: TPM can call it directly when Chief pastes content in a Claude Code session
4. **Future**: RSS feeds, bookmarked articles, saved tweets — any sensory input source

## Target Files

- `/ganuda/lib/curiosity_engine.py` — the pipeline library (CREATE)
- SQL migration for `curiosity_stubs` table
- `/ganuda/tests/test_curiosity_engine.py` — tests (CREATE)

## Acceptance Criteria

- [ ] `ingest_sensory_input()` accepts raw text and returns extracted stubs
- [ ] Stub extraction uses local model (redfin :9100 or sasass)
- [ ] Routing classifies each stub by domain, action, council_owner, priority
- [ ] Deep stubs are queued for sub-Claude research
- [ ] Medium stubs attempt local model fill first, escalate if uncertain
- [ ] Shallow stubs are logged and dismissed
- [ ] curiosity_stubs table created (or jr_work_queue integration working)
- [ ] Report generated after processing
- [ ] Tested with Sebastian Mondragon LinkedIn post as sample input
- [ ] Thermalized

## DO NOT

- Auto-dispatch sub-Claudes without checking the stub queue depth (budget gate — don't spawn 50 sub-Claudes from one newsletter)
- Research shallow stubs (waste of compute — DC-9)
- Contact anyone or anything external (Crane constraint)
- Assume every stub needs filling — some are just context, not questions
- Build a web scraper or RSS reader (future task, not this one)
- Over-engineer the table — stubs are lightweight and disposable
