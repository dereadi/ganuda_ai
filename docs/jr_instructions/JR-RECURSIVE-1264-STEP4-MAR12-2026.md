# [RECURSIVE] Cert Shepherd — Sync TLS Certs Between DMZ Nodes - Step 4

**Parent Task**: #1264
**Auto-decomposed**: 2026-03-12T18:03:09.478512
**Original Step Title**: Create cron job on owlfin

---

### Step 4: Create cron job on owlfin

```bash
# /etc/cron.d/cert-shepherd
0 * * * * root /bin/bash /ganuda/scripts/cert_shepherd.sh >> /var/log/cert-shepherd.log 2>&1
```
