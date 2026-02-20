# Jr Instruction: Ritual Engine Systemd Timer

**Task ID:** RITUAL-TIMER-002
**Priority:** P2
**Assigned To:** Software Engineer Jr.
**Date:** February 10, 2026

## Step 1: Create service unit

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

## Step 2: Create timer unit

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

## Do NOT

- Do not install or enable the units — human operator handles sudo
- Do not modify ritual_review.py
