# LM-OPENCLAW-OTEL — Adapt Phase Plan

**Parent epic:** cycle 3, kanban #2127 / #2128
**Phase 1 design:** `/ganuda/docs/lm_openclaw_otel_phase1.md`
**Council approvals:**
- `813dbb85866e45e2` (APPROVED 11-0-2, Phase 2 design ratification)
- `84beb73ee61cf993` (APPROVED 10-1-2, prioritized Phase 3 as next work, Apr 20 2026)
**Author:** TPM, Apr 20 2026

## Scope

Stand up OpenTelemetry collector on bluefin + instrument Council voting path + Jr executor path with Python-native opentelemetry-api emission. Phase 3 pilot — prove the pattern with Council votes, extend to other surfaces in follow-on cycles.

## Partner prerequisites
**None.** Pure infra + code, TPM + Jr executable.

## Dependency DAG

```
O1 (otel-collector config YAML) → O2 (otel-collector systemd unit) → O3 (deploy collector)
                                   ↓
O4 (ganuda_otel lib module - TPM) ← depends on collector running
     ↓
O5 (instrument specialist_council.py vote path - TPM)
     ↓
O6 (verify traces in collector file export - TPM)
     ↓
O7 (instrument jr_queue_worker.py - Jr atomic)
O8 (instrument memory_api/server.py /search - Jr atomic)
O9 (redaction + sacred-pattern guard tests - Jr atomic)
```

## Atomic step list (9 units)

| # | Unit | Owner | Files | Size |
|---|---|---|---|---|
| O1 | otel-collector config YAML | Jr atomic | `/ganuda/config/otel-collector-config.yaml` | 15 min |
| O2 | otel-collector systemd unit | TPM | `/ganuda/config/systemd/otel-collector.service` | 5 min (Jr-can't-INI) |
| O3 | Install otel-collector-contrib binary + deploy + verify | TPM | apt/snap + systemd enable | 15 min |
| O4 | `ganuda_otel.py` helper lib | TPM | `/ganuda/lib/ganuda_otel.py` | 20 min |
| O5 | Instrument `specialist_council.py` vote path | TPM | edit existing file | 20 min |
| O6 | Verify traces flowing (file exporter) | TPM | manual smoke | 10 min |
| O7 | Instrument `jr_queue_worker.py` | Jr atomic | add ~10 lines to existing file | 10 min |
| O8 | Instrument `memory_api/server.py /search` | Jr atomic | add ~5 lines to one endpoint | 10 min |
| O9 | Redaction/sacred-pattern test | Jr atomic | `/ganuda/services/otel_test/test_redaction.py` | 15 min |

Total: ~2 hr. 4 Jr-atomic + 5 TPM.

## Council amendments from Phase 2 vote

- **Gecko:** cgroup resource isolation on bluefin (MemoryMax=2G, CPUQuota=25%). O2 enforces.
- **Crawdad:** trace attributes MUST NOT leak credentials. O4 + O5 run `redactSensitiveText` on all span attrs.
- **Eagle Eye:** async emission — OTel export is BestEffort, never blocks Council vote path. O4 configures BatchSpanProcessor.
- **Spider:** no new cross-node dependencies — file exporter first, Tempo/Prometheus as separate Phase later.

## Python semantic conventions (align with openclaw where possible)

```
ganuda.council.vote.duration_ms      (histogram, per vote)
ganuda.council.specialist.vote       (counter, tags: specialist_id, vote_value)
ganuda.council.specialist.duration   (histogram, per specialist call)
ganuda.council.vote                  (span, root for a vote)
ganuda.council.specialist            (span, child per specialist)
ganuda.jr.task.duration_ms           (histogram, O7)
ganuda.jr.task.outcome               (counter, tags: status, source, O7)
ganuda.memory_api.search.duration_ms (histogram, O8)
ganuda.memory_api.search.hits        (histogram, O8)
```

## Rollback

- O1-O3: uninstall otel-collector service (`systemctl disable`, rm unit) — collector is additive, removing doesn't break existing work
- O4-O8: all instrumentation wrapped in try/except — if OTel is down, it no-ops silently. ganuda_otel.py helper has no-op fallback when `OTEL_EXPORTER_OTLP_ENDPOINT` isn't set
- O9: test file, independent

## Acceptance criteria

1. `ganuda-otel-collector.service` active, within cgroup limits
2. Running a Council vote writes at least one trace to the collector's file exporter (readable JSON lines at `/var/log/otel-collector/traces.json` or similar)
3. Trace contains expected spans: `ganuda.council.vote` root + N child `ganuda.council.specialist` spans
4. No sacred-pattern content in trace attributes (verified by O9 test)
5. Council vote latency metric emitted and visible in file exporter
6. Collector restart doesn't block Council votes (graceful degradation verified)

## Dispatch order

1. O1 (config YAML) — Jr atomic, smallest, smoke test first
2. Parallel: O2 (systemd unit TPM) + O9 (test suite Jr)
3. O3 (install + deploy TPM) — sequential after O1 + O2
4. O4 (helper lib TPM) — after O3 (needs live collector)
5. O5 (instrument council path TPM) — after O4
6. O6 (smoke test TPM) — after O5
7. Parallel: O7 (Jr instrument executor) + O8 (Jr instrument memory_api)

## Cross-refs

- `deer_signal_compuflair_mean_field_apr2026.md` — physics of why observability matters
- `project_two_hands_diagnosis_apr2026.md` — forcing without measurement → silent drift
- `feedback_adapt_phase_is_tpm_orchestration.md` — decomposition discipline applied here
