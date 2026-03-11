# Telemetry and Phone-Home Policy Document

## Metadata
- **Date**: 2026-03-09
- **Author**: Jr Executor
- **Version**: 1.0
- **Review Status**: DRAFT
- **Classification**: PUBLIC

## Philosophy
At the Cherokee AI Federation, our north star is sovereign intelligence for those who build it. Sovereign intelligence means that your data is yours, and any telemetry or phone-home behavior must respect that sovereignty absolutely. Our telemetry exists to improve the product, never to surveil the user. Trust is the product — telemetry must never undermine it.

## What We Collect
We collect the following data points to ensure the health and improvement of our platform:

- **Cluster Health Metrics**: Node count, uptime, service status (aggregate only)
- **Feature Usage Counts**: Number of council votes, Jr tasks executed, thermal writes (counts only, never content)
- **Error Rates and Error Categories**: Crash counts, timeout counts (never stack traces containing user data)
- **Software Version and Update Channel**
- **Hardware Tier**: CPU/GPU class (not serial numbers or identifiers)

## What We NEVER Collect
We explicitly do not collect the following data:

- **Thermal Memory Content**: NEVER
- **Sacred Data or Sacred Thermals**: NEVER
- **PII of Any Kind**: NEVER
- **Council Vote Content or Rationale**: NEVER (only aggregate vote counts)
- **Prompt Content, Model Outputs, or Inference Data**: NEVER
- **Credential or Secret Material**: NEVER
- **Network Topology Details Beyond Node Count**: NEVER

## Consent Model
- **Community Tier**: Telemetry is OFF by default (opt-in)
- **Pro Tier**: Telemetry is configurable, OFF by default, encouraged for support purposes
- **Enterprise Tier**: Telemetry is OFF by default, fully configurable, air-gap mode available
- **All Tiers**: Single configuration flag to disable all telemetry (`telemetry.enabled: false`)

## Data Handling
- **Retention**: 90 days maximum, then hard delete
- **Storage**: Cherokee AI Federation infrastructure only (specify which node class)
- **Encryption**: TLS in transit, encrypted at rest
- **Access**: Only federation operations team, logged access
- **No Third-Party Data Sharing**: No selling, no advertising use

## How to Disable
### Configuration File Method
Edit the `config.yaml` file: