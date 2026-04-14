"""
ARC-AGI-3 Plan Tracker — Phased Navigation with Wall Memory + Exploration

Empirically-driven approach: don't model sliding movement — just try
directions and learn which ones are blocked at each position.

Key insights:
- The + icon cycles on press toward it (wall-blocked OK)
- Phase 1: horizontal toward target, Phase 2: vertical, Phase 3: interact
- When primary direction is wall-blocked, try perpendicular detour
- Track position history to detect oscillation and force exploration
"""


# Track state across calls within a level
_plus_visited = False
_plus_original_pos = None
_blocked_at = {}        # {(x,y): set of blocked directions}
_last_pos = None
_last_direction = None
_position_history = []  # last N positions for oscillation detection
_explored_positions = set()  # all positions we've been to

def reset_plan():
    """Reset plan state for a new level."""
    global _plus_visited, _plus_original_pos, _blocked_at, _last_pos, _last_direction
    global _position_history, _explored_positions
    _plus_visited = False
    _plus_original_pos = None
    _blocked_at = {}
    _last_pos = None
    _last_direction = None
    _position_history = []
    _explored_positions = set()

def _pick_unblocked(candidates, blocked_here):
    """Pick first candidate not blocked. Returns (direction, is_detour)."""
    for i, d in enumerate(candidates):
        if d not in blocked_here:
            return d, i > 0  # detour if not first candidate
    return None, True

def get_current_step(game_state: dict, level: str, experiences: str = "") -> dict:
    global _plus_visited, _plus_original_pos, _blocked_at, _last_pos, _last_direction
    global _position_history, _explored_positions

    pos = game_state.get('player', {})
    px = pos.get('x', 17)
    py = pos.get('y', 22)
    plus = game_state.get('plusPositions', [])
    blocks = game_state.get('gameBlocks', [])

    current_pos = (px, py)
    _explored_positions.add(current_pos)

    # --- Learn which directions are blocked at each position ---
    if _last_pos is not None and _last_direction is not None:
        if current_pos == _last_pos:
            if _last_pos not in _blocked_at:
                _blocked_at[_last_pos] = set()
            _blocked_at[_last_pos].add(_last_direction)

    # --- Oscillation detection ---
    _position_history.append(current_pos)
    if len(_position_history) > 10:
        _position_history.pop(0)

    oscillating = False
    if len(_position_history) >= 6:
        recent = _position_history[-6:]
        if len(set(recent)) <= 2:
            oscillating = True
            # Mark the directions that bounce between oscillation positions as blocked
            unique = set(recent)
            for osc_pos in unique:
                if osc_pos not in _blocked_at:
                    _blocked_at[osc_pos] = set()
                for other in unique:
                    if other != osc_pos:
                        if other[1] < osc_pos[1]:
                            _blocked_at[osc_pos].add('up')
                        elif other[1] > osc_pos[1]:
                            _blocked_at[osc_pos].add('down')
                        if other[0] < osc_pos[0]:
                            _blocked_at[osc_pos].add('left')
                        elif other[0] > osc_pos[0]:
                            _blocked_at[osc_pos].add('right')
            _position_history.clear()

    blocked_here = _blocked_at.get(current_pos, set())

    # If all 4 directions blocked, clear and defer
    if len(blocked_here) >= 4:
        _blocked_at[current_pos] = set()
        blocked_here = set()

    # If we have no plus positions, let Jr handle it
    if not plus and not _plus_original_pos:
        return _defer('no plus found')

    # Remember the original + position
    if not _plus_original_pos and plus:
        _plus_original_pos = (plus[0].get('x', 10), plus[0].get('y', 15))

    plus_x = _plus_original_pos[0] if _plus_original_pos else 10
    plus_y = _plus_original_pos[1] if _plus_original_pos else 15

    # Find the target block
    target_block = None
    if blocks:
        top_blocks = [b for b in blocks if b.get('y', 99) < 25]
        target_block = top_blocks[0] if top_blocks else blocks[0]

    # Determine current target
    if _plus_visited:
        if target_block:
            tx = target_block.get('x', 17)
            ty = target_block.get('y', 5)
            label = 'block'
        else:
            return _defer('plus visited but no block found')
    else:
        tx, ty = plus_x, plus_y
        label = 'plus'

    # === NAVIGATE toward target ===
    result = _navigate(px, py, tx, ty, blocked_here, label)

    if result:
        direction = result['direction']

        # If navigating to plus and we're adjacent, mark plus as visited
        if label == 'plus' and abs(px - tx) <= 1 and abs(py - ty) <= 1:
            _plus_visited = True
            result['reason'] += ' Plus DONE.'

        return _record(result, current_pos)

    return _defer(f'no unblocked direction at ({px},{py})')


def _navigate(px, py, tx, ty, blocked_here, label):
    """Navigate toward target with phased approach + wall-aware fallback."""
    dx = tx - px
    dy = ty - py

    # Build candidate list: primary directions toward target, then perpendicular, then opposite
    candidates = []

    # Primary: toward target (horizontal first if farther, else vertical first)
    h_dir = 'left' if dx < 0 else 'right' if dx > 0 else None
    v_dir = 'up' if dy < 0 else 'down' if dy > 0 else None

    # Only add horizontal if distance > 1 (avoid overshoot at close range)
    # Only add vertical if distance > 1
    if h_dir and abs(dx) > 1:
        candidates.append(h_dir)
    if v_dir and abs(dy) > 1:
        candidates.append(v_dir)

    # If close range (distance <= 1), still add the direction toward target
    if h_dir and abs(dx) <= 1:
        candidates.append(h_dir)
    if v_dir and abs(dy) <= 1:
        candidates.append(v_dir)

    # Add perpendicular/opposite as exploration fallbacks
    all_dirs = ['up', 'down', 'left', 'right']
    for d in all_dirs:
        if d not in candidates:
            candidates.append(d)

    # Remove duplicates while preserving order
    seen = set()
    unique_candidates = []
    for c in candidates:
        if c not in seen:
            seen.add(c)
            unique_candidates.append(c)
    candidates = unique_candidates

    direction, is_detour = _pick_unblocked(candidates, blocked_here)
    if direction is None:
        return None

    step = 1
    if _plus_visited:
        step = 4 + (1 if is_detour else 0)

    detour = f' (detour, {blocked_here} blocked)' if is_detour else ''
    return {
        'direction': direction,
        'reason': f'Step {step}: {direction.upper()} toward {label} ({tx},{ty}) from ({px},{py}){detour}.',
        'step': step,
        'use_jr': False
    }


def _record(result, current_pos):
    """Record direction and position for wall detection on next call."""
    global _last_pos, _last_direction
    _last_pos = current_pos
    _last_direction = result.get('direction')
    return result


def _defer(reason):
    """Defer to Jr/Council."""
    global _last_pos, _last_direction
    _last_pos = None
    _last_direction = None
    return {
        'direction': None,
        'reason': f'Plan: {reason}. Let Jr decide.',
        'step': 0,
        'use_jr': True
    }
