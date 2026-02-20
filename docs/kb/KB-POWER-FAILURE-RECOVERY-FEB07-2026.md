# KB: Power Failure Recovery - February 7, 2026

**Created:** 2026-02-07
**Author:** TPM (Claude Opus 4.6)
**Category:** Incident Recovery / Infrastructure

## Incident Summary

Catastrophic power failure took down the Cherokee AI Federation. All nodes came back up but several services required manual intervention.

## Impact Assessment

| Service | Status After Power-On | Recovery Action |
|---------|----------------------|-----------------|
| VetAssist (redfin) | Backend crash-looping (2,823 restarts) | .env password fix + code revert |
| Caddy (redfin) | Failed to start | default_bind fix for Tailscale coexistence |
| Camera tunnel (greenfin) | iptables/nft rules lost | Re-applied manually |
| Bluefin PostgreSQL | UP | No action needed |
| Bluefin NVIDIA/Ollama | UP, RTX 5070 healthy | No action needed |
| SAG UI (redfin) | UP | No action needed |

## Root Causes and Fixes

### 1. VetAssist Backend Crash Loop

**Root cause:** Credential rotation on Feb 6 changed the DB password from `jawaseatlasers2` to the rotated password, but the `.env` file on the VetAssist backend still had the old password. Additionally, Jr code changes from Feb 6 had broken imports in `calculator.py`.

**Fixes applied:**
- Updated `/ganuda/vetassist/backend/.env` DATABASE_URL with new password
- Reverted `calculator.py` to committed version (`git checkout HEAD -- backend/app/api/v1/endpoints/calculator.py`) — Jr refactoring had introduced broken relative imports (`from ...models.user import User` → resolves to nonexistent `app.api.models.user`)
- Added `sys.path.insert(0, "/ganuda")` in `council_chat.py` so `specialist_council.py` can find `secrets_loader`
- Removed extraneous DB_HOST/PORT/NAME/USER/PASSWORD fields from `.env` (Pydantic Settings model doesn't define them)

**Lesson:** After credential rotation, verify ALL .env files are updated. The secrets_loader migration should replace .env files entirely. Track this as a follow-up.

### 2. Caddy Port 443 Conflict with Tailscale Serve

**Root cause:** Tailscale Serve binds to `100.116.27.89:443`. Caddy defaults to `0.0.0.0:443`, causing a conflict.

**Fix:** Added `{ default_bind 192.168.132.223 }` to top of `/etc/caddy/Caddyfile` so Caddy only binds the LAN IP.

**Lesson:** Document this in Ansible playbooks. Any node running both Caddy and Tailscale Serve needs `default_bind` configured.

### 3. Greenfin Camera Tunnel (Non-Persistent)

**Root cause:** iptables DNAT rules and nft forward rules are in-memory only. Power cycle cleared them.

**Fix:** Re-applied iptables DNAT (greenfin:10554→camera:554, greenfin:18080→camera:80) and nft forward rule (`iifname "eno1" oifname "wlp195s0" ip daddr 10.0.0.123`).

**Lesson:** ALWAYS persist firewall rules immediately after testing:
```bash
sudo nft list ruleset | sudo tee /etc/nftables.conf > /dev/null
sudo iptables-save | sudo tee /etc/iptables/rules.v4 > /dev/null
```
This MUST be in the Ansible playbook for greenfin.

### 4. Browser ERR_UNSAFE_PORT on 10080

Chrome blocks port 10080 as "unsafe" (HTTP alternate). Changed HTTP tunnel to port 18080 instead.

**Lesson:** Avoid ports in Chrome's unsafe list: 10080, 6000, 6566, 6665-6669, etc. Use 18080+ for tunneled HTTP.

## Key Findings During Recovery

1. **Bluefin RTX 5070 healthy:** Driver 580.126.09, CUDA 13.0 working. Previous driver failure (Task 628) appears resolved.
2. **Ollama consuming 8GB VRAM on bluefin** running Mistral 7B with no active consumers. Queued migration to vLLM (Task #640).
3. **Garage camera already had fleet password** (`jawaseatlasers2`), not default admin/admin as expected. Serial: AMC1086CA4E221E066.
4. **nftables vs iptables on greenfin:** Greenfin uses nftables with iptables-nft backend. The `inet filter forward` chain has policy DROP. Rules added via iptables go into `ip filter FORWARD` (policy ACCEPT) but `inet filter forward` evaluates first and drops. Must add nft rules directly.

## Tasks Queued

| Task # | ID | Title | Assigned |
|--------|-----|-------|----------|
| 640 | VLM-VLLM-001 | Migrate VLM to vLLM on bluefin | Infrastructure Jr. |
| 641 | SAG-GARAGE-CAM-001 | Add garage camera to SAG | Software Engineer Jr. |

## Follow-Up Actions

- [ ] Persist greenfin firewall rules (requires sudo)
- [ ] Rotate camera fleet passwords (all 3 on jawaseatlasers2)
- [ ] Update vault secret (amcrest_camera_password currently tribal_vision_2026, cameras actually use jawaseatlasers2)
- [ ] Add greenfin firewall config to Ansible playbook
- [ ] Add Caddy default_bind to Ansible playbook for redfin
- [ ] Clean up VetAssist git repo (unstaged Jr changes need review/commit)

---
**FOR SEVEN GENERATIONS** - Document failures so future generations learn.
