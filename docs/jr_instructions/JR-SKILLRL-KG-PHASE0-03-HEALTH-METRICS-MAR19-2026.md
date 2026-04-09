# Jr Instruction: SkillRL KG Phase 0 — Knowledge Graph Health Metrics

**Epic**: SKILLRL-EPIC (Phase 0: KG Formalization)
**Council Vote**: #8984 (0.87, APPROVED 7-1)
**Estimated SP**: 1
**Depends On**: JR-SKILLRL-KG-PHASE0-02 (edge population must be running to have meaningful metrics)
**Academic Basis**: Princeton "Alternative Trajectory for Generative AI" — KG health is measurable. Thermalized as #129586.
**Kanban**: task_id 383d4e33

---

## Objective

Create a KG health report script that runs in dawn mist. We need to know if the graph is growing, if edges are forming, and if the three-signal reward is distributing properly. Without observability, KG formalization is a black box — and Coyote will (rightly) kill it.

## Design

### File: `/ganuda/scripts/kg_health_report.py`

Output a structured report suitable for dawn mist / Slack / thermal archival:

```
═══ Knowledge Graph Health Report ═══
Nodes:     92,867 thermals (76,751 with embeddings, 82.7%)
Edges:     147 relationships (3 types)
Density:   0.0016 edges/node
Growth:    +23 edges in last 24h

Edge Type Distribution:
  semantically_related:  89 (60.5%)
  shares_topic:          41 (27.9%)
  same_session:          17 (11.6%)

Reward Signal Distribution (last 7 days):
  Validity:   μ=0.72, σ=0.18  (n=34 tasks)
  Continuity: μ=0.65, σ=0.22
  Grounding:  μ=0.81, σ=0.12
  Composite:  μ=0.73, σ=0.14

Disconnected Nodes: 91,412 (98.4%) — expected until backfill
Sacred Nodes:       312 (excluded from Jr context)
═══════════════════════════════════════
```

### Metrics to Compute

1. **Node count**: `SELECT COUNT(*) FROM thermal_memory_archive`
2. **Embedding coverage**: `SELECT COUNT(*) FROM thermal_memory_archive WHERE embedding IS NOT NULL`
3. **Edge count**: `SELECT COUNT(*) FROM thermal_relationships` (active only if view exists)
4. **Edge type distribution**: `GROUP BY relationship_type`
5. **Edge density**: edges / nodes
6. **24h edge growth**: `WHERE created_at > NOW() - INTERVAL '24 hours'`
7. **Disconnected nodes**: nodes with zero edges (not in source_memory_id or target_memory_id)
8. **Sacred node count**: `WHERE is_sacred = true OR sacred_pattern = true`
9. **Reward signal distribution**: Query `skill_usage_log.metadata` JSONB for signal values from last 7 days — only available after KG-PHASE0-01 is deployed
10. **Confidence distribution on edges**: `AVG(confidence), STDDEV(confidence)` from thermal_relationships

### Graceful Degradation

- If `skill_usage_log` has no JSONB signal data yet (Phase 0-01 not deployed): skip reward section, print "Reward signals: awaiting KG-PHASE0-01 deployment"
- If `thermal_relationships` is empty: report zeros, don't error
- If `active_thermal_relationships` view doesn't exist: query base table with WHERE clause

### Integration

- Add to dawn mist timer (`council-dawn-mist.timer`, runs daily 6:15 AM)
- Import and call from dawn mist script, append output to dawn mist report
- Also callable standalone: `python3 /ganuda/scripts/kg_health_report.py`
- Output goes to stdout (for dawn mist capture) AND thermalizes the report (temp 30, domain_tag 'kg_health', source_triad 'tpm')

## Steps

1. Create `/ganuda/scripts/kg_health_report.py`
2. Implement all 10 metrics with graceful degradation
3. Format output as shown above (fixed-width for Slack/terminal readability)
4. Add thermalization of the report itself (self-documenting — the KG reports on its own health)
5. Wire into dawn mist script (find the dawn mist entry point and add import/call)
6. Test standalone execution: `python3 /ganuda/scripts/kg_health_report.py`

## Verification

1. Run script standalone, verify output format matches template
2. Verify metrics match manual SQL queries
3. Verify thermal created with domain_tag 'kg_health'
4. Verify graceful output when reward signals not yet available

## Council Concerns Applied

- **Coyote**: This IS the circuit breaker observability. If edge density stalls or reward signals cluster, Coyote has data to pull the kill switch.
- **Eagle Eye**: Drift detection on reward signal distribution — σ increasing = reward quality degrading.
- **Turtle**: Read-only report. No writes except the self-thermalization (temp 30 — cool, won't clutter).
