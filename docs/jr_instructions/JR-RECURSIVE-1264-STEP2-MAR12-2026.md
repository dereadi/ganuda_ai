# [RECURSIVE] Cert Shepherd — Sync TLS Certs Between DMZ Nodes - Step 2

**Parent Task**: #1264
**Auto-decomposed**: 2026-03-12T18:03:09.476664
**Original Step Title**: Set up SSH key for rsync (owlfin to eaglefin)

---

### Step 2: Set up SSH key for rsync (owlfin to eaglefin)

On owlfin, generate a dedicated key pair for cert sync (if not already available):
```bash
sudo -u caddy ssh-keygen -t ed25519 -f /var/lib/caddy/.ssh/id_cert_sync -N "" -C "cert-sync-owlfin"
```

Add the public key to eaglefin's authorized_keys for the caddy user (or root if caddy can't SSH). Restrict the key to rsync only using `command=` in authorized_keys for least privilege.
