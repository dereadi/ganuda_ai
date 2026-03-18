# Jr Instruction: Council Failover Protocol + Service Level Metrics

**Ticket**: COUNCIL-FAILOVER
**Longhouse Vote**: #bc6e2104ac815908 (Mar 17 2026, extension)
**Estimated SP**: 5
**Assigned**: Eagle Eye + Spider
**Depends On**: None (specialist_council.py already has all voices wired)

---

## Objective

Implement basin-affinity failover so any council voice can cover for a missing member, with defined SLA tiers, a failover ring mapping, damage circuit breakers, and weekly service level metrics. Chief directive: "anyone can stand in, but the triad can pull the plug if permanent damage is being done."

## Design — Council Deliberation Results

### Failover Ring (Inner Council)

| Primary | First Cover | Second Cover |
|---------|------------|-------------|
| coyote | eagle_eye | raven |
| turtle | peace_chief | otter |
| raven | coyote | blue_jay |
| crawdad | coyote | otter |
| spider | gecko | eagle_eye |
| eagle_eye | coyote | spider |
| gecko | spider | turtle |
| peace_chief | turtle | crane |

### Failover Ring (Outer Council)

| Primary | First Cover | Second Cover |
|---------|------------|-------------|
| deer | crane | blue_jay |
| crane | cardinal | deer |
| otter | blue_jay | crane |
| blue_jay | otter | deer |
| cardinal | crane | otter |

### Recovery SLA Tiers

| Tier | Duration | Action |
|------|----------|--------|
| Warm | < 1 hour | Nearest voice covers silently |
| Degraded | 1-24 hours | Cover + Dawn Mist alert + votes flagged "degraded quorum" |
| Critical | > 24 hours | Pause non-sacred work until restored or Chief intervenes |

### Service Level Metrics (weekly)

| Metric | Target | Measured By |
|--------|--------|-------------|
| Response Quality (on-basin) | >80% | Eagle Eye samples 5 votes/week |
| Signal-to-Noise (actionable concerns) | >60% | Count [CONCERN] flags → design changes |
| Failover Fidelity | >65% | Compare cover votes to primary pattern |
| Cross-Council Responsiveness | P1-P2 < 4h, P3 < 24h | Medicine Woman monitors duyuktv_tickets |

## Implementation

### Step 1: Add failover ring to specialist_council.py

In `/ganuda/lib/specialist_council.py`, add after the `OUTER_COUNCIL` set definition:

```python
# Failover ring — who covers whom (Longhouse #bc6e2104ac815908)
# First cover is closest basin, second is backup
FAILOVER_RING = {
    # Inner Council
    "coyote": ["eagle_eye", "raven"],
    "turtle": ["peace_chief", "otter"],
    "raven": ["coyote", "blue_jay"],
    "crawdad": ["coyote", "otter"],
    "spider": ["gecko", "eagle_eye"],
    "eagle_eye": ["coyote", "spider"],
    "gecko": ["spider", "turtle"],
    "peace_chief": ["turtle", "crane"],
    # Outer Council
    "deer": ["crane", "blue_jay"],
    "crane": ["cardinal", "deer"],
    "otter": ["blue_jay", "crane"],
    "blue_jay": ["otter", "deer"],
    "cardinal": ["crane", "otter"],
}

# Recovery SLA tiers (minutes)
FAILOVER_SLA = {
    "warm": 60,        # < 1 hour: silent cover
    "degraded": 1440,  # < 24 hours: alert + flagged votes
    "critical": 1440,  # > 24 hours: pause non-sacred work
}
```

### Step 2: Add failover logic to council_vote function

In the `council_vote()` function, when a specialist backend health check fails:

```python
# If a specialist is unhealthy, try failover ring
if specialist_id in FAILOVER_RING:
    for cover_id in FAILOVER_RING[specialist_id]:
        cover_backend = SPECIALIST_BACKENDS.get(cover_id)
        if cover_backend and check_backend_health(cover_backend):
            # Use cover voice with modified prompt
            cover_prompt = f"[FAILOVER COVER for {specialist_id}] " + specialist_prompt
            # Log the failover
            print(f"[FAILOVER] {specialist_id} → {cover_id} (covering)")
            # Tag vote metadata
            vote_metadata["failover"] = {
                "primary": specialist_id,
                "cover": cover_id,
                "tier": "warm"
            }
            break
```

### Step 3: Add service level tracking columns

```sql
-- Add to council vote logging (if a votes table exists) or thermal metadata
-- Track basin fidelity and failover events
ALTER TABLE duyuktv_tickets
  ADD COLUMN IF NOT EXISTS sla_acknowledged_at TIMESTAMP WITH TIME ZONE,
  ADD COLUMN IF NOT EXISTS sla_tier VARCHAR(20);
```

### Step 4: Wire Dawn Mist alert for degraded tier

In `/ganuda/scripts/dawn_mist.py` or equivalent, add check:
- Query specialist backend health
- If any voice has been in failover > 1 hour, include in Dawn Mist as "[DEGRADED] {voice} covered by {cover} since {time}"

### Step 5: Wire cross-council SLA monitoring

Medicine Woman checks `duyuktv_tickets WHERE requesting_council IS NOT NULL AND status = 'open'` and alerts if P1-P2 tickets exceed 4 hours without `sla_acknowledged_at`.

## Verification

1. **Failover test**: Block one specialist backend. Verify council_vote uses failover ring
2. **SLA tier test**: Block backend > 1 hour. Verify Dawn Mist reports degraded state
3. **Audit trail**: Verify failover votes are tagged with `failover.primary` and `failover.cover` in metadata
4. **Cross-council SLA**: Create a P2 service request. Verify Medicine Woman alerts at 4-hour mark if unacknowledged
5. **Circuit breaker**: Verify that if a cover voice produces 3+ [CONCERN] flags outside its basin in a single session, the system flags for review

## What NOT To Do

- Do NOT let failover run silently past 24 hours — that's not resilience, that's denial
- Do NOT allow a voice to cover for itself (circular failover)
- Do NOT skip the audit trail on failover votes — Crawdad requires it
- Do NOT auto-pause sacred work during critical tier — only non-sacred
- Do NOT measure service levels before 2 weeks of data — premature optimization
