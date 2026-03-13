# [RECURSIVE] sasass2 Triage — Thunderduck Zero (crash loops, credential scrub, thermalize artifacts) - Step 3

**Parent Task**: #1277
**Auto-decomposed**: 2026-03-11T15:49:06.613997
**Original Step Title**: Log Rotation

---

### Step 3: Log Rotation

The following logs are bloated:

| Log | Size | Status |
|-----|------|--------|
| Hub-spoke sync client | ~180 MB | Active (still writing) |
| executive_jr errors | ~110 MB | Crash loop output |
| memory_jr errors | ~110 MB | Crash loop output |
| meta_jr errors | ~115 MB | Crash loop output |
| Misc | ~385 MB | Various |

Actions:
1. **Crash loop logs**: Truncate after Step 1 fixes the root cause. `> /path/to/logfile` or `truncate -s 0`
2. **Hub-spoke sync log**: Rotate (copy to `.1`, truncate active). Do NOT delete — this is a live service.
3. **Set up basic log rotation**: Create a cron job or launchd plist that truncates logs over 50 MB weekly.

Target: Reclaim ~800 MB. Node should be under 600 MB after cleanup.
