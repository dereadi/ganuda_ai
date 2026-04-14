#!/usr/bin/env python3
"""
Fibonacci Snapshot Explorer — Multi-Scale State Evaluation

Partner's insight: snapshot at Fibonacci intervals (1, 1, 2, 3, 5, 8, 13, 21).
Some games need 1 action. Some need 2 (paired clicks). Some need 13 (block puzzles).
Fibonacci naturally covers all scales without knowing which one the game needs.

Algorithm:
  1. SNAPSHOT the current state
  2. Play N actions (exploring or 72B-guided)
  3. At each Fibonacci checkpoint, compare to snapshot
  4. If state improved at ANY checkpoint → commit, restart Fibonacci counter
  5. If no improvement by fib(21) → that whole direction is unproductive
  6. Try different action sequences and repeat

The golden ratio meets game-playing. Nature's scaling function for the unknown.
"""

import sys
import os
import re
import logging
import numpy as np
import requests
import random
from typing import List, Optional

sys.path.insert(0, os.path.dirname(__file__))

from arc_agi import Arcade
from arcengine import GameAction, GameState

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(message)s', datefmt='%H:%M:%S')
logger = logging.getLogger(__name__)

VLLM_URL = "http://localhost:8000/v1/chat/completions"
VLLM_MODEL = "/ganuda/models/qwen2.5-72b-instruct-awq"

# Fibonacci sequence — the checkpoints where we evaluate
FIBONACCI = [1, 1, 2, 3, 5, 8, 13, 21, 34]

CHARS = {i: c for i, c in enumerate('.123456789ABCDEF')}


def frame_score(frame: np.ndarray, initial: np.ndarray) -> float:
    """Score a frame by how different it is from the initial state.
    More different = more progress (we've changed the game state)."""
    return float(np.sum(frame != initial)) / frame.size


def frame_diff(a: np.ndarray, b: np.ndarray) -> float:
    """Fraction of pixels that differ between two frames."""
    return float(np.sum(a != b)) / a.size


def render_grid(frame: np.ndarray) -> str:
    bg = int(np.median(frame))
    bg_c = CHARS.get(bg, '_')
    lines = []
    for y in range(frame.shape[0]):
        row = ''.join(CHARS.get(frame[y][x], '?') for x in range(frame.shape[1]))
        if any(c != bg_c for c in row):
            lines.append(f'R{y:02d} {row}')
    return '\n'.join(lines)


def get_72b_actions(frame, available):
    """Ask 72B for initial action suggestions."""
    grid = render_grid(frame)
    action_names = [f'ACTION{a}' for a in available]
    prompt = f"""64x64 grid puzzle. Actions: {', '.join(action_names)}.
1-4=arrows, 5=confirm, 6=click(x,y), 7=click2(x,y).

{grid[:2000]}

List 30 specific actions to try. One per line.
CLICK x y / UP / DOWN / LEFT / RIGHT / CONFIRM / ACTION7 x y"""

    try:
        resp = requests.post(VLLM_URL, json={
            'model': VLLM_MODEL,
            'messages': [{'role': 'user', 'content': prompt}],
            'max_tokens': 400, 'temperature': 0.3,
        }, timeout=25)
        text = resp.json()['choices'][0]['message']['content']
        return parse_actions(text, available)
    except:
        return []


def parse_actions(text, available):
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
        if re.search(r'\bUP\b', line) and 1 in available: actions.append(('UP',))
        elif re.search(r'\bDOWN\b', line) and 2 in available: actions.append(('DOWN',))
        elif re.search(r'\bLEFT\b', line) and 3 in available: actions.append(('LEFT',))
        elif re.search(r'\bRIGHT\b', line) and 4 in available: actions.append(('RIGHT',))
        elif re.search(r'\bCONFIRM\b', line) and 5 in available: actions.append(('CONFIRM',))
    return actions


def execute(env, act):
    if act[0] == 'CLICK':
        a = GameAction.ACTION6; a.set_data({'x': act[1], 'y': act[2]})
        return env.step(a, data={'x': act[1], 'y': act[2]}, reasoning={})
    elif act[0] == 'ACTION7':
        a = GameAction.ACTION7; a.set_data({'x': act[1], 'y': act[2]})
        return env.step(a, data={'x': act[1], 'y': act[2]}, reasoning={})
    elif act[0] == 'UP': return env.step(GameAction.ACTION1, data={}, reasoning={})
    elif act[0] == 'DOWN': return env.step(GameAction.ACTION2, data={}, reasoning={})
    elif act[0] == 'LEFT': return env.step(GameAction.ACTION3, data={}, reasoning={})
    elif act[0] == 'RIGHT': return env.step(GameAction.ACTION4, data={}, reasoning={})
    elif act[0] == 'CONFIRM': return env.step(GameAction.ACTION5, data={}, reasoning={})
    return None


def generate_action_sequences(available, count=20, max_len=21):
    """Generate diverse action sequences for Fibonacci exploration."""
    simple = []
    if 1 in available: simple.append(('UP',))
    if 2 in available: simple.append(('DOWN',))
    if 3 in available: simple.append(('LEFT',))
    if 4 in available: simple.append(('RIGHT',))
    if 5 in available: simple.append(('CONFIRM',))

    sequences = []
    for _ in range(count):
        seq = [random.choice(simple) for _ in range(max_len)]
        sequences.append(seq)

    # Add some structured sequences
    if simple:
        # Repeat each direction
        for d in simple:
            sequences.append([d] * max_len)
        # Alternating pairs
        for i in range(len(simple)):
            for j in range(i+1, len(simple)):
                seq = []
                for k in range(max_len):
                    seq.append(simple[i] if k % 2 == 0 else simple[j])
                sequences.append(seq)

    return sequences


def fibonacci_explore(game_id: str, max_total_actions: int = 500,
                      use_72b: bool = True) -> dict:
    """
    Fibonacci Snapshot Explorer.

    For each action sequence:
      1. Take snapshot
      2. Execute actions one by one
      3. At Fibonacci checkpoints (1, 1, 2, 3, 5, 8, 13, 21), evaluate
      4. If state improved → commit snapshot, restart
      5. If no improvement by end → discard, try next sequence
    """
    arcade = Arcade()
    env = arcade.make(game_id)
    obs = env.observation_space
    available = obs.available_actions

    initial_frame = np.array(obs.frame[-1], dtype=np.uint8)
    current_frame = initial_frame.copy()
    best_score = 0.0
    total_actions = 0
    levels = 0
    committed_improvements = 0

    logger.info(f"{game_id}: Fibonacci Explorer (actions: {available})")

    # Get action suggestions from 72B
    guided_actions = []
    if use_72b:
        logger.info("  72B generating action suggestions...")
        guided_actions = get_72b_actions(initial_frame, available)
        logger.info(f"  72B suggested {len(guided_actions)} actions")

    # Generate random action sequences
    random_sequences = generate_action_sequences(available, count=30)

    # Build sequences to try: 72B-guided first, then random
    all_sequences = []
    if guided_actions:
        # Break 72B actions into chunks aligned with Fibonacci
        for fib_len in FIBONACCI:
            for start in range(0, len(guided_actions), fib_len):
                chunk = guided_actions[start:start + fib_len]
                if chunk:
                    all_sequences.append(chunk)
    all_sequences.extend(random_sequences)

    for seq_idx, sequence in enumerate(all_sequences):
        if total_actions >= max_total_actions:
            break

        # SNAPSHOT before this sequence
        snapshot = current_frame.copy()
        snapshot_score = frame_score(snapshot, initial_frame)

        actions_in_seq = 0
        fib_idx = 0
        next_checkpoint = FIBONACCI[0]
        best_checkpoint_frame = None
        best_checkpoint_score = snapshot_score
        best_checkpoint_actions = 0

        for act in sequence:
            if total_actions >= max_total_actions:
                break

            raw = execute(env, act)
            if raw is None:
                continue
            total_actions += 1
            actions_in_seq += 1

            new_frame = np.array(raw.frame[-1], dtype=np.uint8)

            # Check for level completion
            if raw.levels_completed > levels:
                levels = raw.levels_completed
                current_frame = new_frame
                logger.info(f"  LEVEL {levels} SOLVED at action {total_actions}!")
                if 5 in available:
                    raw2 = env.step(GameAction.ACTION5, data={}, reasoning={})
                    total_actions += 1
                    if raw2.levels_completed > levels:
                        levels = raw2.levels_completed
                    new_frame = np.array(raw2.frame[-1], dtype=np.uint8)
                    current_frame = new_frame
                break

            if raw.state == GameState.GAME_OVER:
                env.step(GameAction.RESET, data={}, reasoning={})
                total_actions += 1
                obs2 = env.observation_space
                current_frame = np.array(obs2.frame[-1], dtype=np.uint8)
                break

            # FIBONACCI CHECKPOINT
            if actions_in_seq >= next_checkpoint:
                score = frame_score(new_frame, initial_frame)

                if score > best_checkpoint_score + 0.001:
                    best_checkpoint_score = score
                    best_checkpoint_frame = new_frame.copy()
                    best_checkpoint_actions = actions_in_seq

                # Advance to next Fibonacci number
                fib_idx += 1
                if fib_idx < len(FIBONACCI):
                    next_checkpoint = sum(FIBONACCI[:fib_idx + 1])
                else:
                    break  # Exhausted Fibonacci sequence

            current_frame = new_frame

        # After sequence: did any Fibonacci checkpoint show improvement?
        if best_checkpoint_frame is not None and best_checkpoint_score > best_score + 0.001:
            best_score = best_checkpoint_score
            committed_improvements += 1
            logger.info(f"  Seq {seq_idx}: +{best_checkpoint_score:.4f} at fib checkpoint "
                       f"{best_checkpoint_actions} (total: {total_actions})")

    result = {
        'game_id': game_id,
        'levels': levels,
        'total_actions': total_actions,
        'best_score': round(best_score, 4),
        'committed_improvements': committed_improvements,
    }
    logger.info(f"  Result: {levels} levels, {total_actions} actions, "
               f"score={best_score:.4f}, {committed_improvements} improvements")
    return result


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('games', nargs='*', default=['re86'])
    parser.add_argument('--all-unsolved', action='store_true')
    parser.add_argument('--max-actions', type=int, default=500)
    parser.add_argument('--no-llm', action='store_true')
    args = parser.parse_args()

    if args.all_unsolved:
        games = ['sc25', 'ka59', 'lf52', 're86', 'dc22', 'wa30', 'g50t']
    else:
        games = args.games

    results = []
    for gid in games:
        r = fibonacci_explore(gid, max_total_actions=args.max_actions,
                             use_72b=not args.no_llm)
        results.append(r)

    print(f"\n{'='*50}")
    print("FIBONACCI EXPLORER RESULTS")
    print(f"{'='*50}")
    for r in results:
        status = f"L{r['levels']}" if r['levels'] > 0 else f"score={r['best_score']}"
        print(f"  {r['game_id']}: {status} | {r['total_actions']} actions, "
              f"{r['committed_improvements']} improvements")
    solved = sum(1 for r in results if r['levels'] > 0)
    print(f"\n  Solved: {solved}/{len(results)}")
