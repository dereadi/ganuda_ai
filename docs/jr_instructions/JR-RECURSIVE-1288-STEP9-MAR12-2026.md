# [RECURSIVE] DC-16 Phase 1: Database Reflex Layer — Drop Indexes, Tune Autovacuum, Retention Policies, Fix Fire Guard - Step 9

**Parent Task**: #1288
**Auto-decomposed**: 2026-03-12T17:58:55.936888
**Original Step Title**: Verify fedattn retention

---

### Step 9: Verify fedattn retention

```sql
SELECT 'fedattn_sessions' AS tbl, COUNT(*) FROM fedattn_sessions
UNION ALL
SELECT 'fedattn_contributions', COUNT(*) FROM fedattn_contributions;
```
