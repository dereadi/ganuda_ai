#!/usr/bin/env python3
"""
ARC-AGI-3 Agent — Bilateral Coordinated Tribal Intelligence

The main agent loop that connects perception (canvas reading),
deliberation (specialist Council), memory (thermal Experience Bank),
and action (Playwright keyboard) into a governed game-playing agent.

Usage:
    python agent.py                    # Play task ls20 with Council deliberation
    python agent.py --task ls25        # Different task
    python agent.py --manual           # Manual mode (TPM drives, no Council)
    python agent.py --levels 3         # Stop after N levels

For Seven Generations
"""

import argparse
import sys
import json
import time
from datetime import datetime

sys.path.insert(0, '/ganuda')
sys.path.insert(0, '/ganuda/lib')

from game import ArcGame
from perception import READ_GAME_STATE_JS, render_ascii_grid


def deliberate_move(game_state, level, move_history, experience=None):
    """Ask the specialist Council for the next move.

    This is where the bilateral-hemisphere architecture activates:
    the perception layer (canvas reading) produces structured text,
    which the Council (on bmasass) deliberates over, producing a
    governed move decision.

    Falls back to heuristic if Council is unavailable.
    """
    try:
        from specialist_council import council_vote

        # Build the question for the Council
        pos = game_state.get('player', {})
        fuel = game_state.get('fuelBar', 0)
        blocks = game_state.get('gameBlocks', [])
        plus = game_state.get('plusPositions', [])
        pickups = game_state.get('fuelPickups', [])

        question = f"""ARC-AGI-3 MOVE DECISION — {level}

Player position: ({pos.get('x')}, {pos.get('y')})
Fuel remaining: {fuel}
Blue blocks (targets): {json.dumps(blocks[:6])}
Plus (+) positions: {json.dumps(plus[:4])}
Fuel pickups on board: {json.dumps(pickups[:4])}
Move history (last 10): {move_history[-10:]}
Total moves so far: {len(move_history)}

The game is a grid puzzle. The player slides when you press an arrow key.
Match icon at + then walk over the blue block to advance.
Yellow pickups refuel.

What direction should the player move next: up, down, left, or right?
Give ONE direction and a brief reason."""

        result = council_vote(question, max_tokens=100, include_responses=False)

        # Parse the Council's response for a direction
        response = result.get('consensus', '').lower()
        for direction in ['up', 'down', 'left', 'right']:
            if direction in response:
                return direction, f"Council: {result.get('consensus', '')[:100]}"

        # If Council didn't give a clear direction, fall through to heuristic
        return heuristic_move(game_state, move_history), "Council unclear, using heuristic"

    except Exception as e:
        return heuristic_move(game_state, move_history), f"Council unavailable ({e}), using heuristic"


    # Known-good paths for solved levels (discovered during dry run Apr 12 2026)
KNOWN_PATHS = {
    'Level 1 / 7': ['left', 'left', 'left', 'up', 'up', 'up', 'right', 'up', 'right', 'right', 'right', 'up', 'up', 'up'],
}


def heuristic_move(game_state, move_history):
    """Reactive heuristic fallback when Council is unavailable.

    Strategy:
    - Navigate to + first (cycle icon), then to the block
    - Detect when stuck (same position after move) and try alternate directions
    - Uses the known-good Level 1 path structure as a guide
    """
    pos = game_state.get('player', {})
    px, py = pos.get('x', 17), pos.get('y', 22)
    plus = game_state.get('plusPositions', [])
    blocks = game_state.get('gameBlocks', [])
    directions = ['left', 'up', 'right', 'down']

    # Detect stuck state — if last 2+ moves were the same direction and we haven't moved
    # (caller tracks position; we detect from history patterns)
    stuck_direction = None
    if len(move_history) >= 3:
        last3 = move_history[-3:]
        if last3[0] == last3[1] == last3[2]:
            stuck_direction = last3[0]

    # Phase 1: Navigate to + (icon switcher)
    if plus:
        target = plus[0]
        tx, ty = target.get('x', 10), target.get('y', 15)
        visited_plus = any(m == 'visited_plus' for m in move_history)

        if not visited_plus:
            # Priority order for reaching +, skipping stuck directions
            candidates = []
            if px > tx + 1:
                candidates.append('left')
            if py > ty + 1:
                candidates.append('up')
            if px < tx - 1:
                candidates.append('right')
            if py < ty - 1:
                candidates.append('down')

            # If near + on the x-axis, try right to walk through it
            if abs(px - tx) <= 2 and abs(py - ty) <= 1:
                candidates = ['right', 'left']  # Walk through +

            # Filter out stuck direction
            if stuck_direction:
                candidates = [c for c in candidates if c != stuck_direction]
                if not candidates:
                    # All primary directions stuck — try perpendicular
                    if stuck_direction in ('up', 'down'):
                        candidates = ['left', 'right']
                    else:
                        candidates = ['up', 'down']

            return candidates[0] if candidates else directions[len(move_history) % 4]

    # Phase 2: Navigate to block after visiting +
    if blocks:
        top_blocks = [b for b in blocks if b.get('y', 99) < 15]
        target = top_blocks[0] if top_blocks else blocks[0]
        tx, ty = target.get('x', 17), target.get('y', 5)

        candidates = []
        if py > ty + 1:
            candidates.append('up')
        if px < tx - 1:
            candidates.append('right')
        if px > tx + 1:
            candidates.append('left')
        if py < ty - 1:
            candidates.append('down')

        # Filter stuck
        if stuck_direction:
            candidates = [c for c in candidates if c != stuck_direction]
            if not candidates:
                if stuck_direction in ('up', 'down'):
                    candidates = ['right', 'left']
                else:
                    candidates = ['up', 'down']

        return candidates[0] if candidates else 'up'

    # Default: cycle through directions
    return directions[len(move_history) % 4]


def play_level(game: ArcGame, max_moves: int = 100, use_council: bool = True) -> dict:
    """Play one level of the game.

    Returns:
        dict with level result, move count, and history
    """
    start_level = game.get_level()
    move_history = []
    position_history = []
    stuck_counter = 0
    start_time = time.time()

    # Reset plan tracker state for new level
    try:
        from planner import reset_plan
        reset_plan()
    except ImportError:
        pass

    # Experience Bank: retrieve past experiences for this level
    experience_context = ""
    try:
        from experience import retrieve_experiences
        experience_context = retrieve_experiences(game.task_id, start_level, {})
        if experience_context:
            print(f"\n  📚 Experience Bank: retrieved past attempts for {start_level}")
    except ImportError:
        pass

    print(f"\n{'='*50}")
    print(f"PLAYING: {start_level}")
    if experience_context:
        print(f"  [EXPERIENCE] {experience_context[:200]}...")
    print(f"{'='*50}")

    for i in range(max_moves):
        # 1. PERCEIVE — read game state from canvas
        state = game.get_game_state()
        if not state or 'error' in state:
            print(f"  [!] Perception error: {state}")
            continue

        pos = state.get('player', {})
        fuel = state.get('fuelBar', 0)

        # 2. DELIBERATE — choose a move
        if use_council:
            # Plan Tracker → Jr → Council (graduated autonomy with experience-informed planning)
            try:
                from planner import get_current_step
                plan_step = get_current_step(state, start_level, experience_context)

                if not plan_step.get('use_jr') and plan_step.get('direction'):
                    # Plan tracker has a clear step — execute directly
                    direction = plan_step['direction']
                    reason = f"[plan] {plan_step['reason']}"
                else:
                    # Plan tracker defers to Jr/Council graduated autonomy
                    from deliberation import graduated_decide
                    direction, reason, tier = graduated_decide(
                        state, start_level, move_history,
                        stuck_count=stuck_counter,
                        last_positions=position_history[-8:]
                    )
                    reason = f"[{tier}] {reason}"
            except ImportError:
                direction, reason = deliberate_move(state, start_level, move_history)
        else:
            # Manual mode: plan tracker + heuristic fallback (no Council/Jr LLM)
            try:
                from planner import get_current_step
                plan_step = get_current_step(state, start_level, experience_context)

                if not plan_step.get('use_jr') and plan_step.get('direction'):
                    direction = plan_step['direction']
                    reason = f"[plan] {plan_step['reason']}"
                else:
                    # Plan deferred — check known path, then heuristic
                    level_key = start_level
                    if level_key in KNOWN_PATHS and len(move_history) < len(KNOWN_PATHS[level_key]):
                        direction = KNOWN_PATHS[level_key][len(move_history)]
                        reason = f"known path step {len(move_history)+1}/{len(KNOWN_PATHS[level_key])}"
                    else:
                        direction = heuristic_move(state, move_history)
                        reason = f"[heuristic] {plan_step.get('reason', '')}"
            except ImportError:
                direction = heuristic_move(state, move_history)
                reason = "heuristic"

        # 3. ACT — execute the move
        new_pos = game.move(direction)

        # 4. OBSERVE — check result
        if new_pos is None:
            new_pos = pos  # Position read failed, assume unchanged
        new_level = game.get_level()
        moved = (new_pos.get('x') != pos.get('x') or new_pos.get('y') != pos.get('y')) if new_pos and pos else False

        move_history.append(direction)
        position_history.append(new_pos)

        # Track stuck state
        if not moved:
            stuck_counter += 1
        else:
            stuck_counter = 0

        # Print move (compact)
        status = "→" if moved else "×"
        print(f"  {i+1:3d}. {direction:5s} {status} ({new_pos.get('x','?')},{new_pos.get('y','?')}) fuel={fuel} | {reason[:60]}")

        # Check for level advancement
        if new_level != start_level and start_level.split('/')[0].strip() != new_level.split('/')[0].strip():
            elapsed = time.time() - start_time
            print(f"\n  🎯 LEVEL COMPLETE! {start_level} → {new_level}")
            print(f"     Moves: {len(move_history)} | Time: {elapsed:.1f}s")
            return {
                'solved': True,
                'from_level': start_level,
                'to_level': new_level,
                'moves': len(move_history),
                'history': move_history,
                'elapsed': elapsed,
            }

        # Check for fuel depletion (game auto-resets)
        if fuel <= 0 and i > 5:
            print(f"\n  ⚠️ Fuel depleted at move {i+1}. Level auto-resets.")

            # Experience Bank: store what we learned from this failure
            try:
                from experience import store_attempt_experience, analyze_failure
                lesson = analyze_failure(move_history, state, start_level)
                store_attempt_experience(
                    task_id=game.task_id,
                    level=start_level,
                    move_history=move_history,
                    final_position=new_pos or {'x': '?', 'y': '?'},
                    outcome='fuel_depleted',
                    learned=lesson,
                    game_state_summary=f"Player at ({pos.get('x')},{pos.get('y')}), blocks={len(state.get('gameBlocks', []))}, plus={len(state.get('plusPositions', []))}"
                )
                print(f"  📝 Experience stored: {lesson[:100]}...")
            except Exception as e:
                print(f"  [!] Experience store failed: {e}")

            return {
                'solved': False,
                'from_level': start_level,
                'reason': 'fuel_depleted',
                'moves': len(move_history),
                'history': move_history,
                'elapsed': time.time() - start_time,
            }

    # Experience Bank: store what we learned from max_moves exhaustion
    try:
        from experience import store_attempt_experience, analyze_failure
        last_state = game.get_game_state() or {}
        last_pos = last_state.get('player', {})
        lesson = analyze_failure(move_history, last_state, start_level)
        store_attempt_experience(
            task_id=game.task_id,
            level=start_level,
            move_history=move_history,
            final_position=last_pos or {'x': '?', 'y': '?'},
            outcome='max_moves',
            learned=lesson,
            game_state_summary=f"Player at ({last_pos.get('x','?')},{last_pos.get('y','?')}), blocks={len(last_state.get('gameBlocks', []))}, plus={len(last_state.get('plusPositions', []))}"
        )
        print(f"  📝 Experience stored: {lesson[:100]}...")
    except Exception as e:
        print(f"  [!] Experience store failed: {e}")

    return {
        'solved': False,
        'from_level': start_level,
        'reason': 'max_moves',
        'moves': len(move_history),
        'history': move_history,
        'elapsed': time.time() - start_time,
    }


def main():
    parser = argparse.ArgumentParser(description='ARC-AGI-3 Agent — Ganuda Federation')
    parser.add_argument('--task', default='ls20', help='Task ID (default: ls20)')
    parser.add_argument('--levels', type=int, default=7, help='Max levels to attempt')
    parser.add_argument('--max-moves', type=int, default=100, help='Max moves per level')
    parser.add_argument('--manual', action='store_true', help='Heuristic only, no Council')
    parser.add_argument('--headless', action='store_true', default=True, help='Run headless')
    parser.add_argument('--visible', action='store_true', help='Show browser window')
    args = parser.parse_args()

    headless = not args.visible
    use_council = not args.manual

    print(f"ARC-AGI-3 Agent — Ganuda Federation")
    print(f"Task: {args.task} | Council: {use_council} | Headless: {headless}")
    print(f"Max levels: {args.levels} | Max moves/level: {args.max_moves}")
    print()

    results = []

    with ArcGame(task_id=args.task, headless=headless) as game:
        for level_num in range(args.levels):
            result = play_level(game, max_moves=args.max_moves, use_council=use_council)
            results.append(result)

            if not result['solved']:
                print(f"\n  Level not solved ({result['reason']}). Stopping.")
                break

            # Wait for level transition
            game.page.wait_for_timeout(3000)
            game.page.keyboard.press('Space')
            game.page.wait_for_timeout(2000)

    # Summary
    print(f"\n{'='*50}")
    print(f"SESSION SUMMARY")
    print(f"{'='*50}")
    total_moves = sum(r['moves'] for r in results)
    solved = sum(1 for r in results if r['solved'])
    print(f"Levels solved: {solved}/{len(results)}")
    print(f"Total moves: {total_moves}")
    for r in results:
        status = "✅" if r['solved'] else "❌"
        print(f"  {status} {r.get('from_level', '?')}: {r['moves']} moves, {r.get('elapsed', 0):.1f}s")


if __name__ == '__main__':
    main()
