# JR Instruction: Expand FreeIPA Sudo Scope

**Task:** Add `kill`, `reboot`, and `dbus-send` to the `ganuda-service-management` sudo rule
**Priority:** P2 (prevents future dbus deadlock autonomy loss)
**Assigned:** Infrastructure Jr.
**Context:** On Mar 12 2026, redfin's dbus wedged due to accounts-daemon cascade. TPM had FreeIPA sudo for systemctl but not kill/reboot. Could not fix autonomously. Chief had to intervene manually. DC-10 violation — reflex layer must exist independent of deliberative layer.

---

### Step 1: Update FreeIPA sudo rule on silverfin

**Note:** This step requires Chief SSH to silverfin (via greenfin proxy) and FreeIPA admin credentials.

Add these commands to the `ganuda-service-management` sudo rule:

```text
/usr/bin/kill
/usr/sbin/reboot
/usr/bin/dbus-send
/usr/bin/journalctl
```

FreeIPA admin commands (run on silverfin):
```text
ipa sudocmd-add /usr/bin/kill
ipa sudocmd-add /usr/sbin/reboot
ipa sudocmd-add /usr/bin/dbus-send
ipa sudocmd-add /usr/bin/journalctl
ipa sudorule-add-allow-command ganuda-service-management --sudocmds=/usr/bin/kill
ipa sudorule-add-allow-command ganuda-service-management --sudocmds=/usr/sbin/reboot
ipa sudorule-add-allow-command ganuda-service-management --sudocmds=/usr/bin/dbus-send
ipa sudorule-add-allow-command ganuda-service-management --sudocmds=/usr/bin/journalctl
```

### Step 2: Verify on redfin

After silverfin update, verify from any node:
```text
sudo -l | grep -E 'kill|reboot|dbus-send|journalctl'
```

### Step 3: Disable desktop services on redfin

After reboot (or after dbus recovers):
```text
sudo systemctl disable --now accounts-daemon.service
sudo systemctl mask xdg-document-portal.service
```

Consider setting default target to multi-user if GDM is not needed:
```text
sudo systemctl set-default multi-user.target
```

---

**DC-10 Lesson:** The reflex layer (local process management) must not depend on the deliberative layer (SSSD/dbus/FreeIPA). When the cortex wedges, the spinal cord still needs to fire. `kill` and `reboot` are spinal cord commands.
