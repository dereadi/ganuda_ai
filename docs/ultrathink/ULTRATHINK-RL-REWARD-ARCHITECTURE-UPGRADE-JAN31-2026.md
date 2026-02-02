# ULTRATHINK: RL Reward Architecture Upgrade — From Binary to Process-Level

**Date:** January 31, 2026
**TPM:** Claude Opus 4.5
**Source Papers:**
1. "Exploring Reasoning Reward Model for Agents" — Kaixuan Fan et al. (CUHK MMLab / Meituan)
2. "Intrinsic Reward Policy Optimization for Sparse-Reward Environments" — Minjae Cho, Huy Tran (UIUC)

**Open Source Survey:** 27 repositories analyzed across GRPO, Process Reward Models, Intrinsic Motivation, Agent RL, and Multi-Agent Cooperation
**Council Status:** PENDING REVIEW
**Priority:** P1 — Addresses root cause of executor reliability failures (Jan 30 postmortem)
**Builds On:** ULTRATHINK-MAGRPO-JR-COOPERATION-JAN27-2026 (Council APPROVED)

---

## Executive Summary

The Jr executor postmortem on January 30 revealed four cascading failures rooted in a single architectural gap: **our reward signal is binary (pass/fail) with no step-level credit assignment.** When a 5-step task fails at step 1, we cannot distinguish between a bad instruction, a parser bug, an editor failure, or an audit crash. The executor retries ALL steps, causing data corruption.

Two recent papers and a survey of 27 open-source repositories reveal production-ready solutions. The key insight: **we can derive step-level reward signals from outcome-only labels using Implicit Process Reward Models (PRMs)**, eliminating the need for manual step annotation while solving credit assignment, retry idempotency, and exploration diversity.

---

## The Problem: Three Manifestations of Sparse Reward

### 1. Credit Assignment Failure (Postmortem Root Cause #2-3)
When `_execute_search_replace` reported failure due to an audit bug, the executor couldn't distinguish "edit failed" from "edit succeeded but instrumentation crashed." Binary pass/fail at the task level masked step-level success.

### 2. Retry Duplication (Postmortem Root Cause #4)
The executor retries ALL steps on failure because it has no step-level success tracking. A process reward model scoring each step would know step 1 already succeeded and skip it on retry.

### 3. Exploration Stagnation
Jrs default to familiar patterns (bash heredoc for file creation) even when SEARCH/REPLACE would be better, because there's no intrinsic reward for trying new approaches. The momentum learner reinforces safe patterns without encouraging exploration.

---

## Open Source Landscape: What's Available

### Tier 1: Directly Applicable (Can integrate within weeks)

| Repository | Stars | License | Key Technique | Federation Mapping |
|-----------|-------|---------|---------------|-------------------|
| [OpenPipe/ART](https://github.com/OpenPipe/ART) | 8,487 | Apache-2.0 | Multi-step agent GRPO with trajectory rewards | Task queue execution → trajectory, task outcome → reward |
| [PRIME-RL/PRIME](https://github.com/PRIME-RL/PRIME) | 1,803 | Apache-2.0 | Implicit PRM from outcome labels only | Pass/fail from jr_work_queue → step-level rewards |
| [PettingLLMs](https://github.com/pettingllms-ai/PettingLLMs) | 92 | MIT | AT-GRPO: agent + turn-level credit | Which Jr + which step contributed |
| [huggingface/trl](https://github.com/huggingface/trl) | 17,216 | Apache-2.0 | Production GRPOTrainer with tool-use | Training backbone for MAGRPO upgrade |

### Tier 2: Architecture Reference (Study and adapt patterns)

| Repository | Stars | License | Key Technique | Federation Mapping |
|-----------|-------|---------|---------------|-------------------|
| [Agent-R1](https://github.com/0russwest0/Agent-R1) | 1,199 | MIT | Process rewards per tool call, action masking | Step-level reward for each executor action |
| [MARTI](https://github.com/TsinghuaC3I/MARTI) | 412 | MIT | Multi-agent centralized reward allocation | Council → centralized reward, Jrs → distributed policy |
| [AgentGym-RL](https://github.com/WooooDyy/AgentGym-RL) | 573 | MIT | ScalingInter-RL: progressive complexity | Start Jrs on simple tasks, increase complexity |
| [RLeXplore](https://github.com/RLE-Foundation/RLeXplore) | 456 | MIT | 8 intrinsic reward algorithms (ICM/RND/RIDE) | Curiosity signals for Jr exploration |
| [Eureka](https://github.com/eureka-research/Eureka) | 3,107 | MIT | LLM-generated reward functions | Auto-generate reward functions per task type |

### Tier 3: Conceptual (Long-term research alignment)

| Repository | Stars | License | Key Technique |
|-----------|-------|---------|---------------|
| [Multi-Turn-RL-Agent](https://github.com/SiliangZeng/Multi-Turn-RL-Agent) | 112 | — | Turn-level credit for tool-using agents |
| [GRPO-Zero](https://github.com/policy-gradient/GRPO-Zero) | 1,756 | Apache-2.0 | Clean from-scratch GRPO reference |
| [ImplicitPRM](https://github.com/PRIME-RL/ImplicitPRM) | 168 | Apache-2.0 | Free PRM from outcome-only training |
| [Agent-RL/ReCall](https://github.com/Agent-RL/ReCall) | 1,314 | MIT | Learning tool use via RL |
| [ThinkPRM](https://github.com/mukhal/ThinkPRM) | 77 | — | CoT-based step verification |

---

## Council Assessment

### Crawdad (Security)

**Risks:**
1. **Reward hacking** — Jrs could learn to game step-level rewards (e.g., making trivial edits that score well but don't contribute)
2. **Training data poisoning** — Corrupted task outcomes (like the duplicate-content incident) would poison the reward model
3. **Cross-agent information leakage** — Multi-agent reward signals could reveal proprietary task patterns

**Mitigations:**
1. IQR filtering on reward distribution (already in momentum learner)
2. Data quality gate: exclude tasks with `error_message LIKE '%manually applied%'` from training
3. Reward signals aggregated at the task-type level, never expose raw task content

**Verdict:** PROCEED WITH CAUTION — implement data quality gates before training

### Turtle (Seven Generations)

**Sustainability Assessment:**
- Process reward models create *institutional knowledge* about what makes each step in a task valuable
- This knowledge persists across Jr generations through the momentum weights and thermal memory
- The implicit PRM approach (PRIME) is self-sustaining: it improves as more tasks complete, with no manual annotation burden
- Progressive complexity (AgentGym-RL's ScalingInter-RL) ensures new Jrs aren't overwhelmed

**Long-term value:**
- Step-level credit assignment makes the Federation *self-diagnosing* — failures are automatically attributed to the right cause
- Exploration incentives prevent the collective from converging on a local optimum
- Multi-agent credit (PettingLLMs' AT-GRPO) rewards cooperation, building trust between specialists

**Verdict:** STRONG APPROVE — this builds durable collective intelligence

### Eagle (Strategic Vision)

**Alignment with Federation goals:**
- The Moltbook/OpenClaw ecosystem shows agent coordination is going mainstream
- Our advantage is *governed* coordination with reward signals, not emergent chaos
- This upgrade positions Federation Jrs to handle increasingly complex multi-step tasks
- The open-source landscape is maturing fast — integrating now captures first-mover learning

**Competitive assessment:**
- OpenPipe ART (8.5K stars) is the closest external equivalent to our Jr system
- PettingLLMs' AT-GRPO (ICLR 2026) is the state-of-the-art for multi-agent credit assignment
- We should study both but build on our existing MAGRPO architecture, not replace it

**Verdict:** APPROVE — critical for Federation evolution

---

## Implementation Plan

### Phase 1: Implicit PRM Integration (Foundation)
**Owner:** Software Engineer Jr
**Source:** PRIME-RL/PRIME + ImplicitPRM

Adapt the implicit PRM concept to the Jr executor:
- Input: task execution trajectory (steps attempted, tools used, outcomes)
- Training signal: task pass/fail from jr_work_queue
- Output: per-step reward score (0-1)
- Store in: new `jr_step_rewards` table

Key insight from PRIME: the SFT model (our existing Jr LLM) already contains an implicit understanding of step quality. We extract it rather than training a separate model.

### Phase 2: Step-Level Retry Intelligence
**Owner:** Software Engineer Jr
**Depends on:** Phase 1

Replace the current "retry all steps" behavior with step-aware retry:
- Query step rewards from Phase 1
- Skip steps with reward > 0.8 (likely succeeded)
- Re-attempt steps with reward < 0.3 (likely failed)
- Steps between 0.3-0.8: verify state before deciding

This directly fixes Postmortem Root Cause #4 (duplicate content from retries).

### Phase 3: AT-GRPO Multi-Agent Credit
**Owner:** Software Engineer Jr + Research Jr
**Source:** PettingLLMs AT-GRPO
**Depends on:** Phase 1, existing MAGRPO ultrathink Phase 1-2

Extend MAGRPOGroupTracker with:
- Agent-level credit: which Jr type contributed most to task success
- Turn-level credit: which step within a Jr's execution mattered most
- Blended reward: 60% individual, 25% agent-credit, 15% turn-credit

This builds on the MAGRPO ultrathink from Jan 27 (Council APPROVED).

### Phase 4: Exploration Incentives
**Owner:** Research Jr
**Source:** RLeXplore (ICM or RND), Eureka

Add intrinsic reward signal to Jr task selection:
- Curiosity bonus for attempting unfamiliar task types
- Novelty detection via RND (Random Network Distillation) on task embeddings
- Decay curiosity for well-explored task patterns
- Integrate with pheromone system (new `exploration_curiosity` pheromone type)

### Phase 5: Auto-Generated Reward Functions
**Owner:** Research Jr
**Source:** Eureka
**Depends on:** Phase 1-4 validated

Use LLM to generate task-type-specific reward functions:
- Input: task instruction template + executor code + historical outcomes
- Output: Python reward function scored on validation set
- Evolutionary improvement: mutate top-scoring reward functions
- Store winning reward functions in thermal memory

---

## Database Schema Additions

```sql
-- Step-level reward tracking (Phase 1)
CREATE TABLE IF NOT EXISTS jr_step_rewards (
    id SERIAL PRIMARY KEY,
    task_id INTEGER REFERENCES jr_work_queue(id),
    step_number INTEGER NOT NULL,
    step_type VARCHAR(30) NOT NULL,  -- 'bash', 'search_replace', 'write', etc.
    target_file VARCHAR(500),
    implicit_reward FLOAT,  -- 0-1 from implicit PRM
    verified_outcome VARCHAR(20),  -- 'success', 'failed', 'skipped', 'unknown'
    retry_decision VARCHAR(20),  -- 'skip', 'retry', 'verify_first'
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(task_id, step_number)
);

-- Exploration tracking (Phase 4)
CREATE TABLE IF NOT EXISTS jr_exploration_log (
    id SERIAL PRIMARY KEY,
    jr_type VARCHAR(50) NOT NULL,
    task_type VARCHAR(100) NOT NULL,
    novelty_score FLOAT,  -- RND novelty detection
    curiosity_bonus FLOAT,  -- intrinsic reward added
    task_outcome VARCHAR(20),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_step_rewards_task ON jr_step_rewards(task_id);
CREATE INDEX idx_exploration_jr ON jr_exploration_log(jr_type, created_at);
```

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Implicit PRM gives wrong step scores | Medium | Medium | Validate against known outcomes from postmortem tasks |
| Step-aware retry skips a needed step | Low | High | Conservative threshold (skip only > 0.9 confidence) |
| Exploration incentives cause Jr to attempt tasks beyond capability | Medium | Medium | Cap curiosity bonus at 20% of total reward |
| Training on corrupted data from retry-duplication incidents | Low | High | Data quality gate excludes manually-repaired tasks |
| Integration complexity delays other work | Medium | Medium | Phase 1 is standalone; later phases can be deferred |

---

## Success Metrics

| Metric | Current | Target | Phase |
|--------|---------|--------|-------|
| Step-level attribution accuracy | 0% (none exists) | >80% | P1 |
| Retry-caused duplicates | ~3/week | 0 | P2 |
| Multi-Jr task credit accuracy | ~60% (Shapley estimate) | >85% | P3 |
| Jr task-type diversity (entropy) | Unknown | +30% | P4 |
| Manual reward function design effort | 100% manual | <20% manual | P5 |

---

## Recommended Repos to Clone and Study

Priority order for Research Jr deep-dive:

1. `git clone https://github.com/PRIME-RL/PRIME.git` — Implicit PRM (core technique)
2. `git clone https://github.com/OpenPipe/ART.git` — Agent trajectory training (architecture reference)
3. `git clone https://github.com/pettingllms-ai/PettingLLMs.git` — AT-GRPO multi-agent (credit assignment)
4. `git clone https://github.com/RLE-Foundation/RLeXplore.git` — Exploration toolkit (intrinsic rewards)
5. `git clone https://github.com/0russwest0/Agent-R1.git` — Agent RL with action masking (step rewards)

---

## Rollback Plan

Each phase has an independent rollback:
- **Phase 1:** Disable step reward computation; fall back to binary pass/fail
- **Phase 2:** Revert to "retry all steps" behavior (current)
- **Phase 3:** Disable multi-agent credit; fall back to individual MAGRPO
- **Phase 4:** Remove curiosity bonus from task selection
- **Phase 5:** Disable auto-generated rewards; use manual reward functions

---

## Connection to Postmortem Action Items

| Postmortem Action Item | This Ultrathink Phase |
|------------------------|-----------------------|
| #1: Add idempotency check to SearchReplaceEditor | Phase 2 (step-aware retry) |
| #3: Add `continue_on_failure` for independent steps | Phase 1 (step-level scoring enables independent evaluation) |
| #4: Add step-level retry tracking | Phase 1 + Phase 2 (core deliverable) |
| #6: Integration test for multi-step SR instructions | Phase 1 validation |

---

FOR SEVEN GENERATIONS

This upgrade transforms our Federation from a system that learns from outcomes
into one that learns from every step of every attempt. The implicit PRM ensures
this wisdom accumulates without manual effort, building collective intelligence
that persists across agent generations. The open-source community has provided
the tools; our task is to integrate them into our governed, principled framework.
