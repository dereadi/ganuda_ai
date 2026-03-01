-- Duplo Enzyme System + ATP Accounting + Epigenetic Modifiers
-- The Living Cell Architecture — Cherokee AI Federation
-- March 1, 2026
--
-- Phase 1: Duplo tool registry, context profiles, usage tracking
-- Phase 2: Token ledger (ATP/ADP cycle)
-- Phase 3: Epigenetic modifiers
--
-- Run on bluefin (192.168.132.222) as postgres user:
--   psql -U claude -d zammad_production -f duplo_schema.sql

BEGIN;

-- ============================================================
-- Phase 1: Duplo Enzyme System
-- ============================================================

-- Tool registry — the amino acids (atomic capabilities)
CREATE TABLE IF NOT EXISTS duplo_tool_registry (
    tool_id         SERIAL PRIMARY KEY,
    tool_name       VARCHAR(128) NOT NULL UNIQUE,
    description     TEXT NOT NULL,
    module_path     VARCHAR(256) NOT NULL,       -- e.g. 'lib.ganuda_db' or 'lib.specialist_council'
    function_name   VARCHAR(128) NOT NULL,       -- e.g. 'execute_query' or 'query_thermal_memory_semantic'
    parameters      JSONB NOT NULL DEFAULT '{}', -- parameter schema {name: {type, required, description}}
    return_type     VARCHAR(64) DEFAULT 'any',   -- 'str', 'dict', 'list', 'bool', 'any'
    safety_class    VARCHAR(16) NOT NULL DEFAULT 'read',  -- 'read', 'write', 'execute', 'admin'
    requires_auth   BOOLEAN NOT NULL DEFAULT FALSE,
    active          BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_duplo_tools_safety ON duplo_tool_registry(safety_class);
CREATE INDEX IF NOT EXISTS idx_duplo_tools_active ON duplo_tool_registry(active) WHERE active = TRUE;

-- Context profiles — the enzyme active sites (stored in YAML on disk, metadata here)
CREATE TABLE IF NOT EXISTS duplo_context_profiles (
    profile_id      SERIAL PRIMARY KEY,
    profile_name    VARCHAR(128) NOT NULL UNIQUE,   -- e.g. 'crawdad_enzyme', 'thermal_writer'
    description     TEXT NOT NULL,
    yaml_path       VARCHAR(256) NOT NULL,           -- path to YAML file on disk
    tool_set        TEXT[] NOT NULL DEFAULT '{}',     -- array of tool_name references
    default_model   VARCHAR(64) DEFAULT 'qwen',      -- 'qwen', 'deepseek', 'vlm'
    max_tokens      INTEGER NOT NULL DEFAULT 512,
    temperature     REAL NOT NULL DEFAULT 0.3,
    active          BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Duplo invocation log — enzyme reaction tracking
CREATE TABLE IF NOT EXISTS duplo_usage_log (
    usage_id        BIGSERIAL PRIMARY KEY,
    profile_name    VARCHAR(128) NOT NULL,
    caller_id       VARCHAR(128) NOT NULL,           -- who invoked this enzyme
    substrate       TEXT,                             -- input summary (truncated)
    product         TEXT,                             -- output summary (truncated)
    tools_used      TEXT[] DEFAULT '{}',              -- which tools were actually called
    input_tokens    INTEGER NOT NULL DEFAULT 0,
    output_tokens   INTEGER NOT NULL DEFAULT 0,
    model_used      VARCHAR(128),
    latency_ms      INTEGER NOT NULL DEFAULT 0,
    success         BOOLEAN NOT NULL DEFAULT TRUE,
    error_message   TEXT,
    modifiers       JSONB DEFAULT '{}',               -- active epigenetic modifiers at invocation time
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_duplo_usage_profile ON duplo_usage_log(profile_name);
CREATE INDEX IF NOT EXISTS idx_duplo_usage_caller ON duplo_usage_log(caller_id);
CREATE INDEX IF NOT EXISTS idx_duplo_usage_time ON duplo_usage_log(created_at);

-- ============================================================
-- Phase 2: ATP Accounting — Token Ledger
-- ============================================================

-- Append-only token ledger — every LLM call logged
CREATE TABLE IF NOT EXISTS token_ledger (
    ledger_id       BIGSERIAL PRIMARY KEY,
    model           VARCHAR(128) NOT NULL,           -- model name/path
    caller_id       VARCHAR(128) NOT NULL,           -- service/specialist/enzyme that made the call
    call_type       VARCHAR(64) DEFAULT 'inference', -- 'inference', 'council_vote', 'jr_task', 'duplo_enzyme', 'embedding'
    input_tokens    INTEGER NOT NULL DEFAULT 0,
    output_tokens   INTEGER NOT NULL DEFAULT 0,
    total_tokens    INTEGER GENERATED ALWAYS AS (input_tokens + output_tokens) STORED,
    estimated_cost  NUMERIC(10,6) DEFAULT 0.0,       -- USD estimate
    latency_ms      INTEGER DEFAULT 0,
    metadata        JSONB DEFAULT '{}',               -- additional context (task_id, vote_hash, etc.)
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_token_ledger_model ON token_ledger(model);
CREATE INDEX IF NOT EXISTS idx_token_ledger_caller ON token_ledger(caller_id);
CREATE INDEX IF NOT EXISTS idx_token_ledger_type ON token_ledger(call_type);
CREATE INDEX IF NOT EXISTS idx_token_ledger_time ON token_ledger(created_at);

-- Daily summary materialized view for dashboarding
CREATE MATERIALIZED VIEW IF NOT EXISTS token_daily_summary AS
SELECT
    date_trunc('day', created_at) AS day,
    model,
    call_type,
    COUNT(*) AS call_count,
    SUM(input_tokens) AS total_input_tokens,
    SUM(output_tokens) AS total_output_tokens,
    SUM(input_tokens + output_tokens) AS total_tokens,
    SUM(estimated_cost) AS total_cost,
    AVG(latency_ms) AS avg_latency_ms
FROM token_ledger
GROUP BY date_trunc('day', created_at), model, call_type
ORDER BY day DESC;

-- ============================================================
-- Phase 3: Epigenetic Modifiers
-- ============================================================

-- Modifiers that adjust enzyme/specialist behavior without changing prompts
CREATE TABLE IF NOT EXISTS epigenetic_modifiers (
    modifier_id     SERIAL PRIMARY KEY,
    condition_name  VARCHAR(128) NOT NULL,            -- e.g. 'security_incident', 'high_load', 'night_mode'
    target          VARCHAR(128) NOT NULL,            -- specialist/enzyme name, or '*' for all
    modifier_type   VARCHAR(32) NOT NULL DEFAULT 'weight',  -- 'weight', 'suppress', 'amplify', 'inject'
    modifier_value  JSONB NOT NULL DEFAULT '{}',      -- {weight: 1.5} or {inject: "extra context"} or {suppress: true}
    active          BOOLEAN NOT NULL DEFAULT FALSE,   -- must be explicitly activated
    activated_at    TIMESTAMPTZ,
    activated_by    VARCHAR(128),                     -- who/what turned it on
    expires_at      TIMESTAMPTZ,                      -- auto-deactivate (null = manual only)
    description     TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_epigenetic_active ON epigenetic_modifiers(active) WHERE active = TRUE;
CREATE INDEX IF NOT EXISTS idx_epigenetic_condition ON epigenetic_modifiers(condition_name);
CREATE INDEX IF NOT EXISTS idx_epigenetic_target ON epigenetic_modifiers(target);

COMMIT;
