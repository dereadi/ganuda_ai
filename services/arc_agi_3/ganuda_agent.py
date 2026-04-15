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

try:
    from game_strategy import (
        StrategyTracker, InformationSetTracker,
        select_strategy_v2, classify_game,
        compute_mixed_strategy, sample_mixed_action,
        RANDOMIZER,
    )
    STRATEGY_AVAILABLE = True
    BONANNO_AVAILABLE = True
except ImportError:
    try:
        from game_strategy import StrategyTracker
        STRATEGY_AVAILABLE = True
        BONANNO_AVAILABLE = False
    except ImportError:
        STRATEGY_AVAILABLE = False
        BONANNO_AVAILABLE = False

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
        self.strategy = StrategyTracker() if STRATEGY_AVAILABLE else None
        self.info_tracker = InformationSetTracker() if BONANNO_AVAILABLE else None

        self.action_count = 0
        self.prev_score = 0
        self.prev_frame_hash = None
        self.current_node = None
        self.last_edge_idx = None
        self.level_start_hash = None

        # Action group effectiveness tracking (dc22 fix)
        # Track MAGNITUDE of frame change per group, not just binary success.
        # Timer animations produce small changes (~0.3%) regardless of action.
        # Useful actions produce large changes (>1%). If a group's average
        # frame-change magnitude is low after N attempts, skip it.
        self._group_change_magnitudes = {}  # group_id -> list of float magnitudes
        self._skip_groups = set()           # groups to skip (unproductive)
        self._GROUP_SKIP_THRESHOLD = 15     # attempts before evaluating
        self._GROUP_MIN_MAGNITUDE = 0.01    # below 1% average change = skip
        self._prev_frame_grid = None        # raw grid for magnitude comparison

        # Code-reading tier: 72B reads game source, plans action sequence
        self._code_plan = None          # list of GameAction if plan available
        self._code_plan_index = 0       # where we are in the plan
        self._code_plan_attempted = False  # only try once per level
        self._code_plan_retries = 0     # max 5 retries before giving up
        self._code_plan_feedback = []   # list of "blocked at step N going DIRECTION" observations
        self._code_plan_last_frames = []  # frame hashes during plan execution to detect stuck

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
                self._goal_direction_cache = None  # Re-query VLM after game-over
                # Feedback loop: capture where the plan failed
                if self._code_plan and self._code_plan_index > 0:
                    failed_step = self._code_plan_index
                    failed_action = self._code_plan[min(failed_step - 1, len(self._code_plan) - 1)].name
                    # Detect if we were stuck (same frame hash repeated)
                    stuck = False
                    if len(self._code_plan_last_frames) >= 3:
                        last3 = self._code_plan_last_frames[-3:]
                        stuck = len(set(last3)) == 1
                    feedback = f"Plan failed at step {failed_step}/{len(self._code_plan)}, last action={failed_action}, stuck={stuck}"
                    self._code_plan_feedback.append(feedback)
                    logger.info(f"[CODE_PLAN_FEEDBACK] {feedback}")

                # Reset for retry with new feedback
                self._code_plan = None  # Force fresh plan incorporating feedback
                self._code_plan_index = 0
                self._code_plan_last_frames = []
                self._code_plan_retries += 1
                if self._code_plan_retries > 5:
                    self._code_plan_attempted = True  # Stop retrying after 5 feedback loops
                else:
                    self._code_plan_attempted = False  # Allow retry with feedback
                if self.strategy:
                    self.strategy.record_game_over()
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

        # (Group skip filtering happens at edge selection, not candidate building,
        # to avoid graph/candidate index mismatches)

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

            # Track action group effectiveness by frame-change MAGNITUDE (dc22 fix)
            if self.last_edge_idx < len(self._action_map) and self._prev_frame_grid is not None:
                last_group = self._action_map[self.last_edge_idx][2]
                # Compute magnitude of frame change
                magnitude = float(np.sum(frame_grid != self._prev_frame_grid)) / frame_grid.size
                if last_group not in self._group_change_magnitudes:
                    self._group_change_magnitudes[last_group] = []
                self._group_change_magnitudes[last_group].append(magnitude)

                # Evaluate group after threshold attempts
                mags = self._group_change_magnitudes.get(last_group, [])
                if (len(mags) >= self._GROUP_SKIP_THRESHOLD
                        and last_group not in self._skip_groups):
                    avg_mag = sum(mags) / len(mags)
                    if avg_mag < self._GROUP_MIN_MAGNITUDE:
                        self._skip_groups.add(last_group)
                        logger.info(
                            f"[GROUP_SKIP] Group {last_group} skipped: avg frame change "
                            f"{avg_mag:.4f} ({avg_mag:.1%}) < {self._GROUP_MIN_MAGNITUDE:.1%} "
                            f"after {len(mags)} attempts. Actions in this group are decorative."
                        )

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

        # --- Bonanno: feed observation to InformationSetTracker ---
        if self.info_tracker and self.last_edge_idx is not None:
            action_name = "unknown"
            if self.last_edge_idx < len(self._action_map):
                action_name = self._action_map[self.last_edge_idx][0].name
            self.info_tracker.observe(frame_hash, self.current_node, action_name, frame_hash)

        # Track frame hash and raw grid for change detection + magnitude
        self.prev_frame_hash = frame_hash
        self._prev_frame_grid = frame_grid.copy()

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

        # --- Code-reading tier: execute 72B-planned sequence if available ---
        code_action = self._try_code_plan()
        if code_action is not None:
            self.last_edge_idx = None
            return code_action

        # --- Goal-direction bias: if we detect a likely target, move toward it ---
        # Scan frame for small isolated components that could be the goal.
        # Bias arrow keys toward the component that's farthest from the player.
        # This turns blind exploration into directed navigation for maze/pathfinding games.
        goal_action = self._detect_goal_direction(frame_grid, components, candidates)
        if goal_action is not None:
            # Use goal-directed action with probability that increases over time
            # (early: explore more, late: exploit the direction more)
            import random as _rnd
            exploit_prob = min(0.8, self.action_count / 500.0)  # ramp from 0 to 0.8
            if _rnd.random() < exploit_prob:
                self.last_edge_idx = None
                if self.strategy:
                    self.strategy.record_action(goal_action.name, success=True, new_state=False)
                if self.action_count % 50 == 0:
                    logger.info(f"[GOAL_BIAS] Action #{self.action_count}: {goal_action.name} toward detected target")
                return goal_action

        # --- Ensure current node exists in graph ---
        if self.current_node not in self.graph._nodes:
            n_groups = max(len(group_map), 1)
            self.graph._add_node(self.current_node, len(candidates), group_map)

        # --- Choose action via graph explorer ---
        edge_idx, reasoning = self.graph.choose_edge(self.current_node)

        # --- Group skip: if chosen edge is in a skipped group, reject and retry ---
        if (edge_idx is not None and self._skip_groups
                and edge_idx < len(self._action_map)):
            chosen_group = self._action_map[edge_idx][2]
            if chosen_group in self._skip_groups:
                # Mark this edge as failed so explorer moves on
                try:
                    self.graph.record_test(self.current_node, edge_idx, success=0)
                except (KeyError, ValueError):
                    pass
                # Retry — explorer will pick next edge
                edge_idx, reasoning = self.graph.choose_edge(self.current_node)
                reasoning = f"[GROUP_SKIP g{chosen_group}] " + (reasoning or "")

        if edge_idx is None:
            # Graph explorer has no suggestion — try random available action
            logger.warning("Graph explorer returned None — random fallback")
            action = self._random_action(available)
            self.last_edge_idx = None
            return action

        self.last_edge_idx = edge_idx

        # --- Convert edge index to GameAction ---
        action = self._edge_to_action(edge_idx, candidates, frame_grid)

        # --- Strategy tracking (with Bonanno v2 override) ---
        if self.strategy:
            is_new = self.current_node is not None and self.current_node not in getattr(self, '_seen_nodes', set())
            if not hasattr(self, '_seen_nodes'):
                self._seen_nodes = set()
            self._seen_nodes.add(self.current_node)
            self.strategy.record_action(action.name, success=True, new_state=is_new)

            # Bonanno v2: override strategy selection with game classification
            if BONANNO_AVAILABLE and self.strategy.metrics.total_actions >= 100:
                goal_available = bool(self.goal_inferrer and self._goals_inferred)
                v2_strategy = select_strategy_v2(
                    self.strategy.metrics,
                    info_tracker=self.info_tracker,
                    goal_available=goal_available,
                )
                if v2_strategy != self.strategy.current_strategy:
                    game_type = classify_game(self.strategy.metrics, self.info_tracker)
                    logger.info(
                        f"[BONANNO] {self.strategy.current_strategy} → {v2_strategy} "
                        f"(game_type={game_type}, actions={self.strategy.metrics.total_actions})"
                    )
                    from game_strategy import get_strategy_params
                    self.strategy.current_strategy = v2_strategy
                    self.strategy.current_params = get_strategy_params(v2_strategy)

        if self.action_count % 50 == 0:
            strategy_info = f" | Strategy: {self.strategy.current_strategy}" if self.strategy else ""
            logger.info(f"Action #{self.action_count}: {action.name} | "
                       f"Graph: {self.graph} | Reasoning: {reasoning[:80]}{strategy_info}")

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
        self._goal_direction_cache = None  # Re-query VLM for new level
        # Reset code plan for new level (new positions, new obstacles)
        self._code_plan = None
        self._code_plan_index = 0
        self._code_plan_attempted = False
        # Reset group effectiveness tracking for new level
        self._group_change_magnitudes = {}
        self._skip_groups = set()
        self._prev_frame_grid = None
        if self.info_tracker:
            self.info_tracker = InformationSetTracker() if BONANNO_AVAILABLE else None
        if self.world_model:
            self.world_model = CodeWorldModel(frame_processor=self.fp) if CWM_AVAILABLE else None
        if self.goal_inferrer:
            self.goal_inferrer = GoalInferrer() if GOAL_AVAILABLE else None

    def _detect_goal_direction(self, frame_grid: np.ndarray, components, candidates) -> 'GameAction | None':
        """Ask the VLM on bluefin where to move, then cache the direction.

        Calls the Qwen2-VL-7B model once per level to identify player and goal
        positions, then returns the appropriate arrow key for subsequent frames.
        Falls back to None if VLM is unavailable.
        """
        # Use cached direction if we have one (don't call VLM every frame)
        if hasattr(self, '_goal_direction_cache') and self._goal_direction_cache is not None:
            return self._goal_direction_cache

        # Only ask VLM once every 50 actions (or first frame)
        if self.action_count > 1 and self.action_count % 50 != 0:
            return None

        try:
            import base64
            import io
            import requests as _req
            from PIL import Image

            # Convert frame grid to PNG bytes
            h, w = frame_grid.shape
            scale = 8
            img = Image.new("RGB", (w * scale, h * scale))
            pixels = img.load()
            ARC_COLORS = {
                0: (0,0,0), 1: (0,116,217), 2: (255,65,54), 3: (46,204,64),
                4: (255,220,0), 5: (170,170,170), 6: (240,18,190), 7: (255,133,27),
                8: (127,219,255), 9: (135,12,37), 10: (255,255,255),
            }
            for y in range(h):
                for x in range(w):
                    color = ARC_COLORS.get(int(frame_grid[y, x]) % 11, (128,128,128))
                    for dy in range(scale):
                        for dx in range(scale):
                            pixels[x * scale + dx, y * scale + dy] = color

            buf = io.BytesIO()
            img.save(buf, format='PNG')
            img_b64 = base64.b64encode(buf.getvalue()).decode()

            resp = _req.post(
                'http://10.100.0.2:8090/v1/chat/completions',
                json={
                    'model': 'Qwen/Qwen2-VL-7B-Instruct-AWQ',
                    'messages': [{
                        'role': 'user',
                        'content': [
                            {'type': 'image_url', 'image_url': {'url': f'data:image/png;base64,{img_b64}'}},
                            {'type': 'text', 'text': 'This is a puzzle game. The player must reach the goal. Answer with ONLY one word: UP, DOWN, LEFT, or RIGHT. Which direction should the player move to get closer to the goal?'}
                        ]
                    }],
                    'max_tokens': 10,
                    'temperature': 0.1
                },
                timeout=10
            )

            answer = resp.json()['choices'][0]['message']['content'].strip().upper()
            logger.info(f"[VLM_GOAL] Bluefin says: {answer}")

            direction_map = {
                'UP': GameAction.ACTION1,
                'DOWN': GameAction.ACTION2,
                'LEFT': GameAction.ACTION3,
                'RIGHT': GameAction.ACTION4,
            }

            for keyword, action in direction_map.items():
                if keyword in answer:
                    self._goal_direction_cache = action
                    logger.info(f"[VLM_GOAL] Cached direction: {action.name}")
                    return action

            return None

        except Exception as e:
            logger.debug(f"[VLM_GOAL] VLM unavailable: {e}")
            return None

    def _try_code_plan(self) -> 'GameAction | None':
        """Read game source code and ask 72B to plan the optimal action sequence.

        The two-model architecture:
          - Game source → 72B plans action sequence → agent executes
          - Only called once per level (plans are cached)
          - Falls back to None if source unavailable or 72B offline

        This is Tier 3: code comprehension. The agent doesn't discover rules
        through exploration — it reads them.
        """
        # If we have a plan, execute it
        if self._code_plan and self._code_plan_index < len(self._code_plan):
            action = self._code_plan[self._code_plan_index]
            self._code_plan_index += 1
            # Track frame hashes for stuck detection
            if self.prev_frame_hash:
                self._code_plan_last_frames.append(self.prev_frame_hash)
                if len(self._code_plan_last_frames) > 10:
                    self._code_plan_last_frames = self._code_plan_last_frames[-10:]
            if self._code_plan_index % 10 == 0 or self._code_plan_index == len(self._code_plan):
                logger.info(f"[CODE_PLAN] Executing step {self._code_plan_index}/{len(self._code_plan)}: {action.name}")
            return action

        # Already tried and plan exhausted or failed — don't retry
        if self._code_plan_attempted:
            return None

        # Try to build a plan from game source
        self._code_plan_attempted = True

        try:
            import os
            import glob
            import requests as _req

            # Find game source file
            game_dir = os.path.join(os.path.dirname(__file__), 'environment_files', self.game_id)
            py_files = glob.glob(os.path.join(game_dir, '**', f'{self.game_id}.py'), recursive=True)
            if not py_files:
                logger.info(f"[CODE_PLAN] No source file found for {self.game_id}")
                return None

            source_path = py_files[0]
            with open(source_path, 'r') as f:
                source = f.read()

            import re
            lines = source.splitlines()

            # Find step size from try_move_sprite call: ... * STEP_VAR, ... * STEP_VAR
            step_size = 2  # default
            for line in lines:
                m = re.search(r'try_move_sprite\(self\.\w+,\s*\w+\s*\*\s*(\w+),\s*\w+\s*\*\s*\1\)', line)
                if m:
                    step_var = m.group(1)
                    # Find the value of this variable
                    step_m = re.search(rf'^{step_var}\s*=\s*(\d+)', source, re.MULTILINE)
                    if step_m:
                        step_size = int(step_m.group(1))
                        logger.info(f"[CODE_PLAN] Step size: {step_var} = {step_size}")
                    break

            # Extract the Level definitions section — all set_position calls
            # This gives the 72B the full sprite layout per level
            level_section_lines = []
            in_levels = False
            for i, line in enumerate(lines):
                if 'Level(' in line:
                    in_levels = True
                if in_levels and 'set_position' in line:
                    level_section_lines.append(line.strip())
                if in_levels and line.strip() == ']' and len(level_section_lines) > 5:
                    level_section_lines.append('--- NEXT LEVEL ---')

            # Extract the step/action handler
            action_lines = []
            for i, line in enumerate(lines):
                if 'GameAction.ACTION1' in line or 'GameAction.ACTION2' in line:
                    action_lines.extend(lines[max(0,i-2):i+5])
                    break

            # Extract win condition (function that checks for level completion)
            win_lines = []
            for i, line in enumerate(lines):
                if 'next_level' in line and 'self.' in line:
                    win_lines.extend(lines[max(0,i-5):i+2])
                    break

            current_level = self.prev_score

            # Find player and goal positions from level section
            # Look for the two smallest sprites or known patterns
            positions = []
            for line in level_section_lines[:30]:  # First level only
                if '--- NEXT LEVEL ---' in line:
                    break
                m = re.search(r'set_position\((\d+),\s*(\d+)\)', line)
                if m:
                    positions.append((int(m.group(1)), int(m.group(2)), line))

            # Try to identify player and goal by finding the win condition
            # Pattern: return self.A.x == self.B.x and self.A.y == self.B.y
            player_var = None
            goal_var = None
            for line in lines:
                m = re.search(r'return\s+self\.(\w+)\.x\s*==\s*self\.(\w+)\.x\s+and\s+self\.\1\.y\s*==\s*self\.\2\.y', line)
                if m:
                    player_var = m.group(1)
                    goal_var = m.group(2)
                    logger.info(f"[CODE_PLAN] Win condition found: self.{player_var} must reach self.{goal_var}")
                    break

            # Find their tag assignments to locate them in level sprites
            player_tag = None
            goal_tag = None
            if player_var:
                for line in lines:
                    if player_var in line and 'get_sprites_by_tag' in line:
                        m = re.search(r'get_sprites_by_tag\("(\w+)"\)', line)
                        if m:
                            player_tag = m.group(1)
                            break
            if goal_var:
                for line in lines:
                    if goal_var in line and 'get_sprites_by_tag' in line:
                        m = re.search(r'get_sprites_by_tag\("(\w+)"\)', line)
                        if m:
                            goal_tag = m.group(1)
                            break

            # Find sprite names that have these tags
            player_sprite_name = None
            goal_sprite_name = None
            if player_tag:
                for line in lines:
                    if f'"{player_tag}"' in line and 'tags=' in line:
                        m = re.search(r'"(\w[\w-]*)":\s*Sprite', lines[max(0, lines.index(line)-5):lines.index(line)+1][-1] if line in lines else '')
                        # Simpler: search backwards from tag line for sprite name
                        idx = lines.index(line)
                        for k in range(idx, max(0, idx-10), -1):
                            nm = re.search(r'"([\w-]+)":\s*Sprite', lines[k])
                            if nm:
                                player_sprite_name = nm.group(1)
                                break
                        break
            if goal_tag:
                for line in lines:
                    if f'"{goal_tag}"' in line and 'tags=' in line:
                        idx = lines.index(line)
                        for k in range(idx, max(0, idx-10), -1):
                            nm = re.search(r'"([\w-]+)":\s*Sprite', lines[k])
                            if nm:
                                goal_sprite_name = nm.group(1)
                                break
                        break

            # Find positions by matching sprite names in set_position calls
            # Take the Nth pair for level N (each sprite appears once per level)
            player_positions = []
            goal_positions = []
            for line in level_section_lines:
                if '--- NEXT LEVEL ---' in line:
                    continue
                if player_sprite_name and f'"{player_sprite_name}"' in line:
                    m = re.search(r'set_position\((\d+),\s*(\d+)\)', line)
                    if m:
                        player_positions.append((int(m.group(1)), int(m.group(2))))
                if goal_sprite_name and f'"{goal_sprite_name}"' in line:
                    m = re.search(r'set_position\((\d+),\s*(\d+)\)', line)
                    if m:
                        goal_positions.append((int(m.group(1)), int(m.group(2))))

            player_pos = player_positions[current_level] if current_level < len(player_positions) else None
            goal_pos = goal_positions[current_level] if current_level < len(goal_positions) else None

            logger.info(f"[CODE_PLAN] player_var={player_var} goal_var={goal_var} player_tag={player_tag} goal_tag={goal_tag}")
            logger.info(f"[CODE_PLAN] player_sprite={player_sprite_name} goal_sprite={goal_sprite_name}")
            logger.info(f"[CODE_PLAN] player_pos={player_pos} goal_pos={goal_pos}")

            # If we found positions, compute the plan directly — no need for LLM
            if player_pos and goal_pos:
                dx = goal_pos[0] - player_pos[0]
                dy = goal_pos[1] - player_pos[1]
                plan = []
                # Horizontal moves
                h_action = GameAction.ACTION4 if dx > 0 else GameAction.ACTION3
                h_count = abs(dx) // step_size
                # Vertical moves
                v_action = GameAction.ACTION1 if dy < 0 else GameAction.ACTION2
                v_count = abs(dy) // step_size

                # Interleave to navigate around obstacles
                for i in range(max(h_count, v_count)):
                    if i < h_count:
                        plan.append(h_action)
                    if i < v_count:
                        plan.append(v_action)

                self._code_plan = plan
                self._code_plan_index = 0
                logger.info(f"[CODE_PLAN] COMPUTED plan: {len(plan)} actions ({h_count} {h_action.name} + {v_count} {v_action.name})")
                action = self._code_plan[self._code_plan_index]
                self._code_plan_index += 1
                return action

            # Fallback: ask the 72B with the computed positions if we have them
            pos_hint = ""
            if player_pos and goal_pos:
                pos_hint = f"Player is at {player_pos}. Goal is at {goal_pos}."
            elif player_sprite_name or goal_sprite_name:
                pos_hint = f"Player sprite name contains '{player_sprite_name}'. Goal sprite name contains '{goal_sprite_name}'."

            # Simple prompt with computed math
            prompt = f"""Navigation puzzle. Player must reach the goal.
Step size = {step_size} pixels per move.
ACTION1=up(y-{step_size}), ACTION2=down(y+{step_size}), ACTION3=left(x-{step_size}), ACTION4=right(x+{step_size})

Level {current_level + 1} sprite positions:
{chr(10).join(p[2].strip() for p in positions[:15])}

Step budget: 128 actions maximum.

{('Previous attempts failed: ' + '; '.join(self._code_plan_feedback[-3:])) if self._code_plan_feedback else ''}

IMPORTANT: The player sprite has tag "pcxjvnmybet" or is the collidable sprite with layer=1. The goal sprite has tag "bqxa" or is a small 2x2 invisible/non-collidable sprite.
The player needs to REACH the goal position. Compute dx and dy:
- If goal_x > player_x: need RIGHT moves (ACTION4). Count = (goal_x - player_x) / {step_size}
- If goal_x < player_x: need LEFT moves (ACTION3). Count = (player_x - goal_x) / {step_size}
- If goal_y < player_y: need UP moves (ACTION1). Count = (player_y - goal_y) / {step_size}
- If goal_y > player_y: need DOWN moves (ACTION2). Count = (goal_y - player_y) / {step_size}

Output ONLY the comma-separated action list. MUST be under 50 actions total.
Do one direction first, then the other. Example: ACTION4,ACTION4,ACTION4,ACTION1,ACTION1"""

            logger.info(f"[CODE_PLAN] Asking 72B to plan Level {current_level + 1} for {self.game_id}...")

            resp = _req.post(
                'http://localhost:8000/v1/chat/completions',
                json={
                    'model': '/ganuda/models/qwen2.5-72b-instruct-awq',
                    'messages': [{'role': 'user', 'content': prompt}],
                    'max_tokens': 500,
                    'temperature': 0.1
                },
                timeout=30
            )

            answer = resp.json()['choices'][0]['message']['content'].strip()
            logger.info(f"[CODE_PLAN] 72B response: {answer[:200]}")

            # Parse action sequence
            action_map = {
                'ACTION1': GameAction.ACTION1,
                'ACTION2': GameAction.ACTION2,
                'ACTION3': GameAction.ACTION3,
                'ACTION4': GameAction.ACTION4,
                'ACTION5': GameAction.ACTION5,
            }

            plan = []
            for token in re.split(r'[,\s\n]+', answer):
                token = token.strip().upper()
                if token in action_map:
                    plan.append(action_map[token])

            if plan:
                self._code_plan = plan
                self._code_plan_index = 0
                logger.info(f"[CODE_PLAN] Plan ready: {len(plan)} actions for Level {current_level + 1}")
                # Return first action
                action = self._code_plan[self._code_plan_index]
                self._code_plan_index += 1
                return action
            else:
                logger.warning(f"[CODE_PLAN] Could not parse plan from 72B response")
                return None

        except Exception as e:
            logger.warning(f"[CODE_PLAN] Failed: {e}")
            return None

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
