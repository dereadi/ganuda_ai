# Jr Instruction: Elder Interview Management Workflow

**Task**: Build workflow for managing elder interview transcription and archival
**Council Vote**: #33e50dc466de520e (RC-2026-02C, Turtle's cultural pick)
**Kanban**: #5
**Priority**: 6
**Assigned Jr**: Software Engineer Jr.
**Story Points**: 8

## Context

Elder interviews are the most culturally precious content in the federation. Currently there's no structured workflow for:
1. Tracking which interviews exist and their processing state
2. Prioritizing by elder age/urgency
3. Managing transcription quality review
4. Archiving completed transcriptions into thermal memory with sacred protection

This creates a database-backed workflow with SAG dashboard integration.

## Step 1: Create elder interview schema migration

Create `/ganuda/scripts/migrations/elder_interview_schema.sql`

```python
-- Elder Interview Management Workflow
-- Council Vote #33e50dc466de520e — Turtle's Seven Generations pick
-- Kanban #5

BEGIN;

CREATE TABLE IF NOT EXISTS elder_interviews (
    id SERIAL PRIMARY KEY,

    -- Elder info
    elder_name VARCHAR(200) NOT NULL,
    elder_age INTEGER,
    clan VARCHAR(100),
    community VARCHAR(200),

    -- Interview details
    interview_date DATE,
    interviewer VARCHAR(200),
    duration_minutes INTEGER,
    language VARCHAR(50) DEFAULT 'english',
    topics TEXT[],

    -- Media tracking
    audio_file_path VARCHAR(500),
    video_file_path VARCHAR(500),
    file_format VARCHAR(20),
    file_size_mb FLOAT,

    -- Processing state
    status VARCHAR(30) DEFAULT 'recorded'
        CHECK (status IN ('recorded', 'queued', 'transcribing', 'review', 'approved', 'archived', 'sacred_hold')),
    priority INTEGER DEFAULT 5 CHECK (priority >= 1 AND priority <= 10),
    urgency_reason TEXT,

    -- Transcription
    transcription_text TEXT,
    transcription_method VARCHAR(50),
    transcription_confidence FLOAT,
    reviewed_by VARCHAR(200),
    review_date TIMESTAMP,
    review_notes TEXT,

    -- Cultural sensitivity
    cultural_sensitivity VARCHAR(20) DEFAULT 'normal'
        CHECK (cultural_sensitivity IN ('normal', 'sensitive', 'sacred', 'restricted')),
    sacred_categories TEXT[],
    access_restriction TEXT,

    -- Archival
    thermal_memory_hashes TEXT[],
    archived_at TIMESTAMP,

    -- Metadata
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_elder_interviews_status ON elder_interviews(status);
CREATE INDEX IF NOT EXISTS idx_elder_interviews_priority ON elder_interviews(priority DESC);
CREATE INDEX IF NOT EXISTS idx_elder_interviews_elder ON elder_interviews(elder_name);
CREATE INDEX IF NOT EXISTS idx_elder_interviews_sensitivity ON elder_interviews(cultural_sensitivity);

-- Priority trigger: older elders get higher priority
CREATE OR REPLACE FUNCTION update_elder_interview_priority()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.elder_age IS NOT NULL AND NEW.elder_age >= 80 THEN
        NEW.priority = GREATEST(NEW.priority, 9);
        NEW.urgency_reason = COALESCE(NEW.urgency_reason, 'Elder age >= 80 — auto-elevated priority');
    ELSIF NEW.elder_age IS NOT NULL AND NEW.elder_age >= 70 THEN
        NEW.priority = GREATEST(NEW.priority, 7);
    END IF;
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS elder_interview_priority_trigger ON elder_interviews;
CREATE TRIGGER elder_interview_priority_trigger
    BEFORE INSERT OR UPDATE ON elder_interviews
    FOR EACH ROW EXECUTE FUNCTION update_elder_interview_priority();

COMMIT;
```

## Step 2: Create interview workflow manager

Create `/ganuda/lib/elder_interview_workflow.py`

```python
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
```

## Manual Steps

Run the schema migration on bluefin:

```text
PGPASSWORD='TYDo5U2NVkXqQ8DHuhIpvRgLUrXf2iZE' psql -h 192.168.132.222 -U claude -d zammad_production -f /ganuda/scripts/migrations/elder_interview_schema.sql
```

Verify table created:

```text
PGPASSWORD='TYDo5U2NVkXqQ8DHuhIpvRgLUrXf2iZE' psql -h 192.168.132.222 -U claude -d zammad_production -c "SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'elder_interviews' ORDER BY ordinal_position;"
```

## Success Criteria

- [ ] `elder_interviews` table created with priority trigger
- [ ] Elders age 80+ auto-elevated to priority 9
- [ ] `register_interview()` creates new interview records
- [ ] `submit_transcription()` transitions to review state
- [ ] `approve_and_archive()` stores in thermal_memory_archive with sacred protection
- [ ] `get_queue()` returns interviews ordered by priority
- [ ] Sacred interviews get `sacred_pattern = true` in thermal memory

---

*For Seven Generations - Cherokee AI Federation*
