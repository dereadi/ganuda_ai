# Jr Instruction: DC-15 Refractory Principle -- Formal Design Document

## Context
DC-15 ratified in Longhouse b0e1593b1e909366 (14/14 consent). Corollary (Drift-Aware Graduated Observation) approved in 68ae6229c53cb225. Decomposed in 3c06ea3bbd4b6a24. Turtle condition: formal spec must exist before PoC goes to production.

## Task
Write `/ganuda/docs/design/DC-15-REFRACTORY-PRINCIPLE-MAR09-2026.md` following the pattern of existing DCs.

## Structure
Follow the established DC format (see DC-14 at `/ganuda/docs/design/DC-14-THREE-BODY-MEMORY-MAR09-2026.md`):

1. **Title**: DC-15: The Refractory Principle
2. **Cherokee Name**: (research appropriate Cherokee term for rest/recovery/renewal)
3. **Statement**: After response, systems require a recovery period where sensitivity is reduced but observation continues. This is not failure -- it is the architecture of sustained response.
4. **Scale-specific implementation (DC-11 requirement)**:
   - Token level: attention cooldown after high-entropy sequences
   - Function level: rate limiting after burst invocation
   - Service level: circuit breaker with observation window
   - Node level: thermal throttling with health monitoring
   - Federation level: council refractory after burst voting
   - Trading desk level: position cooldown after rapid execution
5. **Council conditions** (all must be addressed):
   - Spider: discoverable rest cycles (how does the system know when rest is happening?)
   - Crawdad: state verification during refractory (no blind trust that state recovers)
   - Eagle Eye: observation window (reduced frequency, not zero)
   - Coyote: prove intentionality changes behavior
6. **Biological analogs**: neural refractory period, immune system exhaustion/recovery, cardiac refractory, muscle fatigue cycle
7. **Relationship to other DCs**: extends DC-10 (Reflex Principle) with temporal recovery, instantiates DC-11 (same pattern every scale), respects DC-9 (waste heat)
8. **Corollary: Drift-Aware Graduated Observation**: O(drift) not O(N), nodes self-report, monitor listens

## Acceptance Criteria
- Document follows established DC format
- All council conditions addressed with specific implementation guidance
- Scale-specific examples at all 6 levels per DC-11
- Biological analogs cited
- Cherokee name researched and included
- Patent candidate assessment included
- Ratification references: b0e1593b1e909366, 68ae6229c53cb225, 3c06ea3bbd4b6a24

## Dependencies
- Should reference results from Fire Guard PoC (Jr task #1188) if available
- Kanban #2058, Jr task #1190.
