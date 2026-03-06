# Jr Instruction: Fix Promtail Agent Detection Pipeline

**Task**: Fix Promtail config on greenfin to properly detect and label agent log sources
**Priority**: 6
**Story Points**: 2
**Epic**: None (kanban #1895)

## Context

Promtail on greenfin (192.168.132.224) collects logs but the agent detection pipeline is misconfigured. The config at `/ganuda/home/dereadi/promtail/config/promtail.yaml` needs a pipeline stage to extract agent names from log lines.

Key log paths on greenfin:
- `/var/log/syslog` — system
- `/ganuda/logs/*.log` — federation services

Agent names appear in log lines as `[agent_name]` or `agent=name` patterns.

## Steps

### Step 1: Create the pipeline stage config snippet

Create `/ganuda/config/promtail-pipeline-agents.yaml`

```yaml
# Promtail pipeline stage for agent detection
# Merge into promtail.yaml scrape_configs[].pipeline_stages

pipeline_stages:
  - regex:
      expression: '\[(?P<agent>[A-Za-z_]+)\]'
  - labels:
      agent:
  - regex:
      expression: 'agent=(?P<agent_alt>[A-Za-z_]+)'
  - labels:
      agent_alt:
  - template:
      source: agent
      template: '{{ if .agent }}{{ .agent }}{{ else }}{{ .agent_alt }}{{ end }}'
```

## Verification

1. Config syntax: `promtail -config.file=/ganuda/config/promtail-pipeline-agents.yaml -check-syntax` (or validate YAML)
2. NOTE: Actual integration into promtail.yaml requires greenfin SSH — TPM will handle deployment
