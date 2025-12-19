# Jr Build Instructions: Ansible Node Bootstrap

**Priority**: HIGH  
**Phase**: 3 - Hardening & Packaging  
**Assigned To**: IT Triad Jr  
**Date**: December 13, 2025

## Objective

Create comprehensive Ansible playbook to bootstrap a new Cherokee AI Federation node from bare metal to production-ready state.

## Ansible Location

`/ganuda/home/dereadi/ansible/`

## Existing Infrastructure
- `inventory_federation.ini` - All 6 nodes defined
- `ansible.cfg` - Configuration
- `playbooks/` - Some existing playbooks
- `templates/` - Template files

## Bootstrap Playbook

Create `/ganuda/home/dereadi/ansible/playbooks/bootstrap_node.yml`:

```yaml
---
# Cherokee AI Federation Node Bootstrap
# Usage: ansible-playbook -i inventory_federation.ini playbooks/bootstrap_node.yml --limit <hostname>
# Example: ansible-playbook -i inventory_federation.ini playbooks/bootstrap_node.yml --limit redfin

- name: Bootstrap Cherokee AI Federation Node
  hosts: all
  become: yes
  vars:
    ganuda_user: dereadi
    ganuda_base: /ganuda
    postgres_host: 192.168.132.222
    postgres_user: claude
    postgres_db: zammad_production
    
  tasks:
    # ==================== SYSTEM BASICS ====================
    - name: Update apt cache (Debian/Ubuntu)
      apt:
        update_cache: yes
        cache_valid_time: 3600
      when: ansible_os_family == "Debian"
      
    - name: Install base packages (Linux)
      apt:
        name:
          - git
          - curl
          - wget
          - htop
          - vim
          - tmux
          - jq
          - python3
          - python3-pip
          - python3-venv
          - postgresql-client
          - net-tools
          - openssh-server
        state: present
      when: ansible_os_family == "Debian"

    # ==================== GANUDA STRUCTURE ====================
    - name: Create ganuda directory structure
      file:
        path: "{{ item }}"
        state: directory
        owner: "{{ ganuda_user }}"
        group: "{{ ganuda_user }}"
        mode: '0755'
      loop:
        - "{{ ganuda_base }}"
        - "{{ ganuda_base }}/docs"
        - "{{ ganuda_base }}/docs/kb"
        - "{{ ganuda_base }}/docs/jr_instructions"
        - "{{ ganuda_base }}/docs/roadmaps"
        - "{{ ganuda_base }}/scripts"
        - "{{ ganuda_base }}/services"
        - "{{ ganuda_base }}/lib"
        - "{{ ganuda_base }}/runbooks"
        - "{{ ganuda_base }}/backups"
        - /var/log/ganuda

    # ==================== PYTHON ENVIRONMENT ====================
    - name: Create Cherokee virtual environment
      command: python3 -m venv /home/{{ ganuda_user }}/cherokee_venv
      args:
        creates: /home/{{ ganuda_user }}/cherokee_venv/bin/activate
      become_user: "{{ ganuda_user }}"

    - name: Install Python packages in venv
      pip:
        name:
          - fastapi
          - uvicorn
          - httpx
          - psycopg2-binary
          - pydantic
          - requests
          - python-dotenv
        virtualenv: /home/{{ ganuda_user }}/cherokee_venv
      become_user: "{{ ganuda_user }}"

    # ==================== SSH CONFIGURATION ====================
    - name: Ensure SSH directory exists
      file:
        path: /home/{{ ganuda_user }}/.ssh
        state: directory
        owner: "{{ ganuda_user }}"
        group: "{{ ganuda_user }}"
        mode: '0700'

    - name: Copy SSH config for federation
      template:
        src: templates/ssh_config.j2
        dest: /home/{{ ganuda_user }}/.ssh/config
        owner: "{{ ganuda_user }}"
        mode: '0600'

    # ==================== GIT CONFIGURATION ====================
    - name: Configure git user
      git_config:
        name: "{{ item.name }}"
        value: "{{ item.value }}"
        scope: global
      become_user: "{{ ganuda_user }}"
      loop:
        - { name: 'user.name', value: 'GitHub Jr (Cherokee AI)' }
        - { name: 'user.email', value: 'github-jr@cherokee-ai.local' }

    # ==================== DATABASE CONNECTIVITY ====================
    - name: Create pgpass file for database access
      copy:
        content: "{{ postgres_host }}:5432:{{ postgres_db }}:{{ postgres_user }}:jawaseatlasers2\n"
        dest: /home/{{ ganuda_user }}/.pgpass
        owner: "{{ ganuda_user }}"
        mode: '0600'

    - name: Test database connectivity
      command: >
        psql -h {{ postgres_host }} -U {{ postgres_user }} -d {{ postgres_db }} 
        -c "SELECT 'Cherokee node connected' as status"
      become_user: "{{ ganuda_user }}"
      environment:
        PGPASSWORD: jawaseatlasers2
      register: db_test
      changed_when: false

    - name: Show database connection status
      debug:
        msg: "{{ db_test.stdout }}"

    # ==================== CHEROKEE LIBRARIES ====================
    - name: Clone/update specialist council library
      git:
        repo: https://github.com/dereadi/llm-gateway.git
        dest: "{{ ganuda_base }}/lib/llm-gateway"
        version: main
      become_user: "{{ ganuda_user }}"
      ignore_errors: yes  # Private repo may need auth

    # ==================== HEALTH MONITORING ====================
    - name: Create basic health check script
      copy:
        content: |
          #!/bin/bash
          # Cherokee Node Health Check
          echo "=== $(hostname) Health Check ==="
          echo "Date: $(date)"
          echo "Uptime: $(uptime)"
          echo "Memory: $(free -h | grep Mem)"
          echo "Disk: $(df -h / | tail -1)"
          echo "Load: $(cat /proc/loadavg)"
          
          # Test DB connection
          PGPASSWORD=jawaseatlasers2 psql -h {{ postgres_host }} -U {{ postgres_user }} -d {{ postgres_db }} -c "SELECT 1" > /dev/null 2>&1
          if [ $? -eq 0 ]; then
            echo "Database: CONNECTED"
          else
            echo "Database: DISCONNECTED"
          fi
        dest: "{{ ganuda_base }}/scripts/health_check.sh"
        owner: "{{ ganuda_user }}"
        mode: '0755'

    # ==================== CRON JOBS ====================
    - name: Add health check cron (Linux)
      cron:
        name: "Cherokee health check"
        minute: "*/5"
        job: "{{ ganuda_base }}/scripts/health_check.sh >> /var/log/ganuda/health.log 2>&1"
        user: "{{ ganuda_user }}"
      when: ansible_os_family == "Debian"

    # ==================== REGISTER WITH THERMAL MEMORY ====================
    - name: Register node in thermal memory
      command: >
        psql -h {{ postgres_host }} -U {{ postgres_user }} -d {{ postgres_db }} -c "
        INSERT INTO thermal_memory_archive (memory_hash, original_content, current_stage, temperature_score, sacred_pattern)
        VALUES (
          'NODE-BOOTSTRAP-{{ ansible_hostname }}-{{ ansible_date_time.date }}',
          'Node {{ ansible_hostname }} ({{ ansible_default_ipv4.address }}) bootstrapped via Ansible. OS: {{ ansible_distribution }} {{ ansible_distribution_version }}. Cherokee venv installed. Database connected.',
          'FRESH',
          95.0,
          true
        ) ON CONFLICT DO NOTHING;
        "
      become_user: "{{ ganuda_user }}"
      environment:
        PGPASSWORD: jawaseatlasers2

    # ==================== FINAL VERIFICATION ====================
    - name: Run health check
      command: "{{ ganuda_base }}/scripts/health_check.sh"
      become_user: "{{ ganuda_user }}"
      register: health_output

    - name: Display health check results
      debug:
        msg: "{{ health_output.stdout_lines }}"

  handlers:
    - name: restart ssh
      service:
        name: sshd
        state: restarted
```

## SSH Config Template

Create `/ganuda/home/dereadi/ansible/templates/ssh_config.j2`:

```jinja2
# Cherokee AI Federation - SSH Configuration
# Generated by Ansible: {{ ansible_date_time.date }}

Host redfin
    HostName 192.168.132.223
    User dereadi
    IdentityFile ~/.ssh/id_ed25519

Host bluefin
    HostName 192.168.132.222
    User dereadi
    IdentityFile ~/.ssh/id_ed25519

Host greenfin
    HostName 192.168.132.224
    User dereadi
    IdentityFile ~/.ssh/id_ed25519

Host sasass
    HostName 192.168.132.241
    User dereadi
    IdentityFile ~/.ssh/id_ed25519

Host sasass2
    HostName 192.168.132.242
    User dereadi
    IdentityFile ~/.ssh/id_ed25519

Host github.com
    HostName github.com
    User git
    IdentityFile ~/.ssh/ganuda_github
    IdentitiesOnly yes
```

## Usage

### Bootstrap a Single Node
```bash
cd /ganuda/home/dereadi/ansible
ansible-playbook -i inventory_federation.ini playbooks/bootstrap_node.yml --limit redfin -K
```

### Bootstrap All Linux Nodes
```bash
ansible-playbook -i inventory_federation.ini playbooks/bootstrap_node.yml --limit federation_linux -K
```

### Dry Run (Check Mode)
```bash
ansible-playbook -i inventory_federation.ini playbooks/bootstrap_node.yml --limit redfin --check
```

## Verification
```bash
# Check node can reach database
ssh dereadi@<node> "/ganuda/scripts/health_check.sh"

# Check thermal memory registration
PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -U claude -d zammad_production -c "
SELECT memory_hash, LEFT(original_content, 50), created_at 
FROM thermal_memory_archive 
WHERE memory_hash LIKE 'NODE-BOOTSTRAP%' 
ORDER BY created_at DESC;
"
```

## Success Criteria
- [ ] Playbook runs without errors
- [ ] /ganuda structure created
- [ ] Cherokee venv installed with packages
- [ ] Database connectivity verified
- [ ] Health check script working
- [ ] Cron job installed
- [ ] Node registered in thermal memory

---

FOR SEVEN GENERATIONS - Reproducible infrastructure ensures continuity.
