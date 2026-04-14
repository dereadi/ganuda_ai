"""
ARC-AGI-3 Experience Bank — Cross-Attempt Learning via Thermal Memory

After each failed attempt at a level, store what happened and what was learned.
Before each new attempt, retrieve relevant experiences to inform the strategy.

This is the "learn continuously" capability Chollet says is missing from frontier AI.
The thermal memory substrate (PostgreSQL + pgvector) provides the persistence.
The CRAG + ripple expansion provides the retrieval quality.

Without this: Jr + Council both latch onto "go to target" and can't deviate (Chollet failure mode #2).
With this: failed attempt teaches "block requires icon match → visit + first" → next attempt succeeds.
"""

import json
import psycopg2
import os
from datetime import datetime


def get_db_connection():
    """Connect to the thermal memory database."""
    return psycopg2.connect(
        host=os.environ.get('CHEROKEE_DB_HOST', '10.100.0.2'),
        database='triad_federation',
        user='claude',
        password=os.environ.get('CHEROKEE_DB_PASS', ''),
        connect_timeout=5
    )


def store_attempt_experience(task_id: str, level: str, move_history: list,
                              final_position: dict, outcome: str,
                              learned: str, game_state_summary: str = ""):
    """Store what happened in a failed (or successful) attempt.

    This is the WRITE side of the Experience Bank.
    After each attempt, we store:
    - What level and task we were playing
    - The move sequence
    - Where we ended up
    - Whether we solved it or why we failed
    - What we LEARNED (the key insight for next attempt)

    Args:
        task_id: e.g., "ls20"
        level: e.g., "Level 1 / 7"
        move_history: list of direction strings
        final_position: {x, y} of where the player ended
        outcome: "solved", "fuel_depleted", "max_moves", "stuck"
        learned: human-readable lesson, e.g., "block requires icon match, visit + first"
        game_state_summary: optional summary of the game state at failure
    """
    content = f"""ARC-AGI-3 GAME EXPERIENCE — {task_id} {level}

OUTCOME: {outcome}
MOVES: {len(move_history)} total
FINAL POSITION: ({final_position.get('x', '?')}, {final_position.get('y', '?')})
MOVE SEQUENCE: {' '.join(move_history)}

GAME STATE AT END:
{game_state_summary}

LESSON LEARNED:
{learned}

STRATEGY FOR NEXT ATTEMPT:
Based on this experience, on the next attempt at this level:
{learned}
"""

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO triad_shared_memories
            (content, temperature, source_triad, tags, access_level, node_id)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            content,
            85.0,  # Warm — game experience, not sacred
            'arc_agi_3_agent',
            ['arc_agi_3', 'game_experience', f'task_{task_id}',
             f'level_{level.replace(" ", "_").replace("/", "_")}',
             outcome, 'experience_bank'],
            'public',
            'redfin'
        ))
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"  [!] Experience Bank write failed: {e}")
        return False


def retrieve_experiences(task_id: str, level: str, game_state: dict, limit: int = 5) -> str:
    """Retrieve relevant past experiences for the current game state.

    This is the READ side of the Experience Bank.
    Before making a move, we check: have we been in a similar situation before?
    What did we learn?

    Returns a formatted string to inject into the Jr/Council prompt.
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Query for experiences from this task and level
        cur.execute("""
            SELECT content, temperature, created_at
            FROM triad_shared_memories
            WHERE 'arc_agi_3' = ANY(tags)
              AND 'game_experience' = ANY(tags)
              AND (content ILIKE %s OR content ILIKE %s)
            ORDER BY created_at DESC
            LIMIT %s
        """, (
            f'%{task_id}%',
            f'%{level}%',
            limit
        ))

        rows = cur.fetchall()
        cur.close()
        conn.close()

        if not rows:
            return ""

        # Format experiences for prompt injection
        experiences = []
        for content, temp, created_at in rows:
            # Extract just the LESSON LEARNED section
            lesson_start = content.find('LESSON LEARNED:')
            strategy_start = content.find('STRATEGY FOR NEXT ATTEMPT:')
            outcome_start = content.find('OUTCOME:')

            lesson = ""
            if lesson_start >= 0 and strategy_start >= 0:
                lesson = content[lesson_start:strategy_start].strip()
            elif lesson_start >= 0:
                lesson = content[lesson_start:lesson_start + 300].strip()

            outcome = ""
            if outcome_start >= 0:
                outcome_end = content.find('\n', outcome_start)
                outcome = content[outcome_start:outcome_end].strip() if outcome_end > 0 else ""

            experiences.append(f"[{created_at}] {outcome}\n{lesson}")

        header = f"\n=== EXPERIENCE BANK: {len(experiences)} past attempts at {task_id} {level} ===\n"
        return header + "\n---\n".join(experiences) + "\n=== END EXPERIENCES ===\n"

    except Exception as e:
        print(f"  [!] Experience Bank read failed: {e}")
        return ""


def analyze_failure(move_history: list, game_state: dict, level: str) -> str:
    """Auto-generate a lesson learned from a failed attempt.

    Analyzes the move history and game state to determine what went wrong.
    This is the LEARNING part — converting raw play data into actionable insight.
    """
    pos = game_state.get('player', {})
    blocks = game_state.get('gameBlocks', [])
    plus = game_state.get('plusPositions', [])
    fuel = game_state.get('fuelBar', 0)

    lessons = []

    # Check if we visited the + icon switcher
    # The + is usually the key that gets skipped
    if plus:
        plus_pos = plus[0]
        # Check if any move in the history brought us near the +
        # Simple heuristic: if all moves went in one direction toward the block
        # and we never deviated toward the +, that's the lesson
        up_count = move_history.count('up')
        total = len(move_history)
        if up_count > total * 0.6:
            lessons.append(
                f"Went straight toward the block without visiting the plus icon switcher at "
                f"({plus_pos.get('x')}, {plus_pos.get('y')}). "
                f"The block likely requires an icon match before it can be entered. "
                f"On next attempt: visit the + FIRST to cycle the icon, THEN approach the block."
            )

    # Check if we got stuck at one position
    if len(move_history) > 5:
        # Count how many of the last N moves were stuck (×)
        # We don't have stuck info here, but if the same position repeated,
        # the move_history would show repeated directions
        last_moves = move_history[-10:]
        unique_moves = set(last_moves)
        if len(unique_moves) <= 2 and len(last_moves) >= 8:
            lessons.append(
                f"Got stuck oscillating between {unique_moves} directions. "
                f"This usually means the current approach is fundamentally wrong, "
                f"not just slightly off. Try a completely different strategy."
            )

    # Check fuel efficiency
    if fuel <= 3:
        lessons.append(
            f"Ran out of fuel with {fuel} remaining. "
            f"Route was not fuel-efficient. On next attempt, plan the route "
            f"to minimize wasted moves (wall hits cost fuel)."
        )

    # Check if fuel pickups exist and were not collected
    fuel_pickups = game_state.get('fuelPickups', [])
    if fuel_pickups and fuel < 10:
        lessons.append(
            f"Fuel pickups exist on the board at {[(p.get('x'), p.get('y')) for p in fuel_pickups[:3]]} "
            f"but were not collected. On next attempt, route through fuel pickups if needed."
        )

    if not lessons:
        lessons.append("Attempt failed for unclear reasons. Try a different approach entirely.")

    return " ".join(lessons)
