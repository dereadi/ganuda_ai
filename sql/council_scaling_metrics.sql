-- Council Scaling Metrics Schema
-- Cherokee AI Federation - Multi-Agent Optimization
-- For Seven Generations

-- Add scaling metrics columns to council_votes
ALTER TABLE council_votes ADD COLUMN IF NOT EXISTS query_type VARCHAR(20);
ALTER TABLE council_votes ADD COLUMN IF NOT EXISTS mode_auto_selected BOOLEAN DEFAULT false;
ALTER TABLE council_votes ADD COLUMN IF NOT EXISTS error_containment_triggered BOOLEAN DEFAULT false;
ALTER TABLE council_votes ADD COLUMN IF NOT EXISTS specialist_count INTEGER;

-- Create scaling metrics view
CREATE OR REPLACE VIEW council_scaling_metrics AS
SELECT
    date_trunc('hour', created_at) as hour,
    vote_mode,
    query_type,
    COUNT(*) as vote_count,
    AVG(confidence) as avg_confidence,
    AVG(response_time_ms) as avg_latency,
    SUM(CASE WHEN error_containment_triggered THEN 1 ELSE 0 END) as error_containments,
    AVG(specialist_count) as avg_specialists
FROM council_votes
WHERE created_at > NOW() - INTERVAL '7 days'
GROUP BY date_trunc('hour', created_at), vote_mode, query_type
ORDER BY hour DESC;

-- Index for faster analytics queries
CREATE INDEX IF NOT EXISTS idx_council_votes_mode_created
ON council_votes(vote_mode, created_at);