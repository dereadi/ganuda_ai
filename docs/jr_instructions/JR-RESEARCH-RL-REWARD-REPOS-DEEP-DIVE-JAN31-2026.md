# Jr Instruction: Deep-Dive Top RL Reward Repositories

**Task ID:** RESEARCH-RL-REWARD-001
**Assigned To:** Research Jr
**Priority:** P1
**Created:** January 31, 2026
**Depends On:** None
**Estimated Steps:** 12

---

## Objective

Clone and analyze the top 5 open-source repositories from the RL Reward Architecture survey. For each repo, produce a technical summary documenting: architecture, key algorithms, integration points with our MAGRPO/momentum learner, and specific files/functions to adapt.

---

## Steps

### Step 1: Clone repositories

```bash
mkdir -p /ganuda/experiments/rl_reward_research && cd /ganuda/experiments/rl_reward_research
git clone --depth 1 https://github.com/PRIME-RL/PRIME.git
git clone --depth 1 https://github.com/OpenPipe/ART.git
git clone --depth 1 https://github.com/pettingllms-ai/PettingLLMs.git
git clone --depth 1 https://github.com/RLE-Foundation/RLeXplore.git
git clone --depth 1 https://github.com/0russwest0/Agent-R1.git
```

### Step 2: Analyze PRIME (Implicit PRM)

Read and document:
- How the implicit PRM extracts step-level rewards from outcome-only labels
- The Q-function approach for per-token reward
- How it integrates with online RL training
- Key files: training scripts, reward computation, PRM inference
- **Specific question:** Can we apply this to Jr task execution trajectories without fine-tuning a model? Or do we need to train on our task history?

### Step 3: Analyze OpenPipe ART

Read and document:
- The Trajectory abstraction (how agent interactions become training data)
- RULER module for automatic reward generation
- GSPO (Group Sequence Policy Optimization) implementation
- How tool-use is supported during training
- **Specific question:** Can ART's trajectory format capture our Jr executor step sequences (bash commands, SEARCH/REPLACE blocks, file writes)?

### Step 4: Analyze PettingLLMs (AT-GRPO)

Read and document:
- Agent-wise vs turn-wise credit assignment
- Multi-level reward system (process, agent, global)
- How it extends standard GRPO for multiple agents
- **Specific question:** How does AT-GRPO handle heterogeneous agents (our Jrs have different specialties)? Does it assume homogeneous agents?

### Step 5: Analyze RLeXplore

Read and document:
- ICM (Intrinsic Curiosity Module) implementation
- RND (Random Network Distillation) implementation
- How intrinsic rewards are combined with extrinsic rewards
- Plug-and-play API design
- **Specific question:** Can we use RND on task embeddings (not game states) to detect novel task patterns?

### Step 6: Analyze Agent-R1

Read and document:
- BaseTool / BaseToolEnv abstractions
- Process reward per tool call implementation
- Action masking for credit assignment
- MDP formulation of LLM agent behavior
- **Specific question:** Can we model our executor's step sequence as an MDP where states are file-system states and actions are edit operations?

### Step 7: Write comparison matrix

Create a comparison matrix at `/ganuda/experiments/rl_reward_research/COMPARISON_MATRIX.md`:

| Feature | PRIME | ART | PettingLLMs | RLeXplore | Agent-R1 |
|---------|-------|-----|-------------|-----------|----------|
| Step-level rewards | | | | | |
| Multi-agent support | | | | | |
| Tool-use integration | | | | | |
| Outcome-only training | | | | | |
| Exploration incentives | | | | | |
| Production readiness | | | | | |
| Integration effort | | | | | |

### Step 8: Identify integration candidates

For each repo, identify the specific Python files/functions that could be adapted for:
1. `jr_step_rewards` computation (replacing binary pass/fail)
2. `magrpo_tracker.py` enhancement (multi-agent credit)
3. `jr_momentum_learner.py` enhancement (exploration incentives)
4. `task_executor.py` enhancement (step-aware retry)

### Step 9: Check dependency compatibility

For each repo, check:
- Python version requirements (we run 3.12)
- PyTorch version requirements
- Any GPU requirements (we have A800 80GB on bluefin cluster)
- Conflicts with existing cherokee_venv packages

### Step 10: Write integration roadmap

Create `/ganuda/experiments/rl_reward_research/INTEGRATION_ROADMAP.md` with:
- Recommended integration order
- Estimated effort per integration
- Risk assessment per integration
- Minimum viable integration (what's the smallest change that gets us step-level rewards?)

### Step 11: Prototype implicit PRM scoring

Write a proof-of-concept script at `/ganuda/experiments/rl_reward_research/prototype_step_scorer.py` that:
- Takes a completed Jr task from jr_work_queue (by ID)
- Extracts the step sequence from the task instruction
- Uses the local LLM (or API) to score each step's likely contribution to the outcome
- Outputs step-level reward scores
- This is a PROTOTYPE only — not production code

### Step 12: Report findings

Write final report at `/ganuda/experiments/rl_reward_research/RESEARCH_REPORT.md` summarizing:
- Top 3 techniques to integrate (ranked by impact/effort ratio)
- Specific code to adapt (file paths within cloned repos)
- Recommended Phase 1 implementation plan
- Risks and mitigations

---

## Output Artifacts

1. `/ganuda/experiments/rl_reward_research/` — Cloned repos
2. `/ganuda/experiments/rl_reward_research/COMPARISON_MATRIX.md`
3. `/ganuda/experiments/rl_reward_research/INTEGRATION_ROADMAP.md`
4. `/ganuda/experiments/rl_reward_research/prototype_step_scorer.py`
5. `/ganuda/experiments/rl_reward_research/RESEARCH_REPORT.md`

---

## Success Criteria

- All 5 repos cloned and analyzed
- Comparison matrix complete with specific file references
- Integration roadmap identifies minimum viable integration
- Prototype step scorer runs on at least one real task from queue
- Report recommends clear Phase 1 path

---

## Context

Reference documents:
- `/ganuda/docs/ultrathink/ULTRATHINK-RL-REWARD-ARCHITECTURE-UPGRADE-JAN31-2026.md`
- `/ganuda/docs/ultrathink/ULTRATHINK-MAGRPO-JR-COOPERATION-JAN27-2026.md`
- `/ganuda/docs/kb/KB-JR-EXECUTOR-SEARCH-REPLACE-POSTMORTEM-JAN30-2026.md`

Current MAGRPO code: `/ganuda/lib/magrpo_tracker.py`
Current momentum learner: `/ganuda/lib/jr_momentum_learner.py`
Current executor: `/ganuda/jr_executor/task_executor.py`
