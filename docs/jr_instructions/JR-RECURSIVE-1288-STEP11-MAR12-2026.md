# [RECURSIVE] DC-16 Phase 1: Database Reflex Layer — Drop Indexes, Tune Autovacuum, Retention Policies, Fix Fire Guard - Step 11

**Parent Task**: #1288
**Auto-decomposed**: 2026-03-12T17:58:55.937828
**Original Step Title**: Create composite index on jr_work_queue for status+created_at queries

---

### Step 11: Create composite index on jr_work_queue for status+created_at queries

28,834 seq scans on this table. Most queries filter by status and order by created_at.

```sql
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_jr_work_queue_status_created
ON jr_work_queue (status, created_at DESC);
```
