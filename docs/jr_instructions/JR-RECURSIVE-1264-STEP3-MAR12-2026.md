# [RECURSIVE] Cert Shepherd — Sync TLS Certs Between DMZ Nodes - Step 3

**Parent Task**: #1264
**Auto-decomposed**: 2026-03-12T18:03:09.477613
**Original Step Title**: Create the sync script

---

### Step 3: Create the sync script

**File:** `/ganuda/scripts/cert_shepherd.sh`

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
