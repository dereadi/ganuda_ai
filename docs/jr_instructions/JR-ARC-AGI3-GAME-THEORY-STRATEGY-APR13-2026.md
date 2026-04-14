# JR INSTRUCTION: ARC-AGI-3 Game Theory Strategy Switching

**JR ID:** JR-ARC-AGI3-GAME-THEORY-STRATEGY-APR13-2026
**FROM:** TPM (Flying Squirrel / Stoneclad)
**TO:** IT Triad Jr (`it_triad_jr`)
**PRIORITY:** P1
**DATE:** April 13, 2026
**TARGET:** /ganuda/services/arc_agi_3/
**DEPENDS ON:** JR-ARC-AGI3-REGRESSION-DEBUG-APR13-2026 (Task #1502 — must complete first to confirm agent is functional)
**CONTEST DEADLINE:** M1 June 30, 2026 (78 days)

## Context

The ARC-AGI-3 agent currently uses a **level-based** strategy picker:
- Level 1: Pure graph exploration
- Level 2: Graph + CWM after 50 actions
- Level 3+: Deep MCTS

This is wrong. The strategy should be **game-characteristic-based**, not level-based. Different games have different payoff structures. Some reward exploration (many states, deterministic transitions). Some punish it (few states, time-sensitive, action-budget-constrained). The agent should detect which kind of game it's in and adapt.

## Game Theory Framework

### Three Strategy Modes

**1. EXPLORER (Maximin — minimize worst case)**
- Explore thoroughly before committing
- Exhaust all action groups before advancing
- High tolerance for game-overs (they're information)
- Best for: games with large state spaces, deterministic transitions, and clear level-up signals
- Risk: burns action budget if game is simple

**2. EXPLOITER (Maximax — maximize best case)**
- Commit early to promising actions
- Skip low-probability action groups
- Low tolerance for game-overs (reset quickly)
- Best for: games with small state spaces, obvious patterns, or time pressure
- Risk: misses non-obvious solutions

**3. ADAPTIVE (Nash equilibrium search)**
- Start as EXPLORER, track payoff metrics
- Switch to EXPLOITER when marginal value of exploration drops below threshold
- The "marginal value of exploration" = new unique states discovered per action
- When this drops below a threshold (e.g., <0.05 new states per action over last 50 actions), switch
- Best for: unknown games where you don't know the payoff structure yet
- This should be the DEFAULT mode

### Payoff Metrics to Track

The agent should compute these in real-time during play:

```python
@dataclass
class GamePayoffMetrics:
    # Action effectiveness
    action_success_rate: Dict[str, float]  # action_type -> success %
    
    # Exploration value
    unique_states_per_action: float  # rolling window over last 50 actions
    frontier_coverage: float  # explored / total discovered nodes
    
    # Game characteristics (detected, not configured)
    transition_determinism: float  # 0-1, how often same action → same result
    state_space_growth_rate: float  # new states per 100 actions
    game_over_rate: float  # game-overs per 100 actions
    
    # Derived strategy signal
    exploration_marginal_value: float  # diminishing returns indicator
```

### Strategy Selection Logic

```python
def select_strategy(metrics: GamePayoffMetrics, level: int, actions_taken: int) -> str:
    """Game-theory-informed strategy selection."""
    
    # Phase 1: Always start as ADAPTIVE for first 100 actions
    if actions_taken < 100:
        return "ADAPTIVE"
    
    # Phase 2: Classify game based on observed metrics
    
    # High determinism + large state space = EXPLORER
    if metrics.transition_determinism > 0.9 and metrics.state_space_growth_rate > 0.3:
        return "EXPLORER"
    
    # Low state space growth + high action success = EXPLOITER
    if metrics.state_space_growth_rate < 0.05 and max(metrics.action_success_rate.values()) > 0.3:
        return "EXPLOITER"
    
    # Marginal value of exploration dropping = switch to EXPLOITER
    if metrics.exploration_marginal_value < 0.05:
        return "EXPLOITER"
    
    # Default: stay ADAPTIVE
    return "ADAPTIVE"
```

### How Each Strategy Modifies Behavior

**EXPLORER mode changes:**
- `graph_explorer.choose_edge()`: Prefer untested edges even if further from frontier
- CWM synthesis threshold: HIGHER (100 actions instead of 50) — keep exploring longer
- Basin-hop trigger: LOWER (every 3 game-overs instead of 5) — try new openings faster
- Group advancement: SLOWER — exhaust all edges in current group before advancing

**EXPLOITER mode changes:**
- `graph_explorer.choose_edge()`: Prefer edges with highest historical success rate
- CWM synthesis threshold: LOWER (20 actions) — start planning early
- Basin-hop trigger: HIGHER (every 8 game-overs) — commit to current approach longer
- Group advancement: FASTER — skip to most effective group immediately
- Action selection: Weight by `action_success_rate` instead of random

**ADAPTIVE mode changes:**
- Starts as EXPLORER
- Every 50 actions, recompute `exploration_marginal_value`
- If marginal value drops below threshold, switch to EXPLOITER
- If switched to EXPLOITER and success rate drops, switch back to EXPLORER
- Log every strategy switch for post-game analysis

## Implementation Plan

### TASK 1 — Add GamePayoffMetrics tracking to ganuda_agent.py

**File:** `/ganuda/services/arc_agi_3/ganuda_agent.py`

**Changes:**

1. Add `GamePayoffMetrics` dataclass (see above)

2. In the main `choose_action()` loop, update metrics after each action:
   ```python
   # After recording test result
   self._update_payoff_metrics(action_type, success, new_state_discovered)
   ```

3. Add `_update_payoff_metrics()` method:
   - Track rolling window of last 50 actions
   - Compute `unique_states_per_action` = new unique states in last 50 / 50
   - Compute `transition_determinism` = (same action, same result) count / total repeated actions
   - Compute `state_space_growth_rate` = new states in last 100 / 100
   - Compute `exploration_marginal_value` = unique_states_per_action trend (declining = low)

4. Expose metrics for deep_solver.py to read

**Acceptance:** Metrics are computed and logged every 50 actions. No behavior changes yet.

### TASK 2 — Add strategy selection to deep_solver.py

**File:** `/ganuda/services/arc_agi_3/deep_solver.py`

**Changes:**

1. Replace `pick_strategy(level)` with `pick_strategy(level, metrics)`:
   ```python
   def pick_strategy(level: int, metrics: GamePayoffMetrics = None) -> str:
       if metrics is None:
           # Fallback to level-based (backward compatible)
           return _level_based_strategy(level)
       return select_strategy(metrics, level, metrics.total_actions)
   ```

2. Pass metrics from agent to deep_solver on each strategy check

3. Log strategy switches:
   ```
   [STRATEGY] Switched from EXPLORER → EXPLOITER at action 342 
   (marginal_value=0.03, determinism=0.95, growth_rate=0.02)
   ```

**Acceptance:** Strategy selection uses game characteristics when available, falls back to level-based when not.

### TASK 3 — Modify graph_explorer.py edge selection by strategy

**File:** `/ganuda/services/arc_agi_3/graph_explorer.py`

**Changes to `choose_edge()`:**

1. Accept optional `strategy` parameter:
   ```python
   def choose_edge(self, current_node, strategy: str = "ADAPTIVE") -> Tuple[int, str]:
   ```

2. **EXPLORER mode:** Current behavior (random from untested, navigate to frontier). No change needed — this IS the explorer.

3. **EXPLOITER mode:** When choosing among tested edges, weight by success rate:
   ```python
   if strategy == "EXPLOITER":
       # Among candidates, prefer highest success rate
       weighted = [(i, self._action_success_rates.get(i, 0.5)) for i in candidates]
       # Softmax selection weighted by success rate
       weights = [w for _, w in weighted]
       edge_idx = random.choices([i for i, _ in weighted], weights=weights, k=1)[0]
   ```

4. **ADAPTIVE mode:** Use EXPLORER behavior but track when to switch

**Acceptance:** Edge selection adapts based on strategy mode. EXPLORER behavior unchanged. EXPLOITER prefers proven actions.

### TASK 4 — Modify CWM synthesis timing by strategy

**File:** `/ganuda/services/arc_agi_3/deep_solver.py`

**Changes to `_maybe_synthesize_cwm()`:**

```python
def _maybe_synthesize_cwm(self, level: int, strategy: str):
    if strategy == "EXPLORER":
        threshold = 100  # Explore longer before synthesizing
    elif strategy == "EXPLOITER":
        threshold = 20   # Synthesize early, plan fast
    else:  # ADAPTIVE
        threshold = 50   # Current default
    
    if actions_on_level >= threshold and not cwm_active:
        if cwm.store.ready_for_synthesis():
            cwm.attempt_synthesis()
```

**Acceptance:** CWM synthesis timing adapts to strategy.

### TASK 5 — Modify basin-hop trigger by strategy

**File:** `/ganuda/services/arc_agi_3/ganuda_agent.py`

**Changes:**

```python
def _basin_hop_interval(self, strategy: str) -> int:
    if strategy == "EXPLORER":
        return 3   # Try new openings faster
    elif strategy == "EXPLOITER":
        return 8   # Commit to current approach longer
    else:
        return 5   # Current default
```

**Acceptance:** Basin-hop frequency adapts to strategy.

### TASK 6 — Run comparative swarm test

**Intent:** Test all three strategies against the known game set to measure impact.

**Steps:**

1. Run baseline (current code, no strategy changes) on all 25 games × 3 instances:
   ```bash
   cd /ganuda/services/arc_agi_3
   python swarm_runner.py --all --instances 3 --actions 3000
   ```
   Save results.

2. Run with game-theory strategy (ADAPTIVE default) on same 25 games × 3 instances:
   ```bash
   python swarm_runner.py --all --instances 3 --actions 3000 --strategy adaptive
   ```
   Save results.

3. Compare:
   - Total levels solved (baseline vs adaptive)
   - Per-game improvement/regression
   - Strategy switches logged (when did ADAPTIVE switch to EXPLOITER?)
   - Action efficiency (levels per action)

4. Run targeted test on known-solvable games (vc33, lp85, sp80) × 10 instances with each strategy mode forced:
   ```bash
   python swarm_runner.py vc33 lp85 sp80 --instances 10 --strategy explorer
   python swarm_runner.py vc33 lp85 sp80 --instances 10 --strategy exploiter
   python swarm_runner.py vc33 lp85 sp80 --instances 10 --strategy adaptive
   ```

5. Report which strategy mode works best for which games.

**Acceptance:** Comparative data showing strategy impact. Results saved to swarm_results/.

### TASK 7 — Store game-strategy profiles in experience bank

**File:** `/ganuda/services/arc_agi_3/game_experience.py`

**Changes:**

Add to experience signature:
```python
"optimal_strategy": "EXPLOITER",  # or EXPLORER, ADAPTIVE
"strategy_switches": [
    {"action": 150, "from": "EXPLORER", "to": "EXPLOITER", "reason": "marginal_value=0.02"}
],
"payoff_metrics_at_best_level": {
    "transition_determinism": 0.95,
    "state_space_growth_rate": 0.02,
    "exploration_marginal_value": 0.01
}
```

On future plays of the same game, bootstrap with the stored optimal strategy instead of starting from ADAPTIVE.

**Acceptance:** Experience bank stores strategy data. Future plays of known games start with the proven strategy.

---

## Prisoner's Dilemma Application: Action Group Selection

One specific game-theory insight for the edge selection:

The agent faces a **Volunteer's Dilemma** when choosing between action groups. Arrow keys (group 0) are "safe" — low payoff but low cost. Click actions (group 1+) are "risky" — higher potential payoff but more expensive (more actions to exhaust).

Current behavior: exhaust group 0 before trying group 1. This is maximin (minimize worst case).

**Game-theory fix:** Track the **expected value** of each group:
```
EV(group) = success_rate(group) × payoff(group) - cost(group)
```

Where:
- `success_rate` = fraction of actions in this group that led to new states
- `payoff` = average new states discovered per successful action
- `cost` = average actions needed to find a success

If group 1's EV exceeds group 0's EV, promote group 1 to higher priority. This allows the agent to discover that click actions are more valuable than arrow keys for a specific game.

---

## What This Does NOT Do

- Does NOT change the three-tier architecture
- Does NOT modify frame processing or perception
- Does NOT add new action types
- Does NOT require LLM changes
- Does NOT affect the experience bank schema (only adds fields)

## Reporting

Post completion SITREP to thermal memory at 92°C with tags `arc_agi_3,game_theory,strategy_switching,m1_sprint` and source_triad `it_triad_jr`. Include:
- Baseline vs adaptive comparative results
- Per-game strategy profiles
- Biggest wins and biggest regressions
- Recommended default strategy for M1 submission
