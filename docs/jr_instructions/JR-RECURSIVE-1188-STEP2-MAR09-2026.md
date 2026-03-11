# [RECURSIVE] DC-15 Fire Guard Refractory Period PoC - Step 2

**Parent Task**: #1188
**Auto-decomposed**: 2026-03-09T22:37:23.956768
**Original Step Title**: Integrate into fire_guard.py

---

### Step 2: Integrate into fire_guard.py

In `/ganuda/scripts/fire_guard.py`, import and use the refractory manager. The existing check loop should:
1. Call `manager.record_alert()` when an alert condition is detected
2. Check `manager.should_check(iteration)` before running expensive health checks
3. Check `manager.should_alert()` before sending Slack/Telegram notifications
4. Call `manager.verify_state_before_resume()` when refractory period expires
