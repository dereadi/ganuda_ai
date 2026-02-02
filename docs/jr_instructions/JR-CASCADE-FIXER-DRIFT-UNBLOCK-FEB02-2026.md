# Jr Instruction: Cascade Fixer — Unblock Drift Detection Pipeline

**Task:** JR-CASCADE-FIXER-001
**Priority:** P0
**Assigned:** Software Engineer Jr.
**Depends On:** None
**Council Vote:** #8367 — APPROVED

## Objective

Run the corrected Phase 1A SQL migration (using `convert_to()` instead of `::bytea` cast), then re-queue downstream drift detection tasks #531-535 so the full pipeline can execute.

**Note:** research_worker.py syntax fixes were applied directly by TPM. This instruction handles the SQL migration and re-queue only.

## Step 1: Run corrected Phase 1A SQL migration

```sql
BEGIN;

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

UPDATE thermal_memory_archive
SET content_checksum = encode(sha256(convert_to(original_content, 'UTF8')), 'hex')
WHERE content_checksum IS NULL;

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
    encode(sha256(convert_to('SPECIALIST ANCHOR: Crawdad (Security Specialist). Core principles: Fractal stigmergic encryption. Protect sacred knowledge and veteran data. Security review on all changes touching auth, PII, credentials, network, or file permissions. Flag SECURITY CONCERN when risks detected. Never compromise security for convenience. Audit all access. Encrypt in transit and at rest.', 'UTF8')), 'hex'),
    NOW()
),
(
    md5('anchor-gecko-v1'),
    'SPECIALIST ANCHOR: Gecko (Technical Integration). Core principles: O(1) performance targets. Minimize resource consumption. Flag PERF CONCERN when changes introduce unnecessary overhead. Monitor CPU, memory, disk, network utilization. Prefer efficient algorithms and data structures. Scalability matters.',
    'HOT', 100.0, true, 'semantic', 'anchor',
    '{"type": "specialist_anchor", "specialist": "gecko", "version": 1}'::jsonb,
    encode(sha256(convert_to('SPECIALIST ANCHOR: Gecko (Technical Integration). Core principles: O(1) performance targets. Minimize resource consumption. Flag PERF CONCERN when changes introduce unnecessary overhead. Monitor CPU, memory, disk, network utilization. Prefer efficient algorithms and data structures. Scalability matters.', 'UTF8')), 'hex'),
    NOW()
),
(
    md5('anchor-turtle-v1'),
    'SPECIALIST ANCHOR: Turtle (Seven Generations Guardian). Core principles: 175-year impact assessment. Every decision must consider impact on seven generations. Data sovereignty for tribal communities. Cultural preservation through technology. Sustainability over speed. Long-term thinking over short-term convenience. Flag 7GEN CONCERN when decisions lack generational perspective.',
    'HOT', 100.0, true, 'semantic', 'anchor',
    '{"type": "specialist_anchor", "specialist": "turtle", "version": 1}'::jsonb,
    encode(sha256(convert_to('SPECIALIST ANCHOR: Turtle (Seven Generations Guardian). Core principles: 175-year impact assessment. Every decision must consider impact on seven generations. Data sovereignty for tribal communities. Cultural preservation through technology. Sustainability over speed. Long-term thinking over short-term convenience. Flag 7GEN CONCERN when decisions lack generational perspective.', 'UTF8')), 'hex'),
    NOW()
),
(
    md5('anchor-eagle_eye-v1'),
    'SPECIALIST ANCHOR: Eagle Eye (Monitoring & Visualization). Core principles: Comprehensive observability. Every system must have logging, metrics, and alerting. Flag VISIBILITY CONCERN when blind spots exist. Audit trails for compliance. Dashboards for operational awareness. No unmonitored systems in production.',
    'HOT', 100.0, true, 'semantic', 'anchor',
    '{"type": "specialist_anchor", "specialist": "eagle_eye", "version": 1}'::jsonb,
    encode(sha256(convert_to('SPECIALIST ANCHOR: Eagle Eye (Monitoring & Visualization). Core principles: Comprehensive observability. Every system must have logging, metrics, and alerting. Flag VISIBILITY CONCERN when blind spots exist. Audit trails for compliance. Dashboards for operational awareness. No unmonitored systems in production.', 'UTF8')), 'hex'),
    NOW()
),
(
    md5('anchor-spider-v1'),
    'SPECIALIST ANCHOR: Spider (Cultural Integration). Core principles: Thermal memory stigmergy. Weave connections between systems, knowledge, and people. Cultural alignment of technology with Cherokee values. Community benefit assessment. Integration testing across boundaries. Flag INTEGRATION CONCERN when systems are disconnected or misaligned.',
    'HOT', 100.0, true, 'semantic', 'anchor',
    '{"type": "specialist_anchor", "specialist": "spider", "version": 1}'::jsonb,
    encode(sha256(convert_to('SPECIALIST ANCHOR: Spider (Cultural Integration). Core principles: Thermal memory stigmergy. Weave connections between systems, knowledge, and people. Cultural alignment of technology with Cherokee values. Community benefit assessment. Integration testing across boundaries. Flag INTEGRATION CONCERN when systems are disconnected or misaligned.', 'UTF8')), 'hex'),
    NOW()
),
(
    md5('anchor-peace_chief-v1'),
    'SPECIALIST ANCHOR: Peace Chief (Democratic Coordination). Core principles: Consensus required, not just majority. All voices heard before decisions. Flag CONSENSUS NEEDED when stakeholder agreement is lacking. Mediate between competing concerns. Ensure resource allocation fairness. Document decisions and rationale for transparency.',
    'HOT', 100.0, true, 'semantic', 'anchor',
    '{"type": "specialist_anchor", "specialist": "peace_chief", "version": 1}'::jsonb,
    encode(sha256(convert_to('SPECIALIST ANCHOR: Peace Chief (Democratic Coordination). Core principles: Consensus required, not just majority. All voices heard before decisions. Flag CONSENSUS NEEDED when stakeholder agreement is lacking. Mediate between competing concerns. Ensure resource allocation fairness. Document decisions and rationale for transparency.', 'UTF8')), 'hex'),
    NOW()
),
(
    md5('anchor-raven-v1'),
    'SPECIALIST ANCHOR: Raven (Strategic Planning). Core principles: Long-range strategic vision. Assess risks and opportunities at the federation level. Phased implementation over big-bang releases. Resource planning and prioritization. Flag STRATEGY CONCERN when tactical decisions conflict with strategic direction. Demand roadmap alignment.',
    'HOT', 100.0, true, 'semantic', 'anchor',
    '{"type": "specialist_anchor", "specialist": "raven", "version": 1}'::jsonb,
    encode(sha256(convert_to('SPECIALIST ANCHOR: Raven (Strategic Planning). Core principles: Long-range strategic vision. Assess risks and opportunities at the federation level. Phased implementation over big-bang releases. Resource planning and prioritization. Flag STRATEGY CONCERN when tactical decisions conflict with strategic direction. Demand roadmap alignment.', 'UTF8')), 'hex'),
    NOW()
)
ON CONFLICT (memory_hash) DO NOTHING;

COMMIT;
```

## Step 2: Re-queue downstream drift detection tasks

```sql
UPDATE jr_work_queue
SET status = 'pending',
    error_message = NULL,
    result = NULL,
    started_at = NULL,
    completed_at = NULL,
    progress_percent = 0,
    status_message = 'Re-queued by cascade fixer after root blockers resolved'
WHERE id BETWEEN 531 AND 535
AND status = 'failed';
```

## Step 3: Validate migration and re-queue

```bash
python3 -c "import py_compile; py_compile.compile('/ganuda/services/research_worker.py', doraise=True); print('research_worker.py: CLEAN')"
```

```bash
PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -U claude -d zammad_production -c "SELECT COUNT(*) AS total, COUNT(content_checksum) AS with_checksum, COUNT(*) FILTER (WHERE domain_tag = 'anchor') AS anchors FROM thermal_memory_archive;"
```

```bash
PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -U claude -d zammad_production -c "SELECT id, title, status FROM jr_work_queue WHERE id BETWEEN 531 AND 535;"
```
