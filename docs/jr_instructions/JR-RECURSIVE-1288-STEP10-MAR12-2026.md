# [RECURSIVE] DC-16 Phase 1: Database Reflex Layer — Drop Indexes, Tune Autovacuum, Retention Policies, Fix Fire Guard - Step 10

**Parent Task**: #1288
**Auto-decomposed**: 2026-03-12T17:58:55.937326
**Original Step Title**: Tag fedattn retention policy

---

### Step 10: Tag fedattn retention policy

```sql
COMMENT ON TABLE fedattn_sessions IS 'Retention: 30 days. DC-16 telemetry tier.';
COMMENT ON TABLE fedattn_contributions IS 'Retention: 30 days. DC-16 telemetry tier.';
```
