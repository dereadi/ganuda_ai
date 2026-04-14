"""
ARC-AGI-3 Game Experience Bank — Cross-Game Learning via Thermal Memory

After each game (or game-over), store what the agent learned: which action
patterns worked, what goal types were seen, what CWM accuracy was achieved.
Before starting a new game, retrieve relevant past experiences to seed the
agent's strategy.

This is the structural moat: no other ARC-AGI-3 contestant carries memory
across games. The thermal memory substrate (PostgreSQL + pgvector on
10.100.0.2) provides persistence; local JSON fallback when DB is unreachable.

Council vote: SkillRL Experience Bank #fb526dd2212e09a7 APPROVED.
"""

import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DB_HOST = os.environ.get('CHEROKEE_DB_HOST', '10.100.0.2')
DB_NAME = 'triad_federation'
DB_USER = 'claude'
DB_PASS = os.environ.get('CHEROKEE_DB_PASS', '')
DB_TIMEOUT = 5

LOCAL_EXPERIENCE_DIR = Path(__file__).parent / 'experiences'

SOURCE_TRIAD = 'arc_agi_3_agent'
NODE_ID = os.environ.get('GANUDA_NODE_ID', 'redfin')
DEFAULT_TEMPERATURE = 80.0


# ---------------------------------------------------------------------------
# DB helpers (mirrors experience.py pattern)
# ---------------------------------------------------------------------------

def _get_db_connection():
    """Connect to the thermal memory database. Returns None if unavailable."""
    try:
        import psycopg2
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            connect_timeout=DB_TIMEOUT,
        )
        return conn
    except Exception as e:
        logger.warning(f"DB connection failed (will use local fallback): {e}")
        return None


def _ensure_local_dir():
    """Create the local experience directory if it doesn't exist."""
    LOCAL_EXPERIENCE_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# 1. Game Signature Extraction
# ---------------------------------------------------------------------------

def extract_game_signature(game_id: str, agent_state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build a structured signature of a completed game session.

    Args:
        game_id: the game identifier (e.g. 'ls20', 'puzzle_42')
        agent_state: dictionary containing agent runtime data:
            - world_model_status: dict from CodeWorldModel.status()
            - goal_inferrer_status: dict from GoalInferrer.status()
            - action_count: int total actions taken
            - levels_completed: int
            - action_history: list of action name strings (optional)
            - level_up_actions: list of (action_index, action_name) at level-up (optional)
            - frame_characteristics: dict with dominant_colors, object_count_range,
              grid_size, has_grid_pattern (optional, extracted from FrameProcessor)
            - unique_states: int count of unique frame hashes seen (optional)
            - outcome: 'win', 'game_over', 'timeout', 'unknown'

    Returns:
        Structured signature dict.
    """
    wm = agent_state.get('world_model_status', {})
    gi = agent_state.get('goal_inferrer_status', {})
    action_history = agent_state.get('action_history', [])
    level_up_actions = agent_state.get('level_up_actions', [])
    frame_chars = agent_state.get('frame_characteristics', {})

    # Determine action type classification
    action_type = _classify_action_types(action_history)

    # Extract action patterns that led to level-ups
    level_up_patterns = _extract_level_up_patterns(action_history, level_up_actions)

    # Goal hypothesis summary
    hypotheses_summary = []
    raw_hypotheses = gi.get('hypotheses', [])
    for h in raw_hypotheses:
        if isinstance(h, dict):
            hypotheses_summary.append({
                'category': h.get('category', 'unknown'),
                'confidence': h.get('confidence', 0.0),
                'description': h.get('description', '')[:120],
            })
        elif hasattr(h, 'category'):
            hypotheses_summary.append({
                'category': h.category,
                'confidence': h.confidence,
                'description': h.description[:120],
            })

    return {
        'game_id': game_id,
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'outcome': agent_state.get('outcome', 'unknown'),
        'action_type': action_type,
        'action_count': agent_state.get('action_count', 0),
        'levels_completed': agent_state.get('levels_completed', 0),
        'unique_states': agent_state.get('unique_states', 0),
        'frame_characteristics': {
            'dominant_colors': frame_chars.get('dominant_colors', []),
            'object_count_range': frame_chars.get('object_count_range', [0, 0]),
            'grid_size': frame_chars.get('grid_size', [0, 0]),
            'has_grid_pattern': frame_chars.get('has_grid_pattern', False),
        },
        'cwm': {
            'transitions_collected': wm.get('transitions_collected', 0),
            'synthesis_attempts': wm.get('synthesis_attempts', 0),
            'synthesis_successes': wm.get('synthesis_successes', 0),
            'model_ready': wm.get('model_ready', False),
            'accuracy': wm.get('accuracy', 0.0),
        },
        'goal_hypotheses': hypotheses_summary,
        'level_up_patterns': level_up_patterns,
    }


def _classify_action_types(action_history: List[str]) -> str:
    """
    Classify the game's action type from the history of action names.

    Returns one of: 'keyboard', 'click', 'keyboard_click', 'unknown'.
    """
    if not action_history:
        return 'unknown'

    keyboard_actions = {'ACTION1', 'ACTION2', 'ACTION3', 'ACTION4', 'ACTION5'}
    click_actions = {'ACTION6'}

    has_keyboard = any(a in keyboard_actions for a in action_history)
    has_click = any(a in click_actions for a in action_history)

    if has_keyboard and has_click:
        return 'keyboard_click'
    elif has_keyboard:
        return 'keyboard'
    elif has_click:
        return 'click'
    return 'unknown'


def _extract_level_up_patterns(
    action_history: List[str],
    level_up_actions: List,
) -> List[Dict[str, Any]]:
    """
    Extract the action sequences that preceded each level-up event.

    Returns a list of pattern dicts, one per level-up.
    """
    patterns = []
    WINDOW = 20  # look back 20 actions before each level-up

    for entry in level_up_actions:
        if isinstance(entry, (list, tuple)) and len(entry) >= 2:
            idx, action_name = entry[0], entry[1]
        elif isinstance(entry, dict):
            idx = entry.get('action_index', 0)
            action_name = entry.get('action_name', 'unknown')
        else:
            continue

        start = max(0, idx - WINDOW)
        window = action_history[start:idx + 1] if idx < len(action_history) else []

        # Count action frequencies in the window
        freq = {}
        for a in window:
            freq[a] = freq.get(a, 0) + 1

        # Detect repeated subsequences (simple bigram check)
        bigrams = {}
        for i in range(len(window) - 1):
            pair = f"{window[i]}->{window[i+1]}"
            bigrams[pair] = bigrams.get(pair, 0) + 1

        dominant_bigram = max(bigrams, key=bigrams.get) if bigrams else None

        patterns.append({
            'level_up_at_action': idx,
            'trigger_action': action_name,
            'window_size': len(window),
            'action_frequencies': freq,
            'dominant_sequence': dominant_bigram,
        })

    return patterns


# ---------------------------------------------------------------------------
# 2. Experience Storage
# ---------------------------------------------------------------------------

def _signature_to_content(sig: Dict[str, Any]) -> str:
    """Format a game signature as structured text for thermal memory storage."""
    lines = [
        f"ARC-AGI-3 GAME EXPERIENCE — {sig['game_id']}",
        f"Timestamp: {sig['timestamp']}",
        f"Outcome: {sig['outcome']}",
        "",
        "== GAME SIGNATURE ==",
        f"Action Type: {sig['action_type']}",
        f"Total Actions: {sig['action_count']}",
        f"Levels Completed: {sig['levels_completed']}",
        f"Unique States Discovered: {sig['unique_states']}",
        "",
        "== FRAME CHARACTERISTICS ==",
        f"Dominant Colors: {', '.join(str(c) for c in sig['frame_characteristics'].get('dominant_colors', []))}",
        f"Object Count Range: {sig['frame_characteristics'].get('object_count_range', [0, 0])}",
        f"Grid Size: {sig['frame_characteristics'].get('grid_size', [0, 0])}",
        f"Has Grid Pattern: {sig['frame_characteristics'].get('has_grid_pattern', False)}",
        "",
        "== CWM (CODE WORLD MODEL) ==",
        f"Transitions Collected: {sig['cwm']['transitions_collected']}",
        f"Synthesis Attempts: {sig['cwm']['synthesis_attempts']}",
        f"Synthesis Successes: {sig['cwm']['synthesis_successes']}",
        f"Model Ready: {sig['cwm']['model_ready']}",
        f"Accuracy: {sig['cwm']['accuracy']:.2%}" if sig['cwm']['accuracy'] else "Accuracy: N/A",
        "",
        "== GOAL HYPOTHESES ==",
    ]

    if sig['goal_hypotheses']:
        for i, h in enumerate(sig['goal_hypotheses']):
            lines.append(
                f"  {i+1}. [{h['category']}] (conf={h['confidence']:.2f}) {h['description']}"
            )
    else:
        lines.append("  No hypotheses generated.")

    lines.append("")
    lines.append("== LEVEL-UP PATTERNS ==")

    if sig['level_up_patterns']:
        for i, p in enumerate(sig['level_up_patterns']):
            lines.append(f"  Level-up #{i+1} at action {p['level_up_at_action']}:")
            lines.append(f"    Trigger: {p['trigger_action']}")
            lines.append(f"    Window: {p['window_size']} actions")
            if p.get('dominant_sequence'):
                lines.append(f"    Dominant sequence: {p['dominant_sequence']}")
            lines.append(f"    Action mix: {p['action_frequencies']}")
    else:
        lines.append("  No level-ups recorded.")

    lines.append("")
    lines.append("== STRATEGY NOTES ==")

    # Auto-generate strategy notes from the signature
    notes = _generate_strategy_notes(sig)
    for note in notes:
        lines.append(f"  - {note}")

    return "\n".join(lines)


def _generate_strategy_notes(sig: Dict[str, Any]) -> List[str]:
    """Auto-generate strategy notes from the game signature."""
    notes = []
    action_type = sig['action_type']
    outcome = sig['outcome']
    cwm = sig['cwm']
    levels = sig['levels_completed']
    actions = sig['action_count']

    # Action type insight
    if action_type == 'keyboard':
        notes.append("This game uses keyboard-only controls (arrow keys / ACTION1-5).")
    elif action_type == 'click':
        notes.append("This game uses click-only controls (clicking on objects).")
    elif action_type == 'keyboard_click':
        notes.append("This game uses BOTH keyboard and click controls.")

    # Efficiency
    if levels > 0 and actions > 0:
        ratio = actions / levels
        notes.append(f"Averaged {ratio:.0f} actions per level.")
        if ratio < 20:
            notes.append("Efficient play — short action sequences solve levels.")
        elif ratio > 200:
            notes.append("High action count per level — game may require extensive exploration.")

    # CWM effectiveness
    if cwm['synthesis_successes'] > 0:
        notes.append(
            f"CWM synthesis succeeded ({cwm['synthesis_successes']}/{cwm['synthesis_attempts']} attempts, "
            f"accuracy={cwm['accuracy']:.0%}). Model-based planning was available."
        )
    elif cwm['synthesis_attempts'] > 0:
        notes.append(
            f"CWM synthesis failed all {cwm['synthesis_attempts']} attempts. "
            "Game rules may be too complex for single-shot synthesis. "
            "Rely on graph explorer."
        )
    elif cwm['transitions_collected'] < 20:
        notes.append(
            f"Only {cwm['transitions_collected']} transitions collected — "
            "not enough for CWM synthesis. Game may have few distinct states."
        )

    # Outcome
    if outcome == 'win':
        notes.append("GAME WON. Strategies used here should be replicated for similar games.")
    elif outcome == 'game_over':
        notes.append("Game ended in GAME_OVER. Consider different exploration strategy.")
    elif outcome == 'timeout':
        notes.append("Hit action limit / timeout. Need faster convergence.")

    # Goal type insight
    if sig['goal_hypotheses']:
        top = sig['goal_hypotheses'][0]
        notes.append(
            f"Top goal hypothesis: [{top['category']}] — {top['description']}"
        )

    # Level-up patterns
    for p in sig.get('level_up_patterns', []):
        if p.get('dominant_sequence'):
            notes.append(
                f"Level-up pattern: dominant sequence was {p['dominant_sequence']}."
            )

    return notes


def _build_tags(sig: Dict[str, Any]) -> List[str]:
    """Build the tag list for thermal memory storage."""
    tags = [
        'arc_agi_3',
        'game_experience',
        f"game_{sig['game_id']}",
        f"action_{sig['action_type']}",
        sig['outcome'],
    ]

    # Add goal category tags
    for h in sig.get('goal_hypotheses', []):
        cat = h.get('category', '')
        if cat and cat != 'unknown':
            tag = f"goal_{cat}"
            if tag not in tags:
                tags.append(tag)

    # CWM success tag
    if sig['cwm'].get('model_ready'):
        tags.append('cwm_success')
    elif sig['cwm'].get('synthesis_attempts', 0) > 0:
        tags.append('cwm_failed')

    return tags


def _store_to_db(content: str, tags: List[str]) -> bool:
    """Store experience to thermal memory DB. Returns True on success."""
    conn = _get_db_connection()
    if conn is None:
        return False

    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO triad_shared_memories
            (content, temperature, source_triad, tags, access_level, node_id)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            content,
            DEFAULT_TEMPERATURE,
            SOURCE_TRIAD,
            tags,
            'public',
            NODE_ID,
        ))
        conn.commit()
        cur.close()
        conn.close()
        logger.info(f"Experience stored to thermal memory DB ({len(content)} chars, tags={tags[:4]}...)")
        return True
    except Exception as e:
        logger.warning(f"DB write failed: {e}")
        try:
            conn.close()
        except Exception:
            pass
        return False


def _store_to_local(sig: Dict[str, Any], content: str) -> bool:
    """Store experience as a local JSON file. Returns True on success."""
    _ensure_local_dir()
    ts = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    filename = f"{sig['game_id']}_{ts}.json"
    filepath = LOCAL_EXPERIENCE_DIR / filename

    payload = {
        'signature': sig,
        'content': content,
        'tags': _build_tags(sig),
        'stored_at': ts,
    }

    try:
        filepath.write_text(json.dumps(payload, indent=2, default=str))
        logger.info(f"Experience stored locally: {filepath}")
        return True
    except Exception as e:
        logger.warning(f"Local write failed: {e}")
        return False


# ---------------------------------------------------------------------------
# 3. Experience Retrieval
# ---------------------------------------------------------------------------

def _retrieve_from_db(
    game_id: Optional[str] = None,
    action_types: Optional[List[str]] = None,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    """
    Retrieve game experiences from thermal memory DB.

    Returns list of dicts with 'content', 'tags', 'created_at' keys.
    """
    conn = _get_db_connection()
    if conn is None:
        return []

    try:
        cur = conn.cursor()

        # Build dynamic WHERE clause
        conditions = ["'arc_agi_3' = ANY(tags)", "'game_experience' = ANY(tags)"]
        params = []

        if game_id:
            conditions.append("(%s = ANY(tags) OR content ILIKE %s)")
            params.extend([f"game_{game_id}", f"%{game_id}%"])

        if action_types:
            action_tag_conditions = []
            for at in action_types:
                action_tag_conditions.append("%s = ANY(tags)")
                params.append(f"action_{at}")
            conditions.append(f"({' OR '.join(action_tag_conditions)})")

        where = " AND ".join(conditions)
        params.append(limit)

        cur.execute(f"""
            SELECT content, tags, created_at
            FROM triad_shared_memories
            WHERE {where}
            ORDER BY created_at DESC
            LIMIT %s
        """, params)

        rows = cur.fetchall()
        cur.close()
        conn.close()

        return [
            {'content': row[0], 'tags': row[1], 'created_at': row[2]}
            for row in rows
        ]
    except Exception as e:
        logger.warning(f"DB retrieval failed: {e}")
        try:
            conn.close()
        except Exception:
            pass
        return []


def _retrieve_from_local(
    game_id: Optional[str] = None,
    action_types: Optional[List[str]] = None,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    """Retrieve game experiences from local JSON files."""
    if not LOCAL_EXPERIENCE_DIR.exists():
        return []

    results = []
    files = sorted(LOCAL_EXPERIENCE_DIR.glob('*.json'), reverse=True)

    for filepath in files:
        if len(results) >= limit:
            break
        try:
            data = json.loads(filepath.read_text())
            sig = data.get('signature', {})

            # Filter by game_id
            if game_id and sig.get('game_id') != game_id:
                # Also check if game_id appears anywhere in tags
                tags = data.get('tags', [])
                if f"game_{game_id}" not in tags:
                    continue

            # Filter by action types
            if action_types:
                sig_action = sig.get('action_type', 'unknown')
                if sig_action not in action_types:
                    continue

            results.append({
                'content': data.get('content', ''),
                'tags': data.get('tags', []),
                'created_at': data.get('stored_at', ''),
            })
        except (json.JSONDecodeError, OSError) as e:
            logger.debug(f"Skipping {filepath}: {e}")
            continue

    return results


def _format_experiences_for_context(experiences: List[Dict[str, Any]]) -> str:
    """
    Format retrieved experiences into a context string suitable for
    injection into CWM synthesis prompts or agent initialization.
    """
    if not experiences:
        return ""

    lines = [
        "",
        "=== CROSS-GAME EXPERIENCE BANK ===",
        f"Retrieved {len(experiences)} past game experience(s).",
        "",
    ]

    for i, exp in enumerate(experiences):
        content = exp.get('content', '')
        tags = exp.get('tags', [])
        created = exp.get('created_at', 'unknown')

        lines.append(f"--- Experience #{i+1} (from {created}) ---")

        # Extract the key sections from the stored content
        # Pull Strategy Notes section (most useful for context injection)
        strategy_start = content.find('== STRATEGY NOTES ==')
        if strategy_start >= 0:
            strategy_end = content.find('\n==', strategy_start + 20)
            if strategy_end < 0:
                strategy_end = len(content)
            strategy_section = content[strategy_start:strategy_end].strip()
            lines.append(strategy_section)
        else:
            # Fallback: show a summary
            lines.append(content[:500])

        # Pull CWM info
        cwm_start = content.find('== CWM')
        if cwm_start >= 0:
            cwm_end = content.find('\n==', cwm_start + 6)
            if cwm_end < 0:
                cwm_end = min(cwm_start + 300, len(content))
            lines.append(content[cwm_start:cwm_end].strip())

        # Pull Level-Up Patterns
        lup_start = content.find('== LEVEL-UP PATTERNS ==')
        if lup_start >= 0:
            lup_end = content.find('\n==', lup_start + 23)
            if lup_end < 0:
                lup_end = min(lup_start + 400, len(content))
            lines.append(content[lup_start:lup_end].strip())

        # Tag summary
        action_tags = [t for t in tags if t.startswith('action_')]
        goal_tags = [t for t in tags if t.startswith('goal_')]
        if action_tags or goal_tags:
            lines.append(f"Tags: {', '.join(action_tags + goal_tags)}")

        lines.append("")

    lines.append("=== END EXPERIENCE BANK ===")
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 4. Public Integration Hooks
# ---------------------------------------------------------------------------

def store_game_experience(game_id: str, agent_state_dict: Dict[str, Any]) -> bool:
    """
    Store a completed game's experience to thermal memory.

    Call this after a game ends (win, game-over, or timeout).

    Args:
        game_id: the game identifier
        agent_state_dict: dictionary containing agent runtime state:
            - world_model_status: from CodeWorldModel.status()
            - goal_inferrer_status: from GoalInferrer.status()
            - action_count: total actions taken
            - levels_completed: number of levels beaten
            - action_history: list of action name strings
            - level_up_actions: list of (action_index, action_name)
            - frame_characteristics: dominant_colors, object_count_range, etc.
            - unique_states: count of unique frame hashes
            - outcome: 'win', 'game_over', 'timeout', 'unknown'

    Returns:
        True if storage succeeded (DB or local fallback).
    """
    sig = extract_game_signature(game_id, agent_state_dict)
    content = _signature_to_content(sig)
    tags = _build_tags(sig)

    # Try DB first, fall back to local JSON
    if _store_to_db(content, tags):
        return True

    logger.info("DB unavailable, falling back to local JSON storage.")
    return _store_to_local(sig, content)


def retrieve_game_experiences(
    game_id: Optional[str] = None,
    action_types: Optional[List[str]] = None,
    limit: int = 10,
) -> str:
    """
    Retrieve relevant past game experiences as a formatted context string.

    Call this before starting a new game to seed the agent with cross-game
    knowledge. The returned string can be injected into CWM synthesis prompts
    or used to bias the graph explorer's initial strategy.

    Args:
        game_id: optional game ID to filter by (retrieves experiences from
                 the same game for re-attempts, or None for all games)
        action_types: optional list of action type filters, e.g.
                      ['keyboard', 'click'] to retrieve experiences from
                      games that used those input modes
        limit: max number of experiences to retrieve

    Returns:
        Formatted context string. Empty string if no experiences found.
    """
    # Try DB first, fall back to local
    experiences = _retrieve_from_db(game_id, action_types, limit)

    if not experiences:
        logger.info("No DB experiences found, checking local files.")
        experiences = _retrieve_from_local(game_id, action_types, limit)

    if not experiences:
        logger.info("No past game experiences found.")
        return ""

    context = _format_experiences_for_context(experiences)
    logger.info(f"Retrieved {len(experiences)} game experience(s) ({len(context)} chars context).")
    return context


# ---------------------------------------------------------------------------
# CLI test
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    print("=== Game Experience Bank self-test ===\n")

    # Test 1: Signature extraction
    print("1. Game signature extraction")
    test_state = {
        'world_model_status': {
            'transitions_collected': 45,
            'synthesis_attempts': 2,
            'synthesis_successes': 1,
            'model_ready': True,
            'accuracy': 0.72,
        },
        'goal_inferrer_status': {
            'hypotheses': [
                {'category': 'reach', 'confidence': 0.8,
                 'description': 'Move the player to the target zone'},
                {'category': 'clear', 'confidence': 0.3,
                 'description': 'Remove all obstacles'},
            ],
        },
        'action_count': 150,
        'levels_completed': 3,
        'action_history': ['ACTION1', 'ACTION3', 'ACTION2', 'ACTION1',
                           'ACTION4', 'ACTION1', 'ACTION2'] * 20,
        'level_up_actions': [
            (40, 'ACTION1'),
            (85, 'ACTION3'),
            (130, 'ACTION2'),
        ],
        'frame_characteristics': {
            'dominant_colors': ['black', 'blue', 'red'],
            'object_count_range': [3, 8],
            'grid_size': [64, 64],
            'has_grid_pattern': True,
        },
        'unique_states': 28,
        'outcome': 'win',
    }

    sig = extract_game_signature('test_game_42', test_state)
    assert sig['game_id'] == 'test_game_42'
    assert sig['action_type'] == 'keyboard'
    assert sig['levels_completed'] == 3
    assert sig['cwm']['accuracy'] == 0.72
    assert len(sig['goal_hypotheses']) == 2
    assert len(sig['level_up_patterns']) == 3
    print(f"   Signature keys: {list(sig.keys())}")
    print(f"   Action type: {sig['action_type']}")
    print(f"   Level-up patterns: {len(sig['level_up_patterns'])}")
    print("   PASSED\n")

    # Test 2: Content formatting
    print("2. Content formatting for storage")
    content = _signature_to_content(sig)
    assert 'ARC-AGI-3 GAME EXPERIENCE' in content
    assert 'STRATEGY NOTES' in content
    assert 'keyboard-only' in content
    print(f"   Content length: {len(content)} chars")
    print(f"   First 200 chars: {content[:200]}")
    print("   PASSED\n")

    # Test 3: Tag building
    print("3. Tag building")
    tags = _build_tags(sig)
    assert 'arc_agi_3' in tags
    assert 'game_experience' in tags
    assert 'game_test_game_42' in tags
    assert 'action_keyboard' in tags
    assert 'cwm_success' in tags
    assert 'goal_reach' in tags
    print(f"   Tags: {tags}")
    print("   PASSED\n")

    # Test 4: Local storage fallback
    print("4. Local storage fallback")
    success = _store_to_local(sig, content)
    assert success
    assert LOCAL_EXPERIENCE_DIR.exists()
    files = list(LOCAL_EXPERIENCE_DIR.glob('test_game_42_*.json'))
    assert len(files) >= 1
    print(f"   Stored to: {files[-1]}")
    print("   PASSED\n")

    # Test 5: Local retrieval
    print("5. Local retrieval")
    results = _retrieve_from_local(game_id='test_game_42')
    assert len(results) >= 1
    assert 'content' in results[0]
    print(f"   Retrieved {len(results)} experience(s)")
    print("   PASSED\n")

    # Test 6: Context formatting
    print("6. Context formatting for prompt injection")
    context = _format_experiences_for_context(results)
    assert 'CROSS-GAME EXPERIENCE BANK' in context
    assert 'STRATEGY NOTES' in context
    print(f"   Context length: {len(context)} chars")
    print(f"   Preview:\n{context[:400]}")
    print("   PASSED\n")

    # Test 7: Full integration hook (store)
    print("7. store_game_experience integration hook")
    stored = store_game_experience('test_game_42', test_state)
    assert stored  # should succeed via local fallback at minimum
    print(f"   Stored: {stored}")
    print("   PASSED\n")

    # Test 8: Full integration hook (retrieve)
    print("8. retrieve_game_experiences integration hook")
    ctx = retrieve_game_experiences(game_id='test_game_42', action_types=['keyboard'])
    assert len(ctx) > 0
    print(f"   Context length: {len(ctx)} chars")
    print("   PASSED\n")

    # Test 9: Action type classification edge cases
    print("9. Action type classification")
    assert _classify_action_types([]) == 'unknown'
    assert _classify_action_types(['ACTION1', 'ACTION2']) == 'keyboard'
    assert _classify_action_types(['ACTION6']) == 'click'
    assert _classify_action_types(['ACTION1', 'ACTION6']) == 'keyboard_click'
    print("   PASSED\n")

    # Cleanup test files
    for f in LOCAL_EXPERIENCE_DIR.glob('test_game_42_*.json'):
        f.unlink()
    print("   Cleaned up test files.\n")

    print("=== All game experience bank tests passed ===")
