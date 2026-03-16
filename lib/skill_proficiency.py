"""
skill_proficiency: EMA Proficiency Tracker for SkillRL Curriculum Learning
Cherokee AI Federation — SkillRL-04

Tracks how good the organism is at each skill category using an Exponential
Moving Average. Weak categories get more attention from the curriculum selector.

From the Agentic Proposing paper: M(t+1) = (1-α) * M(t) + α * success_rate

Usage:
    from ganuda_db import get_connection
    conn = get_connection()
    prof = SkillProficiency(conn)
    prof.update("general", "file_operations", reward=0.8, success=True)
    score = prof.get_score("general", "file_operations")
    weakest = prof.get_weakest("general", limit=5)
"""

import logging
from datetime import datetime

import psycopg2.extras

logger = logging.getLogger(__name__)

# EMA smoothing factor — responsive to recent results while respecting history
ALPHA = 0.3

# Default score for unseen categories (uncertain)
DEFAULT_SCORE = 0.5


class SkillProficiency:
    """EMA-based proficiency tracker for skill categories."""

    def __init__(self, conn):
        """
        Initialize with a psycopg2 database connection.

        Args:
            conn: A psycopg2 connection object (caller manages lifecycle).
        """
        self.conn = conn

    def get_score(self, domain: str, category: str) -> float:
        """
        Return current proficiency score for a domain/category pair.

        Returns 0.5 for unseen categories (uncertain prior).

        Args:
            domain: Skill domain (e.g., 'general', 'trading').
            category: Skill category (e.g., 'file_operations', 'api_calls').

        Returns:
            float: Proficiency score between 0.0 (weak) and 1.0 (mastered).
        """
        cur = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            "SELECT proficiency_score FROM skill_proficiency "
            "WHERE domain = %s AND category = %s",
            (domain, category),
        )
        row = cur.fetchone()
        cur.close()
        if row is None:
            return DEFAULT_SCORE
        return float(row["proficiency_score"])

    def update(self, domain: str, category: str, reward: float, success: bool) -> float:
        """
        EMA update of proficiency score for a domain/category.

        Formula: new_score = (1 - ALPHA) * old_score + ALPHA * new_signal
        Where new_signal = reward if success, reward * 0.5 if failure.

        Upserts into the skill_proficiency table.

        Args:
            domain: Skill domain.
            category: Skill category.
            reward: Raw reward signal (0.0 to 1.0).
            success: Whether the task succeeded.

        Returns:
            float: The updated proficiency score.
        """
        new_signal = reward if success else reward * 0.5
        old_score = self.get_score(domain, category)
        new_score = (1 - ALPHA) * old_score + ALPHA * new_signal

        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT INTO skill_proficiency (domain, category, proficiency_score,
                                           total_attempts, successful_attempts, last_updated)
            VALUES (%s, %s, %s, 1, %s, %s)
            ON CONFLICT (domain, category) DO UPDATE SET
                proficiency_score = %s,
                total_attempts = skill_proficiency.total_attempts + 1,
                successful_attempts = skill_proficiency.successful_attempts + %s,
                last_updated = %s
            """,
            (
                domain, category, new_score,
                1 if success else 0, datetime.now(),
                new_score,
                1 if success else 0, datetime.now(),
            ),
        )
        self.conn.commit()
        cur.close()
        return new_score

    def get_weakest(self, domain: str, limit: int = 5) -> list:
        """
        Return the lowest proficiency categories that have been attempted at least 3 times.

        These are the curriculum targets — categories where the organism needs
        the most practice.

        Args:
            domain: Skill domain to query.
            limit: Maximum number of results (default 5).

        Returns:
            list[dict]: Weakest categories sorted by proficiency_score ascending.
        """
        cur = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            """
            SELECT domain, category, proficiency_score, total_attempts,
                   successful_attempts, last_updated
            FROM skill_proficiency
            WHERE domain = %s AND total_attempts >= 3
            ORDER BY proficiency_score ASC
            LIMIT %s
            """,
            (domain, limit),
        )
        rows = cur.fetchall()
        cur.close()
        return [dict(r) for r in rows]

    def get_vector(self, domain: str) -> dict:
        """
        Return the full proficiency vector for a domain.

        Used for curriculum sampling probability: P(category) ∝ (1 - proficiency)

        Args:
            domain: Skill domain to query.

        Returns:
            dict[str, float]: Mapping of category -> proficiency_score.
        """
        cur = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            "SELECT category, proficiency_score FROM skill_proficiency "
            "WHERE domain = %s ORDER BY category",
            (domain,),
        )
        rows = cur.fetchall()
        cur.close()
        return {row["category"]: float(row["proficiency_score"]) for row in rows}
