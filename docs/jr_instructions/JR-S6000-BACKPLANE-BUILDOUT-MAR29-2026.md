# JR Instruction: S6000 Backplane Buildout

**JR ID:** JR-NETWORK-002
**Priority:** P0 (Hardware on hand, serial console active)
**Created:** 2026-03-29
**Author:** TPM via Claude Code
**Assigned To:** Chief (physical install) + Network Jr (switch config)
**Effort:** Medium (3 SP)
**Blocking Deps:** None — all hardware received, serial console confirmed on bluefin:/dev/ttyUSB0

## Context

Dell S6000 is powered on and accessible via serial console from bluefin. Firmware: FTOS 9.10(0.1P6). Config is factory default. All procurement items from JR-NETWORK-001 have arrived:

- redfin: 10Gtek BCM57810S dual SFP+ NIC + 10m AOC
- bluefin: SABRENT USB4 10GbE adapter + H!Fiber SFP+ RJ45 transceiver + CAT6a 3m
- R730 SAN: Mellanox ConnectX-3 40GbE + 40G QSFP+ DAC 3m
- S6000: ipolex QSFP+ to 4xSFP+ breakout 0.5m

## Phase 1: Physical Install (Chief — hands required)

### Step 1.1 — S6000 Cabling

1. Insert **QSFP+ breakout cable** (ipolex 0.5m) into **port Fo 0/0** on the S6000
   - This gives us 4x SFP+ legs from a single QSFP+ port
   - Leg 0 → redfin (via 10m AOC)
   - Leg 1 → bluefin (via SFP+ RJ45 transceiver + CAT6a)
   - Legs 2-3 → spare

2. Insert **40G QSFP+ DAC 3m** into **port Fo 0/4** on the S6000
   - Other end goes into R730 Mellanox ConnectX-3

### Step 1.2 — redfin NIC Install

1. Power down redfin
2. Install **10Gtek BCM57810S** in an available PCIe x8 slot
3. Connect **10m AOC** from NIC SFP+ port 0 to S6000 breakout leg 0
4. Power up redfin
5. Verify NIC detected: `lspci | grep -i ethernet`
6. Driver should be `bnx2x` (in-kernel). If not: `sudo modprobe bnx2x`

### Step 1.3 — bluefin Adapter

1. Plug **H!Fiber SFP+ RJ45 transceiver** into S6000 breakout leg 1
2. Connect **CAT6a 3m** from transceiver RJ45 to **SABRENT USB4 adapter**
3. Plug SABRENT into bluefin USB4/TB3 port
4. Verify detected: `ip link show` — look for new interface (likely `enx...` or `eth1`)
5. Driver: `aqc111u` or `cdc_ncm` — should be in-kernel on Ubuntu 24.x

### Step 1.4 — R730 NIC Install

1. Power down R730
2. Install **Mellanox ConnectX-3** in available PCIe x8 slot
3. Connect **40G QSFP+ DAC 3m** from NIC to S6000 port Fo 0/4
4. Power up R730
5. Verify: `lspci | grep -i mellanox` — driver is `mlx4_en`

## Phase 2: S6000 Switch Configuration (via serial console)

Connect from bluefin: `sudo screen /dev/ttyUSB0 9600`

**IMPORTANT:** First add dereadi to dialout group so sudo isn't always needed:
```
sudo usermod -aG dialout dereadi
```
(Requires re-login to take effect)

### Step 2.1 — Basic Switch Setup

```
enable
configure terminal

! Hostname
hostname S6000-backplane

! Management — no external management needed, serial only for now
! Disable telnet, enable SSH if we want remote mgmt later

! Save periodically
end
write memory
```

### Step 2.2 — Configure Breakout Port (Fo 0/0 → 4x 10GbE)

The quad-port-profile in the running config already has port 0 in the breakout list. The breakout cable should auto-negotiate. Verify:

```
show interfaces fortyGigE 0/0
```

If breakout is working, you'll see sub-interfaces like `Te 0/1`, `Te 0/2`, `Te 0/3`, `Te 0/4` (TenGigabitEthernet). If not:

```
configure terminal
stack-unit 0 port 0 portmode quad
end
write memory
reload
```

### Step 2.3 — Assign Backplane IPs (Layer 3)

```
configure terminal

! Create backplane VLAN
interface vlan 100
 description Private-Backplane-10GbE
 tagged fortyGigE 0/4
 no shutdown
 exit

! If breakout created Te interfaces:
interface vlan 100
 tagged tenGigE 0/1
 tagged tenGigE 0/2
 no shutdown
 exit

! S6000 management IP on backplane (optional)
interface vlan 100
 ip address 10.10.10.254/24
 exit

end
write memory
```

**Note:** The S6000 does L2 switching. The 10.10.10.0/24 IPs are configured on the **nodes themselves**, not on the switch. The VLAN just keeps backplane traffic isolated.

### Step 2.4 — Verify Links

```
show interfaces status
show vlan
show lldp neighbors
```

Look for:
- Breakout legs: `Te 0/1` (redfin) and `Te 0/2` (bluefin) should show **Up**
- QSFP+ direct: `Fo 0/4` (R730) should show **Up**

## Phase 3: Node IP Configuration

### redfin (10.10.10.1)

Find the interface name first:
```bash
ip link show | grep -i 'bnx2x\|enp'
```

Then configure:
```bash
# /etc/netplan/99-backplane.yaml
sudo tee /etc/netplan/99-backplane.yaml << 'EOF'
network:
  version: 2
  ethernets:
    enp_REPLACE_ME:
      addresses:
        - 10.10.10.1/24
      mtu: 9000
EOF
sudo netplan apply
```

### bluefin (10.10.10.2)

```bash
ip link show  # find SABRENT interface name
sudo tee /etc/netplan/99-backplane.yaml << 'EOF'
network:
  version: 2
  ethernets:
    enx_REPLACE_ME:
      addresses:
        - 10.10.10.2/24
      mtu: 9000
EOF
sudo netplan apply
```

### R730 SAN (10.10.10.3)

```bash
ip link show | grep -i mlx
sudo tee /etc/netplan/99-backplane.yaml << 'EOF'
network:
  version: 2
  ethernets:
    enp_REPLACE_ME:
      addresses:
        - 10.10.10.3/24
      mtu: 9000
EOF
sudo netplan apply
```

## Phase 4: Verification

### Step 4.1 — Connectivity

From each node, ping the other two:
```bash
ping -c 3 10.10.10.1  # redfin
ping -c 3 10.10.10.2  # bluefin
ping -c 3 10.10.10.3  # R730
```

### Step 4.2 — Bandwidth (iperf3)

Install if needed: `sudo apt install iperf3`

On redfin (server):
```bash
iperf3 -s -B 10.10.10.1
```

From bluefin:
```bash
iperf3 -c 10.10.10.1 -t 10 -P 4
```
**Expected:** ~9.4 Gbps for 10GbE links

From R730:
```bash
iperf3 -c 10.10.10.1 -t 10 -P 4
```
**Expected:** ~35+ Gbps for 40GbE link (limited by redfin's 10GbE NIC on the breakout)

### Step 4.3 — Jumbo Frames

```bash
ping -c 3 -M do -s 8972 10.10.10.1
```
Should succeed if MTU 9000 is set on all three nodes + switch.

## Phase 5: PostgreSQL on Backplane

Once connectivity is verified, update PostgreSQL on bluefin to also listen on the backplane:

```bash
# In postgresql.conf
listen_addresses = 'localhost,192.168.132.222,10.10.10.2'
```

Then restart PostgreSQL and update application configs to prefer `10.10.10.2` for DB connections from redfin.

**Expected improvement:** DB queries from redfin to bluefin go over dedicated 10GbE instead of sharing the 1GbE LAN.

## Rollback

- Node IPs: `sudo rm /etc/netplan/99-backplane.yaml && sudo netplan apply`
- Switch: `enable` → `reload` (factory config if we haven't saved, or `write erase` then `reload`)
- Physical: Unplug cables, remove NICs. No permanent changes.

## Success Criteria

- [ ] All three nodes pingable on 10.10.10.0/24
- [ ] iperf3 shows ≥9 Gbps on 10GbE links
- [ ] Jumbo frames (MTU 9000) working end-to-end
- [ ] PostgreSQL accessible on 10.10.10.2:5432 from redfin
- [ ] No disruption to existing 1GbE LAN traffic

---

FOR SEVEN GENERATIONS
