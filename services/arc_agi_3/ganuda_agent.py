"""
GanudaAgent — ARC-AGI-3 Contest Agent

Three-tier generalist:
  Tier 1: Graph explorer (algorithmic, no LLM) — handles 95%+ of actions
  Tier 2: Jr value estimation (future) — biases exploration toward progress
  Tier 3: Council goal inference (future) — infers win conditions on stall

This file wires the frame processor and graph explorer into the official
Agent interface from the ARC-AGI-3 baseline.

Council vote #526e0696 approved. Coyote dissent noted (95/5 assumption).
"""

import logging
import json
import numpy as np
from typing import Any, Optional

from arcengine import FrameData, GameAction, GameState

from frame_processor import FrameProcessor, Component
from graph_explorer import GraphExplorer

# CWM imports (optional — graceful degradation if not ready)
try:
    from world_model import CodeWorldModel
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


class GanudaAgent:
    """Ganuda Federation ARC-AGI-3 agent.

    Implements the core choose_action / is_done loop without inheriting
    from the baseline Agent class (which has import dependencies on
    arc_agi.EnvironmentWrapper and recorder). This can be used standalone
    for local testing, or wrapped in the baseline Agent for competition.
    """

    MAX_ACTIONS = 10000  # 8 hours of play, not 80 moves

    def __init__(self, game_id: str = "unknown"):
        self.game_id = game_id
        self.fp = FrameProcessor()
        self.graph = GraphExplorer()

        self.action_count = 0
        self.prev_score = 0
        self.prev_frame_hash = None
        self.current_node = None
        self.last_edge_idx = None
        self.level_start_hash = None

        # Basin-hopping: track game-overs to detect when stuck in a basin
        self._game_over_count = 0
        self._basin_hop_sequence = None  # forced opening moves after basin detected
        self._basin_hop_index = 0
        self._tried_openings = set()  # track which opening sequences we've tried

        # Map from edge index to (GameAction, optional data)
        self._action_map = []  # rebuilt each frame

        # CWM (Code World Model) — synthesizes game rules from observations
        self.world_model = CodeWorldModel(frame_processor=self.fp) if CWM_AVAILABLE else None
        self._cwm_active = False  # True when CWM has a validated model

        # Goal inference — infers win conditions from state transitions
        self.goal_inferrer = GoalInferrer() if GOAL_AVAILABLE else None
        self._goals_inferred = False

    def is_done(self, latest_frame: FrameData) -> bool:
        return latest_frame.state is GameState.WIN

    def choose_action(self, latest_frame: FrameData) -> GameAction:
        """Core decision function. Called once per turn."""
        self.action_count += 1

        # --- Handle game start and game over ---
        if latest_frame.state in (GameState.NOT_PLAYED, GameState.GAME_OVER):
            self.last_edge_idx = None
            if latest_frame.state == GameState.GAME_OVER:
                self._game_over_count += 1
                # Basin detection: after 5 game-overs without level-up,
                # we're stuck in a basin. Generate a new opening sequence
                # to land in a different region of the state space.
                if self._game_over_count % 5 == 0:
                    self._basin_hop_sequence = self._generate_basin_hop()
                    self._basin_hop_index = 0
                    logger.info(f"Basin hop #{self._game_over_count // 5}: "
                               f"trying opening {self._basin_hop_sequence[:5]}...")
            return GameAction.RESET

        # --- Basin-hopping: execute forced opening sequence ---
        if self._basin_hop_sequence and self._basin_hop_index < len(self._basin_hop_sequence):
            action = self._basin_hop_sequence[self._basin_hop_index]
            self._basin_hop_index += 1
            if self._basin_hop_index >= len(self._basin_hop_sequence):
                self._basin_hop_sequence = None  # done with forced opening
            return action

        # --- Extract frame data ---
        # frame is list of 2D grids; take the last one (current visual state)
        raw_frames = latest_frame.frame
        if not raw_frames:
            return GameAction.RESET

        frame_grid = np.array(raw_frames[-1], dtype=np.uint8)

        # --- Detect level transition ---
        current_score = latest_frame.levels_completed or 0
        if current_score > self.prev_score:
            logger.info(f"Level up! {self.prev_score} -> {current_score}")
            self._on_level_up(frame_grid)
            self.prev_score = current_score

        # --- Process frame ---
        # process() expects list[list[list[int]]], not numpy
        result = self.fp.process(raw_frames[-1] if isinstance(raw_frames[-1], list)
                                 else frame_grid.tolist())
        frame_hash = result['frame_hash']
        components = result['components']
        action_groups = result['action_groups']

        # --- Build action candidates for this frame ---
        available = set(latest_frame.available_actions or [])
        candidates = self._build_candidates(components, action_groups, available, frame_grid)

        # --- Build group_to_remaining mapping for graph explorer ---
        group_map = self._build_group_map(candidates)

        # --- Initialize or update graph ---
        if self.current_node is None:
            # First frame of game/level
            n_groups = max(len(group_map), 1)
            self.graph = GraphExplorer(n_groups=n_groups)
            self.graph.initialize(frame_hash, len(candidates), group_map)
            self.current_node = frame_hash
            self.level_start_hash = frame_hash
        elif self.last_edge_idx is not None:
            # Did the frame change? That's the success signal
            frame_changed = (frame_hash != self.prev_frame_hash)
            suspicious = (frame_hash == self.level_start_hash)

            try:
                if frame_changed:
                    is_new = frame_hash not in self.graph._nodes
                    self.graph.record_test(
                        self.current_node, self.last_edge_idx,
                        success=1,
                        target_node=frame_hash,
                        target_num_candidates=len(candidates) if is_new else None,
                        target_group_to_remaining=group_map if is_new else None,
                        suspicious_transition=suspicious,
                    )
                else:
                    self.graph.record_test(
                        self.current_node, self.last_edge_idx,
                        success=0,
                    )
            except (KeyError, ValueError) as e:
                # Graph state inconsistency (e.g., after level reset) — reinitialize
                logger.warning(f"Graph error: {e}. Reinitializing node.")
                if frame_hash not in self.graph._nodes:
                    self.graph._add_node(frame_hash, len(candidates), group_map)

            self.current_node = frame_hash

        # Track frame hash for change detection
        self.prev_frame_hash = frame_hash

        # --- CWM: observe frame and attempt synthesis ---
        if self.world_model:
            # Get the action name that produced this frame
            action_name = None
            if self.last_edge_idx is not None and self.last_edge_idx < len(self._action_map):
                action_name = self._action_map[self.last_edge_idx][0].name

            self.world_model.observe_frame(frame_grid, action=action_name)

            # Attempt synthesis periodically when we have enough data
            if (not self._cwm_active and
                self.world_model.store.ready_for_synthesis() and
                self.action_count % 50 == 0):
                logger.info(f"CWM: Attempting synthesis ({len(self.world_model.store)} transitions)...")
                if self.world_model.attempt_synthesis():
                    self._cwm_active = True
                    logger.info(f"CWM: Model validated ({self.world_model.accuracy:.0%})! Planning mode active.")

        # --- Goal inference: feed transitions and trigger on stall ---
        if self.goal_inferrer and self.world_model:
            # Feed transitions from CWM's transition store
            if (not self._goals_inferred and
                self.world_model.store.ready_for_synthesis() and
                self.action_count % 100 == 0):
                logger.info("Goal inference: analyzing transitions...")
                # Feed collected transitions to goal inferrer
                for t in self.world_model.store.transitions:
                    self.goal_inferrer.observe(t.before, t.action, t.after)
                self.goal_inferrer.infer_goals()
                self._goals_inferred = True
                logger.info(f"Goal inference: {self.goal_inferrer.status()}")

        # --- Choose action: CWM planning or graph exploration ---
        if self._cwm_active and self.world_model:
            available_actions = [c[0].name for c in candidates]
            # Pass goal scorer if available — turns wandering into solving
            goal_fn = None
            if self.goal_inferrer and self._goals_inferred:
                goal_fn = self.goal_inferrer.score_objects
            plan = self.world_model.plan(frame_grid, available_actions, goal_score_fn=goal_fn)
            if plan:
                action = self._name_to_action(plan[0], candidates)
                if action:
                    self.last_edge_idx = None
                    return action
            logger.info("CWM: MCTS returned no plan, falling back to explorer")

        # --- Ensure current node exists in graph ---
        if self.current_node not in self.graph._nodes:
            n_groups = max(len(group_map), 1)
            self.graph._add_node(self.current_node, len(candidates), group_map)

        # --- Choose action via graph explorer ---
        edge_idx, reasoning = self.graph.choose_edge(self.current_node)

        if edge_idx is None:
            # Graph explorer has no suggestion — try random available action
            logger.warning("Graph explorer returned None — random fallback")
            action = self._random_action(available)
            self.last_edge_idx = None
            return action

        self.last_edge_idx = edge_idx

        # --- Convert edge index to GameAction ---
        action = self._edge_to_action(edge_idx, candidates, frame_grid)

        if self.action_count % 50 == 0:
            logger.info(f"Action #{self.action_count}: {action.name} | "
                       f"Graph: {self.graph} | Reasoning: {reasoning[:80]}")

        return action

    def _on_level_up(self, frame_grid: np.ndarray):
        """Handle level transition — reset everything for fresh exploration."""
        self.graph.reset()
        self.fp.reset_tracking()
        self.current_node = None
        self.last_edge_idx = None
        self.level_start_hash = None
        self.prev_frame_hash = None
        # Reset basin state — we escaped the basin by solving the level
        self._game_over_count = 0
        self._basin_hop_sequence = None
        self._basin_hop_index = 0
        self._tried_openings = set()
        self._cwm_active = False
        self._goals_inferred = False
        if self.world_model:
            self.world_model = CodeWorldModel(frame_processor=self.fp) if CWM_AVAILABLE else None
        if self.goal_inferrer:
            self.goal_inferrer = GoalInferrer() if GOAL_AVAILABLE else None

    def _build_candidates(self, components, action_groups, available, frame_grid):
        """Build the ordered list of action candidates.

        Group 0 (highest priority): Arrow key actions (ACTION1-5)
        Groups 1-4: Click actions on segmented components, tiered by salience

        Returns list of (GameAction, optional_data, group) tuples.
        """
        candidates = []

        # Arrow keys are always group 0 (highest priority)
        arrow_actions = [
            GameAction.ACTION1, GameAction.ACTION2,
            GameAction.ACTION3, GameAction.ACTION4, GameAction.ACTION5,
        ]
        for action in arrow_actions:
            if action.value in available:
                candidates.append((action, None, 0))

        # Click actions from segmented components
        # GameAction.ACTION6 is the complex click action
        if GameAction.ACTION6.value in available:
            for group_idx, comp_indices in enumerate(action_groups):
                click_group = group_idx + 1  # offset by 1 since arrows are group 0
                for comp_idx in comp_indices:
                    if comp_idx >= len(components):
                        continue
                    comp = components[comp_idx]
                    # Click the center of the component's bounding box
                    cx = (comp.bounding_box[0] + comp.bounding_box[2]) // 2
                    cy = (comp.bounding_box[1] + comp.bounding_box[3]) // 2
                    candidates.append((GameAction.ACTION6, {'x': cx, 'y': cy}, click_group))

        self._action_map = candidates
        return candidates

    def _build_group_map(self, candidates):
        """Build group_to_remaining: list of sets mapping group -> edge indices."""
        if not candidates:
            return [set()]
        n_groups = max(c[2] for c in candidates) + 1
        groups = [set() for _ in range(n_groups)]
        for idx, (action, data, group) in enumerate(candidates):
            groups[group].add(idx)
        return groups

    def _edge_to_action(self, edge_idx, candidates, frame_grid):
        """Convert a graph edge index to a GameAction."""
        if edge_idx < len(candidates):
            action, data, group = candidates[edge_idx]
            if data and action.is_complex():
                action.set_data(data)
            action.reasoning = json.dumps({
                'edge': edge_idx,
                'group': group,
                'agent': 'ganuda',
            })
            return action

        # Fallback: index out of range
        return self._random_action(set())

    def _name_to_action(self, action_name, candidates):
        """Convert an action name (e.g., 'ACTION1') to a GameAction."""
        for action, data, group in candidates:
            if action.name == action_name:
                if data and action.is_complex():
                    action.set_data(data)
                return action
        # Try direct enum lookup
        try:
            return GameAction[action_name]
        except (KeyError, ValueError):
            return None

    def _generate_basin_hop(self, length=8):
        """Generate a new opening sequence to escape the current exploration basin.

        Each hop tries a fundamentally different opening — different first moves
        lead to different regions of the state space. This is basin-hopping:
        when you've thoroughly explored one area without finding the solution,
        jump to a completely different area.
        """
        import random
        import itertools

        simple_actions = [a for a in GameAction if a.is_simple() and a is not GameAction.RESET]

        # Try systematic openings we haven't tried before
        hop_num = self._game_over_count // 5

        # Strategy 1: Start with the action we've used LEAST
        # Strategy 2: Repeat one action many times (go deep in one direction)
        # Strategy 3: Alternate between two actions (zig-zag)
        # Strategy 4: Reverse of previous opening
        # Strategy 5+: Random permutations

        strategies = [
            # Repeat each single action to go deep in one direction
            *[[a] * length for a in simple_actions],
            # Pairs: alternate between two actions
            *[[simple_actions[i], simple_actions[j]] * (length // 2)
              for i in range(len(simple_actions))
              for j in range(i+1, len(simple_actions))],
        ]

        # Pick a strategy we haven't tried, cycling through them
        idx = hop_num % len(strategies) if strategies else 0
        sequence = strategies[idx] if idx < len(strategies) else [random.choice(simple_actions) for _ in range(length)]

        # Convert to tuple for tracking, avoid repeating same opening
        seq_key = tuple(a.name for a in sequence)
        if seq_key in self._tried_openings:
            # Already tried this opening — randomize instead
            sequence = [random.choice(simple_actions) for _ in range(length)]
        self._tried_openings.add(tuple(a.name for a in sequence))

        return sequence

    def _random_action(self, available):
        """Pick a random non-reset action."""
        import random
        choices = [a for a in GameAction if a is not GameAction.RESET and a.is_simple()]
        return random.choice(choices) if choices else GameAction.ACTION1


# ---------------------------------------------------------------------------
# Standalone test runner (uses arc_agi local environment)
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    import sys
    logging.basicConfig(level=logging.INFO, format='%(message)s')

    game_id = sys.argv[1] if len(sys.argv) > 1 else 'ls20'
    max_actions = int(sys.argv[2]) if len(sys.argv) > 2 else 200

    try:
        from arc_agi import Arcade
        arcade = Arcade()
        env = arcade.make(game_id)

        agent = GanudaAgent(game_id=game_id)
        print(f"GanudaAgent — playing {game_id}, max {max_actions} actions")

        # Retrieve past experiences for this game type
        if EXPERIENCE_AVAILABLE:
            prior = retrieve_game_experiences(game_id)
            if prior:
                print(f"  Experience Bank: {len(prior)} chars of prior knowledge loaded")
            else:
                print(f"  Experience Bank: no prior experiences for {game_id}")

        # Get initial frame
        obs = env.observation_space
        frame = FrameData(
            game_id=obs.game_id,
            frame=[arr.tolist() for arr in obs.frame],
            state=obs.state,
            levels_completed=obs.levels_completed,
            win_levels=obs.win_levels,
            guid=obs.guid,
            full_reset=obs.full_reset,
            available_actions=obs.available_actions,
        )

        for i in range(max_actions):
            action = agent.choose_action(frame)

            # Execute action
            if action.is_complex():
                data = action.action_data.model_dump()
            else:
                data = {}
            raw = env.step(action, data=data, reasoning={})

            frame = FrameData(
                game_id=raw.game_id,
                frame=[arr.tolist() for arr in raw.frame],
                state=raw.state,
                levels_completed=raw.levels_completed,
                win_levels=raw.win_levels,
                guid=raw.guid,
                full_reset=raw.full_reset,
                available_actions=raw.available_actions,
            )

            # Print progress every 10 actions
            if (i + 1) % 10 == 0 or frame.state == GameState.WIN:
                print(f"  Action {i+1}: {action.name} | "
                      f"Levels: {frame.levels_completed} | "
                      f"State: {frame.state.name}")

            if agent.is_done(frame):
                print(f"\n  WIN! Solved in {i+1} actions, "
                      f"{frame.levels_completed} levels completed.")
                break

            if frame.state == GameState.GAME_OVER:
                print(f"  Game over at action {i+1}, resetting...")

        else:
            print(f"\n  Max actions ({max_actions}) reached. "
                  f"Levels completed: {frame.levels_completed}")

        # Store experience for future games
        if EXPERIENCE_AVAILABLE:
            state_dict = {
                'action_count': agent.action_count,
                'levels_completed': frame.levels_completed,
                'cwm_status': agent.world_model.status() if agent.world_model else {},
                'goal_status': agent.goal_inferrer.status() if agent.goal_inferrer else {},
            }
            store_game_experience(game_id, state_dict)
            print(f"  Experience stored for {game_id}")

    except ImportError as e:
        print(f"Cannot run standalone test: {e}")
        print("Install arc-agi: pip install arc-agi")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
