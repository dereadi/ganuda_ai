# Jr Instruction: Self-Healing Phase 1 — Alert Bridge + NOTIFY Infrastructure

**Kanban**: #1781 (Phase 1 of 4)
**Story Points**: 3
**Council Vote**: #1872d8f580eaec28 (PROCEED WITH CAUTION, 0.874)
**Priority**: 14 (RC-2026-02B)
**Dependencies**: Ansible Phase 1 Foundation must be complete (DONE)
**Risk**: LOW — new files only, no modifications to existing code

## Objective

Create the PostgreSQL NOTIFY trigger that fires when high-temperature thermal memories
are written, and the Event-Driven Ansible (EDA) rulebook that listens on this channel
and dispatches alerts to the remediation engine.

## Step 1: Create PostgreSQL NOTIFY Trigger SQL

Create `/ganuda/scripts/sql/create_federation_alerts_trigger.sql`

```sql
-- Cherokee AI Federation — Alert Bridge
-- Fires PostgreSQL NOTIFY on 'federation_alerts' channel
-- when thermal memories with temperature_score >= 0.8 are inserted.
-- This is the bridge between Eagle Eye detection and EDA remediation.
--
-- Deploy: psql -h 192.168.132.222 -U claude -d zammad_production -f create_federation_alerts_trigger.sql

-- Function that sends NOTIFY with alert payload
CREATE OR REPLACE FUNCTION notify_federation_alert()
RETURNS TRIGGER AS $$
DECLARE
    alert_payload JSON;
BEGIN
    -- Only fire for high-temperature events (anomalies, failures, critical)
    IF NEW.temperature_score >= 0.8 THEN
        alert_payload := json_build_object(
            'id', NEW.id,
            'temperature', NEW.temperature_score,
            'content_preview', LEFT(NEW.original_content, 200),
            'sacred', NEW.sacred_pattern,
            'created_at', NEW.created_at,
            'memory_hash', NEW.memory_hash
        );
        PERFORM pg_notify('federation_alerts', alert_payload::text);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Attach trigger to thermal_memory_archive
DROP TRIGGER IF EXISTS trg_federation_alert ON thermal_memory_archive;
CREATE TRIGGER trg_federation_alert
    AFTER INSERT ON thermal_memory_archive
    FOR EACH ROW
    EXECUTE FUNCTION notify_federation_alert();

-- Verify trigger exists
SELECT tgname, tgrelid::regclass, tgenabled
FROM pg_trigger
WHERE tgname = 'trg_federation_alert';
```

## Step 2: Create EDA Rulebook for Federation Alerts

Create `/ganuda/ansible/rulebooks/federation_alerts.yml`

```yaml
---
# Cherokee AI Federation — Event-Driven Ansible Rulebook
# Listens on PostgreSQL NOTIFY channel 'federation_alerts'
# and dispatches to the remediation engine.
#
# Run: ansible-rulebook --rulebook rulebooks/federation_alerts.yml -i rulebooks/inventory.yml
#
# Requires: pip install ansible-rulebook psycopg2-binary

- name: Federation Self-Healing Alert Handler
  hosts: all
  sources:
    - ansible.eda.pg_listener:
        host: 192.168.132.222
        port: 5432
        dbname: zammad_production
        user: claude
        channels:
          - federation_alerts

  rules:
    - name: High-temperature alert — service failure pattern
      condition: event.payload.temperature >= 0.9
      action:
        run_playbook:
          name: remediation/triage_alert.yml
          extra_vars:
            alert_id: "{{ event.payload.id }}"
            alert_content: "{{ event.payload.content_preview }}"
            alert_temperature: "{{ event.payload.temperature }}"
            alert_sacred: "{{ event.payload.sacred }}"
            severity: critical

    - name: Elevated alert — config drift or degradation
      condition: event.payload.temperature >= 0.8 and event.payload.temperature < 0.9
      action:
        run_playbook:
          name: remediation/triage_alert.yml
          extra_vars:
            alert_id: "{{ event.payload.id }}"
            alert_content: "{{ event.payload.content_preview }}"
            alert_temperature: "{{ event.payload.temperature }}"
            alert_sacred: "{{ event.payload.sacred }}"
            severity: elevated
```

## Step 3: Create EDA Inventory File

Create `/ganuda/ansible/rulebooks/inventory.yml`

```yaml
---
# EDA-specific inventory — points to the same federation nodes
# but used by ansible-rulebook context
all:
  children:
    linux:
      hosts:
        redfin:
          ansible_host: 192.168.132.223
        bluefin:
          ansible_host: 192.168.132.222
        greenfin:
          ansible_host: 192.168.132.224
    macos:
      hosts:
        sasass:
          ansible_host: 192.168.132.21
```

## Step 4: Create Triage Alert Playbook Stub

Create `/ganuda/ansible/remediation/triage_alert.yml`

```yaml
---
# Cherokee AI Federation — Alert Triage
# Called by EDA rulebook when federation_alerts fires.
# Classifies the alert and invokes the remediation engine.
#
# This playbook runs on localhost (redfin) and calls the
# Python remediation engine to generate a response playbook.
- name: Triage federation alert
  hosts: localhost
  connection: local
  gather_facts: no

  tasks:
    - name: Log alert receipt
      debug:
        msg: >-
          ALERT RECEIVED | ID: {{ alert_id }}
          | Severity: {{ severity }}
          | Temperature: {{ alert_temperature }}
          | Sacred: {{ alert_sacred }}
          | Preview: {{ alert_content | truncate(100) }}

    - name: Invoke remediation engine
      command: >
        /ganuda/amem_venv/bin/python
        /ganuda/ansible/remediation/engine.py
        --alert-id "{{ alert_id }}"
        --severity "{{ severity }}"
        --content "{{ alert_content }}"
      register: engine_result
      ignore_errors: yes

    - name: Report engine result
      debug:
        msg: "Remediation engine returned: {{ engine_result.stdout | default('no output') }}"

    - name: Log failure if engine errored
      debug:
        msg: "ENGINE FAILED: {{ engine_result.stderr }}"
      when: engine_result.rc != 0
```

## Manual Steps

On bluefin (PostgreSQL host):
```text
psql -U claude -d zammad_production -f /ganuda/scripts/sql/create_federation_alerts_trigger.sql
```

On redfin:
```text
pip install ansible-rulebook psycopg2-binary
mkdir -p /ganuda/ansible/remediation
mkdir -p /ganuda/ansible/rulebooks
```
