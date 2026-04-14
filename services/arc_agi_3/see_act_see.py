#!/usr/bin/env python3
"""
See-Act-See Protocol — Iterative Visual Understanding

The bilateral hemisphere approach to game-solving:
  SEE: 72B looks at the game frame visually
  ACT: Execute a few exploratory actions
  SEE: 72B compares before/after, refines understanding
  REPEAT: Until the game mechanics are understood, then solve

This bridges the gap between:
  - Pure exploration (graph explorer) — acts without seeing
  - Single-shot vision (see-first) — sees without iterating

The organism learns by doing AND seeing together.

Usage:
    python see_act_see.py sb26      # Single game
    python see_act_see.py --all     # All unsolved games
"""

import sys
import os
import re
import json
import logging
import hashlib
import numpy as np
import requests
from typing import List, Tuple, Optional, Dict

sys.path.insert(0, os.path.dirname(__file__))

from arc_agi import Arcade
from arcengine import GameAction, GameState, FrameData

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(message)s', datefmt='%H:%M:%S')
logger = logging.getLogger(__name__)

VLLM_URL = "http://localhost:8000/v1/chat/completions"
VLLM_MODEL = "/ganuda/models/qwen2.5-72b-instruct-awq"

COLOR_NAMES = {
    0: 'black', 1: 'blue', 2: 'red', 3: 'green', 4: 'yellow',
    5: 'gray', 6: 'magenta', 7: 'orange', 8: 'darkgray', 9: 'maroon',
    10: 'teal', 11: 'cyan', 12: 'pink', 13: 'olive', 14: 'purple', 15: 'white',
}

CHARS = {i: c for i, c in enumerate('.123456789ABCDEF')}


def render_grid_compact(frame: np.ndarray, skip_bg: bool = True) -> str:
    """Render frame as compact ASCII, skipping pure-background rows."""
    bg = int(np.median(frame))  # most common value = background
    lines = []
    for y in range(frame.shape[0]):
        row = ''.join(CHARS.get(frame[y][x], '?') for x in range(frame.shape[1]))
        bg_char = CHARS.get(bg, '_')
        if skip_bg and all(c == bg_char for c in row):
            continue
        lines.append(f'R{y:02d} {row}')
    return '\n'.join(lines)


def describe_diff(before: np.ndarray, after: np.ndarray) -> str:
    """Describe what changed between two frames in natural language."""
    diff = before != after
    if not diff.any():
        return "Nothing changed."

    changed_pixels = diff.sum()
    changed_rows = np.where(np.any(diff, axis=1))[0]
    changed_cols = np.where(np.any(diff, axis=0))[0]

    # Find which colors appeared/disappeared
    before_colors = set(np.unique(before[diff]))
    after_colors = set(np.unique(after[diff]))
    appeared = after_colors - before_colors
    disappeared = before_colors - after_colors

    desc = f"{changed_pixels} pixels changed in rows {changed_rows[0]}-{changed_rows[-1]}, cols {changed_cols[0]}-{changed_cols[-1]}."
    if appeared:
        desc += f" New colors appeared: {[COLOR_NAMES.get(c, str(c)) for c in appeared]}."
    if disappeared:
        desc += f" Colors disappeared: {[COLOR_NAMES.get(c, str(c)) for c in disappeared]}."

    return desc


def call_72b(messages: list, max_tokens: int = 400) -> str:
    """Call the local 72B for visual reasoning."""
    try:
        resp = requests.post(VLLM_URL, json={
            'model': VLLM_MODEL,
            'messages': messages,
            'max_tokens': max_tokens,
            'temperature': 0.1,
        }, timeout=30)
        return resp.json()['choices'][0]['message']['content']
    except Exception as e:
        logger.warning(f"72B call failed: {e}")
        return ""


def parse_actions(text: str, available: list) -> list:
    """Parse action instructions from 72B response."""
    actions = []
    for line in text.split('\n'):
        line = line.strip().upper()

        # CLICK x y
        m = re.search(r'CLICK\s+(\d+)\s*[,\s]\s*(\d+)', line)
        if m and 6 in available:
            actions.append(('CLICK', int(m.group(1)), int(m.group(2))))
            continue

        # ACTION7 x y
        m = re.search(r'ACTION7\s+(\d+)\s*[,\s]\s*(\d+)', line)
        if m and 7 in available:
            actions.append(('ACTION7', int(m.group(1)), int(m.group(2))))
            continue

        # Directional
        if re.search(r'\bUP\b', line) and 1 in available:
            actions.append(('UP',))
        elif re.search(r'\bDOWN\b', line) and 2 in available:
            actions.append(('DOWN',))
        elif re.search(r'\bLEFT\b', line) and 3 in available:
            actions.append(('LEFT',))
        elif re.search(r'\bRIGHT\b', line) and 4 in available:
            actions.append(('RIGHT',))
        elif re.search(r'\bCONFIRM\b', line) and 5 in available:
            actions.append(('CONFIRM',))

    return actions


def execute_action(env, act_tuple):
    """Execute a single parsed action tuple, return raw observation."""
    if act_tuple[0] == 'CLICK':
        action = GameAction.ACTION6
        data = {'x': act_tuple[1], 'y': act_tuple[2]}
        action.set_data(data)
        return env.step(action, data=data, reasoning={})
    elif act_tuple[0] == 'ACTION7':
        action = GameAction.ACTION7
        data = {'x': act_tuple[1], 'y': act_tuple[2]}
        action.set_data(data)
        return env.step(action, data=data, reasoning={})
    elif act_tuple[0] == 'UP':
        return env.step(GameAction.ACTION1, data={}, reasoning={})
    elif act_tuple[0] == 'DOWN':
        return env.step(GameAction.ACTION2, data={}, reasoning={})
    elif act_tuple[0] == 'LEFT':
        return env.step(GameAction.ACTION3, data={}, reasoning={})
    elif act_tuple[0] == 'RIGHT':
        return env.step(GameAction.ACTION4, data={}, reasoning={})
    elif act_tuple[0] == 'CONFIRM':
        return env.step(GameAction.ACTION5, data={}, reasoning={})
    return None


def see_act_see(game_id: str, max_rounds: int = 5, actions_per_round: int = 8,
                max_total_actions: int = 100) -> dict:
    """
    The See-Act-See Protocol.

    Round 1: SEE the initial frame → generate exploratory actions
    Round 2+: SEE before/after diffs → refine understanding → better actions
    Final: Once mechanics understood, generate solution sequence
    """
    arcade = Arcade()
    env = arcade.make(game_id)
    obs = env.observation_space
    available = obs.available_actions
    action_names = [f'ACTION{a}' for a in available]

    frame = np.array(obs.frame[-1], dtype=np.uint8)
    initial_frame = frame.copy()
    total_actions = 0
    levels = 0
    observations = []  # accumulate what we learn each round

    logger.info(f"{game_id}: Starting See-Act-See (actions: {action_names})")

    # Build conversation history for multi-turn reasoning
    system_msg = {
        "role": "system",
        "content": (
            "You are a puzzle game analyst. You observe game states, suggest actions, "
            "learn from results, and iteratively solve the puzzle. "
            "Available action formats:\n"
            "- CLICK x y (click at coordinate)\n"
            "- UP / DOWN / LEFT / RIGHT (arrow keys)\n"
            "- CONFIRM (submit/special action)\n"
            "- ACTION7 x y (secondary click)\n"
            "Give actions one per line. Be specific with coordinates."
        )
    }
    messages = [system_msg]

    for round_num in range(1, max_rounds + 1):
        logger.info(f"  Round {round_num}/{max_rounds}")

        # === SEE ===
        grid_text = render_grid_compact(frame)

        if round_num == 1:
            user_msg = (
                f"Game: {game_id}\n"
                f"Available actions: {', '.join(action_names)}\n\n"
                f"Initial game state:\n{grid_text}\n\n"
                f"1. What objects and patterns do you see?\n"
                f"2. What might the objective be?\n"
                f"3. Give me {actions_per_round} exploratory actions to learn how the game works.\n"
                f"List each action on its own line."
            )
        else:
            # Include observations from previous round
            obs_text = '\n'.join(observations[-actions_per_round:])
            user_msg = (
                f"Round {round_num}. Here's what happened when I executed your actions:\n\n"
                f"{obs_text}\n\n"
                f"Current game state:\n{grid_text}\n\n"
                f"Based on what you've learned:\n"
                f"1. What do these actions DO in this game?\n"
                f"2. What's the objective now that you've seen the mechanics?\n"
                f"3. Give me {actions_per_round} BETTER actions to make progress toward solving.\n"
                f"List each action on its own line."
            )

        messages.append({"role": "user", "content": user_msg})

        # === THINK ===
        response = call_72b(messages, max_tokens=500)
        if not response:
            logger.warning(f"  72B returned empty response")
            break

        messages.append({"role": "assistant", "content": response})

        # Log first few lines of reasoning
        for line in response.split('\n')[:3]:
            if line.strip():
                logger.info(f"    72B: {line.strip()[:80]}")

        # === ACT ===
        plan = parse_actions(response, available)
        if not plan:
            logger.warning(f"  No actions parsed from 72B response")
            continue

        round_observations = []
        for act in plan[:actions_per_round]:
            if total_actions >= max_total_actions:
                break

            before = frame.copy()
            raw = execute_action(env, act)
            if raw is None:
                continue

            total_actions += 1
            new_frame = np.array(raw.frame[-1], dtype=np.uint8)
            diff_desc = describe_diff(before, new_frame)
            frame = new_frame

            act_str = ' '.join(str(x) for x in act)
            obs_line = f"Action: {act_str} → {diff_desc}"
            round_observations.append(obs_line)
            observations.append(obs_line)

            # Check for level completion
            if raw.levels_completed > levels:
                levels = raw.levels_completed
                logger.info(f"  LEVEL {levels} SOLVED at action {total_actions}!")
                # Try CONFIRM after level-up detection
                if 5 in available:
                    raw2 = env.step(GameAction.ACTION5, data={}, reasoning={})
                    total_actions += 1
                    if raw2.levels_completed > levels:
                        levels = raw2.levels_completed

            if raw.state == GameState.GAME_OVER:
                logger.info(f"  Game over at action {total_actions}")
                # Reset
                env.step(GameAction.RESET, data={}, reasoning={})
                total_actions += 1
                obs3 = env.observation_space
                frame = np.array(obs3.frame[-1], dtype=np.uint8)
                round_observations.append("GAME OVER — reset")
                observations.append("GAME OVER — reset")
                break

            if raw.state == GameState.WIN:
                logger.info(f"  WIN!")
                break

        if levels > 0 or (raw and raw.state == GameState.WIN):
            break

    result = {
        'game_id': game_id,
        'levels': levels,
        'total_actions': total_actions,
        'rounds': round_num,
        'observations': len(observations),
    }
    logger.info(f"  Result: {levels} levels in {total_actions} actions over {round_num} rounds")
    return result


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='See-Act-See Protocol')
    parser.add_argument('games', nargs='*', default=['sb26'])
    parser.add_argument('--all', action='store_true', help='Run all unsolved games')
    parser.add_argument('--rounds', type=int, default=6, help='Max rounds per game')
    parser.add_argument('--actions-per-round', type=int, default=10, help='Actions per round')
    parser.add_argument('--max-actions', type=int, default=150, help='Max total actions')
    args = parser.parse_args()

    if args.all:
        games = ['sb26', 'sc25', 'ka59', 'lf52', 're86', 'dc22', 'wa30', 'g50t']
    else:
        games = args.games

    results = []
    for game_id in games:
        result = see_act_see(
            game_id,
            max_rounds=args.rounds,
            actions_per_round=args.actions_per_round,
            max_total_actions=args.max_actions,
        )
        results.append(result)

    print(f"\n{'='*60}")
    print(f"SEE-ACT-SEE RESULTS")
    print(f"{'='*60}")
    for r in results:
        status = f"L{r['levels']}" if r['levels'] > 0 else "unsolved"
        print(f"  {r['game_id']}: {status} | {r['total_actions']} actions, {r['rounds']} rounds")
    solved = sum(1 for r in results if r['levels'] > 0)
    print(f"\n  Solved: {solved}/{len(results)}")
