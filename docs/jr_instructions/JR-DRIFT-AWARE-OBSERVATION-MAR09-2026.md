# Jr Instruction: Drift-Aware Graduated Observation PoC

## Context
Approved as DC-15 corollary in Longhouse 68ae6229c53cb225. Spider condition: isolate from existing fire_guard.py as a separate module. Reversibility gate: feature flag in .governance_state.json. References DC-10 (reflex), DC-11 (same pattern every scale), DC-15 (refractory). Decomposed in 3c06ea3bbd4b6a24.

## Task
Create `/ganuda/lib/drift_observer.py` -- a module that implements O(drift) health monitoring instead of O(N) polling.

### Core Concept
Instead of fire_guard polling every service at fixed intervals:
- Each service self-reports a "drift score" (how far it has drifted from last known-good state)
- The observer listens for drift reports
- High-drift services get checked more frequently
- Low-drift services get checked less frequently
- Zero-drift services get checked only on schedule (dawn mist, weekly)

### Drift Score Calculation (per service)
- CPU/memory delta from baseline: 0-30 points
- Error rate change: 0-30 points
- Response time deviation: 0-20 points
- Time since last check: 0-20 points (increases naturally)
- Total: 0-100, higher = more drift = check sooner

### Implementation
1. Create `/ganuda/lib/drift_observer.py` with DriftObserver class
2. Each node runs a lightweight drift reporter (future Jr task)
3. Fire guard imports drift_observer and uses drift scores to prioritize checks
4. Feature flag: `dc15_drift_observation_enabled` in .governance_state.json

### Phase 1 (this task): Observer module + fire_guard integration
### Phase 2 (future): Node-side drift reporters
### Phase 3 (future): Full replacement of fixed-interval polling

## Acceptance Criteria
- drift_observer.py exists with DriftObserver class
- Drift score calculation works for known services
- Fire guard can import and use drift scores to skip low-drift checks
- Feature flag controls activation (default: off)
- Logging shows which checks were skipped due to low drift
- Metrics: checks_skipped, checks_run, avg_drift_score
- Reversibility: disable feature flag restores original O(N) behavior exactly

## Dependencies
- Depends on DC-15 Fire Guard Refractory PoC (Jr task #1188) being merged first
- Kanban #2059, Jr task #1191.
