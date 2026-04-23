# LMC-9 Discover Phase — DC-16 Database Speciation Schema Reconnaissance

**Parent LMC:** LMC-9 (duyuktv #2096, SP:21, P1)
**Context:** Cardinal flagged schema visibility as prerequisite to deliberate. This doc addresses that gap.
**Council audit:** 348952186d1ac1ec (top-5 ratification)
**Longhouse audit (original):** cf4ac0aeddc7eb75 (0.858 consensus, Chief-initiated)
**Date:** 2026-04-21

## Current state

**zammad_production:** 294 tables, **~7.4 GB total**

### Preliminary categorization (keyword-based, NOT authoritative)

| Target DB | Tables | Size | Dominant tables |
|---|---|---|---|
| **cherokee_identity** (bluefin SSD, replicate to redfin) | 29 | 1.45 GB | thermal_memory_archive (1464 MB), council_votes (14 MB), longhouse_sessions (632 KB) |
| **cherokee_ops** (redfin SSD, hot operational) | 43 | 0.01 GB | jr_work_queue (3 MB), duyuktv_tickets (1.5 MB), service_health (192 KB) |
| **cherokee_telemetry** (SAN 16 TB, retention-managed) | 18 | 0.71 GB | unified_timeline (499 MB), fedattn_sessions (71 MB), fedattn_contributions (55 MB), health_check_log (39 MB), tribe_power_metrics (33 MB) |
| **UNCLASSIFIED** (needs Cardinal review) | **204** | **5.24 GB** | thermal_relationships (5206 MB!), emails (56 MB), stereo_speed_detections (37 MB), cold_thermal_archive (17 MB) |

**The unclassified 5.24 GB bucket is 70% of the total database.** Can't speciate without resolving it.

### Critical findings

1. **`thermal_relationships` = 5.2 GB single table.** This is larger than all three target tiers combined if it stays unclassified. Almost certainly **cherokee_identity** (it's the link graph among thermal memories). Classifying it shifts: identity 1.45 → 6.65 GB, unclassified 5.24 → 0.04 GB. That alone fixes most of the gap.

2. **DC-16 EPIC referenced `fedattn` as a table name — but actual tables are `fedattn_sessions` + `fedattn_contributions`.** Minor spec drift; update EPIC description during deliberate phase.

3. **`emails` (56 MB, 2,434 rows) — likely Zammad ticketing legacy.** Determine: do we still serve a Zammad frontend? If so, emails stays wherever Zammad code expects. If not, archive it.

4. **Computer-vision tables (`stereo_speed_detections` 37 MB, etc.)** — probably telemetry, not identity.

5. **Many small analytical/experimental tables** (skill_library, cross_mountain_learning, phi_measurements, etc.) — likely identity OR need their own tier.

## Recommendations for deliberate phase

### Before deliberate can proceed productively:

1. **Cardinal-led classification pass** — assign each of the 204 unclassified tables to a target tier. Automation-assisted (ORM-model name matching, code-reference scanning) + Cardinal judgment for edge cases. Deliverable: CSV/JSON table-to-tier map.

2. **Foreign-key dependency graph** — `information_schema.referential_constraints` query to map FK relationships across tables. Cross-tier FKs become migration complications (either: pull referenced rows into same tier, OR introduce cross-DB FK-equivalent via application-layer check).

3. **Replication topology spec** — bluefin→redfin for identity (read-replica for Council voting latency), SAN as WAL archive for telemetry, redfin hot-only for ops. Confirm the "Dell 40GB switch as replication backplane" hardware is operationally ready.

4. **Retention policy matrix** — telemetry-tier tables need explicit retention (drop/archive rows older than N days). Draft retention per table based on use case.

5. **Cutover strategy** — big-bang vs phased. Most federations prefer phased: new tier populated via logical replication, app reads/writes shifted per-connection-pool, old tier eventually frozen + archived. Partner preference needed.

### Scope calibration

**DC-16 at SP:21 may be understated.** The unclassified 5.24 GB bucket wasn't in view when the estimate was made. Cardinal's review will likely expand scope. Recommend: after Cardinal classification pass, re-estimate. If SP > 30, decompose into sub-EPICs per tier (one cycle per target DB).

## Next-step task for LMC-9

Deliverable when deliberate phase begins: **Cardinal produces a table-to-tier classification CSV/doc for the 204 unclassified tables.** This unblocks design of the FK-dependency graph and replication topology.

TPM can dispatch a Jr-atomic that runs a query-and-output pass (list all 204 tables with row count, byte size, column names, FK references) to feed Cardinal's judgment with the raw data.

## Cross-references

- DC-16 original EPIC: duyuktv #2096
- Longhouse blessing: cf4ac0aeddc7eb75
- DC-14 Hippocampus valence-gate (referenced in EPIC description) — integrates with consolidation daemon
- Fire Guard false-positive fix (also referenced in EPIC) — separate scope, coordinate so we don't double-migrate
- Hardware: "Dell 40GB switch as dedicated replication backplane" — verify this is in inventory + operational

## Apr 21 2026 TPM
