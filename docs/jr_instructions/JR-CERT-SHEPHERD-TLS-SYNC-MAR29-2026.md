# JR INSTRUCTION: Cert Shepherd — TLS Certificate Sync and Monitoring

**Task**: Automated TLS certificate monitoring, renewal alerting, and cross-node sync for the DMZ
**Priority**: P1 (production reliability — cert expiry = site down)
**Date**: 2026-03-29
**TPM**: Claude Opus
**Story Points**: 5
**Depends On**: Caddy on owlfin + eaglefin (LIVE), Let's Encrypt certs (LIVE), Fire Guard (LIVE)
**References**: JR-CERT-SHEPHERD-MAR10-2026.md (original design), kanban #2085

## Problem Statement

The federation serves HTTPS on two DMZ nodes (owlfin, eaglefin) via Caddy with Let's Encrypt certificates. Currently:

1. **No renewal monitoring** — if Caddy's auto-renewal fails silently, we find out when the browser shows a cert warning
2. **No cross-node cert sync** — owlfin and eaglefin manage certs independently. If one renews and the other doesn't, users hitting the other node get errors
3. **No Fire Guard visibility** — cert expiry is not part of the health page
4. **No alerting** — nobody gets notified when a cert is within 14 days of expiry

This is a ticking time bomb. Let's Encrypt certs expire every 90 days. One missed renewal = site down.

## Task 1: Cert Expiry Checker Script (2 SP)

**Create**: `/ganuda/scripts/cert_shepherd.py`

A script that checks TLS certificate expiry for all federation domains.

```python
#!/usr/bin/env python3
"""Cert Shepherd — TLS certificate expiry monitoring.

Checks all federation domains, alerts when certs are within WARNING_DAYS
of expiry, and records status for Fire Guard health page.

Kanban #2085. Council vote pending.
"""

import ssl
import socket
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Domains to monitor
DOMAINS = [
    "ganuda.us",
    "vetassist.ganuda.us",
    # Add more as deployed
]

WARNING_DAYS = 14    # Alert when cert expires within this many days
CRITICAL_DAYS = 7    # Escalate to critical within this many days
STATE_FILE = Path("/ganuda/state/cert_shepherd.json")

def check_cert(domain: str, port: int = 443, timeout: int = 10) -> dict:
    """Check TLS cert expiry for a domain. Returns status dict."""
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((domain, port), timeout=timeout) as sock:
            with ctx.wrap_socket(sock, server_hostname=domain) as ssock:
                cert = ssock.getpeercert()

        not_after = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z').replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        days_remaining = (not_after - now).days

        return {
            "domain": domain,
            "issuer": dict(x[0] for x in cert.get('issuer', [])).get('organizationName', 'unknown'),
            "expires": not_after.isoformat(),
            "days_remaining": days_remaining,
            "subject_alt_names": [x[1] for x in cert.get('subjectAltName', [])],
            "status": "CRITICAL" if days_remaining <= CRITICAL_DAYS
                      else "WARNING" if days_remaining <= WARNING_DAYS
                      else "OK",
            "error": None,
        }
    except Exception as e:
        return {
            "domain": domain,
            "status": "ERROR",
            "error": str(e),
            "days_remaining": -1,
        }

def main():
    results = {}
    alerts = []

    for domain in DOMAINS:
        result = check_cert(domain)
        results[domain] = result

        if result["status"] == "CRITICAL":
            alerts.append(f"CRITICAL: {domain} cert expires in {result['days_remaining']} days!")
        elif result["status"] == "WARNING":
            alerts.append(f"WARNING: {domain} cert expires in {result['days_remaining']} days")
        elif result["status"] == "ERROR":
            alerts.append(f"ERROR: Cannot check cert for {domain}: {result['error']}")

        print(f"  {domain}: {result['status']} ({result.get('days_remaining', '?')} days remaining)")

    # Save state for Fire Guard to read
    state = {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "domains": results,
        "alerts": alerts,
    }
    STATE_FILE.write_text(json.dumps(state, indent=2))

    # Alert via existing alert_manager
    if alerts:
        try:
            sys.path.insert(0, '/ganuda')
            from lib.alert_manager import send_alert
            severity = "critical" if any("CRITICAL" in a for a in alerts) else "high"
            send_alert(
                "\n".join(alerts),
                severity=severity,
                channel="fire-guard",
            )
        except Exception as e:
            print(f"  Alert send failed: {e}")

    return 1 if any(r["status"] != "OK" for r in results.values()) else 0

if __name__ == "__main__":
    sys.exit(main())
```

## Task 2: Systemd Timer (0.5 SP)

**Create**: `/ganuda/scripts/systemd/cert-shepherd.timer`

```ini
[Unit]
Description=Cert Shepherd — TLS certificate expiry check

[Timer]
OnCalendar=*-*-* 06:00,18:00
Persistent=true

[Install]
WantedBy=timers.target
```

**Create**: `/ganuda/scripts/systemd/cert-shepherd.service`

```ini
[Unit]
Description=Cert Shepherd — TLS certificate expiry check
After=network-online.target

[Service]
Type=oneshot
User=dereadi
WorkingDirectory=/ganuda
ExecStart=/ganuda/venv/bin/python /ganuda/scripts/cert_shepherd.py
Environment=PYTHONPATH=/ganuda
```

Run twice daily (6 AM and 6 PM). Certs don't change fast — this is plenty.

Deploy:
```bash
sudo cp /ganuda/scripts/systemd/cert-shepherd.* /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now cert-shepherd.timer
```

## Task 3: Fire Guard Integration (1 SP)

**File**: `/ganuda/scripts/fire_guard.py`

Add a cert health check that reads the Cert Shepherd state file:

```python
def check_cert_health():
    """Read cert shepherd state and return alerts for expired/expiring certs."""
    alerts = []
    try:
        state = json.loads(Path("/ganuda/state/cert_shepherd.json").read_text())
        for domain, info in state.get("domains", {}).items():
            if info.get("status") in ("CRITICAL", "WARNING", "ERROR"):
                alerts.append(f"TLS {info['status']}: {domain} — {info.get('days_remaining', '?')} days remaining")
        # Check staleness — if cert shepherd hasn't run in 24h, that's a problem too
        checked_at = datetime.fromisoformat(state["checked_at"])
        age_hours = (datetime.now(timezone.utc) - checked_at).total_seconds() / 3600
        if age_hours > 24:
            alerts.append(f"Cert Shepherd stale: last check {age_hours:.0f}h ago")
    except FileNotFoundError:
        pass  # Cert shepherd not deployed yet — don't alert
    except Exception as e:
        logger.warning(f"Cert health check failed: {e}")
    return alerts
```

Call from `run_checks()` and add results to the alerts list. Also add cert status to the health page HTML.

## Task 4: Cross-Node Cert Sync (1.5 SP)

Caddy stores certs in `~/.local/share/caddy/` by default. On the DMZ nodes (owlfin, eaglefin), both serve the same domains but manage certs independently.

**Option A (simpler)**: Point both Caddy instances at the same ACME account and let them renew independently. This is Caddy's default behavior and works fine for 2 nodes.

**Option B (if Option A fails)**: rsync certs from owlfin to eaglefin on a cron. This is the fallback.

Check current Caddy cert storage on both DMZ nodes:
```bash
ssh owlfin "ls -la ~/.local/share/caddy/certificates/"
ssh eaglefin "ls -la ~/.local/share/caddy/certificates/"
```

If both have valid certs with different expiry dates, Option A is already working. If only one has certs, we need Option B.

**For Option B** — add to owlfin crontab:
```bash
0 7 * * * rsync -az ~/.local/share/caddy/certificates/ eaglefin:~/.local/share/caddy/certificates/ && ssh eaglefin "sudo systemctl reload caddy"
```

## Verification

1. Run cert_shepherd.py manually — should show all domains OK with days remaining
2. Verify state file written to `/ganuda/state/cert_shepherd.json`
3. Check Fire Guard health page — cert section should appear
4. Test alerting: temporarily set WARNING_DAYS=365 and run — should trigger a warning alert
5. Verify timer: `systemctl status cert-shepherd.timer`
6. Check both DMZ nodes have valid certs: `echo | openssl s_client -connect ganuda.us:443 2>/dev/null | openssl x509 -noout -dates`

---

FOR SEVEN GENERATIONS
