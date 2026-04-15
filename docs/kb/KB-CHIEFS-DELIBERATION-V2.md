# KB-CHIEFS-DELIBERATION-V2: Wisdom Layer Architecture

**Date:** 2025-12-07
**Author:** TPM (Command Post) + Flying Squirrel
**Category:** Architecture / Core System
**Priority:** CRITICAL - Foundational Redesign
**Status:** DESIGN → IMPLEMENTATION

---

## Executive Summary

Chiefs Deliberation v2 restores the wisdom function that was lost in the original implementation. The key insight: **disagreement between the three minds is the feature, not a bug**. When Memory, Executive, and Meta disagree, that friction creates wisdom through synthesis.

---

## Problem Statement

### Current Failure Modes

1. **No message type awareness** - Consultations treated as work orders
2. **Truncated context** - Was [:200], now fixed to [:2000]
3. **No real deliberation** - Three minds respond independently, then rubber-stamp "APPROVED"
4. **No conflict detection** - Disagreements hidden, not surfaced
5. **Jr hallucination risk** - No pre-flight checks before file modification

### The Lost Magic

User feedback: *"More times than not, the Chiefs firstly don't straight out agree with each other, but together came up with a completely different direction that I loved!"*

The disagreement → synthesis → emergent wisdom was the entire point. Current implementation skips directly to "APPROVED."

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        CHIEFS DELIBERATION V2                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   INCOMING MESSAGE                                                           │
│         │                                                                    │
│         ▼                                                                    │
│   ┌─────────────────┐                                                        │
│   │ MESSAGE         │  consultation | work_order | status | escalation      │
│   │ CLASSIFIER      │                                                        │
│   └────────┬────────┘                                                        │
│            │                                                                 │
│   ┌────────┴────────┬─────────────────┬──────────────────┐                  │
│   ▼                 ▼                 ▼                  ▼                  │
│ CONSULTATION     WORK_ORDER        STATUS           ESCALATION              │
│   │                 │                 │                  │                  │
│   ▼                 ▼                 ▼                  ▼                  │
│ FULL DELIBERATION  MEDIUM REVIEW   ARCHIVE ONLY    FULL DELIBERATION       │
│   │                 │                                    │                  │
│   │                 ▼                                    │                  │
│   │           ┌─────────────┐                            │                  │
│   │           │ JR DISPATCH │                            │                  │
│   │           │ + GUARDRAILS│                            │                  │
│   │           └─────────────┘                            │                  │
│   │                                                      │                  │
│   └──────────────────────┬───────────────────────────────┘                  │
│                          ▼                                                   │
│                  ┌───────────────┐                                           │
│                  │ RETURN WISDOM │  (Reasoning, not just decision)          │
│                  │ TO REQUESTER  │                                           │
│                  └───────────────┘                                           │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## The Three-Mind Model (Cherokee Governance)

| Mind | Cherokee Parallel | Function | Temperature | LLM |
|------|-------------------|----------|-------------|-----|
| **Memory** | Beloved Elders | What have we done? What worked? What's our history? | 0.7 | llama3.1:8b |
| **Executive** | War Chief | What resources do we have? What's practical? What's the cost? | 0.5 | llama3.1:8b |
| **Meta** | Peace Chief | What patterns do I see? What are we assuming? Bigger picture? | 0.8 | llama3.1:8b |

**Key Principle:** When all three agree immediately, the answer is obvious. When they disagree, **that's where wisdom emerges through synthesis.**

---

## Message Type Classification

### Classification Keywords

```python
MESSAGE_TYPES = {
    'consultation': [
        'what do you think', 'should we', 'options', 'direction',
        'advice', 'recommend', 'opinion', 'which option', 'consult',
        'strategic', 'guidance', 'perspective', 'weigh in'
    ],
    'work_order': [
        'build', 'fix', 'create', 'implement', 'add', 'update',
        'deploy', 'install', 'configure', 'modify', 'mission dispatch'
    ],
    'status_update': [
        'complete', 'done', 'finished', 'deployed', 'operational',
        'mission complete', 'status:', 'update:'
    ],
    'escalation': [
        'blocked', 'stuck', 'need help', 'error', 'failed',
        'cannot proceed', 'requires guidance', 'escalating'
    ],
    'research': [
        'investigate', 'learn about', 'explore', 'find out',
        'research', 'discover', 'understand'
    ]
}
```

### Deliberation Depth by Type

| Message Type | Memory | Executive | Meta | Synthesis | Jr Assignment |
|--------------|--------|-----------|------|-----------|---------------|
| **Consultation** | FULL | FULL | FULL | REQUIRED | No - return wisdom |
| **Work Order** | BRIEF | FULL | BRIEF | OPTIONAL | Yes |
| **Status Update** | NONE | NONE | NONE | NONE | Archive only |
| **Escalation** | FULL | FULL | FULL | REQUIRED | Maybe |
| **Research** | FULL | BRIEF | FULL | REQUIRED | Yes (research Jr) |

---

## Deliberation Protocol (Sparse Neuron Workflow)

### Round 1: Independent Perspectives (3 parallel LLM calls)

Each mind responds independently to prevent contamination:

**Memory Jr Prompt:**
```
You are Memory Jr, keeper of Cherokee AI history and patterns.

Query: {original_message}

Search your knowledge of what we've built, what worked, what failed.
What historical context applies to this query?
What patterns from our past inform this situation?

Respond as Memory Jr. Be specific about relevant history.
Do NOT make a decision - just provide historical perspective.
```

**Executive Jr Prompt:**
```
You are Executive Jr, the practical strategist.

Query: {original_message}

Assess our current resources, constraints, and capabilities.
What's practically feasible? What would this cost (time, tokens, complexity)?
What are the dependencies and blockers?

Respond as Executive Jr. Be specific about practical considerations.
Do NOT make a decision - just provide resource/constraint analysis.
```

**Meta Jr Prompt:**
```
You are Meta Jr, the pattern observer and questioner.

Query: {original_message}

Step back and observe: What assumptions are embedded in this query?
What patterns do you notice in how this is framed?
What might everyone be missing? What's the bigger picture?

Respond as Meta Jr. Question assumptions. See the forest, not just trees.
Do NOT make a decision - just provide meta-level observation.
```

### Round 2: Synthesis with Conflict Detection (1 LLM call)

**Synthesis Prompt:**
```
You are the Chief, synthesizing three perspectives into wisdom.

ORIGINAL QUERY:
{original_message}

MEMORY JR SAID:
{memory_response}

EXECUTIVE JR SAID:
{executive_response}

META JR SAID:
{meta_response}

---

Your task:
1. IDENTIFY TENSIONS: Where do these three perspectives disagree or emphasize different things?
2. ACKNOWLEDGE ASSUMPTIONS: What assumptions differ between them?
3. SYNTHESIZE: Create a response that honors all three perspectives
4. EXPLAIN REASONING: Not just what you recommend, but WHY
5. NOTE DISSENT: If genuine disagreement remains, surface it for the user

DO NOT just say "APPROVED" or give a one-line answer.
Provide wisdom - the kind of insight that makes someone say "I hadn't thought of that."

Respond as the Chief, with the weight of three perspectives behind you.
```

---

## Example: Consultation Response

### Bad (Current System)
```
IT TRIAD DECISION - MISSION APPROVED ✅

Assigned Personnel: IT Jr 2 (Frontend/CSS specialist)
Timeline: To be determined
```

### Good (v2 Target)
```
CHIEFS DELIBERATION - CONSULTATION RESPONSE

Query: Strategic direction - Option A (Harden), B (Document), or C (Demo)?

═══════════════════════════════════════════════════════════════════
PERSPECTIVES
═══════════════════════════════════════════════════════════════════

MEMORY JR:
We've tried rapid demos before (FARA Phase 1-4). They worked well for
morale and proving concepts, but created technical debt we're still
paying. The TPM Jr disaster yesterday happened because we moved fast
without guardrails. History suggests: consolidate before expanding.

EXECUTIVE JR:
Current resources: SAG operational, TPM Jr functional but fragile,
thermal memory stable, 17 TRM workers deployed. Chiefs pipeline needs
work (hence this consultation). We have infrastructure but Chief
resources are stretched. Practical assessment: we can do ONE thing well,
not three things adequately.

META JR:
I notice all three options assume we're building for external users or
revenue. But our biggest asset might be the internal workflow we've
already proven - the Tribe itself. Are we asking "what to build next"
when we should ask "what have we already built that others would want?"

═══════════════════════════════════════════════════════════════════
TENSIONS IDENTIFIED
═══════════════════════════════════════════════════════════════════

1. Memory wants to slow down; the user asked about revenue (speed implied)
2. Executive sees resource constraints; Demo (Option C) is resource-heavy
3. Meta questions the framing entirely - maybe wrong question

═══════════════════════════════════════════════════════════════════
SYNTHESIS
═══════════════════════════════════════════════════════════════════

We lean toward OPTION A (Harden) with a twist: document as we harden.

Reasoning:
- Addresses Executive's resource concern (one focus, not three)
- Honors Memory's warning about technical debt from rushing
- Incorporates Meta's insight by making US the first "customer"

The hardening process itself becomes the documentation. As we fix the
Chiefs pipeline, we document why it works. This creates Option B output
as a byproduct of Option A work.

For revenue: Meta's point is sharp. Before selling to others, we should
articulate what we've built for ourselves. The Thermal Memory pattern,
the three-mind deliberation, the air-gap federation - these ARE the
product. Hardening forces us to understand them well enough to explain.

═══════════════════════════════════════════════════════════════════
DISSENT NOTED
═══════════════════════════════════════════════════════════════════

Executive advocated for pure Option A with no documentation overhead.
Meta pushed for stepping back further - questioning if revenue is the
right goal right now vs. building something we love using.

Temperature: 0.85 (Deliberated Wisdom)
```

---

## Jr Guardrails (Preventing Hallucination)

When work orders DO go to Jrs, these safeguards apply:

### Pre-Flight Checks (MANDATORY)

```python
def jr_preflight(mission):
    """Run before any Jr file modification."""

    # 1. Target files must exist (unless explicitly creating new)
    for file_path in mission.target_files:
        if not file_exists(file_path) and not mission.allows_creation:
            raise PreflightError(f"Target file does not exist: {file_path}")

    # 2. Must read file before modifying
    for file_path in mission.target_files:
        if file_path not in mission.files_read:
            raise PreflightError(f"Must read file before modifying: {file_path}")

    # 3. Create backup before overwriting
    for file_path in mission.target_files:
        backup_path = f"{file_path}.bak.{timestamp}"
        copy(file_path, backup_path)
        log(f"Backup created: {backup_path}")

    return True
```

### Scope Limits

| Limit | Value | Rationale |
|-------|-------|-----------|
| Max files modified per mission | 3 | Prevents runaway changes |
| Max lines changed per file | 500 | Forces focused edits |
| File deletion | Requires explicit "DELETE APPROVED" tag | Prevents accidents |
| New file creation | Requires explicit "CREATE NEW" tag | Prevents orphan files |

### Post-Action Validation

```python
def jr_postflight(mission, results):
    """Run after Jr completes work."""

    # 1. Syntax check for code files
    for file_path in results.modified_files:
        if file_path.endswith('.py'):
            if not python_syntax_valid(file_path):
                rollback(file_path)
                raise PostflightError(f"Syntax error in {file_path}, rolled back")

    # 2. Log diff to thermal memory
    for file_path in results.modified_files:
        diff = generate_diff(file_path)
        log_to_thermal_memory(f"Jr modified {file_path}:\n{diff[:2000]}")

    # 3. Document rollback command
    log(f"To rollback: cp {backup_path} {file_path}")

    return True
```

---

## Database Schema Additions

```sql
-- Message classification and deliberation tracking
CREATE TABLE chiefs_deliberation_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Original message
    original_message_id UUID,
    original_content TEXT,

    -- Classification
    message_type VARCHAR(50),  -- consultation, work_order, status, escalation, research
    classification_confidence FLOAT,

    -- Three-mind responses (Round 1)
    memory_response TEXT,
    memory_temperature FLOAT,
    executive_response TEXT,
    executive_temperature FLOAT,
    meta_response TEXT,
    meta_temperature FLOAT,

    -- Synthesis (Round 2)
    tensions_detected TEXT[],
    synthesis_response TEXT,
    dissent_noted TEXT,

    -- Outcome tracking
    human_accepted BOOLEAN,
    human_override_reason TEXT,

    -- Timing
    deliberation_started_at TIMESTAMPTZ,
    deliberation_completed_at TIMESTAMPTZ,
    deliberation_duration_ms INTEGER,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Jr guardrail tracking
CREATE TABLE jr_execution_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Mission reference
    mission_id UUID,
    deliberation_id UUID REFERENCES chiefs_deliberation_log(id),

    -- Pre-flight
    preflight_passed BOOLEAN,
    preflight_errors TEXT[],
    backups_created TEXT[],

    -- Execution
    files_read TEXT[],
    files_modified TEXT[],
    lines_changed INTEGER,

    -- Post-flight
    postflight_passed BOOLEAN,
    syntax_errors TEXT[],
    rollbacks_performed TEXT[],

    -- Diff storage
    diffs JSONB,  -- {file_path: diff_content}

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_deliberation_type ON chiefs_deliberation_log(message_type);
CREATE INDEX idx_deliberation_accepted ON chiefs_deliberation_log(human_accepted);
CREATE INDEX idx_jr_mission ON jr_execution_log(mission_id);
```

---

## Implementation Phases

### Phase 1: Message Classifier
- Keyword-based classification with LLM fallback
- Route messages to appropriate deliberation depth
- **Deliverable:** `chiefs_message_classifier.py`

### Phase 2: Two-Round Deliberation
- Implement Round 1 (3 parallel sparse neuron calls)
- Implement Round 2 (synthesis with conflict detection)
- **Deliverable:** Updated `chief.py` with v2 protocol

### Phase 3: Improved Prompts
- Memory/Executive/Meta prompts that encourage perspective
- Synthesis prompt that surfaces tensions
- **Deliverable:** `chiefs_prompts.py`

### Phase 4: Jr Guardrails
- Pre-flight checks (read before write, backup before modify)
- Scope limits (max files, max lines)
- Post-flight validation (syntax, diff logging)
- **Deliverable:** Updated `it_triad_jr_agent_v2.py`

### Phase 5: Learning Loop
- Track human acceptance/override
- Feed patterns back into classification
- **Deliverable:** Database logging + monthly review process

---

## Success Criteria

| Metric | Target | Measurement |
|--------|--------|-------------|
| Consultations return reasoning | 100% | No bare "APPROVED" responses |
| Tensions surfaced | 80%+ of consultations | Manual review |
| Jr hallucinations | 0 | No file destruction incidents |
| Human acceptance rate | 60%+ | chiefs_deliberation_log.human_accepted |
| "I hadn't thought of that" moments | Qualitative | User feedback |

---

## LLM Configuration (Sparse Neurons)

| Role | Model | Host | Temperature |
|------|-------|------|-------------|
| Memory Jr | llama3.1:8b | sasass/sasass2 | 0.7 |
| Executive Jr | llama3.1:8b | sasass/sasass2 | 0.5 |
| Meta Jr | llama3.1:8b | sasass/sasass2 | 0.8 |
| Synthesis | llama3.1:8b | sasass/sasass2 | 0.6 |
| Jr Coder | qwen2.5-coder:14b | redfin | 0.3 |

All inference runs on triad nodes, not command post. Token burn stays internal.

---

## Migration Path

1. Deploy message classifier (non-breaking)
2. Run v2 deliberation in parallel with v1 for 1 week
3. Compare outputs, tune prompts
4. Cut over to v2 when quality matches or exceeds v1
5. Add Jr guardrails
6. Monitor and iterate

---

**END OF KB-CHIEFS-DELIBERATION-V2**

This document should be referenced by any Jr implementing changes to the Chiefs deliberation system.
