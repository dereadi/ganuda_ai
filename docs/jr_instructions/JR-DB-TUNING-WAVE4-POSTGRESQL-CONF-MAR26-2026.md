# JR INSTRUCTION: DB Tuning Wave 4 — PostgreSQL Configuration

**Task ID**: DB-TUNE-004
**Priority**: P2
**SP**: 2
**Epic**: DB-HEALTH-EPIC

## Context

Bluefin has 128GB RAM, 32 cores, and an SSD-backed `/postgresdb` volume. The current PostgreSQL config is reasonable but conservative. Several parameters can be improved.

**Current vs Recommended:**

| Parameter | Current | Recommended | Why |
|-----------|---------|-------------|-----|
| shared_buffers | 8GB | 16GB | 128GB machine, 12.5% of RAM is still conservative. Rule of thumb: 25% for dedicated DB servers, but bluefin runs other services. |
| effective_cache_size | 96GB | 96GB | Already good. Matches available memory. |
| work_mem | 32MB | 32MB | Already good for complex queries. Don't increase — too many connections × work_mem = OOM risk. |
| maintenance_work_mem | 2GB | 2GB | Already good. VACUUM/CREATE INDEX use this. |
| max_wal_size | 1GB | 2GB | More WAL headroom reduces checkpoint frequency during bulk writes (Jr task batches, thermal writes). |
| autovacuum_max_workers | 3 | 5 | 17 databases, 3 workers is a bottleneck. We have 32 cores. |
| autovacuum_naptime | 60s | 30s | More frequent checks, especially needed for high-write tables. |
| default_statistics_target | 100 | 200 | Better query plans for thermal_memory_archive (95K+ rows with varied distributions). |
| huge_pages | try | try | Already set. Verify HugePages are actually being used (Step 3). |
| wal_buffers | 16MB | 64MB | With shared_buffers at 16GB, wal_buffers should be ~1/256th = 64MB. |
| synchronous_commit | on | on | Keep on. Data integrity > speed. |
| idle_in_transaction_session_timeout | 60s | 60s | Already good. Kills abandoned transactions. |
| statement_timeout | 120s | 120s | Already good. |

## Step 1: Edit postgresql.conf on bluefin

```bash
ssh 10.100.0.2
sudo -u postgres vi /etc/postgresql/17/main/postgresql.conf
```

Changes:
```
shared_buffers = 16GB                  # was 8GB
max_wal_size = 2GB                     # was 1GB
wal_buffers = 64MB                     # was 16MB
autovacuum_max_workers = 5             # was 3
autovacuum_naptime = 30                # was 60s
default_statistics_target = 200        # was 100
```

## Step 2: Apply Changes (requires restart for shared_buffers)

```bash
# Check which changes need restart vs reload
sudo -u postgres psql -c "SELECT name, pending_restart FROM pg_settings WHERE name IN ('shared_buffers', 'max_wal_size', 'wal_buffers', 'autovacuum_max_workers', 'autovacuum_naptime', 'default_statistics_target');"

# shared_buffers and wal_buffers require restart. The rest are reload-only.
# Schedule restart during low-traffic window (e.g., Sunday 3 AM)

# For reload-only params (can do immediately):
sudo -u postgres psql -c "ALTER SYSTEM SET autovacuum_max_workers = 5;"
sudo -u postgres psql -c "ALTER SYSTEM SET autovacuum_naptime = '30s';"
sudo -u postgres psql -c "ALTER SYSTEM SET default_statistics_target = 200;"
sudo -u postgres psql -c "ALTER SYSTEM SET max_wal_size = '2GB';"
sudo systemctl reload postgresql
```

For restart-requiring params (shared_buffers, wal_buffers):
```bash
# Schedule for Sunday maintenance window
sudo systemctl restart postgresql
```

## Step 3: Verify HugePages (optional, advanced)

```bash
# Check if PostgreSQL is using HugePages
grep -i huge /proc/meminfo
cat /proc/$(pgrep -f 'postgres.*writer')/status | grep -i huge

# If HugePages_Total is 0, they're not configured at OS level
# To enable (16GB shared_buffers needs ~8192 2MB pages):
echo "vm.nr_hugepages = 8192" | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
# Then restart PostgreSQL
```

**NOTE**: HugePages improve TLB performance for large shared_buffers. Optional but recommended for 16GB+.

## Step 4: Post-Change ANALYZE

After restart with new settings, regenerate statistics:

```sql
-- With default_statistics_target = 200, ANALYZE collects more samples
ANALYZE thermal_memory_archive;
ANALYZE council_votes;
ANALYZE api_audit_log;
ANALYZE fedattn_sessions;
```

## Verification

```bash
# Confirm new settings are active
sudo -u postgres psql -c "SHOW shared_buffers; SHOW max_wal_size; SHOW autovacuum_max_workers; SHOW autovacuum_naptime; SHOW default_statistics_target;"

# Monitor cache hit ratio (should stay above 99%)
sudo -u postgres psql -c "
SELECT datname,
       ROUND(100.0 * blks_hit / NULLIF(blks_hit + blks_read, 0), 2) as cache_hit_pct
FROM pg_stat_database
WHERE datname NOT LIKE 'template%'
ORDER BY cache_hit_pct;"
```

## Constraints

- Do NOT change `max_connections` without checking all connection-pooling consumers
- Do NOT lower `statement_timeout` — 120s is needed for council deep-path votes
- Do NOT set `synchronous_commit = off` — data integrity is non-negotiable
- shared_buffers change requires a PostgreSQL restart — schedule it, don't surprise the organism
- Test in a non-peak window. If anything degrades, revert to previous values.

## Risk Assessment

Low risk. These are standard tuning adjustments for a 128GB machine. The biggest change (shared_buffers 8→16GB) is still only 12.5% of RAM. The autovacuum changes are immediately beneficial with zero downside.
