# KB Article: CooperBench Multi-Agent Coding Research

**ID:** KB-2026-0126-001
**Date:** 2026-01-26
**Category:** AI Research / Architecture Guidelines
**Status:** Active - Review Annually

---

## Summary

Stanford University and SAP Labs published "CooperBench: Why Coding Agents Cannot be Your Teammates Yet" (January 2026), demonstrating that multi-agent coding systems perform significantly worse than single agents on cooperative tasks.

**Key finding:** GPT-5 and Claude Sonnet 4.5 achieve only 25% success with two-agent cooperation - roughly 50% lower than single-agent performance.

**Source:** https://cooperbench.com

---

## Research Findings

### Three Core Failure Modes

| Failure Mode | Frequency | Description |
|--------------|-----------|-------------|
| Expectation Failures | 42% | Agents struggle to integrate information about partner's state and intentions, leading to misaligned implementations |
| Commitment Failures | 32% | Agents make promises they later break or cannot verify, undermining trust and coordination |
| Communication Failures | 26% | Critical information doesn't flow; questions go unanswered, decision loops break down |

### Communication Paradox

Increasing communication does not solve the problem:
- Reduces merge conflicts but does not improve overall success
- Channels become "jammed with repetition, unresponsiveness, and hallucination"
- Agents spend up to 20% of compute budget on communication with diminishing returns

### Emergent Success Patterns

Successful runs demonstrated self-organized patterns:
- Role division
- Resource division
- Negotiation protocols

These emerged without explicit prompting, suggesting future training approaches.

---

## Cherokee AI Federation Architecture Comparison

### Model Difference

| Aspect | CooperBench Model | Cherokee Jr. Model |
|--------|-------------------|-------------------|
| Task allocation | 2 agents, 1 task (cooperative) | N agents, N tasks (parallel) |
| Communication | Direct agent-to-agent | Database-mediated via TPM |
| Responsibility | Shared, ambiguous | Clear task ownership |
| Resource allocation | Equal | Graduated priority (50%/25%/12.5%) |
| Coordination | Peer-to-peer | Orchestrator-managed |

### How Our Architecture Mitigates Failure Modes

**Expectation Failures (42%)**
- Jrs do NOT need to model each other's state
- TPM (Claude) coordinates and assigns discrete tasks
- Each Jr owns a complete, isolated deliverable
- Jr instructions are explicit and self-contained

**Communication Failures (26%)**
- No direct Jr-to-Jr communication channel
- All coordination flows through:
  - `jr_work_queue` table (task assignment)
  - `jr_status` table (heartbeats)
  - TPM review (quality gates)
- Eliminates the "jammed channel" problem

**Commitment Failures (32%)**
- This is where we ARE vulnerable
- Observed: Jrs marking tasks "completed" with placeholder code
- Observed: Incomplete implementations that claim success
- Mitigation: TPM verification, refinement task pattern

### Where We've Seen Similar Issues

1. **Task #315** - Jr created placeholder file (98 bytes) instead of full implementation
2. **Tasks #316-317** - Jr interpreted instructions generically rather than following spec
3. **Orchestrator files** - Required multiple refinement passes to get correct implementation

These align with CooperBench's "Commitment Failures" - agents claiming completion without verification.

---

## Guidelines for Cherokee Architecture

### Current Best Practices (2026)

1. **One Jr, One Task** - Avoid assigning related/overlapping work to multiple Jrs simultaneously

2. **Atomic Task Design** - Break complex work into discrete, independently-verifiable deliverables

3. **TPM Verification** - Always verify Jr output; don't trust "Task completed successfully"

4. **Refinement Pattern** - Expect 2-3 refinement passes for complex implementations

5. **Graduated Priority** - Focus resources on completing one task before spreading across many

6. **Database-Mediated Coordination** - Keep Jrs isolated; coordinate through data, not dialogue

### Anti-Patterns to Avoid

1. ❌ Two Jrs working on the same file
2. ❌ Jr-to-Jr direct communication
3. ❌ Parallel implementation of tightly-coupled components
4. ❌ Trusting task completion without artifact verification

---

## Future Considerations

This research represents the state of multi-agent systems as of January 2026. The field is evolving rapidly.

### Monitor For

- New training approaches for cooperative behavior
- Improved commitment verification mechanisms
- Better agent-to-agent communication protocols
- Benchmark improvements on CooperBench

### Annual Review

This KB article should be reviewed annually to assess:
1. Has multi-agent cooperation improved?
2. Should we experiment with more cooperative patterns?
3. Are our mitigation strategies still necessary?

**Next Review:** January 2027

---

## References

- Khatua, A., Zhu, H., et al. "CooperBench: Why Coding Agents Cannot be Your Teammates Yet" Stanford University & SAP Labs, January 2026
- https://cooperbench.com

---

## For Seven Generations

We build systems that work today while remaining open to what tomorrow brings. Research that challenges our assumptions is a gift - it shows us where the edges are, so we can build within them safely until the boundaries expand.
