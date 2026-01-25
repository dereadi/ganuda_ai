# Jr Instructions: Greenfin Route to Nachocheese Network

**Task ID**: NET-NACHOCHEESE-001
**Priority**: HIGH (P1)
**Date**: January 13, 2026
**Target**: greenfin (192.168.132.224)
**Purpose**: Enable temporary route to goldfin via nachocheese WiFi for freeipa-client install

---

## Context

- goldfin (PII Sanctum) needs freeipa-client installed
- goldfin has WiFi on nachocheese network (10.0.0.121)
- goldfin's wired connection (VLAN 20) blocks internet access BY DESIGN
- greenfin bridges to nachocheese but route may not be configured
- Need temporary path: greenfin → nachocheese WiFi → goldfin (10.0.0.121)

---

## Step 1: Check Greenfin's WiFi Interface

```bash
# SSH to greenfin
ssh dereadi@192.168.132.224

# List all interfaces
ip a

# Look for wireless interface (wlp*, wlan*, etc)
ip a | grep -E "wlp|wlan"

# Check if connected to nachocheese
nmcli device status
nmcli connection show --active
```

---

## Step 2: Verify Greenfin's IP on Nachocheese

```bash
# Check if greenfin has 10.0.0.x address
ip addr show | grep "10.0.0"

# Check routing table
ip route | grep 10.0.0
```

---

## Step 3: Add Route if Missing

```bash
# If greenfin has a wifi interface on nachocheese but no route to 10.0.0.0/24:
# Find the wifi interface name first (e.g., wlp2s0)

sudo ip route add 10.0.0.0/24 dev <wifi-interface>

# Verify
ping -c 2 10.0.0.121
```

---

## Step 4: SSH to Goldfin via Nachocheese

```bash
# From greenfin, once route is working
ssh dereadi@10.0.0.121
```

---

## Step 5: On Goldfin - Install FreeIPA Client

```bash
# Disable wired to force wifi as default route
sudo nmcli connection down enp2s0

# Verify internet via wifi
ping -c 2 8.8.8.8

# Install freeipa-client
sudo dnf install -y freeipa-client

# Restore wired connection
sudo nmcli connection up enp2s0

# Seal the wifi rift
sudo nmcli radio wifi off
```

---

## Step 6: Verify Goldfin Back on VLAN 20

```bash
# Check goldfin is back on wired
ip a | grep enp2s0

# Verify reachable from greenfin via VLAN 20
# From greenfin:
ping -c 2 192.168.20.10
```

---

## Post-Install: Remove Temporary Route on Greenfin (Optional)

```bash
# On greenfin, remove nachocheese route if no longer needed
sudo ip route del 10.0.0.0/24 dev <wifi-interface>
```

---

*For Seven Generations*
