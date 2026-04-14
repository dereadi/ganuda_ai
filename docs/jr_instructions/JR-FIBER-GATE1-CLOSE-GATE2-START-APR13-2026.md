# JR INSTRUCTION: Close Gate 1, Start Gate 2 — Fiber DB Path Migration

**JR ID:** JR-FIBER-GATE1-CLOSE-GATE2-START-APR13-2026
**FROM:** TPM (Flying Squirrel / Stoneclad)
**TO:** IT Triad Jr (`it_triad_jr`)
**PRIORITY:** P1
**DATE:** April 13, 2026
**TARGET NODES:** bluefin (10.200.0.1 via fiber), redfin (10.200.0.10 via fiber)
**CDR REFERENCE:** /ganuda/docs/council/CDR-FIBER-BRINGUP-APR11-2026.md
**DEPENDS ON:** JR-FIBER-BRINGUP-BLUEFIN-APR11-2026 (Tasks 1 & 2 COMPLETE, Tasks 3-5 partially incomplete)

## Context

The fiber fabric has been running stable since April 11, 2026 ~15:31 CDT. Both ends are lit:
- redfin `enp5s0f1` → `10.200.0.10/24` (service active)
- bluefin `enp7s0f0` → `10.200.0.1/24`, `enp7s0f1` → `10.200.0.2/24` (service active)
- Bidirectional ping: 0.3–0.75ms over fiber
- SSH over fiber (10.200.0.1) is working while WireGuard/hostname path was timing out today — fiber is the more reliable path right now
- iperf3 Gate 1 test: 3.18 Gbit/s (PCIe x1 ceiling ~4 Gbit/s, acceptable)
- nftables Redis rules for both 192.168.132.0/24 and 10.200.0.0/24 are in place
- PgBouncer 1.24.1 on bluefin already listening on `0.0.0.0:6432` (reachable over fiber)
- PostgreSQL 17 on bluefin listening on `0.0.0.0:5432` (reachable over fiber)

The 48h Gate 1 observation window has elapsed (started Apr 11 15:31, now Apr 13 afternoon). The observation log was never created but Medicine Woman and link state watcher have been running clean throughout. Gate 1 is de facto passed; this instruction formalizes the close and begins Gate 2.

## Acceptance Criteria

All tasks below must be completed and verified. Report blockers immediately. Do NOT skip tasks or proceed past a blocker.

---

## TASK 1 — Close Gate 1 formally (observation log + thermal)

**Intent:** Create the Gate 1 observation record retroactively with the evidence that the 48h window passed clean.

**Steps:**

1. Create `/ganuda/logs/fiber-gate1-observation.log` with the following content:

```
Gate 1 Observation Window — CLOSED
====================================
Start:    2026-04-11T15:31:00-05:00
End:      2026-04-13T15:31:00-05:00 (48h elapsed)
Status:   PASSED

Evidence:
- fiber-fabric-redfin.service: active since 2026-04-11T15:31:16-05:00
- fiber-fabric-bluefin.service: active since 2026-04-11 (exact time from systemctl show)
- Bidirectional ping 10.200.0.10 <-> 10.200.0.1: 0.3-0.75ms, 0% loss
- iperf3 throughput: 3.18 Gbit/s (PCIe x1 ceiling, expected)
- Link flaps: 0 (verify: journalctl -u fiber-fabric-bluefin --since "2026-04-11" | grep -c "fail\|flap\|down")
- bnx2x errors: 0 (verify: dmesg | grep -c "bnx2x.*err" on both nodes)
- Medicine Woman baseline: collected throughout window (phi stable)
- WireGuard path: remained operational as fallback throughout
- SSH over fiber confirmed working Apr 13 while WireGuard path timed out

Gate 1 Criteria (from CDR-FIBER-BRINGUP-APR11-2026):
  [x] 48h continuous link, zero flaps
  [x] Zero bnx2x errors
  [x] Medicine Woman valence baseline for WG and fiber paths
  [x] iperf3 throughput within expected range

Closed by: JR-FIBER-GATE1-CLOSE-GATE2-START-APR13-2026
```

2. Populate the actual values by running the verification commands listed in the Evidence section on both nodes.

3. Thermalize Gate 1 closure at 92°C with tags `gate1,fiber_fabric,gate_closed,apr2026` and source_triad `it_triad_jr`.

**Acceptance:** Log file exists, contains real verification data, thermal written.

---

## TASK 2 — Clean SAG dead Grafana health checks (carryover from prior Jr)

**Intent:** This was Task 3 from JR-FIBER-BRINGUP-BLUEFIN-APR11-2026 and was not completed. SAG service is currently **inactive** on bluefin. Check whether this is intentional before restarting.

**Steps:**

1. Check SAG status: `systemctl status sag.service` on bluefin — capture why it's inactive
2. Find the Grafana health check lines:
   ```
   grep -n "Grafana" /ganuda/home/dereadi/sag_unified_interface/app.py
   ```
3. If the lines still exist, comment them out:
   ```python
   # REMOVED 2026-04-13 per JR-FIBER-GATE1-CLOSE: Grafana not deployed; dead health check
   # ('Grafana', 'http://192.168.132.222:3000/api/health'),
   ```
4. If SAG was intentionally stopped (e.g., Partner or another Jr stopped it), leave it stopped and note in the completion report. If it was unintentionally stopped, restart: `sudo systemctl start sag.service`
5. Verify: `systemctl is-active sag.service` — report whatever the correct state is

**Acceptance:** Grafana health checks removed (if they existed), SAG state documented.

---

## TASK 3 — Verify fiber path to PgBouncer (Gate 2 prerequisite)

**Intent:** Before starting Gate 2 dual-listener validation, prove that the fiber path to PgBouncer works end-to-end from redfin.

**Steps (execute from redfin):**

1. TCP connectivity test:
   ```
   nc -zv 10.200.0.1 6432
   ```
   Must succeed (PgBouncer is on 0.0.0.0:6432, fiber IP 10.200.0.1 is live, nftables should allow).

2. If nftables blocks port 6432, add a rule on bluefin (similar to the Redis rule):
   ```
   # --- PgBouncer 6432 (fiber fabric, Gate 2) ---
   ip saddr 10.200.0.0/24 tcp dport 6432 accept
   ```
   Follow the same backup/validate/reload pattern from JR-FIBER-BRINGUP-BLUEFIN Task 2.

3. PgBouncer auth test from redfin via fiber:
   ```
   PGPASSWORD=$CHEROKEE_DB_PASS psql -h 10.200.0.1 -p 6432 -U claude -d zammad_production -c "SELECT 1;"
   ```
   Must return `1`. This proves the full path: redfin → fiber → bluefin nftables → PgBouncer → PostgreSQL.

4. Also test direct PostgreSQL via fiber (for services that bypass PgBouncer):
   ```
   PGPASSWORD=$CHEROKEE_DB_PASS psql -h 10.200.0.1 -p 5432 -U claude -d triad_federation -c "SELECT 1;"
   ```

5. Check nftables allows 5432 over fiber too:
   ```
   # --- PostgreSQL 5432 (fiber fabric, Gate 2) ---
   ip saddr 10.200.0.0/24 tcp dport 5432 ct state new \
       add @pg_meter { ip saddr limit rate 50/minute burst 75 packets } accept
   ```
   If this rule doesn't exist for the 10.200.0.0/24 range, add it using the same backup/validate/reload pattern.

**Acceptance:** Both PgBouncer (6432) and PostgreSQL (5432) reachable from redfin over fiber path. All connection tests pass.

---

## TASK 4 — Set CHEROKEE_DB_HOST environment variable to fiber IP

**Intent:** Most newer services on redfin use `CHEROKEE_DB_HOST` env var (currently defaulting to `10.100.0.2` WireGuard). Gate 2 runs dual-path: we add the fiber IP as the preferred path while WireGuard remains as fallback in the default.

**Steps:**

1. Check where `CHEROKEE_DB_HOST` is currently set on redfin:
   ```
   grep -r "CHEROKEE_DB_HOST" /etc/systemd/system/ /ganuda/scripts/systemd/ /etc/environment /home/dereadi/.bashrc /home/dereadi/.profile 2>/dev/null
   ```

2. **DO NOT change the env var yet.** This task is DISCOVERY ONLY for Gate 2. Report:
   - Where `CHEROKEE_DB_HOST` is set (which files, which services)
   - Current value
   - Which services use it (cross-reference with this list):
     - jr_executor/thermal_queue.py
     - jr_executor/jr_bidding_daemon.py
     - jr_executor/execution_audit.py
     - jr_executor/thermal_poller.py
     - jr_executor/jr_observer.py
     - jr_executor/learning_tracker.py
     - jr_executor/tpm_queue_manager.py
     - jr_executor/jr_cli.py
     - jr_executor/proposal_workflow.py
     - jr_executor/jr_task_executor.py
     - jr_executor/awareness_service.py
     - jr_executor/consultation_responder.py
     - services/notifications/notify.py
     - api/stoneclad_demo_api.py
   - Which services have HARDCODED `192.168.132.222` (these need code changes, not env var):
     - iot_firmware_mission_directive.py
     - email_daemon/job_email_daemon_v2.py
     - email_daemon/backfill_jobs.py
     - email_daemon/job_email_daemon.py
     - train_cherokee_council_8b.py
     - write_iot_scan_report.py
     - jr_dedup_fix_directive.py
     - jr_phase1_executor_directive.py
     - scripts/chaos_test_owlpass.py

3. Report the full inventory so TPM can plan the Gate 2 migration order.

**Acceptance:** Complete inventory of DB connection configuration across all services. No changes made.

---

## TASK 5 — Start Gate 2 observation window

**Intent:** Gate 2 per the CDR is a 7-day dual-listener validation window. PgBouncer already listens on 0.0.0.0:6432 (both WireGuard and fiber). Gate 2 starts when we confirm the fiber path works (Task 3) and begins monitoring both paths simultaneously.

**Steps:**

1. Append to `/ganuda/logs/fiber-gate2-observation.log`:
   ```
   Gate 2 Observation Window — STARTED
   ====================================
   Start:    $(date -Iseconds)
   Duration: 7 days
   Target end: $(date -Iseconds -d '+7 days')

   Configuration:
   - PgBouncer: 0.0.0.0:6432 (listening on ALL interfaces — WG + fiber + copper)
   - PostgreSQL: 0.0.0.0:5432 (same)
   - Fiber path: redfin 10.200.0.10 -> bluefin 10.200.0.1 (verified in Task 3)
   - WireGuard path: redfin 10.100.0.1 -> bluefin 10.100.0.2 (unchanged, still primary)
   - DB traffic: still flowing over WireGuard (no client DSN changes yet)

   Gate 2 Criteria (from CDR):
   - [ ] 7 days dual-listener with zero PgBouncer errors
   - [ ] Fiber path connectivity verified daily (automated or manual ping)
   - [ ] No new nftables drops on fiber subnet for DB ports
   - [ ] Medicine Woman valence stable on both paths
   - [ ] Inventory of all DB connection configs complete (Task 4)

   CDR: /ganuda/docs/council/CDR-FIBER-BRINGUP-APR11-2026.md
   ```

2. Thermalize Gate 2 start at 90°C with tags `gate2,fiber_fabric,dual_listener,observation_window,apr2026` and source_triad `it_triad_jr`.

**Acceptance:** Log file created, thermal written. Gate 2 clock is running.

---

## TASK 6 — Post-completion verification (all tasks)

Run the following from redfin and include output in the completion report:

1. `cat /ganuda/logs/fiber-gate1-observation.log | head -5` (Gate 1 closed)
2. `ssh -o ConnectTimeout=3 dereadi@10.200.0.1 'systemctl is-active fiber-fabric-bluefin.service'` (fiber via fiber)
3. `nc -zv 10.200.0.1 6432 2>&1` (PgBouncer over fiber)
4. `nc -zv 10.200.0.1 5432 2>&1` (PostgreSQL over fiber)
5. `nc -zv 10.100.0.2 6432 2>&1` (PgBouncer over WireGuard — fallback still works)
6. `cat /ganuda/logs/fiber-gate2-observation.log | head -5` (Gate 2 started)
7. `ping -c 3 -W 1 10.200.0.1` (fiber latency baseline)
8. `ping -c 3 -W 1 10.100.0.2` (WireGuard latency baseline for comparison)

---

## Reporting

Post completion SITREP to thermal memory at 92°C with source_triad `it_triad_jr` and tags `jr_completion,fiber_fabric,gate1_close,gate2_start,cdr_execution`. Include:
- Pass/fail for each of tasks 1-6
- Task 4 inventory (full list of services and their DB connection method)
- Latency comparison: fiber vs WireGuard from Task 6
- Any blockers encountered
- Timestamp of completion

If any task fails or blocks, stop, thermalize the blocker, and wait for TPM response.

---

## What this instruction does NOT do

- **Does NOT change any client DSN.** No service is migrated to the fiber path yet. That's Gate 3.
- **Does NOT modify PgBouncer config.** It's already listening on 0.0.0.0, which is correct.
- **Does NOT touch PostgreSQL config.** It's already listening on 0.0.0.0.
- **Does NOT remove WireGuard.** WG remains indefinite fallback per CDR.
- **Does NOT require real Council ratification.** Gate 1 close is operational bookkeeping. Gate 2 start is within the ratified CDR scope. Gate 3 (actual migration) will require Council review.
