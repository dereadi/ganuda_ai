#!/usr/bin/env python3
"""
Snapshot Explorer — Greedy Hill-Climbing with Visual Feedback

Partner's algorithm:
  1. SNAPSHOT current state
  2. Make one move
  3. If positive change → SNAPSHOT, next move
  4. If no change → try one more move before re-evaluating
     (accounts for paired actions like click-then-place)
  5. Repeat

This is basin-feeling: try, observe, commit or backtrack.
No batch planning. No multi-turn LLM. Just snapshot-act-evaluate.

The 72B is used ONCE at the start to understand the game layout.
After that, the snapshot comparison drives everything.
"""

import sys
import os
import re
import json
import logging
import numpy as np
import requests
from typing import List, Optional, Tuple

sys.path.insert(0, os.path.dirname(__file__))

from arc_agi import Arcade
from arcengine import GameAction, GameState

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(message)s', datefmt='%H:%M:%S')
logger = logging.getLogger(__name__)

VLLM_URL = "http://localhost:8000/v1/chat/completions"
VLLM_MODEL = "/ganuda/models/qwen2.5-72b-instruct-awq"

CHARS = {i: c for i, c in enumerate('.123456789ABCDEF')}


def frame_diff_score(before: np.ndarray, after: np.ndarray) -> float:
    """Score how much the frame changed. Higher = more change.
    Returns fraction of pixels that changed (0.0 to 1.0)."""
    return float(np.sum(before != after)) / before.size


def render_grid(frame: np.ndarray) -> str:
    """Compact ASCII rendering."""
    bg = int(np.median(frame))
    bg_char = CHARS.get(bg, '_')
    lines = []
    for y in range(frame.shape[0]):
        row = ''.join(CHARS.get(frame[y][x], '?') for x in range(frame.shape[1]))
        if any(c != bg_char for c in row):
            lines.append(f'R{y:02d} {row}')
    return '\n'.join(lines)


def ask_72b_initial(frame: np.ndarray, available: list) -> str:
    """One-shot: ask 72B to analyze the game and suggest what to try."""
    grid = render_grid(frame)
    action_names = [f'ACTION{a}' for a in available]

    prompt = f"""Analyze this 64x64 grid puzzle game.
Available actions: {', '.join(action_names)}
Actions 1-4 = arrow keys, ACTION5 = confirm, ACTION6 = click(x,y), ACTION7 = click2(x,y)

{grid}

What objects do you see? What's the likely objective?
List 20 specific actions to try, one per line. Format:
CLICK x y / UP / DOWN / LEFT / RIGHT / CONFIRM / ACTION7 x y
Focus on clicking distinct colored objects and interactive-looking elements."""

    try:
        resp = requests.post(VLLM_URL, json={
            'model': VLLM_MODEL,
            'messages': [{'role': 'user', 'content': prompt}],
            'max_tokens': 600,
            'temperature': 0.2,
        }, timeout=25)
        return resp.json()['choices'][0]['message']['content']
    except:
        return ""


def parse_actions(text: str, available: list) -> list:
    """Parse action instructions from text."""
    actions = []
    for line in text.split('\n'):
        line = line.strip().upper()
        m = re.search(r'CLICK\s+(\d+)\s*[,\s]\s*(\d+)', line)
        if m and 6 in available:
            actions.append(('CLICK', int(m.group(1)), int(m.group(2))))
            continue
        m = re.search(r'ACTION7\s+(\d+)\s*[,\s]\s*(\d+)', line)
        if m and 7 in available:
            actions.append(('ACTION7', int(m.group(1)), int(m.group(2))))
            continue
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


def execute(env, act):
    """Execute one action, return observation."""
    if act[0] == 'CLICK':
        a = GameAction.ACTION6
        a.set_data({'x': act[1], 'y': act[2]})
        return env.step(a, data={'x': act[1], 'y': act[2]}, reasoning={})
    elif act[0] == 'ACTION7':
        a = GameAction.ACTION7
        a.set_data({'x': act[1], 'y': act[2]})
        return env.step(a, data={'x': act[1], 'y': act[2]}, reasoning={})
    elif act[0] == 'UP':
        return env.step(GameAction.ACTION1, data={}, reasoning={})
    elif act[0] == 'DOWN':
        return env.step(GameAction.ACTION2, data={}, reasoning={})
    elif act[0] == 'LEFT':
        return env.step(GameAction.ACTION3, data={}, reasoning={})
    elif act[0] == 'RIGHT':
        return env.step(GameAction.ACTION4, data={}, reasoning={})
    elif act[0] == 'CONFIRM':
        return env.step(GameAction.ACTION5, data={}, reasoning={})
    return None


def snapshot_explore(game_id: str, max_actions: int = 200) -> dict:
    """
    Snapshot Explorer: Partner's greedy hill-climbing algorithm.

    1. 72B looks once → generates action candidates
    2. SNAPSHOT state
    3. Try action → did frame change?
       YES: positive! SNAPSHOT new state, continue
       NO: try one more action before giving up on this direction
    4. After 72B actions exhausted, try systematic grid clicking
    5. After any progress, try CONFIRM
    """
    arcade = Arcade()
    env = arcade.make(game_id)
    obs = env.observation_space
    available = obs.available_actions

    frame = np.array(obs.frame[-1], dtype=np.uint8)
    snapshot = frame.copy()  # The committed state
    total_actions = 0
    levels = 0
    positive_actions = []  # Actions that caused changes

    logger.info(f"{game_id}: Snapshot Explorer starting (actions: {available})")

    # === STEP 1: 72B looks once ===
    logger.info("  72B analyzing game...")
    analysis = ask_72b_initial(frame, available)
    action_candidates = parse_actions(analysis, available)
    logger.info(f"  72B suggested {len(action_candidates)} actions")

    # Add systematic grid clicks if we have click actions
    if 6 in available:
        # Click a grid of points across the frame
        for y in range(5, 60, 8):
            for x in range(5, 60, 8):
                action_candidates.append(('CLICK', x, y))

    if 7 in available:
        for y in range(5, 60, 12):
            for x in range(5, 60, 12):
                action_candidates.append(('ACTION7', x, y))

    # Add directional actions
    for d in [('UP',), ('DOWN',), ('LEFT',), ('RIGHT',), ('CONFIRM',)]:
        if not any(a[0] == d[0] for a in action_candidates):
            action_candidates.append(d)

    logger.info(f"  Total candidates: {len(action_candidates)}")

    # === STEP 2-4: Snapshot-Act-Evaluate loop ===
    i = 0
    while i < len(action_candidates) and total_actions < max_actions:
        act = action_candidates[i]

        # Take snapshot before acting
        snapshot = frame.copy()

        # === ACT ===
        raw = execute(env, act)
        if raw is None:
            i += 1
            continue
        total_actions += 1
        new_frame = np.array(raw.frame[-1], dtype=np.uint8)

        # === EVALUATE ===
        change = frame_diff_score(snapshot, new_frame)

        if raw.levels_completed > levels:
            levels = raw.levels_completed
            logger.info(f"  LEVEL {levels} SOLVED at action {total_actions}! ({act})")
            frame = new_frame
            # Try CONFIRM after level solve
            if 5 in available:
                raw2 = env.step(GameAction.ACTION5, data={}, reasoning={})
                total_actions += 1
                if raw2.levels_completed > levels:
                    levels = raw2.levels_completed
                frame = np.array(raw2.frame[-1], dtype=np.uint8)
            i += 1
            continue

        if raw.state == GameState.GAME_OVER:
            logger.info(f"  Game over at {total_actions}, resetting")
            env.step(GameAction.RESET, data={}, reasoning={})
            total_actions += 1
            obs2 = env.observation_space
            frame = np.array(obs2.frame[-1], dtype=np.uint8)
            i += 1
            continue

        if change > 0.001:  # Positive change!
            frame = new_frame
            positive_actions.append(act)
            act_str = ' '.join(str(x) for x in act)
            logger.info(f"  + Action {total_actions}: {act_str} → {change:.4f} change")

            # After a positive action, try CONFIRM
            if 5 in available and act[0] != 'CONFIRM':
                raw_c = env.step(GameAction.ACTION5, data={}, reasoning={})
                total_actions += 1
                new_c = np.array(raw_c.frame[-1], dtype=np.uint8)
                if raw_c.levels_completed > levels:
                    levels = raw_c.levels_completed
                    logger.info(f"  LEVEL {levels} SOLVED after CONFIRM!")
                    frame = new_c
                elif frame_diff_score(frame, new_c) > 0.001:
                    frame = new_c
                    logger.info(f"  + CONFIRM also changed state")

            i += 1
        else:
            # No change — try ONE MORE action before giving up
            # (accounts for paired interactions: click source, then click destination)
            if i + 1 < len(action_candidates):
                act2 = action_candidates[i + 1]
                raw2 = execute(env, act2)
                if raw2 is None:
                    i += 2
                    continue
                total_actions += 1
                new_frame2 = np.array(raw2.frame[-1], dtype=np.uint8)
                change2 = frame_diff_score(snapshot, new_frame2)

                if raw2.levels_completed > levels:
                    levels = raw2.levels_completed
                    logger.info(f"  LEVEL {levels} SOLVED with paired action!")
                    frame = new_frame2
                elif change2 > 0.001:
                    frame = new_frame2
                    act_str = ' '.join(str(x) for x in act)
                    act2_str = ' '.join(str(x) for x in act2)
                    logger.info(f"  + Paired: {act_str} + {act2_str} → {change2:.4f} change")
                    positive_actions.append(act)
                    positive_actions.append(act2)
                else:
                    frame = new_frame2  # Still update frame even if no visible change

                i += 2  # Skip both actions
            else:
                frame = new_frame
                i += 1

    result = {
        'game_id': game_id,
        'levels': levels,
        'total_actions': total_actions,
        'positive_actions': len(positive_actions),
        'candidates_tried': min(i, len(action_candidates)),
    }
    logger.info(f"  Result: {levels} levels, {total_actions} actions, "
               f"{len(positive_actions)} positive")
    return result


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('games', nargs='*', default=['sb26'])
    parser.add_argument('--all-unsolved', action='store_true')
    parser.add_argument('--max-actions', type=int, default=200)
    args = parser.parse_args()

    if args.all_unsolved:
        games = ['sb26', 'sc25', 'ka59', 'lf52', 're86', 'dc22', 'wa30', 'g50t']
    else:
        games = args.games

    results = []
    for game_id in games:
        r = snapshot_explore(game_id, max_actions=args.max_actions)
        results.append(r)

    print(f"\n{'='*50}")
    print("SNAPSHOT EXPLORER RESULTS")
    print(f"{'='*50}")
    for r in results:
        status = f"L{r['levels']}" if r['levels'] > 0 else "unsolved"
        print(f"  {r['game_id']}: {status} | {r['total_actions']} actions, "
              f"{r['positive_actions']} positive")
    solved = sum(1 for r in results if r['levels'] > 0)
    print(f"\n  Solved: {solved}/{len(results)}")
