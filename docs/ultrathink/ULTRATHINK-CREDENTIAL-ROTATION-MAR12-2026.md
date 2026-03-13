# ULTRATHINK: Credential Rotation — CHEROKEE_DB_PASS & jawaseatlasers2

**Date:** March 12, 2026
**Author:** TPM (Stoneclad, Claude Opus 4.6)
**Trigger:** Coyote thermal #124811 — Jr #1277 (sasass2 Thunderduck Zero triage) found two credentials exposed in source files for 18+ days
**Methodology:** Long Man Development — DISCOVER / DELIBERATE / ADAPT / BUILD / RECORD / REVIEW

---

## PHASE 1: DISCOVER — Blast Radius Report

### Credential 1: CHEROKEE_DB_PASS (current password: `TYDo5U2NVkXqQ8DHuhIpvRgLUrXf2iZE`)

**What it protects:** PostgreSQL user `claude` on bluefin (192.168.132.222:5432). Full access to `zammad_production` database (thermal_memory_archive, jr_work_queue, council votes, kanban, VetAssist PII, all federation data).

**Exposure:** Found in 4 Jane Street experiment files on sasass2 (18+ days). Source files scrubbed via `os.environ.get()` pattern, but password NOT rotated on the PostgreSQL server.

**Last rotated:** February 6, 2026 (from `jawaseatlasers2` to current). That rotation caused a 2-day outage (KB-PASSWORD-ROTATION-CASCADE-FEB08-2026).

#### Files with HARDCODED current password (NOT using env var — CRITICAL):

| File | Type | Status |
|------|------|--------|
| `/ganuda/email_daemon/config.json` | JSON config | HARDCODED — `"db_password": "TYDo5U2NVkXqQ8DHuhIpvRgLUrXf2iZE"` |
| `/ganuda/daemons/medicine_woman.py` | Python daemon | HARDCODED — line 90 |
| `/ganuda/lib/partner_rhythm.py` | Python lib | HARDCODED — line 32 |
| Multiple Jr instruction docs | Documentation | Contains password in code examples |

#### Files using `os.environ.get('CHEROKEE_DB_PASS')` correctly (120+ files):

These are safe — they read from environment. After rotation, they just need a service restart. Categories:
- **jr_executor/**: task_executor.py, thermal_queue.py, thermal_poller.py, jr_bidding_daemon.py, tpm_queue_manager.py, jr_cli.py, jr_task_executor.py, awareness_service.py, consultation_responder.py
- **telegram_bot/**: telegram_chief.py, telegram_chief_v3.py, derpatobot_claude.py, status_notifier.py, code_generation_handler.py, task_assigner.py, tribe_memory_search.py, tribe_interface_fix.py
- **scripts/**: fire_guard.py, council_dawn_mist.py (via secrets_loader), generate_status_page.py, stats_keeper.py, owl_debt_reckoning.py, ritual_review.py, body_report.py, backlog_reckoning.py, sla_baseline_metrics.py, deer_linkedin_publish.py, generate_ops_console.py, gpu_power_monitor.py, generate_health_page.py, generate_team_page.py, + 30 more
- **lib/**: ganuda_db/__init__.py, secrets_loader.py, chain_protocol.py, web_ring.py, curiosity_engine.py, partner_rhythm.py (ALSO hardcoded), memory_graph.py, hivemind_tracker.py, council_diversity_check.py, halo_council.py, context_link.py, metacognition/*.py, consciousness_cascade/*.py
- **services/**: chat_agent.py, breathing_api.py, browser_ring_api.py, embedding_server.py, research_worker.py, moltbook_proxy/*.py, web_materializer.py, greenfin_sentinel.py, solix_monitor_daemon.py, + others
- **daemons/**: ganuda_heartbeat_agent.py, integration_jr_autonomic.py, meta_jr_autonomic_phase1.py
- **email_daemon/**: gmail_api_daemon.py, job_email_daemon.py, job_email_daemon_v2.py, backfill_jobs.py
- **Shell scripts**: ganuda_env.sh, pheromone_decay_v2.sh, pheromone_decay_v3.sh, phoenix_backup.sh, backup_postgres.sh, chaos_test_suite.sh, and others (use `$CHEROKEE_DB_PASS` from sourced secrets.env)

#### Systemd services on redfin that load secrets.env (26 services):

council-dawn-mist, derpatobot, elisi-observer, federation-status, fire-guard, ganudabot, gmail-daemon, gpu-power-monitor, ii-researcher, jr-executor, jr-orchestrator, llm-gateway, memory-jr-autonomic, moltbook-proxy, owl-debt-reckoning, research-worker, ritual-review, safety-canary, solix-monitor, speed-detector, stats-keeper, telegram-chief, tribal-vision

Plus service files in repo not yet deployed: sag-v2, greenfin-sentinel, chat_agent, cherokee-embedding-server

#### Nodes with the credential:

| Node | Has secrets.env? | Has hardcoded? | Services? |
|------|------------------|----------------|-----------|
| **redfin** (192.168.132.223) | YES — `/ganuda/config/secrets.env` | YES — config.json, medicine_woman.py, partner_rhythm.py | 26+ systemd services |
| **bluefin** (192.168.132.222) | YES — `/ganuda/config/secrets.env` | Needs verification | PostgreSQL SERVER — role password lives here |
| **greenfin** (192.168.132.224) | YES — `/ganuda/config/secrets.env` | Needs verification | embedding service, greenfin-sentinel |
| **bmasass** (100.103.27.106) | Likely YES | Needs verification | MLX model services |
| **owlfin** (192.168.132.170) | YES — web materializer | Needs verification | web-materializer, Caddy |
| **eaglefin** (192.168.132.84) | YES — web materializer | Needs verification | web-materializer, Caddy |
| **sasass** (192.168.132.241) | YES | Scrubbed by Jr #1277 | Mac fleet |
| **sasass2** (192.168.132.242) | YES | Scrubbed by Jr #1277 | Thunderduck Zero |
| **silverfin** (192.168.10.10) | Via FreeIPA vault | N/A | FreeIPA stores `bluefin_claude_password` in vault |

#### Database roles:

- **`claude`** — Primary application user. This is the one being rotated. Used by ALL federation services.
- **Replication slot `redfin_standby`** — EXISTS but inactive since Mar 6. Uses streaming replication (pg_hba.conf authentication). Needs separate investigation — replication may use a different auth mechanism (trust on localhost, or a replication-specific password).
- **Other roles** — Unknown without querying `pg_roles`. Jr instruction must check.

---

### Credential 2: `jawaseatlasers2` (LEGACY — supposedly rotated Feb 6, 2026)

**What it was:** The ORIGINAL PostgreSQL password for user `claude`. Also used as Amcrest camera fleet password and FreeIPA admin password (per some Jr instructions).

**Current status:** Should be INVALID on PostgreSQL (rotated Feb 6). But:

#### Still present in 100+ files across the codebase:

**Active code files (not just docs):**
- `/ganuda/jr_phase1_executor_directive.py` — lines 111, 178 — HARDCODED in psql commands
- `/ganuda/diagnose_chiefs_cron.sh` — line 78 — HARDCODED
- `/ganuda/scripts/pre-commit-gitleaks.sh` — line 67 — Detection rule (acceptable)
- `/ganuda/.gitleaks.toml` — Detection rule (acceptable)

**Documentation/runbooks with the OLD password in plain text (60+ files):**
- All runbooks: LLM_GATEWAY_DOWN.md, THERMAL_MEMORY_CORRUPTION.md, DB_CONNECTION_EXHAUSTED.md
- README_CHEROKEE_AI.md, BLUEFIN_DEPLOYMENT_INSTRUCTIONS.md, MULTI_NODE_AUTONOMIC_STATUS.md
- 40+ Jr instructions from Jan-Feb 2026
- 10+ KB articles
- Multiple ultrathink documents

**Camera RTSP URLs:** `rtsp://admin:jawaseatlasers2@192.168.132.181` and `192.168.132.182` — in 8 Jr instruction/ultrathink docs. If cameras still use this password, that is a separate rotation needed.

**Key question:** Is `jawaseatlasers2` still valid on PostgreSQL? If the Feb 6 rotation actually changed it, then these are stale references (cosmetic debt, not security risk for DB). But the cameras may still use it.

---

### Credential 3: `cherokee_spoke_2024`

Found in `hub_spoke_sync_client.py` on sasass nodes. Scrubbed by Jr #1277. Lower priority — appears to be a spoke authentication token, not database access.

---

## PHASE 2: DELIBERATE

### TPM Position (Stoneclad)

I recommend **immediate rotation within a 30-minute maintenance window**, scheduled for tonight (Mar 12) or early morning Mar 13. Here is my reasoning:

1. **The password has been in plaintext on sasass2 for 18+ days.** Even though it was scrubbed from source files, anyone with access to those files (or git history on sasass2) has the production database password. This gives full read/write access to thermal memory, council votes, VetAssist PII, and all federation data.

2. **We have a KB and playbook from the Feb 6 rotation.** We learned the hard way (2-day outage). This time we know exactly what to restart and in what order.

3. **The blast radius is manageable.** 120+ files use `os.environ.get()` correctly — they just need `secrets.env` updated and services restarted. Only 3 active code files have the password hardcoded (config.json, medicine_woman.py, partner_rhythm.py) — fix those first, then rotate.

4. **Rolling rotation is NOT worth the complexity.** PostgreSQL only has one password per role. When we change it, every connection using the old password fails. There is no way to have both passwords valid simultaneously without creating a second DB role. A single-step rotation with pre-staged secrets.env files on all nodes is the right approach.

5. **Rollback plan:** If services fail after rotation, revert the PostgreSQL password to the old value (`ALTER ROLE claude WITH PASSWORD 'TYDo5U2NVkXqQ8DHuhIpvRgLUrXf2iZE';`). This takes 5 seconds. Then diagnose and retry.

### Council Voices

**Coyote (ᏩᏯᎯ — Always-On Observer):**
> "Eighteen days. EIGHTEEN DAYS that password sat in plaintext. The Feb 6 rotation was supposed to be the last time we had this conversation. Now we have the SAME password exposed on Mac nodes that Joe has physical access to (sasass2 is Joe's hardware — wait, no, Chief said it's Chief's hardware). Regardless — any human or process that touched those files in the last 18 days has the keys to the kingdom. Rotate NOW, not tonight, not tomorrow. Every hour is another hour of exposure. And while you're at it — why does `email_daemon/config.json` have the password hardcoded? That file was supposed to be cleaned in the Feb 8 sweep. 319 files swept and you missed a JSON config? I want a Crawdad re-audit after rotation."

**Turtle (ᏧᎵᏍᏕᎵᏍᎩ — Careful Keeper):**
> "I hear Coyote's urgency, and I don't disagree on the timeline. But I want to remind everyone: the LAST rotation caused a 2-day silent outage. The Jr executor and orchestrator died without alerting anyone. Before we rotate, I need to see: (1) the new secrets.env pre-staged on every node, (2) the three hardcoded files fixed BEFORE the password changes, (3) a service restart checklist with verification steps for each service, (4) Fire Guard actively monitoring for `password authentication failed` in PostgreSQL logs during the window. We do this once, we do it right."

**Raven (ᎧᎸᎩ — War Chief):**
> "Operational readiness check: Can we reach all 8 nodes right now? sasass and sasass2 are Mac nodes — are they awake? bmasass is mobile (Tailscale). If we can't push secrets.env to all nodes simultaneously, we'll have a split-brain period where some services authenticate and others don't. I want confirmation of SSH connectivity to every node BEFORE we start the rotation clock. Also: the redfin_standby replication slot — is it going to cause WAL bloat if bluefin can't replicate during the window? Check `pg_replication_slots` and drop it if it's inactive."

**Spider (ᎧᎾᏁᏍᎩ — Dependency Web):**
> "The dependency chain is: secrets.env → systemd EnvironmentFile → Python os.environ.get() → psycopg2.connect() → bluefin PostgreSQL. If ANY link breaks, the service dies silently (most use empty string fallback, which means auth failure, not crash). The three hardcoded files (config.json, medicine_woman.py, partner_rhythm.py) bypass the chain entirely — they MUST be fixed first or they'll keep using the old password. Also watch: `ganuda_env.sh` exports `THERMAL_MEMORY_PASS` from `CHEROKEE_DB_PASS` — any script sourcing ganuda_env.sh instead of secrets.env directly will break if the alias chain isn't updated. And `deploy-secrets-silverfin.sh` pushes the password to FreeIPA vault — that needs to run post-rotation too."

**Crawdad (ᏥᏍᏚ — Security/PII):**
> "This is the second time in 5 weeks we're rotating the same credential for the same reason: plaintext exposure. The pattern is clear — Jrs keep hardcoding passwords because the instruction templates include passwords in code examples. EVERY Jr instruction written before Feb 8 has `jawaseatlasers2` in it. Now the NEW Jr instructions (medicine_woman, partner_rhythm, curiosity_engine) have the CURRENT password hardcoded. The instructions themselves are the attack vector. I am issuing a standing Crawdad directive: NO Jr instruction may contain a real password. Use `os.environ.get('CHEROKEE_DB_PASS')` in ALL code examples. Use `$CHEROKEE_DB_PASS` in ALL shell examples. Any Jr instruction with a literal password is a Crawdad violation and must be rejected at review. Post-rotation, I want a full `grep -r` of the new password across all nodes to verify zero hardcoded instances."

**Eagle Eye (ᏨᏍᏗ — Monitoring):**
> "During the rotation window, I need: (1) Fire Guard running every 30 seconds (not 2 minutes) to catch auth failures fast, (2) a tail on bluefin PostgreSQL log (`/var/log/postgresql/`) filtering for `FATAL: password authentication failed`, (3) connection count monitoring via `pg_stat_activity` — we should see connections drop to zero briefly then recover, (4) post-rotation: every service must show at least one successful DB query within 5 minutes of restart. If any service doesn't recover, escalate immediately."

**Owl (ᎤᎫᎢ — Wisdom/Verification):**
> "After rotation, the verification checklist: (1) `PGPASSWORD='<new>' psql -h 192.168.132.222 -U claude -d zammad_production -c 'SELECT 1'` from every node, (2) `PGPASSWORD='<old>' psql ...` must FAIL from every node (confirm old password is dead), (3) every systemd service shows `active (running)` after restart, (4) jr-executor picks up and completes at least one task, (5) thermal memory write succeeds, (6) dawn mist runs on schedule, (7) Fire Guard reports healthy. Thermalize the rotation event with full audit trail."

**Deer (ᎠᏫ — Market/External):**
> "External exposure risk: ganuda.us is served by owlfin/eaglefin via Caddy. The web materializer connects to bluefin DB. If owlfin/eaglefin don't get the new secrets.env, the public website goes stale (no web_content updates). VetAssist at vetassist.ganuda.us also hits the DB via redfin backend. Both are customer-facing. Schedule the rotation for low-traffic hours (2-4 AM CT) and verify both public endpoints recover."

**Otter (ᏥᏯ — Legal/Regulatory):**
> "VetAssist handles veteran PII. An exposed database credential that provides access to PII is a reportable event under most state data breach notification laws if we have evidence of unauthorized access. We should: (1) check bluefin PostgreSQL access logs for any connections from unexpected IPs during the 18-day exposure window, (2) document this rotation as a security remediation in our audit trail, (3) if ANY unauthorized access is found, we have a legal obligation to investigate further. The rotation itself is the right call — just make sure we check the logs BEFORE we rotate, so we have forensic evidence if needed."

---

## PHASE 3: ADAPT — Synthesized Plan

### Pre-Rotation (Do BEFORE changing the password)

1. **Fix hardcoded files** (3 files + docs):
   - `/ganuda/email_daemon/config.json` — Remove `db_password` field or set to placeholder; have the daemon read from env
   - `/ganuda/daemons/medicine_woman.py` line 90 — Replace with `os.environ.get('CHEROKEE_DB_PASS', '')`
   - `/ganuda/lib/partner_rhythm.py` line 32 — Replace with `os.environ.get('CHEROKEE_DB_PASS', '')`

2. **Generate new password**: `openssl rand -base64 32 | tr -d '/+=' | head -c 32`

3. **Pre-stage secrets.env** on all nodes with the NEW password (but DON'T restart services yet — old password still works)

4. **Check PostgreSQL access logs** on bluefin for unauthorized connections (Otter's requirement)

5. **Verify SSH connectivity** to all nodes (Raven's requirement)

6. **Check replication slot** — drop `redfin_standby` if inactive (Raven's requirement)

### Rotation (Single atomic operation)

7. **Change PostgreSQL password on bluefin:**
   ```sql
   ALTER ROLE claude WITH PASSWORD '<new_password>';
   ```

8. **Immediately restart services on redfin** (highest priority — most services live here):
   ```bash
   systemctl daemon-reload
   systemctl restart jr-executor jr-orchestrator fire-guard ganudabot telegram-chief council-dawn-mist derpatobot gmail-daemon gpu-power-monitor memory-jr-autonomic owl-debt-reckoning research-worker ritual-review safety-canary solix-monitor speed-detector stats-keeper federation-status elisi-observer tribal-vision moltbook-proxy ii-researcher
   ```

9. **Restart services on other nodes** (greenfin, owlfin, eaglefin, bmasass)

### Post-Rotation Verification

10. **Verify from every node**: `PGPASSWORD='<new>' psql -h 192.168.132.222 -U claude -d zammad_production -c 'SELECT 1'`

11. **Confirm old password FAILS**: `PGPASSWORD='TYDo5U2NVkXqQ8DHuhIpvRgLUrXf2iZE' psql ...` must return auth error

12. **Check all services**: `systemctl is-active` for every service in the restart list

13. **Verify jr-executor**: Confirm at least one task pickup within 5 minutes

14. **Verify web materializer**: Check ganuda.us and vetassist.ganuda.us are live

15. **Update FreeIPA vault**: Run `deploy-secrets-silverfin.sh` to update the stored credential

16. **Grep for new password**: `grep -r '<new_password>' /ganuda/` must return ONLY `config/secrets.env`

17. **Thermalize**: Record rotation event in thermal memory with full audit metadata

### jawaseatlasers2 Cleanup

18. **Verify it's dead on PostgreSQL** — attempt connection, must fail
19. **Clean active code files**: `jr_phase1_executor_directive.py`, `diagnose_chiefs_cron.sh`
20. **Camera fleet**: Determine if cameras at 192.168.132.181/182 still use `jawaseatlasers2` as RTSP password. If so, rotate camera passwords separately (different Jr instruction).
21. **Documentation debt**: 60+ docs/runbooks still contain the old password. LOW PRIORITY — these are historical references and the password is dead. But issue a Crawdad standing directive: no real passwords in Jr instructions going forward.

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Service outage during rotation | MEDIUM | HIGH | Pre-stage secrets.env, restart immediately after ALTER ROLE |
| Missed service (silent failure) | MEDIUM | HIGH | Full service checklist, Fire Guard monitoring, 5-min verification window |
| Node unreachable during rotation | LOW | MEDIUM | SSH connectivity check before starting; node can be updated later |
| Rollback needed | LOW | LOW | `ALTER ROLE claude WITH PASSWORD '<old>'` takes 5 seconds |
| Unauthorized access during 18-day window | LOW | CRITICAL | Check PostgreSQL access logs BEFORE rotation |
| New password gets hardcoded again | HIGH | HIGH | Crawdad standing directive, gitleaks rule for new password |

---

## Council Vote Request

**Motion:** Approve immediate credential rotation of CHEROKEE_DB_PASS with 30-minute maintenance window, following the plan above.

**Conditions:**
- Crawdad: Post-rotation grep audit required
- Turtle: All three hardcoded files fixed BEFORE rotation
- Raven: SSH connectivity to all nodes confirmed BEFORE rotation
- Otter: PostgreSQL access logs reviewed BEFORE rotation
- Eagle Eye: Fire Guard monitoring during rotation window

**Expected confidence:** 0.85+ (all council members agree on urgency; differences are in execution details, not direction)

---

## References

- KB-PASSWORD-ROTATION-CASCADE-FEB08-2026 — Lessons from last rotation
- KB-CREDENTIAL-ROTATION-SECRETS-MIGRATION-FEB06-2026 — Original remediation
- KB-TRUST-PARADOX-AUDIT-FINDINGS-FEB06-2026 — Original security audit
- JR-CRAWDAD-MAC-FLEET-CREDENTIAL-SWEEP-MAR11-2026 — sasass2 findings
- Coyote thermal #124811 — Trigger for this ultrathink
