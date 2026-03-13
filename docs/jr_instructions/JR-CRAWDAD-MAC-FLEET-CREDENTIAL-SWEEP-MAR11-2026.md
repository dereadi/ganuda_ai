# JR INSTRUCTION: Crawdad Security Sweep — Mac Fleet Credential Remediation

**Task**: Scrub compromised credentials from sasass + sasass2, lock down exposed services, rotate DB credentials, harden both nodes
**Priority**: P0 — compromised credential on two nodes for 18+ days
**Date**: 2026-03-11
**TPM**: Claude Opus
**Story Points**: 5
**Council Vote**: #8884 (audit a997dd3f4c3b77df), APPROVED (0.91)
**Crawdad Lead**: This is a security remediation task. Crawdad has point.
**Chief Context**: "I did note a couple days ago before I booted all the routers that I was having a connection issue or three with bmasass, it also locked itself out a few times." Chief has security-aware friends who may test the perimeter.

## Problem Statement

The credential `jawaseatlasers2` is hardcoded in at least **14 files across two nodes** (sasass: 7 files, sasass2: 7 files). Both nodes were provisioned from the same template. The credential has been in plaintext for 18+ days minimum. A second credential (`cherokee_spoke_2024`) and a third (`TYDo5U2NVkXqQ8DHuhIpvRgLUrXf2iZE` in Jane Street experiment files) are also exposed on sasass.

Compound risk: bmasass (same LAN) exhibited connection anomalies and self-lockouts ~Mar 9 before Chief rebooted all routers. If `jawaseatlasers2` was harvested, lateral movement to bluefin's production DB is the attack path.

## Scope

Two nodes: **sasass** (192.168.132.241) and **sasass2** (192.168.132.242). Both macOS.

This instruction does NOT cover sasass2 artifact thermalization or daemon fixes — that's in JR-SASASS2-TRIAGE-THUNDERDUCK-ZERO-MAR11-2026.md. This instruction is security-only.

## What You're Building

### Step 1: Verify Credential Status on bluefin

Before scrubbing, determine if `jawaseatlasers2` is the CURRENT password for the `claude` DB user on bluefin, or if it's stale (already rotated).

SSH to bluefin (192.168.132.222 or WireGuard 10.100.0.2):

```text
# Test if the credential works
psql -h 192.168.132.222 -U claude -d zammad_production -c "SELECT 1;"
# With the exposed password
PGPASSWORD='jawaseatlasers2' psql -h 192.168.132.222 -U claude -d zammad_production -c "SELECT 1;"
```

If it connects: the credential is LIVE and must be rotated immediately.
If it fails: the credential is stale (already rotated). Still scrub it from all files — stale credentials in plaintext are still a Crawdad violation.

Also test the Jane Street credential:
```text
PGPASSWORD='TYDo5U2NVkXqQ8DHuhIpvRgLUrXf2iZE' psql -h 192.168.132.222 -U claude -d zammad_production -c "SELECT 1;"
```

**Record results as a thermal** — this is the audit trail.

### Step 2: Credential Rotation (if live)

If `jawaseatlasers2` is still the active credential:

1. Generate a new secure password (32+ chars, alphanumeric + symbols)
2. On bluefin, update the `claude` DB user:
```text
ALTER USER claude WITH PASSWORD 'new_password_here';
```
3. Update `/ganuda/config/secrets.env` on redfin with the new credential
4. Restart all services on redfin that use CHEROKEE_DB_PASS
5. Verify all federation services reconnect cleanly

**If the Jane Street credential is also live**, rotate it too or revoke it if it's a secondary credential for the same user.

**FLAG FOR TPM**: If rotation breaks running services, escalate immediately. Do NOT leave the cluster in a broken state.

### Step 3: Scrub sasass (192.168.132.241)

SSH to sasass (192.168.132.241 or Tailscale 100.93.205.120).

**7 files with `jawaseatlasers2`:**

| # | File | Fix |
|---|------|-----|
| 1 | `.secrets/sasass_secrets.env` | Replace value + chmod 600 |
| 2 | `hub_spoke_sync_client.py` line 61 | Change default to `""` |
| 3 | `jr_executor/jr_bidding_daemon.py` line 30 | Change default to `""` |
| 4 | `jr_executor/jr_task_executor.py` line 34 | Change default to `""` |
| 5 | `lib/xontrib_cherokee.py` line 22 | Replace hardcoded with `os.environ.get("CHEROKEE_DB_PASS", "")` |
| 6 | `services/health_monitor/health_monitor.py` line 19 | Replace hardcoded with `os.environ.get("CHEROKEE_DB_PASS", "")` |
| 7 | `services/embedding_service/embedding_server.py` line 35 | Replace hardcoded with `os.environ.get("CHEROKEE_DB_PASS", "")` |

**Additional credential: `cherokee_spoke_2024`** in `hub_spoke_sync_client.py` line 67:
- Change default to `""`

**Jane Street credential** in 4 files under `experiments/jane-street/track2_permutation/`:
- Replace all instances with `os.environ.get("CHEROKEE_DB_PASS", "")`

**Fix secrets.env permissions:**
```text
chmod 600 /Users/Shared/ganuda/.secrets/sasass_secrets.env
```

### Step 4: Scrub sasass2 (192.168.132.242)

SSH to sasass2 (192.168.132.242).

**7 files with `jawaseatlasers2`** (same template as sasass):

| # | File | Fix |
|---|------|-----|
| 1 | `.secrets/` env file (if exists) | Replace value + chmod 600 |
| 2 | `hub_spoke_sync_client.py` | Change default to `""` |
| 3 | `jr_executor/jr_bidding_daemon.py` | Change default to `""` |
| 4 | `jr_executor/jr_task_executor.py` | Change default to `""` |
| 5 | `lib/xontrib_cherokee.py` | Replace hardcoded with `os.environ.get("CHEROKEE_DB_PASS", "")` |
| 6 | `services/health_monitor/health_monitor.py` (if exists) | Replace hardcoded |
| 7 | `services/embedding_service/embedding_server.py` (if exists) | Replace hardcoded |

Run a full grep after scrubbing to confirm zero remaining instances:
```text
grep -r 'jawaseatlasers2' /Users/Shared/ganuda/
grep -r 'cherokee_spoke_2024' /Users/Shared/ganuda/
grep -r 'TYDo5U2NVkXqQ8DHuhIpvRgLUrXf2iZE' /Users/Shared/ganuda/
```

Must return zero results.

### Step 5: Lock Legacy `claude` User Account on sasass

The `claude` user (UID 1001) on sasass has a live `/bin/bash` shell. It was the original "Claude AI as a user" account from Jun-Jul 2025. It should be locked:

```text
# Lock the shell (macOS)
sudo dscl . -create /Users/claude UserShell /usr/bin/false
```

**Do NOT delete the account** — it may have historical artifacts in its home directory. Just disable interactive login.

`svc_claude` (UID 502) is already locked correctly (`/usr/bin/false`). No action needed.

### Step 6: Network Hardening on sasass

**PostgreSQL** — Currently listening on `*:5432`. Unless other nodes need to connect to sasass's Postgres:
```text
# In postgresql.conf (Postgres.app)
listen_addresses = 'localhost'
```
Then restart Postgres.app.

**Cloudflare tunnel audit** — `/Users/dereadi/.cloudflared/config.yml` exposes:
- `cherokee.derplex.us` → localhost:8080 (Python http.server serving old HTML)
- `terminal.derplex.us` → localhost:4200 (not running)

Confirm with Chief whether these tunnels are intentional. If not, remove the stale entries.

**Grafana on `*:3000`** — Verify auth is enabled in grafana.ini. If no auth, bind to localhost only or add authentication.

### Step 7: Auth Log Review (bmasass correlation)

Check bmasass (192.168.132.21 or Tailscale 100.103.27.106) for auth anomalies around Mar 9:

```text
# macOS unified log — failed auth attempts
log show --predicate 'eventMessage contains "authentication" OR eventMessage contains "failed"' --start '2026-03-08' --end '2026-03-10'

# SSH specifically
log show --predicate 'process == "sshd" AND eventMessage contains "Failed"' --start '2026-03-08' --end '2026-03-10'
```

Also check:
```text
# Tailscale — any peer changes
tailscale status
tailscale debug peer-status

# Open connections
lsof -i | grep ESTABLISHED
```

**Thermalize findings** regardless of result. "No anomalies found" is a valid and important audit record.

### Step 8: Audit Thermal

After all steps, insert a single comprehensive audit thermal:

```text
INSERT INTO thermal_memory_archive (original_content, temperature_score, domain_tag, sacred_pattern, memory_hash, metadata)
VALUES (
  'CRAWDAD SECURITY AUDIT: Mac fleet credential sweep Mar 11, 2026. Nodes: sasass (192.168.132.241), sasass2 (192.168.132.242). Findings: [CREDENTIAL_STATUS], [FILES_SCRUBBED], [ACCOUNTS_LOCKED], [NETWORK_CHANGES], [BMASASS_AUTH_LOG_RESULT]. Rotation: [YES/NO + details]. All jawaseatlasers2 instances removed. All cherokee_spoke_2024 instances removed. Jane Street credential [STATUS].',
  88, 'security', false,
  sha256_hash,
  '{"audit_type": "credential_sweep", "nodes": ["sasass", "sasass2"], "crawdad_led": true, "council_vote": 8884}'::jsonb
);
```

Fill in the bracketed values with actual results.

## Constraints

- **Crawdad**: This is a security task. Credential scrub MUST complete before any other work on these nodes.
- **Coyote**: Treat all exposed credentials as compromised (vote #8883 condition). Rotation before or simultaneous with scrub.
- **Turtle**: Do NOT break running services during rotation. If credential rotation will disrupt the cluster, coordinate with TPM first.
- **DC-7**: The `claude` user account on sasass is historical. Lock it, don't delete it.
- Both nodes are macOS. Use `dscl` for user management, `launchctl` for services.
- bmasass is Chief's mobile node (M4 Max 128GB). Be careful with any changes — report only, don't modify without explicit authorization.
- `jawaseatlasers2` appears in the same relative paths on both nodes — they share a provisioning template. Any fix must cover BOTH nodes.

## Target Files

### sasass (192.168.132.241)
- `/Users/Shared/ganuda/.secrets/sasass_secrets.env` — rotate value + chmod 600
- `/Users/Shared/ganuda/hub_spoke_sync_client.py` — scrub 2 credentials
- `/Users/Shared/ganuda/jr_executor/jr_bidding_daemon.py` — scrub
- `/Users/Shared/ganuda/jr_executor/jr_task_executor.py` — scrub
- `/Users/Shared/ganuda/lib/xontrib_cherokee.py` — scrub (code change required)
- `/Users/Shared/ganuda/services/health_monitor/health_monitor.py` — scrub (code change required)
- `/Users/Shared/ganuda/services/embedding_service/embedding_server.py` — scrub (code change required)
- `/Users/Shared/ganuda/experiments/jane-street/track2_permutation/` — 4 files, scrub

### sasass2 (192.168.132.242)
- Same relative paths as sasass — 7 files minimum

### bluefin (192.168.132.222)
- DB credential rotation if `jawaseatlasers2` is still live

## Acceptance Criteria

- `grep -r 'jawaseatlasers2' /Users/Shared/ganuda/` returns ZERO results on BOTH nodes
- `grep -r 'cherokee_spoke_2024' /Users/Shared/ganuda/` returns ZERO results on sasass
- `grep -r 'TYDo5U2NVkXqQ8DHuhIpvRgLUrXf2iZE' /Users/Shared/ganuda/` returns ZERO results on sasass
- `.secrets/sasass_secrets.env` is chmod 600
- `claude` user on sasass has shell set to `/usr/bin/false`
- bmasass auth logs reviewed and thermalized
- Audit thermal stored with complete findings
- All federation services still running after rotation (if rotation was needed)
- Zero hardcoded credentials remaining in any .py, .sh, .env file on either node

## DO NOT

- Leave any instance of `jawaseatlasers2` in any file on any node
- Delete the `claude` user account — lock it only
- Break running services during credential rotation without TPM coordination
- Modify bmasass beyond reading its auth logs — report only
- Skip the audit thermal — the record matters as much as the fix
- Store the new credential in any source file — env vars only
