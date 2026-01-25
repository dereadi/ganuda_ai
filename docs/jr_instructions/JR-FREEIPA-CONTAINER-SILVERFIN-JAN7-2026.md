# Jr Instruction: FreeIPA Container on silverfin

**Date**: January 7, 2026
**Assigned To**: Infrastructure Jr, TPM (Flying Squirrel)
**Node**: silverfin (192.168.132.57)
**Priority**: High
**Status**: Ready for execution

---

## Overview

FreeIPA server packages are not available for Debian 13 (trixie). We will run FreeIPA in a container using Podman (Docker alternative, rootless capable).

**Container Image**: `freeipa/freeipa-server:fedora-41`

---

## Phase 1: Install Podman

```bash
# Install Podman (Docker-compatible, daemonless)
sudo apt install -y podman podman-compose

# Verify installation
podman --version
```

---

## Phase 2: Prepare FreeIPA Data Directory

```bash
# Create persistent data directory
sudo mkdir -p /var/lib/freeipa-data
sudo chmod 755 /var/lib/freeipa-data
```

---

## Phase 3: Configure System for FreeIPA

```bash
# FreeIPA needs specific sysctls
echo "net.ipv6.conf.all.disable_ipv6 = 0" | sudo tee -a /etc/sysctl.d/99-freeipa.conf
sudo sysctl -p /etc/sysctl.d/99-freeipa.conf

# Set hostname properly (FQDN required)
sudo hostnamectl set-hostname silverfin.cherokee.local

# Add to /etc/hosts
echo "192.168.132.57 silverfin.cherokee.local silverfin" | sudo tee -a /etc/hosts
```

---

## Phase 4: Run FreeIPA Container (Interactive Setup)

First run with interactive setup to configure the IPA server:

```bash
sudo podman run -d --name freeipa-server \
  --hostname silverfin.cherokee.local \
  --read-only \
  --dns=127.0.0.1 \
  -v /var/lib/freeipa-data:/data:Z \
  -v /sys/fs/cgroup:/sys/fs/cgroup:ro \
  -p 80:80 -p 443:443 \
  -p 389:389 -p 636:636 \
  -p 88:88 -p 88:88/udp \
  -p 464:464 -p 464:464/udp \
  -p 53:53 -p 53:53/udp \
  -p 123:123/udp \
  freeipa/freeipa-server:fedora-41 ipa-server-install \
  --realm=CHEROKEE.LOCAL \
  --domain=cherokee.local \
  --ds-password=CHANGEME_DIRECTORY \
  --admin-password=CHANGEME_ADMIN \
  --unattended \
  --setup-dns \
  --no-forwarders \
  --no-ntp
```

**IMPORTANT**: Replace passwords:
- `CHANGEME_DIRECTORY` - Directory Manager password (LDAP admin)
- `CHANGEME_ADMIN` - IPA admin user password

---

## Phase 5: Monitor Installation

```bash
# Watch the installation logs (takes 5-10 minutes)
sudo podman logs -f freeipa-server

# Look for: "The ipa-server-install command was successful"
```

---

## Phase 6: Verify FreeIPA is Running

```bash
# Check container status
sudo podman ps

# Test web UI (should redirect to HTTPS)
curl -k https://silverfin.cherokee.local/ipa/ui/

# Test from inside container
sudo podman exec freeipa-server ipa ping
```

---

## Phase 7: Create Systemd Service for Auto-Start

```bash
# Generate systemd service
sudo podman generate systemd --name freeipa-server --files --new
sudo mv container-freeipa-server.service /etc/systemd/system/

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable container-freeipa-server.service
```

---

## Phase 8: Configure DNS Forwarding (Optional)

If you want FreeIPA to handle DNS for the cluster:

```bash
# Add upstream forwarder
sudo podman exec freeipa-server ipa dnsconfig-mod --forwarder=8.8.8.8

# Or use your router
sudo podman exec freeipa-server ipa dnsconfig-mod --forwarder=192.168.132.1
```

---

## Phase 9: Add Cherokee AI Nodes as Hosts

```bash
# Add each node to FreeIPA
sudo podman exec freeipa-server ipa host-add redfin.cherokee.local --ip-address=192.168.132.223
sudo podman exec freeipa-server ipa host-add bluefin.cherokee.local --ip-address=192.168.132.222
sudo podman exec freeipa-server ipa host-add greenfin.cherokee.local --ip-address=192.168.132.224
sudo podman exec freeipa-server ipa host-add goldfin.cherokee.local --ip-address=192.168.20.10
sudo podman exec freeipa-server ipa host-add sasass.cherokee.local --ip-address=192.168.132.241
sudo podman exec freeipa-server ipa host-add sasass2.cherokee.local --ip-address=192.168.132.242
```

---

## Phase 10: Enroll Client Nodes

On each client node (redfin, bluefin, greenfin, etc.):

```bash
# Install FreeIPA client
sudo apt install -y freeipa-client   # Debian
# or
sudo dnf install -y freeipa-client   # Fedora/RHEL

# Enroll to FreeIPA server
sudo ipa-client-install \
  --server=silverfin.cherokee.local \
  --domain=cherokee.local \
  --realm=CHEROKEE.LOCAL \
  --mkhomedir \
  --unattended
```

---

## Port Reference

| Port | Protocol | Service |
|------|----------|---------|
| 80 | TCP | HTTP (redirects to 443) |
| 443 | TCP | HTTPS Web UI |
| 389 | TCP | LDAP |
| 636 | TCP | LDAPS |
| 88 | TCP/UDP | Kerberos |
| 464 | TCP/UDP | Kerberos password change |
| 53 | TCP/UDP | DNS |
| 123 | UDP | NTP |

---

## Configuration Reference

| Setting | Value |
|---------|-------|
| Realm | CHEROKEE.LOCAL |
| Domain | cherokee.local |
| Web UI | https://silverfin.cherokee.local/ipa/ui/ |
| Admin User | admin |
| LDAP Base DN | dc=cherokee,dc=local |

---

## Troubleshooting

### Container won't start
```bash
# Check logs
sudo podman logs freeipa-server

# Check if ports are in use
sudo ss -tlnp | grep -E ':(80|443|389|636|88|53)\s'
```

### DNS not resolving
```bash
# Restart DNS inside container
sudo podman exec freeipa-server systemctl restart named
```

### Reset and start over
```bash
sudo podman stop freeipa-server
sudo podman rm freeipa-server
sudo rm -rf /var/lib/freeipa-data/*
# Then run Phase 4 again
```

---

## Security Notes

- Directory Manager password grants full LDAP access - keep it safe
- Admin password is for day-to-day administration
- After VLAN migration, only greenfin trunk port can reach silverfin
- Consider enabling 2FA for admin accounts

---

## Post-Migration (VLAN 10)

After FreeIPA is working on compute VLAN:

1. Change silverfin IP to 192.168.10.10
2. Move cable to switch port 13 or 14
3. Update container with new IP
4. Clients will need trunk port access or DNS update

---

## Thermal Memory Archive

Once complete, archive to thermal memory:

```sql
INSERT INTO thermal_memory_archive (
    memory_hash, original_content, temperature_score, tags,
    source_triad, source_node, memory_type
) VALUES (
    md5('freeipa_silverfin_deployed_jan2026'),
    'FREEIPA DEPLOYED ON SILVERFIN - January 2026
    Container: freeipa/freeipa-server:fedora-41
    Realm: CHEROKEE.LOCAL
    Domain: cherokee.local
    Web UI: https://silverfin.cherokee.local/ipa/ui/
    Purpose: Centralized identity management for Cherokee AI Federation',
    95.0,
    ARRAY['freeipa', 'identity', 'silverfin', 'container', 'deployed'],
    'tpm', 'silverfin', 'cmdb_entry'
);
```

---

For Seven Generations.
