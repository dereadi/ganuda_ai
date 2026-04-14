# JR INSTRUCTION: Fiber Fabric Bluefin-Side Bring-Up + D6 Fixes

**JR ID:** JR-FIBER-BRINGUP-BLUEFIN-APR11-2026
**FROM:** TPM (Flying Squirrel / Stoneclad)
**TO:** IT Triad Jr
**PRIORITY:** P1
**DATE:** April 11, 2026
**TARGET NODE:** bluefin (192.168.132.222)
**CDR REFERENCE:** /ganuda/docs/council/CDR-FIBER-BRINGUP-APR11-2026.md (RATIFIED)

## Context

Council ratified the fiber fabric CDR this afternoon. Redfin-side Gate 1 is already done (enp5s0f1 → 10.200.0.10/24 via `fiber-fabric-redfin.service`). This instruction completes the bluefin side of Gate 1 plus two D6 cleanup items the Council ratified for same-session execution.

TPM cannot directly execute these tasks on bluefin because the NOPASSWD sudo scope on bluefin is restricted to PostgreSQL `pg_hba.conf` management. Jr executor has broader access and is the right tool.

## Acceptance Criteria

All five tasks below must be completed and verified. Report blockers immediately.

---

## TASK 1 — Fiber fabric IP assignment on bluefin (Gate 1)

**Intent:** Assign fiber fabric IPs to both bluefin SFP+ ports, persistent across reboot, matching the redfin-side pattern.

**Address plan (from ratified CDR):**
- `enp7s0f0` → `10.200.0.1/24`
- `enp7s0f1` → `10.200.0.2/24`

**Method:** Deploy a systemd oneshot unit via `ganuda-deploy-service`.

**Steps:**
1. Write the service file to `/ganuda/scripts/systemd/fiber-fabric-bluefin.service` with the following content:

```ini
[Unit]
Description=Fiber Fabric IP Assignment (bluefin enp7s0f0/f1 -> 10.200.0.1,2/24)
Documentation=/ganuda/docs/council/CDR-FIBER-BRINGUP-APR11-2026.md
After=network-online.target
Wants=network-online.target
After=NetworkManager.service

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/usr/sbin/ip link set enp7s0f0 up
ExecStart=/usr/sbin/ip link set enp7s0f1 up
ExecStart=/bin/sh -c 'ip addr show enp7s0f0 | grep -q "10.200.0.1/24" || ip addr add 10.200.0.1/24 dev enp7s0f0'
ExecStart=/bin/sh -c 'ip addr show enp7s0f1 | grep -q "10.200.0.2/24" || ip addr add 10.200.0.2/24 dev enp7s0f1'
ExecStop=/bin/sh -c 'ip addr del 10.200.0.1/24 dev enp7s0f0 2>/dev/null || true'
ExecStop=/bin/sh -c 'ip addr del 10.200.0.2/24 dev enp7s0f1 2>/dev/null || true'

[Install]
WantedBy=multi-user.target
```

2. Deploy: `sudo ganuda-deploy-service fiber-fabric-bluefin`
3. Verify: `systemctl is-active fiber-fabric-bluefin.service` returns `active`
4. Verify: `ip -br addr show enp7s0f0` shows `10.200.0.1/24`
5. Verify: `ip -br addr show enp7s0f1` shows `10.200.0.2/24`
6. Test: `ping -c 3 10.200.0.10` (redfin's fiber IP) from bluefin — must succeed with low latency

**Acceptance:** Both IPs up, ping to redfin succeeds, service is enabled and persistent.

---

## TASK 2 — Add Redis nftables rule on bluefin (D6 fix)

**Intent:** Allow `192.168.132.0/24 → tcp 6379` on bluefin's firewall so `cherokee-email-executor.service` on redfin can legitimately reach bluefin's Redis. Redis is running (`redis-server.service`), the drop is a missing firewall rule.

**Current state of `/etc/nftables.conf` on bluefin (excerpt around the section that needs the addition):**
```
        # --- PostgreSQL 5432 (internal only, rate limited) ---
        ip saddr 192.168.132.0/24 tcp dport 5432 ct state new \
            add @pg_meter { ip saddr limit rate 50/minute burst 75 packets } accept
        ip saddr 192.168.132.0/24 tcp dport 5432 ct state new \
            log prefix "[nft-pg-ratelimit] " drop
```

**Add the following BEFORE the `# --- Log and drop everything else ---` line, under the existing allow rules:**
```
        # --- Redis 6379 (internal only, for cherokee-email-executor and federated Redis clients) ---
        ip saddr 192.168.132.0/24 tcp dport 6379 accept
        # --- Redis 6379 (fiber fabric, post-Gate-1) ---
        ip saddr 10.200.0.0/24 tcp dport 6379 accept
```

**Steps:**
1. Back up current `/etc/nftables.conf` to `/etc/nftables.conf.bak.$(date +%Y%m%d-%H%M%S)` via `sudo cp`
2. Edit `/etc/nftables.conf` to add the two rules above
3. Validate syntax: `sudo nft -c -f /etc/nftables.conf` — must return no errors
4. Reload: `sudo systemctl reload nftables.service`
5. Verify: `sudo nft list ruleset | grep -A 1 6379` shows the rule
6. Test from redfin: `nc -zv 192.168.132.222 6379` (Redis port connectivity) — must succeed
7. Check: redfin's `ss -tn state syn-sent | grep 6379` — should be empty (cherokee-email-executor now connecting successfully)

**Acceptance:** Redis port reachable from redfin, firewall config persisted, no dropped SYNs to 6379 in bluefin dmesg for 5 minutes after the change.

---

## TASK 3 — Clean SAG dead Grafana health checks (D6 fix)

**Intent:** SAG's `app.py` has stale Grafana health checks pointing to `192.168.132.222:3000` (bluefin). Grafana is not running anywhere in the cluster (verified: no `:3000` listener on bluefin, no grafana-server service, `next-server` is on redfin:3000 and is Kanban not Grafana). The health checks generate silent dropped SYNs every few seconds. Either remove them or point them at the actual Grafana location.

**Lines to fix in `/ganuda/home/dereadi/sag_unified_interface/app.py`:**
- Line 2006: `('Grafana', 'http://192.168.132.222:3000/api/health'),`
- Line 2126: `("http://192.168.132.222:3000/api/health", "Grafana"),`

**Recommended action:** Comment out both lines with a note referencing this Jr instruction:
```python
        # REMOVED 2026-04-11 per JR-FIBER-BRINGUP-BLUEFIN: Grafana not deployed; dead health check
        # ('Grafana', 'http://192.168.132.222:3000/api/health'),
```

**Steps:**
1. Edit `/ganuda/home/dereadi/sag_unified_interface/app.py` at lines 2006 and 2126
2. Comment out each line with the removal note
3. Restart SAG: `sudo systemctl restart sag.service`
4. Verify: `systemctl is-active sag.service` returns `active`
5. Check after 60 seconds: `ss -tn state syn-sent | grep ":3000"` — should be empty (no more failed SYNs to bluefin:3000)
6. Verify dmesg on bluefin for 2 minutes after: zero new `[nft-input-drop]` for port 3000 from 192.168.132.223

**Acceptance:** SAG running, no dropped SYNs to port 3000, SAG health dashboard still functional (test: `curl http://192.168.132.223:4000/health`).

**Note:** If Grafana is needed in the future, add it back with the correct URL. Do NOT point it at a non-existent service.

---

## TASK 4 — Start 48h observation window (Gate 1 validation)

**Intent:** Gate 1 per the ratified CDR requires 48h of observation with zero link flaps, zero bnx2x errors, Medicine Woman valence baseline captured for both WG and fiber paths.

**Steps:**
1. Append to `/ganuda/logs/fiber-gate1-observation.log`:
   ```
   Gate 1 observation window started: $(date -Iseconds)
   Duration: 48h
   Target end: $(date -Iseconds -d '+48 hours')
   Redfin IP: 10.200.0.10/24 on enp5s0f1
   Bluefin IPs: 10.200.0.1/24 (f0), 10.200.0.2/24 (f1)
   CDR: /ganuda/docs/council/CDR-FIBER-BRINGUP-APR11-2026.md
   ```

2. Thermalize the start of Gate 1 observation at 90°C with tags `gate1,fiber_fabric,observation_window,apr2026`

3. No further action on the 48h window — it runs passively. TPM will monitor link state watcher and Medicine Woman baseline independently.

**Acceptance:** Log entry written, thermal memory entry created, no further blocking.

---

## TASK 5 — Post-deployment verification (all tasks)

Run the following and include output in the completion report:

1. `systemctl is-active fiber-fabric-bluefin.service` (expect: `active`)
2. `ip -br addr show enp7s0f0 enp7s0f1` (expect: both with 10.200.0.x/24)
3. `ping -c 5 -W 1 10.200.0.10` (expect: 0% loss, <1ms latency — fiber path between nodes)
4. `sudo nft list ruleset | grep -c 6379` (expect: >= 1)
5. `ss -tn state syn-sent | grep -E ':6379|:3000' | wc -l` (expect: 0)
6. `systemctl is-active sag.service redis-server.service` (expect: both `active`)
7. Last 2 minutes of bluefin dmesg: `journalctl -k --since '2 minutes ago' | grep -c nft-input-drop` (expect: 0 or small baseline, not climbing)

---

## Reporting

Post completion SITREP to thermal memory at 92°C with source_triad `it_triad_jr` and tags `jr_completion,fiber_fabric,cdr_execution`. Include:
- Pass/fail for each of tasks 1-5
- Any blockers encountered
- Output of verification commands
- Timestamp of completion

If any task fails or blocks, DO NOT proceed to later tasks unconditionally. Stop, thermalize the blocker, and wait for TPM response. The Council's ratification is non-negotiable but the Gates are designed to catch problems early.

---

## CDR Gates this instruction addresses

- **Gate 1 — Pre-Stage (48h observation)**: Tasks 1 + 4 start this
- **D6 — nftables cleanup**: Tasks 2 + 3 complete the ratified D6 work
- **Gate 2**: NOT addressed here. Begins after 48h observation completes and all Gate 1 criteria are met.
