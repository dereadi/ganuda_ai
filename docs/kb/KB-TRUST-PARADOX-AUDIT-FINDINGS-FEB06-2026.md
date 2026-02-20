# KB: Trust Paradox Security Audit - Critical Findings

**Date:** 2026-02-06
**Task ID:** 594
**Category:** Security Audit
**Severity:** HIGH
**Auditor:** Crawdad (Security Specialist)

## Executive Summary

The Trust Paradox Security Audit (Task 594) discovered **50+ files with hardcoded database credentials** across the `/ganuda/lib/` codebase. This represents a significant security vulnerability that requires immediate remediation.

## Critical Finding: Hardcoded Credentials

### Scope of Issue

Password `jawaseatlasers2` found hardcoded in the following files:

| File | Line | Risk |
|------|------|------|
| `/ganuda/lib/specialist_council.py` | 34 | HIGH |
| `/ganuda/lib/agemem_tools.py` | 12 | HIGH |
| `/ganuda/lib/rlm_bootstrap.py` | 17 | HIGH |
| `/ganuda/lib/hive_mind.py` | 22 | HIGH |
| `/ganuda/lib/saga_transactions.py` | 416 | HIGH |
| `/ganuda/lib/magrpo_tracker.py` | 30 | HIGH |
| `/ganuda/lib/jr_momentum_learner.py` | 38 | HIGH |
| `/ganuda/lib/drift_detection.py` | 36 | MEDIUM |
| `/ganuda/lib/research_dispatcher.py` | 19 | HIGH |
| `/ganuda/lib/telegram_session_manager.py` | 19 | MEDIUM |
| `/ganuda/lib/vlm_clause_evaluator.py` | 16 | HIGH |
| `/ganuda/lib/vlm_relationship_storer.py` | 19 | HIGH |
| `/ganuda/lib/consciousness_cascade/gpu_monitor.py` | 26 | MEDIUM |
| `/ganuda/lib/metacognition/reflection_api.py` | 285 | MEDIUM |
| `/ganuda/lib/metacognition/council_integration.py` | 341 | MEDIUM |
| `/ganuda/lib/metacognition/resonance_lookup.py` | 17 | MEDIUM |
| `/ganuda/lib/constitutional_constraints.py` | 31 | HIGH |
| `/ganuda/lib/amem_memory.py` | 20 | HIGH |
| `/ganuda/lib/jr_state_manager.py` | 19 | HIGH |
| `/ganuda/lib/jr_task_executor_v2.py` | 70 | HIGH |
| `/ganuda/lib/jr_bidding_daemon.py` | 50 | HIGH |
| `/ganuda/lib/halo_council.py` | 46 | MEDIUM (uses env fallback) |
| `/ganuda/lib/smadrl_pheromones.py` | 26 | MEDIUM (uses env fallback) |
| 30+ backup files (.bak, .backup_*) | Various | MEDIUM |

### Existing Mitigation (Partial)

A `secrets_loader.py` module exists at `/ganuda/lib/secrets_loader.py` that implements a three-tier secret resolution:

1. `/ganuda/config/secrets.env` (file-based, preferred)
2. Environment variables (fallback)
3. FreeIPA vault via `/ganuda/scripts/get-vault-secret.sh` (last resort)

However, **most library files are NOT using this loader** and instead have inline hardcoded credentials.

## Remediation Required

### Priority 1 (Immediate)
1. Rotate the exposed database password `jawaseatlasers2`
2. Update all files to use `secrets_loader.get_db_config()`
3. Remove credentials from backup files

### Priority 2 (This Week)
4. Create `/ganuda/config/secrets.env` on all nodes
5. Configure systemd services with proper environment files
6. Add pre-commit hook to prevent credential commits

### Priority 3 (This Sprint)
7. Migrate to FreeIPA vault for all secrets
8. Implement credential rotation automation
9. Add CI/CD secret scanning

## Files Using Proper Pattern (Reference)

These files properly use environment variables with fallback:

```python
# Good pattern - halo_council.py line 46
'password': os.environ.get('CHEROKEE_DB_PASS', 'jawaseatlasers2')
```

However, even this pattern exposes the fallback value in code. The ideal pattern is:

```python
# Best pattern - using secrets_loader
from lib.secrets_loader import get_db_config
db_config = get_db_config()  # No hardcoded values
```

## Related Task

- **Task 597 (Bluefin Hardware Probe):** BLOCKED due to NVML driver mismatch
  - Error: `NVML library version: 570.211` vs installed driver
  - Requires manual driver update on bluefin before retry

## Trust Paradox Research Context

This audit was conducted per arXiv:2510.18563 "Trust Paradox in LLM Multi-Agent Systems":
- **Over-Exposure Rate (OER):** HIGH - credentials shared in plain text across all nodes
- **Authorization Drift (AD):** HIGH - any Jr agent can access database with full privileges
- **MNI Compliance:** FAILED - credentials exposed beyond minimum necessary

## For Seven Generations

Security debt compounds across generations. Addressing these hardcoded credentials now prevents future exploitation and establishes proper secret management practices for the Federation.
