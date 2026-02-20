# KB: Power Outage #4 Recovery — Feb 13, 2026

**Thermal Memory**: #88104+
**Severity**: P1 — Infrastructure Down
**Affected Nodes**: bluefin (primary), all nodes (cross-connectivity)
**Data Loss**: None — 80,654 thermal memories verified intact
**Resolution Time**: ~45 minutes

## Summary

Fourth power outage of 2026. No Solix UPS alert received because daemon relied solely on MQTT (which delivers empty payloads for F3800P). Bluefin locked up on reboot due to Docker/nftables conflict. Full recovery achieved with Supabase container cleanup, PG17 restart, and nftables reapplication.

## Timeline

| Time | Event |
|------|-------|
| Overnight | Power outage occurs — no alert received |
| ~08:00 | TPM discovers outage during morning check |
| 08:12 | PG17 startup attempt fails: SSL key permission denied |
| ~08:30 | Supabase Docker containers churning (10 containers, auth unhealthy) |
| ~08:35 | nftables + Docker conflict causes SSH/PG unreachable from other nodes |
| ~08:40 | Bluefin locks up — forced reboot |
| ~08:50 | Flush nftables, kill all Supabase containers |
| ~09:00 | PG17 started, nftables reapplied, cross-node connectivity verified |

## Root Causes

### 1. No Power Alert (Gap in Solix Monitoring)
- Solix daemon relied on MQTT for real-time data
- MQTT delivers **empty payloads** for F3800P model (Anker library decoder limitation)
- `get_device_pv_status` REST API endpoint was not being polled
- **Fix**: Added PV STATUS polling every 5th cycle (~10min) + `check_power_state()` function with Telegram alerts

### 2. Docker/nftables Conflict on Bluefin
- Supabase Docker containers (from old `image_search` project) auto-started on boot
- Docker inserts its own iptables/nft rules that conflict with our nftables default DROP policy
- Result: SSH and PG became unreachable from other nodes
- **Fix**: Killed all Supabase containers, pruned images (25.66GB reclaimed)

### 3. PG17 SSL Certificate Permission
- Recurring issue since Feb 11: `/etc/ssl/private/ssl-cert-snakeoil.key` Permission denied
- PG17 service runs as `postgres` user, which lacks access to `/etc/ssl/private/`
- `pg_ctlcluster 17 main start` works because it runs as postgres directly via pg_wrapper
- **Fix needed**: Either add `postgres` to `ssl-cert` group, or configure PG to use a cert in an accessible location

### 4. Resource Starvation
- 10 Docker containers churning (auth unhealthy, storage/realtime restarting in loop)
- Combined with nftables blocking = no external management access
- Resulted in complete lockup requiring hard reboot

## Recovery Commands (on bluefin)

```text
# 1. Flush restrictive firewall
sudo nft flush ruleset

# 2. Kill all Supabase containers
sudo docker stop $(sudo docker ps -aq)
sudo docker rm $(sudo docker ps -aq)
sudo docker system prune -a    # Reclaimed 25.66GB

# 3. Start PostgreSQL
sudo pg_ctlcluster 17 main start

# 4. Reapply correct nftables
sudo nft -f /etc/nftables.conf

# 5. Verify
psql -h 192.168.132.222 -U claude -d zammad_production -c "SELECT count(*) FROM thermal_memory_archive;"
# → 80,654 (all data intact)
```

## Prevention Measures

1. **Solix PV STATUS polling** — now active, will alert via Telegram on power > 50W discharge
2. **Docker disabled on bluefin** — no containers needed for current config
3. **nftables boot order** — need to ensure nftables loads AFTER Docker is disabled/removed
4. **PG17 SSL fix** — add postgres to ssl-cert group (needs sudo)

## Related KBs

- [KB-POWER-FAILURE-RECOVERY-FEB07-2026.md](KB-POWER-FAILURE-RECOVERY-FEB07-2026.md) — Outage #1
- [KB-BLUEFIN-OLLAMA-REMOVAL-VLLM-MIGRATION-FEB11-2026.md](KB-BLUEFIN-OLLAMA-REMOVAL-VLLM-MIGRATION-FEB11-2026.md) — Outage #2 context
- [KB-SOLIX-3800-MONITORING-API-DISCOVERY-FEB11-2026.md](KB-SOLIX-3800-MONITORING-API-DISCOVERY-FEB11-2026.md) — Solix API details
- [KB-GREENFIN-NFTABLES-XTABLES-COMPAT-FIX-FEB11-2026.md](KB-GREENFIN-NFTABLES-XTABLES-COMPAT-FIX-FEB11-2026.md) — nftables deployment

## Checklist for Next Outage

- [ ] Check Telegram for Solix discharge alert
- [ ] If no alert: check `journalctl -u solix-monitor` on greenfin
- [ ] On bluefin: `sudo nft flush ruleset` FIRST before anything else
- [ ] Kill any Docker containers before reapplying nftables
- [ ] Start PG: `sudo pg_ctlcluster 17 main start`
- [ ] Verify cross-node: `psql -h 192.168.132.222` from redfin/greenfin
