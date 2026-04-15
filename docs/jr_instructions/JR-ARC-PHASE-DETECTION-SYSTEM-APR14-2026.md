# Jr Instruction: ARC-AGI-3 Phase Detection System

**Task ID**: ARC-PHASE-DETECT-001
**Priority**: P1
**Date**: April 14, 2026
**Tag**: it_triad_jr
**Council Vote**: #33e1fe4ae927c482 (0.55, REVIEW REQUIRED — Raven STRATEGY CONCERN: prioritize this before multi-phase training)
**Depends On**: Existing ganuda_agent.py, game_strategy.py (Bonanno components)
**Contest Deadline**: M1 — June 30, 2026

---

## Context

The Council reviewed ARC-AGI-3 progress on April 14 and recommended prioritizing phase detection for multi-phase games. The dc22 deep analysis proved that some games have distinct phases:

**Phase 1: Environment Configuration** — click puzzle sprites to change the environment (open paths, activate buttons, create bridges)
**Phase 2: Navigation** — move the player to the goal through the modified environment

The current agent treats all actions uniformly. It doesn't know when it's in Phase 1 (should be clicking/exploring) vs Phase 2 (should be navigating to goal). This causes:
- Wasted step budget on navigation when the path isn't open yet
- Wasted step budget on clicking when the path IS open
- No ability to reason about phase transitions

dc22 specifics that generalize:
- `sys_click` buttons start INTANGIBLE and must be activated through puzzle interactions
- The death timer is animation-based, not step-count-based in some phases
- Arrow keys produce tiny frame changes (decorative) while clicks produce large changes (meaningful)
- The game has a 4x4 logical grid navigated by click buttons, not arrow keys

This pattern appears in other ARC-AGI-3 games: some require setup before navigation, some require collecting items before reaching the goal, some require solving sub-puzzles to unlock the main path.

---

## Objective

Add a phase detection module to the ARC-AGI-3 agent that:
1. Detects which phase the game is in based on observable signals
2. Adjusts action selection strategy per phase
3. Detects phase transitions (environment changed → switch from configuration to navigation)

---

## Files to Create/Modify

1. **CREATE** `/ganuda/services/arc_agi_3/phase_detector.py` — Phase detection module
2. **MODIFY** `/ganuda/services/arc_agi_3/ganuda_agent.py` — Wire phase detector into agent loop

---

## Implementation

### 1. `/ganuda/services/arc_agi_3/phase_detector.py`

```python
"""
Phase Detection for ARC-AGI-3 Games

Detects which phase a game is in based on observable signals:
  EXPLORE   — initial phase, discovering what actions do
  CONFIGURE — clicking/interacting to change the environment
  NAVIGATE  — moving toward the goal through a configured environment
  STUCK     — no progress in current phase, need to switch strategy

Signals used:
  - Frame change magnitude per action type (clicks vs arrows)
  - Rate of new state discovery (declining = phase may be ending)
  - Game-over pattern (repeating = stuck in wrong phase)
  - Score changes (level up = phase completed)

Council vote #33e1fe4ae927c482 — Raven priority.
ARC-PHASE-DETECT-001 | Tag: it_triad_jr
"""

import logging
from dataclasses import dataclass, field
from collections import deque
from typing import Optional

logger = logging.getLogger(__name__)

# Phase constants
EXPLORE = "EXPLORE"
CONFIGURE = "CONFIGURE"
NAVIGATE = "NAVIGATE"
STUCK = "STUCK"


@dataclass
class PhaseSignals:
    """Observable signals for phase detection."""

    # Frame change magnitudes by action type
    arrow_magnitudes: deque = field(default_factory=lambda: deque(maxlen=20))
    click_magnitudes: deque = field(default_factory=lambda: deque(maxlen=20))

    # Progress tracking
    actions_since_last_progress: int = 0
    game_overs_in_phase: int = 0
    total_actions_in_phase: int = 0
    last_score: int = 0

    # State discovery rate
    unique_frames_seen: set = field(default_factory=set)
    frames_last_window: deque = field(default_factory=lambda: deque(maxlen=30))

    def record_action(self, action_name: str, frame_hash: str, magnitude: float):
        """Record an action and its effect."""
        self.total_actions_in_phase += 1
        self.actions_since_last_progress += 1

        if action_name in ('ACTION1', 'ACTION2', 'ACTION3', 'ACTION4'):
            self.arrow_magnitudes.append(magnitude)
        elif action_name == 'ACTION6':
            self.click_magnitudes.append(magnitude)

        is_new = frame_hash not in self.unique_frames_seen
        self.unique_frames_seen.add(frame_hash)
        self.frames_last_window.append(frame_hash)

    def record_game_over(self):
        self.game_overs_in_phase += 1

    def record_score_change(self, new_score: int):
        if new_score > self.last_score:
            self.actions_since_last_progress = 0
        self.last_score = new_score

    def avg_arrow_magnitude(self) -> float:
        return sum(self.arrow_magnitudes) / len(self.arrow_magnitudes) if self.arrow_magnitudes else 0.0

    def avg_click_magnitude(self) -> float:
        return sum(self.click_magnitudes) / len(self.click_magnitudes) if self.click_magnitudes else 0.0

    def discovery_rate(self) -> float:
        """Fraction of recent frames that were new."""
        if not self.frames_last_window:
            return 1.0
        seen_before = set()
        new_count = 0
        for fh in self.frames_last_window:
            if fh not in seen_before:
                new_count += 1
            seen_before.add(fh)
        return new_count / len(self.frames_last_window)


class PhaseDetector:
    """Detect which phase the game is in and recommend action strategy.

    Phase transitions:
      EXPLORE → CONFIGURE: when clicks produce larger frame changes than arrows
      EXPLORE → NAVIGATE: when arrows produce meaningful progress toward goal
      CONFIGURE → NAVIGATE: when click effects diminish (environment configured)
      ANY → STUCK: when no progress for N actions
      STUCK → EXPLORE: reset and try different approach
    """

    def __init__(self):
        self.signals = PhaseSignals()
        self.current_phase = EXPLORE
        self._phase_history = []  # list of (phase, duration)
        self._stuck_threshold = 50  # actions without progress before STUCK
        self._min_samples = 10  # minimum actions before classifying

    def observe(self, action_name: str, frame_hash: str, magnitude: float, score: int):
        """Record an observation and potentially update phase."""
        self.signals.record_action(action_name, frame_hash, magnitude)
        self.signals.record_score_change(score)

        # Don't classify until we have enough data
        if self.signals.total_actions_in_phase < self._min_samples:
            return

        new_phase = self._classify()
        if new_phase != self.current_phase:
            logger.info(
                f"[PHASE] {self.current_phase} → {new_phase} "
                f"(arrows={self.signals.avg_arrow_magnitude():.4f} "
                f"clicks={self.signals.avg_click_magnitude():.4f} "
                f"discovery={self.signals.discovery_rate():.2f} "
                f"actions={self.signals.total_actions_in_phase})"
            )
            self._phase_history.append((self.current_phase, self.signals.total_actions_in_phase))
            self.current_phase = new_phase
            # Don't reset signals — they carry forward for context

    def observe_game_over(self):
        self.signals.record_game_over()

    def _classify(self) -> str:
        """Classify current phase based on accumulated signals."""
        arrow_mag = self.signals.avg_arrow_magnitude()
        click_mag = self.signals.avg_click_magnitude()
        discovery = self.signals.discovery_rate()
        stale = self.signals.actions_since_last_progress

        # STUCK: no progress for too long
        if stale > self._stuck_threshold:
            return STUCK

        # CONFIGURE: clicks produce more change than arrows
        if click_mag > arrow_mag * 2 and click_mag > 0.01:
            return CONFIGURE

        # NAVIGATE: arrows produce meaningful change, discovery declining
        if arrow_mag > 0.01 and discovery < 0.3:
            return NAVIGATE

        # EXPLORE: still discovering new states
        if discovery > 0.5:
            return EXPLORE

        # Default: if arrows work at all, navigate; otherwise explore
        if arrow_mag > 0.005:
            return NAVIGATE
        return EXPLORE

    def get_action_bias(self) -> dict:
        """Return action selection biases for the current phase.

        Returns dict with:
          prefer_clicks: bool — should the agent prefer click actions?
          prefer_arrows: bool — should the agent prefer arrow keys?
          explore_rate: float — probability of random exploration (0-1)
          goal_directed: bool — should the agent move toward detected goal?
        """
        if self.current_phase == EXPLORE:
            return {
                'prefer_clicks': False,
                'prefer_arrows': False,
                'explore_rate': 0.8,
                'goal_directed': False,
            }
        elif self.current_phase == CONFIGURE:
            return {
                'prefer_clicks': True,
                'prefer_arrows': False,
                'explore_rate': 0.5,
                'goal_directed': False,
            }
        elif self.current_phase == NAVIGATE:
            return {
                'prefer_clicks': False,
                'prefer_arrows': True,
                'explore_rate': 0.2,
                'goal_directed': True,
            }
        else:  # STUCK
            return {
                'prefer_clicks': True,  # Try clicks — might unlock something
                'prefer_arrows': True,  # Try everything
                'explore_rate': 1.0,    # Full random exploration
                'goal_directed': False,
            }

    def reset(self):
        """Reset for new level."""
        self._phase_history.append((self.current_phase, self.signals.total_actions_in_phase))
        self.signals = PhaseSignals()
        self.current_phase = EXPLORE
```

### 2. Wire into `ganuda_agent.py`

**In `__init__`**, add:
```python
from phase_detector import PhaseDetector, EXPLORE, CONFIGURE, NAVIGATE, STUCK
self.phase_detector = PhaseDetector()
```

**After frame processing and magnitude tracking**, add:
```python
# Feed observation to phase detector
if self._prev_frame_grid is not None and self.last_edge_idx is not None:
    action_name = "unknown"
    if self.last_edge_idx < len(self._action_map):
        action_name = self._action_map[self.last_edge_idx][0].name
    self.phase_detector.observe(
        action_name, frame_hash, magnitude,
        latest_frame.levels_completed or 0
    )
```

**Before action selection**, add phase-aware biasing:
```python
# Phase-aware action selection
phase_bias = self.phase_detector.get_action_bias()
if phase_bias['prefer_clicks'] and not phase_bias['prefer_arrows']:
    # In CONFIGURE phase — skip arrow keys, try clicks
    # (implementation: filter candidates or force ACTION6)
    pass  # Integration point — agent chooses click actions
elif phase_bias['goal_directed']:
    # In NAVIGATE phase — use goal direction bias
    # (already implemented via _detect_goal_direction)
    pass
```

**On game-over**, add:
```python
self.phase_detector.observe_game_over()
```

**On level-up**, add:
```python
self.phase_detector.reset()
```

---

## Success Criteria

- [ ] `phase_detector.py` created at `/ganuda/services/arc_agi_3/phase_detector.py`
- [ ] PhaseDetector correctly classifies EXPLORE when discovery rate is high
- [ ] PhaseDetector correctly classifies CONFIGURE when clicks > arrows
- [ ] PhaseDetector correctly classifies NAVIGATE when arrows produce progress
- [ ] PhaseDetector correctly classifies STUCK after 50 actions without progress
- [ ] Phase transitions logged with `[PHASE]` tag
- [ ] `get_action_bias()` returns different biases per phase
- [ ] Agent uses phase bias to adjust action selection
- [ ] dc22 enters CONFIGURE phase (clicks meaningless but phase detector triggers exploration)

## How This Helps dc22 Specifically

dc22's failure mode: the agent spams arrow keys (0.2% frame change) for 128 actions, dies, repeats. With phase detection:

1. **EXPLORE (actions 0-10):** Agent tries both arrows and clicks. Arrow magnitudes are tiny (0.2%). Click magnitudes TBD.
2. **PHASE TRANSITION:** If clicks produce more change than arrows → CONFIGURE. If neither works → STUCK.
3. **STUCK (after 50 actions):** Full random exploration. Try clicking everywhere. Try different action combinations.
4. **CONFIGURE (if clicks work):** Focus on click actions to change the environment.
5. **NAVIGATE (after environment changes):** Use goal-directed arrow keys.

Even if phase detection doesn't SOLVE dc22, it prevents the agent from wasting 128 actions on the wrong action type. That alone improves all multi-phase games.

---

For Seven Generations.
