# Jr Instruction: Ritual Engine Systemd Timer — Weekly Automated Review

**Task ID:** RITUAL-TIMER-001
**Priority:** P2
**Assigned To:** Infrastructure Jr.
**Target Node:** redfin (192.168.132.223)
**Date:** February 10, 2026
**Depends On:** RITUAL-ENGINE-001 (completed Feb 8, 2026)
**Manual Step:** YES — requires human to run sudo commands after Jr creates staged files

---

## Background

The Ritual Reinforcement Engine (`/ganuda/scripts/ritual_review.py`) was deployed on February 8, 2026 (Council Vote #8487). Its first manual run reviewed 18 behavioral patterns, processed 39 failures, and generated the cultural digest at `/ganuda/docs/cultural_digest.md`.

Currently this script has NO automated scheduling. Pheromone decay runs nightly at 3:33 AM via `pheromone_decay_v3.sh`, but the ritual engine (its counterpart — controlled reinforcement rather than cooling) must be triggered manually. This instruction installs a systemd timer to run it automatically every Sunday at 4:00 AM on redfin.

The ritual engine already reads credentials from `/ganuda/config/secrets.env` internally, but we pass the `EnvironmentFile` directive as well so that any future environment-variable-based credential lookups work without code changes.

---

## Step 1: Create the log directory (if missing)

The script writes to `/var/log/ganuda/ritual-review.log`. Ensure the directory exists and is owned by `dereadi`.

This is a manual prerequisite step. The Jr should verify this directory exists before proceeding:

    ls -ld /var/log/ganuda/

If it does not exist, flag it for the human operator to create with:

    sudo mkdir -p /var/log/ganuda
    sudo chown dereadi:dereadi /var/log/ganuda

---

## Step 2: Create the systemd service unit

Create `/ganuda/scripts/systemd/ritual-review.service`

```ini
[Unit]
Description=Cherokee AI Federation — Ritual Reinforcement Engine (weekly review)
Documentation=file:///ganuda/docs/jr_instructions/JR-RITUAL-ENGINE-PROTOTYPE-FEB08-2026.md
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
User=dereadi
Group=dereadi
WorkingDirectory=/ganuda
Environment=PYTHONPATH=/ganuda:/ganuda/lib
EnvironmentFile=/ganuda/config/secrets.env
ExecStart=/usr/bin/python3 /ganuda/scripts/ritual_review.py --mode weekly

StandardOutput=append:/var/log/ganuda/ritual-review.log
StandardError=append:/var/log/ganuda/ritual-review.log
SyslogIdentifier=ritual-review

# Hardening
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=read-only
PrivateTmp=true
ReadWritePaths=/ganuda/docs /var/log/ganuda

[Install]
WantedBy=multi-user.target
```

### Design decisions

- **Type=oneshot**: The ritual engine runs to completion and exits. It is not a long-lived daemon. `oneshot` is correct for timer-triggered batch jobs.
- **PYTHONPATH=/ganuda:/ganuda/lib**: The script imports `psycopg2` (system package) and reads `/ganuda/config/secrets.env` directly. The PYTHONPATH ensures any future imports from `/ganuda/lib` resolve correctly.
- **ReadWritePaths**: The service writes to `/ganuda/docs/cultural_digest.md` (digest output) and `/var/log/ganuda/ritual-review.log` (log file). Both paths are whitelisted under `ProtectSystem=strict`.
- **StandardOutput=append**: Captures all stdout/stderr to the log file in append mode so previous runs are not overwritten. Output also goes to the journal via `SyslogIdentifier`.
- **No Restart directive**: `oneshot` services do not restart. The timer handles re-invocation on schedule.

---

## Step 3: Create the systemd timer unit

Create `/ganuda/scripts/systemd/ritual-review.timer`

```ini
[Unit]
Description=Cherokee AI Federation — Ritual Engine Weekly Timer (Sunday 4 AM)

[Timer]
OnCalendar=Sun *-*-* 04:00:00
Persistent=true
RandomizedDelaySec=300

[Install]
WantedBy=timers.target
```

### Design decisions

- **OnCalendar=Sun \*-\*-\* 04:00:00**: Fires every Sunday at 4:00 AM local time. This is 30 minutes after pheromone decay (3:33 AM) to ensure decay completes first and the ritual engine reviews post-decay temperatures.
- **Persistent=true**: If redfin is powered off on Sunday at 4 AM (e.g., power outage, maintenance), systemd will run the missed timer as soon as the system boots. The ritual should never silently skip a week.
- **RandomizedDelaySec=300**: Up to 5 minutes of jitter to avoid thundering herd with other 4 AM crons. Minor, but good practice.

---

## Step 4: Verify the staged files

After creating both files, verify they parse correctly:

    cat /ganuda/scripts/systemd/ritual-review.service
    cat /ganuda/scripts/systemd/ritual-review.timer

Confirm:
1. Both files exist and are non-empty
2. The service `ExecStart` path matches `/usr/bin/python3 /ganuda/scripts/ritual_review.py --mode weekly`
3. The `EnvironmentFile` points to `/ganuda/config/secrets.env`
4. The timer `OnCalendar` is `Sun *-*-* 04:00:00`

---

## MANUAL DEPLOYMENT (Human Operator Required)

After Jr creates the staged files at `/ganuda/scripts/systemd/`, the human operator runs:

```
# Ensure log directory exists
sudo mkdir -p /var/log/ganuda
sudo chown dereadi:dereadi /var/log/ganuda

# Deploy service and timer to systemd
sudo cp /ganuda/scripts/systemd/ritual-review.service /etc/systemd/system/ritual-review.service
sudo cp /ganuda/scripts/systemd/ritual-review.timer /etc/systemd/system/ritual-review.timer
sudo systemctl daemon-reload

# Enable the timer (NOT the service — the timer triggers the service)
sudo systemctl enable ritual-review.timer
sudo systemctl start ritual-review.timer

# Verify timer is active and scheduled
systemctl list-timers --all | grep ritual

# Optional: test-fire the service manually to confirm it works
sudo systemctl start ritual-review.service
journalctl -u ritual-review --no-pager -n 30

# Verify digest was generated
cat /ganuda/docs/cultural_digest.md | head -20

# Verify log output
cat /var/log/ganuda/ritual-review.log | tail -20
```

---

## Do NOT

- Do not install or enable the systemd units — the human operator handles that (requires sudo)
- Do not modify `/ganuda/scripts/ritual_review.py` — the script is already working and tested
- Do not modify `pheromone_decay_v3.sh` — the ritual engine is a separate complementary process
- Do not hardcode database passwords anywhere — `EnvironmentFile` and the script's internal `load_secrets()` handle credentials
- Do not create a `.service` file with `Type=simple` — the ritual engine runs to completion, not as a daemon

---

## Acceptance Criteria

1. **File exists:** `/ganuda/scripts/systemd/ritual-review.service` is created with correct content matching the specification above
2. **File exists:** `/ganuda/scripts/systemd/ritual-review.timer` is created with correct content matching the specification above
3. **Service runs as dereadi:** `User=dereadi` and `Group=dereadi` are set in the service unit
4. **Working directory is /ganuda:** `WorkingDirectory=/ganuda` is set
5. **PYTHONPATH includes both paths:** `Environment=PYTHONPATH=/ganuda:/ganuda/lib`
6. **Credentials loaded:** `EnvironmentFile=/ganuda/config/secrets.env` is present
7. **Logging to file:** `StandardOutput` and `StandardError` both append to `/var/log/ganuda/ritual-review.log`
8. **Timer schedule correct:** `OnCalendar=Sun *-*-* 04:00:00` fires weekly on Sunday at 4 AM
9. **Persistent timer:** `Persistent=true` ensures missed runs fire on next boot
10. **Security hardening:** `NoNewPrivileges=true`, `ProtectSystem=strict`, `ProtectHome=read-only`, `PrivateTmp=true` are all present
11. **ReadWritePaths whitelist:** Only `/ganuda/docs` and `/var/log/ganuda` are writable — the minimum needed for digest output and log file
12. **No modification to ritual_review.py:** The existing script is untouched
13. **After manual deployment:** `systemctl list-timers --all | grep ritual` shows the timer as active with the next Sunday 4 AM trigger
14. **After manual test-fire:** `sudo systemctl start ritual-review.service` completes with exit code 0, cultural digest is updated, and log file contains the ritual review output
