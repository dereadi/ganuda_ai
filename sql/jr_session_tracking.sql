-- SQL script to create table and indexes for tracking execution sessions

CREATE TABLE IF NOT EXISTS jr_execution_sessions (
    session_id UUID PRIMARY KEY,
    task_id VARCHAR(100) NOT NULL,
    jr_name VARCHAR(100) NOT NULL,
    model_tier VARCHAR(20),
    status VARCHAR(20) DEFAULT 'pending',
    steps JSONB,
    total_tokens INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_jr_sessions_status ON jr_execution_sessions(status);
CREATE INDEX IF NOT EXISTS idx_jr_sessions_jr_name ON jr_execution_sessions(jr_name);
CREATE INDEX IF NOT EXISTS idx_jr_sessions_created ON jr_execution_sessions(created_at DESC);