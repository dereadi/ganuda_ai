# JR INSTRUCTION: Observability Stack — Three-Legged BSM Pattern

**Task**: Build the three-legged observability stack modeled on Partner's BSM Engineering heritage at Walmart.
**Priority**: P1
**Date**: 2026-03-18
**TPM**: Claude Opus
**Story Points**: 11
**Project Spec**: #4
**Depends On**: Fire-guard (LIVE), DB query monitor (LIVE), gateway (LIVE)
**Thermal Context**: Partner BSM three legs, internal SLAs

## Context

Partner's BSM Engineering team at Walmart had three legs:
1. **Event Management** — What happened. Alerts, incidents, state changes.
2. **Performance Management** — How fast. Speed at scale, bottleneck identification.
3. **Remedy** — The platform. 6M transactions/day. Actionable data layer.

They logged ALL data and made it actionable. Not dashboards for show — reports that drove decisions.

We currently have fire-guard (partial Leg 1). Missing Legs 2 and 3 entirely.

## Task 1: Leg 1 Gap Analysis — Fire-Guard Coverage (2 SP, P-3)

Audit fire-guard's necklace. For every service in the federation, verify:
- Health check exists and is semantically correct (not just port-open)
- Alert path works (Slack primary, Telegram fallback)
- Disabled state handled correctly (consultation ring pattern)

**Known gaps**:
- VetAssist has no fire-guard health check
- Some services may have been added since last necklace update
- Confirm consultation ring health check (added this session) works

**Output**: Updated necklace with complete service coverage. Document any services that CANNOT be health-checked and why.

## Task 2: Leg 2 — End-to-End Latency Tracing (5 SP, P-2)

Instrument the gateway request lifecycle. For every request through the gateway:

1. Record timestamp at gateway receive
2. Record timestamp at model inference start/end
3. Record timestamp at DB query start/end (if applicable)
4. Record timestamp at response send
5. Calculate: total_ms, inference_ms, db_ms, overhead_ms

**Implementation options** (pick simplest):
- Option A: Structured logging with request_id correlation (parse from logs)
- Option B: Lightweight middleware in gateway.py that writes timing to a CSV or DB table
- Option C: Langfuse integration (Jr instruction exists: JR-LANGFUSE-GATEWAY-WIRING-MAR16-2026.md)

**Key principle from Partner**: "Follow the latency through EVERY layer — code, API, network, DB. Optimize wherever the pain is, not just where it's easy to measure."

Our stack: gateway (Python) → HTTP → bluefin (PostgreSQL) → back. Consultation ring: tokenizer → frontier API → valence gate → DB. Each hop compounds.

**Output**: Per-request timing breakdown. Stored for aggregation.

## Task 3: Leg 3 — Weekly Actionable Report (3 SP, P-1)

Aggregate all observability data into a single weekly report. This is the BSM "reports that drove decisions" principle.

**Report sections**:
1. **Event Summary**: Service uptime %, incidents this week, fire-guard alert count
2. **Performance Summary**: p50/p95/p99 latency by endpoint, top 10 slowest requests, latency trend (improving/degrading)
3. **DB Health**: Rollback rate, top query offenders by duration, top offenders by frequency, connection utilization
4. **Memory Health**: RSS per service, growth trends, any 20%+ growth alerts
5. **Consultation Ring**: Consultations this week, provider distribution, valence gate reject count
6. **Recommendations**: Auto-generated from thresholds. "Rollback rate above SLA — investigate." "Gateway p95 degraded 15% — check model loading."

**Output format**: Markdown posted to Slack #saturday-morning (or #fire-guard). Compatible with owl-debt-reckoning and dawn-mist consumption.

## Task 4: Wire Into Owl + Dawn Mist (1 SP, P-Day)

- Dawn mist (daily 6:15 AM) gets a health summary: any alerts overnight, current rollback rate, service status
- Owl weekly review (Wed 5 AM) gets the full Leg 3 report
- Saturday Morning Meeting (Sat 7 AM, when built) gets the executive summary

## Design Principle

"We were building around the blackbox to tell the owners of the blackbox what's wrong with their code." — Partner

This stack doesn't FIX problems. It FINDS them and tells us where to look. The fix happens at source — indexes, query rewrites, code paths. The observability stack is the BSM team watching the engine. The development team (Jrs) fixes what BSM finds.
