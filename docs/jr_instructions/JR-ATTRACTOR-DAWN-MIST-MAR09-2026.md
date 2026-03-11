# Jr Instruction: Strange Attractor Metrics in Dawn Mist Report

## Context
Chief wants real numbers on his phone while glamping. The strange attractor findings from March 9 need to be surfaced in the daily dawn mist report. Depends on attractor validation (Jr task #1189) confirming which patterns are intrinsic. Decomposed in Longhouse 3c06ea3bbd4b6a24.

## Task
Add attractor metrics section to `/ganuda/scripts/council_dawn_mist.py`.

### New Metrics Section: "Strange Attractors"
After the existing health/vote sections, add:

1. **Temperature Distribution**: Show memory count in key ranges (0-30 cold, 30-60 warm, 60-70 boundary, 70-90 hot, 90-100 sacred). Highlight the 60-70 gap if still present.
2. **Vote Confidence Clusters**: Show vote count at each 0.1 bucket. Flag any bucket with > 2x average.
3. **Circadian Pattern**: Show memory creation count for last 24h by 2-hour blocks. Note peak hours.
4. **Drift Trend**: If refractory/drift metrics available, show alerts-per-hour trend.

### Format
Keep it concise -- Chief reads this on mobile. One line per metric, like:
```
ATTRACTORS: Temp gap 60-70: 262 (0.3%) | Vote 0.9 cluster: 1618 | Peak hours: 10AM, 10PM
```

## Acceptance Criteria
- Dawn mist report includes attractor section
- Metrics pulled from live DB, not hardcoded
- Format fits on mobile screen (no multi-line tables)
- Section only appears if data is available (graceful skip)
- No new dependencies added to dawn mist

## Dependencies
- Depends on attractor validation (Jr task #1189) for interpretation
- Kanban #2060, Jr task #1192.
