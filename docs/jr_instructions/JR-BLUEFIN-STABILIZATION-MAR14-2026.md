# JR INSTRUCTION: Bluefin Stabilization — pg_hba + SSH + Index Cleanup + Resource Isolation

**Task**: Fix bluefin's chronic intermittent connectivity failures. Three root causes identified: missing pg_hba.conf rules for WireGuard, SSH proxy misconfiguration, and GPU/ML workload resource contention starving system services.
**Priority**: P1
**Date**: 2026-03-14
**TPM**: Claude Opus
**Story Points**: 5
**Council Vote**: Pending (TPM Easy Button — infrastructure stability)
**Depends On**: None
**Node**: bluefin (192.168.132.222 / 10.100.0.2 / 100.112.254.96)

## Problem Statement

Bluefin PostgreSQL connectivity has been intermittently failing for weeks:
- SSH over LAN (192.168.132.222) hangs during banner exchange — "Connection timed out during banner exchange" with spurious port 65535 redirect
- PostgreSQL rejects WireGuard connections — `FATAL: no pg_hba.conf entry for host "10.100.0.1"`
- Tailscale auth method mismatch — rule requires scram-sha-256 but .pgpass stores md5
- GPU workloads (3x VLM on 8090/8091/8092 + YOLO) likely cause OOM/fork failures for new SSH sessions
- bgwriter has written zero dirty buffers — all I/O flushing happens at checkpoint, causing spikes
- thermal_memory_archive: 174 MB data, 1,781 MB indexes (10:1 ratio), 6 unused indexes

## Fix A: pg_hba.conf — WireGuard + Auth Reconciliation

**File**: `/etc/postgresql/17/main/pg_hba.conf` on bluefin

1. **Add WireGuard subnet rule** (before the LAN catch-all):
   ```
   # WireGuard mesh — all federation nodes
   host    all    claude     10.100.0.0/24    md5
   host    all    dereadi    10.100.0.0/24    md5
   ```

2. **Fix Tailscale auth method** — find the existing rule for `100.0.0.0/8` (line ~41) and change `scram-sha-256` to `md5` to match .pgpass:
   ```
   host    all    claude    100.0.0.0/8    md5
   ```
   OR re-set the `claude` user password with scram-sha-256: `ALTER USER claude PASSWORD 'xxx';` (preferred if moving to scram cluster-wide)

3. **Reload** (not restart):
   ```bash
   sudo systemctl reload postgresql
   ```

4. **Verify** from redfin:
   ```bash
   psql -h 10.100.0.2 -U claude -d zammad_production -c "SELECT 1"
   psql -h 100.112.254.96 -U claude -d zammad_production -c "SELECT 1"
   ```

## Fix B: SSH Config Cleanup

**File**: `~/.ssh/config` on redfin (192.168.132.223)

1. Check for any `Host` block matching `192.168.132.222` or `bluefin` that has a `ProxyCommand` or `ProxyJump` directive. The diagnostic showed a spurious "port 65535" redirect — this is an SSH config issue, not a network issue.

2. Either fix or remove the proxy rule. Direct LAN SSH should not go through a proxy:
   ```
   Host bluefin-lan
       HostName 192.168.132.222
       User dereadi
       ProxyCommand none
   ```

3. **Verify**: `ssh -o ConnectTimeout=5 dereadi@192.168.132.222 echo "ok"`

## Fix C: Index Cleanup on thermal_memory_archive

**Database**: zammad_production on bluefin

1. **Identify unused indexes** (zero scans since stats reset Feb 13):
   ```sql
   SELECT indexrelname, idx_scan, pg_size_pretty(pg_relation_size(indexrelid)) as size
   FROM pg_stat_user_indexes
   WHERE relname = 'thermal_memory_archive' AND idx_scan = 0
   ORDER BY pg_relation_size(indexrelid) DESC;
   ```

2. **Drop unused indexes** using `DROP INDEX CONCURRENTLY` (non-blocking):
   ```sql
   -- For each unused index from the query above:
   DROP INDEX CONCURRENTLY IF EXISTS <index_name>;
   ```

3. **Also check other tables** for unused indexes > 1MB:
   ```sql
   SELECT schemaname, relname, indexrelname, idx_scan,
          pg_size_pretty(pg_relation_size(indexrelid)) as size
   FROM pg_stat_user_indexes
   WHERE idx_scan = 0 AND pg_relation_size(indexrelid) > 1048576
   ORDER BY pg_relation_size(indexrelid) DESC;
   ```
   Drop those too (CONCURRENTLY).

4. **REINDEX the HNSW index** after cleanup:
   ```sql
   REINDEX INDEX CONCURRENTLY idx_thermal_memory_archive_embedding;
   ```
   (Find the actual HNSW index name first with `\di+ thermal_memory_archive`)

5. **Verify**: Total index size should drop significantly. Re-run:
   ```sql
   SELECT pg_size_pretty(pg_total_relation_size('thermal_memory_archive')) as total,
          pg_size_pretty(pg_relation_size('thermal_memory_archive')) as data,
          pg_size_pretty(pg_indexes_size('thermal_memory_archive')) as indexes;
   ```

## Fix D: Resource Isolation — cgroup Limits on VLM Services

**Goal**: Prevent GPU/ML workloads from starving SSH and PostgreSQL.

1. **Check current memory usage** on bluefin:
   ```bash
   free -h
   ps aux --sort=-%mem | head -20
   ```

2. **Add MemoryMax to VLM systemd units** — find the service files for the VLM services (ports 8090/8091/8092) and YOLO:
   ```bash
   systemctl list-units --type=service | grep -i -E "vlm|yolo|vllm|optic"
   ```

   For each service, create an override:
   ```bash
   sudo systemctl edit <service-name>
   ```
   Add:
   ```ini
   [Service]
   MemoryMax=24G
   MemoryHigh=20G
   OOMPolicy=stop
   ```
   Adjust the limit based on available RAM minus what PostgreSQL and SSH need (at least 4GB reserved for system).

3. **Tune bgwriter** in `/etc/postgresql/17/main/postgresql.conf`:
   ```
   bgwriter_lru_maxpages = 200    # default 100, write more per round
   bgwriter_delay = 50ms          # default 200ms, wake up more often
   bgwriter_lru_multiplier = 4.0  # default 2.0, write ahead of demand
   ```
   Then: `sudo systemctl reload postgresql`

4. **Add TCP keepalives** to `/etc/postgresql/17/main/postgresql.conf`:
   ```
   tcp_keepalives_idle = 60
   tcp_keepalives_interval = 10
   tcp_keepalives_count = 5
   ```

5. **Add SSH keepalives** to `/etc/ssh/sshd_config` on bluefin:
   ```
   ClientAliveInterval 30
   ClientAliveCountMax 3
   ```
   Then: `sudo systemctl reload sshd`

6. **Check for OOM kills** (diagnostic, inform results):
   ```bash
   dmesg | grep -i oom
   journalctl -u ssh --since "1 week ago" | grep -i -E "error|refused|timeout"
   ```

## Fix E: Kerberos Credential Renewal

**Node**: bluefin

SSSD logs from Mar 13 show "Password has expired" and "Preauthentication failed" from krb5_child. This can cause intermittent auth delays.

1. **Check keytab status**:
   ```bash
   sudo klist -k /etc/krb5.keytab
   sudo kinit -k host/bluefin.cherokee.local@CHEROKEE.LOCAL
   ```

2. **If expired, renew**:
   ```bash
   sudo ipa-getkeytab -s silverfin.cherokee.local -p host/bluefin.cherokee.local@CHEROKEE.LOCAL -k /etc/krb5.keytab
   ```

3. **Restart SSSD** after keytab renewal:
   ```bash
   sudo systemctl restart sssd
   ```

4. **Verify**: `sudo sssctl domain-status ganuda.local` should show Online.

## Fix F: FreeIPA Sudo Rule — Add journalctl

**Node**: silverfin (via greenfin)

The `ganuda-service-management` sudo rule in FreeIPA does not include `journalctl`. The cluster cannot self-diagnose SSSD, SSH, or PostgreSQL issues without Partner intervention.

1. **Add to FreeIPA** (from any enrolled node):
   ```bash
   ipa sudocmd-add /usr/bin/journalctl
   ipa sudorule-add-allow-command ganuda-service-management --sudocmds=/usr/bin/journalctl
   ```

2. **Verify** from bluefin:
   ```bash
   sudo journalctl -u sssd --since "1 hour ago" --no-pager | tail -5
   ```

## Fix G: Apply ProxyCommand Fix to All Nodes

**Nodes**: ALL Linux nodes (redfin done, apply to bluefin, greenfin, owlfin, eaglefin)

The FreeIPA client installs `/etc/ssh/ssh_config.d/04-ipa.conf` with a deprecated `sss_ssh_knownhostsproxy` ProxyCommand that hangs when the proxy binary misbehaves. Comment it out on all nodes.

1. **On each node**:
   ```bash
   sudo cp /etc/ssh/ssh_config.d/04-ipa.conf /etc/ssh/ssh_config.d/04-ipa.conf.bak.20260314
   sudo sed -i 's/^\(\s*ProxyCommand.*sss_ssh_knownhostsproxy\)/#\1/' /etc/ssh/ssh_config.d/04-ipa.conf
   ```

2. **Verify** the `GlobalKnownHostsFile` and `PubkeyAuthentication` lines remain active.

## DO NOT

- Restart PostgreSQL unless absolutely necessary — reload is sufficient for config changes
- Drop indexes without confirming zero scans first — stats were reset Feb 13, so a month of data
- Kill running VLM services during business hours — add cgroup limits and let them take effect on next restart
- Change pg_hba.conf rules for the `postgres` superuser without testing
- Modify shared_buffers (requires restart) — save that for a maintenance window

## Acceptance Criteria

- [ ] `psql -h 10.100.0.2 -U claude -d zammad_production -c "SELECT 1"` succeeds (WireGuard)
- [ ] `psql -h 100.112.254.96 -U claude -d zammad_production -c "SELECT 1"` succeeds (Tailscale)
- [ ] SSH to bluefin LAN IP no longer hangs (proxy config fixed)
- [ ] Unused indexes dropped — thermal_memory_archive index size < 1.5 GB
- [ ] VLM services have MemoryMax cgroup limits in systemd
- [ ] TCP keepalives configured in postgresql.conf
- [ ] bgwriter_lru_maxpages > 100 (actually flushing dirty pages)
- [ ] `dmesg | grep -i oom` results documented (even if clean)
