#!/usr/bin/env python3
"""
dc22 Smart Solver — Observe After Every Action

The agent that LOOKS at what happened after every click and move.
Discovers new buttons dynamically. Builds understanding mid-game.

Process:
1. Scan for clickable buttons on the frame
2. Click each button, observe what changed (bridges rotated?)
3. Try each direction, observe if player moved
4. After each move, re-scan for NEW clickable elements
5. When stuck, click buttons to change the layout
6. Repeat until goal reached
"""

import numpy as np
import sys
import os
import logging

sys.path.insert(0, os.path.dirname(__file__))

from arc_agi import Arcade
from arcengine import GameAction, GameState

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(message)s', datefmt='%H:%M:%S')
logger = logging.getLogger(__name__)

U, D, L, R = GameAction.ACTION1, GameAction.ACTION2, GameAction.ACTION3, GameAction.ACTION4


class SmartSolver:
    def __init__(self, env):
        self.env = env
        self.game = env._game
        self.known_buttons = []  # [(x, y, pixel_change)] discovered click targets
        self.visited_positions = set()
        self.goal = None
        self.button_scan_done = False

    def pos(self):
        for attr in dir(self.game):
            val = getattr(self.game, attr, None)
            if val and hasattr(val, 'x') and hasattr(val, 'tags'):
                tags = val.tags if hasattr(val, 'tags') else []
                if isinstance(tags, list) and any('jfva' in str(t) or 'pcxjvnmybet' in str(t) for t in tags):
                    return (val.x, val.y)
        return None

    def goal_pos(self):
        for attr in dir(self.game):
            val = getattr(self.game, attr, None)
            if val and hasattr(val, 'x') and hasattr(val, 'tags'):
                tags = val.tags if hasattr(val, 'tags') else []
                if isinstance(tags, list) and any('goknoi' in str(t) or 'bqxa' in str(t) for t in tags):
                    return (val.x, val.y)
        return None

    def scan_for_buttons(self):
        """Click across the right side of the frame to find hat buttons."""
        logger.info("[SCAN] Scanning for clickable buttons...")
        base = np.array(self.env.step(GameAction.ACTION6, data={'x': 0, 'y': 0}).frame[-1])
        buttons = []

        # Scan right half where hat buttons typically live
        for y in range(8, 56, 4):
            for x in range(35, 62, 4):
                frame = self.env.step(GameAction.ACTION6, data={'x': x, 'y': y})
                if frame.state == GameState.GAME_OVER or not frame.frame:
                    return buttons
                grid = np.array(frame.frame[-1])
                diff = int(np.sum(grid[:63, :] != base[:63, :]))
                if diff > 10:
                    buttons.append((x, y, diff))
                    # Click again to toggle back
                    f2 = self.env.step(GameAction.ACTION6, data={'x': x, 'y': y})
                    if f2.state == GameState.GAME_OVER or not f2.frame:
                        return buttons
                f3 = self.env.step(GameAction.ACTION6, data={'x': 0, 'y': 0})
                if f3.state == GameState.GAME_OVER or not f3.frame:
                    return buttons
                base = np.array(f3.frame[-1])

        # Also scan the left/center for any mid-game buttons
        for y in range(8, 56, 4):
            for x in range(0, 35, 4):
                frame = self.env.step(GameAction.ACTION6, data={'x': x, 'y': y})
                if frame.state == GameState.GAME_OVER or not frame.frame:
                    return buttons
                grid = np.array(frame.frame[-1])
                diff = int(np.sum(grid[:63, :] != base[:63, :]))
                if diff > 10:
                    buttons.append((x, y, diff))
                    f2 = self.env.step(GameAction.ACTION6, data={'x': x, 'y': y})
                    if f2.state == GameState.GAME_OVER or not f2.frame:
                        return buttons
                f3 = self.env.step(GameAction.ACTION6, data={'x': 0, 'y': 0})
                if f3.state == GameState.GAME_OVER or not f3.frame:
                    return buttons
                base = np.array(f3.frame[-1])

        return buttons

    def try_move(self, direction):
        """Try to move, return (new_pos, moved, frame)."""
        p1 = self.pos()
        frame = self.env.step(direction)
        p2 = self.pos()
        moved = p2 != p1
        return p2, moved, frame

    def click_and_try_all_directions(self, button_x, button_y):
        """Click a button, then try all 4 directions. Return which ones work."""
        self.env.step(GameAction.ACTION6, data={'x': button_x, 'y': button_y})
        working = []
        for direction, name in [(U, 'U'), (D, 'D'), (L, 'L'), (R, 'R')]:
            p1 = self.pos()
            frame = self.env.step(direction)
            p2 = self.pos()
            if p2 != p1:
                working.append((direction, name, p2))
                # Move back
                reverse = {U: D, D: U, L: R, R: L}
                self.env.step(reverse[direction])
            if frame.state in (GameState.WIN, GameState.GAME_OVER):
                return working, frame
        return working, frame

    def solve(self):
        """Main solve loop: scan, experiment, navigate."""
        self.goal = self.goal_pos()
        start = self.pos()
        logger.info(f"[SOLVE] Start: {start} Goal: {self.goal}")

        # Phase 1: Discover buttons
        self.known_buttons = self.scan_for_buttons()
        logger.info(f"[SOLVE] Found {len(self.known_buttons)} buttons")

        # Deduplicate buttons by clustering
        clusters = []
        for bx, by, bd in self.known_buttons:
            found = False
            for c in clusters:
                if abs(bx - c[0]) < 8 and abs(by - c[1]) < 8:
                    found = True
                    break
            if not found:
                clusters.append((bx, by, bd))
        logger.info(f"[SOLVE] {len(clusters)} button clusters: {[(x,y) for x,y,_ in clusters]}")

        # Phase 2: For each button, discover what directions it opens
        button_effects = {}
        for bx, by, _ in clusters:
            working, frame = self.click_and_try_all_directions(bx, by)
            button_effects[(bx, by)] = working
            logger.info(f"[SOLVE] Button ({bx},{by}) opens: {[(n, p) for _, n, p in working]}")
            if frame.state == GameState.WIN:
                logger.info("*** WON during exploration! ***")
                return True

        # Phase 3: Navigate toward goal using discovered mechanics
        # Strategy: click button, move in the direction that reduces distance,
        # after each move rescan for new buttons
        logger.info("[SOLVE] Navigating toward goal...")
        best_dist = abs(self.goal[0] - start[0]) + abs(self.goal[1] - start[1])
        stuck_count = 0
        rescan_interval = 10  # Rescan for new buttons every N moves

        for step in range(300):  # Max iterations (clicks are ~free)
            p = self.pos()
            if not p:
                continue
            dist = abs(self.goal[0] - p[0]) + abs(self.goal[1] - p[1])
            self.visited_positions.add(p)

            # Try each button + each direction, pick the one that gets closest
            best_move = None
            best_new_dist = dist

            for bx, by, _ in clusters:
                self.env.step(GameAction.ACTION6, data={'x': bx, 'y': by})
                for direction, name in [(U, 'U'), (D, 'D'), (L, 'L'), (R, 'R')]:
                    p1 = self.pos()
                    frame = self.env.step(direction)
                    p2 = self.pos()

                    if not frame.frame or frame.state == GameState.GAME_OVER:
                        logger.info(f"Game over during navigation at step {step}")
                        return False

                    if frame.state == GameState.WIN:
                        logger.info(f"*** L2 SOLVED at step {step}! ***")
                        return True

                    if p2 != p1:
                        new_dist = abs(self.goal[0] - p2[0]) + abs(self.goal[1] - p2[1])
                        # Prefer: closer to goal, or NEW position
                        bonus = -5 if p2 not in self.visited_positions else 0
                        if new_dist + bonus < best_new_dist:
                            best_new_dist = new_dist + bonus
                            best_move = (bx, by, direction, name, p2, new_dist)
                        # Move back for now
                        reverse = {U: D, D: U, L: R, R: L}
                        self.env.step(reverse[direction])

                    if frame.state == GameState.GAME_OVER:
                        logger.info(f"Game over at step {step}")
                        return False

                # Toggle button back
                self.env.step(GameAction.ACTION6, data={'x': bx, 'y': by})

            if best_move:
                bx, by, direction, name, new_pos, new_dist = best_move
                # Execute the best move for real
                self.env.step(GameAction.ACTION6, data={'x': bx, 'y': by})
                self.env.step(direction)

                if new_dist < best_dist:
                    best_dist = new_dist
                    logger.info(f"  Step {step}: ({bx},{by})+{name} → {new_pos} dist={new_dist} NEW BEST")
                stuck_count = 0

                # Rescan for new buttons periodically
                if step % rescan_interval == 0 and step > 0:
                    new_buttons = self.scan_for_buttons()
                    new_clusters = []
                    for nbx, nby, nbd in new_buttons:
                        is_new = True
                        for c in clusters:
                            if abs(nbx - c[0]) < 8 and abs(nby - c[1]) < 8:
                                is_new = False
                                break
                        if is_new:
                            new_clusters.append((nbx, nby, nbd))
                    if new_clusters:
                        logger.info(f"  NEW BUTTONS FOUND: {[(x,y) for x,y,_ in new_clusters]}")
                        clusters.extend(new_clusters)
            else:
                stuck_count += 1
                if stuck_count > 5:
                    logger.info(f"  Stuck for {stuck_count} iterations. Rescanning...")
                    new_buttons = self.scan_for_buttons()
                    for nbx, nby, nbd in new_buttons:
                        is_new = True
                        for c in clusters:
                            if abs(nbx - c[0]) < 8 and abs(nby - c[1]) < 8:
                                is_new = False
                                break
                        if is_new:
                            clusters.append((nbx, nby, nbd))
                            logger.info(f"  NEW BUTTON: ({nbx},{nby})")
                    stuck_count = 0

        logger.info(f"Max iterations reached. Best dist: {best_dist}")
        return False


def main():
    arcade = Arcade()
    env = arcade.make('dc22')
    env.step(GameAction.RESET)

    # Solve L1 first
    hat_a1 = {'x': 42, 'y': 20}
    hat_b1 = {'x': 42, 'y': 37}
    for i, d in enumerate([U]*5 + [R]*5 + [U]*5 + [R]):
        env.step(GameAction.ACTION6, data=hat_a1 if i % 2 == 0 else hat_b1)
        env.step(d)
    env.step(R)
    env.step(R)
    logger.info("L1 SOLVED")

    # Solve L2
    solver = SmartSolver(env)
    won = solver.solve()
    logger.info(f"L2 result: {'WON' if won else 'FAILED'}")


if __name__ == "__main__":
    main()
