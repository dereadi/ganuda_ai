# [RECURSIVE] Cert Shepherd — Sync TLS Certs Between DMZ Nodes - Step 5

**Parent Task**: #1264
**Auto-decomposed**: 2026-03-12T18:03:09.479508
**Original Step Title**: Verify

---

### Step 5: Verify

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
