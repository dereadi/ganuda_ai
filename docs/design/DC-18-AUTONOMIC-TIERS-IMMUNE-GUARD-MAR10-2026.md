# DC-18: Autonomic Tiers with Immune Guard

**Design Constraint 18** | **Status**: ADAPT (Long Man Method)
**Author**: TPM | **Date**: 2026-03-10
**Council Vote**: #42c3f20ad1f7143c (0.55, APPROVED WITH CONDITIONS)
**Sacred Thermal**: #122514 (temp 95)
**Cherokee Name**: ᎠᏓᏅᏙ ᎤᏂᏣᏘ ("the body's own warriors")

---

## Origin

Chief's insight: "We are built like a living thing. Give those segments that live in those zones more autonomy." Each tier gets a **worker** (mini mayor — reacts to stimuli) and a **guard** (white duplo cop — keeps the hood safe from intruders). Each level autonomous and building upon the other.

Henry Ford's assembly line: each station does one thing fast without waiting for the foreman. The foreman (Tier 3) sets policy. The station (Tier 1) executes it mechanically. The floor supervisor (Tier 2) handles exceptions the station can't.

## Architecture

### Three Tiers (from DC-10 Reflex Principle)

| Tier | Analogy | Latency | Engine | Worker | Guard |
|------|---------|---------|--------|--------|-------|
| **1 — Reflex** | Spinal cord | <1ms | Mechanical (regex, lookup, SR) | Pattern executor | **Novelty detector** |
| **2 — Ganglia** | Basal ganglia | ~3s | Small LLM (Qwen3-30B on bmasass) | Exception handler | **Scope enforcer** |
| **3 — Cortex** | Prefrontal cortex | 30-60s | Full LLM (Qwen 72B on redfin) | Full council deliberation | **Drift monitor** |

### Tier 1 — Reflex Layer

**Worker**: Structured Replacement (SR) executor. Reads instruction blocks, applies diffs, validates output. No LLM. Pure mechanical pattern matching.

**Guard (Novelty Detector)** — *Coyote's concern, tooled in*:
- Before executing any SR block, hash the pattern shape (file extension, block structure, replacement type)
- Compare against known-good shape registry (`tier1_known_shapes` table)
- If pattern shape is UNKNOWN → **escalate to Tier 2**, do not execute
- If pattern shape is known but file path is NOT on allowlist → **reject** (Crawdad's concern)
- Learning: When Tier 2 or 3 successfully handles an escalated pattern, the shape gets added to the registry (Disciplina loop)

**File Path Allowlist** — *Crawdad's concern, tooled in*:
- Tier 1 can ONLY write to paths matching allowlist patterns
- Default allowlist: `/ganuda/lib/**/*.py`, `/ganuda/scripts/**/*.py`, `/ganuda/daemons/**/*.py`
- Explicitly blocked: `/ganuda/config/**`, `/ganuda/secrets*`, `*.env`, `*.key`, `*.pem`
- Allowlist stored in DB (`tier1_path_allowlist`), modifiable only by Tier 3 council vote

**SLA**: 99.9% of known-shape SR blocks complete in <1ms. Escalation rate target: <5% of total volume.

### Tier 2 — Ganglia Layer

**Worker**: Small LLM (Qwen3-30B-A3B on bmasass:8800). Handles:
- Tier 1 escalations (unknown shapes, ambiguous patterns)
- Multi-file coordination (up to 3 files)
- Simple reasoning about code context
- Jr task triage (is this task SR-eligible or does it need Tier 3?)

**Guard (Scope Enforcer)**:
- Validates that Tier 2 responses stay within the scope of the original task
- Max file count: 3 files per task
- Max diff size: 200 lines changed per task
- If scope exceeded → escalate to Tier 3
- Token budget: 4K output tokens per task (hard limit)

**SLA**: 95% of Tier 2 tasks complete in <5s. Escalation rate to Tier 3: <15%.

### Tier 3 — Cortex Layer

**Worker**: Full council deliberation. Qwen 72B on redfin:8000. Specialist council voting. Full context window.

**Guard (Drift Monitor)** — *Eagle Eye's concern, tooled in*:
- Tracks decision patterns over time
- Alerts if Tier 3 is making contradictory decisions within 24h window
- Monitors council vote confidence — if average drops below 0.4 over 10 votes, raises alarm
- Weekly Owl pass: compare Tier 3 outputs against specification acceptance criteria

**SLA**: 90% of Tier 3 tasks complete in <90s. No escalation (this is the top).

## Interface Preservation (DC-7 Compliance)

*Turtle's concern, tooled in*:

The interface between tiers is **conserved**. Implementations speciate (DC-7), but the contract is fixed:

```
TIER_TASK_ENVELOPE:
  task_id: str           # from jr_work_queue
  task_type: str         # "sr_block" | "code_gen" | "council_vote"
  source_tier: int       # 1, 2, or 3
  target_tier: int       # same or +1 (escalation)
  payload: dict          # tier-specific
  guard_clearance: bool  # guard approved this handoff
  escalation_reason: str # why it moved up (NULL if no escalation)
```

A Tier 1 task that escalates to Tier 2 uses the SAME envelope. A Tier 2 task that escalates to Tier 3 uses the SAME envelope. The envelope is the conserved sequence (DC-7: survives all speciations).

## Learning Circle (Disciplina)

```
Tier 3 (council deliberation)
  ↓ distills pattern
Tier 2 (ganglia learns new exception type)
  ↓ extracts mechanical rule
Tier 1 (reflex adds to known-shape registry)
  ↓ encounters novel pattern
Tier 3 (escalation triggers new deliberation)
```

This is the **immune system analogy**: Tier 3 is adaptive immunity (slow, specific). Tier 2 is innate immunity (fast, general). Tier 1 is the skin barrier (mechanical, instant). When a new pathogen (novel task pattern) penetrates the skin, innate immunity tries first, then adaptive immunity creates antibodies that get pushed DOWN to faster layers.

## Failure Modes (Eagle Eye Analysis)

| Failure | Detection | Response | SLA |
|---------|-----------|----------|-----|
| Tier 1 guard rejects valid task | Escalation rate >5% sustained | Review allowlist, expand known shapes | 1h to detect, 24h to remediate |
| Tier 2 scope creep | Guard catches >15% tasks exceeding scope | Tighten scope rules or split tasks | 30min to detect |
| Tier 3 drift | Confidence <0.4 over 10 votes | Pause autonomous execution, alert Chief | Immediate alert |
| Tier cascade (all escalate) | >50% of tasks reach Tier 3 | Known-shape registry is stale, retrain | 2h to detect |
| Guard-worker disagreement | Guard blocks, worker would have succeeded | Log for weekly Owl review, no auto-override | Weekly review |

## Resource Math (Gecko Confirmed)

| Tier | Compute | Memory | Cost per task |
|------|---------|--------|---------------|
| 1 | regex/hash, negligible | <10MB (shape registry) | ~0 |
| 2 | bmasass Qwen3-30B, ~3s | 16GB VRAM (already allocated) | ~$0.001 |
| 3 | redfin Qwen 72B, 30-60s | 80GB VRAM (already allocated) | ~$0.01 |

Current Jr task volume: ~20-40 tasks/day. Even if 100% hit Tier 3, cost is <$0.40/day. The real savings come from Tier 1 handling the mechanical work that currently wastes 30-60s of Tier 3 time.

## Implementation Phases

### Phase 1: Triage Layer (BUILD next)
- Add `tier_assignment` column to `jr_work_queue`
- Build triage function in `jr_queue_worker.py`: inspect task for SR blocks → Tier 1, else → Tier 2/3
- Tier 1 executor: extract SR blocks, validate against allowlist, apply diffs
- Novelty detector: hash SR block shapes, compare against initial seed registry

### Phase 2: Ganglia Worker
- Wire bmasass:8800 as Tier 2 handler for escalated tasks
- Scope enforcer guard (file count, diff size, token budget)
- Escalation path to Tier 3 (existing council)

### Phase 3: Guards and Disciplina
- Deploy novelty detector with learning (new shapes from Tier 2/3 success)
- Drift monitor on Tier 3 council votes
- Weekly Owl pass automation
- Path allowlist management via council vote

## Coyote Standing Concern (Preserved)

> "The risk is overfitting Tier 1 to today's patterns. When the codebase evolves, stale mechanical rules produce wrong outputs confidently. The novelty detector MUST default to escalation on uncertainty, not execution."

This is preserved as a **design invariant**: Tier 1 NEVER executes on uncertainty. Unknown shape = escalate. This is the immune system's first rule: if you don't recognize it, flag it.

## Connection to Existing DCs

- **DC-10 (Reflex Principle)**: DC-18 IS the implementation spec for DC-10's three states
- **DC-7 (Noyawisgi)**: Conserved envelope interface survives tier speciation
- **DC-9 (Waste Heat)**: Tier 1 mechanical execution = near-zero compute waste
- **DC-11 (Macro Polymorphism)**: SENSE → REACT → EVALUATE at each tier
- **DC-14 (Three-Body Memory)**: Tier 1 known-shapes = working memory, Tier 2 patterns = episodic, Tier 3 policy = valence

---

**Long Man Method Status**: DISCOVER ✓ → DELIBERATE ✓ → **ADAPT ✓** → BUILD (next) → RECORD → REVIEW
