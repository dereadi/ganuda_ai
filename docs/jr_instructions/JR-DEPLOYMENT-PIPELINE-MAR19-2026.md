# JR INSTRUCTION: Deployment Pipeline — ganuda-deploy + Service Map

**Task ID**: DEPLOY-PIPELINE-001
**Priority**: P1 (Critical — active stale-code incident)
**SP Estimate**: 8
**Council Vote**: #8983 (hash c43d076c738c3c04), UNANIMOUS APPROVE, confidence 0.88
**Standing Dissent**: Coyote — fire-guard stale-code detection required as Phase 2
**Created**: March 19, 2026
**Thermal**: #129366

---

## Problem Statement

Running systemd services do not pick up code changes after `git pull`. The LLM gateway ran stale code for 3 days (Mar 16-19, 2026). There are 20+ running services on redfin alone. No mechanism exists to:
1. Detect which services are affected by a code change
2. Restart those services after pull
3. Verify the restart succeeded

This is a systemic gap. Every `git pull` since federation inception has silently left services running old code.

## Solution (Council-Approved: Option 5 — Hybrid)

Three deliverables:
1. **`/ganuda/config/service-map.yaml`** — Manifest mapping code paths to systemd service names
2. **`/ganuda/scripts/ganuda-deploy`** — Script that diffs changes and restarts affected services
3. **Jr workflow amendment** — All Jr tasks touching service code must call `ganuda-deploy` post-merge

---

## Implementation Steps

### Step 1: Create Service Map Manifest (2 SP)

Create `/ganuda/config/service-map.yaml` with the following structure:

```yaml
# Cherokee AI Federation — Service Map
# Maps source code paths to systemd service names
# Used by ganuda-deploy to detect which services need restart after code changes
# SECURITY: This file must be owned root:root, mode 0644 (Crawdad condition)

services:
  llm-gateway.service:
    paths:
      - services/llm_gateway/
    critical: true    # Requires health check before restart (Turtle condition)

  sag.service:
    paths:
      - services/sag_unified/
      - services/sag-v2/
    critical: true

  jr-executor.service:
    paths:
      - services/jr-executor/
    critical: true

  consultation-ring.service:
    paths:
      - services/consultation_ring.py
    critical: false

  embedding.service:
    paths:
      - services/embedding_service/
    critical: false

  # ... map ALL 20+ services
```

Populate by cross-referencing:
- `ls /ganuda/services/` (source directories)
- `systemctl list-units --type=service --state=running` (running services)
- `ls /ganuda/scripts/systemd/*.service` (service unit files, check ExecStart paths)

Set file permissions: `chmod 644 /ganuda/config/service-map.yaml` (Crawdad condition: non-privileged users cannot modify).

### Step 2: Create ganuda-deploy Script (4 SP)

Create `/ganuda/scripts/ganuda-deploy` (executable, owned root:root):

**Inputs**: None (operates on current git state)

**Logic**:
1. `cd /ganuda`
2. Capture current HEAD: `OLD_HEAD=$(git rev-parse HEAD)`
3. `git pull origin main`
4. Capture new HEAD: `NEW_HEAD=$(git rev-parse HEAD)`
5. If `OLD_HEAD == NEW_HEAD`, print "Already up to date" and exit 0
6. Get changed files: `git diff --name-only $OLD_HEAD $NEW_HEAD`
7. Parse `/ganuda/config/service-map.yaml` — for each service entry, check if any changed file matches any of its paths
8. For each matched service:
   a. Check if service is currently running (`systemctl is-active`)
   b. If service is marked `critical: true`:
      - Log warning: "Critical service {name} affected — restarting with health check"
      - Run pre-restart check (verify unit file syntax: `systemd-analyze verify`)
   c. Call `ganuda-deploy-service {service_name}` (uses existing FreeIPA sudo wrapper)
   d. Wait 3 seconds, verify service is active
   e. If restart failed, log error and continue (do not cascade-fail)
9. Log all actions to `/ganuda/logs/deploy.log` (append-only) with:
   - Timestamp
   - OLD_HEAD and NEW_HEAD hashes (Crawdad: code hash in log)
   - List of services restarted and their status
   - Operator (from `whoami`)
10. Validate git remote origin is `github.com/ganuda` or expected origin (Crawdad: origin validation)

**Flags**:
- `--dry-run`: Show what would restart, do not restart
- `--force`: Skip critical service confirmation (use with caution)
- `--service <name>`: Restart only a specific service regardless of diff

**Error handling**:
- If `git pull` fails, exit 1 with error
- If a service restart fails, log and continue (do not abort remaining restarts)
- Send Telegram notification on any failure (reuse existing notification pattern from ganuda-deploy-service)

### Step 3: Add to FreeIPA Sudo Rules (0.5 SP)

The `ganuda-deploy` script calls `ganuda-deploy-service` internally (already FreeIPA-approved). Verify that the existing `ganuda-service-management` sudo rule covers the restart path. If `ganuda-deploy` itself needs sudo, add it to the FreeIPA `ganuda-service-management` rule:

```
/ganuda/scripts/ganuda-deploy
```

### Step 4: Jr Workflow Amendment (1 SP)

Add to the Jr executor task template (in `/ganuda/services/jr-executor/`):

**Post-completion step for any task that modifies files under `/ganuda/services/`**:

> After committing and pushing changes to any file under `/ganuda/services/`, run:
> ```
> /ganuda/scripts/ganuda-deploy --dry-run
> ```
> Review output. If services are listed for restart, run:
> ```
> /ganuda/scripts/ganuda-deploy
> ```
> Include the deploy output in the task completion report.

This must be wired into the Jr executor's task completion logic, not just documented.

### Step 5: Immediate Remediation (0.5 SP)

Restart the LLM gateway NOW to resolve the active stale-code incident:

```bash
sudo systemctl restart llm-gateway.service
systemctl is-active llm-gateway.service
# Verify: curl http://localhost:8080/health
```

---

## Verification Criteria

- [ ] `/ganuda/config/service-map.yaml` exists, maps all running services to source paths, permissions 0644
- [ ] `/ganuda/scripts/ganuda-deploy` is executable, runs without error
- [ ] `ganuda-deploy --dry-run` correctly identifies services affected by a test commit
- [ ] `ganuda-deploy` successfully restarts a non-critical service after a code change
- [ ] Critical services prompt health check before restart
- [ ] Deploy log written to `/ganuda/logs/deploy.log` with commit hashes
- [ ] Jr executor includes post-deploy step for service-touching tasks
- [ ] LLM gateway is running current code (immediate fix)

## Council Conditions Checklist

- [ ] **Turtle**: Health-check gates on critical services before restart
- [ ] **Turtle**: Rollback path documented (re-checkout old commit + restart)
- [ ] **Crawdad**: Git remote origin validated before pull
- [ ] **Crawdad**: Deploy log includes code hashes, append-only
- [ ] **Crawdad**: service-map.yaml permissions locked (0644, root-owned)
- [ ] **Owl**: No new daemons created (script-only, no inotify/watcher)
- [ ] **Raven**: Script is node-agnostic (works on any node with ganuda repo)
- [ ] **Spider**: Integrates with existing ganuda-deploy-service FreeIPA wrapper

## Phase 2 (Not Blocked — Future Jr Task)

Per Coyote standing dissent: Add stale-code detection to fire-guard. Fire-guard should compare running service code (via `/proc/{pid}/exe` or service start time vs. file mtime) against git HEAD and alert if drift exceeds 1 hour. This is a separate Jr task to be created after Phase 1 is verified.

## Blocking Dependencies

- None. This task can begin immediately.
- The existing `ganuda-deploy-service` script and FreeIPA sudo rules are already in place.

## Do Not

- Do NOT create a new daemon or long-running service for this
- Do NOT use git hooks as the primary mechanism (they are local and bypassable)
- Do NOT auto-restart without the service-map — guessing which services to restart is worse than not restarting
