# [RECURSIVE] DC-16 Phase 1: Database Reflex Layer — Drop Indexes, Tune Autovacuum, Retention Policies, Fix Fire Guard - Step 12

**Parent Task**: #1288
**Auto-decomposed**: 2026-03-12T17:58:55.938169
**Original Step Title**: Create partial composite index on jr_work_queue for pending poll

---

### Step 12: Create partial composite index on jr_work_queue for pending poll

The TPM daemon polling pattern filters status='pending' and orders by priority, created_at.

```sql
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_jr_work_queue_status_priority
ON jr_work_queue (status, priority ASC, created_at ASC)
WHERE status = 'pending';
```
