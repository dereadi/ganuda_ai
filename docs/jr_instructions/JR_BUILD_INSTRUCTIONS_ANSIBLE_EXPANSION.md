# Jr Build Instructions: Ansible Playbook Expansion

**Task ID:** JR-ANSIBLE-EXPAND-001
**Priority:** Medium
**Assigned Specialist:** Gecko (Technical Integration)
**Date:** 2025-12-25

---

## Context

Currently only one Ansible playbook exists: `/ganuda/ansible/provision_jsdorn_user.yml` on bluefin. The inventory is defined but playbooks for service deployment, patching, and configuration management are missing.

## Objective

Expand Ansible infrastructure to enable reproducible deployments and configuration management across the 6-node federation.

---

## Current State

**Inventory:** `/ganuda/ansible/inventory_federation.ini` (exists)
```
[federation_linux]
bluefin, redfin, greenfin

[federation_macos]
sasass, sasass2, bmasass

[federation:vars]
ansible_python_interpreter=/usr/bin/python3
```

**Templates:** Only `jsdorn_account_report.j2`

**Playbooks:** Only user provisioning

---

## Required Playbooks

### 1. Base System Configuration

Create `/ganuda/ansible/playbooks/base_system.yml`:

```yaml
---
# Base system configuration for all Federation nodes
- name: Configure Federation Base Systems
  hosts: federation
  become: yes
  tasks:
    - name: Ensure /ganuda directory structure
      file:
        path: "{{ item }}"
        state: directory
        owner: dereadi
        mode: '0755'
      loop:
        - /ganuda
        - /ganuda/scripts
        - /ganuda/lib
        - /ganuda/logs
        - /ganuda/docs

    - name: Install common packages (Linux)
      apt:
        name:
          - python3-pip
          - python3-venv
          - git
          - curl
          - jq
          - htop
        state: present
      when: ansible_os_family == "Debian"

    - name: Configure timezone
      timezone:
        name: America/Chicago

    - name: Ensure log rotation for /ganuda/logs
      copy:
        dest: /etc/logrotate.d/ganuda
        content: |
          /ganuda/logs/*.log {
              daily
              rotate 14
              compress
              missingok
              notifempty
          }
      when: ansible_os_family == "Debian"
```

### 2. Service Deployment Playbook

Create `/ganuda/ansible/playbooks/deploy_service.yml`:

```yaml
---
# Generic service deployment playbook
# Usage: ansible-playbook deploy_service.yml -e "service=llm_gateway node=redfin"
- name: Deploy Federation Service
  hosts: "{{ node }}"
  become: yes
  vars:
    service_path: "/ganuda/services/{{ service }}"
    venv_path: "{{ service_path }}/venv"
    log_path: "/ganuda/logs/{{ service }}.log"

  tasks:
    - name: Create service directory
      file:
        path: "{{ service_path }}"
        state: directory
        owner: dereadi
        mode: '0755'

    - name: Create Python venv
      command: python3 -m venv {{ venv_path }}
      args:
        creates: "{{ venv_path }}/bin/python"

    - name: Copy service files
      synchronize:
        src: "{{ playbook_dir }}/../services/{{ service }}/"
        dest: "{{ service_path }}/"
        rsync_opts:
          - "--exclude=venv"
          - "--exclude=__pycache__"
          - "--exclude=*.pyc"

    - name: Install requirements
      pip:
        requirements: "{{ service_path }}/requirements.txt"
        virtualenv: "{{ venv_path }}"
      when: lookup('file', service_path + '/requirements.txt', errors='ignore')

    - name: Deploy systemd unit
      template:
        src: "templates/{{ service }}.service.j2"
        dest: "/etc/systemd/system/{{ service }}.service"
      notify: reload systemd

    - name: Enable and start service
      systemd:
        name: "{{ service }}"
        enabled: yes
        state: started

    - name: Register in CMDB
      command: >
        python3 /ganuda/scripts/cmdb_register.py
        --type service
        --name {{ service }}
        --node {{ inventory_hostname }}
        --status running
        --path {{ service_path }}
        --systemd {{ service }}.service

  handlers:
    - name: reload systemd
      systemd:
        daemon_reload: yes
```

### 3. Database Configuration Playbook

Create `/ganuda/ansible/playbooks/configure_postgresql.yml`:

```yaml
---
# PostgreSQL configuration for bluefin
- name: Configure PostgreSQL
  hosts: bluefin
  become: yes
  vars:
    pg_data: /var/lib/postgresql/14/main
    pg_hba: /etc/postgresql/14/main/pg_hba.conf

  tasks:
    - name: Ensure PostgreSQL listening on network
      lineinfile:
        path: /etc/postgresql/14/main/postgresql.conf
        regexp: "^#?listen_addresses"
        line: "listen_addresses = '*'"
      notify: restart postgresql

    - name: Allow federation network access
      lineinfile:
        path: "{{ pg_hba }}"
        line: "host    all    claude    192.168.132.0/24    md5"
        insertafter: "^# IPv4 local connections"
      notify: restart postgresql

    - name: Ensure claude user exists
      become_user: postgres
      postgresql_user:
        name: claude
        password: jawaseatlasers2
        role_attr_flags: CREATEDB,LOGIN

    - name: Ensure zammad_production database exists
      become_user: postgres
      postgresql_db:
        name: zammad_production
        owner: claude

  handlers:
    - name: restart postgresql
      service:
        name: postgresql
        state: restarted
```

### 4. Patching Playbook

Create `/ganuda/ansible/playbooks/patch_nodes.yml`:

```yaml
---
# Security patching for Federation nodes
- name: Patch Federation Nodes
  hosts: federation_linux
  become: yes
  serial: 1  # One node at a time for safety

  tasks:
    - name: Update apt cache
      apt:
        update_cache: yes
        cache_valid_time: 3600

    - name: Upgrade all packages
      apt:
        upgrade: safe
      register: upgrade_result

    - name: Check if reboot required
      stat:
        path: /var/run/reboot-required
      register: reboot_required

    - name: Record patching event
      command: >
        python3 /ganuda/scripts/create_kb_article.py
        --type how_to
        --title "Patching {{ inventory_hostname }} - {{ ansible_date_time.date }}"
        --symptoms "Routine patching"
        --root_cause "Security updates"
        --resolution "{{ upgrade_result.stdout | default('No output') }}"
        --prevention "Automated patching"
        --nodes {{ inventory_hostname }}
      when: upgrade_result.changed

    - name: Notify if reboot required
      debug:
        msg: "REBOOT REQUIRED on {{ inventory_hostname }}"
      when: reboot_required.stat.exists
```

### 5. Service Templates

Create `/ganuda/ansible/templates/` with:

**llm_gateway.service.j2:**
```ini
[Unit]
Description=Cherokee AI LLM Gateway
After=network.target

[Service]
Type=simple
User=dereadi
WorkingDirectory={{ service_path }}
ExecStart={{ venv_path }}/bin/python gateway.py
Restart=always
RestartSec=10
StandardOutput=append:{{ log_path }}
StandardError=append:{{ log_path }}

[Install]
WantedBy=multi-user.target
```

**hive_mind_bidding.service.j2:**
```ini
[Unit]
Description=Cherokee AI Hive Mind Bidding Daemon
After=network.target

[Service]
Type=simple
User=dereadi
WorkingDirectory={{ service_path }}
ExecStart={{ venv_path }}/bin/python hive_mind_bidding.py {{ agent_id }} {{ node }}
Restart=always
RestartSec=30
StandardOutput=append:{{ log_path }}
StandardError=append:{{ log_path }}

[Install]
WantedBy=multi-user.target
```

---

## Directory Structure

After implementation:

```
/ganuda/ansible/
├── inventory_federation.ini       # Existing
├── ansible.cfg                    # New
├── playbooks/
│   ├── base_system.yml
│   ├── deploy_service.yml
│   ├── configure_postgresql.yml
│   └── patch_nodes.yml
├── templates/
│   ├── jsdorn_account_report.j2   # Existing
│   ├── llm_gateway.service.j2
│   └── hive_mind_bidding.service.j2
└── roles/
    └── common/
        └── tasks/
            └── main.yml
```

---

## Acceptance Criteria

1. [ ] All playbooks created and tested
2. [ ] Templates created for active services
3. [ ] `ansible.cfg` configured with proper paths
4. [ ] Documentation updated
5. [ ] At least one successful run of each playbook

---

## Dependencies

- Ansible 2.9+ installed on orchestration node
- SSH key access to all nodes
- sudo/become privileges

---

*For Seven Generations*
