# Jr Instruction: SkillRL — Database Schema + Ring Registration

**Task ID**: To be assigned
**Priority**: P1
**Story Points**: 1
**Node**: bluefin (PostgreSQL)
**Blocks**: All other SkillRL tasks
**Epic**: SkillRL (Council vote `#b91e297a508525c3`)

## What This Delivers

Three database tables and one ring registration. After this task, the skill library has a home.

## Implementation

Run on bluefin PostgreSQL (`zammad_production` database):

```sql
-- Skill Library — learned reusable patterns
CREATE TABLE IF NOT EXISTS skill_library (
    id SERIAL PRIMARY KEY,
    skill_id VARCHAR(64) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    intent TEXT NOT NULL,
    method TEXT NOT NULL,
    difficulty INTEGER CHECK (difficulty BETWEEN 1 AND 10),
    tool_hints TEXT[],
    domain VARCHAR(50) DEFAULT 'general',

    -- Composition
    is_compound BOOLEAN DEFAULT FALSE,
    parent_skills VARCHAR(64)[],

    -- Governance
    council_vote_id VARCHAR(64),
    provenance_hash VARCHAR(64) NOT NULL,
    source_task_id INTEGER,
    status VARCHAR(20) DEFAULT 'candidate',

    -- UCB Stats (optimistic prior: 1 success / 2 uses)
    total_uses INTEGER DEFAULT 2,
    successful_uses INTEGER DEFAULT 1,
    total_reward NUMERIC(12,4) DEFAULT 1.0,
    avg_latency_ms NUMERIC(10,2) DEFAULT 0,

    -- Integrity (Eagle Eye condition)
    content_hash VARCHAR(64) NOT NULL,

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    last_used TIMESTAMP,
    retired_at TIMESTAMP,
    retire_reason TEXT
);

-- Proficiency tracking per skill category
CREATE TABLE IF NOT EXISTS skill_proficiency (
    id SERIAL PRIMARY KEY,
    domain VARCHAR(50) NOT NULL,
    category VARCHAR(100) NOT NULL,
    proficiency_score NUMERIC(5,4) DEFAULT 0.5,
    total_attempts INTEGER DEFAULT 0,
    successful_attempts INTEGER DEFAULT 0,
    last_updated TIMESTAMP DEFAULT NOW(),
    UNIQUE(domain, category)
);

-- Skill usage log (RL reward attribution)
CREATE TABLE IF NOT EXISTS skill_usage_log (
    id SERIAL PRIMARY KEY,
    skill_id VARCHAR(64) REFERENCES skill_library(skill_id),
    task_id INTEGER,
    domain VARCHAR(50),
    reward NUMERIC(5,4),
    success BOOLEAN,
    latency_ms INTEGER,
    used_at TIMESTAMP DEFAULT NOW()
);

-- Index for selector queries
CREATE INDEX IF NOT EXISTS idx_skill_library_domain_status
    ON skill_library(domain, status);
CREATE INDEX IF NOT EXISTS idx_skill_usage_log_skill_id
    ON skill_usage_log(skill_id);
CREATE INDEX IF NOT EXISTS idx_skill_proficiency_domain
    ON skill_proficiency(domain);

-- Register ring
INSERT INTO duplo_tool_registry (ring_name, ring_type, status, registered_at)
VALUES ('skill_rl', 'associate', 'active', NOW())
ON CONFLICT DO NOTHING;
```

## Verification

```sql
-- Tables exist
SELECT table_name FROM information_schema.tables
WHERE table_name IN ('skill_library', 'skill_proficiency', 'skill_usage_log');

-- Ring registered
SELECT * FROM duplo_tool_registry WHERE ring_name = 'skill_rl';

-- Indexes exist
SELECT indexname FROM pg_indexes WHERE tablename = 'skill_library';
```

## Definition of Done

- [ ] Three tables created on bluefin
- [ ] Indexes created
- [ ] `skill_rl` ring registered in duplo_tool_registry
- [ ] Verification queries return expected results
