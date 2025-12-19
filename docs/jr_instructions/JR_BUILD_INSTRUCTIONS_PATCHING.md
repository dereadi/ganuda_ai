# Jr Build Instructions: Federation Patching Procedure

**Priority**: MEDIUM (Routine) / HIGH (Security CVEs)  
**Assigned To**: IT Triad Jr  
**Date**: December 13, 2025

## Patching Schedule

| Patch Type | Frequency | Window | Approval |
|------------|-----------|--------|----------|
| Critical CVEs | ASAP (24-48h) | Any | TPM approval |
| Security (High) | Weekly | Sunday 2-4 AM | TPM approval |
| Regular updates | Monthly | 1st Sunday 2-4 AM | TPM approval |
| Major upgrades | Quarterly | Scheduled | Council vote |

## Patch Order (Rolling Deployment)

**Always patch in this order with 24h between tiers:**

```
1. greenfin (canary)     ─── test 24h ───►
2. sasass/sasass2 (dev)  ─── test 24h ───►  
3. redfin (GPU/Gateway)  ─── verify ───►
4. bluefin (Database)    ─── LAST, backup first!
```

## Playbook Location

`/ganuda/home/dereadi/ansible/playbooks/`

- `patch_nodes.yml` - Apply patches (no auto-reboot)
- `reboot_node.yml` - Manual reboot when approved

## Usage

### Patch Single Node (Canary)
```bash
cd /ganuda/home/dereadi/ansible
ansible-playbook -i inventory_federation.ini playbooks/patch_nodes.yml --limit greenfin -K
```

### Patch Dev Nodes
```bash
ansible-playbook -i inventory_federation.ini playbooks/patch_nodes.yml --limit federation_macos -K
```

### Patch Production (GPU)
```bash
ansible-playbook -i inventory_federation.ini playbooks/patch_nodes.yml --limit redfin -K
```

### Patch Database (LAST - Backup First!)
```bash
ansible-playbook -i inventory_federation.ini playbooks/patch_nodes.yml --limit bluefin -K
```

### Dry Run (Check Only)
```bash
ansible-playbook -i inventory_federation.ini playbooks/patch_nodes.yml --limit greenfin -K --check
```

## Reboot Procedure

**Only when TPM approves and no active work:**

```bash
# Check if reboot needed
ssh dereadi@<node> "cat /var/run/reboot-required 2>/dev/null && echo 'REBOOT NEEDED' || echo 'No reboot needed'"

# When approved, use playbook:
ansible-playbook -i inventory_federation.ini playbooks/reboot_node.yml --limit <hostname> -K

# OR manual:
ssh dereadi@<node> "sudo reboot"
```

## Pre-Patch Checklist

- [ ] No active development/builds in progress
- [ ] TPM approval obtained
- [ ] Previous tier tested for 24h (if rolling)
- [ ] Backup verified (bluefin)
- [ ] Maintenance window communicated

## Post-Patch Verification

```bash
# Check services
ssh dereadi@<node> "systemctl status llm-gateway"  # redfin
ssh dereadi@<node> "systemctl status postgresql"   # bluefin

# Health check
ssh dereadi@<node> "/ganuda/scripts/health_check.sh"

# Gateway health (redfin)
curl -s http://192.168.132.223:8080/health | jq .
```

## Rollback

If patches cause issues:

```bash
# Check apt history
ssh dereadi@<node> "cat /var/log/apt/history.log | tail -50"

# Downgrade specific package
ssh dereadi@<node> "sudo apt install <package>=<previous-version>"
```

## Emergency Contacts

- TPM: dereadi (approval required for all reboots)
- Council: Use /v1/council/vote for major upgrade decisions

---

FOR SEVEN GENERATIONS - Stable systems protect future operations.
