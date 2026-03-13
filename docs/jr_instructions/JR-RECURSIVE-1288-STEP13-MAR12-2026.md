# [RECURSIVE] DC-16 Phase 1: Database Reflex Layer — Drop Indexes, Tune Autovacuum, Retention Policies, Fix Fire Guard - Step 13

**Parent Task**: #1288
**Auto-decomposed**: 2026-03-12T17:58:55.938501
**Original Step Title**: Verify jr_work_queue indexes

---

### Step 13: Verify jr_work_queue indexes

```sql
SELECT indexrelname, idx_scan
FROM pg_stat_user_indexes
WHERE relname = 'jr_work_queue';
```
