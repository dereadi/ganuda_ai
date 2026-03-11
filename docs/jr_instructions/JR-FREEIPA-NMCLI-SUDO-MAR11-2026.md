# JR INSTRUCTION: Add nmcli to FreeIPA Sudo Allowlist

**Task**: Add `nmcli` to the `ganuda-service-management` sudo rule in FreeIPA so the cluster can self-heal network drops
**Priority**: P2 — operational autonomy
**Date**: 2026-03-11
**TPM**: Claude Opus
**Story Points**: 1

## Problem Statement

During a power outage on Mar 11 2026, greenfin's WiFi interface (`wlp195s0`, SSID `nachocheese`) dropped its association with the IoT AP. This WiFi bridge is the only path to the garage camera at `10.0.0.123`. The camera had power (blinky lights confirmed by Chief) but greenfin couldn't reach it.

The fix was one command: `sudo nmcli connection up nachocheese`. But the TPM couldn't run it — `nmcli` is not in the FreeIPA `ganuda-service-management` sudo rule. Chief had to SSH into greenfin manually and run it himself.

Every manual intervention is a gap in the organism's immune system. Fire Guard should be able to detect "WiFi bridge down, camera unreachable" and self-heal it.

## What You're Doing

Add `nmcli` to the existing `ganuda-service-management` sudo command group in FreeIPA on silverfin (192.168.10.10).

## Steps

### 1. Authenticate to FreeIPA

From greenfin (which has the route to silverfin at 192.168.10.10):

```bash
kinit admin
# or
kinit dereadi
```

### 2. Check current sudo command list

```bash
ipa sudorule-show ganuda-service-management --all
ipa sudocmd-find
```

Document what commands are currently in the rule. Expected (from memory):
- `/usr/bin/systemctl`
- `/usr/bin/cp`
- `/usr/bin/chmod`
- `/usr/bin/mkdir`
- `/usr/bin/wg`
- `/usr/bin/tee`
- `/usr/bin/cat`
- `/usr/local/bin/ganuda-deploy-service`
- `/usr/local/bin/ganuda-service-ctl`
- `/usr/sbin/nft`

### 3. Add nmcli sudo command

```bash
# Find nmcli path
which nmcli
# Expected: /usr/bin/nmcli

# Add the command to FreeIPA
ipa sudocmd-add /usr/bin/nmcli
ipa sudorule-add-allow-command ganuda-service-management --sudocmds=/usr/bin/nmcli
```

### 4. Verify the rule updated

```bash
ipa sudorule-show ganuda-service-management --all | grep nmcli
```

### 5. Clear SSSD cache and test

On greenfin (or any node):
```bash
sudo sss_cache -E
# Wait 10 seconds for SSSD to refresh
sleep 10

# Test — this should work without password now
sudo nmcli connection show
sudo nmcli connection up nachocheese
```

### 6. Test on another node

SSH to redfin or bluefin and verify `sudo nmcli` works there too. The rule applies federation-wide.

## Target Files

- FreeIPA server: silverfin (192.168.10.10, via greenfin bridge)
- Sudo rule: `ganuda-service-management` (MODIFY — add nmcli)

## Constraints

- Do NOT modify any other sudo rules
- Do NOT add broad commands like `/bin/bash` or `/usr/bin/python3`
- Do NOT change the rule's user scope — it should remain scoped to `dereadi`
- Only add the exact path `/usr/bin/nmcli`, not wildcards

## Future: Fire Guard Self-Heal (out of scope, note for backlog)

Once `nmcli` is in the sudo rule, Fire Guard can add a self-heal action:

```python
# Pseudocode for future Fire Guard enhancement
if camera_unreachable and greenfin_wifi_down:
    subprocess.run(["ssh", "greenfin", "sudo", "nmcli", "connection", "up", "nachocheese"])
    log_thermal("fire_guard_self_heal", "Reconnected greenfin WiFi bridge to IoT subnet")
```

This is a separate Jr task — don't implement it here. Just add `nmcli` to the sudo rule.

## Acceptance Criteria

- `ipa sudorule-show ganuda-service-management --all` includes `/usr/bin/nmcli`
- `sudo nmcli connection show` works without password prompt on greenfin
- `sudo nmcli connection show` works without password prompt on at least one other node
- No other sudo rules were modified
- Existing commands in the rule still work (`sudo systemctl status caddy` etc.)

## DO NOT

- Add commands beyond `nmcli`
- Modify the user scope of the sudo rule
- Touch any network configuration — this is sudo rule only
- Restart SSSD — just clear the cache with `sss_cache -E`
