# Jr Instruction: Validate Strange Attractors in Federation Data

## Context
March 9 session discovered potential strange attractors in federation data. Before we build dashboards or make architectural decisions on these patterns, Coyote demands null hypothesis testing. Are these intrinsic emergent patterns or artifacts of our scoring functions? Decomposed in Longhouse 3c06ea3bbd4b6a24.

## Task
Write `/ganuda/scripts/validate_strange_attractors.py` that reproduces and tests each finding.

### Finding 1: Temperature Phase Boundary at 60-70
Only 262 of 91,893 memories (0.3%) have temperature between 60-70. This looks like a phase boundary, but could be an artifact of temperature assignment logic.

**Test**: Query temperature distribution in 5-degree bins. Also inspect the code that assigns temperature scores -- if there is a threshold or branch at 60 or 70, the "gap" is just a code artifact, not an emergent boundary.

```sql
SELECT
    width_bucket(temperature_score, 0, 100, 20) as bucket,
    COUNT(*) as count,
    MIN(temperature_score) as min_temp,
    MAX(temperature_score) as max_temp
FROM thermal_memory_archive
GROUP BY bucket
ORDER BY bucket;
```

Also search for temperature assignment logic in:
- `/ganuda/lib/specialist_council.py` (safe_thermal_write calls)
- `/ganuda/scripts/council_dawn_mist.py`
- Any function that sets temperature_score

If the code has `if important: temp=70 else: temp=50` style logic, the gap is artificial.

### Finding 2: Vote Confidence at 0.9 (1,618 votes, phi ratio)
1,618 votes at 0.9 confidence. 1,618 is the first 4 digits of the golden ratio (phi = 1.618...).

**Test**: This is almost certainly coincidence. Check total vote count and the distribution:

```sql
SELECT
    ROUND(confidence::numeric, 1) as conf_bucket,
    COUNT(*) as count
FROM council_votes
GROUP BY ROUND(confidence::numeric, 1)
ORDER BY conf_bucket;
```

If 0.9 is a common default or threshold in the voting code, the cluster is artificial. Check specialist_council.py for hardcoded 0.9 values.

### Finding 3: Circadian Rhythm (bimodal 10AM/10PM, peak 4PM)
Bimodal peaks at 10AM and 10PM, highest temperature at 4PM.

**Test**: This likely reflects Chief's work patterns, not an emergent property of the system.

```sql
SELECT
    EXTRACT(HOUR FROM created_at AT TIME ZONE 'America/Chicago') as hour_ct,
    COUNT(*) as memory_count,
    AVG(temperature_score) as avg_temp
FROM thermal_memory_archive
GROUP BY hour_ct
ORDER BY hour_ct;
```

If peaks correlate with Chief's known schedule (bipolar productive cycles, typically AM burst and PM burst), this is a human input pattern, not system emergence.

### Output Format
The script should print a clear verdict for each finding:

```
FINDING 1: Temperature Phase Boundary
  Distribution: [histogram]
  Code artifacts found: [yes/no, with evidence]
  VERDICT: INTRINSIC / ARTIFACT / INCONCLUSIVE

FINDING 2: Phi Ratio at 0.9
  Distribution: [histogram]
  Hardcoded thresholds found: [yes/no]
  VERDICT: INTRINSIC / ARTIFACT / COINCIDENCE

FINDING 3: Circadian Rhythm
  Hourly distribution: [table]
  Correlates with known human patterns: [yes/no]
  VERDICT: INTRINSIC / HUMAN-DRIVEN / INCONCLUSIVE
```

## Acceptance Criteria
- Script runs end-to-end and produces verdicts for all 3 findings
- Each finding has null hypothesis clearly stated and tested
- Code artifact analysis included (not just data analysis)
- Verdicts are honest -- if it is an artifact, say so. We seek truth.
- Results written to thermal memory with temperature 75 (research finding, not sacred)
- Summary suitable for dawn mist report

## Dependencies
- Database access (bluefin PostgreSQL, zammad_production)
- Kanban #2057, Jr task #1189.
