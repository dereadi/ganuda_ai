# Jr Build Instructions: Tribe Configuration Registry

**Priority**: HIGH
**Phase**: 3 - Hardening & Packaging
**Assigned To**: Executive Jr / IT Triad Jr
**Date**: December 13, 2025

## Objective

The **Tribe Configuration Registry** is a unified source of truth for all Tribe-managed configurations. It enables any LLM (Executive Jr, IT Jr, etc.) to recall any setting, service, playbook, or cron job that the Tribe controls.

## Why This Matters

Before this registry, knowledge was scattered:
- Ansible playbooks in `/ganuda/home/dereadi/ansible/`
- Systemd services on each node
- Cron jobs on bluefin/redfin
- Software CMDB in separate tables
- Thermal memory (unstructured)

Now, any Jr can ask: *"How do I patch redfin?"* and get the exact command.

## Database Table

### tribe_config_registry

```sql
SELECT * FROM tribe_config_registry LIMIT 5;
```

Key columns:
| Column | Purpose |
|--------|---------|
| config_name | Unique identifier |
| config_type | service, cron, script, playbook, database, api_endpoint |
| hostname | Which node (redfin, bluefin, greenfin) |
| file_path | Where it lives on disk |
| start/stop/restart_command | How to manage services |
| ansible_playbook | Which playbook manages this |
| schedule_cron | Cron schedule (e.g., `33 3 * * *`) |
| depends_on | What this depends on |
| manages | What tables/resources this controls |
| tags | Searchable tags |

## Lookup Functions

### 1. Search by Keyword

```sql
SELECT * FROM tribe_config_search('pheromone');
```

Returns configs matching the keyword with relevance score.

### 2. Get Full Config Details

```sql
SELECT * FROM tribe_config_get('llm-gateway');
```

Returns all details for a specific config.

### 3. What Runs on a Node?

```sql
SELECT * FROM tribe_config_by_node('redfin');
SELECT * FROM tribe_config_by_node('bluefin');
```

### 4. Get by Type

```sql
SELECT * FROM tribe_config_by_type('playbook');
SELECT * FROM tribe_config_by_type('cron');
SELECT * FROM tribe_config_by_type('service');
```

### 5. How to Manage Something

```sql
SELECT * FROM tribe_how_to_manage('llm-gateway');
```

Returns:
```
 action  |                   command                   |   note
---------+---------------------------------------------+-----------
 start   | sudo systemctl start llm-gateway            | On redfin
 stop    | sudo systemctl stop llm-gateway             | On redfin
 restart | sudo systemctl restart llm-gateway          | On redfin
 status  | systemctl status llm-gateway                | On redfin
 health  | curl -s http://localhost:8080/health | jq . | On redfin
```

### 6. Natural Language Questions

```sql
SELECT * FROM tribe_answer_question('How do I patch redfin?');
SELECT * FROM tribe_answer_question('What manages thermal memory decay?');
SELECT * FROM tribe_answer_question('What runs on a schedule?');
```

### 7. Dependencies

```sql
SELECT * FROM tribe_config_dependencies('llm-gateway');
```

## Current Registry Contents

### Services (7)
| Config | Node | Criticality |
|--------|------|-------------|
| llm-gateway | redfin | critical |
| vllm | redfin | critical |
| postgresql | bluefin | critical |
| grafana | bluefin | high |
| executive-jr-autonomic | redfin | high |
| it-triad | redfin | medium |
| ganuda-heartbeat | redfin | medium |

### Cron Jobs (3)
| Config | Schedule | Description |
|--------|----------|-------------|
| pheromone-decay | 33 3 * * * | Daily thermal memory decay |
| fse-key-decay | 33 4 * * * | Daily FSE key strength decay |
| health-check-cron | */5 * * * * | 5-minute health checks |

### Playbooks (4)
| Config | Playbook |
|--------|----------|
| ansible-patch-nodes | patch_nodes.yml |
| ansible-patch-intelligent | patch_nodes_intelligent.yml |
| ansible-reboot-node | reboot_node.yml |
| ansible-bootstrap-node | bootstrap_node.yml |

### API Endpoints (4)
| Config | Port | Description |
|--------|------|-------------|
| api-chat-completions | 8080 | OpenAI-compatible chat |
| api-council-vote | 8080 | Council voting |
| api-models | 8080 | List models |
| sag-ui | 4000 | ITSM frontend |

### Database Components (9)
- thermal-memory-archive
- council-votes
- breadcrumb-trails
- software-cmdb
- multi-tenant-namespaces
- api-keys
- func-can-auto-patch-node
- func-check-namespace-access
- func-calculate-fse-strength

## Adding New Configurations

When deploying something new, register it:

```sql
INSERT INTO tribe_config_registry (
    config_name, config_type, description, hostname, file_path, port,
    start_command, stop_command, restart_command, status_command,
    depends_on, manages, owner, criticality, tags
) VALUES (
    'new-service', 'service', 'Description of what it does',
    'redfin', '/ganuda/services/new_service/', 9000,
    'sudo systemctl start new-service',
    'sudo systemctl stop new-service',
    'sudo systemctl restart new-service',
    'systemctl status new-service',
    ARRAY['postgresql'], ARRAY['some_table'],
    'tribe', 'medium', ARRAY['tag1', 'tag2']
);
```

## Executive Jr Integration

Executive Jr should query this registry before taking action:

```python
# Before patching
result = await db.fetch("SELECT * FROM tribe_answer_question('How do I patch redfin?')")

# Before managing a service
result = await db.fetch("SELECT * FROM tribe_how_to_manage('llm-gateway')")

# Find what controls something
result = await db.fetch("SELECT * FROM tribe_config_search('thermal')")
```

## Maintenance

### Verify Registry is Current

```sql
SELECT config_name, last_verified,
       CASE WHEN last_verified < now() - interval '7 days' THEN 'STALE' ELSE 'OK' END as status
FROM tribe_config_registry
ORDER BY last_verified NULLS FIRST;
```

### Update Last Verified

```sql
UPDATE tribe_config_registry
SET last_verified = now()
WHERE config_name = 'llm-gateway';
```

### Find Orphaned Configs

```sql
-- Configs that might be removed
SELECT config_name, config_type, hostname, description
FROM tribe_config_registry
WHERE last_verified < now() - interval '30 days'
   OR last_verified IS NULL;
```

---

FOR SEVEN GENERATIONS - Unified knowledge enables autonomous operation.
