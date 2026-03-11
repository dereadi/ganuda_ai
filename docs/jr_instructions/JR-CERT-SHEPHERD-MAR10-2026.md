# JR INSTRUCTION: Cert Shepherd — Sync TLS Certs Between DMZ Nodes

**Task**: Ensure both DMZ nodes have valid TLS certificates for all ganuda.us domains
**Priority**: P1 — production TLS is broken on failover
**Date**: 2026-03-10
**TPM**: Claude Opus
**Council Vote**: Longhouse blessed, #bc1de267de3dc86d

## Problem Statement

Caddy on owlfin and eaglefin serves TLS for ganuda.us, vetassist.ganuda.us, and www.ganuda.us. Caddy uses tls-alpn-01 ACME challenges by default, which require the node to hold the VIP (192.168.30.10) on port 443. Only the keepalived MASTER holds the VIP, so only it can complete ACME challenges. The BACKUP node's certs expire and are never renewed, meaning a failover results in TLS errors for all visitors.

This was exposed during the eaglefin network outage on Mar 10 2026 — after reboot, eaglefin's Caddy could not renew certs because it was the BACKUP node.

## Network Context

- **owlfin**: 192.168.132.170 (mgmt LAN) / 192.168.30.2 (DMZ) / 10.100.0.5 (WireGuard)
  - keepalived MASTER (normally)
- **eaglefin**: 192.168.132.84 (mgmt LAN) / 192.168.30.3 (DMZ) / 10.100.0.6 (WireGuard)
  - keepalived BACKUP (normally)
- **VIP**: 192.168.30.10 — shared DMZ IP for incoming web traffic
- **Domains**: ganuda.us, www.ganuda.us, vetassist.ganuda.us

## Approach Options (Evaluate and Pick Best)

You must evaluate all three options and document your reasoning before implementing. Pick the one with the best reliability-to-complexity ratio.

### Option A: rsync Caddy cert storage via cron over WireGuard

- Set up a cron job (every 1 hour) on owlfin that rsyncs Caddy's cert/key storage to eaglefin
- Caddy stores certs at `/var/lib/caddy/.local/share/caddy/` (verify actual path with `find /var/lib/caddy -name "*.crt" -o -name "*.key" 2>/dev/null` or check Caddy docs)
- Use rsync over SSH via WireGuard IPs (10.100.0.5 -> 10.100.0.6) for encrypted transit
- After rsync, reload Caddy on eaglefin: `systemctl reload caddy`
- Pros: Simple, no external dependencies
- Cons: Up to 1 hour of stale certs after renewal, requires SSH key setup between nodes

### Option B: Shared Caddy storage backend

- Configure both Caddy instances to use the same storage backend (e.g., consul, S3-compatible like MinIO)
- Caddy supports `storage` directive in the global options block
- Pros: Real-time cert sharing, no cron
- Cons: Adds infrastructure dependency (another service to maintain), overkill for 2 nodes

### Option C: Switch ACME challenge to HTTP-01

- Change Caddy config to use HTTP-01 challenges instead of tls-alpn-01
- HTTP-01 challenges serve a token on port 80 — this may work through keepalived VIP to whichever node is active
- Pros: Both nodes could potentially renew their own certs when they become MASTER
- Cons: Still only works for the active MASTER; doesn't solve BACKUP renewal. Also requires port 80 to be open and unblocked.

### TPM Recommendation

Option A (rsync) is the pragmatic choice. It's simple, uses infrastructure we already have (WireGuard, SSH, cron), and covers the failure mode. Document why you picked what you picked.

## Steps (for Option A — adapt if you pick differently)

### 1. Identify Caddy cert storage path

SSH to owlfin and find the cert storage:
```bash
sudo find /var/lib/caddy -type f -name "*.crt" -o -name "*.key" 2>/dev/null
# Also check:
sudo find /root/.local/share/caddy -type f 2>/dev/null
# Caddy 2.x default: $XDG_DATA_HOME/caddy or /var/lib/caddy/.local/share/caddy
```

### 2. Set up SSH key for rsync (owlfin -> eaglefin)

On owlfin, generate a dedicated key pair for cert sync (if not already available):
```bash
sudo -u caddy ssh-keygen -t ed25519 -f /var/lib/caddy/.ssh/id_cert_sync -N "" -C "cert-sync-owlfin"
```

Add the public key to eaglefin's authorized_keys for the caddy user (or root if caddy can't SSH). Restrict the key to rsync only using `command=` in authorized_keys for least privilege.

### 3. Create the sync script

Create `/ganuda/scripts/cert_shepherd.sh`:
```bash
#!/bin/bash
# Cert Shepherd — sync Caddy TLS certs from owlfin to eaglefin
# Runs on owlfin only (the usual MASTER)

set -euo pipefail

CADDY_DATA="/var/lib/caddy/.local/share/caddy"  # Verify actual path
REMOTE_HOST="10.100.0.6"  # eaglefin WireGuard IP
REMOTE_USER="root"  # or caddy if SSH access exists
SSH_KEY="/var/lib/caddy/.ssh/id_cert_sync"
LOG_TAG="cert-shepherd"

logger -t "$LOG_TAG" "Starting cert sync to eaglefin"

rsync -az --delete \
  -e "ssh -i $SSH_KEY -o StrictHostKeyChecking=no -o ConnectTimeout=10" \
  "$CADDY_DATA/" \
  "${REMOTE_USER}@${REMOTE_HOST}:${CADDY_DATA}/"

if [ $? -eq 0 ]; then
  # Reload Caddy on eaglefin to pick up new certs
  ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no -o ConnectTimeout=10 \
    "${REMOTE_USER}@${REMOTE_HOST}" "systemctl reload caddy"
  logger -t "$LOG_TAG" "Cert sync complete, Caddy reloaded on eaglefin"
else
  logger -t "$LOG_TAG" "ERROR: rsync failed"
  exit 1
fi
```

### 4. Create cron job on owlfin

```bash
# /etc/cron.d/cert-shepherd
0 * * * * root /bin/bash /ganuda/scripts/cert_shepherd.sh >> /var/log/cert-shepherd.log 2>&1
```

### 5. Verify

From an external machine (or redfin):
```bash
# Point directly at eaglefin DMZ IP and check cert
curl -v --resolve ganuda.us:443:192.168.30.3 https://ganuda.us 2>&1 | grep "expire date"

# Point at owlfin
curl -v --resolve ganuda.us:443:192.168.30.2 https://ganuda.us 2>&1 | grep "expire date"

# Both should show expiry >30 days out
```

## Target Files

- `/ganuda/scripts/cert_shepherd.sh` — sync script (CREATE)
- Cron job on owlfin: `/etc/cron.d/cert-shepherd` (CREATE, needs sudo)
- SSH key pair on owlfin for cert sync (CREATE, needs sudo)
- authorized_keys on eaglefin for the sync key (MODIFY, needs sudo)

## Constraints

- Cert material MUST be encrypted in transit — use SSH/rsync over WireGuard (10.100.0.x addresses)
- Do NOT break Caddy on either node — test reload before automating
- Do NOT store private keys in the ganuda repo or any DB table
- Do NOT disable TLS or switch to self-signed certs
- Must work with keepalived failover — if roles flip, document what changes
- Use FreeIPA scoped sudo where possible (see MEMORY.md SSH/Remote Access Rules)

## Failure Modes to Consider

1. **Roles flip permanently**: If eaglefin becomes MASTER, it will renew its own certs but owlfin (now BACKUP) goes stale. Consider running the sync bidirectionally or from whichever node is MASTER.
2. **SSH connection fails**: rsync should timeout gracefully (ConnectTimeout=10), log the error, and exit non-zero
3. **Caddy reload fails**: Check exit code of the reload command

## Acceptance Criteria

- Both owlfin and eaglefin serve valid TLS certs for ganuda.us, www.ganuda.us, and vetassist.ganuda.us
- `curl -v https://ganuda.us` succeeds when pointed at either node's DMZ IP
- Cert expiry is >30 days on both nodes
- Sync runs automatically every hour
- Sync uses encrypted transport (WireGuard or SSH)
- Verify with: `bash -n /ganuda/scripts/cert_shepherd.sh` for syntax check

## DO NOT

- Store private keys in git, DB, or any shared location
- Disable TLS or use self-signed certs
- Modify keepalived configuration
- Run rsync over unencrypted channels (no plain LAN rsync without SSH)
- Hardcode passwords — use SSH keys only
