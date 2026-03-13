# [RECURSIVE] DC-16 Phase 1: Database Reflex Layer — Drop Indexes, Tune Autovacuum, Retention Policies, Fix Fire Guard - Step 5

**Parent Task**: #1288
**Auto-decomposed**: 2026-03-12T17:58:55.928402
**Original Step Title**: Retention purge for health_check_log

---

### Step 5: Retention purge for health_check_log

404K rows, zero index usage, 38 MB. Keep 7 days.

```sql
DELETE FROM health_check_log WHERE created_at < NOW() - INTERVAL '7 days';
```
