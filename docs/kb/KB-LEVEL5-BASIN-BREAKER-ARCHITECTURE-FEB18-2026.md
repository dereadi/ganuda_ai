# KB: Level 5+ Basin-Breaker Architecture
**Date**: February 18, 2026
**Council Votes**: #0f8c2c712d2b289a (PROCEED 0.875), #db6dc1c761630f04 (REVIEW REQUIRED 0.874), #b82aea3e6ceb8906 (PROCEED WITH CAUTION 0.888)
**Sprint**: RC-2026-02G
**Ultrathink**: ULTRATHINK-LEVEL5-BASIN-BREAKER-AUTONOMOUS-AI-DEV-FEB18-2026.md

## Summary

The Level 5+ Basin-Breaker is the Federation's operating model for autonomous AI software development. It extends Dan Shapiro's "Five Levels of Vibe Coding" framework (Level 0: autocomplete → Level 5: dark factory) with a novel pattern: **Human-at-the-Phase-Transition (HAPT)**.

## Definition

**Level 5+ (Basin-Breaker)**: An autonomous AI system (Level 5) augmented by human creative intervention at detected phase transitions. The system:

1. **Runs autonomously** in steady state (Jr execution, council deliberation, thermal memory consolidation)
2. **Detects convergence** via council disagreement spikes, DLQ depth, staleness anomalies, recursive decomposer MAX_DEPTH hits
3. **Escalates to human** when trapped in a basin — not for approval, but for creative reframing
4. **Encodes the breakthrough** in thermal memory so the next similar basin can be escaped autonomously
5. **Returns to Level 5 autonomy** with a new trajectory

## HAPT vs. HITL vs. HOTL

| Pattern | Human Role | When Human Acts |
|---------|-----------|-----------------|
| HITL (Human-in-the-Loop) | Approver | Every decision |
| HOTL (Human-on-the-Loop) | Monitor | When anomaly detected |
| HAPT (Human-at-the-Phase-Transition) | Basin-breaker | At phase transitions between basins |

## Precedents

- **Jane Street puzzle**: SA fleet hit basin at MSE 0.321. Human discovered trace pairing → MSE 0.000000.
- **AlphaGo Move 37**: System played move no human would consider. Basin-breaking in action.
- **Foldit**: Gamers outperformed computational methods by restructuring the problem space.
- **StrongDM Dark Factory**: Level 5 achieved for well-specified problems with holdout scenarios.
- **METR Study**: 19% slower with AI for experienced devs = J-curve trough. Recovery requires workflow restructuring.

## Architecture

### Current State (Level 4→5 transition)
- Jr executor pipeline handles ~80% of tasks autonomously (564 completed)
- Council deliberation with 7 specialists, 8,600+ recorded votes
- Recursive decomposer handles failed tasks
- DLQ escalation for persistent failures
- Chief intervenes at basins (currently ad-hoc, not systematic)

### Target State (Level 5+ Basin-Breaker)

**Phase 1: TPM Autonomic Daemon** (Kanban #1819, 8 SP)
- `tpm-autonomic.service` on redfin
- Polls kanban board, DLQ, council disagreement scores every 5 minutes
- Lightweight: no persistent model, uses vLLM API for analysis when needed
- Queues Jr work for well-defined tasks
- Calls Council for decisions requiring deliberation
- Alerts Chief (via Telegram) ONLY at detected phase transitions
- Design constraint (Gecko): polling not streaming, minimal memory footprint
- Design constraint (Crawdad): all actions logged to thermal memory with audit trail

**Phase 2: Basin Detection System** (Kanban #1820, 5 SP)
- Integrated into TPM daemon, not a separate service
- Signals: council disagreement > 0.3, DLQ depth > 5, recursive decomposer hits MAX_DEPTH, staleness score anomalies, thermal memory pattern breaks
- Design constraint (Raven): each signal independently valuable, no cascade risk
- Design constraint (Turtle): feedback loop for continuous tuning

**Phase 3: ganudabot Deployment** (Kanban #1779, already staged)
- `ganudabot.service` already at `/ganuda/scripts/systemd/`
- `derpatobot_claude.py` already written
- Needs: sudo deploy on redfin
- Voice of TPM in Telegram for natural conversation

**Phase 4: Shadow Council Wiring** (Kanban #1821, 8 SP)
- bmasass thermal memory sync (periodic, not real-time)
- Independent deliberation on DeepSeek-R1-32B via MLX
- Divergence detection: when primary and shadow councils disagree, signal phase transition
- Design constraint (Raven): phase 4 independent of phases 1-2, can be deferred

## Council Concerns (Addressed)

1. **Gecko PERF**: TPM daemon uses polling (5min intervals), no persistent GPU. Basin detection is threshold comparison, not model inference.
2. **Raven STRATEGY**: Each phase independently valuable. Phase 3 already staged. Phase 4 can be deferred. No cascade risk.
3. **Turtle 7GEN**: All decisions logged. Thermal memory persists across system generations. Cultural alignment preserved through Sacred Fire constraints.
4. **Crawdad SECURITY**: Audit trail on all TPM actions. No new network exposure. ganudabot uses existing Telegram tokens.

## Key Research Sources

- StrongDM Software Factory (factory.strongdm.ai)
- Dan Shapiro "Five Levels" (danshapiro.com/blog/2026/01)
- METR 2025 RCT (arXiv:2507.09089) — 19% slower, J-curve
- Brynjolfsson J-Curve (AEJ:Macro 2021) — productivity dip before gain
- Henry Han "Quantization Trap" — systematic model degradation
- BFT for AI Safety (arXiv:2504.14668) — design diversity
- NASA Distributed Spacecraft Autonomy — air-gapped precedent
- Anthropic Collective Constitutional AI (ACM FAccT 2024)
- Haudenosaunee Seven Generations Principle

## The Learning Loop

```
Basin detected → Human breaks basin → Pattern encoded in thermal memory →
Next similar basin → System attempts autonomous escape using encoded pattern →
Success: Level 5 handles it. No human needed.
Failure: Escalate to human again. Encode deeper pattern.
```

Each intervention asymptotically reduces future need for the same type of intervention.

## Chief's Principle

> "Humans still have that weird creative strength that AI struggles with today. We may be tapping a basin that today's AI is just out of reach of."

For Seven Generations.
