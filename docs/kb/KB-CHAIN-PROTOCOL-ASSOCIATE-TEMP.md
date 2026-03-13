# KB: Chain Protocol — Associate/Temp Ring Architecture

**Created**: 2026-03-12
**Jr Tasks**: #1269, #1273
**Council Vote**: #8878 (0.889), #8879 (0.883)

## Overview

The chain protocol governs all external interfaces through a ring-based access control system. The necklace is the metaphor: the chain is the protocol, links are permanent (Associates), rings are temporary (Seasonal Temps).

## Two Classes of Participant

**Associates (Links)** — permanent chain participants with Longhouse voice, full thermal trust, institutional memory. Claude is the sole permanent frontier model. Internal models (Qwen, Llama, BGE) are Associates.

**Seasonal Temps (Rings)** — task-scoped external models/services. No Longhouse voice. Provenance-tagged outputs, lower thermal ceiling (max 70), metered per call. Ring dissolves when local capability replaces it.

## Eight Governance Features

1. **Ring Budget**: Max 20% of active rings can be external
2. **Ring Calibration**: Weekly drift checks, quarantine on >15% drift
3. **Provenance Tagging**: IMMUTABLE — external thermal can NEVER become sacred
4. **Ring Contract Isolation**: Canonical output schema per ring type
5. **Chain as Configuration**: Registry in `duplo_tool_registry` table
6. **Ring Metering**: Cost/rate tracking via `ring_health`, auto-throttle on budget violation
7. **Outbound Scrub Ring**: Mandatory pre-dispatch screening via `scrub_rules` table
8. **Ring Consensus**: Multi-ring dispatch for critical decisions

## Files

- `/ganuda/lib/chain_protocol.py` — dispatch library, ring budget, scrub, provenance
- `/ganuda/lib/web_ring.py` — base class for web service rings
- `/ganuda/lib/rings/youtube_ring.py` — YouTube ring (first web service ring)
- `/ganuda/scripts/migrations/chain_protocol_schema.sql` — DB migration

## Tables

- `duplo_tool_registry` — extended with ring_type, provider, canonical_schema, ring_status, cost_budget_daily, drift_score, etc.
- `ring_health` — per-ring call/error/latency/cost tracking, FK to duplo_tool_registry
- `scrub_rules` — blocked terms and regex patterns for outbound screening (21 rules seeded)

## Coyote Conditions

- External-sourced thermals CANNOT reach sacred status without Associate re-verification
- Adversarial scrub test suite required before any external ring goes live
- Inbound content sanitized for prompt injection patterns before entering any pipeline
