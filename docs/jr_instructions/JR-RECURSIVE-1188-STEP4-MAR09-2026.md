# [RECURSIVE] DC-15 Fire Guard Refractory Period PoC - Step 4

**Parent Task**: #1188
**Auto-decomposed**: 2026-03-09T22:37:23.973463
**Original Step Title**: Add metrics to dawn mist

---

### Step 4: Add metrics to dawn mist

At the end of each fire guard run, write refractory metrics to a JSON file at `/ganuda/logs/refractory_metrics.json` that dawn mist can read.

## Acceptance Criteria
- After 3+ alerts in 5 minutes, fire guard enters refractory (check frequency drops 10x)
- During refractory, alerts are logged but NOT sent to Slack/Telegram
- State verification runs before resuming full frequency
- If state still degraded at refractory end, refractory extends by half duration
- Feature flag `dc15_refractory_enabled` in .governance_state.json controls activation
- Metrics available: alerts_before, alerts_during, refractory_entries, noise_reduction_ratio
- Coyote answer: compare noise_reduction_ratio across runs. If > 0.3, intentionality reduces noise.

## Dependencies
- None for PoC. Production deployment requires DC-15 formal spec (Jr task #1190).
- Kanban #2056, Jr task #1188.
