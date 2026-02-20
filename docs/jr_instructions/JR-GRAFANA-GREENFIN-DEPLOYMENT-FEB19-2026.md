# Jr Instruction: Deploy Grafana on Greenfin Port 3000

**Task ID**: GRAFANA-GREENFIN-001
**Priority**: 3
**Assigned Jr**: Infrastructure Jr.
**Story Points**: 3
**use_rlm**: false
**Council Vote**: #c213ecee1d54de33 (Option A, 0.842 confidence)

## Context

Grafana was found as a ghost process on redfin:3000 conflicting with VetAssist. Council voted to permanently place Grafana on greenfin:3000, co-located with OpenObserve (greenfin:5601) and Promtail (greenfin:9080) — the existing monitoring stack.

Greenfin IP: 192.168.132.224

## Step 1: Create Grafana systemd service file

Create `/ganuda/scripts/systemd/grafana.service`

```ini
[Unit]
Description=Grafana Dashboard — Cherokee AI Federation
After=network.target
Wants=network.target

[Service]
Type=simple
User=dereadi
Group=dereadi
ExecStart=/usr/share/grafana/bin/grafana server --config=/etc/grafana/grafana.ini --homepath=/usr/share/grafana
Restart=always
RestartSec=10
StandardOutput=append:/ganuda/logs/grafana.log
StandardError=append:/ganuda/logs/grafana.log
Environment="GF_SERVER_HTTP_PORT=3000"
Environment="GF_SERVER_HTTP_ADDR=0.0.0.0"

[Install]
WantedBy=multi-user.target
```

## Step 2: Create Grafana Ansible playbook for greenfin

Create `/ganuda/ansible/playbooks/grafana-greenfin.yaml`

```yaml
---
- name: Deploy Grafana on Greenfin
  hosts: greenfin
  become: yes
  vars:
    grafana_port: 3000
    grafana_bind: "0.0.0.0"

  tasks:
    - name: Add Grafana APT repository key
      ansible.builtin.apt_key:
        url: https://apt.grafana.com/gpg.key
        state: present

    - name: Add Grafana APT repository
      ansible.builtin.apt_repository:
        repo: "deb https://apt.grafana.com stable main"
        state: present

    - name: Install Grafana
      ansible.builtin.apt:
        name: grafana
        state: present
        update_cache: yes

    - name: Configure Grafana port
      ansible.builtin.lineinfile:
        path: /etc/grafana/grafana.ini
        regexp: '^;?http_port'
        line: 'http_port = {{ grafana_port }}'
        section: server

    - name: Configure Grafana bind address
      ansible.builtin.lineinfile:
        path: /etc/grafana/grafana.ini
        regexp: '^;?http_addr'
        line: 'http_addr = {{ grafana_bind }}'
        section: server

    - name: Enable and start Grafana
      ansible.builtin.systemd:
        name: grafana-server
        enabled: yes
        state: started
        daemon_reload: yes

    - name: Add nftables rule for Grafana port
      ansible.builtin.lineinfile:
        path: /ganuda/config/nftables-greenfin.conf
        insertafter: 'tcp dport 8003 accept'
        line: '    tcp dport 3000 accept comment "Grafana dashboard"'
```

## Step 3: Update CMDB with Grafana location

File: `/ganuda/config/ganuda.yaml`

<<<<<<< SEARCH
  greenfin:
    ip: 192.168.132.224
    role: monitoring
=======
  greenfin:
    ip: 192.168.132.224
    role: monitoring
    grafana_port: 3000
>>>>>>> REPLACE

## Manual Steps (TPM on greenfin)

1. Run the Ansible playbook: `ansible-playbook -i /ganuda/ansible/inventory /ganuda/ansible/playbooks/grafana-greenfin.yaml`
2. Verify: `curl -s http://192.168.132.224:3000/api/health`
3. Add OpenObserve as Grafana data source (Prometheus-compatible endpoint)
4. Update nftables: `sudo nft -f /ganuda/config/nftables-greenfin.conf`
