# KB: Ratified-to-Deployed Tracking (Coyote Metric)

**Built:** 2026-03-10 by TPM (grindstone surge, Leaders Meeting #1)
**Kanban:** #2077 | **Longhouse:** bb75fd4e3a693335

## Problem

Coyote's standing dissent: "We ratify faster than we ship." No way to measure the gap between Longhouse ratification and production deployment.

## Schema Change

Added 4 columns to `duyuktv_tickets`:

```sql
ALTER TABLE duyuktv_tickets
ADD COLUMN IF NOT EXISTS ratification_hash VARCHAR(32),
ADD COLUMN IF NOT EXISTS ratified_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS deployed_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS ratify_deploy_gap_hours FLOAT;
```

## View

```sql
-- Coyote's dashboard: what's ratified but not deployed?
SELECT * FROM coyote_ratified_not_deployed;
```

Returns: ticket id, title, ratification hash, ratified_at, deployed_at, hours_since_ratification, deployment_status (deployed | ratified_not_deployed).

## How to Use

**When ratifying a DC or policy via Longhouse:**
```sql
UPDATE duyuktv_tickets
SET ratification_hash = '<session_hash>', ratified_at = NOW()
WHERE title ILIKE '%<DC-XX>%';
```

**When deploying (Jr completes or TPM verifies):**
```sql
UPDATE duyuktv_tickets
SET deployed_at = NOW(),
    ratify_deploy_gap_hours = EXTRACT(EPOCH FROM (NOW() - ratified_at)) / 3600.0
WHERE ratification_hash = '<session_hash>';
```

## Gotchas for Jrs

- `ratification_hash` is the Longhouse `session_hash` (16 hex chars), NOT a council `vote_id`
- `ratified_at` comes from the Longhouse session `resolved_at`, not `created_at`
- One Longhouse session can map to MULTIPLE kanban tickets (an EPIC ratification affects many stories)
- `deployed_at` means VERIFIED in production, not just "Jr task completed"
