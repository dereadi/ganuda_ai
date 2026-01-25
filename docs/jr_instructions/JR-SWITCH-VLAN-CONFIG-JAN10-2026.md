# Jr Instruction: Switch VLAN Configuration

**Date**: January 10, 2026
**Assigned To**: Web4AI Jr (browser automation)
**Target**: TP-Link TL-SG1428PE at http://192.168.132.132
**Priority**: High
**Status**: Ready for execution

---

## Credentials

- **Username**: admin
- **Password**: jawaseatlasers2 (same as bluefin PostgreSQL)

---

## Task Overview

Configure VLANs on the TP-Link switch for the DMZ/Sanctum architecture:

| VLAN ID | Name | Purpose |
|---------|------|---------|
| 1 | Default | Compute network (existing) |
| 10 | Identity | DMZ - silverfin (FreeIPA) |
| 20 | Sanctum | PII - goldfin (air-gapped) |

---

## Port Assignments

| Port | Node | VLAN Config |
|------|------|-------------|
| 14 | silverfin | VLAN 10 Untagged, Remove from VLAN 1 |
| 16 | goldfin | VLAN 20 Untagged, Remove from VLAN 1 |
| 18 | greenfin | Trunk: VLAN 1 Untagged, VLAN 10 Tagged, VLAN 20 Tagged |

---

## Step-by-Step Instructions

### Step 1: Login
1. Navigate to http://192.168.132.132
2. Enter username: `admin`
3. Enter password: `jawaseatlasers2`
4. Click Login

### Step 2: Create VLAN 10 (Identity)
1. Go to **VLAN** → **802.1Q VLAN** (or similar menu)
2. Click **Create** or **Add VLAN**
3. VLAN ID: `10`
4. VLAN Name: `Identity`
5. Save/Apply

### Step 3: Create VLAN 20 (Sanctum)
1. Click **Create** or **Add VLAN**
2. VLAN ID: `20`
3. VLAN Name: `Sanctum`
4. Save/Apply

### Step 4: Configure Port 18 as Trunk (greenfin)
1. Go to **VLAN** → **802.1Q VLAN** → Port settings (or PVID settings)
2. For Port 18:
   - VLAN 1: **Untagged** (native/PVID)
   - VLAN 10: **Tagged**
   - VLAN 20: **Tagged**
3. Set PVID for Port 18 to `1`
4. Save/Apply

### Step 5: Configure Port 14 as Access (silverfin - VLAN 10)
1. For Port 14:
   - VLAN 1: **Not Member** (remove)
   - VLAN 10: **Untagged**
2. Set PVID for Port 14 to `10`
3. Save/Apply

**WARNING**: After this step, silverfin will lose network connectivity until its IP is changed to 192.168.10.10

### Step 6: Configure Port 16 as Access (goldfin - VLAN 20)
1. For Port 16:
   - VLAN 1: **Not Member** (remove)
   - VLAN 20: **Untagged**
2. Set PVID for Port 16 to `20`
3. Save/Apply

**WARNING**: After this step, goldfin will lose network connectivity until its IP is changed to 192.168.20.10

### Step 7: Save Configuration
1. Go to **Save** or **System** → **Save Config**
2. Save to startup config (persists across reboot)

---

## Verification

After configuration, the VLAN table should show:

| VLAN | Ports (Untagged) | Ports (Tagged) |
|------|------------------|----------------|
| 1 | 1-13, 15, 17, 18-28 | - |
| 10 | 14 | 18 |
| 20 | 16 | 18 |

---

## Rollback (if needed)

If something goes wrong:
1. Reset Port 14 to VLAN 1 Untagged
2. Reset Port 16 to VLAN 1 Untagged
3. Reset Port 18 to VLAN 1 Untagged only
4. Delete VLANs 10 and 20

---

## Post-Switch Config (TPM will handle)

After switch is configured:
1. SSH to silverfin via console/direct and set IP to 192.168.10.10/24, gateway 192.168.10.1
2. SSH to goldfin via console/direct and set IP to 192.168.20.10/24, gateway 192.168.20.1
3. Verify routing through greenfin

---

For Seven Generations.
