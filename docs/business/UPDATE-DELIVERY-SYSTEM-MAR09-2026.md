# UPDATE-DELIVERY-SYSTEM-MAR09-2026.md

## Document Metadata
- **Date**: 2026-03-09
- **Author**: Jr Executor
- **Version**: 1.0
- **Review Status**: DRAFT
- **Design Constraint References**:
  - DC-7 Noyawisgi for transformation
  - DC-10 Reflex Principle for tiered response

## Overview
The federation nodes require a secure, governed mechanism for receiving software updates. Currently, the deployment model involves direct file operations and systemd restarts. For external customers, we need a proper update delivery system that respects sovereignty (pull-based, not push), ensures integrity (signed artifacts), supports air-gap environments, and integrates with the existing governance topology (council vote before applying). The SAGA pattern in the Jr executor already provides rollback capability — this design should build on that.

## Signed Artifacts
### Signing Method
- **Primary**: GPG signatures
- **Secondary/Future**: cosign/sigstore

### Artifact Format
- **Tarball**: Contains files and a manifest
- **Manifest**: File list with SHA256 hashes
- **Detached Signature**: Separate file for the signature

### Key Management
- **Federation Signing Key**: Rotated annually
- **Public Key**: Shipped with installation

### Verification
- Every node verifies the signature before unpacking the artifact
- Reject unsigned artifacts

### Chain of Trust
- The signing key is signed by a root key held offline

## Update Channels
### Stable
- **Description**: Production-ready, council-approved
- **Soak Time**: Minimum 72-hour soak in beta

### Beta
- **Description**: Feature-complete, passed automated tests
- **Availability**: Available for early adopters

### Nightly
- **Description**: Automated builds, no stability guarantee
- **Usage**: Development use only

### Channel Selection
- Per-node configuration
- Default: Stable

### Channel Promotion
- **Nightly to Beta**: Requires automated test pass
- **Beta to Stable**: Requires council vote

## Pull-Based Delivery
### Polling Interval
- **Stable**: Daily
- **Beta**: Every 6 hours
- **Nightly**: Every hour

### Update Server
- Simple HTTPS endpoint serving manifests and artifacts
- No push capability — federation never initiates connections to customer nodes

### Manifest Check
- Node downloads the manifest first (small)
- Compares versions
- Downloads artifact if newer

### Bandwidth Consideration
- Delta updates where possible (future enhancement)

## Rollback Capability
### Pre-Update Snapshot
- Preserve current state before applying update

### SAGA Pattern Integration
- Each update step has a compensating action

### Automatic Rollback Triggers
- Service health check fails within 5 minutes of update

### Manual Rollback
- CLI command to revert to previous version

### Rollback Depth
- Maintain last 3 versions for rollback

### Reference
- Existing Jr executor SAGA pattern implementation

## Air-Gap Support
### Offline Bundle
- Downloadable package containing artifacts, signatures, and manifests

### USB Transfer
- Signed bundle can be transferred via USB drive

### Offline Verification
- Signature verification works without network access (public key is local)

### Bundle Creation Tool
- CLI that packages specific version for offline delivery

### Audit Trail
- Air-gap updates still logged locally in thermal memory

## Governance Integration
### Update Proposal
- When a new update is available, create a Longhouse proposal

### Council Vote
- Council reviews changelog, votes on applying the update

### Auto-Apply Rules
- Security patches can be auto-applied if council has pre-approved security channel (DC-10 reflex tier)

### Scheduled Maintenance Window
- Updates apply during configured maintenance window after approval

### Notification
- Slack/Telegram notification on update availability, vote result, and application status

## Architecture Diagram