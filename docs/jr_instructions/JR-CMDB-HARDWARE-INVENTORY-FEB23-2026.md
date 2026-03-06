# Jr Instruction: CMDB Hardware Inventory Ansible Playbook

**Kanban**: #1797
**Priority**: 3
**Story Points**: 5
**use_rlm**: false
**assigned_jr**: Software Engineer Jr.

---

## Overview

Create an Ansible playbook that gathers hardware inventory from all federation nodes (redfin, greenfin, bluefin, bmasass, owlfin, eaglefin) and outputs a structured YAML report. Uses ansible_facts for standard hardware info and shell commands for GPU detection since ansible_facts does not include GPU details. Supports both NVIDIA (nvidia-smi) on Linux nodes and Apple Silicon (system_profiler) on macOS nodes.

---

## Steps

### Step 1: Create the hardware inventory playbook

Create `/ganuda/ansible/playbooks/hardware-inventory.yml`

```yaml
---
# Hardware Inventory Playbook - Cherokee AI Federation
# Kanban #1797
#
# Usage:
#   ansible-playbook /ganuda/ansible/playbooks/hardware-inventory.yml -i /ganuda/ansible/inventory
#
# Output: /ganuda/reports/hardware-inventory.yml

- name: Gather Hardware Inventory from All Federation Nodes
  hosts: all
  gather_facts: true
  become: false

  tasks:
    - name: Detect NVIDIA GPU info (Linux nodes)
      shell: nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader 2>/dev/null || echo "no-nvidia-gpu"
      register: nvidia_gpu_info
      changed_when: false
      failed_when: false
      when: ansible_system == "Linux"

    - name: Detect Apple GPU info (macOS nodes)
      shell: system_profiler SPDisplaysDataType 2>/dev/null | grep -E '(Chipset Model|VRAM|Metal)' | sed 's/^[[:space:]]*//' || echo "no-apple-gpu"
      register: apple_gpu_info
      changed_when: false
      failed_when: false
      when: ansible_system == "Darwin"

    - name: Collect disk information
      shell: lsblk -d -o NAME,SIZE,TYPE,MODEL --noheadings 2>/dev/null || diskutil list 2>/dev/null | head -30 || echo "disk-info-unavailable"
      register: disk_info
      changed_when: false
      failed_when: false

    - name: Set GPU fact
      set_fact:
        gpu_info: >-
          {%- if ansible_system == "Linux" and nvidia_gpu_info.stdout is defined and nvidia_gpu_info.stdout != "no-nvidia-gpu" -%}
            {{ nvidia_gpu_info.stdout }}
          {%- elif ansible_system == "Darwin" and apple_gpu_info.stdout is defined and apple_gpu_info.stdout != "no-apple-gpu" -%}
            {{ apple_gpu_info.stdout }}
          {%- else -%}
            none detected
          {%- endif -%}

    - name: Build inventory entry
      set_fact:
        hw_inventory:
          hostname: "{{ ansible_hostname }}"
          fqdn: "{{ ansible_fqdn }}"
          ip_addresses: "{{ ansible_all_ipv4_addresses }}"
          os: "{{ ansible_distribution }} {{ ansible_distribution_version }}"
          kernel: "{{ ansible_kernel }}"
          architecture: "{{ ansible_architecture }}"
          cpu_model: "{{ ansible_processor[2] | default(ansible_processor[0]) }}"
          cpu_cores_physical: "{{ ansible_processor_cores | default('N/A') }}"
          cpu_cores_logical: "{{ ansible_processor_vcpus | default('N/A') }}"
          ram_total_mb: "{{ ansible_memtotal_mb }}"
          ram_free_mb: "{{ ansible_memfree_mb }}"
          swap_total_mb: "{{ ansible_swaptotal_mb }}"
          disk_info: "{{ disk_info.stdout_lines }}"
          gpu: "{{ gpu_info }}"
          uptime_seconds: "{{ ansible_uptime_seconds }}"
          python_version: "{{ ansible_python_version }}"

    - name: Debug inventory entry
      debug:
        var: hw_inventory

- name: Write consolidated inventory report
  hosts: localhost
  gather_facts: false
  connection: local

  tasks:
    - name: Ensure reports directory exists
      file:
        path: /ganuda/reports
        state: directory
        mode: "0755"

    - name: Write hardware inventory YAML
      copy:
        content: |
          ---
          # Cherokee AI Federation - Hardware Inventory
          # Generated: {{ lookup('pipe', 'date -Iseconds') }}
          # Playbook: /ganuda/ansible/playbooks/hardware-inventory.yml
          # Kanban: #1797

          nodes:
          {% for host in groups['all'] %}
            {{ host }}:
              {{ hostvars[host]['hw_inventory'] | to_nice_yaml(indent=2) | indent(4) }}
          {% endfor %}
        dest: /ganuda/reports/hardware-inventory.yml
        mode: "0644"

    - name: Report complete
      debug:
        msg: "Hardware inventory written to /ganuda/reports/hardware-inventory.yml"
```

---

## Verification

1. Confirm file exists at `/ganuda/ansible/playbooks/hardware-inventory.yml`
2. Validate YAML syntax: `python3 -c "import yaml; yaml.safe_load(open('/ganuda/ansible/playbooks/hardware-inventory.yml'))"`
3. Confirm playbook targets `hosts: all` and includes GPU detection for both Linux (nvidia-smi) and macOS (system_profiler)
4. Confirm output path is `/ganuda/reports/hardware-inventory.yml`
5. Confirm no `become: true` is set at play level (GPU commands do not require root)
