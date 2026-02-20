"""
Elder Interview Workflow Manager — Cherokee AI Federation

Manages the lifecycle of elder interview recordings from capture to
thermal memory archival. Ensures cultural sensitivity at every step.

Turtle's Seven Generations pick — Council Vote #33e50dc466de520e.
"""

import hashlib
import logging
from datetime import datetime
from typing import Dict, List, Optional

import psycopg2
import psycopg2.extras
from psycopg2.extras import Json

from lib.secrets_loader import get_db_config

logger = logging.getLogger(__name__)
DB_CONFIG = get_db_config()


def get_conn():
    return psycopg2.connect(**DB_CONFIG)


def register_interview(elder_name: str, interview_date: str,
                       interviewer: str, topics: List[str] = None,
                       elder_age: int = None, clan: str = None,
                       audio_path: str = None, **kwargs) -> int:
    """Register a new elder interview in the workflow."""
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO elder_interviews
                    (elder_name, elder_age, clan, interview_date, interviewer,
                     topics, audio_file_path, status, metadata)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 'recorded', %s)
                RETURNING id
            """, (elder_name, elder_age, clan, interview_date, interviewer,
                  topics, audio_path, Json(kwargs)))
            interview_id = cur.fetchone()[0]
        conn.commit()
        logger.info("Registered interview #%d: %s with %s", interview_id, elder_name, interviewer)
        return interview_id
    finally:
        conn.close()


def update_status(interview_id: int, new_status: str, notes: str = None) -> bool:
    """Update interview processing status."""
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE elder_interviews
                SET status = %s, review_notes = COALESCE(%s, review_notes)
                WHERE id = %s
                RETURNING id
            """, (new_status, notes, interview_id))
            updated = cur.fetchone() is not None
        conn.commit()
        return updated
    finally:
        conn.close()


def submit_transcription(interview_id: int, transcription: str,
                         method: str = "manual",
                         confidence: float = 1.0) -> bool:
    """Submit transcription for an interview."""
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE elder_interviews
                SET transcription_text = %s,
                    transcription_method = %s,
                    transcription_confidence = %s,
                    status = 'review'
                WHERE id = %s
                RETURNING id
            """, (transcription, method, confidence, interview_id))
            updated = cur.fetchone() is not None
        conn.commit()
        return updated
    finally:
        conn.close()


def approve_and_archive(interview_id: int, reviewed_by: str,
                        cultural_sensitivity: str = "normal",
                        sacred_categories: List[str] = None) -> Dict:
    """Approve transcription and archive to thermal memory."""
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT elder_name, transcription_text, topics, interview_date, clan
                FROM elder_interviews WHERE id = %s AND status = 'review'
            """, (interview_id,))
            row = cur.fetchone()

            if not row:
                return {"error": "Interview not found or not in review status"}

            elder_name, transcription, topics, interview_date, clan = row

            if not transcription:
                return {"error": "No transcription to archive"}

            # Create thermal memory from transcription
            memory_content = (
                f"ELDER INTERVIEW: {elder_name}"
                f"{' (Clan: ' + clan + ')' if clan else ''}"
                f" — {interview_date}\n"
                f"Topics: {', '.join(topics) if topics else 'general'}\n\n"
                f"{transcription}"
            )
            memory_hash = hashlib.sha256(memory_content.encode()).hexdigest()

            is_sacred = cultural_sensitivity in ("sacred", "restricted")

            # Insert into thermal memory
            cur.execute("""
                INSERT INTO thermal_memory_archive
                    (memory_hash, original_content, temperature_score,
                     sacred_pattern, memory_type, tags, metadata)
                VALUES (%s, %s, %s, %s, 'semantic', %s, %s)
                ON CONFLICT (memory_hash) DO NOTHING
                RETURNING id
            """, (
                memory_hash,
                memory_content,
                95 if is_sacred else 85,
                is_sacred,
                ["elder_interview", elder_name.lower().replace(" ", "_")]
                    + (sacred_categories or []),
                Json({
                    "source": "elder_interview",
                    "interview_id": interview_id,
                    "elder_name": elder_name,
                    "cultural_sensitivity": cultural_sensitivity,
                }),
            ))

            # Update interview record
            cur.execute("""
                UPDATE elder_interviews
                SET status = 'archived',
                    cultural_sensitivity = %s,
                    sacred_categories = %s,
                    thermal_memory_hashes = ARRAY[%s],
                    archived_at = NOW(),
                    reviewed_by = %s,
                    review_date = NOW()
                WHERE id = %s
            """, (cultural_sensitivity, sacred_categories,
                  memory_hash, reviewed_by, interview_id))

        conn.commit()
        return {
            "interview_id": interview_id,
            "memory_hash": memory_hash,
            "sacred": is_sacred,
            "status": "archived",
        }
    finally:
        conn.close()


def get_queue(status: str = None, limit: int = 20) -> List[Dict]:
    """Get interview queue, ordered by priority."""
    conn = get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            if status:
                cur.execute("""
                    SELECT id, elder_name, elder_age, clan, interview_date,
                           status, priority, cultural_sensitivity, urgency_reason
                    FROM elder_interviews
                    WHERE status = %s
                    ORDER BY priority DESC, created_at
                    LIMIT %s
                """, (status, limit))
            else:
                cur.execute("""
                    SELECT id, elder_name, elder_age, clan, interview_date,
                           status, priority, cultural_sensitivity, urgency_reason
                    FROM elder_interviews
                    WHERE status NOT IN ('archived', 'sacred_hold')
                    ORDER BY priority DESC, created_at
                    LIMIT %s
                """, (limit,))
            return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()