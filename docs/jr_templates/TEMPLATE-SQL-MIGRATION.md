# Jr Instruction: [TITLE]

**Ticket**: [TICKET-ID]
**Estimated SP**: [number]
**Target DB**: [bluefin/zammad_production or specific database]

---

## Objective

[What this migration accomplishes]

## Pre-Flight

```sql
-- Verify current state before migration
[SELECT query showing current state]
```

## Migration

### Step 1: [Create/Alter/Insert]

```sql
[SQL statement]
```

### Step 2: [repeat]

## Verification

```sql
-- Verify migration succeeded
[SELECT query showing new state]
```

## Rollback

```sql
-- Undo migration if needed
[DROP/ALTER/DELETE statements]
```

## What NOT To Do

- Do NOT run on production without pre-flight check
- Do NOT drop columns without backing up data first
