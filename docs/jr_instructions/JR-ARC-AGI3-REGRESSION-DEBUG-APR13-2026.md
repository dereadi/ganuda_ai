# JR INSTRUCTION: ARC-AGI-3 Agent Regression Debug

**JR ID:** JR-ARC-AGI3-REGRESSION-DEBUG-APR13-2026
**FROM:** TPM (Flying Squirrel / Stoneclad)
**TO:** IT Triad Jr (`it_triad_jr`)
**PRIORITY:** P1
**DATE:** April 13, 2026
**TARGET:** /ganuda/services/arc_agi_3/
**DEADLINE CONTEXT:** M1 contest deadline June 30, 2026 (78 days). Every day the agent is broken is a day lost.

## Context

The ARC-AGI-3 agent experienced a performance regression between two swarm batches on April 12:

- **Apr 12 16:18 UTC (working):** 5 games × 5 instances. vc33 reached L2, lp85 reached L2, sp80 reached L1.
- **Apr 12 19:24 UTC (broken):** 7 games × 30 instances. ALL games stalled at L0. Zero levels across 210 instances.
- **Apr 13 08:00 UTC (still broken):** Individual runs show timeout outcomes, 0 transitions collected, 0 unique states.

The architecture pivot (Apr 12 Council vote #526e0696) moved to a three-tier system:
- Tier 1: Graph explorer (algorithmic, no LLM) — 95% of actions
- Tier 2: World model / MCTS — Jr value estimation
- Tier 3: Goal inferrer — Council-level reasoning on stall

The regression appears to be in the **perception/frame processing layer**, not the strategy layer. The agent isn't collecting any state transitions, which means it can't even begin exploring.

## Acceptance Criteria

1. Root cause of the Apr 12 regression identified
2. Agent restored to at least Apr 12 morning performance (L2 on known-solvable games)
3. Swarm test confirming fix across multiple games
4. No regressions in working functionality

---

## TASK 1 — Diff the working vs broken configurations

**Intent:** Find what changed between the working morning run and the broken evening run.

**Steps:**

1. Compare the two swarm result files:
   - Working: `/ganuda/services/arc_agi_3/swarm_results/swarm_20260412T161807.json` (or closest timestamp)
   - Broken: `/ganuda/services/arc_agi_3/swarm_results/swarm_20260412T192420.json`
   
2. Check for configuration differences:
   - Agent parameters (timeouts, action limits, tier thresholds)
   - Browser/Playwright settings
   - LLM endpoint configuration (vLLM URL, model path, temperature)
   - Frame processing parameters (hash algorithm, resolution, crop regions)

3. Check git history for changes between the two runs:
   ```bash
   git log --since="2026-04-12T16:00:00Z" --until="2026-04-12T20:00:00Z" -- services/arc_agi_3/
   ```

4. Check if any working-tree modifications exist:
   ```bash
   git diff -- services/arc_agi_3/
   git diff --stat -- services/arc_agi_3/
   ```

5. Report: exact diff between working and broken state.

**Acceptance:** Root cause hypothesis documented with evidence.

---

## TASK 2 — Diagnose the frame processing failure

**Intent:** The Apr 13 experiences show 0 transitions collected and 0 unique states. The perception layer is not seeing the game.

**Steps:**

1. Read the most recent experience files:
   ```
   /ganuda/services/arc_agi_3/experiences/cn04_20260413T130319Z.json
   /ganuda/services/arc_agi_3/experiences/lp85_20260413T130026Z.json
   ```
   Look for: `transitions_collected`, `unique_states`, `cwm_metrics`, error messages, frame data.

2. Read `frame_processor.py` (761 lines) — understand the perception pipeline:
   - How does it capture frames from the browser?
   - How does it hash states?
   - What could cause it to return zero transitions?

3. Check for Playwright/browser issues:
   - Is the browser actually launching?
   - Is the game URL (`https://arcprize.org/tasks/{task_id}`) reachable?
   - Are there screenshots being captured?
   - Check for any certificate, network, or timeout errors

4. Check for vLLM dependency:
   - Does frame processing depend on the LLM endpoint?
   - If localhost:8000 was down during the evening batch, would that break perception?
   - The HyDE generation was timing out on port 8000 today (observed during Council vote) — could this affect the agent?

5. Run a single-game diagnostic:
   ```bash
   cd /ganuda/services/arc_agi_3
   python3 -c "
   from frame_processor import FrameProcessor
   fp = FrameProcessor()
   # Test if frame capture works at all
   print(f'Processor initialized: {fp}')
   "
   ```

6. Report: what specifically is failing in the perception pipeline.

**Acceptance:** Specific failure point identified (browser, frame capture, hashing, LLM dependency, or network).

---

## TASK 3 — Check the swarm runner for configuration issues

**Intent:** The working batch used 5 instances per game. The broken batch used 30. The swarm runner may have a concurrency or resource issue at scale.

**Steps:**

1. Read `swarm_runner.py` (795 lines) — understand:
   - How many parallel browser instances does it launch?
   - Is there a resource limit (CPU, memory, GPU, browser contexts)?
   - Does it share a single vLLM endpoint across all instances?

2. Check system resources during a swarm run:
   - How much RAM does 30 parallel Playwright instances consume?
   - Could the system be OOM-killing browser processes?
   - Check `dmesg | grep -i oom` and `journalctl -k | grep -i kill`

3. Check if the 5-instance batch and 30-instance batch used different parameters:
   - Different agent class? Different timeout? Different game list?
   - The 5-instance batch tested vc33, lp85, sp80, sb26, r11l
   - The 30-instance batch tested dc22, g50t, ka59, lf52, re86, sc25, wa30
   - **These are DIFFERENT games.** The regression might not be a regression at all — it might be that the second set of games is simply harder.

4. Test: run the WORKING games (vc33, lp85, sp80) with the CURRENT code at 5 instances:
   ```bash
   cd /ganuda/services/arc_agi_3
   python3 swarm_runner.py --games vc33,lp85,sp80 --instances 5 --timeout 120
   ```
   (Adjust command syntax to match actual CLI — read swarm_runner.py first)

5. Report: 
   - Is it a code regression or a game-difficulty difference?
   - Resource utilization at 30 instances
   - Results from re-running known-solvable games

**Acceptance:** Clear answer on whether this is a regression or game-difficulty effect, plus resource assessment.

---

## TASK 4 — Validate Tier 1 (graph explorer) in isolation

**Intent:** The graph explorer is the foundation. If it's broken, nothing else matters. Test it independently.

**Steps:**

1. Read `graph_explorer.py` (671 lines) — understand:
   - How it builds the state graph
   - Frontier tracking and BFS distance
   - Priority groups and action selection
   - The 3-strike suspicious transition rule

2. Read `ganuda_agent.py` (501 lines) — understand:
   - How the graph explorer integrates with the main agent loop
   - Level-up detection logic
   - When does it escalate to Tier 2 or Tier 3?

3. Check the working experience files (Apr 12 morning) to understand what a successful run looks like:
   - How many states were explored?
   - How many actions were taken?
   - What was the action-to-level ratio?

4. Compare with broken experience files:
   - Where does the execution diverge?
   - Is the graph explorer getting valid state data to work with?
   - Is it getting stuck in a loop?

5. Report: Is the graph explorer itself functioning correctly, or is it being starved of input from the perception layer?

**Acceptance:** Graph explorer validated or specific failure identified.

---

## TASK 5 — Fix and verify

**Intent:** Apply the fix for whatever root cause was found in Tasks 1-4.

**Steps:**

1. Based on findings, implement the fix. Likely scenarios:
   - **If perception layer failure:** Fix frame capture, browser launch, or LLM dependency
   - **If resource exhaustion at 30 instances:** Add resource limits, reduce concurrency
   - **If game-difficulty (not a regression):** Document which games are solvable and which aren't. Focus development on expanding the solvable set.
   - **If vLLM timeout dependency:** Add fallback when LLM is unavailable (graph explorer should work WITHOUT LLM for Tier 1)

2. Re-run the known-solvable games (vc33, lp85, sp80) and verify L1+ is achieved:
   ```bash
   # Run 5 instances of each, capture results
   ```

3. Run a broader swarm (at least 5 games × 10 instances) and capture results

4. Save results to `/ganuda/services/arc_agi_3/swarm_results/` with timestamp

**Acceptance:** Known-solvable games reach L1+. Results saved. No regressions.

---

## TASK 6 — Status report

**Intent:** TPM needs a clear picture for the M1 sprint plan.

Report must include:

1. Root cause of the regression (one sentence)
2. Fix applied (one sentence)
3. Current success rate: which games reach L1, L2, L3?
4. Current failure modes: why do unsolved games fail?
5. Biggest bottleneck: perception, exploration, or reasoning?
6. Estimated games solvable with current architecture (out of the contest set)
7. Top 3 improvements that would increase score most

Post to thermal memory at 92°C with tags `arc_agi_3,regression_fix,m1_sprint,contest` and source_triad `it_triad_jr`.

---

## What this instruction does NOT do

- Does NOT change the three-tier architecture (that's Council-ratified)
- Does NOT submit to the contest (patent gate must clear first)
- Does NOT modify the graph explorer algorithm unless it's provably buggy
- Does NOT add new features — this is a debug/fix instruction

## Important Note on Game Differences

The "regression" may not be a regression. The two batches tested DIFFERENT games. Before concluding the code is broken, verify by re-running the SAME games that worked before. If vc33/lp85/sp80 still work with current code, the agent isn't regressed — the second batch just had harder games. This changes the response from "fix the bug" to "expand capability."
