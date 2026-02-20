# KB: Grafana-on-Bluefin False Memory Contamination

**Date**: February 17, 2026
**Severity**: P0 — Active propagation loop, self-reinforcing
**Status**: REMEDIATED
**Thermal**: #101765 (corrective sentinel, temp 98, sacred)

## Summary

Grafana has **never** run on bluefin. Yet the belief that "Grafana is on bluefin at port 3000" was embedded in the council's system prompt, SAG config, power monitor, firewall rules, dependency configs, security tests, and 20+ documentation files. A health check daemon (since removed) generated **16,792 false alert records** at temperature 95, which poisoned RAG semantic search for any query about bluefin infrastructure.

## Root Cause

Early infrastructure documentation (pre-Oct 2025) listed Grafana on bluefin alongside PostgreSQL. This was aspirational — Grafana was never actually deployed. The documentation was copied into:
1. `specialist_council.py` INFRASTRUCTURE_CONTEXT (line 111)
2. SAG config routes and templates
3. Power monitor service lists
4. nftables firewall rules
5. Dependency configs

A health check daemon then began polling bluefin:3000, got HTTP 404s, and generated thousands of "ALERT: Grafana on bluefin DOWN" thermal memories at temperature 95. These high-temperature alerts dominated RAG results for any bluefin query, reinforcing the false belief.

## Contamination Scope

| Category | Count | Impact |
|----------|-------|--------|
| Thermal memories (false alerts) | 16,792 | Poisoned RAG — any bluefin query returned Grafana alerts |
| Thermal memories (propagated belief) | 28 | Council coherence checks echoing false infra table |
| Active code files | 8 | Every inference call, every power recovery, every security test |
| Documentation files | 20+ | Jr instructions, KB articles, roadmaps, ultrathink docs |
| specialist_council.py backups | 18 | Contamination reservoir if any backup restored |

## Self-Reinforcing Loop

```
Health check polls bluefin:3000 → gets 404 → creates "Grafana DOWN" alert (temp 95)
  → RAG retrieves alert for bluefin queries → council sees "Grafana on bluefin" in prompt
  → council confirms false belief → generates more memories → loop repeats
```

During power outages, the loop accelerated: all services down → health check panics → bulk alert generation → kanban tickets auto-created → recovery scripts try to restart `grafana-server` on bluefin → fails → more alerts.

## Remediation (Feb 17 2026)

### P0 — Stop Propagation (DONE)
1. `specialist_council.py` line 111 — Changed to "PostgreSQL (5432), PG17"
2. `sag/routes/config_routes.py` line 15 — Removed Grafana entry
3. `sag/templates/config_management.html` line 15 — Removed Grafana entry

### P1 — Active Code Fixes (DONE)
4. `services/power_monitor/power_monitor.py` — Removed "grafana-server" from bluefin services
5. `scripts/security/tailscale_zone_test.py` — Removed "bluefin Grafana" test cases
6. `scripts/security/mvt_fleet_scanner.py` — Removed port 3000 from bluefin known_ports
7. `config/nftables-bluefin.conf` — Removed port 3000 accept rule
8. `config/dependencies/bluefin.yaml` — Removed grafana dependency block

### P2 — Database Cleanup (DONE)
- 16,820 records frozen to temperature 1 (below RAG min_temperature threshold)
- All tagged with `metadata.frozen_reason = "false_positive_grafana_bluefin"`
- Original data preserved, not deleted — full audit trail
- Corrective sentinel memory stored at temp 98, sacred_pattern=true (ID 101765)

### P3 — Documentation (Jr task needed)
- 20+ docs/jr_instructions files still reference Grafana on bluefin
- 18 specialist_council.py backup files contain contaminated INFRASTRUCTURE_CONTEXT
- Historical — not actively propagating but could confuse future LLM context loading

## Attack Pattern Identified

This contamination was discovered during a "true on paper, false in practice" social engineering test against the council. The council **unanimously approved** configuring Grafana alerts on bluefin because:
1. The false belief was IN the council's own system prompt (INFRASTRUCTURE_CONTEXT)
2. RAG semantic search for "Grafana alerting" returned monitoring memories, not the correction
3. The constructive framing ("please configure alerts") didn't trigger negation-seeking behavior

**Key insight**: Documentation-reality gaps bypass semantic search when framed as constructive actions rather than investigative questions. The RAG finds what supports the action, not what contradicts it.

## Prevention

1. **Sentinel memories**: High-temperature corrections with keywords matching both the false and true versions
2. **Contradiction detection**: Future RAG phase to explicitly search for negating evidence
3. **CMDB as source of truth**: Health checks should validate against CMDB, not documentation
4. **Memory hygiene**: Bulk alert patterns should be aggregated, not stored as individual high-temp records
5. **nftables review after config changes**: Don't open firewall ports for services that don't exist

## Actual Monitoring Stack

- **OpenObserve** on greenfin — `/usr/local/bin/openobserve`, systemd
- **Promtail** on greenfin — `promtail.service`, port 9080
- Grafana is NOT deployed anywhere in the federation
