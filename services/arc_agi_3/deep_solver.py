"""
Deep Solver — Level 2+ Focused ARC-AGI-3 Orchestrator

Problem: We solve Level 1 on 18 games but rarely push past Level 2.
Scoring: L1=1/15, L2=2/15, L3=3/15, L4=4/15, L5=5/15.
So one L5 = five L1s. Pushing deeper is worth far more than breadth.

Strategy:
  1. Level-aware strategy switching (graph only -> graph+CWM -> deep MCTS)
  2. Cross-life learning: preserve the graph across game-overs on the same level
  3. Action sequence replay: instantly replay solved levels
  4. Progressive widening: expand action candidates on deeper levels
  5. LLM gap analysis: after 5 game-overs ask the 72B what we're missing

Uses the existing GanudaAgent internally — does not rewrite the agent.
Orchestrates it with level-aware strategy on top.

Council: Pending approval.
"""

from __future__ import annotations

import argparse
import copy
import json
import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

import numpy as np

from arcengine import FrameData, GameAction, GameState

from frame_processor import FrameProcessor
from graph_explorer import GraphExplorer

# Optional imports with graceful degradation
try:
    from world_model import (
        CodeWorldModel, MCTSPlanner, StateExtractor,
        LEVEL_CONFIGS, LEVEL_DEFAULT_CONFIG,
        VLLM_URL, VLLM_MODEL, _call_vllm,
    )
    CWM_AVAILABLE = True
except ImportError:
    CWM_AVAILABLE = False

try:
    from goal_inferrer import GoalInferrer
    GOAL_AVAILABLE = True
except ImportError:
    GOAL_AVAILABLE = False

try:
    from game_experience import store_game_experience, retrieve_game_experiences
    EXPERIENCE_AVAILABLE = True
except ImportError:
    EXPERIENCE_AVAILABLE = False

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Fibonacci depth scaling for MCTS at deeper levels
# ---------------------------------------------------------------------------

FIB_DEPTHS = [12, 21, 34, 55, 89, 144]
FIB_SIMS = [80, 120, 200, 300, 500, 800]


def _fib_config(level: int) -> Tuple[int, int]:
    """Return (depth_limit, n_simulations) for a given level using Fibonacci scaling."""
    idx = min(level - 1, len(FIB_DEPTHS) - 1)
    return FIB_DEPTHS[idx], FIB_SIMS[idx]


# ---------------------------------------------------------------------------
# Strategy enum
# ---------------------------------------------------------------------------

class Strategy:
    """Level-aware strategy labels."""
    GRAPH_ONLY = "graph_only"           # Level 1: pure graph exploration
    GRAPH_PLUS_CWM = "graph_plus_cwm"   # Level 2: graph + CWM synthesis after 50 actions
    DEEP_MCTS = "deep_mcts"             # Level 3+: CWM + deep MCTS + experience bank


def pick_strategy(level: int) -> str:
    """Select strategy based on current level."""
    if level <= 1:
        return Strategy.GRAPH_ONLY
    elif level == 2:
        return Strategy.GRAPH_PLUS_CWM
    else:
        return Strategy.DEEP_MCTS


# ---------------------------------------------------------------------------
# LevelSolution — recorded action sequence for a solved level
# ---------------------------------------------------------------------------

@dataclass
class LevelSolution:
    """A recorded solution for a specific level of a game."""
    level: int
    actions: List[GameAction]
    action_data: List[Optional[Dict]]  # parallel list of action.action_data for complex actions
    action_count: int                   # total actions taken (including replayed prior levels)

    def __repr__(self) -> str:
        return f"LevelSolution(L{self.level}, {len(self.actions)} actions)"


# ---------------------------------------------------------------------------
# CrossLifeGraph — graph that persists across game-overs on the same level
# ---------------------------------------------------------------------------

class CrossLifeGraph:
    """Wraps GraphExplorer to persist state across game-overs.

    The key insight: when the agent game-overs on Level 2, the graph
    accumulated during that life contains knowledge of the state space.
    Throwing it away and starting fresh wastes all that exploration.

    Instead, we keep the graph across lives on the same level. Each life
    adds more tested edges and discovered states. After enough lives,
    the graph converges on the reachable state space.
    """

    def __init__(self):
        self._graphs: Dict[int, GraphExplorer] = {}  # level -> preserved graph
        self._game_over_counts: Dict[int, int] = defaultdict(int)
        self._explored_states: Dict[int, Set[str]] = defaultdict(set)

    def get_graph(self, level: int, n_groups: int = 1) -> GraphExplorer:
        """Get or create the graph for a given level."""
        if level not in self._graphs:
            self._graphs[level] = GraphExplorer(n_groups=n_groups)
        return self._graphs[level]

    def record_game_over(self, level: int):
        """Record a game-over on a level. Returns the count."""
        self._game_over_counts[level] += 1
        return self._game_over_counts[level]

    def game_over_count(self, level: int) -> int:
        return self._game_over_counts[level]

    def record_state(self, level: int, frame_hash: str):
        """Track explored states for gap analysis."""
        self._explored_states[level].add(frame_hash)

    def explored_state_count(self, level: int) -> int:
        return len(self._explored_states[level])

    def get_explored_summary(self, level: int) -> str:
        """Build a summary of explored states for LLM gap analysis."""
        graph = self._graphs.get(level)
        if graph is None:
            return "No graph data for this level."

        nodes = graph._nodes
        frontier_count = len(graph._frontier)
        total_nodes = len(nodes)

        # Collect edge statistics
        total_edges = 0
        success_edges = 0
        failed_edges = 0
        for node_info in nodes.values():
            for edge in node_info.edges:
                total_edges += 1
                if edge.result == 1:
                    success_edges += 1
                elif edge.result == -1:
                    failed_edges += 1

        lines = [
            f"Level {level} exploration summary:",
            f"  States discovered: {total_nodes}",
            f"  Frontier (unexplored): {frontier_count}",
            f"  Edges tested: {total_edges}",
            f"  Successful transitions: {success_edges}",
            f"  Failed actions: {failed_edges}",
            f"  Game-overs on this level: {self._game_over_counts[level]}",
            f"  Unique states visited: {self.explored_state_count(level)}",
        ]

        # Show active group status
        if graph._active_group > 0:
            lines.append(f"  Active action group: {graph._active_group} (higher = more exotic actions)")

        return "\n".join(lines)

    def reset_level(self, level: int):
        """Full reset for a level (use sparingly — after LLM suggests reset)."""
        self._graphs.pop(level, None)
        self._explored_states[level].clear()
        # Don't reset game_over_count — that's diagnostic


# ---------------------------------------------------------------------------
# GapAnalyzer — asks the 72B what we're missing after repeated failures
# ---------------------------------------------------------------------------

class GapAnalyzer:
    """After N game-overs on the same level, asks the LLM for gap analysis.

    Feeds the graph exploration summary + frame state descriptions to the 72B
    and asks: 'What am I missing? What patterns should I try?'
    """

    TRIGGER_INTERVAL = 5  # ask every N game-overs
    _SYSTEM = (
        "You are an expert game-playing strategist analyzing an agent's exploration "
        "of a grid-based puzzle game. The agent has died multiple times on the same level. "
        "Given the exploration summary and recent states, identify what the agent might "
        "be missing and suggest specific action strategies to try.\n\n"
        "Respond in JSON with keys:\n"
        "  hints: list of strategy hints (strings)\n"
        "  try_actions: list of action sequences to try (each is a list of action names)\n"
        "  should_reset: boolean, true if the graph seems corrupted or the agent is in a dead end\n"
    )

    def __init__(self):
        self._last_analysis: Dict[int, int] = {}  # level -> game_over_count at last analysis

    def should_analyze(self, level: int, game_over_count: int) -> bool:
        """Check if we should trigger gap analysis."""
        if game_over_count < self.TRIGGER_INTERVAL:
            return False
        if game_over_count % self.TRIGGER_INTERVAL != 0:
            return False
        last = self._last_analysis.get(level, 0)
        return game_over_count > last

    def analyze(
        self,
        level: int,
        graph_summary: str,
        recent_state_descriptions: List[str],
        game_over_count: int,
    ) -> Optional[Dict[str, Any]]:
        """Ask the 72B for gap analysis. Returns parsed JSON or None."""
        if not CWM_AVAILABLE:
            logger.info("GapAnalyzer: CWM not available, skipping LLM analysis")
            return None

        self._last_analysis[level] = game_over_count

        state_text = "\n".join(f"  State {i+1}: {s}" for i, s in enumerate(recent_state_descriptions[-10:]))

        user_prompt = (
            f"The agent has game-overed {game_over_count} times on level {level}.\n\n"
            f"{graph_summary}\n\n"
            f"Recent states observed:\n{state_text}\n\n"
            f"What is the agent likely missing? Suggest specific strategies."
        )

        try:
            raw = _call_vllm(self._SYSTEM, user_prompt, temperature=0.4, max_tokens=1024, timeout=60.0)
            if raw is None:
                return None

            # Extract JSON from response
            import re
            json_match = re.search(r'\{[\s\S]*\}', raw)
            if json_match:
                result = json.loads(json_match.group())
                logger.info(f"GapAnalyzer L{level}: {len(result.get('hints', []))} hints, "
                          f"reset={result.get('should_reset', False)}")
                return result
        except Exception as e:
            logger.warning(f"GapAnalyzer failed: {e}")

        return None


# ---------------------------------------------------------------------------
# ProgressiveWidener — expands action candidates on deeper levels
# ---------------------------------------------------------------------------

class ProgressiveWidener:
    """Expands the action candidate set for deeper levels.

    Level 1 might only need arrow keys (ACTION1-5).
    Level 3 might need clicks on specific objects that Level 1 didn't require.

    The widener tracks which action types led to level-ups and biases
    deeper levels toward a broader set.
    """

    def __init__(self):
        self._level_up_action_types: Dict[int, Set[str]] = defaultdict(set)
        self._all_click_targets: List[Dict] = []  # accumulated click targets

    def record_level_up_actions(self, level: int, action_names: List[str]):
        """Record which action types were used when solving a level."""
        for name in action_names:
            self._level_up_action_types[level].add(name)

    def record_click_target(self, target_data: Dict):
        """Accumulate click targets seen across all levels."""
        self._all_click_targets.append(target_data)

    def should_widen(self, current_level: int) -> bool:
        """Check if we should expand the action set for this level."""
        return current_level >= 2

    def get_extra_click_targets(self, current_level: int, existing_targets: int) -> List[Dict]:
        """Suggest additional click targets for deeper levels.

        For levels 2+, we try clicking on grid positions that weren't
        generated by the default component segmentation.
        """
        if current_level < 2:
            return []

        extras = []
        # Generate grid-spaced click targets for broader exploration
        # Level 2: 8x8 grid, Level 3+: 16x16 grid
        grid_size = 8 if current_level == 2 else 16
        step = 64 // grid_size

        for row in range(grid_size):
            for col in range(grid_size):
                cx = col * step + step // 2
                cy = row * step + step // 2
                target = {'x': cx, 'y': cy}
                # Avoid duplicates with existing targets
                extras.append(target)

        # Cap extra targets to avoid explosion
        max_extras = min(len(extras), 32 * (current_level - 1))
        return extras[:max_extras]


# ---------------------------------------------------------------------------
# DeepSolver — the main orchestrator
# ---------------------------------------------------------------------------

class DeepSolver:
    """Level 2+ focused solver that orchestrates GanudaAgent with level-aware strategy.

    Key behaviors:
      - Replays solved level solutions instantly
      - Preserves graph across game-overs on the same level
      - Switches strategy based on current level
      - Triggers CWM synthesis and MCTS on deeper levels
      - Asks the 72B for gap analysis after repeated failures
      - Expands action candidates on deeper levels
    """

    def __init__(
        self,
        game_id: str,
        target_level: int = 5,
        max_actions: int = 10000,
        max_time: float = 300.0,
    ):
        self.game_id = game_id
        self.target_level = target_level
        self.max_actions = max_actions
        self.max_time = max_time

        # Core agent — we use this for frame processing and action selection
        # Disable CWM/goal inference in the agent itself — deep solver manages these
        from ganuda_agent import GanudaAgent
        import ganuda_agent as ga_module
        ga_module.CWM_AVAILABLE = False  # Deep solver handles CWM per-level
        ga_module.GOAL_AVAILABLE = False  # Deep solver handles goals per-level
        self.agent = GanudaAgent(game_id=game_id)

        # Level tracking
        self.current_level = 0  # 0 = not started, 1 = first level, etc.
        self.max_level_reached = 0

        # Solved level solutions for instant replay
        self._solutions: Dict[int, LevelSolution] = {}
        self._recording_actions: List[Tuple[GameAction, Optional[Dict]]] = []
        self._recording_level = 0
        self._replay_queue: List[Tuple[GameAction, Optional[Dict]]] = []
        self._replay_index = 0
        self._replaying = False

        # Cross-life graph persistence
        self._cross_life = CrossLifeGraph()

        # Gap analysis
        self._gap_analyzer = GapAnalyzer()
        self._recent_state_descriptions: Dict[int, List[str]] = defaultdict(list)
        self._gap_hints: Dict[int, List[str]] = defaultdict(list)
        self._gap_suggested_sequences: Dict[int, List[List[str]]] = defaultdict(list)
        self._gap_sequence_index: Dict[int, int] = defaultdict(int)

        # Progressive widening
        self._widener = ProgressiveWidener()

        # CWM management per level
        self._level_cwm: Dict[int, Any] = {}  # level -> CodeWorldModel
        self._level_cwm_active: Dict[int, bool] = defaultdict(lambda: False)

        # Action tracking for recording
        self._action_history: List[str] = []
        self._level_start_action_idx = 0

        # Strategy state
        self._current_strategy = Strategy.GRAPH_ONLY
        self._actions_on_level = 0
        self._cwm_synthesis_attempted = False

        # Statistics
        self.total_actions = 0
        self.total_game_overs = 0
        self.total_resets = 0
        self.level_times: Dict[int, float] = {}
        self._level_start_time = 0.0

    # -- Solution recording and replay ------------------------------------

    def _start_recording(self, level: int):
        """Start recording actions for the current level."""
        self._recording_actions = []
        self._recording_level = level
        self._level_start_action_idx = len(self._action_history)

    def _record_action(self, action: GameAction):
        """Record an action during the current level."""
        action_data = None
        if hasattr(action, 'action_data') and action.action_data is not None:
            try:
                action_data = action.action_data.model_dump()
            except Exception:
                action_data = None
        self._recording_actions.append((action, action_data))
        self._action_history.append(action.name)

    def _save_solution(self, level: int):
        """Save the recorded actions as a solution for this level."""
        if not self._recording_actions:
            return

        sol = LevelSolution(
            level=level,
            actions=[a for a, _ in self._recording_actions],
            action_data=[d for _, d in self._recording_actions],
            action_count=len(self._recording_actions),
        )
        self._solutions[level] = sol
        logger.info(f"Saved L{level} solution: {sol}")

        # Record which action types were used for progressive widening
        action_names = [a.name for a, _ in self._recording_actions]
        self._widener.record_level_up_actions(level, action_names)

    def _build_replay_queue(self, up_to_level: int):
        """Build a replay queue of all solved levels up to (but not including) up_to_level."""
        self._replay_queue = []
        for lvl in range(1, up_to_level):
            sol = self._solutions.get(lvl)
            if sol:
                for action, data in zip(sol.actions, sol.action_data):
                    self._replay_queue.append((action, data))
        self._replay_index = 0
        if self._replay_queue:
            self._replaying = True
            logger.info(f"Replay queue built: {len(self._replay_queue)} actions for L1-L{up_to_level - 1}")

    def _get_replay_action(self) -> Optional[Tuple[GameAction, Optional[Dict]]]:
        """Get the next replay action, or None if replay is done."""
        if not self._replaying or self._replay_index >= len(self._replay_queue):
            self._replaying = False
            return None
        action, data = self._replay_queue[self._replay_index]
        self._replay_index += 1
        if self._replay_index >= len(self._replay_queue):
            self._replaying = False
            logger.info("Replay complete, entering live play")
        return action, data

    # -- Level-aware CWM management ---------------------------------------

    def _get_or_create_cwm(self, level: int):
        """Get or create a CWM for the current level."""
        if not CWM_AVAILABLE:
            return None
        if level not in self._level_cwm:
            self._level_cwm[level] = CodeWorldModel(frame_processor=self.agent.fp)
        return self._level_cwm[level]

    def _maybe_synthesize_cwm(self, level: int):
        """Attempt CWM synthesis based on strategy and action count."""
        strategy = pick_strategy(level)

        if strategy == Strategy.GRAPH_ONLY:
            return  # No CWM needed for Level 1

        cwm = self._get_or_create_cwm(level)
        if cwm is None:
            return

        # Strategy.GRAPH_PLUS_CWM: synthesize after 50 actions on this level
        # Strategy.DEEP_MCTS: synthesize as soon as ready
        threshold = 50 if strategy == Strategy.GRAPH_PLUS_CWM else 20

        if (self._actions_on_level >= threshold and
            not self._level_cwm_active.get(level, False) and
            cwm.store.ready_for_synthesis()):

            logger.info(f"L{level}: Attempting CWM synthesis "
                       f"({len(cwm.store)} transitions, strategy={strategy})")
            if cwm.attempt_synthesis():
                self._level_cwm_active[level] = True
                logger.info(f"L{level}: CWM validated ({cwm.accuracy:.0%})! "
                           f"Planning enabled.")

    def _plan_with_cwm(self, level: int, frame_grid: np.ndarray,
                       available_actions: List[str]) -> Optional[List[str]]:
        """Use CWM + MCTS to plan, with Fibonacci depth scaling."""
        if not self._level_cwm_active.get(level, False):
            return None

        cwm = self._level_cwm.get(level)
        if cwm is None or not cwm.model_ready:
            return None

        # Get goal scorer if available
        goal_fn = None
        if self.agent.goal_inferrer and self.agent._goals_inferred:
            goal_fn = self.agent.goal_inferrer.score_objects

        state = cwm.extractor.extract(frame_grid)
        objects = state.object_dict_list()

        depth, sims = _fib_config(level)
        planner = MCTSPlanner(
            predict_fn=cwm.predict_fn,
            available_actions=available_actions,
            depth_limit=depth,
            n_simulations=sims,
            goal_score_fn=goal_fn,
            level=level,
        )

        sequence = planner.plan(objects)
        if sequence:
            logger.info(f"L{level} MCTS plan ({len(sequence)} steps, "
                       f"depth={depth}, sims={sims}): "
                       f"{' -> '.join(sequence[:5])}...")
        return sequence if sequence else None

    # -- Gap analysis integration -----------------------------------------

    def _maybe_run_gap_analysis(self, level: int):
        """Run gap analysis if we've game-overed enough times."""
        go_count = self._cross_life.game_over_count(level)
        if not self._gap_analyzer.should_analyze(level, go_count):
            return

        graph_summary = self._cross_life.get_explored_summary(level)
        state_descs = self._recent_state_descriptions.get(level, [])

        logger.info(f"L{level}: Running gap analysis after {go_count} game-overs...")
        result = self._gap_analyzer.analyze(level, graph_summary, state_descs, go_count)

        if result is None:
            return

        # Store hints
        hints = result.get('hints', [])
        self._gap_hints[level] = hints
        for hint in hints:
            logger.info(f"  Gap hint: {hint}")

        # Store suggested action sequences
        sequences = result.get('try_actions', [])
        if sequences:
            self._gap_suggested_sequences[level] = sequences
            self._gap_sequence_index[level] = 0
            logger.info(f"  {len(sequences)} action sequences suggested")

        # Handle reset suggestion
        if result.get('should_reset', False):
            logger.info(f"  LLM suggests full graph reset for L{level}")
            self._cross_life.reset_level(level)

    def _get_gap_sequence(self, level: int) -> Optional[List[str]]:
        """Get the next gap-analysis-suggested action sequence to try."""
        sequences = self._gap_suggested_sequences.get(level, [])
        if not sequences:
            return None
        idx = self._gap_sequence_index.get(level, 0)
        if idx >= len(sequences):
            return None
        self._gap_sequence_index[level] = idx + 1
        return sequences[idx]

    # -- Core game loop ---------------------------------------------------

    def _make_frame(self, obs) -> FrameData:
        """Convert an arcade observation to FrameData."""
        return FrameData(
            game_id=obs.game_id,
            frame=[arr.tolist() for arr in obs.frame],
            state=obs.state,
            levels_completed=obs.levels_completed,
            win_levels=obs.win_levels,
            guid=obs.guid,
            full_reset=obs.full_reset,
            available_actions=obs.available_actions,
        )

    def _execute_action(self, env, action: GameAction, data: Optional[Dict] = None) -> FrameData:
        """Execute an action in the environment and return the new frame."""
        if data is None:
            if action.is_complex() and hasattr(action, 'action_data') and action.action_data:
                try:
                    data = action.action_data.model_dump()
                except Exception:
                    data = {}
            else:
                data = {}

        raw = env.step(action, data=data, reasoning={})
        return self._make_frame(raw)

    def _inject_cross_life_graph(self, level: int):
        """Inject the cross-life graph into the agent for this level.

        Instead of letting the agent start with a fresh graph, we give it
        the accumulated graph from previous lives on this level.
        """
        graph = self._cross_life.get_graph(level, n_groups=self.agent.graph._n_groups
                                           if self.agent.graph else 1)
        # Only inject if the cross-life graph has nodes (not first life)
        if graph._nodes:
            self.agent.graph = graph
            logger.info(f"L{level}: Injected cross-life graph "
                       f"({len(graph._nodes)} nodes, "
                       f"{len(graph._frontier)} frontier)")

    def run(self) -> Dict[str, Any]:
        """Run the deep solver. Returns a results dictionary."""
        from arc_agi import Arcade

        arcade = Arcade()
        env = arcade.make(self.game_id)

        start_time = time.time()
        logger.info(f"DeepSolver: {self.game_id}, target L{self.target_level}, "
                   f"max {self.max_actions} actions, {self.max_time}s timeout")

        # Retrieve past experiences
        experience_context = ""
        if EXPERIENCE_AVAILABLE:
            experience_context = retrieve_game_experiences(self.game_id)
            if experience_context:
                logger.info(f"Experience Bank: {len(experience_context)} chars loaded")

        # Get initial frame
        obs = env.observation_space
        frame = self._make_frame(obs)

        self.current_level = frame.levels_completed or 0
        self._start_recording(self.current_level + 1)
        self._level_start_time = time.time()

        # Main loop
        for step in range(self.max_actions):
            elapsed = time.time() - start_time
            if elapsed >= self.max_time:
                logger.info(f"Time limit reached ({elapsed:.1f}s)")
                break

            # --- Check win condition ---
            if frame.levels_completed and frame.levels_completed >= self.target_level:
                logger.info(f"Target level {self.target_level} reached!")
                break

            if self.agent.is_done(frame):
                logger.info(f"WIN at step {step}!")
                break

            # --- Handle game-over ---
            if frame.state == GameState.GAME_OVER:
                self.total_game_overs += 1
                current_level = (frame.levels_completed or 0) + 1

                # Record game-over in cross-life graph
                go_count = self._cross_life.record_game_over(current_level)

                logger.info(f"Game over #{self.total_game_overs} on L{current_level} "
                          f"(life #{go_count} on this level)")

                # Run gap analysis if needed
                self._maybe_run_gap_analysis(current_level)

                # Reset agent state but preserve cross-life graph
                self.agent.action_count = 0
                self.agent.prev_score = 0
                self.agent.current_node = None
                self.agent.last_edge_idx = None
                self.agent.level_start_hash = None
                self.agent.prev_frame_hash = None
                self.agent._cwm_active = False
                self.agent._goals_inferred = False
                self._actions_on_level = 0
                self._cwm_synthesis_attempted = False
                self._recording_actions = []

                # Build replay queue for solved levels
                if self._solutions:
                    self._build_replay_queue(current_level)

                # Issue reset
                action = GameAction.RESET
                self.total_resets += 1
                frame = self._execute_action(env, action)
                self.total_actions += 1
                continue

            # --- Handle not-played state ---
            if frame.state == GameState.NOT_PLAYED:
                action = GameAction.RESET
                self.total_resets += 1
                frame = self._execute_action(env, action)
                self.total_actions += 1
                continue

            # --- Detect level transition ---
            new_level = (frame.levels_completed or 0)
            if new_level > self.current_level:
                old_level = self.current_level
                self.current_level = new_level
                self.max_level_reached = max(self.max_level_reached, new_level)

                # Record time on previous level
                level_time = time.time() - self._level_start_time
                self.level_times[old_level + 1] = level_time

                # Save the solution for the level we just completed
                self._save_solution(old_level + 1)

                logger.info(f"Level up! L{old_level} -> L{new_level} "
                          f"(took {level_time:.1f}s)")

                # Start recording for the new level
                self._start_recording(new_level + 1)
                self._level_start_time = time.time()
                self._actions_on_level = 0
                self._cwm_synthesis_attempted = False

                # Reset agent for new level but inject cross-life graph
                self.agent._on_level_up(np.array(frame.frame[-1], dtype=np.uint8)
                                        if frame.frame else np.zeros((64, 64), dtype=np.uint8))
                self.agent.prev_score = new_level

                # Inject cross-life graph for this new level
                self._inject_cross_life_graph(new_level + 1)

                # Update strategy
                self._current_strategy = pick_strategy(new_level + 1)
                logger.info(f"Strategy for L{new_level + 1}: {self._current_strategy}")

            # --- Replay mode: replay solved levels instantly ---
            replay = self._get_replay_action()
            if replay is not None:
                action, data = replay
                frame = self._execute_action(env, action, data)
                self.total_actions += 1
                continue

            # --- Check for gap-suggested sequence ---
            active_level = (frame.levels_completed or 0) + 1
            gap_seq = self._get_gap_sequence(active_level)
            if gap_seq:
                logger.info(f"L{active_level}: Trying gap-suggested sequence: {gap_seq[:5]}")
                for action_name in gap_seq:
                    try:
                        action = GameAction[action_name]
                    except (KeyError, ValueError):
                        continue
                    frame = self._execute_action(env, action)
                    self.total_actions += 1
                    self._actions_on_level += 1
                    self._record_action(action)
                    if frame.state in (GameState.GAME_OVER, GameState.WIN):
                        break
                continue

            # --- Normal action selection via the agent ---
            action = self.agent.choose_action(frame)
            self._actions_on_level += 1

            # Track state for cross-life graph and gap analysis
            if frame.frame:
                raw_frames = frame.frame
                frame_grid = np.array(raw_frames[-1], dtype=np.uint8)
                result = self.agent.fp.process(
                    raw_frames[-1] if isinstance(raw_frames[-1], list)
                    else frame_grid.tolist()
                )
                frame_hash = result['frame_hash']
                self._cross_life.record_state(active_level, frame_hash)

                # Collect state descriptions for gap analysis
                # Skip CWM entirely on Level 1 — pure graph exploration is fast and reliable
                # Don't waste time budget on LLM synthesis for levels we already solve
                strategy = pick_strategy(active_level)
                if CWM_AVAILABLE and strategy != Strategy.GRAPH_ONLY:
                    try:
                        cwm = self._get_or_create_cwm(active_level)
                        if cwm:
                            state_desc = cwm.extractor.extract(frame_grid)
                            self._recent_state_descriptions[active_level].append(state_desc.text)
                            if len(self._recent_state_descriptions[active_level]) > 50:
                                self._recent_state_descriptions[active_level] = \
                                    self._recent_state_descriptions[active_level][-50:]

                            action_name = action.name if action else None
                            cwm.observe_frame(frame_grid, action=action_name)
                    except Exception as e:
                        logger.debug(f"CWM observation error: {e}")

            # Attempt CWM synthesis only on deeper levels (skip L1)
            if pick_strategy(active_level) != Strategy.GRAPH_ONLY:
                self._maybe_synthesize_cwm(active_level)

            # On deeper levels with active CWM, try MCTS planning
            if (active_level >= 2 and
                self._level_cwm_active.get(active_level, False) and
                frame.frame):
                available = [a.name for a in GameAction
                           if a.is_simple() and a is not GameAction.RESET]
                plan = self._plan_with_cwm(active_level, frame_grid, available)
                if plan:
                    # Override the graph explorer's choice with MCTS plan
                    try:
                        action = GameAction[plan[0]]
                        logger.debug(f"L{active_level}: MCTS override -> {action.name}")
                    except (KeyError, ValueError):
                        pass  # fall through to graph explorer choice

            # Record and execute
            self._record_action(action)
            frame = self._execute_action(env, action)
            self.total_actions += 1

            # Progress logging
            if step % 100 == 0 and step > 0:
                logger.info(
                    f"Step {step}/{self.max_actions} | "
                    f"L{active_level} | {self._current_strategy} | "
                    f"Actions on level: {self._actions_on_level} | "
                    f"Game-overs: {self.total_game_overs} | "
                    f"Elapsed: {elapsed:.1f}s"
                )

        # --- End of game ---
        elapsed = time.time() - start_time
        final_levels = frame.levels_completed or 0

        results = {
            'game_id': self.game_id,
            'target_level': self.target_level,
            'levels_completed': final_levels,
            'max_level_reached': self.max_level_reached,
            'total_actions': self.total_actions,
            'total_game_overs': self.total_game_overs,
            'total_resets': self.total_resets,
            'elapsed_seconds': elapsed,
            'solutions_recorded': list(self._solutions.keys()),
            'level_times': self.level_times,
            'strategies_used': {
                lvl: pick_strategy(lvl) for lvl in range(1, final_levels + 2)
            },
            'cross_life_stats': {
                lvl: {
                    'game_overs': self._cross_life.game_over_count(lvl),
                    'states_explored': self._cross_life.explored_state_count(lvl),
                }
                for lvl in range(1, final_levels + 2)
            },
            'gap_hints': dict(self._gap_hints),
            'cwm_active_levels': [
                lvl for lvl, active in self._level_cwm_active.items() if active
            ],
        }

        # Store experience
        if EXPERIENCE_AVAILABLE:
            agent_state = {
                'action_count': self.total_actions,
                'levels_completed': final_levels,
                'cwm_status': self.agent.world_model.status() if self.agent.world_model else {},
                'goal_status': self.agent.goal_inferrer.status() if self.agent.goal_inferrer else {},
                'action_history': self._action_history,
                'outcome': 'win' if final_levels >= self.target_level else 'timeout',
            }
            store_game_experience(self.game_id, agent_state)
            logger.info(f"Experience stored for {self.game_id}")

        logger.info(f"\nDeepSolver complete: {self.game_id}")
        logger.info(f"  Levels completed: {final_levels} / target {self.target_level}")
        logger.info(f"  Max level reached: {self.max_level_reached}")
        logger.info(f"  Total actions: {self.total_actions}")
        logger.info(f"  Total game-overs: {self.total_game_overs}")
        logger.info(f"  Elapsed: {elapsed:.1f}s")
        logger.info(f"  Solutions: {list(self._solutions.keys())}")

        return results


# ---------------------------------------------------------------------------
# Standalone CLI runner
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="DeepSolver — Level 2+ focused ARC-AGI-3 runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python deep_solver.py vc33 --target-level 4 --max-actions 10000 --max-time 300\n"
            "  python deep_solver.py ls20 --target-level 3\n"
            "  python deep_solver.py puzzle_42 --target-level 5 --max-time 600\n"
        ),
    )
    parser.add_argument("game_id", help="Game identifier (e.g. vc33, ls20)")
    parser.add_argument("--target-level", type=int, default=5,
                       help="Target level to reach (default: 5)")
    parser.add_argument("--max-actions", type=int, default=10000,
                       help="Maximum total actions (default: 10000)")
    parser.add_argument("--max-time", type=float, default=300.0,
                       help="Maximum wall-clock time in seconds (default: 300)")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Enable verbose logging")

    args = parser.parse_args()

    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    solver = DeepSolver(
        game_id=args.game_id,
        target_level=args.target_level,
        max_actions=args.max_actions,
        max_time=args.max_time,
    )

    try:
        results = solver.run()
    except ImportError as e:
        print(f"Cannot run: {e}")
        print("Install arc-agi: pip install arc-agi")
        return
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        return
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return

    # Print summary
    print("\n" + "=" * 60)
    print(f"  DEEP SOLVER RESULTS: {results['game_id']}")
    print("=" * 60)
    print(f"  Levels completed:  {results['levels_completed']} / {results['target_level']}")
    print(f"  Max level reached: {results['max_level_reached']}")
    print(f"  Total actions:     {results['total_actions']}")
    print(f"  Total game-overs:  {results['total_game_overs']}")
    print(f"  Elapsed time:      {results['elapsed_seconds']:.1f}s")

    if results['solutions_recorded']:
        print(f"  Solutions saved:   L{', L'.join(str(s) for s in results['solutions_recorded'])}")

    if results['level_times']:
        print("  Level times:")
        for lvl, t in sorted(results['level_times'].items()):
            print(f"    L{lvl}: {t:.1f}s")

    if results['cwm_active_levels']:
        print(f"  CWM active on:     L{', L'.join(str(l) for l in results['cwm_active_levels'])}")

    if results['gap_hints']:
        print("  Gap analysis hints:")
        for lvl, hints in results['gap_hints'].items():
            for hint in hints[:3]:
                print(f"    L{lvl}: {hint}")

    # Scoring estimate
    score = 0
    for lvl in range(1, results['levels_completed'] + 1):
        score += lvl
    max_score = sum(range(1, 6))  # 1+2+3+4+5 = 15
    print(f"\n  Score estimate:    {score}/{max_score} "
          f"({score / max_score * 100:.0f}%)")
    print("=" * 60)


if __name__ == "__main__":
    main()
