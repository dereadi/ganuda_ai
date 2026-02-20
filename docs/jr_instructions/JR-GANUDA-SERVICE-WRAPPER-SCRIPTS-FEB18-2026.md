# Jr Instruction: Federation Service Wrapper Scripts

**Task**: Build two wrapper scripts that allow the federation to deploy and manage its own systemd services with safety validation and notification
**Priority**: 8/10
**Story Points**: 5
**Kanban**: #1822
**Assigned Jr**: Software Engineer Jr.

## Context

The federation is transitioning to Level 5+ autonomous operation. Currently, every service deployment requires the Chief to manually run sudo commands. These wrapper scripts eliminate that bottleneck by providing validated, audited, notification-sending wrappers around systemctl and service file deployment.

FreeIPA will grant sudo access ONLY to these two scripts — not to raw systemctl or cp. All policy enforcement lives in the scripts themselves.

Study these existing patterns before building:
- `/ganuda/scripts/gpu_power_monitor.py` — Telegram notification pattern
- `/ganuda/telegram_bot/telegram_chief_v3.py` — Telegram sendMessage API usage
- `/ganuda/scripts/systemd/` — the staging directory where .service files live before deployment
- `/ganuda/lib/secrets_loader.py` — how we load env vars from secrets.env

## Script 1: `/usr/local/bin/ganuda-deploy-service`

A bash script that safely deploys a staged .service file to systemd.

### Behavior

1. Takes one argument: the service name (e.g., `tpm-autonomic` or `tpm-autonomic.service`)
2. Appends `.service` if not already present
3. Validates the .service file exists in `/ganuda/scripts/systemd/` (the ONLY allowed source directory)
4. Validates the file is actually a systemd unit file (contains `[Unit]` or `[Service]` section header)
5. Copies the file to `/etc/systemd/system/`
6. Runs `systemctl daemon-reload`
7. Runs `systemctl enable --now <service>`
8. Checks the service status (capture output of `systemctl is-active`)
9. Sends a Telegram notification to the Chief with: service name, node hostname, whether it started successfully, timestamp
10. Logs the action to `/ganuda/logs/service-deploy.log` with timestamp

### Safety constraints

- MUST reject any path traversal attempts (no `../`, no absolute paths in the argument)
- MUST only deploy from `/ganuda/scripts/systemd/` — hardcoded, not configurable
- MUST NOT deploy if the .service file doesn't pass basic validation
- If the service fails to start, still send the Telegram notification (with failure status) and exit non-zero

### Environment variables (loaded by the caller or from secrets.env)

- `TELEGRAM_BOT_TOKEN` — for notifications
- `TELEGRAM_CHIEF_CHAT_ID` — recipient chat ID

### Exit codes

- 0: success
- 1: invalid arguments
- 2: service file not found in staging
- 3: validation failed
- 4: copy/reload failed
- 5: service failed to start (but was deployed)

## Script 2: `/usr/local/bin/ganuda-service-ctl`

A bash script that provides safe start/stop/restart/status for federation services.

### Behavior

1. Takes two arguments: action (`start`, `stop`, `restart`, `status`, `enable`, `disable`) and service name
2. Appends `.service` if not already present
3. Validates the service file exists in `/etc/systemd/system/` (only manage services that are actually deployed)
4. Runs `systemctl <action> <service>`
5. For actions that change state (`start`, `stop`, `restart`, `enable`, `disable`): sends Telegram notification with action, service name, hostname, result
6. For `status`: just outputs the result, no notification
7. Logs all state-changing actions to `/ganuda/logs/service-ctl.log`

### Safety constraints

- Only allows the six listed actions — reject anything else
- Rejects path traversal in service name
- Only operates on services that exist in `/etc/systemd/system/`

## Both scripts

- Should be written in bash (not Python) — they need to work without any venv
- Should source `/ganuda/config/secrets.env` for Telegram tokens if env vars aren't set
- Should use `curl` for Telegram API calls (not Python requests)
- Should include a `--dry-run` flag that shows what would happen without doing it
- Should be executable (`chmod +x`)

## Step 1: Create the deploy script

Create `/ganuda/scripts/ganuda-deploy-service`

(This will later be copied to `/usr/local/bin/` by the Ansible playbook — the Jr does NOT need sudo)

## Step 2: Create the ctl script

Create `/ganuda/scripts/ganuda-service-ctl`

## Step 3: Create log directory

Ensure `/ganuda/logs/` exists.

## Acceptance Criteria

- [ ] Both scripts pass `bash -n` syntax check
- [ ] `ganuda-deploy-service --dry-run tpm-autonomic` shows the actions it would take without executing
- [ ] `ganuda-deploy-service` rejects `../etc/passwd` and similar path traversal
- [ ] `ganuda-deploy-service` rejects files not in `/ganuda/scripts/systemd/`
- [ ] `ganuda-service-ctl status vllm` works and outputs service status
- [ ] `ganuda-service-ctl --dry-run restart vllm` shows what it would do
- [ ] Telegram notification format includes hostname, service name, action, result, timestamp
- [ ] Log files are appended to, not overwritten

## Out of Scope

- FreeIPA sudo rule configuration (separate Jr instruction)
- Ansible playbook for distribution (separate Jr instruction)
- Actually deploying to /usr/local/bin/ (requires sudo — handled by Ansible)
