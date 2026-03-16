# Jr Instruction: SkillRL — Self-Improving ToolSet Rings with Reinforcement Learning

**Task ID**: Supersedes research ticket #1397
**Priority**: P1
**Story Points**: 21 (EPIC)
**Nodes**: redfin (service), bmasass (training), sasass2 (code review)
**Council Vote**: `#017cb349fddb92a0` — REVIEW REQUIRED (0.25 confidence). Resubmitted with featurized conditions below.
**Patent Candidate**: #8 — Self-improving skill library with governance-gated reinforcement learning

## Context

### The Papers (March 2026)

Two independent teams converged on the same architecture we're building:

1. **SAGE** (AWS + UW-Madison, Mar 10 2026): RL framework where agents build skill libraries through sequential rollouts. Skills accumulate, agent self-improves via Skill-Augmented GRPO.

2. **Agentic Proposing** (Alibaba + Shanghai Jiao Tong, Feb 2026): 4B model trained on synthesized skill compositions outperforms GPT-5.2 and Claude 4.5 Opus on math benchmarks. Skill tuple: (intent, method, difficulty, tool_hint). Curriculum learning focuses training on weak areas.

### What We Already Have (80%)

| Component | Location | Status |
|-----------|----------|--------|
| ToolSet base class + rings | `/ganuda/lib/toolsets/base.py` | LIVE |
| ThermalToolSet (6 tools) | `/ganuda/lib/toolsets/thermal_toolset.py` | LIVE |
| KanbanToolSet (3 tools) | `/ganuda/lib/toolsets/kanban_toolset.py` | LIVE |
| Duplo tool registry | `/ganuda/lib/duplo/registry.py` | LIVE |
| UCB1 bandit (model selection) | `/ganuda/lib/ucb_bandit.py` | LIVE |
| Valence gate (reward signal) | `/ganuda/lib/valence_gate.py` | LIVE |
| MAGRPO group reward | `/ganuda/lib/magrpo_tracker.py` | LIVE |
| Sub-agent dispatch (8 models) | `/ganuda/lib/sub_agent_dispatch.py` | LIVE |
| Specialist council (7 members) | `/ganuda/lib/specialist_council.py` | LIVE |
| Chain protocol (ring governance) | `/ganuda/lib/chain_protocol.py` | LIVE |
| Frontier adapters (4 providers) | `/ganuda/lib/frontier_adapters.py` | LIVE |
| Valence evaluator (retrospective) | `/ganuda/lib/harness/valence_evaluator.py` | LIVE |
| Tool-calling loop | `/ganuda/lib/tool_executor.py` | LIVE |
| Immune registry | `/ganuda/lib/duplo/immune_registry.py` | LIVE |

### What's Missing (20% — This Task)

| Gap | Description |
|-----|-------------|
| **Skill Extraction** | Jr completes a task → extract the reusable pattern as a new skill |
| **Skill Composition** | Combine atomic skills into compound skills (the paper's key insight) |
| **Curriculum Learning** | Track proficiency per skill category, focus compute on weak areas |
| **Skill Verification** | Council votes on new skills before they enter the library |
| **RL Training Loop** | Reward signal from task outcomes feeds back to skill selection |
| **Skill Registry** | Persistent catalog of learned skills with metadata |

## Architecture

### The Skill Lifecycle

```
Jr Task Completes Successfully
  → Skill Extractor analyzes: What reusable pattern emerged?
  → Skill Descriptor created: (intent, method, difficulty, tool_hints)
  → Council Verification: Is this a valid, safe, reusable skill?
  → Skill Registry: Stored with provenance + initial UCB prior
  → Available for future tasks via ToolSet ring injection
  → Task outcomes update skill reward (UCB bandit)
  → Curriculum tracker identifies weak skill categories
  → Future Jr tasks biased toward weak categories
  → Cycle repeats — organism learns
```

### Mapping to Papers

| Paper Concept | Our Implementation |
|---|---|
| Skill tuple (intent, method, difficulty, tool_hint) | `SkillDescriptor` dataclass |
| Sequential rollout accumulation | Jr task chain — each extraction feeds the library |
| Verification committee (3 models) | Specialist council + `council_vote()` |
| Skill-Augmented GRPO (SAGE) | UCB bandit extended with skill-integrated reward |
| Curriculum learning (proficiency vector) | `SkillProficiency` tracker — EMA per category |
| Atomic skill composition | `compose_skills()` — combine 2-3 skills into compound |
| Skill library loading on demand | ToolSet ring injection via duplo registry (lazy) |

### Data Flow

```
                    ┌─────────────────────────────────────┐
                    │         SKILL REGISTRY               │
                    │  (skill_library table on bluefin)    │
                    │                                       │
                    │  intent | method | difficulty |       │
                    │  tool_hints | domain | ucb_stats |   │
                    │  council_vote_id | provenance |      │
                    └──────┬──────────────┬────────────────┘
                           │              │
                    ┌──────▼──────┐ ┌─────▼──────────┐
                    │  SKILL      │ │  CURRICULUM     │
                    │  SELECTOR   │ │  TRACKER        │
                    │  (UCB1)     │ │  (proficiency   │
                    │             │ │   per category) │
                    └──────┬──────┘ └─────┬──────────┘
                           │              │
                    ┌──────▼──────────────▼──────────────┐
                    │         TOOL EXECUTOR               │
                    │  Injects selected skills as tools   │
                    │  into Jr context window             │
                    └──────┬──────────────────────────────┘
                           │
                    ┌──────▼──────────────────────────────┐
                    │         JR TASK EXECUTION            │
                    │  Jr uses skills to complete task     │
                    └──────┬──────────────────────────────┘
                           │
                    ┌──────▼──────────────────────────────┐
                    │         SKILL EXTRACTOR              │
                    │  Analyzes completed task:            │
                    │  - What pattern emerged?             │
                    │  - Is it reusable?                   │
                    │  - Compose atomic skills?            │
                    └──────┬──────────────────────────────┘
                           │
                    ┌──────▼──────────────────────────────┐
                    │         COUNCIL VERIFICATION         │
                    │  Specialist vote on new skill        │
                    │  - Valid? Safe? Reusable?            │
                    │  - Sovereignty check                 │
                    │  - DC alignment                      │
                    └──────┬──────────────────────────────┘
                           │
                    ┌──────▼──────────────────────────────┐
                    │         REWARD UPDATE                │
                    │  Task outcome → skill reward         │
                    │  UCB stats updated                   │
                    │  Proficiency vector recalculated     │
                    └─────────────────────────────────────┘
```

## Implementation

### New Files (7)

| File | Purpose | SP |
|------|---------|-----|
| `scripts/migrations/skill_library_schema.sql` | DB tables for skill registry + proficiency tracking | 1 |
| `lib/skill_descriptor.py` | SkillDescriptor dataclass + composition logic | 2 |
| `lib/skill_extractor.py` | Extract reusable patterns from completed Jr tasks | 5 |
| `lib/skill_selector.py` | UCB1-based skill selection with curriculum weighting | 3 |
| `lib/skill_proficiency.py` | EMA proficiency tracker per skill category | 2 |
| `lib/toolsets/skill_toolset.py` | SkillToolSet ring — inject skills into tool executor | 3 |
| `tests/test_skill_rl.py` | Unit tests for extraction, composition, selection, proficiency | 2 |

### Modified Files (4)

| File | Change |
|------|--------|
| `lib/tool_executor.py` | Register SkillToolSet in TOOLSETS dict |
| `lib/harness/config.yaml` | Add `skill_rl:` configuration section |
| `lib/duplo/registry.py` | Add skill-related tool registrations |
| `services/jr_executor/` | Post-task hook: call skill_extractor on success |

---

### Step 1: Database Schema

**File**: `scripts/migrations/skill_library_schema.sql`

```sql
-- Skill Library — learned reusable patterns
CREATE TABLE skill_library (
    id SERIAL PRIMARY KEY,
    skill_id VARCHAR(64) UNIQUE NOT NULL,  -- deterministic hash of intent+method
    name VARCHAR(200) NOT NULL,
    intent TEXT NOT NULL,                   -- reasoning principle (WHY)
    method TEXT NOT NULL,                   -- construction procedure (HOW)
    difficulty INTEGER CHECK (difficulty BETWEEN 1 AND 10),
    tool_hints TEXT[],                      -- which tools/APIs this skill uses
    domain VARCHAR(50) DEFAULT 'general',   -- code, research, ops, legal, general

    -- Composition
    is_compound BOOLEAN DEFAULT FALSE,
    parent_skills VARCHAR(64)[],            -- skill_ids this was composed from

    -- Governance
    council_vote_id VARCHAR(64),            -- longhouse vote approving this skill
    provenance_hash VARCHAR(64) NOT NULL,   -- chain_protocol provenance
    source_task_id INTEGER,                 -- jr_work_queue.id that spawned this
    status VARCHAR(20) DEFAULT 'candidate', -- candidate, approved, active, retired, revoked

    -- UCB Stats (mirror consultation_model_stats pattern)
    total_uses INTEGER DEFAULT 0,
    successful_uses INTEGER DEFAULT 0,
    total_reward NUMERIC(12,4) DEFAULT 1.0, -- optimistic prior (1 success / 2 uses)
    avg_latency_ms NUMERIC(10,2) DEFAULT 0,

    -- Integrity (Eagle Eye condition #4)
    content_hash VARCHAR(64) NOT NULL,      -- SHA256(intent||method||tool_hints) for corruption detection

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    last_used TIMESTAMP,
    retired_at TIMESTAMP,
    retire_reason TEXT
);

-- Proficiency tracking per skill category
CREATE TABLE skill_proficiency (
    id SERIAL PRIMARY KEY,
    domain VARCHAR(50) NOT NULL,
    category VARCHAR(100) NOT NULL,         -- e.g., "db_migration", "api_integration", "css_layout"
    proficiency_score NUMERIC(5,4) DEFAULT 0.5,  -- 0.0 to 1.0, EMA
    total_attempts INTEGER DEFAULT 0,
    successful_attempts INTEGER DEFAULT 0,
    last_updated TIMESTAMP DEFAULT NOW(),
    UNIQUE(domain, category)
);

-- Skill usage log (for RL reward attribution)
CREATE TABLE skill_usage_log (
    id SERIAL PRIMARY KEY,
    skill_id VARCHAR(64) REFERENCES skill_library(skill_id),
    task_id INTEGER,                        -- jr_work_queue.id
    domain VARCHAR(50),
    reward NUMERIC(5,4),                    -- 0.0 to 1.0
    success BOOLEAN,
    latency_ms INTEGER,
    used_at TIMESTAMP DEFAULT NOW()
);

-- Register in duplo_tool_registry
INSERT INTO duplo_tool_registry (ring_name, ring_type, status, registered_at)
VALUES ('skill_rl', 'associate', 'active', NOW());
```

---

### Step 2: Skill Descriptor

**File**: `lib/skill_descriptor.py`

```python
"""
SkillDescriptor — the atomic unit of learned capability.

Maps to the paper's skill tuple: (intent, method, difficulty, tool_hint)
Extended with governance fields for federation context.
"""

import hashlib
import json
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class SkillDescriptor:
    """A learned, reusable pattern extracted from successful Jr task execution."""

    name: str                               # Human-readable name
    intent: str                             # WHY — the reasoning principle
    method: str                             # HOW — the construction procedure
    difficulty: int                         # 1-10 complexity rating
    tool_hints: list[str] = field(default_factory=list)  # Which tools/APIs this uses
    domain: str = "general"                 # code, research, ops, legal, general

    # Composition
    is_compound: bool = False
    parent_skills: list[str] = field(default_factory=list)  # skill_ids

    # Provenance
    source_task_id: Optional[int] = None

    @property
    def skill_id(self) -> str:
        """Deterministic hash of intent + method. Same pattern = same skill."""
        content = f"{self.intent}||{self.method}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def to_tool_description(self) -> dict:
        """Convert to OpenAI function-calling format for injection into context."""
        return {
            "type": "function",
            "function": {
                "name": f"skill_{self.skill_id}",
                "description": f"[Skill: {self.name}] {self.intent}",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "apply_to": {
                            "type": "string",
                            "description": "What to apply this skill to"
                        }
                    },
                    "required": ["apply_to"]
                }
            }
        }

    def to_context_block(self) -> str:
        """Render as a skill MD block for context window injection."""
        return f"""## Skill: {self.name}
**Intent**: {self.intent}
**Method**: {self.method}
**Difficulty**: {self.difficulty}/10
**Tools**: {', '.join(self.tool_hints) if self.tool_hints else 'None'}
**Domain**: {self.domain}
"""


def compose_skills(skills: list[SkillDescriptor],
                   name: str,
                   intent: str,
                   method: str) -> SkillDescriptor:
    """
    Combine atomic skills into a compound skill.

    The paper's key insight: compositions of simple skills
    solve problems that no single skill can handle alone.
    """
    return SkillDescriptor(
        name=name,
        intent=intent,
        method=method,
        difficulty=min(10, max(s.difficulty for s in skills) + len(skills) - 1),
        tool_hints=list(set(h for s in skills for h in s.tool_hints)),
        domain=skills[0].domain,
        is_compound=True,
        parent_skills=[s.skill_id for s in skills]
    )
```

---

### Step 3: Skill Extractor

**File**: `lib/skill_extractor.py`

This is the hardest piece — analyzing a completed Jr task and extracting the reusable pattern.

```python
"""
SkillExtractor — harvest reusable patterns from completed Jr tasks.

Called as a post-task hook when a Jr task succeeds.
Uses a local model (DC-9) to analyze what happened and whether
a reusable skill emerged.

Paper reference: SAGE sequential rollout skill accumulation.
"""

import json
import logging
from lib.skill_descriptor import SkillDescriptor
from lib.sub_agent_dispatch import dispatch

logger = logging.getLogger("skill_extractor")

EXTRACTION_PROMPT = """You are a skill extractor for a software federation.

A Jr engineer just completed a task successfully. Analyze the task and its outcome to determine if a REUSABLE SKILL emerged.

A skill is reusable if:
1. The SAME PATTERN could apply to future, different tasks
2. It's not just "I edited a file" — it's a transferable technique
3. It has clear intent (WHY), method (HOW), and tool requirements

Task Title: {title}
Task Description: {description}
Acceptance Criteria: {acceptance_criteria}
Files Modified: {files_modified}
Steps Completed: {steps_summary}

If a reusable skill emerged, respond with this JSON (and nothing else):
{{
    "skill_found": true,
    "name": "short descriptive name",
    "intent": "the reasoning principle — WHY this pattern works",
    "method": "the construction procedure — HOW to apply this pattern step by step",
    "difficulty": <1-10>,
    "tool_hints": ["tool1", "tool2"],
    "domain": "code|research|ops|legal|general",
    "reasoning": "why you believe this is reusable"
}}

If NO reusable skill emerged (task was too specific, one-off, or trivial), respond:
{{
    "skill_found": false,
    "reasoning": "why no skill was extracted"
}}
"""

async def extract_skill(task: dict) -> SkillDescriptor | None:
    """
    Analyze a completed Jr task and extract a reusable skill if one exists.

    Uses local model (DC-9 — no external API for internal reflection).
    Returns SkillDescriptor or None.
    """
    prompt = EXTRACTION_PROMPT.format(
        title=task.get("title", ""),
        description=task.get("description", ""),
        acceptance_criteria=task.get("acceptance_criteria", ""),
        files_modified=json.dumps(task.get("files_modified", [])),
        steps_summary=task.get("steps_summary", "")
    )

    # Use local model — skill extraction is internal reflection, not external consultation
    result = await dispatch(prompt, node="redfin_vllm")

    if not result or not result.get("ok"):
        logger.warning("Skill extraction dispatch failed")
        return None

    try:
        parsed = json.loads(result["text"])
    except json.JSONDecodeError:
        logger.warning("Skill extraction returned non-JSON")
        return None

    if not parsed.get("skill_found"):
        logger.info(f"No skill extracted: {parsed.get('reasoning', 'unknown')}")
        return None

    skill = SkillDescriptor(
        name=parsed["name"],
        intent=parsed["intent"],
        method=parsed["method"],
        difficulty=parsed.get("difficulty", 5),
        tool_hints=parsed.get("tool_hints", []),
        domain=parsed.get("domain", "general"),
        source_task_id=task.get("id")
    )

    logger.info(f"Skill extracted: {skill.name} (id={skill.skill_id})")
    return skill


async def check_duplicate(skill: SkillDescriptor, db_conn) -> bool:
    """Check if this skill already exists in the library."""
    row = await db_conn.fetchone(
        "SELECT skill_id FROM skill_library WHERE skill_id = %s",
        (skill.skill_id,)
    )
    return row is not None


async def submit_for_verification(skill: SkillDescriptor, council) -> dict:
    """
    Submit extracted skill to specialist council for verification.

    Council checks:
    - Is the intent valid and clearly stated?
    - Is the method safe (no security violations)?
    - Is this actually reusable (not just a one-off)?
    - Does it align with DCs (sovereignty, build-to-last, waste heat)?

    Returns council vote result.
    """
    proposal = f"""SKILL LIBRARY ADDITION PROPOSAL

A new skill has been extracted from a completed Jr task and requires council verification before entering the active skill library.

Skill Name: {skill.name}
Skill ID: {skill.skill_id}
Domain: {skill.domain}
Difficulty: {skill.difficulty}/10
Intent: {skill.intent}
Method: {skill.method}
Tool Hints: {', '.join(skill.tool_hints)}
Source Task: #{skill.source_task_id}
Compound: {skill.is_compound}
Parent Skills: {', '.join(skill.parent_skills) if skill.parent_skills else 'None (atomic)'}

EVALUATION CRITERIA:
1. Is the intent clearly stated and valid?
2. Is the method safe — no security violations, no sovereignty compromise?
3. Is this genuinely reusable across future tasks, or a one-off pattern?
4. Does it align with Design Constraints (DC-1 through DC-16)?
5. Is the difficulty rating appropriate?
6. Are the tool hints accurate?

Vote CONSENT to add to skill library.
Vote CONCERN with specific issues to address.
Vote DISSENT if this skill should NOT be added.
"""

    return await council.council_vote(
        proposal=proposal,
        context=f"Skill extraction from Jr task #{skill.source_task_id}"
    )
```

---

### Step 4: Skill Selector (UCB1 + Curriculum)

**File**: `lib/skill_selector.py`

```python
"""
SkillSelector — UCB1 bandit for skill selection with curriculum weighting.

Extends the UCBBandit pattern from /ganuda/lib/ucb_bandit.py.
Adds proficiency-based curriculum learning from the Agentic Proposing paper.

Key insight: Focus compute on weak skill categories, not strong ones.
"""

import math
import logging
from lib.skill_proficiency import SkillProficiency

logger = logging.getLogger("skill_selector")

# Standard UCB1 exploration weight (sqrt(2))
EXPLORATION_WEIGHT = 1.41


class SkillSelector:
    """Select skills for a task using UCB1 + curriculum weighting."""

    def __init__(self, db_conn):
        self.db = db_conn
        self.proficiency = SkillProficiency(db_conn)

    async def select_skills(self, domain: str, task_description: str,
                            max_skills: int = 5) -> list[dict]:
        """
        Select the best skills for a task from the library.

        1. Filter by domain + status='active'
        2. Score each with UCB1
        3. Weight by inverse proficiency (curriculum — weak areas get more attention)
        4. Return top-k skills
        """
        # Get all active skills for this domain
        skills = await self.db.fetch(
            """SELECT skill_id, name, intent, method, difficulty, tool_hints,
                      domain, total_uses, successful_uses, total_reward,
                      is_compound, parent_skills
               FROM skill_library
               WHERE (domain = %s OR domain = 'general')
                 AND status = 'active'
               ORDER BY total_uses ASC""",  # least-used first for cold start
            (domain,)
        )

        if not skills:
            return []

        total_uses_all = sum(s["total_uses"] for s in skills) or 1

        scored = []
        for skill in skills:
            # UCB1 score
            n = max(skill["total_uses"], 2)  # optimistic prior: 2 total
            mean_reward = float(skill["total_reward"]) / n
            exploration = EXPLORATION_WEIGHT * math.sqrt(math.log(total_uses_all) / n)
            ucb_score = mean_reward + exploration

            # Curriculum weight — boost skills in weak categories
            # Inverse proficiency: if we're bad at this category, select it more
            category = await self._infer_category(skill)
            prof_score = await self.proficiency.get_score(domain, category)
            curriculum_weight = 1.0 + (1.0 - prof_score)  # Range: 1.0 (mastered) to 2.0 (weak)

            # Combined score
            final_score = ucb_score * curriculum_weight

            scored.append({
                **skill,
                "ucb_score": ucb_score,
                "curriculum_weight": curriculum_weight,
                "final_score": final_score,
                "category": category,
                "proficiency": prof_score
            })

        # Sort by final score, return top-k
        scored.sort(key=lambda s: s["final_score"], reverse=True)
        return scored[:max_skills]

    async def update_reward(self, skill_id: str, domain: str,
                            reward: float, success: bool, latency_ms: int = 0):
        """
        Update skill stats after use. Reward comes from task outcome.

        Reward signal:
        - Task completed successfully: 0.7 - 1.0 (based on quality)
        - Task completed with issues: 0.3 - 0.7
        - Task failed: 0.0 - 0.3
        """
        await self.db.execute(
            """UPDATE skill_library
               SET total_uses = total_uses + 1,
                   successful_uses = successful_uses + CASE WHEN %s THEN 1 ELSE 0 END,
                   total_reward = total_reward + %s,
                   avg_latency_ms = (avg_latency_ms * total_uses + %s) / (total_uses + 1),
                   last_used = NOW()
               WHERE skill_id = %s""",
            (success, reward, latency_ms, skill_id)
        )

        # Update proficiency for this category
        category = await self._get_skill_category(skill_id)
        if category:
            await self.proficiency.update(domain, category, reward, success)

        # Log for audit trail
        await self.db.execute(
            """INSERT INTO skill_usage_log (skill_id, domain, reward, success, latency_ms)
               VALUES (%s, %s, %s, %s, %s)""",
            (skill_id, domain, reward, success, latency_ms)
        )

    async def _infer_category(self, skill: dict) -> str:
        """Infer skill category from tool hints and domain."""
        hints = skill.get("tool_hints", [])
        if any("db" in h or "sql" in h or "migration" in h for h in hints):
            return "db_operations"
        if any("api" in h or "http" in h or "endpoint" in h for h in hints):
            return "api_integration"
        if any("css" in h or "html" in h or "frontend" in h for h in hints):
            return "frontend"
        if any("systemd" in h or "deploy" in h or "service" in h for h in hints):
            return "ops_deployment"
        if any("test" in h for h in hints):
            return "testing"
        return skill.get("domain", "general")

    async def _get_skill_category(self, skill_id: str) -> str | None:
        """Get the category for a skill from the DB."""
        row = await self.db.fetchone(
            "SELECT tool_hints, domain FROM skill_library WHERE skill_id = %s",
            (skill_id,)
        )
        if row:
            return await self._infer_category(row)
        return None
```

---

### Step 5: Skill Proficiency Tracker

**File**: `lib/skill_proficiency.py`

```python
"""
SkillProficiency — Exponential Moving Average proficiency per skill category.

From the Agentic Proposing paper:
  M(t+1) = (1-α) * M(t) + α * success_rate

When proficiency is LOW, the curriculum selector biases toward that category.
When proficiency is HIGH, compute is spent elsewhere.

This is the self-regulating curriculum — no human in the scheduling loop.
"""

import logging

logger = logging.getLogger("skill_proficiency")

# Smoothing factor — how quickly we react to new signal vs historical
# 0.3 = responsive to recent results while respecting history
ALPHA = 0.3


class SkillProficiency:
    """Track proficiency per (domain, category) pair."""

    def __init__(self, db_conn):
        self.db = db_conn

    async def get_score(self, domain: str, category: str) -> float:
        """
        Get current proficiency score. 0.0 = completely weak, 1.0 = mastered.
        Returns 0.5 (uncertain) for unseen categories.
        """
        row = await self.db.fetchone(
            """SELECT proficiency_score FROM skill_proficiency
               WHERE domain = %s AND category = %s""",
            (domain, category)
        )
        return float(row["proficiency_score"]) if row else 0.5

    async def update(self, domain: str, category: str,
                     reward: float, success: bool):
        """
        Update proficiency with EMA.

        M(t+1) = (1-α) * M(t) + α * new_signal

        new_signal = reward if success else reward * 0.5
        """
        new_signal = reward if success else reward * 0.5

        existing = await self.db.fetchone(
            """SELECT proficiency_score, total_attempts
               FROM skill_proficiency
               WHERE domain = %s AND category = %s""",
            (domain, category)
        )

        if existing:
            old_score = float(existing["proficiency_score"])
            new_score = (1 - ALPHA) * old_score + ALPHA * new_signal

            await self.db.execute(
                """UPDATE skill_proficiency
                   SET proficiency_score = %s,
                       total_attempts = total_attempts + 1,
                       successful_attempts = successful_attempts + CASE WHEN %s THEN 1 ELSE 0 END,
                       last_updated = NOW()
                   WHERE domain = %s AND category = %s""",
                (round(new_score, 4), success, domain, category)
            )
            logger.info(f"Proficiency {domain}/{category}: {old_score:.3f} → {new_score:.3f}")
        else:
            await self.db.execute(
                """INSERT INTO skill_proficiency
                   (domain, category, proficiency_score, total_attempts, successful_attempts)
                   VALUES (%s, %s, %s, 1, %s)""",
                (domain, category, round(new_signal, 4), 1 if success else 0)
            )
            logger.info(f"Proficiency {domain}/{category}: NEW → {new_signal:.3f}")

    async def get_weakest(self, domain: str, limit: int = 5) -> list[dict]:
        """Get the weakest skill categories — curriculum targets."""
        rows = await self.db.fetch(
            """SELECT category, proficiency_score, total_attempts
               FROM skill_proficiency
               WHERE domain = %s AND total_attempts >= 3
               ORDER BY proficiency_score ASC
               LIMIT %s""",
            (domain, limit)
        )
        return [dict(r) for r in rows]

    async def get_vector(self, domain: str) -> dict[str, float]:
        """
        Get full proficiency vector for a domain.
        Used for curriculum sampling probability calculation.

        Sampling probability ∝ (1 - proficiency)
        Weak categories get more training time.
        """
        rows = await self.db.fetch(
            """SELECT category, proficiency_score
               FROM skill_proficiency
               WHERE domain = %s""",
            (domain,)
        )
        return {r["category"]: float(r["proficiency_score"]) for r in rows}
```

---

### Step 6: SkillToolSet Ring

**File**: `lib/toolsets/skill_toolset.py`

```python
"""
SkillToolSet — inject learned skills into the tool executor as callable tools.

When a Jr task runs, SkillToolSet provides skills as tools the Jr can invoke.
This is how learned patterns become available to future tasks.

DC-11: SENSE (proficiency) → REACT (skill selection) → EVALUATE (reward update)
"""

from lib.toolsets.base import ToolSet, ToolDescriptor, ToolResult
from lib.skill_selector import SkillSelector

class SkillToolSet(ToolSet):
    """ToolSet ring that provides learned skills as callable tools."""

    domain = "skillrl"

    def __init__(self, db_conn):
        super().__init__()
        self.selector = SkillSelector(db_conn)
        self._loaded_skills = {}  # skill_id → skill data

    async def load_skills_for_task(self, domain: str, task_description: str):
        """
        Pre-load relevant skills before task execution.
        Called by tool_executor when a Jr task starts.
        """
        selected = await self.selector.select_skills(
            domain=domain,
            task_description=task_description,
            max_skills=5
        )
        self._loaded_skills = {s["skill_id"]: s for s in selected}

    def get_tools(self) -> list[ToolDescriptor]:
        """Return loaded skills as tool descriptors."""
        tools = [
            ToolDescriptor(
                name="list_available_skills",
                description="List all skills currently available for this task, with their methods and proficiency scores",
                parameters={},
                safety_class="read"
            ),
            ToolDescriptor(
                name="apply_skill",
                description="Apply a learned skill to the current task context",
                parameters={
                    "skill_id": {"type": "string", "description": "ID of the skill to apply"},
                    "context": {"type": "string", "description": "What to apply the skill to"}
                },
                safety_class="read"
            ),
            ToolDescriptor(
                name="get_skill_method",
                description="Get the detailed method/procedure for a specific skill",
                parameters={
                    "skill_id": {"type": "string", "description": "ID of the skill"}
                },
                safety_class="read"
            )
        ]
        return tools

    async def execute(self, tool_name: str, args: dict) -> ToolResult:
        """Execute a skill tool."""
        if tool_name == "list_available_skills":
            return self._list_skills()
        elif tool_name == "apply_skill":
            return await self._apply_skill(args["skill_id"], args["context"])
        elif tool_name == "get_skill_method":
            return self._get_method(args["skill_id"])
        else:
            return ToolResult(success=False, error=f"Unknown tool: {tool_name}")

    def _list_skills(self) -> ToolResult:
        """List all loaded skills with scores."""
        if not self._loaded_skills:
            return ToolResult(
                success=True,
                data={"skills": [], "message": "No skills loaded for this task domain"}
            )

        skills = []
        for sid, s in self._loaded_skills.items():
            skills.append({
                "skill_id": sid,
                "name": s["name"],
                "intent": s["intent"],
                "difficulty": s["difficulty"],
                "proficiency": s.get("proficiency", 0.5),
                "ucb_score": round(s.get("ucb_score", 0), 3),
                "domain": s["domain"]
            })

        return ToolResult(success=True, data={"skills": skills})

    async def _apply_skill(self, skill_id: str, context: str) -> ToolResult:
        """Apply a skill — return the method as actionable instructions."""
        skill = self._loaded_skills.get(skill_id)
        if not skill:
            return ToolResult(success=False, error=f"Skill {skill_id} not loaded")

        return ToolResult(
            success=True,
            data={
                "skill_id": skill_id,
                "name": skill["name"],
                "intent": skill["intent"],
                "method": skill["method"],
                "tool_hints": skill.get("tool_hints", []),
                "instruction": f"Apply the following method to: {context}\n\n{skill['method']}"
            }
        )

    def _get_method(self, skill_id: str) -> ToolResult:
        """Get detailed method for a skill."""
        skill = self._loaded_skills.get(skill_id)
        if not skill:
            return ToolResult(success=False, error=f"Skill {skill_id} not loaded")

        return ToolResult(
            success=True,
            data={
                "skill_id": skill_id,
                "name": skill["name"],
                "method": skill["method"],
                "tool_hints": skill.get("tool_hints", []),
                "difficulty": skill["difficulty"],
                "is_compound": skill.get("is_compound", False),
                "parent_skills": skill.get("parent_skills", [])
            }
        )
```

---

## Council Deliberation

### Proposal for Longhouse Vote

**PROPOSAL: SkillRL — Self-Improving ToolSet Rings**

The federation adds a self-improving skill library where completed Jr tasks can spawn reusable skills, verified by the council, selected by UCB1 bandit with curriculum learning, and injected into future Jr task contexts as callable tools.

**Why now**: Two independent research teams (AWS and Alibaba) published papers validating this exact architecture. A 4B model with proper skill composition outperforms GPT-5.2. We have 80% of the infrastructure. The remaining 20% is 7 files and 4 modifications.

**Risk**: The organism starts learning. Skills compound. Compound skills compose into higher-order skills. The question isn't whether this works — the papers prove it does. The question is whether our governance (council verification, valence gate, provenance tagging) is sufficient to ensure the organism learns the RIGHT things.

### Anticipated Specialist Concerns (Featurized)

**Turtle** (Reversibility):
- *Concern*: "Once a skill enters the library and gets used 100 times, retiring it may break dependent compound skills."
- *Feature*: Skill retirement cascade checker. Before retiring a skill, verify no active compound skills depend on it. If they do, retire the compounds first or refuse. Add `retired_at` and `retire_reason` columns. Retired skills remain queryable but not selectable.

**Coyote** (Observer / Edge Cases):
- *Concern*: "What if the extractor generates garbage skills from trivial tasks? Library fills with noise."
- *Feature*: Quality gate — skills must pass council vote AND have difficulty ≥ 3 to enter the library. Skills with < 3 uses after 30 days auto-retire (cold skill pruning). Coyote's circuit breaker: if skill extraction rate exceeds 5 per day, pause and audit.

**Crawdad** (Security / PII):
- *Concern*: "Skill methods could embed sensitive information — node names, IPs, credentials from the source task."
- *Feature*: Run every extracted skill through `domain_tokenizer.tokenize()` before storage. If any NEVER_SEND pattern matches, reject the skill. Skills are stored sanitized — no infrastructure details in the method text.

**Eagle Eye** (Drift):
- *Concern*: "How do we detect if the skill library is drifting — learning patterns that violate DCs over time?"
- *Feature*: Weekly skill audit (new timer: `skill-drift-audit.timer`). Compare skill library contents against DC violation patterns from valence_gate.py. Flag any skill whose method contains sovereignty/security/waste-heat violation terms.

**Spider** (Isolation):
- *Concern*: "Skill extraction runs on the Jr executor. If extraction fails or hangs, does it block the Jr task pipeline?"
- *Feature*: Extraction is async and non-blocking. Jr task marks complete regardless of extraction outcome. Extraction has a 30-second timeout. Failures are logged but never block the pipeline.

**Raven** (Strategy):
- *Concern*: "The cold start problem — with an empty library, skill selection returns nothing. When does the library become useful?"
- *Feature*: Seed the library with 10-15 hand-crafted skills extracted from our most successful Jr tasks. Optimistic UCB prior (1/2) ensures new skills get tried. Library becomes self-sustaining after ~50 tasks.

**Peace Chief** (Governance):
- *Concern*: "Council votes on every skill? That's 7 specialist queries per extraction. At scale, this dominates compute."
- *Feature*: Tiered verification. Difficulty 1-3 atomic skills: auto-approve if no NEVER_SEND patterns (reflex tier). Difficulty 4-7: 3-specialist subset vote (deliberation tier). Difficulty 8-10 or compound skills: full council (council tier). DC-10 Reflex Principle applied to skill governance itself.

**Deer** (Cultural / Sustainability):
- *Concern*: "Are we creating a system that knows HOW but not WHY? Skills without understanding."
- *Feature*: The `intent` field IS the why. Every skill must have a clear intent (reasoning principle) — not just a method (procedure). Skills with empty or vague intents are rejected by council. The intent is what makes our skills different from the competition: ours carry the reason, not just the recipe.

## Council Conditions (Vote `#017cb349fddb92a0` — Featurized)

The following conditions were raised during the first Longhouse vote and have been incorporated into the design. Each concern is now a feature.

### Condition 1: Coyote's DISSENT — Skill Propagation Brake

**Concern**: A flawed skill could propagate rapidly via UCB bandit across many tasks before the weekly drift audit catches it. The async extraction + optimistic prior means bad skills get tried fast.

**Feature**: **Auto-quarantine threshold**. Added to `skill_selector.py`:
- After each reward update, check: if `successful_uses / total_uses < 0.3` AND `total_uses >= 5`, auto-set `status = 'quarantine'`
- Quarantined skills are excluded from selection immediately — no waiting for weekly audit
- Eagle Eye notified via Slack `#fire-guard` channel on quarantine
- Quarantined skills require explicit council vote to reactivate or retire
- **Kill metric**: If >3 skills quarantined in a single day, circuit breaker pauses ALL extraction for 24 hours

```python
# In skill_selector.py update_reward():
if total_uses >= 5 and (successful_uses / total_uses) < 0.3:
    await self.db.execute(
        "UPDATE skill_library SET status = 'quarantine' WHERE skill_id = %s",
        (skill_id,)
    )
    logger.warning(f"QUARANTINE: Skill {skill_id} — success rate {successful_uses/total_uses:.2f} after {total_uses} uses")
    # Alert Eagle Eye
```

### Condition 2: Turtle's 7GEN — Council Verification Fallback Path

**Concern**: Council verification could become a bottleneck or single-point-of-failure. If the council is down, skills pile up unverified or the pipeline stalls.

**Feature**: **Candidate queue with timeout**. Skills never auto-approve, but they never block either:
- If council is unreachable for >60 seconds, skill enters `candidate` status (not `active`)
- Candidates are queued in `skill_library` with `status = 'candidate'`
- Next available council window processes the candidate queue (FIFO)
- Candidates are NEVER injected into Jr tasks — only `active` skills are selectable
- **Max candidate queue**: 20. If exceeded, oldest candidates are dropped with a log entry
- **Reversibility**: Any `active` skill can be moved to `retired` by a single council member's request (no full vote needed for retirement, only for activation)

### Condition 3: Raven's STRATEGY — Phased Sprint Allocation

**Concern**: 21 SP displaces other work. 142-task backlog in the Jr queue. SkillRL should wait until the backlog clears.

**Feature**: **Phase 1 only this sprint (8 SP)**. Phases 2-4 explicitly deferred:
- **This sprint**: Phase 1 Foundation (schema + descriptor + extractor = 8 SP)
- **Next sprint**: Phase 2 Intelligence (selector + proficiency = 5 SP) + Phase 3 Integration (SkillToolSet + Jr hooks = 8 SP)
- **Sprint after**: Phase 4 Governance + Seeding (tiered verification + seed library + drift audit = 3 SP, but blocked on Phase 3)
- SkillRL is the thing that reduces the backlog over time — skills make Jrs faster. But Raven is right that we can't do everything at once.

### Condition 4: Eagle Eye's VISIBILITY — Integrity Validation

**Concern**: Skill library data corruption lacks automated integrity check.

**Feature**: **Content hash + periodic validation**:
- On skill creation, compute `content_hash = SHA256(intent || method || tool_hints)` and store in `skill_library`
- On every skill read (selection), verify hash matches. Mismatch = auto-quarantine + critical alert
- Weekly `skill_integrity_check()` runs as part of the drift audit timer:
  - Recompute all content hashes
  - Flag any mismatches
  - Verify no `active` skills have NEVER_SEND patterns (re-scan)
  - Report to `#fire-guard` Slack channel
- Add `content_hash VARCHAR(64)` column to `skill_library` table

### Condition 5: Peace Chief's GAPS — Scalability + Interaction

**Concern**: Long-term scalability of skill library and interaction with consultation ring not addressed.

**Feature**: **Library cap + consultation ring integration roadmap**:
- Phase 1 cap: **500 active skills maximum**. If hit, auto-retire the lowest-reward skill with `total_uses > 10` (avoid retiring unexplored skills)
- Retirement log entry created with `retire_reason = 'cap_overflow'`
- **Consultation ring interaction (Phase 3)**: Skills can inform which frontier model to consult. If a skill's `tool_hints` include a specific provider (e.g., "anthropic_code_review"), the consultation ring's UCB bandit gets a soft prior from the skill's reward history. Deferred to Phase 3 — not blocking.
- **Jr executor performance**: Skill loading adds one DB query per task start. Benchmark target: <50ms overhead. If exceeded, add Redis cache layer (Phase 2).

## Build Order (Long Man Method)

### Phase 1: Foundation — THIS SPRINT (8 SP) ← Raven condition
1. **DB Migration** (1 SP) — Create `skill_library` (with `content_hash`), `skill_proficiency`, `skill_usage_log` tables on bluefin. Register `skill_rl` ring in duplo_tool_registry.
2. **SkillDescriptor** (2 SP) — Dataclass with composition logic, content_hash generation. Unit tests for skill_id determinism, to_tool_description(), compose_skills().
3. **Skill Extractor** (5 SP) — Post-task analysis via local model. Duplicate check. Council submission with candidate fallback (Turtle condition). 30-second timeout. Non-blocking. Auto-quarantine threshold (Coyote condition).

### Phase 2: Intelligence — NEXT SPRINT (5 SP)
4. **Skill Selector** — UCB1 + curriculum weighting. Optimistic prior. Category inference. Quarantine check on every selection. Integrity hash validation on read (Eagle Eye condition).
5. **Skill Proficiency** — EMA tracker. get_weakest(), get_vector(). α=0.3.

### Phase 3: Integration — NEXT SPRINT (8 SP)
6. **SkillToolSet Ring** — ToolSet implementation. Register in tool_executor.py TOOLSETS dict. load_skills_for_task() pre-loading. 500-skill cap enforcement (Peace Chief condition).
7. **Jr Executor Hook** — Post-task: call skill_extractor. Pre-task: call SkillToolSet.load_skills_for_task(). Wire both directions of the learning loop. Consultation ring soft priors (Phase 3 only).

### Phase 4: Governance + Seeding — SPRINT +2 (3 SP)
8. **Tiered Verification** — Reflex/deliberation/council tiers for skill approval based on difficulty.
9. **Seed Library** — Extract 10-15 skills from top completed Jr tasks. Hand-verify. Populate skill_library.
10. **Skill Drift Audit Timer** — Weekly check: DC violations in skill methods + content hash integrity + NEVER_SEND re-scan.

## Verification

1. **Extraction round-trip**: Complete a Jr task → skill extracted → council approves → skill appears in library → next task sees it as available tool.
2. **Curriculum bias**: After 20 tasks across 3 domains, verify proficiency tracker shows differentiated scores. Verify selector biases toward weak categories.
3. **Composition**: Create two atomic skills. Compose into compound. Verify compound has parent_skills populated, difficulty increases, tool_hints merge.
4. **NEVER_SEND**: Extract skill from task that touched node names/IPs. Verify skill method is sanitized — no infrastructure details stored.
5. **Cold skill pruning**: Create skill. Don't use it for 30 days. Verify auto-retirement fires.
6. **Retirement cascade**: Create compound skill from two atomics. Retire one atomic. Verify compound flagged for review.
7. **Pipeline isolation**: Kill skill extraction mid-process. Verify Jr task still shows as complete. No pipeline blockage.
8. **UCB exploration**: With 5 active skills, verify bandit explores all 5 within first 15 selections (not stuck on one).

## Definition of Done

- [ ] skill_library, skill_proficiency, skill_usage_log tables created on bluefin
- [ ] SkillDescriptor with composition logic
- [ ] Skill extractor runs on completed Jr tasks (async, non-blocking)
- [ ] Council verification with tiered gate (reflex/deliberation/council)
- [ ] UCB1 selector with curriculum weighting
- [ ] EMA proficiency tracker per (domain, category)
- [ ] SkillToolSet registered in tool executor
- [ ] Jr executor hooks: pre-task skill loading + post-task extraction
- [ ] NEVER_SEND sanitization on all extracted skills
- [ ] 10+ seed skills from historical Jr tasks
- [ ] Skill drift audit timer (weekly)
- [ ] Cold skill pruning (30 days unused → retire)
- [ ] All 8 verification tests pass

**Total: 21 SP, 10 Jr sub-tasks, builds on 14 existing production-tested modules.**
**Patent Candidate #8**: Self-improving skill library with governance-gated reinforcement learning. No published system combines UCB1 skill selection + council verification + curriculum learning + DC-aligned valence gate. The governance layer is the differentiator.
