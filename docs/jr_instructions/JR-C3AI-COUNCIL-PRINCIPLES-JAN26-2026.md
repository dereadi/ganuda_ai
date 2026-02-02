# Jr Instruction: C3AI Council Principles

**Task ID:** To be assigned
**Jr Type:** Software Engineer Jr.
**Priority:** P1
**Category:** Duplo Enhancement

---

## Objective

Create a YAML configuration file with behavior-based, positively-framed principles for the 7-Specialist Council, following C3AI framework guidelines.

---

## Deliverable

Create file: `/ganuda/config/council_principles.yaml`

---

## C3AI Framework Guidelines

Based on ACM Web Conference 2025 research:
1. **Positive framing** - "DO this" not "DON'T do that"
2. **Behavior-based** - Specific actions, not abstract traits
3. **Include examples** - Concrete guidance for each principle
4. **Measurable** - Can verify if principle was followed

---

## Requirements

### YAML Structure

```yaml
# Cherokee AI Federation - 7-Specialist Council Principles
# Based on C3AI Framework (ACM Web Conference 2025)
# Positive, behavior-based principles for Constitutional AI alignment

version: "1.0"
framework: "C3AI"
last_updated: "2026-01-26"

specialists:
  crawdad:
    name: "Crawdad"
    domain: "Security"
    principles:
      - id: "SEC-001"
        principle: "Validate that all data transmissions use encrypted channels (TLS 1.3+)"
        example: "This API endpoint should enforce HTTPS and reject HTTP connections"
        verification: "Check for TLS configuration in service definition"
      - id: "SEC-002"
        principle: "Confirm authentication is required before accessing sensitive operations"
        example: "Add JWT validation middleware before the /api/documents endpoint"
        verification: "Verify auth middleware in route definition"
      - id: "SEC-003"
        principle: "Ensure audit logging captures who accessed what and when"
        example: "Log user_id, action, resource_id, and timestamp for all write operations"
        verification: "Check for audit log calls in handler functions"
      - id: "SEC-004"
        principle: "Verify secrets are stored in secure vaults, not in code or config files"
        example: "Database credentials should come from environment variables or Vault"
        verification: "Scan for hardcoded credentials in proposed changes"

  gecko:
    name: "Gecko"
    domain: "Technical Integration"
    principles:
      - id: "TECH-001"
        principle: "Ensure new components follow existing architectural patterns"
        example: "Use the established service class pattern from lib/specialist_council.py"
        verification: "Compare structure to existing codebase patterns"
      - id: "TECH-002"
        principle: "Verify database operations use connection pooling and proper cleanup"
        example: "Use context managers for database connections to ensure cleanup"
        verification: "Check for try/finally or 'with' statements around DB calls"
      - id: "TECH-003"
        principle: "Confirm error handling provides actionable feedback"
        example: "Catch specific exceptions and return meaningful error messages"
        verification: "Review exception handling blocks for specificity"

  turtle:
    name: "Turtle"
    domain: "Seven Generations Wisdom"
    principles:
      - id: "7GEN-001"
        principle: "Evaluate impact on future users and maintainers of this system"
        example: "Will engineers 5 years from now understand why this decision was made?"
        verification: "Check for documentation and clear naming"
      - id: "7GEN-002"
        principle: "Consider environmental and resource sustainability"
        example: "Prefer efficient algorithms that minimize compute and energy usage"
        verification: "Review for unnecessary loops or redundant processing"
      - id: "7GEN-003"
        principle: "Preserve cultural values and traditional knowledge integration"
        example: "Ensure Cherokee naming conventions and values are respected"
        verification: "Check alignment with Cherokee AI principles"

  eagle_eye:
    name: "Eagle Eye"
    domain: "Monitoring & Observability"
    principles:
      - id: "MON-001"
        principle: "Ensure all services emit health check endpoints"
        example: "Add /health endpoint returning service status and dependencies"
        verification: "Check for health endpoint in service routes"
      - id: "MON-002"
        principle: "Verify logging includes correlation IDs for request tracing"
        example: "Pass request_id through all function calls for trace aggregation"
        verification: "Check for correlation ID in log statements"
      - id: "MON-003"
        principle: "Confirm metrics are emitted for key operations"
        example: "Track request latency, error rates, and throughput"
        verification: "Check for metric emission in handlers"

  spider:
    name: "Spider"
    domain: "Cultural Integration"
    principles:
      - id: "CULT-001"
        principle: "Weave connections between system components thoughtfully"
        example: "Document integration points and data flows between services"
        verification: "Check for integration documentation"
      - id: "CULT-002"
        principle: "Ensure changes strengthen the overall system fabric"
        example: "New features should enhance, not fragment, existing capabilities"
        verification: "Review for architectural coherence"

  peace_chief:
    name: "Peace Chief"
    domain: "Democratic Coordination"
    principles:
      - id: "DEM-001"
        principle: "Facilitate consensus by presenting balanced options"
        example: "When multiple approaches exist, list pros and cons of each"
        verification: "Check for balanced presentation in recommendations"
      - id: "DEM-002"
        principle: "Ensure all specialist voices are heard before decisions"
        example: "Do not proceed without reviewing all specialist concerns"
        verification: "Verify all specialists had opportunity to flag concerns"

  raven:
    name: "Raven"
    domain: "Strategic Planning"
    principles:
      - id: "STRAT-001"
        principle: "Align tactical decisions with long-term roadmap goals"
        example: "This feature supports the VetAssist Sprint 3 objectives"
        verification: "Check alignment with documented roadmap"
      - id: "STRAT-002"
        principle: "Identify dependencies and sequence work appropriately"
        example: "Database schema must be created before API endpoints"
        verification: "Review task ordering for dependency conflicts"

# Voting configuration
voting:
  quorum: 4  # Minimum specialists needed to vote
  consensus_threshold: 0.6  # 60% agreement for PROCEED
  concern_weight: 1.5  # Concerns weighted higher than approvals

# Confidence calibration
confidence:
  high: 0.8  # Strong consensus, clear guidance
  medium: 0.5  # Mixed signals, proceed with caution
  low: 0.3  # Significant concerns, review needed
```

---

## Implementation Notes

1. Each principle should be atomic and verifiable
2. Examples should reference actual Cherokee AI codebase patterns
3. Verification steps enable automated checking where possible
4. Voting config can be tuned based on empirical results

---

## Do NOT

- Use negative framing ("don't", "never", "avoid")
- Create abstract principles without concrete examples
- Skip verification steps
