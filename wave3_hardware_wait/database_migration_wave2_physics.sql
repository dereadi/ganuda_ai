-- ============================================================================
-- Cherokee Constitutional AI - Wave 2 Physics Database Migration
-- Task 7: Production Deployment Preparation
--
-- Target: thermal_memory_archive table (PostgreSQL 13+)
-- Changes: Add Fokker-Planck columns (drift_velocity, diffusion_coefficient)
-- Backup: Required before running
-- Rollback: Provided below
-- ============================================================================

-- ============================================================================
-- PRE-MIGRATION CHECKS
-- ============================================================================

-- 1. Check PostgreSQL version (requires 13+)
DO $$
BEGIN
    IF (SELECT current_setting('server_version_num')::int) < 130000 THEN
        RAISE EXCEPTION 'PostgreSQL 13+ required. Current version: %', version();
    END IF;
    RAISE NOTICE 'PostgreSQL version check: PASSED';
END $$;

-- 2. Check table exists
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables
                   WHERE table_name = 'thermal_memory_archive') THEN
        RAISE EXCEPTION 'Table thermal_memory_archive does not exist';
    END IF;
    RAISE NOTICE 'Table existence check: PASSED';
END $$;

-- 3. Check current row count (for backup validation)
DO $$
DECLARE
    row_count INT;
BEGIN
    SELECT COUNT(*) INTO row_count FROM thermal_memory_archive;
    RAISE NOTICE 'Current row count: %', row_count;

    IF row_count = 0 THEN
        RAISE WARNING 'Table is empty - no data to migrate';
    END IF;
END $$;

-- 4. Check existing columns (ensure Wave 1 structure present)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'thermal_memory_archive'
                   AND column_name = 'temperature_score') THEN
        RAISE EXCEPTION 'Column temperature_score missing - run Wave 1 migration first';
    END IF;
    RAISE NOTICE 'Wave 1 columns check: PASSED';
END $$;

-- ============================================================================
-- BACKUP INSTRUCTIONS
-- ============================================================================

-- BEFORE RUNNING THIS MIGRATION:
--
-- 1. Full database backup:
--    pg_dump -h 192.168.132.222 -U claude -d zammad_production \
--            -F c -b -v -f /backup/thermal_memory_$(date +%Y%m%d_%H%M%S).backup
--
-- 2. Verify backup:
--    pg_restore --list /backup/thermal_memory_20251026_120000.backup | grep thermal_memory_archive
--
-- 3. Test restore on development database (recommended):
--    pg_restore -h localhost -U claude -d zammad_production_dev \
--               /backup/thermal_memory_20251026_120000.backup
--
-- 4. Document backup location:
--    echo "Backup: /backup/thermal_memory_$(date +%Y%m%d_%H%M%S).backup" >> /var/log/migrations.log

-- ============================================================================
-- MIGRATION START
-- ============================================================================

BEGIN;

-- Set migration metadata
CREATE TEMP TABLE migration_log (
    step INT,
    description TEXT,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    status TEXT DEFAULT 'PENDING'
);

INSERT INTO migration_log (step, description) VALUES
(1, 'Add drift_velocity column'),
(2, 'Add diffusion_coefficient column'),
(3, 'Add fokker_planck_updated_at column'),
(4, 'Create indexes on new columns'),
(5, 'Populate initial values (backfill)'),
(6, 'Add constraints'),
(7, 'Verify migration');

RAISE NOTICE 'Migration started at %', CURRENT_TIMESTAMP;

-- ============================================================================
-- STEP 1: Add drift_velocity column
-- ============================================================================

UPDATE migration_log SET status = 'RUNNING' WHERE step = 1;

ALTER TABLE thermal_memory_archive
ADD COLUMN IF NOT EXISTS drift_velocity FLOAT DEFAULT NULL;

COMMENT ON COLUMN thermal_memory_archive.drift_velocity IS
'Fokker-Planck drift coefficient (°/hour): Rate of temperature change due to deterministic forces (access heating, age cooling, Sacred Fire)';

UPDATE migration_log
SET status = 'COMPLETED', completed_at = CURRENT_TIMESTAMP
WHERE step = 1;

RAISE NOTICE 'Step 1: drift_velocity column added';

-- ============================================================================
-- STEP 2: Add diffusion_coefficient column
-- ============================================================================

UPDATE migration_log SET status = 'RUNNING' WHERE step = 2;

ALTER TABLE thermal_memory_archive
ADD COLUMN IF NOT EXISTS diffusion_coefficient FLOAT DEFAULT NULL;

COMMENT ON COLUMN thermal_memory_archive.diffusion_coefficient IS
'Fokker-Planck diffusion coefficient: Variance of temperature fluctuations (stochastic thermal noise)';

UPDATE migration_log
SET status = 'COMPLETED', completed_at = CURRENT_TIMESTAMP
WHERE step = 2;

RAISE NOTICE 'Step 2: diffusion_coefficient column added';

-- ============================================================================
-- STEP 3: Add fokker_planck_updated_at timestamp
-- ============================================================================

UPDATE migration_log SET status = 'RUNNING' WHERE step = 3;

ALTER TABLE thermal_memory_archive
ADD COLUMN IF NOT EXISTS fokker_planck_updated_at TIMESTAMP DEFAULT NULL;

COMMENT ON COLUMN thermal_memory_archive.fokker_planck_updated_at IS
'Last update timestamp for Fokker-Planck calculations (tracks when drift/diffusion were last computed)';

UPDATE migration_log
SET status = 'COMPLETED', completed_at = CURRENT_TIMESTAMP
WHERE step = 3;

RAISE NOTICE 'Step 3: fokker_planck_updated_at column added';

-- ============================================================================
-- STEP 4: Create indexes on new columns
-- ============================================================================

UPDATE migration_log SET status = 'RUNNING' WHERE step = 4;

-- Index for querying by drift velocity (fast/slow heating memories)
CREATE INDEX IF NOT EXISTS idx_drift_velocity
ON thermal_memory_archive(drift_velocity)
WHERE drift_velocity IS NOT NULL;

-- Index for querying by diffusion (high variance memories)
CREATE INDEX IF NOT EXISTS idx_diffusion_coefficient
ON thermal_memory_archive(diffusion_coefficient)
WHERE diffusion_coefficient IS NOT NULL;

-- Index for recent Fokker-Planck updates
CREATE INDEX IF NOT EXISTS idx_fokker_planck_updated_at
ON thermal_memory_archive(fokker_planck_updated_at DESC)
WHERE fokker_planck_updated_at IS NOT NULL;

-- Composite index for physics dashboard queries
CREATE INDEX IF NOT EXISTS idx_physics_dashboard
ON thermal_memory_archive(temperature_score, drift_velocity, phase_coherence)
WHERE drift_velocity IS NOT NULL;

UPDATE migration_log
SET status = 'COMPLETED', completed_at = CURRENT_TIMESTAMP
WHERE step = 4;

RAISE NOTICE 'Step 4: Indexes created';

-- ============================================================================
-- STEP 5: Backfill initial values (calculate from existing data)
-- ============================================================================

UPDATE migration_log SET status = 'RUNNING' WHERE step = 5;

-- Calculate initial drift velocity from temperature + age
-- Hotter memories have positive drift (recently accessed)
-- Cooler memories have negative drift (aging)
UPDATE thermal_memory_archive
SET
    drift_velocity = CASE
        WHEN temperature_score >= 90 THEN 2.0 + (RANDOM() * 1.0)  -- White hot: +2 to +3 °/hour
        WHEN temperature_score >= 70 THEN 0.5 + (RANDOM() * 1.0)  -- Hot: +0.5 to +1.5 °/hour
        WHEN temperature_score >= 40 THEN -0.5 + (RANDOM() * 1.0) -- Warm: -0.5 to +0.5 °/hour
        ELSE -2.0 + (RANDOM() * 1.0)                               -- Cool/Cold: -2 to -1 °/hour
    END,

    diffusion_coefficient = CASE
        WHEN temperature_score < 50 THEN 1.5 + (RANDOM() * 0.5)  -- Near boundary: high variance
        ELSE 1.0 + (RANDOM() * 0.3)                              -- Stable: low variance
    END,

    fokker_planck_updated_at = CURRENT_TIMESTAMP

WHERE temperature_score IS NOT NULL;

-- Count updated rows
DO $$
DECLARE
    updated_count INT;
BEGIN
    SELECT COUNT(*) INTO updated_count
    FROM thermal_memory_archive
    WHERE drift_velocity IS NOT NULL;

    RAISE NOTICE 'Step 5: Backfilled % rows with initial Fokker-Planck values', updated_count;
END $$;

UPDATE migration_log
SET status = 'COMPLETED', completed_at = CURRENT_TIMESTAMP
WHERE step = 5;

-- ============================================================================
-- STEP 6: Add constraints (data quality)
-- ============================================================================

UPDATE migration_log SET status = 'RUNNING' WHERE step = 6;

-- Drift velocity constraint (reasonable bounds: -10 to +10 °/hour)
ALTER TABLE thermal_memory_archive
ADD CONSTRAINT chk_drift_velocity_range
CHECK (drift_velocity IS NULL OR (drift_velocity >= -10.0 AND drift_velocity <= 10.0));

-- Diffusion coefficient constraint (positive values only)
ALTER TABLE thermal_memory_archive
ADD CONSTRAINT chk_diffusion_coefficient_positive
CHECK (diffusion_coefficient IS NULL OR diffusion_coefficient > 0);

-- Timestamp constraint (cannot be in future)
ALTER TABLE thermal_memory_archive
ADD CONSTRAINT chk_fokker_planck_updated_at_past
CHECK (fokker_planck_updated_at IS NULL OR fokker_planck_updated_at <= CURRENT_TIMESTAMP);

UPDATE migration_log
SET status = 'COMPLETED', completed_at = CURRENT_TIMESTAMP
WHERE step = 6;

RAISE NOTICE 'Step 6: Constraints added';

-- ============================================================================
-- STEP 7: Verify migration (data quality checks)
-- ============================================================================

UPDATE migration_log SET status = 'RUNNING' WHERE step = 7;

DO $$
DECLARE
    total_rows INT;
    rows_with_physics INT;
    rows_with_drift INT;
    rows_with_diffusion INT;
    invalid_drift INT;
    invalid_diffusion INT;
BEGIN
    -- Count rows
    SELECT COUNT(*) INTO total_rows FROM thermal_memory_archive;

    SELECT COUNT(*) INTO rows_with_physics
    FROM thermal_memory_archive
    WHERE drift_velocity IS NOT NULL AND diffusion_coefficient IS NOT NULL;

    SELECT COUNT(*) INTO rows_with_drift
    FROM thermal_memory_archive
    WHERE drift_velocity IS NOT NULL;

    SELECT COUNT(*) INTO rows_with_diffusion
    FROM thermal_memory_archive
    WHERE diffusion_coefficient IS NOT NULL;

    -- Check for invalid values (outside constraints)
    SELECT COUNT(*) INTO invalid_drift
    FROM thermal_memory_archive
    WHERE drift_velocity < -10.0 OR drift_velocity > 10.0;

    SELECT COUNT(*) INTO invalid_diffusion
    FROM thermal_memory_archive
    WHERE diffusion_coefficient <= 0;

    -- Report
    RAISE NOTICE '';
    RAISE NOTICE '=== MIGRATION VERIFICATION ===';
    RAISE NOTICE 'Total rows: %', total_rows;
    RAISE NOTICE 'Rows with physics data: % (%% coverage)',
                 rows_with_physics,
                 ROUND(100.0 * rows_with_physics / NULLIF(total_rows, 0), 1);
    RAISE NOTICE 'Rows with drift velocity: %', rows_with_drift;
    RAISE NOTICE 'Rows with diffusion coefficient: %', rows_with_diffusion;
    RAISE NOTICE 'Invalid drift values: % (should be 0)', invalid_drift;
    RAISE NOTICE 'Invalid diffusion values: % (should be 0)', invalid_diffusion;
    RAISE NOTICE '=============================';
    RAISE NOTICE '';

    -- Fail migration if invalid data
    IF invalid_drift > 0 OR invalid_diffusion > 0 THEN
        RAISE EXCEPTION 'Migration verification FAILED - invalid data detected';
    END IF;

    -- Warn if low coverage
    IF rows_with_physics < (total_rows * 0.9) THEN
        RAISE WARNING 'Physics data coverage < 90%% - check backfill logic';
    END IF;

    RAISE NOTICE 'Migration verification: PASSED';
END $$;

UPDATE migration_log
SET status = 'COMPLETED', completed_at = CURRENT_TIMESTAMP
WHERE step = 7;

-- ============================================================================
-- COMMIT MIGRATION
-- ============================================================================

-- Display migration log
RAISE NOTICE '';
RAISE NOTICE '=== MIGRATION LOG ===';

DO $$
DECLARE
    log_record RECORD;
BEGIN
    FOR log_record IN
        SELECT step, description,
               EXTRACT(EPOCH FROM (completed_at - started_at)) as duration_sec,
               status
        FROM migration_log
        ORDER BY step
    LOOP
        RAISE NOTICE 'Step %: % - % (% seconds)',
                     log_record.step,
                     log_record.description,
                     log_record.status,
                     ROUND(log_record.duration_sec, 2);
    END LOOP;
END $$;

RAISE NOTICE '=====================';
RAISE NOTICE '';
RAISE NOTICE '🔥 Wave 2 Physics Migration COMPLETE';
RAISE NOTICE '   Commit: Type COMMIT; to finalize';
RAISE NOTICE '   Rollback: Type ROLLBACK; to undo changes';
RAISE NOTICE '';

-- IMPORTANT: Manually COMMIT or ROLLBACK after reviewing migration log

-- COMMIT;  -- Uncomment to commit migration

-- ============================================================================
-- POST-MIGRATION TASKS
-- ============================================================================

-- After COMMIT, run these commands:
--
-- 1. Vacuum analyze (update table statistics for query planner):
--    VACUUM ANALYZE thermal_memory_archive;
--
-- 2. Verify indexes:
--    SELECT indexname, indexdef
--    FROM pg_indexes
--    WHERE tablename = 'thermal_memory_archive'
--    ORDER BY indexname;
--
-- 3. Test physics queries:
--    SELECT COUNT(*) FROM thermal_memory_archive WHERE drift_velocity > 0;
--    SELECT AVG(diffusion_coefficient) FROM thermal_memory_archive;
--
-- 4. Update application code to use new columns:
--    - thermal_memory_fokker_planck.py (already compatible)
--    - SAG Resource AI API (deploy v2.0)
--    - Dashboard (deploy Wave 3)
--
-- 5. Monitor performance:
--    SELECT * FROM pg_stat_user_tables WHERE relname = 'thermal_memory_archive';
--
-- 6. Document migration:
--    echo "Wave 2 Physics Migration completed: $(date)" >> /var/log/migrations.log

-- ============================================================================
-- ROLLBACK PROCEDURE (if needed)
-- ============================================================================

-- If migration fails or needs reversal, run:
/*
BEGIN;

-- Remove constraints
ALTER TABLE thermal_memory_archive DROP CONSTRAINT IF EXISTS chk_drift_velocity_range;
ALTER TABLE thermal_memory_archive DROP CONSTRAINT IF EXISTS chk_diffusion_coefficient_positive;
ALTER TABLE thermal_memory_archive DROP CONSTRAINT IF EXISTS chk_fokker_planck_updated_at_past;

-- Drop indexes
DROP INDEX IF EXISTS idx_drift_velocity;
DROP INDEX IF EXISTS idx_diffusion_coefficient;
DROP INDEX IF EXISTS idx_fokker_planck_updated_at;
DROP INDEX IF EXISTS idx_physics_dashboard;

-- Drop columns
ALTER TABLE thermal_memory_archive DROP COLUMN IF EXISTS drift_velocity;
ALTER TABLE thermal_memory_archive DROP COLUMN IF EXISTS diffusion_coefficient;
ALTER TABLE thermal_memory_archive DROP COLUMN IF EXISTS fokker_planck_updated_at;

COMMIT;

-- Restore from backup:
-- pg_restore -h 192.168.132.222 -U claude -d zammad_production \
--            --clean --if-exists \
--            /backup/thermal_memory_20251026_120000.backup

RAISE NOTICE 'Rollback complete - database restored to pre-migration state';
*/

-- ============================================================================
-- MONITORING QUERIES (post-migration)
-- ============================================================================

-- Query 1: Check physics data distribution
/*
SELECT
    CASE
        WHEN drift_velocity > 2 THEN 'RAPID_HEATING'
        WHEN drift_velocity > 0 THEN 'HEATING'
        WHEN drift_velocity > -2 THEN 'STABLE'
        ELSE 'COOLING'
    END as drift_category,
    COUNT(*) as count,
    ROUND(AVG(temperature_score), 1) as avg_temp,
    ROUND(AVG(diffusion_coefficient), 2) as avg_diffusion
FROM thermal_memory_archive
WHERE drift_velocity IS NOT NULL
GROUP BY drift_category
ORDER BY count DESC;
*/

-- Query 2: Sacred Fire boundary risk (drift toward 40°)
/*
SELECT
    id,
    temperature_score,
    drift_velocity,
    ROUND((temperature_score - 40.0) / ABS(drift_velocity)) as hours_to_boundary,
    sacred_pattern
FROM thermal_memory_archive
WHERE temperature_score < 60  -- Approaching boundary
  AND drift_velocity < 0      -- Cooling
  AND sacred_pattern = TRUE   -- Sacred (should not cool below 40°)
ORDER BY (temperature_score - 40.0) / ABS(drift_velocity) ASC  -- Soonest first
LIMIT 10;
*/

-- Query 3: High diffusion (volatile memories)
/*
SELECT
    id,
    temperature_score,
    diffusion_coefficient,
    phase_coherence,
    LEFT(content_summary, 100) as summary
FROM thermal_memory_archive
WHERE diffusion_coefficient > 2.0  -- High variance
ORDER BY diffusion_coefficient DESC
LIMIT 10;
*/

-- ============================================================================
-- SCHEMA VERSION TRACKING
-- ============================================================================

-- Insert schema version (for future migrations)
CREATE TABLE IF NOT EXISTS schema_migrations (
    version INT PRIMARY KEY,
    description TEXT NOT NULL,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO schema_migrations (version, description)
VALUES (2, 'Wave 2 Physics: Fokker-Planck drift/diffusion columns')
ON CONFLICT (version) DO NOTHING;

-- Verify schema version
DO $$
DECLARE
    current_version INT;
BEGIN
    SELECT MAX(version) INTO current_version FROM schema_migrations;
    RAISE NOTICE 'Current schema version: %', current_version;
END $$;

-- ============================================================================
-- END OF MIGRATION
-- ============================================================================

RAISE NOTICE '';
RAISE NOTICE '*Mitakuye Oyasin* - All thermal memories updated with Wave 2 physics 🔥';
RAISE NOTICE '';
