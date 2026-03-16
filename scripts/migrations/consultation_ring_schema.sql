-- Consultation Ring: Multi-Model Consultation Service
-- Patent Brief #7: Tokenized Air-Gap Proxy
-- Council Vote: a3ee2a8066e04490 (UNANIMOUS)
-- Date: 2026-03-14
--
-- Deploy: psql -h 192.168.132.222 -U claude -d zammad_production -f consultation_ring_schema.sql

BEGIN;

-- ── Consultation model performance stats (UCB bandit) ──
CREATE TABLE IF NOT EXISTS consultation_model_stats (
    id SERIAL PRIMARY KEY,
    model_name VARCHAR(100) NOT NULL,
    provider VARCHAR(50) NOT NULL,
    domain VARCHAR(50) NOT NULL DEFAULT 'general',
    total_calls INTEGER DEFAULT 0,
    successful_calls INTEGER DEFAULT 0,
    total_reward NUMERIC(12,4) DEFAULT 0,
    avg_latency_ms NUMERIC(10,2) DEFAULT 0,
    total_cost NUMERIC(10,4) DEFAULT 0,
    last_called TIMESTAMP,
    enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(model_name, domain)
);

CREATE INDEX IF NOT EXISTS idx_consultation_stats_domain
    ON consultation_model_stats (domain, enabled);

CREATE INDEX IF NOT EXISTS idx_consultation_stats_provider
    ON consultation_model_stats (provider, enabled);

-- ── Consultation audit log ──
CREATE TABLE IF NOT EXISTS consultation_log (
    id SERIAL PRIMARY KEY,
    query_hash VARCHAR(64) NOT NULL,
    domain VARCHAR(50) NOT NULL DEFAULT 'general',
    model_selected VARCHAR(100) NOT NULL,
    provider VARCHAR(50) NOT NULL,
    tokenized BOOLEAN DEFAULT true,
    pii_tokens_replaced INTEGER DEFAULT 0,
    infra_tokens_replaced INTEGER DEFAULT 0,
    outbound_scrub_passed BOOLEAN DEFAULT true,
    valence_outcome VARCHAR(20) DEFAULT 'accept',
    valence_score NUMERIC(5,4),
    latency_ms INTEGER,
    cost NUMERIC(10,6),
    error TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_consultation_log_created
    ON consultation_log (created_at);

CREATE INDEX IF NOT EXISTS idx_consultation_log_model
    ON consultation_log (model_selected, created_at);

-- ── Seed frontier models for UCB bandit ──
-- Optimistic prior: 1 success / 2 total (encourages exploration)
INSERT INTO consultation_model_stats (model_name, provider, domain, total_calls, successful_calls, total_reward)
VALUES
    ('claude-sonnet-4-6', 'anthropic', 'general', 2, 1, 1.0),
    ('claude-sonnet-4-6', 'anthropic', 'code', 2, 1, 1.0),
    ('claude-sonnet-4-6', 'anthropic', 'research', 2, 1, 1.0),
    ('claude-sonnet-4-6', 'anthropic', 'legal', 2, 1, 1.0),
    ('gpt-4o', 'openai', 'general', 2, 1, 1.0),
    ('gpt-4o', 'openai', 'code', 2, 1, 1.0),
    ('gpt-4o', 'openai', 'research', 2, 1, 1.0),
    ('gemini-2.0-flash', 'google', 'general', 2, 1, 1.0),
    ('gemini-2.0-flash', 'google', 'research', 2, 1, 1.0),
    ('local-qwen-72b', 'local', 'general', 2, 1, 1.0),
    ('local-qwen-72b', 'local', 'code', 2, 1, 1.0),
    ('local-llama-70b', 'local', 'general', 2, 1, 1.0),
    ('local-llama-70b', 'local', 'code', 2, 1, 1.0),
    ('local-qwen3-30b', 'local', 'general', 2, 1, 1.0)
ON CONFLICT (model_name, domain) DO NOTHING;

-- ── Register consultation_ring in duplo_tool_registry ──
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
ON CONFLICT (tool_name) DO NOTHING;

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
