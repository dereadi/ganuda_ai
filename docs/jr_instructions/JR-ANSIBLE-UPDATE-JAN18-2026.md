# JR Instruction: Ansible Infrastructure Update

## Metadata
```yaml
task_id: ansible_update_jan18
priority: 2
assigned_to: it_triad_jr
estimated_effort: medium
category: infrastructure
```

## Overview

Update Ansible inventory and create playbooks for new services deployed in January 2026.

## BACKEND LOCATION: /ganuda/home/dereadi/ansible

## Current State

| Item | Status |
|------|--------|
| Inventory | Missing goldfin, silverfin |
| Jr Executor | No deployment playbook |
| VetAssist | No deployment playbook |
| Service Health | Missing new services |

## MODIFY FILE: inventory_federation.ini

Add new nodes:
```ini
[federation_linux]
bluefin ansible_host=192.168.132.222 ansible_user=dereadi
redfin ansible_host=192.168.132.223 ansible_user=dereadi
greenfin ansible_host=192.168.132.224 ansible_user=dereadi
goldfin ansible_host=192.168.132.225 ansible_user=dereadi
silverfin ansible_host=192.168.132.226 ansible_user=dereadi
```

## CREATE FILE: playbooks/deploy_jr_executor.yml

```yaml
---
# Deploy Jr Executor services to redfin
# Cherokee AI Federation

- name: Deploy Jr Executor
  hosts: redfin
  become: yes
  vars:
    ganuda_base: /ganuda
    venv_path: /home/dereadi/cherokee_venv

  tasks:
    - name: Ensure ganuda directories exist
      file:
        path: "{{ item }}"
        state: directory
        owner: dereadi
        group: dereadi
        mode: '0755'
      loop:
        - "{{ ganuda_base }}/jr_executor"
        - "{{ ganuda_base }}/lib"
        - "{{ ganuda_base }}/logs"

    - name: Copy Jr executor files
      copy:
        src: "{{ ganuda_base }}/jr_executor/"
        dest: "{{ ganuda_base }}/jr_executor/"
        owner: dereadi
        group: dereadi
        mode: '0644'

    - name: Copy Jr library files
      copy:
        src: "{{ ganuda_base }}/lib/"
        dest: "{{ ganuda_base }}/lib/"
        owner: dereadi
        group: dereadi
        mode: '0644'

    - name: Install Python dependencies
      pip:
        name:
          - aiohttp
          - psycopg2-binary
          - pydantic
        virtualenv: "{{ venv_path }}"
        state: present

    - name: Deploy systemd service
      template:
        src: templates/jr-queue-worker.service.j2
        dest: /etc/systemd/system/jr-queue-worker.service
        mode: '0644'
      notify: Reload systemd

    - name: Enable and start Jr queue worker
      systemd:
        name: jr-queue-worker
        enabled: yes
        state: started

  handlers:
    - name: Reload systemd
      systemd:
        daemon_reload: yes
```

## CREATE FILE: templates/jr-queue-worker.service.j2

```ini
[Unit]
Description=Cherokee AI Jr Queue Worker
After=network.target postgresql.service

[Service]
Type=simple
User=dereadi
Group=dereadi
WorkingDirectory=/ganuda/jr_executor
Environment="PATH=/home/dereadi/cherokee_venv/bin:/usr/bin"
ExecStart=/home/dereadi/cherokee_venv/bin/python jr_queue_worker.py it_triad_jr
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

## CREATE FILE: playbooks/deploy_vetassist.yml

```yaml
---
# Deploy VetAssist backend to redfin
# Cherokee AI Federation

- name: Deploy VetAssist Backend
  hosts: redfin
  become: yes
  vars:
    vetassist_base: /ganuda/vetassist

  tasks:
    - name: Ensure VetAssist directories
      file:
        path: "{{ item }}"
        state: directory
        owner: dereadi
        group: dereadi
        mode: '0755'
      loop:
        - "{{ vetassist_base }}/backend"
        - "{{ vetassist_base }}/backend/app"
        - "{{ vetassist_base }}/backend/app/api"
        - "{{ vetassist_base }}/frontend"

    - name: Install VetAssist Python dependencies
      pip:
        name:
          - fastapi
          - uvicorn
          - sqlalchemy
          - presidio-analyzer
          - presidio-anonymizer
        virtualenv: /home/dereadi/cherokee_venv
        state: present

    - name: Deploy VetAssist systemd service
      template:
        src: templates/vetassist-backend.service.j2
        dest: /etc/systemd/system/vetassist-backend.service
        mode: '0644'
      notify: Reload systemd

  handlers:
    - name: Reload systemd
      systemd:
        daemon_reload: yes
```

## SQL: Add service_health entries

```sql
-- Add monitoring for new services
INSERT INTO service_health (node_name, service_name, status, last_check)
VALUES
('redfin', 'Jr Queue Worker', 'unknown', NOW()),
('redfin', 'VetAssist Backend', 'unknown', NOW()),
('goldfin', 'PostgreSQL PII', 'unknown', NOW()),
('silverfin', 'FreeIPA', 'unknown', NOW())
ON CONFLICT DO NOTHING;
```

## Success Criteria

1. Ansible inventory includes all 6 nodes
2. Jr executor deployment playbook tested
3. VetAssist deployment playbook tested
4. Service health entries for new services

## Testing

```bash
cd /ganuda/home/dereadi/ansible
ansible-playbook -i inventory_federation.ini playbooks/deploy_jr_executor.yml --check
```

---
Cherokee AI Federation - For Seven Generations
