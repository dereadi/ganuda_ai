# [RECURSIVE] Cert Shepherd — Sync TLS Certs Between DMZ Nodes - Step 1

**Parent Task**: #1264
**Auto-decomposed**: 2026-03-12T18:03:09.470033
**Original Step Title**: Identify Caddy cert storage path

---

### Step 1: Identify Caddy cert storage path

SSH to owlfin and find the cert storage:
```bash
sudo find /var/lib/caddy -type f -name "*.crt" -o -name "*.key" 2>/dev/null
# Also check:
sudo find /root/.local/share/caddy -type f 2>/dev/null
# Caddy 2.x default: $XDG_DATA_HOME/caddy or /var/lib/caddy/.local/share/caddy
```
