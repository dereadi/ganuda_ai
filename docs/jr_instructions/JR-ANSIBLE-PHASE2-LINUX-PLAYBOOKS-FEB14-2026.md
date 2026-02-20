# Jr Instruction: Ansible Phase 2 — Linux Playbooks

**Kanban**: #1755 (Phase 2 of 3)
**Story Points**: 8
**Council Vote**: #1bcd4a66217c3a21 (PROCEED, 0.89, unanimous)
**Priority**: 13 (RC-2026-02B)
**Dependencies**: Phase 1 (Foundation) must be complete
**Risk**: LOW — new files only, uses host_vars from Phase 1

## Objective

Create the core Linux playbooks: federation sync, service deployment, and firewall management
for redfin, bluefin, and greenfin.

## Step 1: Create Federation Sync Playbook

Create `/ganuda/ansible/playbooks/sync-federation.yml`

```yaml
---
# Cherokee AI Federation — Sync common files and packages across Linux nodes
# Run: ansible-playbook playbooks/sync-federation.yml
- name: Sync federation common configuration
  hosts: linux
  become: yes

  tasks:
    - name: Ensure common packages installed
      apt:
        name: "{{ common_packages }}"
        state: present
        update_cache: yes
        cache_valid_time: 3600

    - name: Ensure ganuda directory exists
      file:
        path: "{{ ganuda_base_path }}"
        state: directory
        owner: dereadi
        group: dereadi
        mode: "0755"

    - name: Ensure log directory exists
      file:
        path: /var/log/ganuda
        state: directory
        owner: dereadi
        group: dereadi
        mode: "0755"

    - name: Sync ganuda config directory
      synchronize:
        src: "{{ ganuda_config_path }}/"
        dest: "{{ ganuda_config_path }}/"
        rsync_opts:
          - "--include=*.yml"
          - "--include=*.yaml"
          - "--include=*.conf"
          - "--exclude=*"
      delegate_to: "{{ inventory_hostname }}"
      when: inventory_hostname != 'redfin'

    - name: Ensure fail2ban is configured
      copy:
        src: "{{ ganuda_config_path }}/fail2ban-action-telegram.conf"
        dest: /etc/fail2ban/action.d/telegram.conf
        owner: root
        group: root
        mode: "0644"
        remote_src: yes
      notify: restart fail2ban
      when: fail2ban_enabled | default(true)

    - name: Enable fail2ban
      systemd:
        name: fail2ban
        enabled: yes
        state: started
      when: fail2ban_enabled | default(true)

  handlers:
    - name: restart fail2ban
      systemd:
        name: fail2ban
        state: restarted
```

## Step 2: Create Service Deployment Playbook

Create `/ganuda/ansible/playbooks/deploy-services.yml`

```yaml
---
# Cherokee AI Federation — Deploy systemd services per node
# Run: ansible-playbook playbooks/deploy-services.yml
# Run for specific node: ansible-playbook playbooks/deploy-services.yml --limit redfin
- name: Deploy federation systemd services
  hosts: linux
  become: yes

  tasks:
    - name: Find service files for this node
      find:
        paths: "{{ ganuda_services_path }}"
        patterns: "*.service,*.timer"
      register: service_files

    - name: Build list of services to deploy
      set_fact:
        services_to_deploy: >-
          {{ service_files.files | selectattr('path', 'search', item + '\\.') | list }}
      loop: "{{ managed_services | default([]) }}"
      register: service_matches

    - name: Deploy service files
      copy:
        src: "{{ ganuda_services_path }}/{{ item }}.service"
        dest: "/etc/systemd/system/{{ item }}.service"
        owner: root
        group: root
        mode: "0644"
        remote_src: yes
      loop: "{{ managed_services | default([]) }}"
      register: services_deployed
      ignore_errors: yes
      notify: reload systemd

    - name: Deploy timer files (if they exist)
      copy:
        src: "{{ ganuda_services_path }}/{{ item }}.timer"
        dest: "/etc/systemd/system/{{ item }}.timer"
        owner: root
        group: root
        mode: "0644"
        remote_src: yes
      loop: "{{ managed_services | default([]) }}"
      ignore_errors: yes
      notify: reload systemd

    - name: Reload systemd daemon
      systemd:
        daemon_reload: yes
      when: services_deployed.changed | default(false)

    - name: Enable and start services
      systemd:
        name: "{{ item }}.service"
        enabled: yes
        state: started
      loop: "{{ managed_services | default([]) }}"
      ignore_errors: yes

    - name: Report service status
      command: "systemctl is-active {{ item }}.service"
      loop: "{{ managed_services | default([]) }}"
      register: service_status
      changed_when: false
      ignore_errors: yes

    - name: Show service status summary
      debug:
        msg: "{{ item.item }}: {{ item.stdout | default('unknown') }}"
      loop: "{{ service_status.results }}"
      when: service_status is defined

  handlers:
    - name: reload systemd
      systemd:
        daemon_reload: yes
```

## Step 3: Create Firewall Deployment Playbook

Create `/ganuda/ansible/playbooks/deploy-firewall.yml`

```yaml
---
# Cherokee AI Federation — Deploy nftables firewall rules to Linux nodes
# Run: ansible-playbook playbooks/deploy-firewall.yml
# WARNING: This modifies firewall rules. Test with --check first.
- name: Deploy nftables firewall configuration
  hosts: linux
  become: yes

  tasks:
    - name: Ensure nftables is installed
      apt:
        name: nftables
        state: present

    - name: Check if nftables config exists for this node
      stat:
        path: "{{ ganuda_config_path }}/{{ nftables_config | default('') }}"
      register: nft_config_check
      when: nftables_config is defined

    - name: Deploy nftables ruleset
      copy:
        src: "{{ ganuda_config_path }}/{{ nftables_config }}"
        dest: /etc/nftables.conf
        owner: root
        group: root
        mode: "0644"
        remote_src: yes
        backup: yes
      when:
        - nftables_config is defined
        - nft_config_check.stat.exists | default(false)
      notify: restart nftables

    - name: Enable nftables service
      systemd:
        name: nftables
        enabled: yes
        state: started

    - name: Verify active ruleset
      command: nft list ruleset
      register: nft_output
      changed_when: false

    - name: Show active rules count
      debug:
        msg: "{{ inventory_hostname }}: {{ nft_output.stdout_lines | length }} lines in active ruleset"

  handlers:
    - name: restart nftables
      systemd:
        name: nftables
        state: restarted
```

## Step 4: Create Site-wide Orchestration Playbook

Create `/ganuda/ansible/playbooks/site.yml`

```yaml
---
# Cherokee AI Federation — Master Site Playbook
# Runs all playbooks in correct order across all nodes
# Run: ansible-playbook playbooks/site.yml
# Run dry: ansible-playbook playbooks/site.yml --check

- name: "Phase 1: Sync federation common config"
  import_playbook: sync-federation.yml

- name: "Phase 2: Deploy firewall rules"
  import_playbook: deploy-firewall.yml

- name: "Phase 3: Deploy services"
  import_playbook: deploy-services.yml
```

## Manual Steps

After Jr execution, on any node with Ansible installed:
```text
cd /ganuda/ansible
ansible-playbook playbooks/site.yml --check --diff
```

Review the dry-run output before applying. The --check flag prevents any actual changes.
