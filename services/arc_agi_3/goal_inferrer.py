"""
Goal Inference Module for ARC-AGI-3.

Observes state transitions, uses the 72B LLM to hypothesize win conditions,
and provides a goal score function for MCTS planning.

Called from ganuda_agent.py when the graph explorer stalls. The LLM is invoked
ONCE per inference trigger, not every frame.

Dependencies: numpy, requests (both in venv).
"""

from __future__ import annotations

import json
import logging
import math
import re
import textwrap
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import requests

from world_model import (
    VLLM_URL,
    VLLM_MODEL,
    ObjectDesc,
    StateDescription,
    Transition,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

GOAL_INFERENCE_TEMPERATURE = 0.4
GOAL_INFERENCE_MAX_TOKENS = 2048
GOAL_INFERENCE_TIMEOUT = 90.0

# Minimum transitions before we attempt goal inference
MIN_TRANSITIONS_FOR_INFERENCE = 5


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class GoalHypothesis:
    """A single hypothesis about the game's win condition."""
    description: str        # human-readable description
    category: str           # one of: match, sort, clear, reach, align, group, transform, unknown
    confidence: float       # 0-1, LLM's self-assessed confidence
    scoring_hint: str       # brief instruction for how to score toward this goal

    def __repr__(self) -> str:
        return f"GoalHypothesis({self.category}, conf={self.confidence:.2f}, {self.description[:60]})"


@dataclass
class TransitionPattern:
    """Summary of observed patterns across state transitions."""
    objects_that_move: List[str]           # labels of objects that change position
    objects_that_appear: List[str]         # labels that appear in after but not before
    objects_that_disappear: List[str]      # labels that appear in before but not after
    color_changes: List[Tuple[str, str]]   # (from_color, to_color) pairs observed
    spatial_trend: str                     # converging, diverging, aligning, static, mixed
    consistent_actions: Dict[str, str]     # action -> typical effect description
    object_count_trend: str               # increasing, decreasing, stable


# ---------------------------------------------------------------------------
# 1. Transition Pattern Analysis
# ---------------------------------------------------------------------------

def analyze_transitions(transitions: List[Transition]) -> TransitionPattern:
    """
    Analyze a list of state transitions to identify recurring patterns.

    Examines which objects move, appear, disappear, change color, and
    whether there are spatial trends (convergence, divergence, alignment).
    """
    movers = set()
    appeared = set()
    disappeared = set()
    color_changes = []
    action_effects: Dict[str, List[str]] = {}
    count_deltas = []

    # Track centroid movement for spatial trend
    centroid_distances = []  # per-transition, avg pairwise distance change

    for t in transitions:
        before_labels = {o.label: o for o in t.before.objects}
        after_labels = {o.label: o for o in t.after.objects}

        before_set = set(before_labels.keys())
        after_set = set(after_labels.keys())

        # Appeared / disappeared
        for label in after_set - before_set:
            appeared.add(label)
        for label in before_set - after_set:
            disappeared.add(label)

        # Movers and color changes (objects present in both)
        common = before_set & after_set
        effects = []
        for label in common:
            ob = before_labels[label]
            oa = after_labels[label]
            if ob.x != oa.x or ob.y != oa.y:
                movers.add(label)
                dx = oa.x - ob.x
                dy = oa.y - ob.y
                effects.append(f"{label} moved ({dx:+d},{dy:+d})")
            if ob.color != oa.color:
                color_changes.append((ob.color, oa.color))
                effects.append(f"{label} color {ob.color}->{oa.color}")

        if t.action not in action_effects:
            action_effects[t.action] = []
        action_effects[t.action].extend(effects)

        # Object count trend
        count_deltas.append(len(t.after.objects) - len(t.before.objects))

        # Spatial trend: average pairwise distance among objects
        before_centroids = [(o.x + o.width / 2, o.y + o.height / 2)
                           for o in t.before.objects]
        after_centroids = [(o.x + o.width / 2, o.y + o.height / 2)
                          for o in t.after.objects]

        if len(before_centroids) >= 2 and len(after_centroids) >= 2:
            before_spread = _avg_pairwise_dist(before_centroids)
            after_spread = _avg_pairwise_dist(after_centroids)
            if before_spread > 0:
                centroid_distances.append(after_spread - before_spread)

    # Determine spatial trend
    if centroid_distances:
        avg_delta = sum(centroid_distances) / len(centroid_distances)
        if avg_delta < -1.0:
            spatial_trend = "converging"
        elif avg_delta > 1.0:
            spatial_trend = "diverging"
        else:
            spatial_trend = "static"
    else:
        spatial_trend = "static"

    # Summarize action effects
    consistent_actions = {}
    for action, effects_list in action_effects.items():
        if effects_list:
            # Take the most common effect
            from collections import Counter
            counter = Counter(effects_list)
            most_common = counter.most_common(1)[0][0]
            consistent_actions[action] = most_common
        else:
            consistent_actions[action] = "no visible effect"

    # Object count trend
    if count_deltas:
        avg_count = sum(count_deltas) / len(count_deltas)
        if avg_count < -0.3:
            count_trend = "decreasing"
        elif avg_count > 0.3:
            count_trend = "increasing"
        else:
            count_trend = "stable"
    else:
        count_trend = "stable"

    # Deduplicate color changes
    unique_color_changes = list(set(color_changes))

    return TransitionPattern(
        objects_that_move=sorted(movers),
        objects_that_appear=sorted(appeared),
        objects_that_disappear=sorted(disappeared),
        color_changes=unique_color_changes,
        spatial_trend=spatial_trend,
        consistent_actions=consistent_actions,
        object_count_trend=count_trend,
    )


def _avg_pairwise_dist(points: List[Tuple[float, float]]) -> float:
    """Average Euclidean distance between all pairs of points."""
    n = len(points)
    if n < 2:
        return 0.0
    total = 0.0
    count = 0
    for i in range(n):
        for j in range(i + 1, n):
            dx = points[i][0] - points[j][0]
            dy = points[i][1] - points[j][1]
            total += math.sqrt(dx * dx + dy * dy)
            count += 1
    return total / count if count > 0 else 0.0


# ---------------------------------------------------------------------------
# 2. Goal Hypothesis Generation (LLM-based)
# ---------------------------------------------------------------------------

GOAL_INFERENCE_SYSTEM_PROMPT = textwrap.dedent("""\
    You are a puzzle analyst. You observe state transitions in a grid-based
    puzzle game and infer what the player must do to win.

    You will receive:
    - A summary of observed transition patterns
    - Object descriptions (colors, positions, sizes)
    - What changes and what stays the same across actions

    Respond with EXACTLY a JSON array of 3-5 hypothesis objects. Each object has:
    {
        "description": "one sentence describing the hypothesized win condition",
        "category": "one of: match, sort, clear, reach, align, group, transform, unknown",
        "confidence": 0.0 to 1.0,
        "scoring_hint": "brief instruction for scoring progress toward this goal"
    }

    Categories:
    - match: same-colored objects must be adjacent or paired
    - sort: objects must be arranged in a specific order
    - clear: objects must be removed from the board
    - reach: an object must reach a target position
    - align: objects must form a line or pattern
    - group: objects must be gathered into clusters by property
    - transform: objects must change color/shape to match a target
    - unknown: cannot determine the goal

    Return ONLY the JSON array, no other text.
""")


def _build_goal_inference_prompt(
    pattern: TransitionPattern,
    recent_states: List[StateDescription],
) -> str:
    """Build the user prompt for goal hypothesis generation."""
    lines = []

    lines.append("== Transition Pattern Summary ==")
    if pattern.objects_that_move:
        lines.append(f"Objects that move: {', '.join(pattern.objects_that_move[:10])}")
    if pattern.objects_that_appear:
        lines.append(f"Objects that appear: {', '.join(pattern.objects_that_appear[:10])}")
    if pattern.objects_that_disappear:
        lines.append(f"Objects that disappear: {', '.join(pattern.objects_that_disappear[:10])}")
    if pattern.color_changes:
        cc = [f"{a}->{b}" for a, b in pattern.color_changes[:5]]
        lines.append(f"Color changes observed: {', '.join(cc)}")
    lines.append(f"Spatial trend: {pattern.spatial_trend}")
    lines.append(f"Object count trend: {pattern.object_count_trend}")

    if pattern.consistent_actions:
        lines.append("\n== Action Effects ==")
        for action, effect in list(pattern.consistent_actions.items())[:8]:
            lines.append(f"  {action}: {effect}")

    # Include the most recent state descriptions for context
    if recent_states:
        lines.append("\n== Recent State Snapshots ==")
        for i, state in enumerate(recent_states[-3:]):
            lines.append(f"State {i + 1}: {state.text}")

    lines.append("\nBased on these observations, what are 3-5 hypotheses about the win condition?")
    lines.append("IMPORTANT: Many puzzle games require SEQUENTIAL sub-goals (e.g., 'first interact")
    lines.append("with object A to change state, THEN move to object B'). If you see evidence of")
    lines.append("multi-step mechanics, include the sub-goal ORDER in your hypothesis description.")
    lines.append("Actions can have non-movement effects (pressing toward an object may trigger it")
    lines.append("even without reaching it).")
    return "\n".join(lines)


def _call_vllm_for_goals(system: str, user: str) -> Optional[str]:
    """Call the local vLLM endpoint for goal inference."""
    payload = {
        "model": VLLM_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": GOAL_INFERENCE_TEMPERATURE,
        "max_tokens": GOAL_INFERENCE_MAX_TOKENS,
    }
    try:
        resp = requests.post(VLLM_URL, json=payload, timeout=GOAL_INFERENCE_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        logger.warning(f"Goal inference LLM call failed: {e}")
        return None


def _parse_hypotheses(raw: str) -> List[GoalHypothesis]:
    """Parse the LLM's JSON response into GoalHypothesis objects."""
    # Try to extract JSON array from the response
    # The LLM might wrap it in markdown code blocks
    text = raw.strip()

    # Strip markdown code fences if present
    json_match = re.search(r"```(?:json)?\s*\n?(.*?)```", text, re.DOTALL)
    if json_match:
        text = json_match.group(1).strip()

    # If the text doesn't start with [, try to find the array
    if not text.startswith("["):
        bracket_start = text.find("[")
        if bracket_start >= 0:
            bracket_end = text.rfind("]")
            if bracket_end > bracket_start:
                text = text[bracket_start:bracket_end + 1]

    try:
        items = json.loads(text)
    except json.JSONDecodeError:
        logger.warning(f"Could not parse goal hypotheses JSON: {text[:200]}")
        return []

    if not isinstance(items, list):
        return []

    valid_categories = {"match", "sort", "clear", "reach", "align", "group", "transform", "unknown"}
    hypotheses = []

    for item in items:
        if not isinstance(item, dict):
            continue
        cat = item.get("category", "unknown")
        if cat not in valid_categories:
            cat = "unknown"
        conf = item.get("confidence", 0.5)
        conf = max(0.0, min(1.0, float(conf)))

        hypotheses.append(GoalHypothesis(
            description=str(item.get("description", "unknown goal")),
            category=cat,
            confidence=conf,
            scoring_hint=str(item.get("scoring_hint", "")),
        ))

    return hypotheses


def generate_hypotheses(
    transitions: List[Transition],
    recent_states: List[StateDescription],
) -> List[GoalHypothesis]:
    """
    Use the 72B LLM to generate hypotheses about the game's win condition.

    This is called ONCE when goal inference is triggered, not every frame.
    Returns a list of GoalHypothesis objects sorted by confidence (highest first).
    """
    if len(transitions) < MIN_TRANSITIONS_FOR_INFERENCE:
        logger.info(f"Not enough transitions for goal inference "
                    f"({len(transitions)}/{MIN_TRANSITIONS_FOR_INFERENCE})")
        return []

    pattern = analyze_transitions(transitions)
    prompt = _build_goal_inference_prompt(pattern, recent_states)

    raw = _call_vllm_for_goals(GOAL_INFERENCE_SYSTEM_PROMPT, prompt)
    if raw is None:
        return _fallback_hypotheses(pattern)

    hypotheses = _parse_hypotheses(raw)
    if not hypotheses:
        logger.warning("LLM returned no parseable hypotheses, using fallback")
        return _fallback_hypotheses(pattern)

    # Sort by confidence descending
    hypotheses.sort(key=lambda h: h.confidence, reverse=True)
    return hypotheses


def _fallback_hypotheses(pattern: TransitionPattern) -> List[GoalHypothesis]:
    """
    Generate heuristic hypotheses when the LLM is unavailable.
    Uses the transition pattern analysis to make educated guesses.
    """
    hypotheses = []

    if pattern.objects_that_disappear:
        hypotheses.append(GoalHypothesis(
            description="Clear all movable objects from the board",
            category="clear",
            confidence=0.4,
            scoring_hint="Score by inverse of remaining non-background objects",
        ))

    if pattern.spatial_trend == "converging":
        hypotheses.append(GoalHypothesis(
            description="Group objects together or move them to a central location",
            category="group",
            confidence=0.4,
            scoring_hint="Score by inverse of average pairwise distance between objects",
        ))

    if pattern.color_changes:
        hypotheses.append(GoalHypothesis(
            description="Transform object colors to match a target pattern",
            category="transform",
            confidence=0.3,
            scoring_hint="Score by how many objects share the same color",
        ))

    if pattern.objects_that_move and not pattern.objects_that_disappear:
        hypotheses.append(GoalHypothesis(
            description="Move objects to target positions or align them",
            category="reach",
            confidence=0.3,
            scoring_hint="Score by how different the state is from the starting state",
        ))

    # Always include a novelty fallback
    hypotheses.append(GoalHypothesis(
        description="Reach a novel state that differs maximally from the start",
        category="unknown",
        confidence=0.1,
        scoring_hint="Score by state novelty compared to initial state",
    ))

    hypotheses.sort(key=lambda h: h.confidence, reverse=True)
    return hypotheses


# ---------------------------------------------------------------------------
# 3. Goal Score Function
# ---------------------------------------------------------------------------

class GoalScorer:
    """
    Scores how close a state appears to winning based on the current
    best hypothesis. Returns a float 0-1 for use as an MCTS value function.
    """

    def __init__(self):
        self.hypotheses: List[GoalHypothesis] = []
        self.initial_state: Optional[StateDescription] = None
        self._scoring_fn: Optional[callable] = None

    def update_hypotheses(
        self,
        hypotheses: List[GoalHypothesis],
        initial_state: Optional[StateDescription] = None,
    ) -> None:
        """Set the current hypotheses. The highest-confidence one drives scoring."""
        self.hypotheses = hypotheses
        if initial_state is not None:
            self.initial_state = initial_state
        self._scoring_fn = self._build_scoring_fn()

    def score(self, state: StateDescription) -> float:
        """
        Score a state 0-1 based on how close it appears to winning.

        If no hypotheses are set, falls back to novelty scoring.
        """
        if self._scoring_fn is not None:
            return self._scoring_fn(state)
        return self._score_novelty(state)

    def _build_scoring_fn(self) -> callable:
        """Build the scoring function based on the best hypothesis category."""
        if not self.hypotheses:
            return self._score_novelty

        best = self.hypotheses[0]
        category = best.category

        scorers = {
            "match": self._score_match,
            "sort": self._score_sort,
            "clear": self._score_clear,
            "reach": self._score_reach,
            "align": self._score_align,
            "group": self._score_group,
            "transform": self._score_transform,
            "unknown": self._score_novelty,
        }

        fn = scorers.get(category, self._score_novelty)

        # Blend the category-specific score with novelty using confidence
        # High confidence -> rely on category scorer
        # Low confidence -> lean toward novelty
        confidence = best.confidence

        def blended(state: StateDescription) -> float:
            cat_score = fn(state)
            nov_score = self._score_novelty(state)
            return confidence * cat_score + (1.0 - confidence) * nov_score

        return blended

    def _score_match(self, state: StateDescription) -> float:
        """Score by how many same-colored objects are adjacent."""
        objects = state.objects
        if len(objects) < 2:
            return 0.0

        adjacency_threshold = 3  # pixels
        matched_pairs = 0
        total_pairs = 0

        for i in range(len(objects)):
            for j in range(i + 1, len(objects)):
                oi, oj = objects[i], objects[j]
                if oi.color == oj.color:
                    total_pairs += 1
                    # Check adjacency: bounding boxes within threshold
                    dx = max(0, max(oi.x, oj.x) - min(oi.x + oi.width, oj.x + oj.width))
                    dy = max(0, max(oi.y, oj.y) - min(oi.y + oi.height, oj.y + oj.height))
                    dist = math.sqrt(dx * dx + dy * dy)
                    if dist <= adjacency_threshold:
                        matched_pairs += 1

        if total_pairs == 0:
            return 0.5  # no same-colored pairs to match
        return min(1.0, matched_pairs / total_pairs)

    def _score_sort(self, state: StateDescription) -> float:
        """Score by how sorted objects are (by x or y position, grouped by color)."""
        objects = state.objects
        if len(objects) < 2:
            return 1.0

        # Check if objects are sorted by x-position within color groups
        from itertools import groupby
        sorted_by_x = sorted(objects, key=lambda o: o.x)
        color_sequence = [o.color for o in sorted_by_x]

        # Count color-group transitions (fewer = more sorted)
        transitions = sum(1 for i in range(1, len(color_sequence))
                         if color_sequence[i] != color_sequence[i - 1])
        max_transitions = len(color_sequence) - 1
        if max_transitions == 0:
            return 1.0

        return 1.0 - (transitions / max_transitions)

    def _score_clear(self, state: StateDescription) -> float:
        """Score by inverse of remaining objects (fewer = closer to winning)."""
        n = len(state.objects)
        if self.initial_state is not None:
            initial_n = len(self.initial_state.objects)
            if initial_n == 0:
                return 1.0
            # Fraction of objects cleared
            return max(0.0, 1.0 - n / initial_n)
        # Without initial state, just penalize object count
        return 1.0 / (1.0 + n)

    def _score_reach(self, state: StateDescription) -> float:
        """Score by how different this state is from the starting state (proxy for progress)."""
        return self._score_novelty(state)

    def _score_align(self, state: StateDescription) -> float:
        """Score by how well objects form lines (horizontal or vertical)."""
        objects = state.objects
        if len(objects) < 2:
            return 1.0

        # Check horizontal alignment: how many objects share a y-center
        y_centers = [o.y + o.height / 2 for o in objects]
        x_centers = [o.x + o.width / 2 for o in objects]

        h_alignment = _alignment_score(y_centers)
        v_alignment = _alignment_score(x_centers)

        # Take the better alignment axis
        return max(h_alignment, v_alignment)

    def _score_group(self, state: StateDescription) -> float:
        """Score by how tightly same-colored objects cluster together."""
        objects = state.objects
        if len(objects) < 2:
            return 1.0

        # Group objects by color
        color_groups: Dict[str, List[ObjectDesc]] = {}
        for o in objects:
            color_groups.setdefault(o.color, []).append(o)

        if len(color_groups) <= 1:
            return 1.0  # all same color, trivially grouped

        # For each color group, compute the spread (avg pairwise distance)
        total_spread = 0.0
        n_groups = 0

        for color, group in color_groups.items():
            if len(group) < 2:
                continue
            centers = [(o.x + o.width / 2, o.y + o.height / 2) for o in group]
            spread = _avg_pairwise_dist(centers)
            total_spread += spread
            n_groups += 1

        if n_groups == 0:
            return 0.5

        avg_spread = total_spread / n_groups
        # Normalize: spread of 0 = perfect grouping (score 1.0)
        # spread of 64 (max possible in 64x64) = no grouping (score 0.0)
        return max(0.0, 1.0 - avg_spread / 64.0)

    def _score_transform(self, state: StateDescription) -> float:
        """Score by color uniformity (more same-colored objects = higher score)."""
        objects = state.objects
        if not objects:
            return 0.0

        # Count the most common color
        from collections import Counter
        colors = Counter(o.color for o in objects)
        most_common_count = colors.most_common(1)[0][1]
        return most_common_count / len(objects)

    def _score_novelty(self, state: StateDescription) -> float:
        """Score by how different this state is from the initial state."""
        if self.initial_state is None:
            return 0.5  # no baseline, neutral score

        initial_objs = {o.label: o for o in self.initial_state.objects}
        current_objs = {o.label: o for o in state.objects}

        if not initial_objs and not current_objs:
            return 0.0  # both empty, no progress

        # Count differences
        all_labels = set(initial_objs.keys()) | set(current_objs.keys())
        if not all_labels:
            return 0.0

        differences = 0
        for label in all_labels:
            if label not in initial_objs or label not in current_objs:
                differences += 1
                continue
            oi = initial_objs[label]
            oc = current_objs[label]
            if oi.x != oc.x or oi.y != oc.y:
                differences += 1
            elif oi.color != oc.color:
                differences += 1

        return min(1.0, differences / len(all_labels))


def _alignment_score(values: List[float], tolerance: float = 2.0) -> float:
    """
    Score how well a list of values cluster into lines.
    Groups values within tolerance, then returns fraction in the largest group.
    """
    if len(values) < 2:
        return 1.0

    sorted_vals = sorted(values)
    groups = []
    current_group = [sorted_vals[0]]

    for v in sorted_vals[1:]:
        if v - current_group[-1] <= tolerance:
            current_group.append(v)
        else:
            groups.append(len(current_group))
            current_group = [v]
    groups.append(len(current_group))

    return max(groups) / len(values)


# ---------------------------------------------------------------------------
# 4. GoalInferrer — top-level orchestrator
# ---------------------------------------------------------------------------

class GoalInferrer:
    """
    Top-level goal inference engine.

    Usage from ganuda_agent.py:
        inferrer = GoalInferrer()
        # Feed transitions as they happen:
        inferrer.observe(before_state, action, after_state)
        # When the explorer stalls, trigger inference:
        if stalled:
            inferrer.infer_goals()
        # Use the scorer in MCTS:
        score = inferrer.score_state(some_state)
    """

    def __init__(self):
        self.transitions: List[Transition] = []
        self.recent_states: List[StateDescription] = []
        self.scorer = GoalScorer()
        self._initial_state: Optional[StateDescription] = None
        self._inference_done = False

    @property
    def has_hypotheses(self) -> bool:
        return len(self.scorer.hypotheses) > 0

    @property
    def best_hypothesis(self) -> Optional[GoalHypothesis]:
        return self.scorer.hypotheses[0] if self.scorer.hypotheses else None

    def observe(
        self,
        before: StateDescription,
        action: str,
        after: StateDescription,
    ) -> None:
        """Record a state transition for later analysis."""
        self.transitions.append(Transition(before=before, action=action, after=after))
        self.recent_states.append(after)
        # Keep recent states bounded
        if len(self.recent_states) > 20:
            self.recent_states = self.recent_states[-20:]
        # Track initial state
        if self._initial_state is None:
            self._initial_state = before

    def infer_goals(self) -> List[GoalHypothesis]:
        """
        Trigger goal inference using the 72B LLM.

        Called once when the graph explorer stalls, not every frame.
        Returns the generated hypotheses and configures the scorer.
        """
        hypotheses = generate_hypotheses(self.transitions, self.recent_states)
        self.scorer.update_hypotheses(hypotheses, self._initial_state)
        self._inference_done = True

        if hypotheses:
            logger.info(f"Goal inference produced {len(hypotheses)} hypotheses. "
                       f"Best: {hypotheses[0]}")
        else:
            logger.warning("Goal inference produced no hypotheses")

        return hypotheses

    def score_state(self, state: StateDescription) -> float:
        """
        Score a state 0-1 for MCTS value estimation.

        If infer_goals() hasn't been called yet, returns 0.5 (neutral).
        """
        if not self._inference_done:
            return 0.5
        return self.scorer.score(state)

    def score_objects(self, objects: List[Dict[str, Any]]) -> float:
        """
        Score from a plain dict list (as used by MCTSPlanner).

        Converts dicts to a StateDescription, then scores.
        """
        obj_descs = []
        for o in objects:
            obj_descs.append(ObjectDesc(
                label=o.get("label", ""),
                color=o.get("color", ""),
                color_id=o.get("color_id", 0),
                x=o.get("x", 0),
                y=o.get("y", 0),
                width=o.get("width", 0),
                height=o.get("height", 0),
                area=o.get("area", 0),
            ))
        state = StateDescription(
            objects=obj_descs,
            background_color="black",
            text="",
        )
        return self.score_state(state)

    def status(self) -> Dict[str, Any]:
        """Return a summary of the goal inferrer's state."""
        return {
            "transitions_observed": len(self.transitions),
            "inference_done": self._inference_done,
            "num_hypotheses": len(self.scorer.hypotheses),
            "best_hypothesis": str(self.best_hypothesis) if self.best_hypothesis else None,
        }


# ---------------------------------------------------------------------------
# __main__ test — synthetic state descriptions
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    print("=== GoalInferrer self-test ===\n")

    # --- Test 1: TransitionPattern analysis ---
    print("1. Transition pattern analysis")

    def _make_state(objects_data: List[dict], bg: str = "black") -> StateDescription:
        objs = []
        for d in objects_data:
            objs.append(ObjectDesc(
                label=d["label"],
                color=d["color"],
                color_id=d.get("color_id", 0),
                x=d["x"], y=d["y"],
                width=d.get("width", 4), height=d.get("height", 4),
                area=d.get("area", 16),
            ))
        text = ", ".join(o.to_text() for o in objs) if objs else "empty"
        return StateDescription(objects=objs, background_color=bg, text=text)

    # Simulate: blue block moves right each step
    transitions = []
    for i in range(10):
        before = _make_state([
            {"label": "blue_0", "color": "blue", "color_id": 1, "x": 5 + i, "y": 10},
            {"label": "red_0", "color": "red", "color_id": 2, "x": 30, "y": 30},
        ])
        after = _make_state([
            {"label": "blue_0", "color": "blue", "color_id": 1, "x": 6 + i, "y": 10},
            {"label": "red_0", "color": "red", "color_id": 2, "x": 30, "y": 30},
        ])
        transitions.append(Transition(before=before, action="move_right", after=after))

    pattern = analyze_transitions(transitions)
    print(f"   Movers: {pattern.objects_that_move}")
    print(f"   Spatial trend: {pattern.spatial_trend}")
    print(f"   Count trend: {pattern.object_count_trend}")
    assert "blue_0" in pattern.objects_that_move, "blue_0 should be detected as moving"
    assert "red_0" not in pattern.objects_that_move, "red_0 should not move"
    print("   PASSED\n")

    # --- Test 2: Disappearing objects ---
    print("2. Object disappearance detection")
    transitions2 = []
    for i in range(6):
        n_objects = max(1, 5 - i)
        before_objs = [{"label": f"block_{j}", "color": "green", "color_id": 3,
                        "x": j * 10, "y": 20} for j in range(n_objects)]
        after_objs = [{"label": f"block_{j}", "color": "green", "color_id": 3,
                       "x": j * 10, "y": 20} for j in range(max(0, n_objects - 1))]
        before = _make_state(before_objs)
        after = _make_state(after_objs)
        transitions2.append(Transition(before=before, action="click", after=after))

    pattern2 = analyze_transitions(transitions2)
    print(f"   Disappeared: {pattern2.objects_that_disappear}")
    print(f"   Count trend: {pattern2.object_count_trend}")
    assert len(pattern2.objects_that_disappear) > 0, "Should detect disappearing objects"
    assert pattern2.object_count_trend == "decreasing", "Count should be decreasing"
    print("   PASSED\n")

    # --- Test 3: GoalScorer — match scoring ---
    print("3. Goal scoring — match hypothesis")
    scorer = GoalScorer()
    scorer.update_hypotheses([
        GoalHypothesis(
            description="Match same-colored objects by placing them adjacent",
            category="match",
            confidence=0.8,
            scoring_hint="adjacent same-color pairs",
        )
    ])

    # State with same-colored objects far apart (low score)
    far_state = _make_state([
        {"label": "blue_0", "color": "blue", "color_id": 1, "x": 0, "y": 0},
        {"label": "blue_1", "color": "blue", "color_id": 1, "x": 50, "y": 50},
    ])
    far_score = scorer.score(far_state)

    # State with same-colored objects adjacent (high score)
    near_state = _make_state([
        {"label": "blue_0", "color": "blue", "color_id": 1, "x": 10, "y": 10},
        {"label": "blue_1", "color": "blue", "color_id": 1, "x": 14, "y": 10},
    ])
    near_score = scorer.score(near_state)

    print(f"   Far apart score:  {far_score:.3f}")
    print(f"   Adjacent score:   {near_score:.3f}")
    assert near_score > far_score, "Adjacent objects should score higher for match goal"
    print("   PASSED\n")

    # --- Test 4: GoalScorer — clear scoring ---
    print("4. Goal scoring — clear hypothesis")
    initial = _make_state([
        {"label": f"block_{i}", "color": "red", "color_id": 2,
         "x": i * 8, "y": 20} for i in range(5)
    ])
    scorer2 = GoalScorer()
    scorer2.update_hypotheses([
        GoalHypothesis(
            description="Clear all blocks",
            category="clear",
            confidence=0.9,
            scoring_hint="fewer objects = better",
        )
    ], initial_state=initial)

    full_score = scorer2.score(initial)
    partial = _make_state([
        {"label": f"block_{i}", "color": "red", "color_id": 2,
         "x": i * 8, "y": 20} for i in range(2)
    ])
    partial_score = scorer2.score(partial)
    empty = _make_state([])
    empty_score = scorer2.score(empty)

    print(f"   Full board (5 objects): {full_score:.3f}")
    print(f"   Partial (2 objects):    {partial_score:.3f}")
    print(f"   Empty board:            {empty_score:.3f}")
    assert empty_score > partial_score > full_score, \
        "Fewer objects should score higher for clear goal"
    print("   PASSED\n")

    # --- Test 5: GoalScorer — group scoring ---
    print("5. Goal scoring — group hypothesis")
    scorer3 = GoalScorer()
    scorer3.update_hypotheses([
        GoalHypothesis(
            description="Group same-colored objects together",
            category="group",
            confidence=0.7,
            scoring_hint="minimize spread within color groups",
        )
    ])

    scattered = _make_state([
        {"label": "blue_0", "color": "blue", "color_id": 1, "x": 0, "y": 0},
        {"label": "blue_1", "color": "blue", "color_id": 1, "x": 60, "y": 60},
        {"label": "red_0", "color": "red", "color_id": 2, "x": 60, "y": 0},
        {"label": "red_1", "color": "red", "color_id": 2, "x": 0, "y": 60},
    ])
    scattered_score = scorer3.score(scattered)

    grouped = _make_state([
        {"label": "blue_0", "color": "blue", "color_id": 1, "x": 5, "y": 5},
        {"label": "blue_1", "color": "blue", "color_id": 1, "x": 9, "y": 5},
        {"label": "red_0", "color": "red", "color_id": 2, "x": 40, "y": 40},
        {"label": "red_1", "color": "red", "color_id": 2, "x": 44, "y": 40},
    ])
    grouped_score = scorer3.score(grouped)

    print(f"   Scattered score: {scattered_score:.3f}")
    print(f"   Grouped score:   {grouped_score:.3f}")
    assert grouped_score > scattered_score, "Grouped objects should score higher"
    print("   PASSED\n")

    # --- Test 6: GoalInferrer end-to-end (without LLM) ---
    print("6. GoalInferrer end-to-end (fallback hypotheses, no LLM)")
    inferrer = GoalInferrer()

    # Feed transitions where objects disappear
    for i in range(6):
        n_objects = max(1, 5 - i)
        before_objs = [{"label": f"block_{j}", "color": "green", "color_id": 3,
                        "x": j * 10, "y": 20} for j in range(n_objects)]
        after_objs = [{"label": f"block_{j}", "color": "green", "color_id": 3,
                       "x": j * 10, "y": 20} for j in range(max(0, n_objects - 1))]
        before = _make_state(before_objs)
        after = _make_state(after_objs)
        inferrer.observe(before, "click", after)

    # Infer goals (will use fallback since no LLM)
    hypotheses = inferrer.infer_goals()
    print(f"   Hypotheses generated: {len(hypotheses)}")
    for h in hypotheses:
        print(f"     {h}")
    assert len(hypotheses) > 0, "Should generate at least one hypothesis"
    assert inferrer.has_hypotheses

    # Score a state
    test_state = _make_state([
        {"label": "block_0", "color": "green", "color_id": 3, "x": 0, "y": 20}
    ])
    score = inferrer.score_state(test_state)
    print(f"   Score for 1-object state: {score:.3f}")
    assert 0.0 <= score <= 1.0, "Score must be in [0, 1]"
    print("   PASSED\n")

    # --- Test 7: score_objects (dict interface for MCTS) ---
    print("7. score_objects dict interface")
    obj_dicts = [{"label": "blue_0", "color": "blue", "color_id": 1,
                  "x": 10, "y": 10, "width": 4, "height": 4, "area": 16}]
    dict_score = inferrer.score_objects(obj_dicts)
    print(f"   Dict-based score: {dict_score:.3f}")
    assert 0.0 <= dict_score <= 1.0
    print("   PASSED\n")

    # --- Test 8: Status ---
    print("8. Status report")
    status = inferrer.status()
    print(f"   {status}")
    assert status["inference_done"] is True
    assert status["num_hypotheses"] > 0
    print("   PASSED")

    # --- Test 9: LLM goal generation (requires vLLM) ---
    print("\n9. LLM goal generation (requires vLLM at localhost:8000)")
    try:
        llm_hypotheses = generate_hypotheses(transitions, [transitions[-1].after])
        if llm_hypotheses:
            print(f"   LLM generated {len(llm_hypotheses)} hypotheses:")
            for h in llm_hypotheses:
                print(f"     {h}")
        else:
            print("   LLM returned no hypotheses (fallback was used)")
    except requests.ConnectionError:
        print("   vLLM not available -- skipping (OK for offline)")
    except Exception as e:
        print(f"   LLM test error (non-fatal): {e}")

    print("\n=== All offline tests passed ===")
