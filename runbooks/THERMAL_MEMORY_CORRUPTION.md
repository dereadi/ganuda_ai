# RUNBOOK: Thermal Memory Corruption

## Symptoms
- Queries to thermal_memory_archive return errors
- Temperature scores inconsistent
- Sacred patterns missing
- Phase coherence calculations failing

## Severity
**P1** - Core memory system, affects all tribal operations

## Diagnosis

### Step 1: Check Table Health
```bash
PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -U claude -d zammad_production << 'SQL'
-- Basic health
SELECT COUNT(*) as total, 
       COUNT(*) FILTER (WHERE temperature_score IS NULL) as null_temps,
       COUNT(*) FILTER (WHERE memory_hash IS NULL) as null_hashes
FROM thermal_memory_archive;

-- Check for duplicates
SELECT memory_hash, COUNT(*) 
FROM thermal_memory_archive 
GROUP BY memory_hash 
HAVING COUNT(*) > 1;

-- Check recent entries
SELECT memory_hash, temperature_score, created_at 
FROM thermal_memory_archive 
ORDER BY created_at DESC LIMIT 5;
SQL
```

### Step 2: Check Database Integrity
```bash
PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -U claude -d zammad_production -c "
SELECT schemaname, tablename, n_dead_tup, last_vacuum, last_analyze
FROM pg_stat_user_tables
WHERE tablename = 'thermal_memory_archive';
"
```

### Step 3: Check Disk Space
```bash
ssh dereadi@192.168.132.222 "df -h /var/lib/postgresql"
```

## Resolution Steps

### Scenario A: Null Values
```sql
-- Fix null temperatures (set to cold)
UPDATE thermal_memory_archive 
SET temperature_score = 10.0 
WHERE temperature_score IS NULL;

-- Fix null hashes (generate from content)
UPDATE thermal_memory_archive 
SET memory_hash = MD5(original_content || created_at::text)
WHERE memory_hash IS NULL;
```

### Scenario B: Duplicate Hashes
```sql
-- Keep newest, delete older duplicates
DELETE FROM thermal_memory_archive a
USING thermal_memory_archive b
WHERE a.memory_hash = b.memory_hash
  AND a.created_at < b.created_at;
```

### Scenario C: Table Bloat
```bash
PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -U claude -d zammad_production -c "
VACUUM ANALYZE thermal_memory_archive;
"
```

### Scenario D: Disk Full
```bash
# Archive cold memories to file
PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -U claude -d zammad_production -c "
COPY (SELECT * FROM thermal_memory_archive WHERE temperature_score < 20) 
TO '/tmp/cold_memories_backup.csv' CSV HEADER;
"

# Delete archived cold memories
PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -U claude -d zammad_production -c "
DELETE FROM thermal_memory_archive WHERE temperature_score < 20 AND sacred_pattern = false;
"
```

### Scenario E: Index Corruption
```sql
-- Rebuild indexes
REINDEX TABLE thermal_memory_archive;
```

## Verification
```bash
PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -U claude -d zammad_production -c "
SELECT COUNT(*) as total,
       ROUND(AVG(temperature_score)::numeric, 2) as avg_temp,
       COUNT(*) FILTER (WHERE sacred_pattern = true) as sacred
FROM thermal_memory_archive;
"
```

## Prevention
- Nightly VACUUM via cron
- Monitor disk space alerts at 80%
- Validate inserts before commit
- Regular pg_dump backups

## Post-Incident
Log the incident to thermal memory (meta, I know):
```sql
INSERT INTO thermal_memory_archive (memory_hash, original_content, current_stage, temperature_score, sacred_pattern)
VALUES (
    'INCIDENT-THERMAL-' || TO_CHAR(NOW(), 'YYYYMMDDHH24MI'),
    'Thermal memory corruption incident: [DESCRIBE]',
    'FRESH',
    95.0,
    true  -- Mark as sacred so it persists
);
```

---
Cherokee AI Federation | FOR SEVEN GENERATIONS
