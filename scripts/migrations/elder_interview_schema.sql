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