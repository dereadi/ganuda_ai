-- Consultation Ring: Multi-Model Consultation Service
-- Patent Brief #7: Tokenized Air-Gap Proxy
-- Council Vote: a3ee2a8066e04490 (UNANIMOUS)
-- Jr Task #1424: DB Migration + Config
-- Date: 2026-03-18
--
-- Deploy: psql -h 192.168.132.222 -U claude -d zammad_production -f consultation_ring_schema.sql

BEGIN;

-- ── Drop old schema if exists (v1 → v2 migration) ──
DROP TABLE IF EXISTS consultation_log CASCADE;
DROP TABLE IF EXISTS consultation_model_stats CASCADE;

-- ── Consultation log (audit trail, tokenized queries only) ──
CREATE TABLE consultation_log (
    id SERIAL PRIMARY KEY,
    query_hash VARCHAR(64) NOT NULL,
    query_text TEXT NOT NULL,
    domain VARCHAR(64),
    model_selected VARCHAR(128),
    adapter_used VARCHAR(64),
    response_text TEXT,
    valence_score FLOAT,
    valence_tier VARCHAR(20) CHECK (valence_tier IN ('accept','flag','reject')),
    token_count_in INTEGER,
    token_count_out INTEGER,
    latency_ms INTEGER,
    cost_estimate FLOAT DEFAULT 0.0,
    provenance JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_consultation_log_created ON consultation_log (created_at);
CREATE INDEX idx_consultation_log_model ON consultation_log (model_selected, created_at);
CREATE INDEX idx_consultation_log_domain ON consultation_log (domain);
CREATE INDEX idx_consultation_log_query_hash ON consultation_log (query_hash);

-- ── Consultation model performance stats (UCB1 bandit) ──
CREATE TABLE consultation_model_stats (
    id SERIAL PRIMARY KEY,
    model_name VARCHAR(128) NOT NULL UNIQUE,
    domain VARCHAR(64) DEFAULT 'general',
    total_pulls INTEGER DEFAULT 0,
    total_reward FLOAT DEFAULT 0.0,
    mean_reward FLOAT DEFAULT 0.0,
    last_selected_at TIMESTAMPTZ,
    enabled BOOLEAN DEFAULT true,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_consultation_stats_domain ON consultation_model_stats (domain, enabled);
CREATE INDEX idx_consultation_stats_enabled ON consultation_model_stats (enabled);

-- ── Seed frontier models for UCB1 bandit ──
-- Optimistic prior: 2 pulls, 1.0 total reward, 0.5 mean reward
INSERT INTO consultation_model_stats (model_name, domain, total_pulls, total_reward, mean_reward, enabled) VALUES
    ('anthropic/claude-sonnet-4-6', 'general', 2, 1.0, 0.5, true),
    ('local/qwen-72b', 'general', 2, 1.0, 0.5, true),
    ('openai/gpt-4o', 'general', 2, 1.0, 0.5, false),
    ('google/gemini-pro', 'general', 2, 1.0, 0.5, false);

-- ── Re-register consultation_ring in duplo_tool_registry ──
INSERT INTO duplo_tool_registry (
    tool_name, description, module_path, function_name, parameters,
    safety_class, ring_type, provider, ring_status, canonical_schema,
    removal_procedure, calibration_schedule, cost_budget_daily
)
VALUES (
    'consultation_ring',
    'Multi-model consultation ring — tokenized air-gap proxy for frontier model consultation',
    'services/consultation_ring.py',
    'consult',
    '{"query": "string", "context": "string", "domain": "string"}',
    'read',
    'associate',
    'multi_provider',
    'active',
    '{"input": {"query": "string", "context": "string", "domain": "general|code|research|legal"}, "output": {"response": "string", "model": "string", "valence": "string", "provenance": "object"}}',
    'Set consultation_ring.enabled: false in config.yaml. Service returns 503. No downstream dependencies — advisory only.',
    'weekly',
    10.00
)
ON CONFLICT (tool_name) DO UPDATE SET
    description = EXCLUDED.description,
    updated_at = NOW();

-- ── Add consultation-specific scrub rules ──
INSERT INTO scrub_rules (rule_type, pattern, applies_to) VALUES
    ('blocked_term', 'sasass', 'consultation_ring'),
    ('blocked_term', 'sasass2', 'consultation_ring'),
    ('blocked_term', 'thunderduck', 'consultation_ring'),
    ('blocked_term', 'ganuda.us', 'consultation_ring'),
    ('blocked_term', 'duplo_tool_registry', 'consultation_ring'),
    ('blocked_term', 'thermal_memory_archive', 'consultation_ring'),
    ('blocked_term', 'cherokee_identity', 'consultation_ring'),
    ('blocked_term', 'consultation_model_stats', 'consultation_ring'),
    ('blocked_term', 'secrets.env', 'consultation_ring'),
    ('blocked_term', 'dereadi', 'consultation_ring'),
    ('regex', '\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', 'consultation_ring'),
    ('regex', 'sk-ant-api\w+', 'consultation_ring'),
    ('regex', 'sk-\w{20,}', 'consultation_ring'),
    ('regex', 'xoxb-\w+', 'consultation_ring')
ON CONFLICT DO NOTHING;

COMMIT;
