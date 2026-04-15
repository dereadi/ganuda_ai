#!/usr/bin/env python3
"""
ARC-AGI-3 Visual Agent — Click-First Exploration

Design philosophy (from ARC-AGI-3 game rules):
  1. Everything interactive is ON SCREEN — no hidden keyboard mappings
  2. You CLICK things to discover what they do
  3. Arrow keys are ONLY for movement (and cost step counter)
  4. The step counter is the key signal — watch when it ticks vs when it doesn't
  5. The agent must EXPERIMENT: click, observe, build model, plan, execute

Three phases:
  DISCOVER — click every visible element, observe changes, watch counter
  PLAN     — use discovered mechanics to plan the solution
  EXECUTE  — click the right things in order, then navigate to goal

Works with the Python API (env.step) not the browser.
Uses VLM for frame analysis when available, falls back to pixel diffing.
"""

import logging
import numpy as np
import os
import sys
import time
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict

sys.path.insert(0, os.path.dirname(__file__))

from arcengine import GameAction, GameState

logger = logging.getLogger(__name__)

# VLM endpoint (try local GPU first, then bluefin)
VLM_ENDPOINTS = [
    "http://localhost:9101/v1/chat/completions",
    "http://10.100.0.2:8090/v1/chat/completions",
]
VLM_MODEL = "Qwen/Qwen2-VL-7B-Instruct-AWQ"


@dataclass
class ClickableElement:
    """A discovered interactive element on screen."""
    x: int
    y: int
    label: str = ""
    effect: str = ""  # what happened when we clicked it
    counter_cost: int = 0  # did the step counter tick? 0=free, 1=costs a step
    frame_change: float = 0.0  # magnitude of visual change


@dataclass
class GameModel:
    """Mental model built from exploration."""
    clickables: List[ClickableElement] = field(default_factory=list)
    arrow_cost: int = 1  # arrows always cost steps (assumption)
    free_clicks: List[ClickableElement] = field(default_factory=list)  # clicks that don't cost steps
    costly_clicks: List[ClickableElement] = field(default_factory=list)
    player_pos: Tuple[int, int] = (0, 0)
    goal_pos: Tuple[int, int] = (0, 0)
    counter_start: int = 0
    counter_current: int = 0


class VisualAgent:
    """ARC-AGI-3 agent that learns through visual experimentation.

    Phase 1 (DISCOVER): Click everything on screen. For each click:
      - Capture frame before and after
      - Measure pixel change magnitude
      - Track step counter (row y=63) to see if click cost a step
      - Record what changed

    Phase 2 (PLAN): Using discovered mechanics:
      - Identify which clicks change the game state meaningfully
      - Determine click order (some might need to be clicked before others)
      - Plan movement path after clicks configure the environment

    Phase 3 (EXECUTE):
      - Click the right elements in order (free clicks first)
      - Navigate with arrows to the goal
    """

    def __init__(self):
        self.model = GameModel()
        self.phase = "DISCOVER"
        self.action_count = 0
        self.discover_queue = []  # positions to try clicking
        self.execute_plan = []  # planned actions
        self.execute_index = 0

    def _get_counter_value(self, grid: np.ndarray) -> int:
        """Read the step counter from the bottom row (y=63).

        The counter bar fills from left to right at y=63.
        Count how many pixels are non-zero (filled).
        """
        if grid.shape[0] <= 63:
            return 0
        bottom_row = grid[63, :]
        # Counter pixels are non-zero and non-background
        bg_val = int(np.median(grid[:60, :]))  # background from game area
        counter_pixels = np.sum(bottom_row != 0)
        return counter_pixels

    def _find_clickable_regions(self, grid: np.ndarray) -> List[Tuple[int, int, str]]:
        """Find distinct colored regions that might be interactive.

        Strategy: find all unique color clusters that aren't background.
        Each cluster center is a potential click target.
        """
        bg_val = int(np.median(grid[:60, :]))
        targets = []

        # Find all unique non-background colors
        unique_colors = np.unique(grid[:60, :])  # exclude counter bar

        for color in unique_colors:
            if color == bg_val or color == 0:
                continue

            # Find center of mass for this color
            ys, xs = np.where(grid[:60, :] == color)
            if len(xs) == 0:
                continue

            cx = int(np.mean(xs))
            cy = int(np.mean(ys))
            area = len(xs)

            # Only consider clusters of reasonable size (not noise)
            if area >= 2:
                targets.append((cx, cy, f"color_{color}_area_{area}"))

        # Sort by area (largest first — more likely to be important)
        targets.sort(key=lambda t: -int(t[2].split("area_")[1]))

        # Deduplicate nearby targets (within 4 pixels)
        deduped = []
        for t in targets:
            too_close = False
            for d in deduped:
                if abs(t[0] - d[0]) < 4 and abs(t[1] - d[1]) < 4:
                    too_close = True
                    break
            if not too_close:
                deduped.append(t)

        return deduped[:20]  # max 20 targets

    def _measure_counter_change(self, grid_before: np.ndarray, grid_after: np.ndarray) -> int:
        """Did the step counter tick between these two frames?

        Returns the number of counter pixels that changed.
        0 = free action, >0 = cost steps.
        """
        if grid_before.shape[0] <= 63 or grid_after.shape[0] <= 63:
            return 0
        counter_before = grid_before[63, :]
        counter_after = grid_after[63, :]
        return int(np.sum(counter_before != counter_after))

    def _frame_change_magnitude(self, grid_before: np.ndarray, grid_after: np.ndarray) -> float:
        """How much did the game area change (excluding counter bar)?"""
        game_before = grid_before[:63, :]
        game_after = grid_after[:63, :]
        return float(np.sum(game_before != game_after)) / game_before.size

    def discover_phase(self, env) -> List[ClickableElement]:
        """Phase 1: Click everything and observe.

        Returns list of discovered interactive elements.
        """
        logger.info("[DISCOVER] Starting click exploration...")

        # Get initial frame
        frame = env.step(GameAction.RESET)
        grid = np.array(frame.frame[-1])

        # Find all potential click targets
        targets = self._find_clickable_regions(grid)
        logger.info(f"[DISCOVER] Found {len(targets)} potential click targets")

        initial_counter = self._get_counter_value(grid)
        self.model.counter_start = initial_counter

        discovered = []

        for x, y, label in targets:
            # Capture before
            grid_before = np.array(frame.frame[-1])
            counter_before = self._get_counter_value(grid_before)

            # Click it
            click = GameAction.ACTION6
            click.set_data({'x': x, 'y': y})
            frame = env.step(click)

            # Capture after
            grid_after = np.array(frame.frame[-1])
            counter_after = self._get_counter_value(grid_after)

            # Measure effects
            counter_cost = self._measure_counter_change(grid_before, grid_after)
            magnitude = self._frame_change_magnitude(grid_before, grid_after)

            element = ClickableElement(
                x=x, y=y, label=label,
                effect=f"change={magnitude:.4f}",
                counter_cost=counter_cost,
                frame_change=magnitude,
            )
            discovered.append(element)

            if magnitude > 0.001:
                logger.info(
                    f"[DISCOVER] Click ({x},{y}) {label}: "
                    f"change={magnitude:.3f} counter_cost={counter_cost} "
                    f"{'FREE!' if counter_cost == 0 else 'COSTS STEP'}"
                )

            # Check for game over
            if frame.state == GameState.GAME_OVER:
                logger.info("[DISCOVER] Game over during exploration — resetting")
                frame = env.step(GameAction.RESET)
                grid = np.array(frame.frame[-1])

            if frame.state == GameState.WIN:
                logger.info("[DISCOVER] Won during exploration!")
                return discovered

        # Also test arrow keys to confirm they cost steps
        logger.info("[DISCOVER] Testing arrow key cost...")
        grid_before = np.array(frame.frame[-1])
        frame = env.step(GameAction.ACTION1)  # UP
        grid_after = np.array(frame.frame[-1])
        arrow_counter_cost = self._measure_counter_change(grid_before, grid_after)
        arrow_magnitude = self._frame_change_magnitude(grid_before, grid_after)
        logger.info(f"[DISCOVER] Arrow UP: change={arrow_magnitude:.3f} counter_cost={arrow_counter_cost}")

        # Categorize
        self.model.clickables = discovered
        self.model.free_clicks = [e for e in discovered if e.counter_cost == 0 and e.frame_change > 0.001]
        self.model.costly_clicks = [e for e in discovered if e.counter_cost > 0 and e.frame_change > 0.001]

        logger.info(
            f"[DISCOVER] Summary: {len(self.model.free_clicks)} free interactive, "
            f"{len(self.model.costly_clicks)} costly interactive, "
            f"{len(discovered) - len(self.model.free_clicks) - len(self.model.costly_clicks)} non-interactive"
        )

        return discovered

    def plan_phase(self, env) -> List:
        """Phase 2: Plan the solution based on discovered mechanics.

        Strategy:
        1. Click all FREE interactive elements (they don't cost steps)
        2. Observe cumulative effect — did clicking open a path?
        3. Plan movement using arrows (which DO cost steps)
        """
        logger.info("[PLAN] Building solution plan...")

        plan = []

        # Step 1: Click all free elements (might need multiple passes)
        for click_pass in range(3):  # up to 3 passes
            for element in self.model.free_clicks:
                plan.append(('click', element.x, element.y, f"free_{element.label}"))

        # Step 2: Click costly elements that produced big changes
        big_effects = sorted(self.model.costly_clicks, key=lambda e: -e.frame_change)
        for element in big_effects[:3]:  # top 3 most impactful
            plan.append(('click', element.x, element.y, f"costly_{element.label}"))

        # Step 3: Navigate — try systematic movement toward goal
        # Since we don't know exact positions, try a mix
        # The all-4 cycling works for movement; bias toward UP and RIGHT
        for i in range(15):
            plan.append(('move', 'UP'))
            plan.append(('move', 'RIGHT'))
            plan.append(('move', 'UP'))
            plan.append(('move', 'RIGHT'))
            plan.append(('move', 'UP'))
            plan.append(('move', 'DOWN'))
            plan.append(('move', 'LEFT'))

        logger.info(f"[PLAN] Plan: {len(plan)} actions ({sum(1 for p in plan if p[0]=='click')} clicks + {sum(1 for p in plan if p[0]=='move')} moves)")
        return plan

    def execute_phase(self, env, plan: List) -> bool:
        """Phase 3: Execute the plan.

        Returns True if we won.
        """
        logger.info(f"[EXECUTE] Running {len(plan)} planned actions...")

        for i, action in enumerate(plan):
            if action[0] == 'click':
                _, x, y, label = action
                click = GameAction.ACTION6
                click.set_data({'x': int(x), 'y': int(y)})
                frame = env.step(click)

                if i < 10 or i % 20 == 0:
                    logger.info(f"[EXECUTE] Step {i}: click ({x},{y}) {label}")

            elif action[0] == 'move':
                direction = action[1]
                direction_map = {
                    'UP': GameAction.ACTION1,
                    'DOWN': GameAction.ACTION2,
                    'LEFT': GameAction.ACTION3,
                    'RIGHT': GameAction.ACTION4,
                }
                frame = env.step(direction_map[direction])

            if frame.state == GameState.WIN:
                logger.info(f"[EXECUTE] *** WIN at step {i}! ***")
                return True

            if frame.state == GameState.GAME_OVER:
                logger.info(f"[EXECUTE] Game over at step {i}")
                return False

        logger.info(f"[EXECUTE] Plan exhausted without win. Score: {frame.levels_completed}")
        return False

    def play_game(self, env, max_attempts: int = 5) -> dict:
        """Full game loop: discover → plan → execute, with retries.

        On game over, reset and try with accumulated knowledge.
        """
        results = {
            'attempts': 0,
            'won': False,
            'levels_completed': 0,
            'discovered_elements': 0,
            'free_clicks': 0,
        }

        for attempt in range(max_attempts):
            results['attempts'] = attempt + 1
            logger.info(f"\n{'='*60}")
            logger.info(f"[GAME] Attempt {attempt + 1}/{max_attempts}")
            logger.info(f"{'='*60}")

            # Phase 1: Discover (only on first attempt or if model is empty)
            if attempt == 0 or not self.model.clickables:
                discovered = self.discover_phase(env)
                results['discovered_elements'] = len(discovered)
                results['free_clicks'] = len(self.model.free_clicks)

            # Phase 2: Plan
            plan = self.plan_phase(env)

            # Reset for clean execution
            env.step(GameAction.RESET)

            # Phase 3: Execute
            won = self.execute_phase(env, plan)

            if won:
                results['won'] = True
                results['levels_completed'] = 1
                logger.info("[GAME] LEVEL COMPLETE!")
                return results

            logger.info(f"[GAME] Attempt {attempt + 1} failed. Retrying with modified plan...")

            # Shuffle the click order for next attempt
            import random
            random.shuffle(self.model.free_clicks)
            random.shuffle(self.model.costly_clicks)

        return results


def main():
    """Run the visual agent on a specified game."""
    import argparse

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(message)s',
        datefmt='%H:%M:%S',
    )

    parser = argparse.ArgumentParser(description="ARC-AGI-3 Visual Agent")
    parser.add_argument('game', default='dc22', nargs='?', help='Game ID')
    parser.add_argument('--attempts', type=int, default=5, help='Max attempts')
    args = parser.parse_args()

    from arc_agi import Arcade

    arcade = Arcade()
    env = arcade.make(args.game)

    agent = VisualAgent()
    results = agent.play_game(env, max_attempts=args.attempts)

    print(f"\n{'='*60}")
    print(f"RESULTS: {args.game}")
    print(f"  Attempts: {results['attempts']}")
    print(f"  Won: {results['won']}")
    print(f"  Discovered elements: {results['discovered_elements']}")
    print(f"  Free clicks: {results['free_clicks']}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
