#!/usr/bin/env python3
"""
Council Emotion State — Foundation Agents GAP 1

Russell's Circumplex Model: valence (-1 to +1) x arousal (-1 to +1)
- High valence + high arousal = enthusiastic, energized
- High valence + low arousal = calm, content, patient
- Low valence + high arousal = anxious, alarmed, aggressive
- Low valence + low arousal = sad, withdrawn, conservative

Coyote standing dissent: opt-in per specialist (coyote opts OUT)
Crawdad conditions: strict bounds, immutable audit trail, 3-sigma reset
Longhouse c4e68ce0fcea60a3

Design constraint: DC-6 (Gradient Principle) — specialization is gravity, not boundary.
Emotion shifts the gradient, doesn't change who they are.
"""

import math
from datetime import datetime
from typing import Optional, Tuple

# Emotion label mapping (Plutchik-inspired, simplified for prompts)
EMOTION_LABELS = {
    # (valence_sign, arousal_sign): (emotion_word, prompt_modifier)
    (1, 1):  ("energized",   "You feel sharp and engaged. Your analysis is crisp and forward-leaning."),
    (1, -1): ("calm",        "You feel settled and patient. Take the long view. No rush."),
    (-1, 1): ("vigilant",    "Something feels off. Sharpen your focus. Look harder at what others might miss."),
    (-1, -1):("cautious",    "Tread carefully. Conserve energy. Only speak on what you are certain about."),
    (0, 0):  ("neutral",     ""),  # no modifier at baseline
}

# 3-sigma threshold for circuit breaker (Crawdad condition)
SIGMA_THRESHOLD = 3.0
BASELINE_STD = 0.33  # expected std of valence/arousal shifts
CIRCUIT_BREAKER_LIMIT = SIGMA_THRESHOLD * BASELINE_STD  # ~1.0 (full range)

# Maximum sessions before mandatory reset to baseline
MAX_SESSIONS_BEFORE_RESET = 20


def get_emotion_label(valence: float, arousal: float) -> Tuple[str, str]:
    """Map valence+arousal to emotion label and prompt modifier."""
    magnitude = math.sqrt(valence**2 + arousal**2)
    if magnitude < 0.15:
        return "neutral", ""

    v_sign = 1 if valence >= 0 else -1
    a_sign = 1 if arousal >= 0 else -1
    label, modifier = EMOTION_LABELS.get((v_sign, a_sign), ("neutral", ""))

    # Scale modifier intensity by magnitude
    if magnitude < 0.4:
        intensity = "slightly"
    elif magnitude < 0.7:
        intensity = ""
    else:
        intensity = "strongly"

    if intensity and modifier:
        modifier = f"You are {intensity} {label}. " + modifier.split(". ", 1)[-1] if ". " in modifier else modifier

    return label, modifier


def get_emotion_state(specialist_id: str, conn) -> Optional[dict]:
    """Read current emotion state for a specialist. Returns None if disabled."""
    cur = conn.cursor()
    cur.execute("""
        SELECT valence, arousal, emotion_enabled, session_count
        FROM council_emotion_state
        WHERE specialist_id = %s
    """, (specialist_id,))
    row = cur.fetchone()
    cur.close()
    if not row or not row[2]:  # not found or not enabled
        return None
    return {
        "valence": row[0],
        "arousal": row[1],
        "enabled": row[2],
        "session_count": row[3],
    }


def build_emotion_prompt_modifier(specialist_id: str, conn) -> str:
    """Generate the prompt modifier string for a specialist's current emotion state.

    Returns empty string if emotion is disabled or at baseline.
    This is the string that gets appended to the specialist's system prompt.
    """
    state = get_emotion_state(specialist_id, conn)
    if not state:
        return ""

    # Check session count — force reset if over limit
    if state["session_count"] >= MAX_SESSIONS_BEFORE_RESET:
        reset_to_baseline(specialist_id, conn, "session_count_limit")
        return ""

    label, modifier = get_emotion_label(state["valence"], state["arousal"])
    if not modifier:
        return ""

    return f"\n\n[EMOTIONAL STATE: {label} (v={state['valence']:.2f}, a={state['arousal']:.2f})]\n{modifier}"


def update_emotion_state(specialist_id: str, new_valence: float, new_arousal: float,
                          conn, trigger_source: str = "council_feedback",
                          vote_hash: str = None):
    """Update a specialist's emotion state with bounds checking and audit trail.

    Enforces Crawdad conditions:
    - Strict bounds [-1, 1]
    - Immutable audit trail
    - 3-sigma circuit breaker
    """
    # Clamp to bounds
    new_valence = max(-1.0, min(1.0, new_valence))
    new_arousal = max(-1.0, min(1.0, new_arousal))

    cur = conn.cursor()

    # Read current state
    cur.execute("""
        SELECT valence, arousal, emotion_enabled, session_count
        FROM council_emotion_state
        WHERE specialist_id = %s
    """, (specialist_id,))
    row = cur.fetchone()
    if not row:
        cur.close()
        return False
    old_valence, old_arousal, enabled, session_count = row

    if not enabled:
        cur.close()
        return False  # opt-out respected

    # 3-sigma circuit breaker: if shift is too large, clamp
    delta_v = abs(new_valence - old_valence)
    delta_a = abs(new_arousal - old_arousal)
    if delta_v > CIRCUIT_BREAKER_LIMIT or delta_a > CIRCUIT_BREAKER_LIMIT:
        print(f"[EMOTION] {specialist_id}: 3-sigma circuit breaker — shift too large "
              f"(dv={delta_v:.2f}, da={delta_a:.2f}, limit={CIRCUIT_BREAKER_LIMIT:.2f}). Clamping.")
        if delta_v > CIRCUIT_BREAKER_LIMIT:
            direction = 1 if new_valence > old_valence else -1
            new_valence = old_valence + (direction * CIRCUIT_BREAKER_LIMIT)
        if delta_a > CIRCUIT_BREAKER_LIMIT:
            direction = 1 if new_arousal > old_arousal else -1
            new_arousal = old_arousal + (direction * CIRCUIT_BREAKER_LIMIT)
        new_valence = max(-1.0, min(1.0, new_valence))
        new_arousal = max(-1.0, min(1.0, new_arousal))

    # Write audit trail (immutable — Crawdad condition)
    cur.execute("""
        INSERT INTO council_emotion_audit
            (specialist_id, old_valence, old_arousal, new_valence, new_arousal, trigger_source, council_vote_hash)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (specialist_id, old_valence, old_arousal, new_valence, new_arousal, trigger_source, vote_hash))

    # Update state
    cur.execute("""
        UPDATE council_emotion_state
        SET valence = %s, arousal = %s, updated_at = NOW(), session_count = session_count + 1
        WHERE specialist_id = %s
    """, (new_valence, new_arousal, specialist_id))

    conn.commit()
    cur.close()
    return True


def reset_to_baseline(specialist_id: str, conn, trigger_source: str = "manual_reset"):
    """Reset a specialist to neutral baseline. Logged in audit trail."""
    cur = conn.cursor()
    cur.execute("""
        SELECT valence, arousal FROM council_emotion_state WHERE specialist_id = %s
    """, (specialist_id,))
    row = cur.fetchone()
    if row:
        cur.execute("""
            INSERT INTO council_emotion_audit
                (specialist_id, old_valence, old_arousal, new_valence, new_arousal, trigger_source)
            VALUES (%s, %s, %s, 0.0, 0.0, %s)
        """, (specialist_id, row[0], row[1], trigger_source))
    cur.execute("""
        UPDATE council_emotion_state
        SET valence = 0.0, arousal = 0.0, session_count = 0, updated_at = NOW()
        WHERE specialist_id = %s
    """, (specialist_id,))
    conn.commit()
    cur.close()


def update_emotions_from_vote(vote_result, conn):
    """Adjust specialist emotions based on council vote outcome.

    This is the feedback loop — vote results shift emotional state.
    High confidence + consent → positive valence shift
    Low confidence + concerns → negative valence, higher arousal
    Own concern raised → arousal boost (engaged)
    Own concern ignored → slight negative valence (frustrated)
    """
    if not vote_result or not hasattr(vote_result, 'responses'):
        return

    confidence = getattr(vote_result, 'confidence', 0.5)
    vote_hash = getattr(vote_result, 'audit_hash', None)
    responses = vote_result.responses

    # responses can be List[SpecialistResponse] or dict — handle both
    if isinstance(responses, list):
        items = [(getattr(r, 'specialist_id', ''), r) for r in responses]
    elif isinstance(responses, dict):
        items = responses.items()
    else:
        return

    for specialist_id, resp in items:
        state = get_emotion_state(specialist_id, conn)
        if not state:
            continue  # disabled or not found

        has_concern = getattr(resp, 'has_concern', False) if hasattr(resp, 'has_concern') else resp.get('has_concern', False)
        v = state["valence"]
        a = state["arousal"]

        # Shift rules (small increments — emotion drifts, doesn't jump)
        if confidence > 0.7:
            # High confidence vote — things are going well
            v += 0.1   # positive valence
            a -= 0.05  # slightly calmer
        elif confidence < 0.3:
            # Low confidence — tension
            v -= 0.1   # negative valence
            a += 0.1   # more aroused/alert

        if has_concern:
            a += 0.15   # raising a concern = engaged
            v -= 0.05   # slight negative (something is wrong)

        update_emotion_state(specialist_id, v, a, conn,
                             trigger_source="vote_feedback", vote_hash=vote_hash)
