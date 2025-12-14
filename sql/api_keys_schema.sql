-- Cherokee AI API Keys Schema
-- Deploy to: bluefin (192.168.132.222) sag_thermal_memory database
-- Created: 2025-12-12

-- Enable pgcrypto for secure random generation
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- API Keys table
CREATE TABLE IF NOT EXISTS api_keys (
    key_id VARCHAR(64) PRIMARY KEY,  -- SHA256 hash of actual key
    user_id VARCHAR(100) NOT NULL,
    description VARCHAR(255),
    quota_total INTEGER DEFAULT 10000,
    quota_used INTEGER DEFAULT 0,
    rate_limit INTEGER DEFAULT 60,  -- requests per minute
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,
    last_used TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    permissions JSONB DEFAULT '["chat", "models"]'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_api_keys_user ON api_keys(user_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_active ON api_keys(is_active) WHERE is_active = true;

-- Audit log for all API access
CREATE TABLE IF NOT EXISTS api_audit_log (
    log_id BIGSERIAL PRIMARY KEY,
    key_id VARCHAR(64),
    endpoint VARCHAR(100),
    method VARCHAR(10),
    status_code INTEGER,
    response_time_ms INTEGER,
    tokens_used INTEGER DEFAULT 0,
    client_ip INET,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_key ON api_audit_log(key_id);
CREATE INDEX IF NOT EXISTS idx_audit_time ON api_audit_log(created_at);

-- Function to create new API key (returns unhashed key ONCE)
CREATE OR REPLACE FUNCTION create_api_key(
    p_user_id VARCHAR,
    p_description VARCHAR DEFAULT NULL,
    p_quota INTEGER DEFAULT 10000,
    p_rate_limit INTEGER DEFAULT 60
) RETURNS TABLE(api_key VARCHAR, key_id VARCHAR) AS $$
DECLARE
    v_raw_key VARCHAR;
    v_key_hash VARCHAR;
BEGIN
    -- Generate random key with 'ck-' prefix (cherokee key)
    v_raw_key := 'ck-' || encode(gen_random_bytes(32), 'hex');
    v_key_hash := encode(sha256(v_raw_key::bytea), 'hex');

    INSERT INTO api_keys (key_id, user_id, description, quota_total, rate_limit)
    VALUES (v_key_hash, p_user_id, p_description, p_quota, p_rate_limit);

    -- Return raw key (only time it's visible) and hash for reference
    RETURN QUERY SELECT v_raw_key, v_key_hash;
END;
$$ LANGUAGE plpgsql;

-- Function to revoke an API key
CREATE OR REPLACE FUNCTION revoke_api_key(p_key_id VARCHAR) RETURNS BOOLEAN AS $$
BEGIN
    UPDATE api_keys SET is_active = false WHERE key_id = p_key_id;
    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

-- Function to reset quota (for monthly resets, etc.)
CREATE OR REPLACE FUNCTION reset_quota(p_key_id VARCHAR) RETURNS INTEGER AS $$
DECLARE
    v_quota INTEGER;
BEGIN
    UPDATE api_keys SET quota_used = 0 WHERE key_id = p_key_id
    RETURNING quota_total INTO v_quota;
    RETURN v_quota;
END;
$$ LANGUAGE plpgsql;

-- View: API key usage summary
CREATE OR REPLACE VIEW api_key_usage AS
SELECT
    k.key_id,
    k.user_id,
    k.description,
    k.quota_total,
    k.quota_used,
    k.quota_total - k.quota_used as quota_remaining,
    k.rate_limit,
    k.is_active,
    k.created_at,
    k.last_used,
    COUNT(a.log_id) as total_requests,
    AVG(a.response_time_ms) as avg_response_time_ms,
    SUM(a.tokens_used) as total_tokens_used
FROM api_keys k
LEFT JOIN api_audit_log a ON k.key_id = a.key_id
GROUP BY k.key_id, k.user_id, k.description, k.quota_total, k.quota_used,
         k.rate_limit, k.is_active, k.created_at, k.last_used;

-- Create initial admin API key
DO $$
DECLARE
    v_result RECORD;
BEGIN
    -- Check if admin key already exists
    IF NOT EXISTS (SELECT 1 FROM api_keys WHERE user_id = 'admin') THEN
        SELECT * INTO v_result FROM create_api_key('admin', 'Initial admin key', 100000, 120);
        RAISE NOTICE 'Created admin API key: %', v_result.api_key;
        RAISE NOTICE 'Key ID (hash): %', v_result.key_id;
        RAISE NOTICE 'SAVE THIS KEY - it will not be shown again!';
    ELSE
        RAISE NOTICE 'Admin key already exists';
    END IF;
END $$;

-- Create TPM-Claude API key
DO $$
DECLARE
    v_result RECORD;
BEGIN
    IF NOT EXISTS (SELECT 1 FROM api_keys WHERE user_id = 'tpm-claude') THEN
        SELECT * INTO v_result FROM create_api_key('tpm-claude', 'TPM Claude orchestrator', 50000, 60);
        RAISE NOTICE 'Created TPM-Claude API key: %', v_result.api_key;
        RAISE NOTICE 'SAVE THIS KEY - it will not be shown again!';
    END IF;
END $$;

-- Grant permissions
GRANT SELECT, INSERT, UPDATE ON api_keys TO claude;
GRANT SELECT, INSERT ON api_audit_log TO claude;
GRANT USAGE, SELECT ON SEQUENCE api_audit_log_log_id_seq TO claude;
GRANT SELECT ON api_key_usage TO claude;
