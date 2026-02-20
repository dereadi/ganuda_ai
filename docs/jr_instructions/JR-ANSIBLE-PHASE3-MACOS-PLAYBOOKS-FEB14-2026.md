# Jr Instruction: Ansible Phase 3 — macOS Playbooks

**Kanban**: #1755 (Phase 3 of 3)
**Story Points**: 5
**Council Vote**: #1bcd4a66217c3a21 (PROCEED, 0.89, unanimous)
**Priority**: 13 (RC-2026-02B)
**Dependencies**: Phase 1 (Foundation) must be complete
**Risk**: LOW — new files only

## Objective

Create macOS playbooks for sasass (M4 Max, MLX inference) and sasass2 (Munki server).
Handles Homebrew packages, launchd services, and Munki configuration.

## Step 1: Create macOS Deployment Playbook

Create `/ganuda/ansible/playbooks/deploy-macos.yml`

```yaml
---
# Cherokee AI Federation — macOS Node Configuration
# Run: ansible-playbook playbooks/deploy-macos.yml
- name: Configure macOS federation nodes
  hosts: macos
  become: no

  tasks:
    - name: Ensure Homebrew is available
      stat:
        path: /opt/homebrew/bin/brew
      register: brew_check

    - name: Install common packages via Homebrew
      community.general.homebrew:
        name: "{{ item }}"
        state: present
      loop: "{{ common_packages }}"
      when: brew_check.stat.exists

    - name: Ensure ganuda directory exists
      file:
        path: "{{ ganuda_base_path }}"
        state: directory
        owner: dereadi
        mode: "0755"

    - name: Ensure ganuda config directory exists
      file:
        path: "{{ ganuda_config_path }}"
        state: directory
        owner: dereadi
        mode: "0755"

    - name: Configure Munki client
      become: yes
      community.general.osx_defaults:
        domain: /Library/Preferences/ManagedInstalls
        key: SoftwareRepoURL
        type: string
        value: "{{ munki_repo_url }}"
      when: munki_client_enabled | default(false)

    - name: Set Munki client identifier
      become: yes
      community.general.osx_defaults:
        domain: /Library/Preferences/ManagedInstalls
        key: ClientIdentifier
        type: string
        value: "{{ hostname }}"
      when: munki_client_enabled | default(false)

- name: Configure sasass MLX services
  hosts: sasass
  become: yes

  tasks:
    - name: Deploy MLX DeepSeek launchd plist
      copy:
        dest: /Library/LaunchDaemons/com.cherokee.mlx-deepseek-r1.plist
        owner: root
        group: wheel
        mode: "0644"
        content: |
          <?xml version="1.0" encoding="UTF-8"?>
          <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
          <plist version="1.0">
          <dict>
            <key>Label</key>
            <string>com.cherokee.mlx-deepseek-r1</string>
            <key>ProgramArguments</key>
            <array>
              <string>/opt/homebrew/bin/python3</string>
              <string>-m</string>
              <string>mlx_lm.server</string>
              <string>--model</string>
              <string>mlx-community/DeepSeek-R1-Distill-Qwen-32B-4bit</string>
              <string>--port</string>
              <string>{{ mlx_deepseek_port }}</string>
            </array>
            <key>WorkingDirectory</key>
            <string>{{ ganuda_base_path }}</string>
            <key>RunAtLoad</key>
            <true/>
            <key>KeepAlive</key>
            <true/>
            <key>StandardOutPath</key>
            <string>/var/log/ganuda/mlx-deepseek.log</string>
            <key>StandardErrorPath</key>
            <string>/var/log/ganuda/mlx-deepseek.err</string>
            <key>EnvironmentVariables</key>
            <dict>
              <key>PATH</key>
              <string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin</string>
            </dict>
          </dict>
          </plist>
      notify: reload mlx deepseek

    - name: Ensure ganuda log directory exists
      file:
        path: /var/log/ganuda
        state: directory
        owner: dereadi
        mode: "0755"

    - name: Load MLX DeepSeek service
      command: launchctl load /Library/LaunchDaemons/com.cherokee.mlx-deepseek-r1.plist
      register: launchctl_result
      changed_when: launchctl_result.rc == 0
      ignore_errors: yes

  handlers:
    - name: reload mlx deepseek
      command: launchctl unload /Library/LaunchDaemons/com.cherokee.mlx-deepseek-r1.plist
      ignore_errors: yes
      notify: load mlx deepseek

    - name: load mlx deepseek
      command: launchctl load /Library/LaunchDaemons/com.cherokee.mlx-deepseek-r1.plist

- name: Configure sasass2 Munki server
  hosts: sasass2
  become: yes

  tasks:
    - name: Ensure Munki repo directory exists
      file:
        path: "{{ munki_repo_path }}"
        state: directory
        owner: dereadi
        mode: "0755"
      when: munki_server_enabled | default(false)

    - name: Ensure Munki repo subdirectories exist
      file:
        path: "{{ munki_repo_path }}/{{ item }}"
        state: directory
        owner: dereadi
        mode: "0755"
      loop:
        - pkgs
        - pkgsinfo
        - catalogs
        - manifests
        - icons
      when: munki_server_enabled | default(false)

    - name: Verify nginx is serving Munki repo
      uri:
        url: "http://localhost:{{ munki_server_port }}/catalogs/all"
        method: GET
        status_code: [200, 404]
      register: munki_check
      ignore_errors: yes
      when: munki_server_enabled | default(false)

    - name: Report Munki server status
      debug:
        msg: "Munki server at port {{ munki_server_port }}: {{ 'SERVING' if munki_check.status == 200 else 'NOT SERVING (run makecatalogs)' }}"
      when: munki_server_enabled | default(false) and munki_check is defined
```

## Step 2: Create Ansible Smoke Test Playbook

Create `/ganuda/ansible/playbooks/smoke-test.yml`

```yaml
---
# Cherokee AI Federation — Smoke Test All Nodes
# Run: ansible-playbook playbooks/smoke-test.yml
# Quick validation that all nodes are reachable and configured
- name: Federation smoke test
  hosts: all
  gather_facts: yes

  tasks:
    - name: Ping check
      ping:

    - name: Report basic info
      debug:
        msg: >-
          {{ inventory_hostname }} |
          OS: {{ ansible_distribution | default('unknown') }} {{ ansible_distribution_version | default('') }} |
          Python: {{ ansible_python_version | default('unknown') }} |
          RAM: {{ ansible_memtotal_mb | default('unknown') }}MB |
          Role: {{ node_role | default('unassigned') }}

    - name: Check ganuda directory
      stat:
        path: "{{ ganuda_base_path }}"
      register: ganuda_dir

    - name: Report ganuda status
      debug:
        msg: "{{ ganuda_base_path }}: {{ 'EXISTS' if ganuda_dir.stat.exists else 'MISSING' }}"

    - name: Check database connectivity (Linux only)
      command: "pg_isready -h {{ db_host | default('192.168.132.222') }} -p 5432"
      register: db_check
      changed_when: false
      ignore_errors: yes
      when: ansible_system == 'Linux'

    - name: Report database status
      debug:
        msg: "PostgreSQL: {{ db_check.stdout | default('N/A') }}"
      when: ansible_system == 'Linux'
```

## Manual Steps

After Jr execution:
```text
cd /ganuda/ansible
ansible-galaxy collection install -r requirements.yml
ansible-playbook playbooks/smoke-test.yml
```

The smoke test validates connectivity to all 5 nodes before running any changes.
