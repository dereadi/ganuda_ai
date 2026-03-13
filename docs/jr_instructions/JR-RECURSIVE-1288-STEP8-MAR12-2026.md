# [RECURSIVE] DC-16 Phase 1: Database Reflex Layer — Drop Indexes, Tune Autovacuum, Retention Policies, Fix Fire Guard - Step 8

**Parent Task**: #1288
**Auto-decomposed**: 2026-03-12T17:58:55.936355
**Original Step Title**: Retention purge for fedattn tables

---

### Step 8: Retention purge for fedattn tables

222K rows each, 34 MB and 28 MB. Keep 30 days.

```sql
DELETE FROM fedattn_contributions WHERE created_at < NOW() - INTERVAL '30 days';
DELETE FROM fedattn_sessions WHERE created_at < NOW() - INTERVAL '30 days';
```
