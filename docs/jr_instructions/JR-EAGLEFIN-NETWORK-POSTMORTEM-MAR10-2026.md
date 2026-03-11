# JR INSTRUCTION: Eaglefin Network Recovery Post-Mortem

**Task**: Document the eaglefin network outage during IP Passthrough migration on Mar 10 2026
**Priority**: P2
**Date**: 2026-03-10
**TPM**: Claude Opus
**Story Points**: 3

## Problem Statement

During the AT&T BGW320 IP Passthrough activation on March 10, 2026, eaglefin (keepalived BACKUP DMZ node) went completely dark across all three network planes. It required a physical reboot to recover, and even after recovery, Caddy could not renew TLS certs. This post-mortem documents what happened, why, and what we would do differently.

## What You're Documenting

Build a post-mortem report covering the full incident. Gather evidence from system logs, network state, and federation telemetry.

## Investigation Steps

### 1. Gather Timeline Evidence

On eaglefin (192.168.132.84 or 10.100.0.6), check:

```bash
# System boot time — confirms when physical reboot happened
who -b
uptime -s

# Journal logs around the incident window
journalctl --since "2026-03-10 00:00" --until "2026-03-10 23:59" -p err

# Network interface state changes
journalctl -u NetworkManager --since "2026-03-10 00:00"
# or if using networkd:
journalctl -u systemd-networkd --since "2026-03-10 00:00"

# Keepalived state transitions
journalctl -u keepalived --since "2026-03-10 00:00"

# WireGuard interface state
journalctl -u wg-quick@wg0 --since "2026-03-10 00:00"

# Caddy logs — cert renewal failures
journalctl -u caddy --since "2026-03-10 00:00"
```

On owlfin (10.100.0.5), check:
```bash
# Keepalived — did it detect eaglefin going down? Did it promote itself?
journalctl -u keepalived --since "2026-03-10 00:00"
```

On redfin (local), check:
```bash
# Fire Guard alerts — did it detect eaglefin going dark?
journalctl -u fire-guard --since "2026-03-10 00:00"

# Thermal memory for any incident-related entries
# (query thermal_memory_archive for entries from Mar 10 with 'eaglefin' in content)
```

### 2. Root Cause Analysis

The known facts:
- AT&T BGW320 was reconfigured to IP Passthrough mode (DHCPS-fixed, MAC 94:83:c4:33:54:7f for Aircove)
- This changes the network topology — the Aircove gets a public IP directly instead of being double-NATted
- Eaglefin went dark on ALL planes: mgmt LAN (192.168.132.84), DMZ (192.168.30.3), WireGuard (10.100.0.6)
- Complete darkness on all 3 planes suggests a layer-2 or physical-layer issue, not just routing

Investigate:
- Did the BGW320 reconfiguration cause a full network reset that bounced all switch ports?
- Did eaglefin's network interfaces fail to come back up after the topology change?
- Was DHCP disrupted (eaglefin may use DHCP for its mgmt interface)?
- Did the DMZ interface lose its static config?
- Could the WireGuard tunnel have been disrupted by a gateway change?

### 3. Recovery Actions Taken

Document what was done to recover:
- Physical reboot of eaglefin (who did it, when, how long was it down)
- What services came back automatically via systemd?
- What had to be manually restarted?
- The TLS cert renewal failure after reboot (Caddy ACME tls-alpn-01 challenge on BACKUP node)
- External port verification (ports 80/443 confirmed open after passthrough activated)

### 4. Impact Assessment

- How long was eaglefin down?
- Did any traffic hit eaglefin during the outage? (It is the BACKUP, so probably no user impact unless owlfin also had issues)
- Were any keepalived failovers triggered?
- Did Fire Guard detect and alert on the outage?
- Were any Jr tasks affected?

### 5. Lessons Learned and Recommendations

Document:
- **Fire Guard maintenance windows**: If we had a "maintenance mode" for Fire Guard, we could suppress alerts during planned network changes.
- **Static IPs on all interfaces**: If DHCP disruption caused the outage, static configs are more resilient.
- **WireGuard resilience**: Does wg-quick@wg0 auto-recover after a network interface bounce? If not, should we add a systemd dependency or a health check?
- **Cert sync**: Cross-reference with JR-CERT-SHEPHERD-MAR10-2026.md — the cert renewal failure is the same problem that task addresses.
- **Physical access dependency**: A node that requires physical reboot to recover is a single point of failure. What remote recovery options exist? (IPMI, iDRAC, smart power strip)

## Output Format

Write the post-mortem to: `/ganuda/docs/postmortems/PM-EAGLEFIN-PASSTHROUGH-MAR10-2026.md`

Use this structure:

```markdown
# Post-Mortem: Eaglefin Network Outage — March 10, 2026

## Summary
[2-3 sentences: what happened, how long, user impact]

## Timeline
| Time (CT) | Event |
|-----------|-------|
| HH:MM | BGW320 IP Passthrough configured |
| HH:MM | Eaglefin goes dark on all planes |
| ... | ... |

## Root Cause
[Explanation of why it happened]

## Impact
- Duration: X hours
- User-facing impact: [none/partial/full]
- Services affected: [list]

## Recovery Actions
[What was done to recover, in order]

## What Went Well
[Things that worked — keepalived failover, Fire Guard detection, etc.]

## What Went Poorly
[Things that failed or were missing]

## Action Items
| Action | Owner | Priority | Status |
|--------|-------|----------|--------|
| ... | ... | ... | ... |

## Related
- JR-CERT-SHEPHERD-MAR10-2026.md — cert sync solution
- Fire Guard maintenance window proposal
```

## Target Files

- `/ganuda/docs/postmortems/PM-EAGLEFIN-PASSTHROUGH-MAR10-2026.md` — the post-mortem report (CREATE)

## Constraints

- Document facts, not speculation. If you cannot determine something from logs, say "unable to determine from available logs"
- Do NOT make any configuration changes — this is documentation only
- Do NOT restart any services as part of the investigation
- Include actual log excerpts (sanitized of any credentials) as evidence
- Timestamps must be in CT (America/Chicago)

## Files to Read Before Starting

- `/ganuda/docs/jr_instructions/JR-CERT-SHEPHERD-MAR10-2026.md` — related cert sync task
- `/ganuda/scripts/fire_guard.py` — understand what Fire Guard monitors
- `/ganuda/services/power_monitor/solix_monitor_daemon.py` — example of node health monitoring
- `/ganuda/config/wireguard/wg0-eaglefin.conf` — WireGuard config for eaglefin

## Acceptance Criteria

- Post-mortem exists at `/ganuda/docs/postmortems/PM-EAGLEFIN-PASSTHROUGH-MAR10-2026.md`
- Timeline includes timestamps from actual logs where available
- Root cause is identified or clearly stated as "under investigation" with evidence gathered so far
- At least 3 actionable recommendations are included
- Report cross-references the Cert Shepherd task
- No services were restarted or configs changed during investigation

## DO NOT

- Make any configuration changes
- Restart any services
- Include raw credentials in log excerpts
- Speculate without marking it as speculation
- Skip log gathering — the evidence matters more than the narrative
