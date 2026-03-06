# Manual Instruction: Keepalived VRRP Failover for DMZ Web Servers

**Task ID:** DMZ-KEEPALIVED
**Kanban:** #1885
**Priority:** 3
**Assigned:** TPM (manual — requires sudo on DMZ nodes)
**Executor:** MANUAL — not Jr-compatible (apt install + sudo + DMZ SSH)

---

## Overview

Deploy Keepalived on owlfin (primary) and eaglefin (failover) to provide automatic failover via a shared Virtual IP (192.168.30.10). AT&T router port-forwards 443 → VIP. If owlfin dies, eaglefin claims the VIP in under 1 second.

---

## Prerequisites

- SSH access to both nodes via greenfin jump host
- sudo on owlfin and eaglefin (FreeIPA)
- AT&T router admin access (to change port-forward target)
- Caddy already running on both nodes

---

## Step 1: Install keepalived on both nodes

**On owlfin:**
```
sudo apt update && sudo apt install -y keepalived
```

**On eaglefin:**
```
sudo apt update && sudo apt install -y keepalived
```

---

## Step 2: Create health check script on both nodes

**On both owlfin and eaglefin**, create `/etc/keepalived/check_caddy.sh`:

```
#!/bin/bash
# Check if Caddy is serving HTTPS locally
curl -sf -o /dev/null --max-time 3 -k https://localhost/ 2>/dev/null
exit $?
```

Then make it executable:
```
sudo chmod +x /etc/keepalived/check_caddy.sh
```

---

## Step 3: Configure keepalived on owlfin (MASTER)

**On owlfin**, create `/etc/keepalived/keepalived.conf`:

```
global_defs {
    router_id owlfin
    script_user dereadi
    enable_script_security
}

vrrp_script chk_caddy {
    script "/etc/keepalived/check_caddy.sh"
    interval 5
    fall 3
    rise 2
    weight -50
}

vrrp_instance VI_WEB {
    state MASTER
    interface enp2s0
    virtual_router_id 51
    priority 100
    advert_int 1

    authentication {
        auth_type PASS
        auth_pass ch3r0k33
    }

    virtual_ipaddress {
        192.168.30.10/24
    }

    track_script {
        chk_caddy
    }

    notify_master "/etc/keepalived/notify.sh MASTER"
    notify_backup "/etc/keepalived/notify.sh BACKUP"
    notify_fault  "/etc/keepalived/notify.sh FAULT"
}
```

**IMPORTANT:** Verify the interface name with `ip addr` — it may be `enp2s0`, `enp1s0`, `eth0`, or similar. Replace `enp2s0` with the actual interface that has the 192.168.30.2 address.

---

## Step 4: Configure keepalived on eaglefin (BACKUP)

**On eaglefin**, create `/etc/keepalived/keepalived.conf`:

```
global_defs {
    router_id eaglefin
    script_user dereadi
    enable_script_security
}

vrrp_script chk_caddy {
    script "/etc/keepalived/check_caddy.sh"
    interval 5
    fall 3
    rise 2
    weight -50
}

vrrp_instance VI_WEB {
    state BACKUP
    interface enp2s0
    virtual_router_id 51
    priority 90
    advert_int 1

    authentication {
        auth_type PASS
        auth_pass ch3r0k33
    }

    virtual_ipaddress {
        192.168.30.10/24
    }

    track_script {
        chk_caddy
    }

    notify_master "/etc/keepalived/notify.sh MASTER"
    notify_backup "/etc/keepalived/notify.sh BACKUP"
    notify_fault  "/etc/keepalived/notify.sh FAULT"
}
```

Same note: verify interface name with `ip addr`.

---

## Step 5: Create Telegram notification script on both nodes

**On both nodes**, create `/etc/keepalived/notify.sh`:

```
#!/bin/bash
# Keepalived state change notification via Telegram
STATE=$1
HOSTNAME=$(hostname)
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# Telegram bot token (derpatobot)
BOT_TOKEN="${TELEGRAM_BOT_TOKEN:-}"
CHAT_ID="${TELEGRAM_CHAT_ID:-}"

MESSAGE="[KEEPALIVED] ${HOSTNAME} transitioned to ${STATE} at ${TIMESTAMP}"

if [ -n "$BOT_TOKEN" ] && [ -n "$CHAT_ID" ]; then
    curl -sf -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
        -d "chat_id=${CHAT_ID}" \
        -d "text=${MESSAGE}" \
        -d "parse_mode=HTML" > /dev/null 2>&1
fi

# Also log locally
logger -t keepalived "State change: ${STATE}"
```

Then:
```
sudo chmod +x /etc/keepalived/notify.sh
```

**Note:** If you want Telegram alerts, set `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` in `/etc/default/keepalived` or hardcode them. Otherwise the script just logs to syslog, which is fine.

---

## Step 6: Enable and start keepalived on both nodes

**On owlfin:**
```
sudo systemctl enable keepalived
sudo systemctl start keepalived
sudo systemctl status keepalived
```

**On eaglefin:**
```
sudo systemctl enable keepalived
sudo systemctl start keepalived
sudo systemctl status keepalived
```

---

## Step 7: Verify VIP assignment

**On owlfin:**
```
ip addr show | grep 192.168.30.10
```

Should show the VIP on the network interface. Eaglefin should NOT have it.

**Test VRRP communication:**
```
sudo journalctl -u keepalived -n 20
```

Look for `Entering MASTER STATE` on owlfin and `Entering BACKUP STATE` on eaglefin.

---

## Step 8: Update AT&T router port-forward

Log into AT&T router admin and change the port-forward rule:

- **Old:** Port 443 → 192.168.30.2 (owlfin)
- **New:** Port 443 → 192.168.30.10 (VIP)

Also update port 80 if you forward that for ACME/HTTP redirect.

---

## Step 9: Failover test

**On owlfin:**
```
sudo systemctl stop caddy
```

Wait 15 seconds (5s interval × 3 failures), then:

**On eaglefin:**
```
ip addr show | grep 192.168.30.10
```

Should now show the VIP on eaglefin. Verify the site still loads:
```
curl -sk https://192.168.30.10/ -H "Host: ganuda.us" | head -5
```

**Restore owlfin:**
```
sudo systemctl start caddy
```

Owlfin should reclaim the VIP within 10 seconds (5s interval × 2 rises).

---

## Step 10: Verify from external

From bmasass or another device:
```
curl -sk https://ganuda.us/ | head -5
```

---

## Rollback

If anything goes wrong:
```
sudo systemctl stop keepalived
sudo systemctl disable keepalived
```

Change AT&T port-forward back to 192.168.30.2. Everything returns to current state.

---

## Architecture Diagram

```
Internet → AT&T Router :443
                ↓
         Port-forward to 192.168.30.10 (VIP)
                ↓
    ┌───────────────────────────┐
    │    VRRP (Keepalived)      │
    │                           │
    │  owlfin    eaglefin       │
    │  MASTER    BACKUP         │
    │  .2        .3             │
    │  priority  priority       │
    │  100       90             │
    │                           │
    │  VIP: 192.168.30.10       │
    │  (floats to active node)  │
    └───────────────────────────┘
         ↓              ↓
      Caddy           Caddy
      (TLS)           (TLS)
```

---

## What NOT to Change

- Do NOT modify Caddy configs — they stay exactly as-is
- Do NOT change DNS records — VIP is internal only, public DNS stays the same
- Do NOT remove the direct IPs (.2, .3) — they're still needed for SSH access
