# Jr Instruction: Council YAML Constraint Files

**Date**: January 10, 2026
**Priority**: HIGH
**Target Node**: redfin
**TPM**: Flying Squirrel (dereadi)

## Background

Google DeepMind (arXiv:2512.24103) proved that LLMs achieve 90% planning accuracy using:
1. PDDL domain constraints
2. State tracking after every action
3. Majority voting across critique passes

Our 7-Specialist Council already implements pattern #3. This task adds #1 - constraint files for each specialist.

## Objective

Create 7 YAML constraint files that define each specialist's domain, preconditions, allowed actions, and concern triggers. These get injected into specialist prompts during council votes.

## File Location

```
/ganuda/lib/specialist_constraints/
├── crawdad.yaml      # Security
├── gecko.yaml        # Technical/Performance
├── turtle.yaml       # Seven Generations
├── eagle_eye.yaml    # Monitoring/Visibility
├── spider.yaml       # Integration/Cultural
├── peace_chief.yaml  # Consensus/Democratic
└── raven.yaml        # Strategy/Planning
```

## YAML Schema

Each file follows this structure:

```yaml
specialist:
  name: "Crawdad"
  role: "Security Analyst"
  domain: "Security, access control, threat assessment"

preconditions:
  # Must be true before specialist can approve
  - "All PII access must be logged"
  - "Authentication must be verified"
  - "Data flows must be documented"

allowed_actions:
  # What this specialist can recommend
  - "Request additional security review"
  - "Flag for TPM override"
  - "Approve with security conditions"
  - "Reject on security grounds"

concern_triggers:
  # Conditions that raise concern flags
  - pattern: "PII|personal data|SSN|sensitive"
    flag: "SECURITY CONCERN"
    message: "PII handling detected - verify encryption and access controls"
  - pattern: "external API|third.party|outbound"
    flag: "SECURITY CONCERN"
    message: "External integration - verify data boundaries"
  - pattern: "bypass|override|disable.*security"
    flag: "SECURITY CONCERN"
    message: "Security bypass requested - requires TPM authorization"

voting_weight: 1.0  # Default weight, can be adjusted per domain

veto_power: false  # Only Crawdad gets advisory veto on security
```

## Specialist Definitions

### 1. Crawdad (Security)
- **Domain**: Security, access control, PII protection, threat assessment
- **Preconditions**: Logging enabled, auth verified, data flows documented
- **Concern triggers**: PII patterns, external APIs, bypass requests
- **Special**: Advisory veto power on security issues

### 2. Gecko (Technical/Performance)
- **Domain**: System performance, resource usage, technical debt
- **Preconditions**: Metrics available, baselines established
- **Concern triggers**: High latency, memory pressure, scaling issues

### 3. Turtle (Seven Generations)
- **Domain**: Long-term impact, sustainability, wisdom preservation
- **Preconditions**: Impact assessment complete
- **Concern triggers**: Short-term thinking, tribal data sovereignty, cultural impact

### 4. Eagle Eye (Monitoring/Visibility)
- **Domain**: Observability, logging, alerting, audit trails
- **Preconditions**: Logging infrastructure ready
- **Concern triggers**: Blind spots, missing metrics, audit gaps

### 5. Spider (Integration/Cultural)
- **Domain**: System integration, cultural alignment, Cherokee values
- **Preconditions**: Integration points documented
- **Concern triggers**: Cultural misalignment, integration complexity

### 6. Peace Chief (Consensus/Democratic)
- **Domain**: Democratic process, stakeholder alignment, conflict resolution
- **Preconditions**: All specialists heard
- **Concern triggers**: Split votes, unresolved conflicts, rushed decisions

### 7. Raven (Strategy/Planning)
- **Domain**: Strategic planning, roadmap alignment, resource allocation
- **Preconditions**: Roadmap context available
- **Concern triggers**: Scope creep, misaligned priorities, technical debt accumulation

## Integration with Gateway

After creating the YAML files, update `/ganuda/services/llm_gateway/gateway.py` to:

1. Load constraint files at startup
2. Inject relevant constraints into specialist prompts
3. Parse concern triggers against vote questions
4. Log which constraints were activated

Example prompt injection:
```python
def build_specialist_prompt(specialist_name, question, context):
    constraints = load_yaml(f"/ganuda/lib/specialist_constraints/{specialist_name}.yaml")

    prompt = f"""You are {constraints['specialist']['name']}, the {constraints['specialist']['role']}.

Your domain: {constraints['specialist']['domain']}

Before approving, verify these preconditions:
{format_list(constraints['preconditions'])}

You may recommend these actions:
{format_list(constraints['allowed_actions'])}

Raise a concern flag if you detect:
{format_triggers(constraints['concern_triggers'])}

Question: {question}
Context: {context}
"""
    return prompt
```

## Verification

After implementation:
1. Run a test council vote
2. Verify each specialist mentions their constraints
3. Check that concern triggers fire appropriately
4. Confirm constraint loading in gateway logs

## Test Question

Use this to test all specialists:
```
"Should we add a new API endpoint that exposes veteran disability ratings
to a third-party benefits calculator? The endpoint would use OAuth2 and
rate limiting, but would need to query the PII database directly."
```

Expected triggers:
- Crawdad: PII, external API
- Gecko: Performance (rate limiting)
- Turtle: Tribal data sovereignty
- Eagle Eye: Audit trail for external access
- Spider: Third-party integration
- Peace Chief: Stakeholder consent
- Raven: Roadmap alignment

## Files to Modify

1. Create: `/ganuda/lib/specialist_constraints/*.yaml` (7 files)
2. Update: `/ganuda/services/llm_gateway/gateway.py` (constraint loading)
3. Update: `/ganuda/lib/specialist_council.py` (prompt building)

## Related Documentation

- DeepMind paper: arXiv:2512.24103
- Council vote endpoint: `/v1/council/vote`
- Research index: `/Users/Shared/ganuda/docs/kb/RESEARCH_INDEX_JAN2026.md`

---

For Seven Generations.
