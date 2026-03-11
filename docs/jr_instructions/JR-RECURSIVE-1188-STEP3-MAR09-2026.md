# [RECURSIVE] DC-15 Fire Guard Refractory Period PoC - Step 3

**Parent Task**: #1188
**Auto-decomposed**: 2026-03-09T22:37:23.963391
**Original Step Title**: Add feature flag

---

### Step 3: Add feature flag

In `/ganuda/daemons/.governance_state.json`, add:
```json
"dc15_refractory_enabled": false
```
Fire guard should check this flag. When false, skip all refractory logic (Spider reversibility gate).
