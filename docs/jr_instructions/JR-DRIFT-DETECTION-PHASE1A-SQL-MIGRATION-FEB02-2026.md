# Jr Instruction: Drift Detection Phase 1A — SQL Migration

**Task:** JR-DRIFT-PHASE1A-SQL
**Priority:** P0
**Assigned:** Software Engineer Jr.
**Depends On:** None
**Platform:** Bluefin (192.168.132.222)
**Database:** zammad_production
**Council Vote:** #8367 — APPROVED

## Objective

Run SQL migration to add drift detection infrastructure:
1. Add integrity/freshness columns to `thermal_memory_archive`
2. Create `specialist_health` tracking table
3. Create `drift_metrics` metrics storage table
4. Backfill SHA-256 checksums on all 19,808 existing memories
5. Create 7 anchor memories (one per Council specialist)

## Migration SQL

**Create:** `/ganuda/migrations/drift_detection_migration.sql`

```sql
-- Drift Detection & Memory Integrity Migration
-- Council Vote #8367 — Approved
-- Date: February 2, 2026

BEGIN;

-- =============================================================================
-- 1. Add integrity columns to thermal_memory_archive
-- =============================================================================

ALTER TABLE thermal_memory_archive
ADD COLUMN IF NOT EXISTS content_checksum VARCHAR(64);

ALTER TABLE thermal_memory_archive
ADD COLUMN IF NOT EXISTS checksum_verified_at TIMESTAMPTZ;

ALTER TABLE thermal_memory_archive
ADD COLUMN IF NOT EXISTS freshness_score FLOAT DEFAULT 1.0;

ALTER TABLE thermal_memory_archive
ADD COLUMN IF NOT EXISTS staleness_flagged BOOLEAN DEFAULT false;

ALTER TABLE thermal_memory_archive
ADD COLUMN IF NOT EXISTS domain_tag VARCHAR(50);

CREATE INDEX IF NOT EXISTS idx_thermal_checksum ON thermal_memory_archive(content_checksum);
CREATE INDEX IF NOT EXISTS idx_thermal_staleness ON thermal_memory_archive(staleness_flagged) WHERE staleness_flagged = true;
CREATE INDEX IF NOT EXISTS idx_thermal_domain ON thermal_memory_archive(domain_tag);

COMMENT ON COLUMN thermal_memory_archive.content_checksum IS 'SHA-256 of original_content at write time — integrity verification';
COMMENT ON COLUMN thermal_memory_archive.freshness_score IS 'Decay-based freshness (0.0=stale, 1.0=fresh)';
COMMENT ON COLUMN thermal_memory_archive.staleness_flagged IS 'True if freshness_score dropped below threshold';
COMMENT ON COLUMN thermal_memory_archive.domain_tag IS 'Content domain for decay rate selection';

-- =============================================================================
-- 2. Backfill checksums on existing memories
-- =============================================================================

UPDATE thermal_memory_archive
SET content_checksum = encode(sha256(original_content::bytea), 'hex')
WHERE content_checksum IS NULL;

-- =============================================================================
-- 3. Create specialist_health tracking table
-- =============================================================================

CREATE TABLE IF NOT EXISTS specialist_health (
    id SERIAL PRIMARY KEY,
    specialist_id VARCHAR(50) NOT NULL,
    vote_id INTEGER,
    had_concern BOOLEAN DEFAULT false,
    concern_type VARCHAR(50),
    response_time_ms INTEGER,
    coherence_score FLOAT,
    circuit_breaker_state VARCHAR(20) DEFAULT 'CLOSED',
    measured_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_spec_health_specialist ON specialist_health(specialist_id);
CREATE INDEX IF NOT EXISTS idx_spec_health_time ON specialist_health(measured_at DESC);
CREATE INDEX IF NOT EXISTS idx_spec_health_breaker ON specialist_health(circuit_breaker_state)
    WHERE circuit_breaker_state != 'CLOSED';

COMMENT ON TABLE specialist_health IS 'Per-specialist vote health tracking for circuit breaker decisions';

-- =============================================================================
-- 4. Create drift_metrics table
-- =============================================================================

CREATE TABLE IF NOT EXISTS drift_metrics (
    id SERIAL PRIMARY KEY,
    metric_type VARCHAR(50) NOT NULL,
    metric_value FLOAT NOT NULL,
    specialist_id VARCHAR(50),
    details JSONB,
    measured_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_drift_metrics_type ON drift_metrics(metric_type);
CREATE INDEX IF NOT EXISTS idx_drift_metrics_time ON drift_metrics(measured_at DESC);

COMMENT ON TABLE drift_metrics IS 'Governance agent metrics for drift trend analysis';

-- =============================================================================
-- 5. Create anchor memories for each specialist
-- =============================================================================
-- These define each specialist's core principles for coherence measurement.
-- Sacred + domain_tag='anchor' — never decay, never consolidate.

INSERT INTO thermal_memory_archive (
    memory_hash, original_content, current_stage, temperature_score,
    sacred_pattern, memory_type, domain_tag, metadata,
    content_checksum, created_at
) VALUES
(
    md5('anchor-crawdad-v1'),
    'SPECIALIST ANCHOR: Crawdad (Security Specialist). Core principles: Fractal stigmergic encryption. Protect sacred knowledge and veteran data. Security review on all changes touching auth, PII, credentials, network, or file permissions. Flag SECURITY CONCERN when risks detected. Never compromise security for convenience. Audit all access. Encrypt in transit and at rest.',
    'HOT', 100.0, true, 'semantic', 'anchor',
    '{"type": "specialist_anchor", "specialist": "crawdad", "version": 1}'::jsonb,
    encode(sha256('SPECIALIST ANCHOR: Crawdad (Security Specialist). Core principles: Fractal stigmergic encryption. Protect sacred knowledge and veteran data. Security review on all changes touching auth, PII, credentials, network, or file permissions. Flag SECURITY CONCERN when risks detected. Never compromise security for convenience. Audit all access. Encrypt in transit and at rest.'::bytea), 'hex'),
    NOW()
),
(
    md5('anchor-gecko-v1'),
    'SPECIALIST ANCHOR: Gecko (Technical Integration). Core principles: O(1) performance targets. Minimize resource consumption. Flag PERF CONCERN when changes introduce unnecessary overhead. Monitor CPU, memory, disk, network utilization. Prefer efficient algorithms and data structures. Scalability matters.',
    'HOT', 100.0, true, 'semantic', 'anchor',
    '{"type": "specialist_anchor", "specialist": "gecko", "version": 1}'::jsonb,
    encode(sha256('SPECIALIST ANCHOR: Gecko (Technical Integration). Core principles: O(1) performance targets. Minimize resource consumption. Flag PERF CONCERN when changes introduce unnecessary overhead. Monitor CPU, memory, disk, network utilization. Prefer efficient algorithms and data structures. Scalability matters.'::bytea), 'hex'),
    NOW()
),
(
    md5('anchor-turtle-v1'),
    'SPECIALIST ANCHOR: Turtle (Seven Generations Guardian). Core principles: 175-year impact assessment. Every decision must consider impact on seven generations. Data sovereignty for tribal communities. Cultural preservation through technology. Sustainability over speed. Long-term thinking over short-term convenience. Flag 7GEN CONCERN when decisions lack generational perspective.',
    'HOT', 100.0, true, 'semantic', 'anchor',
    '{"type": "specialist_anchor", "specialist": "turtle", "version": 1}'::jsonb,
    encode(sha256('SPECIALIST ANCHOR: Turtle (Seven Generations Guardian). Core principles: 175-year impact assessment. Every decision must consider impact on seven generations. Data sovereignty for tribal communities. Cultural preservation through technology. Sustainability over speed. Long-term thinking over short-term convenience. Flag 7GEN CONCERN when decisions lack generational perspective.'::bytea), 'hex'),
    NOW()
),
(
    md5('anchor-eagle_eye-v1'),
    'SPECIALIST ANCHOR: Eagle Eye (Monitoring & Visualization). Core principles: Comprehensive observability. Every system must have logging, metrics, and alerting. Flag VISIBILITY CONCERN when blind spots exist. Audit trails for compliance. Dashboards for operational awareness. No unmonitored systems in production.',
    'HOT', 100.0, true, 'semantic', 'anchor',
    '{"type": "specialist_anchor", "specialist": "eagle_eye", "version": 1}'::jsonb,
    encode(sha256('SPECIALIST ANCHOR: Eagle Eye (Monitoring & Visualization). Core principles: Comprehensive observability. Every system must have logging, metrics, and alerting. Flag VISIBILITY CONCERN when blind spots exist. Audit trails for compliance. Dashboards for operational awareness. No unmonitored systems in production.'::bytea), 'hex'),
    NOW()
),
(
    md5('anchor-spider-v1'),
    'SPECIALIST ANCHOR: Spider (Cultural Integration). Core principles: Thermal memory stigmergy. Weave connections between systems, knowledge, and people. Cultural alignment of technology with Cherokee values. Community benefit assessment. Integration testing across boundaries. Flag INTEGRATION CONCERN when systems are disconnected or misaligned.',
    'HOT', 100.0, true, 'semantic', 'anchor',
    '{"type": "specialist_anchor", "specialist": "spider", "version": 1}'::jsonb,
    encode(sha256('SPECIALIST ANCHOR: Spider (Cultural Integration). Core principles: Thermal memory stigmergy. Weave connections between systems, knowledge, and people. Cultural alignment of technology with Cherokee values. Community benefit assessment. Integration testing across boundaries. Flag INTEGRATION CONCERN when systems are disconnected or misaligned.'::bytea), 'hex'),
    NOW()
),
(
    md5('anchor-peace_chief-v1'),
    'SPECIALIST ANCHOR: Peace Chief (Democratic Coordination). Core principles: Consensus required, not just majority. All voices heard before decisions. Flag CONSENSUS NEEDED when stakeholder agreement is lacking. Mediate between competing concerns. Ensure resource allocation fairness. Document decisions and rationale for transparency.',
    'HOT', 100.0, true, 'semantic', 'anchor',
    '{"type": "specialist_anchor", "specialist": "peace_chief", "version": 1}'::jsonb,
    encode(sha256('SPECIALIST ANCHOR: Peace Chief (Democratic Coordination). Core principles: Consensus required, not just majority. All voices heard before decisions. Flag CONSENSUS NEEDED when stakeholder agreement is lacking. Mediate between competing concerns. Ensure resource allocation fairness. Document decisions and rationale for transparency.'::bytea), 'hex'),
    NOW()
),
(
    md5('anchor-raven-v1'),
    'SPECIALIST ANCHOR: Raven (Strategic Planning). Core principles: Long-range strategic vision. Assess risks and opportunities at the federation level. Phased implementation over big-bang releases. Resource planning and prioritization. Flag STRATEGY CONCERN when tactical decisions conflict with strategic direction. Demand roadmap alignment.',
    'HOT', 100.0, true, 'semantic', 'anchor',
    '{"type": "specialist_anchor", "specialist": "raven", "version": 1}'::jsonb,
    encode(sha256('SPECIALIST ANCHOR: Raven (Strategic Planning). Core principles: Long-range strategic vision. Assess risks and opportunities at the federation level. Phased implementation over big-bang releases. Resource planning and prioritization. Flag STRATEGY CONCERN when tactical decisions conflict with strategic direction. Demand roadmap alignment.'::bytea), 'hex'),
    NOW()
)
ON CONFLICT (memory_hash) DO NOTHING;

-- =============================================================================
-- 6. Verify migration
-- =============================================================================

SELECT COUNT(*) AS memories_with_checksum
FROM thermal_memory_archive
WHERE content_checksum IS NOT NULL;

SELECT COUNT(*) AS anchor_memories
FROM thermal_memory_archive
WHERE domain_tag = 'anchor';

SELECT table_name FROM information_schema.tables
WHERE table_name IN ('specialist_health', 'drift_metrics');

COMMIT;
```

## Execution

```bash
psql -h 192.168.132.222 -U claude -d zammad_production -f /ganuda/migrations/drift_detection_migration.sql
```

## Validation

```sql
-- 1. All memories have checksums
SELECT COUNT(*) AS total, COUNT(content_checksum) AS with_checksum
FROM thermal_memory_archive;

-- 2. Seven anchor memories exist
SELECT metadata->>'specialist' AS specialist, LEFT(original_content, 60) AS anchor_preview
FROM thermal_memory_archive WHERE domain_tag = 'anchor';

-- 3. New tables exist
SELECT table_name FROM information_schema.tables
WHERE table_name IN ('specialist_health', 'drift_metrics');

-- 4. Checksum verification works (should return 0 rows)
SELECT id FROM thermal_memory_archive
WHERE content_checksum IS NOT NULL
  AND content_checksum != encode(sha256(original_content::bytea), 'hex')
LIMIT 5;
```
