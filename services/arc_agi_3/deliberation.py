"""
ARC-AGI-3 Deliberation Layer — Graduated Autonomy Tiers (Patent #4)

Two-tier decision architecture:
- Jr (Qwen2.5-72B on redfin:8000): fast reflex decisions, handles obvious moves
- Council (specialist_council.py on bmasass): deliberative decisions when Jr is stuck

The Jr handles most moves. The Council handles the hard ones.
This is the Graduated Autonomy Tiers patent applied to game playing.
"""

import json
import requests
import sys

sys.path.insert(0, '/ganuda')
sys.path.insert(0, '/ganuda/lib')

# vLLM endpoint on redfin (72B fast path)
VLLM_URL = "http://localhost:8000/v1/chat/completions"
VLLM_MODEL = "/ganuda/models/qwen2.5-72b-instruct-awq"

# Escalation thresholds
STUCK_THRESHOLD = 3  # consecutive non-moving moves before escalation
FUEL_CRITICAL = 5    # fuel level below which every move gets Council review


def jr_decide(game_state: dict, level: str, move_history: list, stuck_count: int = 0) -> tuple:
    """Jr tier — fast move decision via 72B on redfin.

    Returns:
        (direction, confidence, reason) where confidence is 'high', 'medium', or 'low'
    """
    pos = game_state.get('player', {})
    fuel = game_state.get('fuelBar', 0)
    blocks = game_state.get('gameBlocks', [])
    plus = game_state.get('plusPositions', [])
    pickups = game_state.get('fuelPickups', [])

    # Build compact prompt for the Jr
    # Retrieve past experiences for this level
    experience_context = ""
    try:
        from experience import retrieve_experiences
        experience_context = retrieve_experiences("ls20", level, game_state)
    except Exception:
        pass

    prompt = f"""You are an AI agent playing a grid puzzle game.
{experience_context}
CURRENT STATE:
- Player position: ({pos.get('x')}, {pos.get('y')})
- Fuel remaining: {fuel}
- Blue blocks (targets to clear): {json.dumps(blocks[:4])}
- Plus icon switcher (+): {json.dumps(plus[:2])}
- Yellow fuel pickups: {json.dumps(pickups[:4])}
- Level: {level}
- Moves so far: {len(move_history)}
- Last 5 moves: {move_history[-5:]}
- Times stuck (no movement): {stuck_count}

GAME RULES:
- Arrow keys move the player (slides until hitting a wall)
- Walk through the + to cycle your icon to match the blue block
- Match your icon then walk onto the blue block to clear the level
- Yellow pickups refuel
- Each move costs fuel

RESPOND WITH EXACTLY:
DIRECTION: [up/down/left/right]
CONFIDENCE: [high/medium/low]
REASON: [one sentence]"""

    try:
        resp = requests.post(VLLM_URL, json={
            "model": VLLM_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 60,
            "temperature": 0.1,
        }, timeout=10)

        if resp.status_code == 200:
            text = resp.json()['choices'][0]['message']['content'].strip()

            # Parse response
            direction = None
            confidence = 'medium'
            reason = text

            for d in ['up', 'down', 'left', 'right']:
                if f'DIRECTION: {d}' in text.lower() or f'direction: {d}' in text.lower():
                    direction = d
                    break
                elif text.lower().startswith(d) or f': {d}' in text.lower():
                    direction = d
                    break

            if 'CONFIDENCE: high' in text or 'confidence: high' in text:
                confidence = 'high'
            elif 'CONFIDENCE: low' in text or 'confidence: low' in text:
                confidence = 'low'

            # Extract reason
            for line in text.split('\n'):
                if line.upper().startswith('REASON:'):
                    reason = line[7:].strip()
                    break

            if direction:
                return direction, confidence, reason[:80]
            else:
                # Couldn't parse direction — try to extract any direction word
                for d in ['up', 'down', 'left', 'right']:
                    if d in text.lower():
                        return d, 'low', f"parsed-from: {text[:60]}"
                return None, 'low', f"unparseable: {text[:60]}"

    except Exception as e:
        return None, 'low', f"Jr error: {str(e)[:60]}"

    return None, 'low', "Jr inference failed"


def council_decide(game_state: dict, level: str, move_history: list, jr_reason: str = "") -> tuple:
    """Council tier — multi-voice deliberation via specialist_council.py on bmasass.

    Called when Jr is stuck or low-confidence. This is the slow, thorough path.

    Returns:
        (direction, reason)
    """
    try:
        from specialist_council import council_vote

        pos = game_state.get('player', {})
        fuel = game_state.get('fuelBar', 0)
        blocks = game_state.get('gameBlocks', [])
        plus = game_state.get('plusPositions', [])
        pickups = game_state.get('fuelPickups', [])

        question = f"""ARC-AGI-3 GAME — Jr ESCALATED TO COUNCIL

The Jr agent is stuck or uncertain. Council must deliberate on the next move.

Jr's assessment: {jr_reason}

GAME STATE — {level}:
Player: ({pos.get('x')}, {pos.get('y')})
Fuel: {fuel}
Blue blocks: {json.dumps(blocks[:6])}
Plus (+): {json.dumps(plus[:4])}
Fuel pickups: {json.dumps(pickups[:4])}
Move history (last 15): {move_history[-15:]}
Total moves: {len(move_history)}

The player slides when an arrow key is pressed (variable distance, stops at walls).
The + cycles the player icon. Match icon + walk onto blue block = clear level.
Yellow blocks refuel.

Council: what direction should the player move? Give ONE direction and reasoning.
Consider: optimal route, fuel conservation, whether to visit + or go directly to block."""

        result = council_vote(question, max_tokens=150, include_responses=False)
        response = result.get('consensus', '').lower()

        for direction in ['up', 'down', 'left', 'right']:
            if direction in response:
                return direction, f"Council ({result.get('audit_hash', '?')[:8]}): {result.get('consensus', '')[:80]}"

        return None, f"Council unclear: {response[:80]}"

    except Exception as e:
        return None, f"Council error: {str(e)[:60]}"


def graduated_decide(game_state: dict, level: str, move_history: list,
                     stuck_count: int = 0, last_positions: list = None) -> tuple:
    """Graduated Autonomy Tiers — the main decision function.

    Implements Patent #4:
    - Reflex tier: Jr handles confident, obvious moves
    - Deliberation tier: Jr handles medium-confidence moves
    - Council tier: escalation when Jr is stuck or low-confidence
    - Critical tier: Council + extra caution when fuel is critically low

    Returns:
        (direction, reason, tier_used)
    """
    fuel = game_state.get('fuelBar', 0)

    # Determine if escalation is needed
    should_escalate = False
    escalation_reason = ""

    if stuck_count >= STUCK_THRESHOLD:
        should_escalate = True
        escalation_reason = f"stuck {stuck_count} consecutive moves"

    if fuel <= FUEL_CRITICAL:
        should_escalate = True
        escalation_reason = f"critical fuel ({fuel})"

    # Check for oscillation (bouncing between same 2 positions)
    if last_positions and len(last_positions) >= 6:
        recent = last_positions[-6:]
        positions_set = set(str(p) for p in recent)
        if len(positions_set) <= 2:
            should_escalate = True
            escalation_reason = "oscillating between 2 positions"

    if should_escalate:
        # COUNCIL TIER — escalate to multi-voice deliberation
        direction, reason = council_decide(game_state, level, move_history, escalation_reason)
        if direction:
            return direction, reason, "council"
        # Council failed — fall back to Jr
        escalation_reason += " (council failed, Jr fallback)"

    # JR TIER — fast decision
    direction, confidence, reason = jr_decide(game_state, level, move_history, stuck_count)

    if direction and confidence in ('high', 'medium'):
        return direction, f"Jr ({confidence}): {reason}", "jr"

    if direction and confidence == 'low':
        # Low confidence — escalate to Council
        council_dir, council_reason = council_decide(game_state, level, move_history, f"Jr low-confidence: {reason}")
        if council_dir:
            return council_dir, council_reason, "council"
        # Council also failed — use Jr's low-confidence answer anyway
        return direction, f"Jr (low, council-failed): {reason}", "jr-fallback"

    # Neither Jr nor Council produced a direction — default rotation
    default = ['up', 'right', 'down', 'left'][len(move_history) % 4]
    return default, "all tiers failed, rotating", "default"
