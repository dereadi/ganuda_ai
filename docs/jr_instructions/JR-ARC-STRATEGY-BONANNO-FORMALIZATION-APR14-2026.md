# Jr Instruction: ARC-AGI-3 Strategy Mode Formalization (Bonanno Ch 3/4/6)

**Task ID**: ARC-STRAT-BONANNO-001
**Priority**: P1
**Date**: April 14, 2026
**Tag**: it_triad_jr
**Reference**: Bonanno, *Game Theory* 3rd Ed (2024), Ch 3 (p.77-120), Ch 4 (p.121-173), Ch 6 (p.203-236)
**Upstream**: `/ganuda/docs/reference/Bonanno-GameTheory-3rdEd-2024.pdf`
**Depends On**: Existing `/ganuda/services/arc_agi_3/game_strategy.py` (StrategyTracker, PayoffMetrics)
**Contest Deadline**: M1 — June 30, 2026
**Council Vote**: #526e0696 (ARC-AGI-3 architecture approved)

---

## Context

The ARC-AGI-3 agent at `/ganuda/services/arc_agi_3/game_strategy.py` already has four strategy modes (EXPLORER, EXPLOITER, ADAPTIVE, RANDOMIZER) with a `select_strategy()` function that switches based on threshold heuristics. This works but it's ad-hoc — the thresholds (0.9, 0.3, 0.7, 0.05, etc.) were hand-tuned.

Bonanno gives us the formal machinery to replace these heuristics:

1. **Ch 3: Backward Induction (p.81-90)** — For perfect-information games (deterministic, fully observable state space). The agent should work backward from known goal states. Currently, the EXPLOITER mode approximates this but doesn't actually do backward induction — it just favors proven edges.

2. **Ch 4: Imperfect Information + Subgame-Perfect Equilibrium (p.121-145)** — For games where the agent doesn't know which transformation rule applies. Section 4.1 (Imperfect Information) formalizes what our agent faces: it sees the grid but doesn't know the rule. Section 4.4 (Subgame-Perfect Equilibrium) tells us when to commit vs. keep options open. Currently, ADAPTIVE approximates this.

3. **Ch 6.2-6.3: Mixed Strategies + Computing Nash Equilibria (p.206-216)** — For stochastic games where deterministic play fails. The RANDOMIZER mode already uses uniform randomization, but Bonanno shows that the *optimal* mix is computed from the payoff matrix, not uniform. The support enumeration method (§6.3) gives us the actual probabilities.

The key upgrade: instead of "if determinism < 0.7 then RANDOMIZER," we build the actual game-theoretic objects (game trees, information sets, payoff matrices) from observed data and derive the strategy mathematically.

---

## Objective

Extend `game_strategy.py` with three formal strategy components that replace heuristic thresholds with game-theoretic reasoning. Each component is a standalone function that the existing `select_strategy()` can call.

---

## File to Modify

1. `/ganuda/services/arc_agi_3/game_strategy.py` — Add formal strategy components

---

## Implementation

Add the following three components BELOW the existing code in `game_strategy.py`. Do not modify the existing `PayoffMetrics`, `StrategyTracker`, or `get_strategy_params` — those are working and tested. The new code extends `select_strategy()` with formal backing.

### Component 1: Backward Induction Engine (Bonanno Ch 3, §3.2)

```python
# ============================================================
# BONANNO FORMALIZATION — Ch 3: Backward Induction
# ============================================================
# When the game has perfect information (high determinism, known
# goal state), backward induction finds the optimal path.
#
# Bonanno §3.2 (p.81): "Start from the terminal nodes and work
# backward, at each node selecting the action that leads to the
# best outcome for the player who moves at that node."
#
# In ARC-AGI-3: the "terminal node" is the goal state (puzzle solved).
# Backward induction applies when:
#   1. We know the goal state (GoalInferrer has a candidate)
#   2. Transitions are deterministic (same action → same result)
#   3. The state graph has paths to the goal
#
# ARC-STRAT-BONANNO-001 | Bonanno Ch 3 §3.2

def backward_induction_path(graph_explorer, goal_state_hash: str) -> list:
    """Find optimal path from current state to goal via backward induction.

    Args:
        graph_explorer: GraphExplorer instance with populated state graph
        goal_state_hash: Blake2b hash of the target state

    Returns:
        List of (node_hash, edge_index) tuples representing the optimal
        path from current position to goal. Empty list if no path exists.

    Bonanno §3.2: At each node, select the action leading to the
    subtree with the best terminal payoff. For ARC-AGI-3, "best
    terminal payoff" = fewest actions to reach goal state.
    """
    # BFS backward from goal to find shortest paths
    # This IS backward induction for single-player perfect-info games
    # (equivalent to BFS because the "opponent" is Nature with deterministic moves)

    if not hasattr(graph_explorer, 'graph') or not graph_explorer.graph:
        return []

    graph = graph_explorer.graph

    # Check goal is in graph
    if goal_state_hash not in graph:
        return []

    # BFS backward: build parent pointers from goal
    visited = {goal_state_hash}
    queue = [goal_state_hash]
    parent = {}  # node -> (parent_node, edge_index)

    while queue:
        current = queue.pop(0)

        # Find all nodes that have an edge TO current
        for node_hash, node_data in graph.items():
            if node_hash in visited:
                continue
            edges = node_data.get("edges", [])
            for edge_idx, edge in enumerate(edges):
                if edge.get("to_node") == current:
                    parent[node_hash] = (current, edge_idx)
                    visited.add(node_hash)
                    queue.append(node_hash)
                    break  # First path found = shortest (BFS)

    # Reconstruct path from current position
    current_hash = graph_explorer.current_node
    if current_hash not in parent and current_hash != goal_state_hash:
        return []  # No path

    path = []
    node = current_hash
    while node in parent:
        next_node, edge_idx = parent[node]
        path.append((node, edge_idx))
        node = next_node

    return path


def should_use_backward_induction(metrics: 'PayoffMetrics', goal_available: bool) -> bool:
    """Decision function: is backward induction applicable?

    Bonanno §3.4 (p.87): Backward induction requires:
    1. Perfect information (each information set is a singleton)
    2. Finite game tree
    3. No ties in payoffs at terminal nodes

    For ARC-AGI-3:
    1. Perfect info ≈ high transition determinism (>0.95)
    2. Finite ≈ state space growth rate declining (we're finding fewer new states)
    3. No ties ≈ we have a single goal state (goal_available=True)
    """
    return (
        goal_available
        and metrics.transition_determinism > 0.95
        and metrics.exploration_marginal_value < 0.1  # Most states found
        and metrics.total_actions > 200  # Enough data
    )
```

### Component 2: Information Set Tracker (Bonanno Ch 4, §4.1-4.4)

```python
# ============================================================
# BONANNO FORMALIZATION — Ch 4: Imperfect Information
# ============================================================
# When the agent can't distinguish between states (same visual
# appearance, different underlying rules), it's playing a game
# with imperfect information. Actions must be consistent across
# indistinguishable states.
#
# Bonanno §4.1 (p.121): "An information set of player i is a set
# of nodes where player i cannot distinguish between the nodes."
#
# In ARC-AGI-3: the agent sees the grid but doesn't know the rule.
# Two puzzles with different rules but similar-looking grids are
# in the same information set. The agent must choose a strategy
# that works across all states in the information set.
#
# ARC-STRAT-BONANNO-001 | Bonanno Ch 4 §4.1-4.4

from collections import defaultdict
from typing import Dict, Set, List, Tuple


class InformationSetTracker:
    """Track which states the agent cannot distinguish.

    States are grouped into information sets based on observable features.
    The agent must play the same strategy across all states in an
    information set (Bonanno §4.2: "A strategy must specify the same
    action at all nodes in an information set").

    For ARC-AGI-3: two states are in the same information set if they
    have the same frame hash (same visual appearance) but different
    action outcomes. This means the underlying rule differs.
    """

    def __init__(self):
        # frame_hash -> set of state_hashes (different underlying states
        # that LOOK the same to the agent)
        self.info_sets: Dict[str, Set[str]] = defaultdict(set)

        # state_hash -> {action -> outcome_hash}
        # Track what happened when we took each action from each state
        self.action_outcomes: Dict[str, Dict[str, str]] = defaultdict(dict)

    def observe(self, frame_hash: str, state_hash: str, action: str, outcome_hash: str):
        """Record an observation: at state with this frame, action led to outcome.

        If two different state_hashes have the same frame_hash, they're in
        the same information set — the agent can't tell them apart visually.
        """
        self.info_sets[frame_hash].add(state_hash)
        self.action_outcomes[state_hash][action] = outcome_hash

    def get_info_set_size(self, frame_hash: str) -> int:
        """How many distinct states look like this frame?

        Size 1 = perfect information (singleton information set, Bonanno §4.1)
        Size > 1 = imperfect information (the agent is uncertain)
        """
        return len(self.info_sets.get(frame_hash, set()))

    def is_perfect_information(self, frame_hash: str) -> bool:
        """Is this state a singleton information set? (Bonanno §3.1 vs §4.1)"""
        return self.get_info_set_size(frame_hash) <= 1

    def consistent_actions(self, frame_hash: str) -> Set[str]:
        """Which actions have consistent outcomes across the information set?

        Bonanno §4.4 (Subgame-perfect equilibrium): prefer actions that
        work regardless of which state in the info set we're actually in.
        An action is "consistent" if it leads to a new-state-discovery
        from every state in the information set.
        """
        states = self.info_sets.get(frame_hash, set())
        if not states:
            return set()

        # Find actions that appear in ALL states' outcome records
        action_sets = [set(self.action_outcomes[s].keys()) for s in states]
        if not action_sets:
            return set()
        common_actions = action_sets[0]
        for s in action_sets[1:]:
            common_actions &= s

        # Among common actions, find those with consistent outcomes
        # "Consistent" = same outcome hash across all states in info set
        consistent = set()
        for action in common_actions:
            outcomes = {self.action_outcomes[s][action] for s in states
                       if action in self.action_outcomes[s]}
            if len(outcomes) == 1:
                consistent.add(action)

        return consistent

    def subgame_perfect_actions(self, frame_hash: str) -> List[str]:
        """Actions that form a subgame-perfect equilibrium for this info set.

        Bonanno §4.4 (p.133): A strategy profile is subgame-perfect if
        it induces a Nash equilibrium in every subgame.

        For single-player ARC-AGI-3: this simplifies to "actions that
        are optimal regardless of which state we're in." Priority:
        1. Consistent actions (same outcome everywhere)
        2. Actions available in all states (even if outcomes differ)
        3. Any available action (information-free choice)
        """
        consistent = self.consistent_actions(frame_hash)
        if consistent:
            return sorted(consistent)

        # Fallback: actions available in all states
        states = self.info_sets.get(frame_hash, set())
        if not states:
            return []
        action_sets = [set(self.action_outcomes[s].keys()) for s in states]
        common = action_sets[0]
        for s in action_sets[1:]:
            common &= s
        return sorted(common)

    def uncertainty_ratio(self) -> float:
        """What fraction of observed frames have imperfect information?

        High ratio (>0.3) = the game is fundamentally about hidden state.
        Low ratio (<0.1) = mostly perfect information, backward induction applies.
        """
        if not self.info_sets:
            return 0.0
        imperfect = sum(1 for s in self.info_sets.values() if len(s) > 1)
        return imperfect / len(self.info_sets)
```

### Component 3: Mixed Strategy Computer (Bonanno Ch 6, §6.2-6.3)

```python
# ============================================================
# BONANNO FORMALIZATION — Ch 6: Mixed Strategies
# ============================================================
# When no pure strategy dominates (stochastic game, or opponent
# is adversarial), compute the optimal probability mix.
#
# Bonanno §6.2 (p.206): "A mixed strategy for player i is a
# probability distribution over player i's set of pure strategies."
#
# Bonanno §6.3 (p.211): Support enumeration — compute Nash
# equilibria by finding the probability mix that makes the
# opponent indifferent between their strategies.
#
# In ARC-AGI-3: the "opponent" is the environment (stochastic
# transitions). The optimal mix isn't uniform — it's the
# probabilities that maximize expected new-state-discovery
# given the observed transition matrix.
#
# ARC-STRAT-BONANNO-001 | Bonanno Ch 6 §6.2-6.3

import random


def compute_mixed_strategy(action_outcomes: dict, action_names: list) -> Dict[str, float]:
    """Compute optimal mixed strategy from observed payoff matrix.

    Instead of uniform randomization (current RANDOMIZER mode), compute
    the probability distribution that maximizes expected exploration value.

    Args:
        action_outcomes: {action_name: [list of (success, new_state) booleans]}
        action_names: list of available action names

    Returns:
        {action_name: probability} summing to 1.0

    Method: Softmax over expected new-state-discovery rates.
    This isn't full Nash computation (that requires knowing the opponent's
    strategy space), but it's the optimal single-player mixed strategy
    given observed outcomes. Bonanno §6.3 simplifies for 1-player games
    to: play each action proportional to its expected payoff.

    For stochastic environments where the SAME action gives DIFFERENT
    results: higher variance actions get HIGHER weight (exploration value).
    This is the "matching pennies" insight from Bonanno §6.2: in a
    zero-sum game, the optimal mix makes you unpredictable to Nature.
    """
    if not action_names:
        return {}

    # Compute expected new-state-discovery rate per action
    rates = {}
    for action in action_names:
        outcomes = action_outcomes.get(action, [])
        if not outcomes:
            rates[action] = 0.5  # Unknown = optimistic prior (exploration bonus)
        else:
            # new_state rate
            new_state_rate = sum(1 for _, ns in outcomes if ns) / len(outcomes)
            # Variance bonus: stochastic actions are MORE interesting
            success_rate = sum(1 for s, _ in outcomes if s) / len(outcomes)
            variance = success_rate * (1 - success_rate)
            # Combined: base rate + variance bonus (Bonanno: explore uncertain regions)
            rates[action] = new_state_rate + 0.5 * variance

    # Softmax to get probabilities (temperature=1.0)
    import math
    max_rate = max(rates.values()) if rates else 0
    exp_rates = {a: math.exp(r - max_rate) for a, r in rates.items()}
    total = sum(exp_rates.values())

    if total == 0:
        # Uniform fallback
        p = 1.0 / len(action_names)
        return {a: p for a in action_names}

    return {a: exp_rates[a] / total for a in action_names}


def sample_mixed_action(strategy: Dict[str, float]) -> str:
    """Sample an action from the mixed strategy distribution.

    Bonanno §6.2: "The player does not choose an action; she
    chooses a probability distribution and then a random device
    selects the action."
    """
    actions = list(strategy.keys())
    probs = [strategy[a] for a in actions]
    return random.choices(actions, weights=probs, k=1)[0]
```

### Component 4: Upgraded `select_strategy_v2()` that uses the formal components

```python
# ============================================================
# UPGRADED STRATEGY SELECTOR
# ============================================================
# Replaces heuristic thresholds with formal game classification.
# The existing select_strategy() is preserved as fallback.
#
# ARC-STRAT-BONANNO-001

def classify_game(metrics: 'PayoffMetrics', info_tracker: 'InformationSetTracker' = None) -> str:
    """Classify the current game using Bonanno's taxonomy.

    Returns one of:
      "perfect_info_finite"     — Ch 3: backward induction applies
      "imperfect_info"          — Ch 4: subgame-perfect equilibrium
      "stochastic"              — Ch 6: mixed strategies
      "unknown"                 — not enough data, use ADAPTIVE

    This replaces the ad-hoc threshold checks in select_strategy().
    """
    if metrics.total_actions < 100:
        return "unknown"

    # Check information structure
    uncertainty = info_tracker.uncertainty_ratio() if info_tracker else 0.0

    # Perfect information + declining growth = finite game (Ch 3)
    if (metrics.transition_determinism > 0.95
            and uncertainty < 0.1
            and metrics.exploration_marginal_value < 0.1):
        return "perfect_info_finite"

    # High uncertainty = imperfect information game (Ch 4)
    if uncertainty > 0.3:
        return "imperfect_info"

    # Low determinism = stochastic game (Ch 6)
    if metrics.transition_determinism < 0.7:
        return "stochastic"

    # High determinism but still finding states = still exploring
    if metrics.state_space_growth_rate > 0.1:
        return "unknown"

    # Default: imperfect info (safer than assuming perfect)
    return "imperfect_info"


def select_strategy_v2(metrics: 'PayoffMetrics',
                       info_tracker: 'InformationSetTracker' = None,
                       goal_available: bool = False) -> str:
    """Game-theory-informed strategy selection v2.

    Uses Bonanno's game classification instead of raw thresholds.
    Falls back to select_strategy() if info_tracker is not available.
    """
    game_type = classify_game(metrics, info_tracker)

    if game_type == "perfect_info_finite" and goal_available:
        return EXPLOITER  # Backward induction mode — commit to the known path

    if game_type == "imperfect_info":
        return ADAPTIVE  # Subgame-perfect — keep options open, gather info

    if game_type == "stochastic":
        return RANDOMIZER  # Mixed strategy — optimal probability mix, not uniform

    # Unknown or insufficient data
    return ADAPTIVE
```

---

## Integration Notes

The Jr should add these components to the BOTTOM of `game_strategy.py`, below the existing `StrategyTracker` class. The existing code is untouched.

Integration into `ganuda_agent.py` happens in a separate task — this instruction only creates the formal components. The agent currently calls `select_strategy()` via `StrategyTracker.record_action()`. A follow-up instruction will wire `select_strategy_v2()`, `InformationSetTracker`, and `backward_induction_path()` into the agent loop.

---

## Success Criteria

- [ ] All four components added to `/ganuda/services/arc_agi_3/game_strategy.py`
- [ ] `backward_induction_path()` correctly finds shortest path via BFS from goal
- [ ] `InformationSetTracker.consistent_actions()` identifies actions with uniform outcomes
- [ ] `compute_mixed_strategy()` produces non-uniform probabilities (not all equal)
- [ ] `classify_game()` correctly classifies: deterministic+finite → "perfect_info_finite", high uncertainty → "imperfect_info", low determinism → "stochastic"
- [ ] `select_strategy_v2()` returns the same modes (EXPLORER/EXPLOITER/ADAPTIVE/RANDOMIZER) — just with formal backing
- [ ] Existing tests still pass (no modifications to existing functions)
- [ ] Code runs without numpy dependency (only stdlib math + random)

## Test Cases

From Bonanno exercises that map to ARC scenarios:

1. **Exercise 3.7.2** (p.97): Backward induction in a 2-move game. Create a 3-node graph (start → mid → goal) with deterministic transitions. `backward_induction_path()` should return [(start, edge_0), (mid, edge_0)].

2. **Exercise 4.6.1** (p.146): Imperfect information game. Create two states with the same frame_hash but different action outcomes. `InformationSetTracker.is_perfect_information()` should return False. `consistent_actions()` should return only actions that have the same outcome in both states.

3. **Exercise 6.5.2** (p.222): Mixed strategy computation. Given 3 actions with new-state rates [0.8, 0.2, 0.5], `compute_mixed_strategy()` should assign highest probability to the 0.8 action, lowest to 0.2.

---

For Seven Generations.
