# JR-NETWORK-CONFIG-CAPTURE-JAN13-2026: Capture Network Settings to CMDB and Ansible

**Created**: 2026-01-13
**Author**: TPM (Flying Squirrel) + Claude
**Priority**: HIGH
**Target**: bluefin (Ansible controller)

---

## Objective

After getting inter-VLAN routing working, capture all network configurations to:
1. Update CMDB (federation_nodes table)
2. Update Ansible inventory
3. Create network config playbook
4. Write KB article

---

## Part 1: Update CMDB (federation_nodes)

Current incorrect data:
- silverfin shows 192.168.132.122 (WiFi) instead of 192.168.10.10 (VLAN 10)
- greenfin missing local_ip
- goldfin missing entirely

### SQL to fix federation_nodes:

```sql
-- Connect to bluefin PostgreSQL
PGPASSWORD='jawaseatlasers2' psql -h 192.168.132.222 -U claude -d triad_federation

-- Update silverfin with correct VLAN 10 IP
UPDATE federation_nodes
SET local_ip = '192.168.10.10',
    status = 'active'
WHERE node_name = 'silverfin';

-- Update greenfin with local IP
UPDATE federation_nodes
SET local_ip = '192.168.132.224'
WHERE node_name = 'greenfin';

-- Add goldfin if missing
INSERT INTO federation_nodes (node_name, platform, local_ip, tailscale_ip, status)
VALUES ('goldfin', 'linux', '192.168.20.10', NULL, 'active')
ON CONFLICT (node_name) DO UPDATE SET local_ip = '192.168.20.10';

-- Verify
SELECT node_name, platform, local_ip, tailscale_ip, status FROM federation_nodes ORDER BY node_name;
```

---

## Part 2: Update Ansible Inventory

Edit `/ganuda/home/dereadi/ansible/inventory/cherokee_federation.yml` on bluefin:

### Add identity_servers group (VLAN 10):

```yaml
identity_servers:
  hosts:
    silverfin:
      ansible_host: 192.168.10.10
      platform: linux
      role: identity_server
      vlan: 10
      services:
        - freeipa
        - kerberos
        - dns
      freeipa_realm: CHEROKEE.LOCAL
```

### Add sanctum group (VLAN 20):

```yaml
sanctum:
  hosts:
    goldfin:
      ansible_host: 192.168.20.10
      platform: linux
      role: pii_sanctum
      vlan: 20
      services:
        - vetassist_pii
```

### Add VLAN routing info to greenfin:

```yaml
cpu_workers:
  hosts:
    greenfin:
      ansible_host: 192.168.132.224
      tailscale_ip: 100.100.243.116
      platform: linux
      role: cpu_worker
      is_vlan_router: true
      vlan_interfaces:
        - name: eno1.10
          ip: 192.168.10.1
          vlan: 10
        - name: eno1.20
          ip: 192.168.20.1
          vlan: 20
```

### Update children groups:

```yaml
linux_nodes:
  children:
    hub:
    gpu_inference:
    cpu_workers:
    identity_servers:
    sanctum:
```

---

## Part 3: Create Network Config Playbook

Create `/ganuda/home/dereadi/ansible/playbooks/network_vlan_routes.yml`:

```yaml
---
# Cherokee AI Federation - Inter-VLAN Routing Playbook
# Configures persistent routes for VLAN 10 (DMZ) and VLAN 20 (Sanctum) access
# For Seven Generations

- name: Configure VLAN routes on Ubuntu nodes
  hosts: hub:gpu_inference
  become: yes
  vars:
    vlan_gateway: 192.168.132.224  # greenfin
  tasks:
    - name: Get current netplan config file
      find:
        paths: /etc/netplan
        patterns: "*.yaml"
      register: netplan_files

    - name: Backup existing netplan config
      copy:
        src: "{{ item.path }}"
        dest: "{{ item.path }}.backup.{{ ansible_date_time.iso8601_basic_short }}"
        remote_src: yes
      loop: "{{ netplan_files.files }}"

    - name: Ensure routes exist in netplan (manual edit required)
      debug:
        msg: |
          Add these routes to your netplan config under the ethernet interface:
          routes:
            - to: 192.168.10.0/24
              via: {{ vlan_gateway }}
            - to: 192.168.20.0/24
              via: {{ vlan_gateway }}

          Then run: sudo netplan apply

- name: Configure VLAN router (greenfin)
  hosts: cpu_workers
  become: yes
  tasks:
    - name: Create sysctl config for VLAN routing
      copy:
        dest: /etc/sysctl.d/99-vlan-routing.conf
        content: |
          # Cherokee AI Federation - Inter-VLAN routing
          # Disable reverse path filtering for routing between VLANs
          net.ipv4.conf.all.rp_filter = 0
          net.ipv4.conf.default.rp_filter = 0
          net.ipv4.conf.eno1.rp_filter = 0
          net.ipv4.conf.eno1/10.rp_filter = 0
          net.ipv4.conf.eno1/20.rp_filter = 0
          net.ipv4.ip_forward = 1
        mode: '0644'
      notify: reload sysctl

    - name: Apply sysctl settings
      command: sysctl --system

  handlers:
    - name: reload sysctl
      command: sysctl --system

- name: Configure return route on silverfin (VLAN 10)
  hosts: identity_servers
  become: yes
  tasks:
    - name: Create route file for eno1
      copy:
        dest: /etc/sysconfig/network-scripts/route-eno1
        content: |
          192.168.132.0/24 via 192.168.10.1 dev eno1
        mode: '0644'
      when: ansible_os_family == "RedHat"
      notify: reload network

  handlers:
    - name: reload network
      command: nmcli connection reload

- name: Configure return route on goldfin (VLAN 20)
  hosts: sanctum
  become: yes
  tasks:
    - name: Create route file
      copy:
        dest: /etc/sysconfig/network-scripts/route-{{ ansible_default_ipv4.interface }}
        content: |
          192.168.132.0/24 via 192.168.20.1 dev {{ ansible_default_ipv4.interface }}
        mode: '0644'
      when: ansible_os_family == "RedHat"
      notify: reload network

  handlers:
    - name: reload network
      command: nmcli connection reload
```

---

## Part 4: KB Article

Create `/Users/Shared/ganuda/kb/KB-VLAN-ARCHITECTURE-JAN2026.md` with:

- Network diagram (ASCII art)
- VLAN assignments (1=Compute, 10=DMZ, 20=Sanctum)
- Routing through greenfin
- IP assignments for each node
- Troubleshooting tips (rp_filter, return routes)

---

## Execution Order

1. First: Make routes persistent manually (JR-PERSISTENT-VLAN-ROUTES-JAN13-2026.md)
2. Then: Update CMDB SQL
3. Then: Update Ansible inventory
4. Then: Create playbook (for future use)
5. Finally: Write KB article

---

## Verification

After all changes:

```bash
# Test from bluefin
ansible all -i inventory/cherokee_federation.yml -m ping

# Specifically test new nodes
ansible identity_servers -i inventory/cherokee_federation.yml -m ping
ansible sanctum -i inventory/cherokee_federation.yml -m ping
```

---

**For Seven Generations**: Document infrastructure for those who come after.
