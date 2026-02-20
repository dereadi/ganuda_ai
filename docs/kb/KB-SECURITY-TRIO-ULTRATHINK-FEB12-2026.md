# KB: Security Trio Ultrathink — Tailscale ACL, Firewall, MVT

**Date**: February 12, 2026
**Kanban**: #546 (SF=95), #547 (SF=85), #549 (SF=95)
**Jr Tasks**: #710, #711, #712
**River Cycle**: RC-2026-02A

## Key Discovery

Phase 1 security work from **November 2025** created comprehensive tooling that was marked "READY FOR APPROVAL" but **NEVER DEPLOYED**. Three months of exposure.

## What Already Exists (Nov 2025)

| Component | Location | Status |
|-----------|----------|--------|
| Tailscale ACL policy (3-zone) | `/ganuda/home/dereadi/security_jr/spoke_security_phase1/tailscale_acl_policy.json` | Ready, not applied |
| nftables config (redfin) | `/ganuda/config/nftables-redfin.conf` | Ready, not persisted |
| nftables config (bluefin) | `/ganuda/config/nftables-bluefin.conf` | Ready, not persisted |
| fail2ban configs | `/ganuda/config/fail2ban-*.conf` | Ready, not deployed |
| MVT venv + Pegasus IOCs | `/ganuda/home/dereadi/security_jr/spoke_security_phase1/` | Ready, redfin-only scan |
| Redfin Pegasus scan | Phase 1 results | VERIFIED CLEAN |
| Firewall deploy scripts | `/ganuda/home/dereadi/security_jr/spoke_security_phase1/spoke_firewall_rules.sh` | Ready |
| Ansible playbook (greenfin) | `/ganuda/ansible/playbooks/greenfin-firewall.yml` | Ready |

## What Phase 2 Adds (Feb 12, Jr Tasks #710-#712)

### #710 — Tailscale ACL Validation (Infrastructure Jr.)
- `tailscale_acl_audit.py`: Validates ACL JSON against live mesh state
- `tailscale_zone_test.py`: Tests connectivity patterns to assess zone placement
- Does NOT deploy ACLs (Chief does via Tailscale admin console)

### #711 — Firewall Audit & Deploy Helper (Infrastructure Jr.)
- `firewall_audit.py`: Checks nftables service, ruleset, persistence, fail2ban, xtables compat
- `firewall_deploy_helper.py`: Generates exact sudo commands per node with rollback instructions
- Does NOT apply rules (Chief runs generated commands)

### #712 — MVT Fleet Scanner (Software Engineer Jr.)
- `mvt_fleet_scanner.py`: 5-check scan (processes, network, crons, SSH keys, persistence)
- `ioc_updater.py`: Downloads latest Pegasus IOCs from Amnesty International
- Stores results in security_health_checks DB table

## Deployment Sequence (Chief Runs)

1. **Run audit scripts** on each node to assess current state
2. **Deploy Tailscale ACLs** via admin console (using validated policy JSON)
3. **Deploy nftables** per node using firewall_deploy_helper.py output (keep 2nd SSH open!)
4. **Deploy fail2ban** alongside nftables
5. **Run MVT fleet scan** on bluefin and greenfin (redfin already clean)
6. **Update IOCs** to current Amnesty database
7. **Verify** with zone test + firewall audit + fleet scan

## Critical Lessons

1. **Persistence is everything**: Firewall rules lost on BOTH power outages (Feb 7, Feb 11). Must persist to `/etc/nftables.conf`.
2. **xtables compat breaks reloads**: Tailscale generates xtables compat expressions. Fix: replace `xt target "MASQUERADE"` with native `masquerade`. See KB-GREENFIN-NFTABLES-XTABLES-COMPAT-FIX.
3. **Keep 2nd SSH session open**: During firewall changes, always have a fallback shell.
4. **Executor can't create .service/.conf**: Jr instructions limited to .py/.sh/.md files. Config deployment is Chief work.
5. **"Ready for approval" ≠ deployed**: Three months of drift between creation and deployment means re-validation is essential.

## Three-Zone Tailscale Architecture

```
QUARANTINE (Red)  → Hub-only access (new/suspicious spokes → redfin only)
LIMITED (Yellow)   → Hub + SSH/HTTPS to bluefin, greenfin
TRUSTED (Green)    → Full mesh access (redfin, bluefin, greenfin, bmasass)
```

## Related

- KB-POWER-FAILURE-RECOVERY-FEB07-2026 (firewall rules lost)
- KB-GREENFIN-NFTABLES-XTABLES-COMPAT-FIX-FEB11-2026 (xtables issue)
- KB-ISOLATED-VLAN-TAILSCALE-VIA-SQUID-JAN15-2026 (VLAN architecture)
- `/ganuda/home/dereadi/security_jr/spoke_security_phase1/PHASE1_IMPLEMENTATION_SUMMARY.md`
