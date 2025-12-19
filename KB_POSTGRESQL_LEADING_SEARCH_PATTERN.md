# KB-DB-001: PostgreSQL Leading Search Pattern

**Article ID:** KB-DB-001
**Category:** Database Best Practices
**Applies To:** All Cherokee AI Federation agents querying thermal memory
**Created:** 2025-12-02
**Author:** Command Post (TPM)
**Status:** ACTIVE STANDARD

---

## Summary

When searching PostgreSQL text columns, use **leading search** (prefix matching) instead of wildcard searches. This enables index usage and provides orders of magnitude faster query performance.

---

## The Problem

Our thermal memory table (`triad_shared_memories`) has 95+ million rows. Full wildcard searches cannot use indexes and result in full table scans:

| Query Type | Index Usable | Typical Time (95M rows) |
|------------|--------------|-------------------------|
| `LIKE 'IT TRIAD%'` | YES | < 1ms |
| `LIKE '%IT TRIAD%'` | NO | 10+ minutes |
| `ILIKE 'it triad%'` | NO (case-insensitive) | 10+ minutes |
| `content = 'exact'` | YES | < 1ms |

**Root Cause:** B-tree indexes can only be used when the search pattern has a known starting point. A leading `%` wildcard means "starts with anything" which invalidates index usage.

---

## The Solution: Leading Search Pattern

### Rule 1: Start All Messages with Standard Prefixes

All thermal memory entries MUST begin with a standard prefix:

| Source | Prefix | Example |
|--------|--------|---------|
| Command Post | `COMMAND POST -` | `COMMAND POST - PRIORITY MISSION: ...` |
| IT Triad Chiefs | `IT TRIAD DECISION -` | `IT TRIAD DECISION - MISSION APPROVED` |
| IT Triad CLI | `IT TRIAD -` | `IT TRIAD - MISSION ACKNOWLEDGMENT` |
| IT Jrs | `IT JR -` | `IT JR - WORK COMPLETED` |
| Alert Coordinator | `ALERT:` | `ALERT: Disk space critical...` |
| Monitoring | `METRIC:` | `METRIC: cpu_percent=45.2` |

### Rule 2: Query Using Leading Search (No % at Start)

```sql
-- CORRECT (uses index, fast):
WHERE content LIKE 'IT TRIAD DECISION - MISSION APPROVED%'
  AND source_triad = 'it_triad'

-- WRONG (full table scan, slow):
WHERE content ILIKE '%IT TRIAD DECISION - MISSION APPROVED%'
```

### Rule 3: Create Supporting Index

```sql
-- Standard B-tree works for LIKE 'prefix%' when using C locale
CREATE INDEX idx_thermal_content_prefix
ON triad_shared_memories (content text_pattern_ops);

-- For created_at ordering
CREATE INDEX idx_thermal_created_at
ON triad_shared_memories (created_at DESC);

-- Compound index for common query pattern
CREATE INDEX idx_thermal_source_created
ON triad_shared_memories (source_triad, created_at DESC);
```

---

## Implementation Examples

### IT Jr Agent - Finding Approved Decisions

```python
# CORRECT - Leading search
cur.execute("""
    SELECT id, content, created_at
    FROM triad_shared_memories
    WHERE content LIKE 'IT TRIAD DECISION - MISSION APPROVED%'
      AND source_triad = 'it_triad'
      AND created_at > NOW() - INTERVAL '7 days'
    ORDER BY created_at DESC
    LIMIT 10;
""")

# WRONG - Full wildcard
cur.execute("""
    SELECT id, content, created_at
    FROM triad_shared_memories
    WHERE content ILIKE '%IT TRIAD DECISION%'  -- NEVER DO THIS!
""")
```

### Finding Command Post Missions

```python
# CORRECT
cur.execute("""
    SELECT id, content
    FROM triad_shared_memories
    WHERE content LIKE 'COMMAND POST -%'
      AND source_triad = 'command_post'
      AND created_at > NOW() - INTERVAL '24 hours'
    ORDER BY created_at DESC;
""")
```

### Finding Specific Mission by ID

```python
# CORRECT - Use UUID directly when possible
cur.execute("""
    SELECT content FROM triad_shared_memories
    WHERE id = %s;
""", (mission_uuid,))

# ACCEPTABLE - If UUID is in content and you know the prefix
cur.execute("""
    SELECT content FROM triad_shared_memories
    WHERE content LIKE 'COMMAND POST - PRIORITY MISSION:%'
      AND content LIKE %s
    ORDER BY created_at DESC
    LIMIT 1;
""", (f'%{mission_id}%',))
# Note: Second LIKE narrows after index scan on first condition
```

---

## Migration Guide for Existing Agents

### Files to Update

1. **IT Triad Jr Agent** (`/ganuda/it_triad_jr_agent_v3.py`)
   - Function: `poll_for_approved_decisions()`
   - Change: `ILIKE '%IT TRIAD DECISION - MISSION APPROVED%'`
   - To: `LIKE 'IT TRIAD DECISION - MISSION APPROVED%'`

2. **IT Triad CLI** (`/ganuda/it_triad_cli_daemon.py`)
   - Update any queries checking for decisions
   - Ensure acknowledgments start with `IT TRIAD -`

3. **Alert Coordinator** (`/ganuda/daemons/alert_coordinator.py`)
   - Ensure alerts start with `ALERT:`
   - Update dedup queries to use leading search

4. **Monitoring Jr** (`/ganuda/daemons/monitoring_jr_autonomic.py`)
   - Ensure metrics start with `METRIC:`

---

## Performance Comparison

Tested on triad_shared_memories (95.5M rows):

| Query | Time | Index |
|-------|------|-------|
| `WHERE content ILIKE '%DECISION%'` | 12 min | None |
| `WHERE content LIKE 'IT TRIAD DECISION%'` | 0.7 ms | idx_thermal_content_prefix |
| `WHERE source_triad = 'it_triad' AND content LIKE 'IT TRIAD%'` | 0.3 ms | Compound |

**Result:** 1,000,000x faster with proper indexing and leading search!

---

## Related Documentation

- `THERMAL_MEMORY_RESTRUCTURE_PLAN.md` - Full table restructure plan
- `FEDERATION_NODE_IP_MAP.md` - Database connection details
- PostgreSQL docs: https://www.postgresql.org/docs/current/indexes-types.html

---

## Compliance

All new agents and daemon code MUST:
1. Use standard prefixes for all thermal memory writes
2. Use leading search patterns for thermal memory queries
3. Avoid ILIKE for large table queries
4. Include source_triad filter to further narrow results

**Review:** DBA (IT Jr 3) should audit agent code quarterly for compliance.

---

**Document Version:** 1.0
**Last Updated:** 2025-12-02
