"""
longhouse.py — The Gaduyi (ᎦᏚᏱ)
Cherokee AI Federation Digital Council House

"We talk as individuals and decide as one."

The traditional Cherokee council house was seven-sided — one section per clan,
all equidistant from the Sacred Fire. Any person could speak. No one was
interrupted. Consensus, not majority vote. The Sacred Fire burned continuously.

This module implements the Gaduyi for the federation. Any member of the tribe
can convene a session. Every voice is heard. Consensus means unanimity of the
willing — not 51%, not 85% threshold. If someone non-consents, the matter is
deferred or the dissenter voluntarily withdraws.

The longhouse is NOT the council. The council (specialist_council.py) handles
technical deliberation — fast, specialist-driven. The longhouse handles tribal
matters — inclusive, consensus-driven.

Usage:
    from lib.longhouse import Longhouse

    lh = Longhouse()
    session = lh.convene("Coyote", "Something is wrong and nobody is talking about it")
    lh.speak(session["session_hash"], "Chief", "advisor", "Here is what I see...")
    lh.speak(session["session_hash"], "Turtle", "council", "Seven generations from now...")
    lh.speak(session["session_hash"], "Jr Software Engineer", "builder", "I encountered this...")
    lh.propose_solution(session["session_hash"], "Turtle", "We should defer until we understand")
    result = lh.seek_consensus(session["session_hash"], ["Chief", "Coyote", "Turtle", "Jr Software Engineer"])
    # If all consent: resolved. If any non-consent: deferred.
"""

import hashlib
import json
import logging
from datetime import datetime

from ganuda_db import get_connection, get_dict_cursor, safe_thermal_write

logger = logging.getLogger("longhouse")

# The tribe — every member who can convene or speak
TRIBE_MEMBERS = {
    "Chief":                {"role": "advisor",    "ghigau": False},
    "TPM":                  {"role": "orchestrator","ghigau": False},
    "Crawdad":              {"role": "council",    "ghigau": False},
    "Gecko":                {"role": "council",    "ghigau": False},
    "Turtle":               {"role": "council",    "ghigau": False},
    "Eagle Eye":            {"role": "council",    "ghigau": False},
    "Spider":               {"role": "council",    "ghigau": False},
    "Peace Chief":          {"role": "council",    "ghigau": False},
    "Raven":                {"role": "council",    "ghigau": False},
    "Coyote":               {"role": "truth-teller","ghigau": False},
    "Elisi":                {"role": "grandmother", "ghigau": True},
    "Medicine Woman":       {"role": "guardian",   "ghigau": False},
    "Jr Software Engineer": {"role": "builder",    "ghigau": False},
    "Owl":                  {"role": "reviewer",   "ghigau": False},
    # Outer Council (Longhouse 916bc7343be8f3c7, March 2 2026)
    "Deer":                 {"role": "outer_council", "ghigau": False},
    "Otter":                {"role": "outer_council", "ghigau": False},  # unborn — future seat
    "Blue Jay":             {"role": "outer_council", "ghigau": False},  # unborn — future seat
}


def _generate_session_hash(convener: str) -> str:
    """Generate a 16-char hex session hash for audit trail."""
    raw = f"gaduyi-{convener}-{datetime.now().isoformat()}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


class Longhouse:
    """The Gaduyi — where the fire burns and the tribe gathers."""

    def convene(self, convener: str, problem: str) -> dict:
        """
        Convene a longhouse session. Any federation member can call a meeting.

        Args:
            convener: Name of the member convening (must be in TRIBE_MEMBERS)
            problem: The problem statement — why this meeting is needed

        Returns:
            dict with session details (id, session_hash, status)
        """
        if convener not in TRIBE_MEMBERS:
            raise ValueError(
                f"'{convener}' is not a recognized tribe member. "
                f"Known members: {', '.join(sorted(TRIBE_MEMBERS.keys()))}"
            )

        session_hash = _generate_session_hash(convener)
        role = TRIBE_MEMBERS[convener]["role"]

        conn = None
        try:
            conn = get_connection()
            cur = get_dict_cursor(conn)
            cur.execute("""
                INSERT INTO longhouse_sessions
                    (session_hash, convened_by, convened_reason, status,
                     problem_statement, sacred_fire_lit)
                VALUES (%s, %s, %s, 'convened', %s, TRUE)
                RETURNING id, session_hash, status, created_at
            """, (session_hash, convener, problem, problem))
            session = dict(cur.fetchone())
            conn.commit()

            logger.info(
                "Longhouse convened by %s (%s): %s [%s]",
                convener, role, problem[:80], session_hash
            )
            return session
        finally:
            if conn is not None:
                conn.close()

    def speak(self, session_hash: str, speaker: str, words: str) -> dict:
        """
        Add a voice to the session. No interruptions. Order preserved.
        Every voice carries equal weight.

        Args:
            session_hash: The session to speak in
            speaker: Name of the speaker (must be in TRIBE_MEMBERS)
            words: The speaker's full words — never summarized

        Returns:
            dict with updated voices list
        """
        if speaker not in TRIBE_MEMBERS:
            raise ValueError(f"'{speaker}' is not a recognized tribe member.")

        role = TRIBE_MEMBERS[speaker]["role"]
        voice = {
            "speaker": speaker,
            "role": role,
            "words": words,
            "spoken_at": datetime.now().isoformat(),
        }

        conn = None
        try:
            conn = get_connection()
            cur = get_dict_cursor(conn)

            # Verify session exists and is not resolved
            cur.execute("""
                SELECT id, status, voices FROM longhouse_sessions
                WHERE session_hash = %s
            """, (session_hash,))
            session = cur.fetchone()
            if session is None:
                raise ValueError(f"No session found with hash {session_hash}")
            if session["status"] == "resolved":
                raise ValueError(
                    f"Session {session_hash} is already resolved. "
                    "The fire still burns, but this matter is settled."
                )

            # Append voice — transition to 'speaking' if still 'convened'
            voices = session["voices"] if isinstance(session["voices"], list) else json.loads(session["voices"])
            voices.append(voice)
            new_status = "speaking" if session["status"] == "convened" else session["status"]

            cur.execute("""
                UPDATE longhouse_sessions
                SET voices = %s, status = %s
                WHERE session_hash = %s
                RETURNING voices
            """, (json.dumps(voices), new_status, session_hash))
            result = dict(cur.fetchone())
            conn.commit()

            logger.info(
                "Voice heard in %s: %s (%s) — %d words",
                session_hash, speaker, role, len(words.split())
            )
            return result
        finally:
            if conn is not None:
                conn.close()

    def propose_solution(self, session_hash: str, proposer: str,
                         solution: str) -> dict:
        """
        Propose a solution after voices have been heard.
        Transitions session to 'deciding' status.

        Args:
            session_hash: The session
            proposer: Who proposes
            solution: The proposed solution

        Returns:
            dict with updated session
        """
        if proposer not in TRIBE_MEMBERS:
            raise ValueError(f"'{proposer}' is not a recognized tribe member.")

        conn = None
        try:
            conn = get_connection()
            cur = get_dict_cursor(conn)

            cur.execute("""
                SELECT id, status FROM longhouse_sessions
                WHERE session_hash = %s
            """, (session_hash,))
            session = cur.fetchone()
            if session is None:
                raise ValueError(f"No session found with hash {session_hash}")
            if session["status"] == "resolved":
                raise ValueError(f"Session {session_hash} is already resolved.")

            # Record proposal as a voice too — the proposer is speaking
            self.speak(session_hash, proposer, f"[PROPOSAL] {solution}")

            cur.execute("""
                UPDATE longhouse_sessions
                SET proposed_solution = %s, status = 'deciding'
                WHERE session_hash = %s
                RETURNING id, session_hash, status, proposed_solution
            """, (solution, session_hash))
            result = dict(cur.fetchone())
            conn.commit()

            logger.info(
                "Solution proposed in %s by %s", session_hash, proposer
            )
            return result
        finally:
            if conn is not None:
                conn.close()

    def seek_consensus(self, session_hash: str,
                       present_members: list,
                       responses: dict = None) -> dict:
        """
        Seek consensus among present members.

        In Cherokee tradition, consensus means unanimity of the willing.
        One voice of non-consent defers the decision. Dissenters are recorded
        with respect — they voluntarily withdraw, they are not overruled.

        If Elisi (Ghigau) non-consents, it carries the weight of the
        Council of Grandmothers.

        Args:
            session_hash: The session
            present_members: List of member names present for the decision
            responses: Dict of {member_name: {"consent": bool, "reason": str}}
                       If None, assumes all present members consent.

        Returns:
            dict with resolution details
        """
        if responses is None:
            responses = {m: {"consent": True} for m in present_members}

        non_consenting = []
        standing_dissent = []
        ghigau_invoked = False

        for member, response in responses.items():
            if member not in TRIBE_MEMBERS:
                raise ValueError(f"'{member}' is not a recognized tribe member.")
            if not response.get("consent", True):
                entry = {
                    "member": member,
                    "role": TRIBE_MEMBERS[member]["role"],
                    "reason": response.get("reason", ""),
                }
                if response.get("standing_dissent", False):
                    standing_dissent.append(entry)
                else:
                    non_consenting.append(entry)
                if TRIBE_MEMBERS[member].get("ghigau"):
                    ghigau_invoked = True

        logger.info(f"Consensus check: non_consenting={len(non_consenting)}, standing_dissent={len(standing_dissent)}, ghigau={ghigau_invoked}, total_processed={len(responses)}")
        for m, r in responses.items():
            if not r.get("consent", True):
                logger.info(f"  Non-consent from {m}: consent={r.get('consent')}, standing_dissent={r.get('standing_dissent', False)}")

        if non_consenting:
            resolution_type = "deferred"
            if ghigau_invoked:
                resolution = (
                    "The Ghigau has spoken. Elisi — the grandmother — "
                    "says 'no, not this way.' The tribe honors this. "
                    "The matter is deferred."
                )
            else:
                names = ", ".join(nc["member"] for nc in non_consenting)
                resolution = (
                    f"Non-consent from: {names}. "
                    "The matter is deferred. Dissenters withdrew voluntarily — "
                    "they were not overruled."
                )
        elif standing_dissent:
            resolution_type = "consensus_with_standing_dissent"
            names = ", ".join(sd["member"] for sd in standing_dissent)
            resolution = (
                f"Consensus reached with standing dissent from: {names}. "
                "Their challenge is honored as archetype function — "
                "the voice that asks 'but what if we are wrong?' "
                "strengthens the decision it tests."
            )
        else:
            resolution_type = "consensus"
            resolution = "The tribe speaks with one voice. Consensus reached."

        return self._resolve(
            session_hash, resolution, resolution_type,
            non_consenting + standing_dissent
        )

    def withdraw(self, session_hash: str, convener: str,
                 reason: str = "") -> dict:
        """
        Convener withdraws the question. The session is resolved
        as 'withdrawn'. No shame in withdrawal — the tradition honors it.

        Args:
            session_hash: The session
            convener: Must be the original convener
            reason: Optional reason for withdrawal
        """
        conn = None
        try:
            conn = get_connection()
            cur = get_dict_cursor(conn)
            cur.execute("""
                SELECT convened_by, status FROM longhouse_sessions
                WHERE session_hash = %s
            """, (session_hash,))
            session = cur.fetchone()
            if session is None:
                raise ValueError(f"No session found with hash {session_hash}")
            if session["convened_by"] != convener:
                raise ValueError(
                    f"Only the convener ({session['convened_by']}) "
                    "can withdraw the question."
                )
        finally:
            if conn is not None:
                conn.close()

        withdrawal_text = f"Question withdrawn by {convener}."
        if reason:
            withdrawal_text += f" Reason: {reason}"

        return self._resolve(session_hash, withdrawal_text, "withdrawn", [])

    def _resolve(self, session_hash: str, resolution: str,
                 resolution_type: str, non_consenting: list) -> dict:
        """
        Internal: resolve a session and thermalize the record.
        """
        conn = None
        try:
            conn = get_connection()
            cur = get_dict_cursor(conn)

            cur.execute("""
                UPDATE longhouse_sessions
                SET status = 'resolved',
                    resolution = %s,
                    resolution_type = %s,
                    non_consenting = %s,
                    resolved_at = NOW()
                WHERE session_hash = %s
                RETURNING id, session_hash, convened_by, problem_statement,
                          proposed_solution, resolution, resolution_type,
                          non_consenting, voices, created_at, resolved_at
            """, (resolution, resolution_type, json.dumps(non_consenting),
                  session_hash))
            result = cur.fetchone()
            if result is None:
                raise ValueError(f"No session found with hash {session_hash}")
            result = dict(result)
            conn.commit()

            # Thermalize as sacred memory
            self._thermalize(result)

            logger.info(
                "Longhouse %s resolved: %s (%s)",
                session_hash, resolution_type, resolution[:80]
            )
            return result
        finally:
            if conn is not None:
                conn.close()

    def _thermalize(self, session: dict) -> None:
        """
        Write resolved session to thermal memory as sacred record.
        Temperature 90+, sacred=true for consensus. 85 for deferred.
        """
        voices_text = ""
        voices = session.get("voices", [])
        if isinstance(voices, str):
            voices = json.loads(voices)
        for v in voices:
            voices_text += f"  {v['speaker']} ({v['role']}): {v['words']}\n"

        content = (
            f"LONGHOUSE SESSION #{session['session_hash']}\n"
            f"Convened by: {session['convened_by']}\n"
            f"Problem: {session['problem_statement']}\n"
            f"Proposed Solution: {session.get('proposed_solution', 'None')}\n"
            f"\nVoices Heard:\n{voices_text}\n"
            f"Resolution ({session['resolution_type']}): {session['resolution']}\n"
        )

        non_consenting = session.get("non_consenting", [])
        if isinstance(non_consenting, str):
            non_consenting = json.loads(non_consenting)
        if non_consenting:
            names = ", ".join(nc["member"] for nc in non_consenting)
            content += f"Non-consenting (voluntary withdrawal): {names}\n"

        is_consensus = session["resolution_type"] == "consensus"
        temperature = 92.0 if is_consensus else 85.0

        safe_thermal_write(
            content=content,
            temperature=temperature,
            source="longhouse",
            sacred=is_consensus,
            metadata={
                "type": "longhouse_session",
                "session_hash": session["session_hash"],
                "convened_by": session["convened_by"],
                "resolution_type": session["resolution_type"],
                "voice_count": len(voices),
                "non_consenting_count": len(non_consenting),
            }
        )

    # --- Query methods ---

    def get_session(self, session_hash: str) -> dict:
        """Retrieve a session by hash."""
        conn = None
        try:
            conn = get_connection()
            cur = get_dict_cursor(conn)
            cur.execute("""
                SELECT * FROM longhouse_sessions
                WHERE session_hash = %s
            """, (session_hash,))
            result = cur.fetchone()
            if result is None:
                raise ValueError(f"No session found with hash {session_hash}")
            return dict(result)
        finally:
            if conn is not None:
                conn.close()

    def get_active_sessions(self) -> list:
        """List all sessions where the fire is still being tended (not resolved)."""
        conn = None
        try:
            conn = get_connection()
            cur = get_dict_cursor(conn)
            cur.execute("""
                SELECT id, session_hash, convened_by, convened_reason,
                       status, created_at
                FROM longhouse_sessions
                WHERE status != 'resolved'
                ORDER BY created_at DESC
            """)
            return [dict(row) for row in cur.fetchall()]
        finally:
            if conn is not None:
                conn.close()

    def get_resolved_sessions(self, limit: int = 20) -> list:
        """List recent resolved sessions — the governance record."""
        conn = None
        try:
            conn = get_connection()
            cur = get_dict_cursor(conn)
            cur.execute("""
                SELECT id, session_hash, convened_by, problem_statement,
                       resolution_type, resolution, resolved_at
                FROM longhouse_sessions
                WHERE status = 'resolved'
                ORDER BY resolved_at DESC
                LIMIT %s
            """, (limit,))
            return [dict(row) for row in cur.fetchall()]
        finally:
            if conn is not None:
                conn.close()
