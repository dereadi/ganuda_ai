# Jr Atomic: LMC-7 — Cert Shepherd TLS sync owlfin → eaglefin

**Parent Long Man cycle:** LMC-7 (duyuktv #2085)
**Council audits:** Longhouse bc1de267de3dc86d (original blessing) + `348952186d1ac1ec` (Apr 21 top-5 ratification)
**SP:** 3
**Long Man phase:** adapt

## Task

Build a systemd-timer-driven "Cert Shepherd" that syncs Let's Encrypt certs from owlfin (ACME master) to eaglefin. This removes silent cert-drift risk across the DMZ.

## Context

- **ACME master:** owlfin. All Let's Encrypt renewals happen there.
- **Replica:** eaglefin. Currently has NO automated cert refresh → certs drift → HTTPS breaks when certs approach expiry.
- **eaglefin reachability confirmed** via WireGuard 10.100.0.5 (handshake <1 min ago as of Apr 21 2026). TCP:22 open. No blocker from #2086 network recovery.
- Longhouse-blessed design: `bc1de267de3dc86d` (pull from thermal or longhouse_sessions if you need the original rationale).

## Design

**Shepherd = systemd timer + shell script on owlfin.** Rsync pulls every 6 hours + on ACME renewal hook.

### File 1: `/usr/local/bin/cert-shepherd.sh` (on owlfin, NOT bluefin — TPM handles cross-node deploy; your job is to write the files + instructions)

```bash
#!/usr/bin/env bash
# Cert Shepherd — syncs /etc/letsencrypt from owlfin to eaglefin.
# Idempotent; safe to re-run on timer + post-renewal hook.
set -euo pipefail

SOURCE=/etc/letsencrypt/
TARGET_HOST=eaglefin
TARGET_PATH=/etc/letsencrypt/
LOG=/var/log/cert-shepherd.log
TS="$(date -Iseconds)"

echo "[$TS] cert-shepherd: starting sync owlfin → ${TARGET_HOST}" >> "$LOG"

rsync -azL --delete \
  --rsync-path="sudo rsync" \
  -e "ssh -o BatchMode=yes -o StrictHostKeyChecking=accept-new" \
  "$SOURCE" \
  "${TARGET_HOST}:${TARGET_PATH}" 2>&1 | tee -a "$LOG"

# Trigger cert-reload on target (nginx, caddy, or whatever the target uses)
ssh -o BatchMode=yes "$TARGET_HOST" 'sudo systemctl reload nginx || sudo systemctl reload caddy || true' 2>&1 | tee -a "$LOG"

echo "[$TS] cert-shepherd: sync complete" >> "$LOG"
```

### File 2: `/etc/systemd/system/cert-shepherd.service`

```ini
[Unit]
Description=Cert Shepherd — sync LE certs from owlfin (ACME master) to replicas
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
ExecStart=/usr/local/bin/cert-shepherd.sh
StandardOutput=append:/var/log/cert-shepherd.log
StandardError=append:/var/log/cert-shepherd.log
```

### File 3: `/etc/systemd/system/cert-shepherd.timer`

```ini
[Unit]
Description=Cert Shepherd timer — 6h interval + 5m post-boot
Requires=cert-shepherd.service

[Timer]
OnBootSec=5min
OnUnitActiveSec=6h
Persistent=true

[Install]
WantedBy=timers.target
```

### File 4: ACME hook — `/etc/letsencrypt/renewal-hooks/deploy/10-cert-shepherd.sh`

```bash
#!/usr/bin/env bash
# Fire cert-shepherd immediately after a successful ACME renewal.
# certbot sets RENEWED_LINEAGE and RENEWED_DOMAINS env vars.
systemctl start cert-shepherd.service
```
Make it executable (`chmod +x`).

### File 5: SSH key + sudoers entry documentation (install.md)

**Prereqs** (document in `/ganuda/docs/install/cert-shepherd-setup.md`):
- Generate SSH keypair on owlfin (`/root/.ssh/cert_shepherd_ed25519` — owned root:root mode 600)
- Deploy public key to `~root/.ssh/authorized_keys` on eaglefin with `command="rsync ..."` forced-command restriction (prevents abuse of the key)
- Sudoers on eaglefin: add `root ALL=(root) NOPASSWD: /usr/bin/rsync --server*, /bin/systemctl reload nginx, /bin/systemctl reload caddy` in `/etc/sudoers.d/cert-shepherd`
- Force-command pattern: `command="rsync --server --daemon ."` (restrict to rsync only — do NOT give the key shell access)

## Verification

```bash
# Dry-run the shepherd script (on owlfin):
sudo bash -n /usr/local/bin/cert-shepherd.sh   # syntax check
sudo systemctl daemon-reload
sudo systemctl start cert-shepherd.service
sudo journalctl -u cert-shepherd.service --no-pager | tail -20

# Verify cert landed on eaglefin (from owlfin):
ssh eaglefin 'sudo ls -la /etc/letsencrypt/live/'

# Verify timer scheduled:
sudo systemctl list-timers cert-shepherd.timer
```

## Done criteria

- [ ] All 5 files created (script + service + timer + ACME hook + setup doc)
- [ ] `systemd daemon-reload` + `cert-shepherd.timer enable/start` works without errors
- [ ] Manual run of cert-shepherd.service succeeds (cert files land on eaglefin)
- [ ] `systemctl list-timers` shows next fire in <6h
- [ ] Setup doc captures SSH key + sudoers steps for operator reproduction

## Non-goals

- Do NOT roll our own ACME — use existing certbot on owlfin
- Do NOT deploy to bluefin or redfin (only eaglefin per original scope; others can be added via config extension later)
- Do NOT embed private keys in the repo
- Do NOT give the shepherd SSH key shell access (force-command only)

Report: files written (paths), dry-run output, timer-list output.
