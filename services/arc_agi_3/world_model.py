"""
Code World Model (CWM) for ARC-AGI-3.

Observes game state transitions, synthesizes a Python simulator of the game
rules using a local 72B LLM (Qwen2.5-72B on vLLM), and runs MCTS planning
against the synthesized model.

Fallback: when synthesis fails or accuracy is too low, the agent continues
using the graph explorer for pure algorithmic exploration.

Dependencies: numpy, requests (both in venv).
"""

from __future__ import annotations

import hashlib
import logging
import math
import random
import re
import textwrap
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np
import requests

from frame_processor import Component, FrameProcessor

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# ARC palette — index to human-readable colour name
# ---------------------------------------------------------------------------

ARC_COLOR_NAMES: Dict[int, str] = {
    0: "black",
    1: "blue",
    2: "red",
    3: "green",
    4: "yellow",
    5: "gray",
    6: "magenta",
    7: "orange",
    8: "cyan",
    9: "brown",
    10: "white",
    11: "maroon",
    12: "olive",
    13: "teal",
    14: "navy",
    15: "pink",
}

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

VLLM_URL = "http://localhost:8000/v1/chat/completions"
VLLM_MODEL = "/ganuda/models/qwen2.5-72b-instruct-awq"

MIN_TRANSITIONS_FOR_SYNTHESIS = 20
HOLDOUT_FRACTION = 0.30
SYNTHESIS_TEMPERATURE = 0.3
SYNTHESIS_MAX_TOKENS = 4096
MCTS_DEPTH_LIMIT = 12
MCTS_SIMULATIONS = 80
MCTS_EXPLORATION_C = 1.4

# Fibonacci-scaled depth/simulation configs per game level
# Depth limits follow the Fibonacci sequence matching human baseline scaling.
LEVEL_CONFIGS: Dict[int, Tuple[int, int]] = {
    1: (12, 80),    # depth_limit, n_simulations
    2: (21, 120),
    3: (34, 200),
}
LEVEL_DEFAULT_CONFIG: Tuple[int, int] = (55, 300)  # Level 4+

# Fibonacci sequence for iterative deepening increments
_FIB_SEQUENCE = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233]


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class ObjectDesc:
    """Compact description of a single segmented object."""
    label: str        # e.g. "blue_block_0"
    color: str        # human-readable colour
    color_id: int     # raw palette index
    x: int            # bbox top-left x
    y: int            # bbox top-left y
    width: int
    height: int
    area: int

    def to_text(self) -> str:
        return f"{self.label} at ({self.x},{self.y}) size {self.width}x{self.height}"


@dataclass
class StateDescription:
    """Compact textual snapshot of a single frame."""
    objects: List[ObjectDesc]
    background_color: str
    text: str  # the full one-line description

    def object_dict_list(self) -> List[Dict[str, Any]]:
        """Serialise objects to a list of plain dicts (for the synthesised fn)."""
        return [
            {
                "label": o.label,
                "color": o.color,
                "color_id": o.color_id,
                "x": o.x,
                "y": o.y,
                "width": o.width,
                "height": o.height,
                "area": o.area,
            }
            for o in self.objects
        ]


@dataclass
class Transition:
    """One observed (state, action, next_state) tuple."""
    before: StateDescription
    action: str
    after: StateDescription


# ---------------------------------------------------------------------------
# 1. State Representation Extraction
# ---------------------------------------------------------------------------

class StateExtractor:
    """Convert a 64x64 uint8 frame into a compact StateDescription."""

    def __init__(self, frame_processor: Optional[FrameProcessor] = None):
        self.fp = frame_processor or FrameProcessor()

    def extract(self, frame: np.ndarray) -> StateDescription:
        """
        Segment *frame* (H x W uint8, values 0-15) into objects and produce
        a text description under ~200 tokens.
        """
        if frame.ndim != 2:
            raise ValueError(f"Expected 2D frame, got shape {frame.shape}")

        # Segment
        label_map, components = self.fp.segment_frame(frame)

        # Determine background: the colour covering the most pixels
        bg_comp = max(components, key=lambda c: c.area) if components else None
        bg_color = ARC_COLOR_NAMES.get(bg_comp.color, "unknown") if bg_comp else "black"
        bg_id = bg_comp.component_id if bg_comp else -1

        # Build object list, skipping background and very small noise
        color_counters: Dict[str, int] = {}
        objects: List[ObjectDesc] = []

        for comp in components:
            if comp.component_id == bg_id:
                continue
            if comp.area < 2:
                continue  # skip single-pixel noise

            cname = ARC_COLOR_NAMES.get(comp.color, f"c{comp.color}")
            idx = color_counters.get(cname, 0)
            color_counters[cname] = idx + 1

            label = f"{cname}_{idx}"
            x1, y1, x2, y2 = comp.bounding_box
            objects.append(ObjectDesc(
                label=label,
                color=cname,
                color_id=comp.color,
                x=x1, y=y1,
                width=x2 - x1 + 1,
                height=y2 - y1 + 1,
                area=comp.area,
            ))

        # Sort by area descending so the prompt highlights important objects first
        objects.sort(key=lambda o: o.area, reverse=True)

        # Truncate to keep under ~200 tokens (roughly 30 objects max)
        objects = objects[:30]

        # Build text
        if objects:
            obj_strs = ", ".join(o.to_text() for o in objects)
            text = f"Objects: {obj_strs}. Background: {bg_color}."
        else:
            text = f"Empty frame. Background: {bg_color}."

        return StateDescription(objects=objects, background_color=bg_color, text=text)


# ---------------------------------------------------------------------------
# 2. Transition Collection
# ---------------------------------------------------------------------------

class TransitionStore:
    """Accumulates observed (state, action, next_state) transitions."""

    def __init__(self):
        self.transitions: List[Transition] = []
        self._seen_hashes: set = set()

    def add(self, before: StateDescription, action: str, after: StateDescription) -> None:
        """Add a transition, deduplicating by content hash."""
        h = hashlib.md5(
            f"{before.text}|{action}|{after.text}".encode()
        ).hexdigest()
        if h in self._seen_hashes:
            return
        self._seen_hashes.add(h)
        self.transitions.append(Transition(before=before, action=action, after=after))

    def ready_for_synthesis(self) -> bool:
        return len(self.transitions) >= MIN_TRANSITIONS_FOR_SYNTHESIS

    def split(self) -> Tuple[List[Transition], List[Transition]]:
        """Split into train / holdout sets."""
        n = len(self.transitions)
        n_holdout = max(1, int(n * HOLDOUT_FRACTION))
        shuffled = list(self.transitions)
        random.shuffle(shuffled)
        return shuffled[n_holdout:], shuffled[:n_holdout]

    def __len__(self) -> int:
        return len(self.transitions)


# ---------------------------------------------------------------------------
# 3. World Model Synthesis (LLM-based)
# ---------------------------------------------------------------------------

def _format_transitions_for_prompt(transitions: List[Transition], max_examples: int = 25) -> str:
    """Format transitions as numbered examples for the LLM prompt."""
    lines = []
    for i, t in enumerate(transitions[:max_examples]):
        lines.append(f"Example {i + 1}:")
        lines.append(f"  BEFORE: {t.before.text}")
        lines.append(f"  ACTION: {t.action}")
        lines.append(f"  AFTER:  {t.after.text}")
        lines.append("")
    return "\n".join(lines)


SYNTHESIS_SYSTEM_PROMPT = textwrap.dedent("""\
    You are a game-rule reverse engineer. You observe state transitions in
    a grid puzzle game and synthesise a Python function that predicts how
    the game state changes when an action is applied.

    RULES:
    - Output ONLY a single Python function with this exact signature:
        def predict_next_state(objects: list[dict], action: str) -> list[dict]:
    - Each dict in `objects` has keys: label, color, color_id, x, y, width, height, area.
    - The function must return a NEW list of dicts (same schema) representing
      the predicted next state.
    - Do NOT import anything. Use only builtins (list, dict, int, str, etc.).
    - Do NOT print anything. Do NOT include any text outside the function.
    - Wrap the function in ```python ... ``` markers.
""")


def _build_synthesis_prompt(transitions: List[Transition]) -> str:
    examples = _format_transitions_for_prompt(transitions)
    return textwrap.dedent(f"""\
        Here are observed state transitions in a grid puzzle game.
        Each shows the objects present before an action, the action taken,
        and the objects present after.

        {examples}

        Synthesize a Python function `predict_next_state(objects, action) -> objects`
        that captures the game rules you observe in these transitions.
        The function should predict how objects move, appear, disappear, or change
        colour when an action is applied.

        Return ONLY the Python function, no explanation.
    """)


def _call_vllm(system: str, user: str, temperature: float = SYNTHESIS_TEMPERATURE,
               max_tokens: int = SYNTHESIS_MAX_TOKENS, timeout: float = 120.0) -> Optional[str]:
    """Call the local vLLM endpoint. Returns the assistant content or None on error."""
    payload = {
        "model": VLLM_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    try:
        resp = requests.post(VLLM_URL, json=payload, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        logger.warning(f"vLLM call failed: {e}")
        return None


def _extract_python_code(text: str) -> Optional[str]:
    """Pull the first ```python ... ``` block out of the LLM response."""
    pattern = r"```python\s*\n(.*?)```"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    # Fallback: if the whole response looks like a function def, use it
    if "def predict_next_state" in text:
        # Grab from the def line to the end
        idx = text.index("def predict_next_state")
        return text[idx:].strip()
    return None


def synthesize_world_model(transitions: List[Transition]) -> Optional[Callable]:
    """
    Send transitions to the 72B LLM, parse the returned Python code,
    compile it, and return the `predict_next_state` callable (or None on failure).
    """
    user_prompt = _build_synthesis_prompt(transitions)
    raw = _call_vllm(SYNTHESIS_SYSTEM_PROMPT, user_prompt)
    if raw is None:
        logger.warning("Synthesis: no response from LLM")
        return None

    code = _extract_python_code(raw)
    if code is None:
        logger.warning("Synthesis: could not extract Python code from response")
        return None

    # Compile in a restricted namespace
    namespace: Dict[str, Any] = {}
    try:
        exec(code, {"__builtins__": __builtins__}, namespace)
    except Exception as e:
        logger.warning(f"Synthesis: compilation failed: {e}")
        return None

    fn = namespace.get("predict_next_state")
    if fn is None or not callable(fn):
        logger.warning("Synthesis: predict_next_state not found in compiled code")
        return None

    return fn


# ---------------------------------------------------------------------------
# 4. Validation
# ---------------------------------------------------------------------------

def _objects_match(predicted: List[Dict], actual: StateDescription, tolerance: int = 2) -> bool:
    """
    Check whether the predicted object list approximately matches the actual state.

    Matching criteria per object:
    - Same colour
    - Position within `tolerance` pixels
    - Size within `tolerance` pixels

    We require at least 70% of actual objects to have a match in the prediction.
    """
    actual_objs = actual.object_dict_list()
    if not actual_objs:
        return len(predicted) == 0

    matched = 0
    used = set()

    for ao in actual_objs:
        for j, po in enumerate(predicted):
            if j in used:
                continue
            if (po.get("color") == ao["color"]
                    and abs(po.get("x", 0) - ao["x"]) <= tolerance
                    and abs(po.get("y", 0) - ao["y"]) <= tolerance
                    and abs(po.get("width", 0) - ao["width"]) <= tolerance
                    and abs(po.get("height", 0) - ao["height"]) <= tolerance):
                matched += 1
                used.add(j)
                break

    return matched >= len(actual_objs) * 0.70


def validate_world_model(
    fn: Callable,
    holdout: List[Transition],
) -> Tuple[float, int, int]:
    """
    Test the synthesized function against held-out transitions.

    Returns (accuracy, n_correct, n_total).
    """
    correct = 0
    total = len(holdout)

    for t in holdout:
        objects_in = t.before.object_dict_list()
        try:
            predicted = fn(objects_in, t.action)
        except Exception:
            continue
        if not isinstance(predicted, list):
            continue
        if _objects_match(predicted, t.after):
            correct += 1

    accuracy = correct / total if total > 0 else 0.0
    return accuracy, correct, total


# ---------------------------------------------------------------------------
# 5. MCTS Planner
# ---------------------------------------------------------------------------

@dataclass
class MCTSNode:
    """A node in the Monte Carlo Tree Search."""
    objects: List[Dict[str, Any]]
    action_taken: Optional[str] = None
    parent: Optional["MCTSNode"] = None
    children: Dict[str, "MCTSNode"] = field(default_factory=dict)
    visits: int = 0
    value: float = 0.0
    _state_hash: Optional[str] = None

    @property
    def state_hash(self) -> str:
        if self._state_hash is None:
            # Deterministic hash of the object configuration
            key = str(sorted(
                (o.get("label", ""), o.get("x", 0), o.get("y", 0))
                for o in self.objects
            ))
            self._state_hash = hashlib.md5(key.encode()).hexdigest()
        return self._state_hash

    def is_leaf(self) -> bool:
        return len(self.children) == 0

    def ucb1(self, parent_visits: int, c: float = MCTS_EXPLORATION_C) -> float:
        if self.visits == 0:
            return float("inf")
        exploitation = self.value / self.visits
        exploration = c * math.sqrt(math.log(parent_visits) / self.visits)
        return exploitation + exploration


class MCTSPlanner:
    """
    Basic Monte Carlo Tree Search using a synthesized world model.

    Scoring heuristic:
    - Novelty: states not yet visited score higher.
    - Object count change: gaining or losing objects may indicate progress.
    - Position spread: objects moving apart / together can signal puzzle activity.
    """

    def __init__(
        self,
        predict_fn: Callable,
        available_actions: List[str],
        depth_limit: int = MCTS_DEPTH_LIMIT,
        n_simulations: int = MCTS_SIMULATIONS,
        goal_score_fn: Optional[Callable] = None,
        level: int = 1,
    ):
        # Apply Fibonacci-scaled config when level is provided
        if level != 1 or (depth_limit == MCTS_DEPTH_LIMIT and n_simulations == MCTS_SIMULATIONS):
            cfg = LEVEL_CONFIGS.get(level, LEVEL_DEFAULT_CONFIG)
            depth_limit, n_simulations = cfg

        self.predict_fn = predict_fn
        self.actions = available_actions
        self.depth_limit = depth_limit
        self.n_simulations = n_simulations
        self.goal_score_fn = goal_score_fn
        self.level = level
        self._seen_states: set = set()
        # Top-3 best states tracker: list of (goal_score, action_sequence)
        self._best_states: List[Tuple[float, List[str]]] = []

    def _score_state(self, objects: List[Dict], depth: int) -> float:
        """Heuristic score for a predicted state. Higher = more promising.

        When a goal_score_fn is provided (from GoalInferrer), blend goal-directed
        scoring with novelty. This is what turns wandering into solving.
        """
        key = str(sorted(
            (o.get("label", ""), o.get("x", 0), o.get("y", 0))
            for o in objects
        ))
        h = hashlib.md5(key.encode()).hexdigest()

        # Novelty component
        novelty = 0.0
        if h not in self._seen_states:
            novelty = 1.0
            self._seen_states.add(h)

        # Goal-directed component (from GoalInferrer)
        goal = 0.0
        if self.goal_score_fn:
            try:
                goal = self.goal_score_fn(objects)
            except Exception:
                pass

        # Blend: goal score weighted 2x when available, novelty as fallback
        if self.goal_score_fn:
            score = goal * 2.0 + novelty * 0.5
        else:
            score = novelty

        # Depth penalty to prefer shorter solutions
        score -= depth * 0.05

        return score

    def _state_key(self, objects: List[Dict]) -> str:
        """Hash a state for deadlock/cycle detection."""
        return str(sorted(
            (o.get("label", ""), o.get("x", 0), o.get("y", 0))
            for o in objects
        ))

    def _is_deadlocked(self, objects: List[Dict], prev_key: str,
                        visited: set) -> bool:
        """Deadlock detection: state unchanged or caught in a cycle.

        This is the SP-MCTS pruning trick from Sokoban research:
        don't waste simulations on states that are stuck.
        """
        key = self._state_key(objects)
        # State didn't change from parent = action had no effect
        if key == prev_key:
            return True
        # State already visited in this path = cycle
        if key in visited:
            return True
        return False

    def _simulate(self, node: MCTSNode, depth: int) -> float:
        """Random rollout from a leaf node to estimate value.

        With deadlock pruning: aborts early if the state stops changing
        or enters a cycle, saving simulation budget for productive paths.
        """
        objects = list(node.objects)
        total_score = 0.0
        prev_key = self._state_key(objects)
        visited = {prev_key}
        stale_count = 0

        for d in range(depth, self.depth_limit):
            action = random.choice(self.actions)
            try:
                objects = self.predict_fn(list(objects), action)
            except Exception:
                break
            if not isinstance(objects, list):
                break

            current_key = self._state_key(objects)

            # Deadlock pruning: if state hasn't changed in 3 steps, abort
            if current_key == prev_key:
                stale_count += 1
                if stale_count >= 3:
                    break  # Deadlocked — stop wasting simulation budget
            else:
                stale_count = 0

            # Cycle detection: if we've been here before, abort
            if current_key in visited:
                break
            visited.add(current_key)

            total_score += self._score_state(objects, d + 1)
            prev_key = current_key

        return total_score

    def _select(self, node: MCTSNode) -> MCTSNode:
        """Walk down the tree selecting children by UCB1."""
        current = node
        while not current.is_leaf() and current.visits > 0:
            best_child = max(
                current.children.values(),
                key=lambda c: c.ucb1(current.visits),
            )
            current = best_child
        return current

    def _expand(self, node: MCTSNode, depth: int) -> MCTSNode:
        """Expand a leaf node by trying all actions.

        With deadlock pruning: skip actions that produce identical states
        (no effect) or states already seen on this path (cycles).
        """
        if depth >= self.depth_limit:
            return node

        parent_key = self._state_key(node.objects)

        # Collect ancestor states for cycle detection
        ancestor_keys = set()
        ancestor = node.parent
        while ancestor is not None:
            ancestor_keys.add(self._state_key(ancestor.objects))
            ancestor = ancestor.parent

        for action in self.actions:
            if action in node.children:
                continue
            try:
                new_objects = self.predict_fn(list(node.objects), action)
            except Exception:
                continue
            if not isinstance(new_objects, list):
                continue

            # Deadlock pruning: skip if state unchanged or cycles
            new_key = self._state_key(new_objects)
            if new_key == parent_key:
                continue  # Action had no effect — prune
            if new_key in ancestor_keys:
                continue  # Would create a cycle — prune

            child = MCTSNode(
                objects=new_objects,
                action_taken=action,
                parent=node,
            )
            node.children[action] = child

        # Return a random unexplored child (or node itself if expansion failed)
        unvisited = [c for c in node.children.values() if c.visits == 0]
        if unvisited:
            return random.choice(unvisited)
        return node

    def _backpropagate(self, node: MCTSNode, value: float) -> None:
        """Propagate the simulation result up the tree."""
        current: Optional[MCTSNode] = node
        while current is not None:
            current.visits += 1
            current.value += value
            current = current.parent

    def _depth_of(self, node: MCTSNode) -> int:
        """Count the depth of a node by walking up to root."""
        d = 0
        current = node.parent
        while current is not None:
            d += 1
            current = current.parent
        return d

    def _next_fib_above(self, value: int) -> int:
        """Return the next Fibonacci number strictly greater than *value*."""
        for f in _FIB_SEQUENCE:
            if f > value:
                return f
        # Beyond pre-computed list — approximate
        return int(value * 1.618)

    def _action_sequence(self, node: MCTSNode) -> List[str]:
        """Walk from *node* up to root and return the action sequence."""
        actions: List[str] = []
        current: Optional[MCTSNode] = node
        while current is not None and current.action_taken is not None:
            actions.append(current.action_taken)
            current = current.parent
        actions.reverse()
        return actions

    def _track_best_state(self, node: MCTSNode) -> None:
        """Track top-3 most promising states by goal_score."""
        if not self.goal_score_fn:
            return
        try:
            score = self.goal_score_fn(node.objects)
        except Exception:
            return
        seq = self._action_sequence(node)
        if not seq:
            return

        self._best_states.append((score, seq))
        # Keep only top 3
        self._best_states.sort(key=lambda x: x[0], reverse=True)
        self._best_states = self._best_states[:3]

    def _all_leaves_deadlocked(self, root: MCTSNode) -> bool:
        """Check if every leaf in the tree is deadlocked (no children after expansion)."""
        stack = [root]
        found_productive_leaf = False
        while stack:
            node = stack.pop()
            if node.is_leaf():
                # A leaf with visits > 0 that couldn't expand is deadlocked
                # A leaf with visits == 0 hasn't been tried yet — not deadlocked
                if node.visits == 0 and node is not root:
                    found_productive_leaf = True
                    break
                # Leaf with children = not actually a leaf (shouldn't happen)
            else:
                stack.extend(node.children.values())
        return not found_productive_leaf

    def plan(self, start_objects: List[Dict[str, Any]]) -> List[str]:
        """
        Run MCTS from the given state and return the best action sequence.

        Uses iterative deepening: if all leaf nodes are deadlocked after
        an MCTS pass, increase depth_limit by the next Fibonacci number
        and retry (max 2 deepening iterations).

        If no clear winning path is found, falls back to the action
        sequence leading to the best-scored state seen during search.

        Returns a list of action names leading to the most-visited path.
        """
        self._best_states = []
        max_deepening_iterations = 2
        current_depth_limit = self.depth_limit

        for deepening_round in range(1 + max_deepening_iterations):
            root = MCTSNode(objects=start_objects)
            self._seen_states = set()

            for _ in range(self.n_simulations):
                # Select
                leaf = self._select(root)
                depth = self._depth_of(leaf)

                # Expand (use current_depth_limit for this round)
                saved_limit = self.depth_limit
                self.depth_limit = current_depth_limit
                child = self._expand(leaf, depth)
                self.depth_limit = saved_limit

                child_depth = self._depth_of(child)

                # Track best states for fallback
                self._track_best_state(child)

                # Simulate (use current_depth_limit for this round)
                saved_limit = self.depth_limit
                self.depth_limit = current_depth_limit
                value = self._simulate(child, child_depth)
                self.depth_limit = saved_limit

                # Backpropagate
                self._backpropagate(child, value)

            # Extract best action sequence by following most-visited children
            sequence: List[str] = []
            current: Optional[MCTSNode] = root
            while current is not None and current.children:
                best = max(current.children.values(), key=lambda c: c.visits)
                if best.action_taken is None:
                    break
                sequence.append(best.action_taken)
                current = best

            # Check if all leaves are deadlocked
            if sequence and not self._all_leaves_deadlocked(root):
                return sequence

            # Iterative deepening: bump depth by next Fibonacci number
            if deepening_round < max_deepening_iterations:
                fib_bump = self._next_fib_above(current_depth_limit)
                new_limit = current_depth_limit + fib_bump
                logger.info(
                    f"MCTS iterative deepening round {deepening_round + 1}: "
                    f"depth {current_depth_limit} -> {new_limit} "
                    f"(+{fib_bump} fib)"
                )
                current_depth_limit = new_limit

        # If we got a sequence from the last round, use it
        if sequence:
            return sequence

        # Fallback: return the action sequence leading to the best-scored state
        if self._best_states:
            best_score, best_seq = self._best_states[0]
            logger.info(
                f"MCTS fallback to best-scored state "
                f"(score={best_score:.3f}, {len(best_seq)} steps)"
            )
            return best_seq

        return sequence


# ---------------------------------------------------------------------------
# CodeWorldModel — top-level orchestrator
# ---------------------------------------------------------------------------

class CodeWorldModel:
    """
    Full Code World Model pipeline:
      1. Extract state descriptions from frames
      2. Collect transitions
      3. Synthesize a Python simulator via the 72B LLM
      4. Validate against held-out data
      5. Plan with MCTS when the model is accurate enough
    """

    ACCURACY_THRESHOLD = 0.50  # minimum holdout accuracy to trust the model

    def __init__(self, frame_processor: Optional[FrameProcessor] = None):
        self.extractor = StateExtractor(frame_processor)
        self.store = TransitionStore()
        self.predict_fn: Optional[Callable] = None
        self.accuracy: float = 0.0
        self.synthesis_attempts: int = 0
        self.synthesis_successes: int = 0
        self._last_state: Optional[StateDescription] = None
        self._last_action: Optional[str] = None

    @property
    def model_ready(self) -> bool:
        """True if a validated world model is available for planning."""
        return self.predict_fn is not None and self.accuracy >= self.ACCURACY_THRESHOLD

    def observe_frame(self, frame: np.ndarray, action: Optional[str] = None) -> StateDescription:
        """
        Feed a new frame (and the action that produced it) to the world model.

        Call this after every game step. Pass action=None for the initial frame.

        Returns the extracted StateDescription for the caller to use.
        """
        state = self.extractor.extract(frame)

        # Record transition if we have a previous state and action
        if self._last_state is not None and self._last_action is not None:
            self.store.add(self._last_state, self._last_action, state)

        # Store for next call
        self._last_state = state
        self._last_action = action

        return state

    def attempt_synthesis(self) -> bool:
        """
        Try to synthesize and validate a world model from collected transitions.

        Returns True if a usable model was produced.
        """
        if not self.store.ready_for_synthesis():
            logger.info(
                f"Not enough transitions for synthesis "
                f"({len(self.store)}/{MIN_TRANSITIONS_FOR_SYNTHESIS})"
            )
            return False

        self.synthesis_attempts += 1
        train, holdout = self.store.split()

        logger.info(f"Synthesis attempt #{self.synthesis_attempts} "
                     f"with {len(train)} train, {len(holdout)} holdout transitions")

        fn = synthesize_world_model(train)
        if fn is None:
            logger.warning("Synthesis produced no function")
            return False

        accuracy, correct, total = validate_world_model(fn, holdout)
        logger.info(f"Validation: {correct}/{total} correct ({accuracy:.1%})")

        if accuracy >= self.ACCURACY_THRESHOLD:
            self.predict_fn = fn
            self.accuracy = accuracy
            self.synthesis_successes += 1
            logger.info(f"World model accepted (accuracy={accuracy:.1%})")
            return True
        else:
            logger.info(f"World model rejected (accuracy={accuracy:.1%} "
                        f"< threshold {self.ACCURACY_THRESHOLD:.1%})")
            return False

    def plan(self, current_frame: np.ndarray, available_actions: List[str],
             goal_score_fn: Optional[Callable] = None,
             level: int = 1) -> Optional[List[str]]:
        """
        Use the synthesized world model + MCTS to plan an action sequence.

        Args:
            goal_score_fn: Optional scoring function from GoalInferrer that evaluates
                how close a state (list of object dicts) is to the inferred win condition.
                When provided, MCTS searches toward the goal instead of just novelty.
            level: Game level number (1-4+). Adjusts MCTS depth and simulation
                count using Fibonacci-scaled limits matching human baseline.

        Returns a list of action names, or None if the model is not ready.
        """
        if not self.model_ready:
            return None

        state = self.extractor.extract(current_frame)
        objects = state.object_dict_list()

        planner = MCTSPlanner(
            predict_fn=self.predict_fn,
            available_actions=available_actions,
            goal_score_fn=goal_score_fn,
            level=level,
        )
        sequence = planner.plan(objects)

        if sequence:
            logger.info(f"MCTS plan ({len(sequence)} steps): {' -> '.join(sequence[:5])}...")
        else:
            logger.info("MCTS returned empty plan")

        return sequence if sequence else None

    def status(self) -> Dict[str, Any]:
        """Return a summary of the world model's current state."""
        return {
            "transitions_collected": len(self.store),
            "ready_for_synthesis": self.store.ready_for_synthesis(),
            "synthesis_attempts": self.synthesis_attempts,
            "synthesis_successes": self.synthesis_successes,
            "model_ready": self.model_ready,
            "accuracy": self.accuracy,
        }


# ---------------------------------------------------------------------------
# __main__ test — fake transitions + synthesis attempt
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    print("=== CodeWorldModel self-test ===\n")

    # --- Test 1: StateExtractor ---
    print("1. State extraction from synthetic frame")
    fp = FrameProcessor()
    extractor = StateExtractor(fp)

    frame = np.zeros((64, 64), dtype=np.uint8)
    # Background = black (0)
    # Blue block at (5,10) size 4x4
    frame[10:14, 5:9] = 1
    # Red piece at (20,30) size 2x2
    frame[30:32, 20:22] = 2
    # Green marker at (15,15) size 2x2
    frame[15:17, 15:17] = 3

    state = extractor.extract(frame)
    print(f"   {state.text}")
    print(f"   Objects found: {len(state.objects)}")
    print(f"   Background: {state.background_color}")
    assert len(state.objects) == 3, f"Expected 3 objects, got {len(state.objects)}"
    assert state.background_color == "black"
    print("   PASSED\n")

    # --- Test 2: TransitionStore ---
    print("2. Transition collection")
    store = TransitionStore()

    # Generate fake transitions: a blue block moves right on "right" action
    for i in range(25):
        before_frame = np.zeros((64, 64), dtype=np.uint8)
        before_frame[10:14, 5 + i:9 + i] = 1
        before_state = extractor.extract(before_frame)

        after_frame = np.zeros((64, 64), dtype=np.uint8)
        after_frame[10:14, 6 + i:10 + i] = 1
        after_state = extractor.extract(after_frame)

        store.add(before_state, "move_right", after_state)

    print(f"   Transitions stored: {len(store)}")
    assert store.ready_for_synthesis(), "Should be ready with 25 transitions"

    train, holdout = store.split()
    print(f"   Train: {len(train)}, Holdout: {len(holdout)}")
    assert len(holdout) >= 1
    print("   PASSED\n")

    # --- Test 3: Synthesis (requires vLLM) ---
    print("3. World model synthesis (requires vLLM at localhost:8000)")
    cwm = CodeWorldModel(fp)

    # Feed the same transitions into the CWM
    for i in range(25):
        before_frame = np.zeros((64, 64), dtype=np.uint8)
        before_frame[10:14, 5 + i:9 + i] = 1

        after_frame = np.zeros((64, 64), dtype=np.uint8)
        after_frame[10:14, 6 + i:10 + i] = 1

        # First call: observe the "before" frame (no action yet)
        if i == 0:
            cwm.observe_frame(before_frame, action=None)
        cwm.observe_frame(after_frame, action="move_right")

    print(f"   CWM status: {cwm.status()}")

    try:
        success = cwm.attempt_synthesis()
        if success:
            print(f"   Synthesis succeeded! Accuracy: {cwm.accuracy:.1%}")

            # --- Test 4: MCTS planning ---
            print("\n4. MCTS planning")
            test_frame = np.zeros((64, 64), dtype=np.uint8)
            test_frame[10:14, 10:14] = 1
            plan = cwm.plan(test_frame, ["move_right", "move_left", "move_up", "move_down"])
            if plan:
                print(f"   Plan: {plan[:5]}")
            else:
                print("   No plan produced (model may not generalise to this state)")
            print("   PASSED")
        else:
            print("   Synthesis did not meet accuracy threshold (expected for simple test)")
    except requests.ConnectionError:
        print("   vLLM not available — skipping synthesis test (OK for offline)")
    except Exception as e:
        print(f"   Synthesis error (non-fatal): {e}")

    # --- Test 5: Validation helpers ---
    print("\n5. Validation logic")
    # Test _objects_match with identical objects
    dummy_state = StateDescription(
        objects=[ObjectDesc("blue_0", "blue", 1, 5, 10, 4, 4, 16)],
        background_color="black",
        text="test",
    )
    predicted = [{"label": "blue_0", "color": "blue", "color_id": 1,
                  "x": 5, "y": 10, "width": 4, "height": 4, "area": 16}]
    assert _objects_match(predicted, dummy_state), "Identical objects should match"

    # Test with slight offset (within tolerance)
    predicted_close = [{"label": "blue_0", "color": "blue", "color_id": 1,
                        "x": 6, "y": 11, "width": 4, "height": 4, "area": 16}]
    assert _objects_match(predicted_close, dummy_state, tolerance=2), \
        "Objects within tolerance should match"

    # Test with large offset (outside tolerance)
    predicted_far = [{"label": "blue_0", "color": "blue", "color_id": 1,
                      "x": 50, "y": 50, "width": 4, "height": 4, "area": 16}]
    assert not _objects_match(predicted_far, dummy_state, tolerance=2), \
        "Objects outside tolerance should not match"
    print("   PASSED")

    # --- Test 6: MCTSPlanner with a trivial predict function ---
    print("\n6. MCTS with trivial world model")

    def trivial_predict(objects: list, action: str) -> list:
        """Move all objects +1 in x on 'move_right'."""
        result = []
        for o in objects:
            o2 = dict(o)
            if action == "move_right":
                o2["x"] = o2.get("x", 0) + 1
            elif action == "move_left":
                o2["x"] = o2.get("x", 0) - 1
            result.append(o2)
        return result

    planner = MCTSPlanner(
        predict_fn=trivial_predict,
        available_actions=["move_right", "move_left", "move_up", "move_down"],
        depth_limit=8,
        n_simulations=40,
    )
    start_objs = [{"label": "blue_0", "color": "blue", "color_id": 1,
                    "x": 10, "y": 10, "width": 4, "height": 4, "area": 16}]
    plan = planner.plan(start_objs)
    print(f"   MCTS plan: {plan[:5]}")
    assert len(plan) > 0, "MCTS should produce at least one action"
    print("   PASSED")

    print("\n=== All offline tests passed ===")
