# ULTRATHINK: Cluster & Infrastructure Enhancement

**Date:** January 29, 2026
**Author:** TPM Claude
**Council Vote:** 7-0 APPROVE (unanimous)
**Status:** Implementation Ready

---

## Executive Summary

The 7-Specialist Council unanimously approved infrastructure enhancements addressing:
1. 15 failed Jr tasks (protected paths)
2. No self-healing automation
3. Limited per-node visibility

---

## Council Deliberation

| Specialist | Vote | Key Points |
|------------|------|------------|
| Peace Chief | APPROVE | Enhances reliability and observability |
| Raven | APPROVE | Addresses task failures and self-healing |
| Crawdad | APPROVE | Improves cluster reliability and efficiency |
| Spider | APPROVE | Path protection and enhanced monitoring |
| Eagle Eye | APPROVE | Significantly improves reliability |
| Gecko | APPROVE | Improves overall reliability and efficiency |
| Turtle | APPROVE | Improves reliability and security |

**Consensus:** All tools address critical issues. Implement in priority order.

---

## Priority Implementation Plan

### Phase 1: Jr Sandbox Layer (P0) - Fixes 15 Failed Tasks

**Problem:** Jrs can't write to protected paths, tasks fail even with correct code.

**Solution:** Staging directory pattern with TPM approval workflow.

```
┌─────────────────────────────────────────────────────────────┐
│                    Jr Task Execution                         │
│                          │                                   │
│                          ▼                                   │
│    ┌─────────────────────────────────────────────────────┐  │
│    │            Staging Directory                         │  │
│    │         /ganuda/staging/{task_id}/                   │  │
│    │                                                       │  │
│    │  Jr writes here freely:                              │  │
│    │  - /ganuda/staging/abc123/telegram_bot/chunker.py    │  │
│    │  - /ganuda/staging/abc123/services/worker.py         │  │
│    └─────────────────────────────────────────────────────┘  │
│                          │                                   │
│                          ▼                                   │
│    ┌─────────────────────────────────────────────────────┐  │
│    │            TPM Review Queue                          │  │
│    │                                                       │  │
│    │  - Diff against production                           │  │
│    │  - Security scan                                     │  │
│    │  - Auto-approve if low-risk                          │  │
│    │  - Manual review if high-risk                        │  │
│    └─────────────────────────────────────────────────────┘  │
│                          │                                   │
│                          ▼                                   │
│              Merge to /ganuda/ (production)                  │
└─────────────────────────────────────────────────────────────┘
```

**Files to Create:**
- `/ganuda/lib/staging_manager.py` - Manages staging directories
- `/ganuda/jr_executor/staging_writer.py` - Jr writes to staging
- `/ganuda/scripts/merge_staging.py` - TPM approves and merges

### Phase 2: Keep AIOps Integration (P0) - Self-Healing

**Problem:** Manual intervention required for service restarts, Jr retries.

**Solution:** Keep workflows for automated remediation.

```yaml
# /ganuda/config/keep/workflows/service-restart.yaml
workflow:
  id: auto-restart-crashed-service
  triggers:
    - type: alert
      filters:
        - key: alertname
          value: ServiceDown
  actions:
    - name: restart-service
      provider:
        type: ssh
        config:
          host: "{{ alert.labels.host }}"
          command: "sudo systemctl restart {{ alert.labels.service }}"
    - name: notify-tpm
      provider:
        type: telegram
        with:
          chat_id: "-1003439875431"
          message: "🔧 Auto-restarted {{ alert.labels.service }} on {{ alert.labels.host }}"
```

**Deployment:**
```bash
docker run -d --name keep \
  -p 3001:3000 \
  -e KEEP_DATABASE_URL=postgresql://claude:jawaseatlasers2@192.168.132.222/keep \
  -v /ganuda/config/keep:/keep/config \
  keephq/keep
```

### Phase 3: Netdata Per-Node Agents (P1)

**Problem:** Limited visibility into individual node health.

**Solution:** Netdata agents on all 6 nodes reporting to central dashboard.

```bash
# Deploy on each node
curl https://get.netdata.cloud/kickstart.sh > /tmp/netdata-install.sh
bash /tmp/netdata-install.sh --dont-wait

# Configure to stream to central
cat >> /etc/netdata/stream.conf << EOF
[stream]
  enabled = yes
  destination = 192.168.132.222:19999
  api key = cherokee-ai-federation-2026
EOF
```

**Nodes:**
| Node | IP | Role |
|------|-----|------|
| redfin | 192.168.132.223 | GPU Server |
| bluefin | 192.168.132.222 | Database (central) |
| greenfin | 192.168.132.224 | Daemons |
| sasass | 192.168.132.241 | Mac Studio |
| silverfin | TBD | Secrets |
| goldfin | TBD | PII Vault |

### Phase 4: claude-flow Evaluation (P2)

**Consider for:**
- Enhanced Jr orchestration
- 175+ MCP tools integration
- Self-learning from successful executions

**Evaluation criteria:**
1. Does it improve Jr success rate?
2. Does it reduce TPM intervention?
3. Resource requirements acceptable?

### Phase 5: Coroot APM (P2)

**Consider for:**
- AI-powered root cause analysis
- SLO-based alerting
- Replaces/enhances health_monitor.py

---

## Implementation JRs

| JR ID | Title | Priority | Assigned |
|-------|-------|----------|----------|
| JR-STAGING-MANAGER-JAN29-2026 | Jr Staging Directory Manager | P0 | Software Engineer Jr. |
| JR-KEEP-AIOPS-INTEGRATION-JAN29-2026 | Keep AIOps Self-Healing | P0 | Infrastructure Jr. |
| JR-NETDATA-DEPLOYMENT-JAN29-2026 | Netdata Per-Node Agents | P1 | Infrastructure Jr. |

---

## Success Metrics

1. **Jr Task Success Rate:** From ~50% → 95% (with staging)
2. **MTTR (Mean Time to Recovery):** From manual → automatic (<60s)
3. **Node Visibility:** 6/6 nodes with real-time metrics
4. **Alert Noise:** Deduplicated and correlated via Keep

---

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| Staging adds latency | Auto-approve low-risk changes |
| Keep adds complexity | Start with 2-3 simple workflows |
| Netdata resource usage | Monitor and tune if needed |

---

## Sources

- [Keep AIOps](https://github.com/keephq/keep)
- [Arrakis Sandbox](https://github.com/abshkbh/arrakis)
- [Netdata](https://github.com/netdata/netdata)
- [claude-flow](https://github.com/ruvnet/claude-flow)
- [Coroot](https://github.com/coroot/coroot)

---

FOR SEVEN GENERATIONS
