# Jr Ultrathink Instructions: Ansible Infrastructure Deployment

**Task ID:** JR-ANSIBLE-DEPLOY-001
**Priority:** High (P2)
**Assigned Specialist:** Gecko (Technical Integration)
**Date:** 2025-12-25
**Ultrathink Analysis:** Complete

---

## ULTRATHINK ANALYSIS

### Problem Statement

The Cherokee AI Federation has 6 nodes but only ONE Ansible playbook (`provision_jsdorn_user.yml`). This creates:

1. **Reproducibility Gap**: If a node fails, we cannot rebuild it consistently
2. **Configuration Drift**: Manual changes accumulate, nodes diverge
3. **Tribal Knowledge Loss**: Deployment steps exist only in thermal memory, not executable code
4. **Audit Failure**: No proof of consistent configuration across federation

### Seven Generations Impact Assessment

**Without Ansible automation:**
- Knowledge of "how to deploy X" lives in human memory and thermal memory
- Each deployment is slightly different
- Recovery from failure requires archeology through logs and memory
- New team members cannot easily understand infrastructure

**With Ansible automation:**
- Infrastructure as Code = self-documenting
- Any node can be rebuilt from scratch
- Configuration is version-controlled and auditable
- Future generations inherit executable knowledge, not just documentation

### Risk Analysis

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Playbook breaks production | Medium | High | Use `--check` mode first, serial execution |
| SSH key issues | Low | Medium | Test connectivity before playbook runs |
| Package conflicts | Medium | Medium | Pin versions, use apt cache |
| Systemd unit errors | Medium | High | Template validation, restart handlers |

### Architecture Decision

**Option A:** Central Ansible control node (tpm-macbook)
- Pros: Single point of management, clear ownership
- Cons: Single point of failure, requires VPN for remote

**Option B:** Distributed Ansible (each node can run playbooks)
- Pros: Resilient, any node can recover others
- Cons: Coordination complexity, version sync

**DECISION:** Option A with backup. Primary on tpm-macbook, inventory and playbooks synced to redfin as backup control point.

---

## EXECUTION PLAN

### Phase 1: Ansible Control Setup (on tpm-macbook)

```bash
# 1. Verify Ansible installation
ansible --version

# 2. Create local Ansible directory structure
mkdir -p /Users/Shared/ganuda/ansible/{playbooks,templates,roles/common/tasks,group_vars,host_vars}

# 3. Create ansible.cfg
cat > /Users/Shared/ganuda/ansible/ansible.cfg << 'EOF'
[defaults]
inventory = inventory_federation.ini
remote_user = dereadi
host_key_checking = False
retry_files_enabled = False
gathering = smart
fact_caching = jsonfile
fact_caching_connection = /Users/Shared/ganuda/ansible/.facts_cache
fact_caching_timeout = 86400

[privilege_escalation]
become = True
become_method = sudo
become_user = root
become_ask_pass = False

[ssh_connection]
ssh_args = -o ControlMaster=auto -o ControlPersist=60s
pipelining = True
EOF
```

### Phase 2: Inventory Configuration

```ini
# /Users/Shared/ganuda/ansible/inventory_federation.ini
[federation_linux]
redfin ansible_host=192.168.132.223
bluefin ansible_host=192.168.132.222
greenfin ansible_host=192.168.132.224

[federation_macos]
sasass ansible_host=192.168.132.241
sasass2 ansible_host=192.168.132.242

[gpu_nodes]
redfin

[database_nodes]
bluefin

[daemon_nodes]
greenfin

[edge_nodes]
sasass
sasass2

[federation:children]
federation_linux
federation_macos

[federation:vars]
ansible_python_interpreter=/usr/bin/python3
ganuda_base=/ganuda
ganuda_logs=/ganuda/logs
ganuda_scripts=/ganuda/scripts
```

### Phase 3: Base System Playbook

Create `/Users/Shared/ganuda/ansible/playbooks/base_system.yml`:

```yaml
---
# Base system configuration for all Federation Linux nodes
- name: Configure Federation Base Systems
  hosts: federation_linux
  become: yes

  vars:
    required_packages:
      - python3-pip
      - python3-venv
      - python3-psycopg2
      - git
      - curl
      - jq
      - htop
      - tmux
      - rsync
      - net-tools

  tasks:
    - name: Ensure /ganuda directory structure exists
      file:
        path: "{{ item }}"
        state: directory
        owner: dereadi
        group: dereadi
        mode: '0755'
      loop:
        - "{{ ganuda_base }}"
        - "{{ ganuda_base }}/scripts"
        - "{{ ganuda_base }}/lib"
        - "{{ ganuda_base }}/logs"
        - "{{ ganuda_base }}/docs"
        - "{{ ganuda_base }}/services"
        - "{{ ganuda_base }}/backups"

    - name: Update apt cache
      apt:
        update_cache: yes
        cache_valid_time: 3600

    - name: Install required packages
      apt:
        name: "{{ required_packages }}"
        state: present

    - name: Configure timezone to America/Chicago
      timezone:
        name: America/Chicago

    - name: Ensure log rotation for ganuda logs
      copy:
        dest: /etc/logrotate.d/ganuda
        content: |
          {{ ganuda_logs }}/*.log {
              daily
              rotate 14
              compress
              delaycompress
              missingok
              notifempty
              create 0644 dereadi dereadi
          }
        owner: root
        group: root
        mode: '0644'

    - name: Ensure dereadi can sudo without password
      lineinfile:
        path: /etc/sudoers.d/dereadi
        line: 'dereadi ALL=(ALL) NOPASSWD:ALL'
        create: yes
        validate: 'visudo -cf %s'
        mode: '0440'

    - name: Register base system in CMDB
      command: >
        python3 {{ ganuda_scripts }}/cmdb_register.py
        --type config
        --name base_system
        --node {{ inventory_hostname }}
        --status running
        --version "ansible-deployed"
      ignore_errors: yes
      changed_when: false
```

### Phase 4: Service Deployment Playbook

Create `/Users/Shared/ganuda/ansible/playbooks/deploy_service.yml`:

```yaml
---
# Deploy a service to a Federation node
# Usage: ansible-playbook deploy_service.yml -e "service=llm_gateway target_node=redfin"
- name: Deploy Federation Service
  hosts: "{{ target_node }}"
  become: yes

  vars:
    service_base: "{{ ganuda_base }}/services/{{ service }}"
    venv_path: "{{ service_base }}/venv"
    log_file: "{{ ganuda_logs }}/{{ service }}.log"

  tasks:
    - name: Fail if service not specified
      fail:
        msg: "You must specify 'service' variable"
      when: service is not defined

    - name: Create service directory
      file:
        path: "{{ service_base }}"
        state: directory
        owner: dereadi
        group: dereadi
        mode: '0755'

    - name: Check if service files exist locally
      local_action:
        module: stat
        path: "{{ playbook_dir }}/../services/{{ service }}"
      register: service_source
      become: no

    - name: Synchronize service files
      synchronize:
        src: "{{ playbook_dir }}/../services/{{ service }}/"
        dest: "{{ service_base }}/"
        rsync_opts:
          - "--exclude=venv"
          - "--exclude=__pycache__"
          - "--exclude=*.pyc"
          - "--exclude=*.log"
      when: service_source.stat.exists

    - name: Create Python virtual environment
      command: python3 -m venv {{ venv_path }}
      args:
        creates: "{{ venv_path }}/bin/python"

    - name: Check for requirements.txt
      stat:
        path: "{{ service_base }}/requirements.txt"
      register: requirements_file

    - name: Install Python requirements
      pip:
        requirements: "{{ service_base }}/requirements.txt"
        virtualenv: "{{ venv_path }}"
        state: present
      when: requirements_file.stat.exists

    - name: Check for systemd template
      local_action:
        module: stat
        path: "{{ playbook_dir }}/../templates/{{ service }}.service.j2"
      register: systemd_template
      become: no

    - name: Deploy systemd unit file
      template:
        src: "{{ playbook_dir }}/../templates/{{ service }}.service.j2"
        dest: "/etc/systemd/system/{{ service }}.service"
        owner: root
        group: root
        mode: '0644'
      when: systemd_template.stat.exists
      notify:
        - Reload systemd
        - Restart service

    - name: Enable service
      systemd:
        name: "{{ service }}"
        enabled: yes
      when: systemd_template.stat.exists

    - name: Update CMDB
      command: >
        python3 {{ ganuda_scripts }}/cmdb_register.py
        --type service
        --name {{ service }}
        --node {{ inventory_hostname }}
        --status running
        --path {{ service_base }}
        --systemd {{ service }}.service
      ignore_errors: yes
      changed_when: false

  handlers:
    - name: Reload systemd
      systemd:
        daemon_reload: yes

    - name: Restart service
      systemd:
        name: "{{ service }}"
        state: restarted
```

### Phase 5: PostgreSQL Configuration Playbook

Create `/Users/Shared/ganuda/ansible/playbooks/configure_postgresql.yml`:

```yaml
---
# PostgreSQL configuration for bluefin
- name: Configure PostgreSQL for Federation
  hosts: bluefin
  become: yes

  vars:
    pg_version: "17"
    pg_data: "/var/lib/postgresql/{{ pg_version }}/main"
    pg_conf: "/etc/postgresql/{{ pg_version }}/main/postgresql.conf"
    pg_hba: "/etc/postgresql/{{ pg_version }}/main/pg_hba.conf"
    federation_network: "192.168.132.0/24"

  tasks:
    - name: Ensure PostgreSQL is listening on all interfaces
      lineinfile:
        path: "{{ pg_conf }}"
        regexp: "^#?listen_addresses\\s*="
        line: "listen_addresses = '*'"
        backup: yes
      notify: Restart PostgreSQL

    - name: Configure shared_buffers for thermal memory workload
      lineinfile:
        path: "{{ pg_conf }}"
        regexp: "^#?shared_buffers\\s*="
        line: "shared_buffers = 2GB"
        backup: yes
      notify: Restart PostgreSQL

    - name: Configure work_mem
      lineinfile:
        path: "{{ pg_conf }}"
        regexp: "^#?work_mem\\s*="
        line: "work_mem = 256MB"
      notify: Restart PostgreSQL

    - name: Configure effective_cache_size
      lineinfile:
        path: "{{ pg_conf }}"
        regexp: "^#?effective_cache_size\\s*="
        line: "effective_cache_size = 6GB"
      notify: Restart PostgreSQL

    - name: Allow Federation network access in pg_hba.conf
      lineinfile:
        path: "{{ pg_hba }}"
        line: "host    all    claude    {{ federation_network }}    md5"
        insertafter: "^# IPv4 local connections"
        state: present
      notify: Restart PostgreSQL

    - name: Allow localhost TCP connections
      lineinfile:
        path: "{{ pg_hba }}"
        line: "host    all    claude    127.0.0.1/32    md5"
        insertafter: "^# IPv4 local connections"
        state: present
      notify: Restart PostgreSQL

    - name: Update CMDB with PostgreSQL config
      command: >
        python3 {{ ganuda_scripts }}/cmdb_register.py
        --type database
        --name postgresql
        --node bluefin
        --port 5432
        --status running
        --version {{ pg_version }}
        --configs {{ pg_conf }},{{ pg_hba }}
      ignore_errors: yes
      changed_when: false

  handlers:
    - name: Restart PostgreSQL
      systemd:
        name: postgresql
        state: restarted
```

### Phase 6: Patching Playbook

Create `/Users/Shared/ganuda/ansible/playbooks/patch_federation.yml`:

```yaml
---
# Security patching for Federation nodes
- name: Patch Federation Linux Nodes
  hosts: federation_linux
  become: yes
  serial: 1  # One node at a time for safety

  vars:
    patch_date: "{{ ansible_date_time.date }}"

  tasks:
    - name: Update apt cache
      apt:
        update_cache: yes
      register: apt_update

    - name: Get list of upgradable packages
      command: apt list --upgradable
      register: upgradable_packages
      changed_when: false

    - name: Display upgradable packages
      debug:
        msg: "{{ upgradable_packages.stdout_lines }}"
      when: upgradable_packages.stdout_lines | length > 1

    - name: Perform safe upgrade
      apt:
        upgrade: safe
      register: upgrade_result

    - name: Check if reboot is required
      stat:
        path: /var/run/reboot-required
      register: reboot_required

    - name: Display reboot requirement
      debug:
        msg: "REBOOT REQUIRED on {{ inventory_hostname }}"
      when: reboot_required.stat.exists

    - name: Create KB article for patching event
      command: >
        python3 {{ ganuda_scripts }}/create_kb_article.py
        --type how_to
        --title "Patching {{ inventory_hostname }} - {{ patch_date }}"
        --symptoms "Routine security patching"
        --root_cause "Security updates available"
        --resolution "Applied {{ upgrade_result.stdout_lines | default(['none']) | length }} updates"
        --prevention "Automated monthly patching schedule"
        --nodes {{ inventory_hostname }}
      when: upgrade_result.changed
      ignore_errors: yes
      changed_when: false

    - name: Update CMDB with patch status
      command: >
        python3 {{ ganuda_scripts }}/cmdb_register.py
        --type config
        --name patching
        --node {{ inventory_hostname }}
        --status running
        --version "patched-{{ patch_date }}"
      ignore_errors: yes
      changed_when: false
```

### Phase 7: Service Templates

Create `/Users/Shared/ganuda/ansible/templates/llm_gateway.service.j2`:

```ini
[Unit]
Description=Cherokee AI LLM Gateway v1.2
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=dereadi
Group=dereadi
WorkingDirectory={{ service_base }}
ExecStart={{ venv_path }}/bin/python gateway.py
Restart=always
RestartSec=10
StandardOutput=append:{{ log_file }}
StandardError=append:{{ log_file }}
Environment="PYTHONUNBUFFERED=1"
Environment="DB_HOST=192.168.132.222"
Environment="DB_NAME=zammad_production"
Environment="DB_USER=claude"

[Install]
WantedBy=multi-user.target
```

Create `/Users/Shared/ganuda/ansible/templates/hive_mind_bidding.service.j2`:

```ini
[Unit]
Description=Cherokee AI Hive Mind Bidding Daemon
After=network.target postgresql.service
Wants=network-online.target

[Service]
Type=simple
User=dereadi
Group=dereadi
WorkingDirectory={{ service_base }}
ExecStart={{ venv_path }}/bin/python hive_mind_bidding.py
Restart=always
RestartSec=30
StandardOutput=append:{{ log_file }}
StandardError=append:{{ log_file }}
Environment="PYTHONUNBUFFERED=1"
Environment="NODE_NAME={{ inventory_hostname }}"

[Install]
WantedBy=multi-user.target
```

---

## VALIDATION STEPS

### Pre-Deployment Checks

```bash
# 1. Test inventory connectivity
cd /Users/Shared/ganuda/ansible
ansible all -m ping

# 2. Dry-run base system playbook
ansible-playbook playbooks/base_system.yml --check --diff

# 3. Verify template syntax
ansible-playbook playbooks/deploy_service.yml --syntax-check
```

### Post-Deployment Verification

```bash
# 1. Verify CMDB entries updated
ssh dereadi@192.168.132.222 "PGPASSWORD=jawaseatlasers2 psql -h 127.0.0.1 -U claude -d zammad_production -c \"SELECT metadata->>'cmdb_id', metadata->>'status' FROM thermal_memory_archive WHERE 'cmdb_entry' = ANY(tags) AND metadata->>'cmdb_id' LIKE 'CMDB-base_system%';\""

# 2. Check service status on each node
ansible federation_linux -m shell -a "systemctl list-units --type=service | grep cherokee"
```

---

## ACCEPTANCE CRITERIA

1. [ ] `ansible.cfg` configured with proper paths
2. [ ] `inventory_federation.ini` with all 6 nodes
3. [ ] `base_system.yml` playbook created and tested
4. [ ] `deploy_service.yml` playbook created
5. [ ] `configure_postgresql.yml` playbook created
6. [ ] `patch_federation.yml` playbook created
7. [ ] Service templates for llm_gateway and hive_mind_bidding
8. [ ] All playbooks pass `--syntax-check`
9. [ ] `ansible all -m ping` succeeds for Linux nodes
10. [ ] At least one successful `--check` run of base_system.yml

---

## DEPENDENCIES

- Ansible 2.9+ on tpm-macbook
- SSH key access to all Linux nodes
- sudo/become privileges for dereadi
- Python 3.x on all target nodes

---

## ESTIMATED COMPLEXITY

High - Multiple playbooks, templates, cross-node coordination. Requires careful testing.

---

*For Seven Generations - Cherokee AI Federation*
