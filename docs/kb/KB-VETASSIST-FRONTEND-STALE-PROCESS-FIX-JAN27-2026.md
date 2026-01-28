# KB: VetAssist Frontend Stale Process Issue

**KB ID:** KB-VETASSIST-FRONTEND-STALE-PROCESS-FIX-JAN27-2026
**Date:** 2026-01-27
**Severity:** P1 - Production Impact
**Status:** Resolved

---

## Symptom

VetAssist dashboard loading extremely slowly (~11 seconds or 136+ seconds per request) when accessed via the public URL (https://vetassist.ganuda.us/).

## Root Cause Analysis

### Finding 1: Stale Process Running from Deleted Directory

The Next.js server (PID 267573) was started at **21:55:03** on Jan 26, 2026.
The frontend was **rebuilt** at **22:43** (~48 minutes later).

The running process was executing from a **deleted directory**:
```
/proc/267573/cwd -> /ganuda/vetassist/frontend/.next/standalone (deleted)
```

This caused file access delays manifesting as 11-second timeouts when the process tried to access resources from the deleted standalone build.

### Finding 2: NAT Hairpin Issue

Testing from inside the network to the public IP (162.233.86.232) experiences connection timeouts due to NAT hairpin/loopback not being configured on the network router/firewall.

**Impact:** Cannot test external access from inside the network. External users may or may not experience the same issue depending on their network path.

## Resolution

### Immediate Fix Applied

1. Killed the stale Next.js process:
   ```bash
   kill 267573
   ```

2. Started fresh Next.js server from the current standalone build:
   ```bash
   cd /ganuda/vetassist/frontend/.next/standalone
   nohup node server.js > /var/log/ganuda/vetassist-frontend.log 2>&1 &
   ```

3. Verified the new process (PID 996971) is running from the correct directory:
   ```
   /proc/996971/cwd -> /ganuda/vetassist/frontend/.next/standalone
   ```
   (No "deleted" marker)

### Post-Fix Performance

| Endpoint | Response Time |
|----------|---------------|
| Frontend (localhost:3000) | 1.6ms |
| Backend (localhost:8001/health) | 1.5ms |
| Caddy proxy (127.0.0.1:80) | 0.4ms |

## Prevention

### Recommended: Systemd Service for Next.js

Create a systemd service to manage the VetAssist frontend that:
1. Automatically restarts after rebuilds
2. Watches for file changes in the standalone directory
3. Logs to a consistent location

**JR Instruction:** Create `/ganuda/docs/jr_instructions/JR-VETASSIST-FRONTEND-SYSTEMD-SERVICE.md`

### Build Process Enhancement

After running `npm run build` for the frontend, the deployment script should:
1. Check if Next.js process is running from the old standalone directory
2. Restart the service gracefully

## Verification Commands

```bash
# Check if process is running from deleted directory
ls -la /proc/$(pgrep -f 'next-server')/cwd

# Test local endpoints
curl -w "%{time_total}s\n" -s http://localhost:3000/ -o /dev/null
curl -w "%{time_total}s\n" -s http://localhost:8001/health -o /dev/null

# Check Caddy proxy
curl -w "%{time_total}s\n" -s -H "Host: vetassist.ganuda.us" http://127.0.0.1:80/ -o /dev/null
```

## Related

- VetAssist Sprint 3 deliverables
- Network infrastructure NAT hairpin configuration (separate task)

---

FOR SEVEN GENERATIONS
