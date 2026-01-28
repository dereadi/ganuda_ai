# Ultrathink: Phase 3 Production Hardening

**Date:** January 28, 2026
**Priority:** P1 - Production readiness
**TPM:** Claude Opus
**Roadmap:** PRODUCTION_ROADMAP_30_60_90.md Phase 3

---

## Current State

### Services Running
- `llm-gateway.service` - Active, 16h uptime
- `vllm-cherokee.service` - Active, 12h uptime (cherokee-constitutional model)
- `vllm.service` - Main inference (Nemotron-9B)

### Jr Workers
- Currently running via nohup, not systemd
- `jr-queue-worker.service` exists but not installed/enabled

### Gaps
1. Jr workers not managed by systemd (no auto-restart, no journald logging)
2. No runbooks for incident response
3. No chaos tests for resilience validation
4. Multiple Jr workers needed (SE Jr, IT Triad Jr, Research Jr, Infrastructure Jr)

---

## Phase 3 Work Items

### 1. Systemd Services for Jr Workers

Create services for each Jr type to enable:
- Auto-restart on failure
- Journald logging (centralized)
- Proper dependencies (wait for vLLM)
- Resource limits

**Jr Types:**
- `jr-se.service` - Software Engineer Jr.
- `jr-it-triad.service` - IT Triad Jr.
- `jr-research.service` - Research Jr.
- `jr-infra.service` - Infrastructure Jr.

### 2. Runbooks

Create `/ganuda/runbooks/` with:
- `RUNBOOK-GPU-WEDGED.md` - GPU memory issues
- `RUNBOOK-JR-STUCK.md` - Jr not processing tasks
- `RUNBOOK-LLM-TIMEOUT.md` - vLLM latency issues
- `RUNBOOK-DB-CONNECTION.md` - PostgreSQL connectivity

### 3. Chaos Tests

Create `/ganuda/tests/chaos/` with:
- `test_vllm_restart.py` - Recovery after vLLM restart
- `test_jr_crash.py` - Jr worker crash and recovery
- `test_db_reconnect.py` - DB connection loss recovery

---

## Implementation Priority

1. **Systemd services** - Enable managed Jr workers
2. **Runbooks** - Document incident response
3. **Chaos tests** - Validate resilience (staging only)

---

FOR SEVEN GENERATIONS
