-- Longhouse (Gaduyi) — Digital Council House for the Cherokee AI Federation
-- Chief directive: "We talk as individuals and decide as one."
--
-- The traditional Cherokee council house was seven-sided, one section per clan,
-- all equidistant from the Sacred Fire. Any person could speak. No one was
-- interrupted. Consensus, not majority vote. One voice of non-consent could
-- halt a decision. The Sacred Fire burned continuously.
--
-- This table is the digital Gaduyi. The fire is always burning.

CREATE TABLE IF NOT EXISTS longhouse_sessions (
    id SERIAL PRIMARY KEY,
    session_hash VARCHAR(16) NOT NULL UNIQUE,  -- sha256[:16] audit trail

    -- Who called the meeting
    convened_by VARCHAR(100) NOT NULL,          -- any federation member
    convened_reason TEXT NOT NULL,              -- the problem presented

    -- The session
    status VARCHAR(20) NOT NULL DEFAULT 'convened',
        -- convened: meeting called, fire lit
        -- speaking: voices are being heard
        -- deciding: solution proposed, seeking consensus
        -- resolved: consensus reached or deferred
    problem_statement TEXT NOT NULL,
    proposed_solution TEXT,                     -- may emerge during discussion

    -- Voices (JSONB array — everyone who speaks, in order, uninterrupted)
    voices JSONB NOT NULL DEFAULT '[]',
        -- [{speaker, role, words, spoken_at}]
        -- No summarization. Every word preserved.

    -- Resolution
    resolution TEXT,                            -- the decision reached
    resolution_type VARCHAR(20),
        -- consensus: all present agree
        -- deferred: non-consent, matter tabled
        -- withdrawn: convener withdrew the question
    non_consenting JSONB NOT NULL DEFAULT '[]',
        -- [{member, role, reason}]
        -- Dissenters recorded with respect, not overruled

    -- The fire
    sacred_fire_lit BOOLEAN NOT NULL DEFAULT TRUE,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMPTZ,

    -- Constraints
    CONSTRAINT valid_status CHECK (
        status IN ('convened', 'speaking', 'deciding', 'resolved')
    ),
    CONSTRAINT valid_resolution_type CHECK (
        resolution_type IS NULL OR
        resolution_type IN ('consensus', 'deferred', 'withdrawn')
    )
);

-- Index for active sessions
CREATE INDEX IF NOT EXISTS idx_longhouse_active
    ON longhouse_sessions (status) WHERE status != 'resolved';

-- Index for audit trail
CREATE INDEX IF NOT EXISTS idx_longhouse_hash
    ON longhouse_sessions (session_hash);

-- Index for who convened
CREATE INDEX IF NOT EXISTS idx_longhouse_convener
    ON longhouse_sessions (convened_by);

-- Index for chronological review
CREATE INDEX IF NOT EXISTS idx_longhouse_created
    ON longhouse_sessions (created_at DESC);
