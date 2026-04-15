"""
Game-Theory-Informed Strategy Switching for ARC-AGI-3

Four strategy modes based on real-time payoff metrics:
  EXPLORER   — maximin: minimize worst case via thorough exploration
  EXPLOITER  — maximax: maximize best case via early commitment
  RANDOMIZER — mixed strategy: for stochastic games where deterministic play fails
  ADAPTIVE   — Nash equilibrium search: start exploring, switch when marginal value drops

Council vote d022edb51960cef1 context. Game theory references:
  simplypsychology.org/game-theory.html (Prisoner's Dilemma, Volunteer's Dilemma)
  Moulin, Rice ECO 440 (Minimax Theorem, backward induction, mixed strategies)

The key insight: strategy should be game-characteristic-based, not level-based.
Different games have different payoff structures.
"""

import logging
from dataclasses import dataclass, field
from collections import deque
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# Strategy constants
EXPLORER = "EXPLORER"
EXPLOITER = "EXPLOITER"
ADAPTIVE = "ADAPTIVE"
RANDOMIZER = "RANDOMIZER"


@dataclass
class PayoffMetrics:
    """Real-time game payoff metrics for strategy selection."""

    # Rolling window tracking
    _window_size: int = 50
    _recent_actions: deque = field(default_factory=lambda: deque(maxlen=50))
    _recent_new_states: deque = field(default_factory=lambda: deque(maxlen=50))
    _action_outcomes: Dict[str, list] = field(default_factory=dict)
    _repeated_actions: int = 0
    _repeated_same_result: int = 0

    # Computed metrics (updated after each action)
    total_actions: int = 0
    unique_states_discovered: int = 0
    unique_states_per_action: float = 0.0
    transition_determinism: float = 1.0
    state_space_growth_rate: float = 1.0
    game_over_rate: float = 0.0
    exploration_marginal_value: float = 1.0

    # Action effectiveness
    action_success_rates: Dict[str, float] = field(default_factory=dict)

    # Game-overs
    _total_game_overs: int = 0

    def record_action(self, action_name: str, success: bool, new_state: bool):
        """Record outcome of a single action. Call after every action."""
        self.total_actions += 1

        # Track new state discovery
        self._recent_actions.append(action_name)
        self._recent_new_states.append(1 if new_state else 0)
        if new_state:
            self.unique_states_discovered += 1

        # Track action success rates
        if action_name not in self._action_outcomes:
            self._action_outcomes[action_name] = []
        self._action_outcomes[action_name].append(1 if success else 0)

        # Update computed metrics every window_size actions
        if self.total_actions % self._window_size == 0:
            self._recompute()

    def record_repeated_action(self, same_result: bool):
        """Track determinism: when we repeat an action, did we get the same result?"""
        self._repeated_actions += 1
        if same_result:
            self._repeated_same_result += 1
        if self._repeated_actions > 0:
            self.transition_determinism = self._repeated_same_result / self._repeated_actions

    def record_game_over(self):
        """Track game-over frequency."""
        self._total_game_overs += 1
        if self.total_actions > 0:
            self.game_over_rate = self._total_game_overs / self.total_actions

    def _recompute(self):
        """Recompute derived metrics from rolling window."""
        if len(self._recent_new_states) > 0:
            self.unique_states_per_action = sum(self._recent_new_states) / len(self._recent_new_states)

        # State space growth rate (new states per action over full history)
        if self.total_actions > 0:
            self.state_space_growth_rate = self.unique_states_discovered / self.total_actions

        # Exploration marginal value: trend of unique_states_per_action
        # Compare first half vs second half of window
        window = list(self._recent_new_states)
        if len(window) >= 20:
            first_half = sum(window[:len(window)//2]) / max(len(window)//2, 1)
            second_half = sum(window[len(window)//2:]) / max(len(window)//2, 1)
            # If second half is finding fewer new states, marginal value is declining
            self.exploration_marginal_value = second_half  # raw rate in recent window

        # Per-action success rates
        for action_name, outcomes in self._action_outcomes.items():
            recent = outcomes[-50:]  # last 50 uses of this action
            self.action_success_rates[action_name] = sum(recent) / max(len(recent), 1)

    def summary(self) -> str:
        """One-line summary for logging."""
        return (
            f"actions={self.total_actions} states={self.unique_states_discovered} "
            f"states/act={self.unique_states_per_action:.3f} "
            f"determinism={self.transition_determinism:.2f} "
            f"growth={self.state_space_growth_rate:.3f} "
            f"marginal={self.exploration_marginal_value:.3f} "
            f"go_rate={self.game_over_rate:.3f}"
        )


def select_strategy(metrics: PayoffMetrics, level: int) -> str:
    """
    Game-theory-informed strategy selection.

    Phase 1 (< 100 actions): Always ADAPTIVE — not enough data to classify game
    Phase 2 (>= 100 actions): Classify game based on observed metrics

    Returns: EXPLORER, EXPLOITER, or ADAPTIVE
    """
    if metrics.total_actions < 100:
        return ADAPTIVE

    # High determinism + large state space = EXPLORER
    # This game rewards thorough exploration — many states to find, predictable transitions
    if metrics.transition_determinism > 0.9 and metrics.state_space_growth_rate > 0.3:
        return EXPLORER

    # Low state space growth + high action success on some actions = EXPLOITER
    # This game has few states — exploit the effective actions
    if metrics.state_space_growth_rate < 0.05:
        if metrics.action_success_rates:
            best_rate = max(metrics.action_success_rates.values())
            if best_rate > 0.3:
                return EXPLOITER

    # Low determinism = RANDOMIZER (Moulin Theorem 13: mixed strategies)
    # Non-deterministic game — same action gives different results.
    # Matching pennies insight: "the best way to play is to be unpredictable."
    # Don't greedily follow best-known path; deliberately randomize.
    if metrics.transition_determinism < 0.7:
        return RANDOMIZER

    # Marginal value of exploration declining = switch to EXPLOITER
    # We've found most of what there is to find — commit to what works
    if metrics.exploration_marginal_value < 0.05 and metrics.total_actions > 200:
        return EXPLOITER

    # High game-over rate + low determinism = RANDOMIZER
    # Stochastic punishment — randomize to find mixed-strategy equilibrium
    if metrics.game_over_rate > 0.3 and metrics.transition_determinism < 0.85:
        return RANDOMIZER

    # High game-over rate + high determinism = EXPLOITER
    # Deterministic punishment — exploit what works, avoid what doesn't
    if metrics.game_over_rate > 0.3:
        return EXPLOITER

    return ADAPTIVE


def get_strategy_params(strategy: str) -> dict:
    """
    Return parameter adjustments for each strategy mode.

    These modify behavior in graph_explorer and deep_solver.
    """
    if strategy == EXPLORER:
        return {
            "cwm_synthesis_threshold": 100,   # Explore longer before synthesizing
            "basin_hop_interval": 3,          # Try new openings faster
            "prefer_untested": True,          # Always prefer untested edges
            "success_weight": 0.0,            # Don't weight by success rate
            "group_advance_eagerness": 0.5,   # Slow group advancement
        }
    elif strategy == EXPLOITER:
        return {
            "cwm_synthesis_threshold": 20,    # Synthesize early, plan fast
            "basin_hop_interval": 8,          # Commit to current approach longer
            "prefer_untested": False,         # Prefer proven edges
            "success_weight": 1.0,            # Weight heavily by success rate
            "group_advance_eagerness": 2.0,   # Advance groups quickly
        }
    elif strategy == RANDOMIZER:
        return {
            "cwm_synthesis_threshold": 30,    # Moderate — gather data, then model
            "basin_hop_interval": 2,          # Very fast resets — try many openings
            "prefer_untested": True,          # Explore broadly
            "success_weight": 0.0,            # NO success weighting — deliberately unpredictable
            "group_advance_eagerness": 1.5,   # Try different action types quickly
            "use_mixed_strategy": True,       # Signal to use randomized selection
            "randomize_tested_edges": True,   # Even among tested edges, randomize uniformly
        }
    else:  # ADAPTIVE
        return {
            "cwm_synthesis_threshold": 50,    # Current default
            "basin_hop_interval": 5,          # Current default
            "prefer_untested": True,          # Default exploration bias
            "success_weight": 0.3,            # Light success weighting
            "group_advance_eagerness": 1.0,   # Normal advancement
        }


class StrategyTracker:
    """
    Tracks strategy switches and provides strategy-informed action selection.

    Usage:
        tracker = StrategyTracker()

        # In main loop:
        tracker.record_action(action_name, success, new_state)
        strategy = tracker.current_strategy
        params = tracker.current_params

        # On game over:
        tracker.record_game_over()
    """

    def __init__(self, log_interval: int = 50):
        self.metrics = PayoffMetrics()
        self.current_strategy = ADAPTIVE
        self.current_params = get_strategy_params(ADAPTIVE)
        self._log_interval = log_interval
        self._switches: list = []  # [(action_count, from, to, reason)]

    def record_action(self, action_name: str, success: bool, new_state: bool):
        """Record action and maybe switch strategy."""
        self.metrics.record_action(action_name, success, new_state)

        # Check for strategy switch every log_interval actions
        if self.metrics.total_actions % self._log_interval == 0:
            new_strategy = select_strategy(self.metrics, level=1)
            if new_strategy != self.current_strategy:
                reason = (
                    f"marginal={self.metrics.exploration_marginal_value:.3f} "
                    f"determinism={self.metrics.transition_determinism:.2f} "
                    f"growth={self.metrics.state_space_growth_rate:.3f} "
                    f"go_rate={self.metrics.game_over_rate:.3f}"
                )
                logger.info(
                    f"[STRATEGY] {self.current_strategy} → {new_strategy} "
                    f"at action {self.metrics.total_actions} ({reason})"
                )
                self._switches.append((
                    self.metrics.total_actions,
                    self.current_strategy,
                    new_strategy,
                    reason,
                ))
                self.current_strategy = new_strategy
                self.current_params = get_strategy_params(new_strategy)

            # Log metrics periodically
            logger.info(f"[PAYOFF] {self.metrics.summary()} strategy={self.current_strategy}")

    def record_repeated_action(self, same_result: bool):
        """Pass through to metrics."""
        self.metrics.record_repeated_action(same_result)

    def record_game_over(self):
        """Pass through to metrics."""
        self.metrics.record_game_over()

    def reset(self):
        """Reset for new level."""
        # Preserve determinism knowledge across levels
        old_determinism = self.metrics.transition_determinism
        self.metrics = PayoffMetrics()
        self.metrics.transition_determinism = old_determinism
        self.current_strategy = ADAPTIVE
        self.current_params = get_strategy_params(ADAPTIVE)

    def is_randomizer(self) -> bool:
        """Is the agent in RANDOMIZER mode (mixed strategy for stochastic games)?"""
        return self.current_strategy == RANDOMIZER

    def should_randomize_tested(self) -> bool:
        """In RANDOMIZER mode, randomize even among tested edges (no success bias)."""
        return self.current_params.get("randomize_tested_edges", False)

    def should_prefer_untested(self) -> bool:
        """Should the graph explorer prefer untested edges?"""
        return self.current_params["prefer_untested"]

    def get_success_weight(self) -> float:
        """How much to weight edges by historical success rate (0.0-1.0)."""
        return self.current_params["success_weight"]

    def get_basin_hop_interval(self) -> int:
        """How many game-overs before trying a new opening sequence."""
        return self.current_params["basin_hop_interval"]

    def get_cwm_threshold(self) -> int:
        """How many actions before attempting CWM synthesis."""
        return self.current_params["cwm_synthesis_threshold"]

    def get_action_weights(self, edge_count: int) -> list:
        """
        Get selection weights for edges based on success rates.

        Returns list of weights (one per edge). Higher = more likely to be selected.
        Used by graph_explorer.choose_edge() in EXPLOITER mode.
        """
        weight = self.get_success_weight()
        if weight == 0.0 or not self.metrics.action_success_rates:
            return [1.0] * edge_count  # Uniform

        # Build weights from action success rates
        # Default weight 0.5 for unknown actions
        base_weights = [0.5] * edge_count
        # The caller would need to map edge indices to action names
        # For now, return uniform — the integration step handles the mapping
        return base_weights

    def to_dict(self) -> dict:
        """Serialize for experience bank storage."""
        return {
            "final_strategy": self.current_strategy,
            "switches": [
                {"action": a, "from": f, "to": t, "reason": r}
                for a, f, t, r in self._switches
            ],
            "metrics_at_end": {
                "total_actions": self.metrics.total_actions,
                "unique_states": self.metrics.unique_states_discovered,
                "transition_determinism": self.metrics.transition_determinism,
                "state_space_growth_rate": self.metrics.state_space_growth_rate,
                "exploration_marginal_value": self.metrics.exploration_marginal_value,
                "game_over_rate": self.metrics.game_over_rate,
                "action_success_rates": dict(self.metrics.action_success_rates),
            },
        }


# ============================================================
# BONANNO FORMALIZATION — Ch 3: Backward Induction
# ============================================================
# Bonanno §3.2 (p.81): "Start from the terminal nodes and work
# backward, at each node selecting the action that leads to the
# best outcome for the player who moves at that node."
#
# ARC-STRAT-BONANNO-001 | Bonanno Ch 3 §3.2

def backward_induction_path(graph_explorer, goal_state_hash: str) -> list:
    """Find optimal path from current state to goal via backward induction."""
    if not hasattr(graph_explorer, 'graph') or not graph_explorer.graph:
        return []

    graph = graph_explorer.graph
    if goal_state_hash not in graph:
        return []

    visited = {goal_state_hash}
    queue = [goal_state_hash]
    parent = {}

    while queue:
        current = queue.pop(0)
        for node_hash, node_data in graph.items():
            if node_hash in visited:
                continue
            edges = node_data.get("edges", [])
            for edge_idx, edge in enumerate(edges):
                if edge.get("to_node") == current:
                    parent[node_hash] = (current, edge_idx)
                    visited.add(node_hash)
                    queue.append(node_hash)
                    break

    current_hash = graph_explorer.current_node
    if current_hash not in parent and current_hash != goal_state_hash:
        return []

    path = []
    node = current_hash
    while node in parent:
        next_node, edge_idx = parent[node]
        path.append((node, edge_idx))
        node = next_node

    return path


def should_use_backward_induction(metrics: PayoffMetrics, goal_available: bool) -> bool:
    """Decision function: is backward induction applicable? (Bonanno §3.4)"""
    return (
        goal_available
        and metrics.transition_determinism > 0.95
        and metrics.exploration_marginal_value < 0.1
        and metrics.total_actions > 200
    )


# ============================================================
# BONANNO FORMALIZATION — Ch 4: Imperfect Information
# ============================================================
# ARC-STRAT-BONANNO-001 | Bonanno Ch 4 §4.1-4.4

from collections import defaultdict


class InformationSetTracker:
    """Track which states the agent cannot distinguish.

    States are grouped into information sets based on observable features.
    The agent must play the same strategy across all states in an
    information set (Bonanno §4.2).
    """

    def __init__(self):
        self.info_sets: dict = defaultdict(set)
        self.action_outcomes: dict = defaultdict(dict)

    def observe(self, frame_hash: str, state_hash: str, action: str, outcome_hash: str):
        self.info_sets[frame_hash].add(state_hash)
        self.action_outcomes[state_hash][action] = outcome_hash

    def get_info_set_size(self, frame_hash: str) -> int:
        return len(self.info_sets.get(frame_hash, set()))

    def is_perfect_information(self, frame_hash: str) -> bool:
        return self.get_info_set_size(frame_hash) <= 1

    def consistent_actions(self, frame_hash: str) -> set:
        states = self.info_sets.get(frame_hash, set())
        if not states:
            return set()
        action_sets = [set(self.action_outcomes[s].keys()) for s in states]
        if not action_sets:
            return set()
        common_actions = action_sets[0]
        for s in action_sets[1:]:
            common_actions &= s
        consistent = set()
        for action in common_actions:
            outcomes = {self.action_outcomes[s][action] for s in states
                       if action in self.action_outcomes[s]}
            if len(outcomes) == 1:
                consistent.add(action)
        return consistent

    def subgame_perfect_actions(self, frame_hash: str) -> list:
        consistent = self.consistent_actions(frame_hash)
        if consistent:
            return sorted(consistent)
        states = self.info_sets.get(frame_hash, set())
        if not states:
            return []
        action_sets = [set(self.action_outcomes[s].keys()) for s in states]
        common = action_sets[0]
        for s in action_sets[1:]:
            common &= s
        return sorted(common)

    def uncertainty_ratio(self) -> float:
        if not self.info_sets:
            return 0.0
        imperfect = sum(1 for s in self.info_sets.values() if len(s) > 1)
        return imperfect / len(self.info_sets)


# ============================================================
# BONANNO FORMALIZATION — Ch 6: Mixed Strategies
# ============================================================
# ARC-STRAT-BONANNO-001 | Bonanno Ch 6 §6.2-6.3

import math
import random


def compute_mixed_strategy(action_outcomes: dict, action_names: list) -> dict:
    """Compute optimal mixed strategy from observed payoff matrix.

    Softmax over expected new-state-discovery rates with variance bonus.
    """
    if not action_names:
        return {}

    rates = {}
    for action in action_names:
        outcomes = action_outcomes.get(action, [])
        if not outcomes:
            rates[action] = 0.5
        else:
            new_state_rate = sum(1 for _, ns in outcomes if ns) / len(outcomes)
            success_rate = sum(1 for s, _ in outcomes if s) / len(outcomes)
            variance = success_rate * (1 - success_rate)
            rates[action] = new_state_rate + 0.5 * variance

    max_rate = max(rates.values()) if rates else 0
    exp_rates = {a: math.exp(r - max_rate) for a, r in rates.items()}
    total = sum(exp_rates.values())

    if total == 0:
        p = 1.0 / len(action_names)
        return {a: p for a in action_names}

    return {a: exp_rates[a] / total for a in action_names}


def sample_mixed_action(strategy: dict) -> str:
    """Sample an action from the mixed strategy distribution."""
    actions = list(strategy.keys())
    probs = [strategy[a] for a in actions]
    return random.choices(actions, weights=probs, k=1)[0]


# ============================================================
# UPGRADED STRATEGY SELECTOR
# ============================================================
# ARC-STRAT-BONANNO-001

def classify_game(metrics: PayoffMetrics, info_tracker: 'InformationSetTracker' = None) -> str:
    """Classify the current game using Bonanno's taxonomy."""
    if metrics.total_actions < 100:
        return "unknown"

    uncertainty = info_tracker.uncertainty_ratio() if info_tracker else 0.0

    if (metrics.transition_determinism > 0.95
            and uncertainty < 0.1
            and metrics.exploration_marginal_value < 0.1):
        return "perfect_info_finite"

    if uncertainty > 0.3:
        return "imperfect_info"

    if metrics.transition_determinism < 0.7:
        return "stochastic"

    if metrics.state_space_growth_rate > 0.1:
        return "unknown"

    return "imperfect_info"


def select_strategy_v2(metrics: PayoffMetrics,
                       info_tracker: 'InformationSetTracker' = None,
                       goal_available: bool = False) -> str:
    """Game-theory-informed strategy selection v2.

    Uses Bonanno's game classification instead of raw thresholds.
    """
    game_type = classify_game(metrics, info_tracker)

    if game_type == "perfect_info_finite" and goal_available:
        return EXPLOITER

    if game_type == "imperfect_info":
        return ADAPTIVE

    if game_type == "stochastic":
        return RANDOMIZER

    return ADAPTIVE
