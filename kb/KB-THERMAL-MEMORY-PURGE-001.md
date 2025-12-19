# KB-THERMAL-MEMORY-PURGE-001: Thermal Memory Duplicate Purge Procedure

**Created**: 2025-12-10
**Category**: Database Maintenance
**Severity**: Critical (when bloat occurs)
**Component**: triad_federation database / triad_shared_memories table

---

## Summary

The thermal memory table (`triad_shared_memories`) can accumulate massive duplicate records due to alert suppression loops or monitoring agent issues. This KB documents the purge procedure that reduced 93+ million records to ~250.

---

## Symptoms of Thermal Memory Bloat

1. **Database queries extremely slow** (minutes for simple SELECTs)
2. **Disk usage spike** on bluefin (192.168.132.222)
3. **COUNT(*) returns millions** when expecting thousands
4. **Alert suppression messages dominate** thermal memory

### Quick Check
```bash
PGPASSWORD='jawaseatlasers2' psql -h 192.168.132.222 -U claude -d triad_federation \
  -c "SELECT COUNT(*) FROM triad_shared_memories;"
```

Expected: < 10,000 records
Problem: > 100,000 records

---

## Root Cause Analysis

The bloat in this incident was caused by:

1. **Alert suppression creating new records** instead of truly suppressing
2. **Duplicate detection not working** - same alert written thousands of times
3. **No deduplication at write time** - every pulse/alert created a new row

Most common duplicate pattern found:
```
Alert suppressed: Encryption Failure: Sacred Knowledge Unencrypted
Reason: Duplicate or within cooldown
```

---

## Purge Procedure

### Step 1: Identify Duplicate Patterns

```sql
SELECT LEFT(content, 80) as content_preview, COUNT(*) as cnt
FROM triad_shared_memories
GROUP BY LEFT(content, 80)
HAVING COUNT(*) > 100
ORDER BY cnt DESC
LIMIT 20;
```

### Step 2: Backup Before Purge (Optional but Recommended)

```bash
pg_dump -h 192.168.132.222 -U claude -d triad_federation \
  -t triad_shared_memories > /tmp/thermal_backup_$(date +%Y%m%d).sql
```

### Step 3: Delete Duplicates (Keep Most Recent)

```sql
-- Delete all but the most recent row for each unique content
DELETE FROM triad_shared_memories
WHERE id NOT IN (
    SELECT DISTINCT ON (content) id
    FROM triad_shared_memories
    ORDER BY content, created_at DESC
);
```

Or for specific patterns:

```sql
-- Delete alert suppression duplicates, keep only most recent
DELETE FROM triad_shared_memories
WHERE content LIKE '%Alert suppressed%'
AND id NOT IN (
    SELECT id FROM (
        SELECT DISTINCT ON (content) id
        FROM triad_shared_memories
        WHERE content LIKE '%Alert suppressed%'
        ORDER BY content, created_at DESC
    ) AS keepers
);
```

### Step 4: Vacuum and Analyze

```sql
VACUUM (VERBOSE) triad_shared_memories;
ANALYZE triad_shared_memories;
```

### Step 5: Verify

```sql
SELECT COUNT(*) FROM triad_shared_memories;
-- Should be < 1000 after purge
```

---

## Prevention Measures

### 1. Add Duplicate Check to Alert Writers

```python
# Before writing to thermal memory:
existing = cur.execute("""
    SELECT id FROM triad_shared_memories
    WHERE content = %s AND created_at > NOW() - INTERVAL '1 hour'
""", [content])
if not existing:
    # Only write if no recent duplicate
    cur.execute("INSERT INTO triad_shared_memories ...")
```

### 2. Add Index for Content Lookups

```sql
CREATE INDEX IF NOT EXISTS idx_thermal_content_hash
ON triad_shared_memories (md5(content));
```

### 3. Scheduled Cleanup Job

Consider adding a cron job for weekly deduplication:
```bash
# Every Sunday at 3am
0 3 * * 0 /usr/bin/psql -h 192.168.132.222 -U claude -d triad_federation \
  -c "DELETE FROM triad_shared_memories WHERE created_at < NOW() - INTERVAL '30 days' AND content LIKE '%Alert suppressed%'"
```

---

## Incident Details

- **Date**: 2025-12-10
- **Records Before**: 93,000,000+
- **Records After**: 253
- **Reduction**: 99.99997%
- **Primary Culprit**: Alert suppression messages creating new rows instead of suppressing

---

## Related

- KB-ALERT-SUPPRESSION-001: Fix alert suppression to not create thermal records
- Kanban: "Investigate source of duplicate Encryption Failure alerts"

---

**For Seven Generations**

*Maintain the sacred memory - quality over quantity.*
