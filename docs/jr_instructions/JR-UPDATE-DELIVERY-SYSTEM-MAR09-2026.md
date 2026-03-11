# JR Task #1202: Design Signed Artifact Update Delivery System

**Date**: 2026-03-09
**Priority**: High
**Type**: Business / Design
**Output**: `/ganuda/docs/business/UPDATE-DELIVERY-SYSTEM-MAR09-2026.md`

## Context

Federation nodes need a secure, governed mechanism for receiving software updates. The current deployment model uses direct file operations and systemd restarts. For external customers, we need a proper update delivery system that respects sovereignty (pull-based, not push), ensures integrity (signed artifacts), supports air-gap environments, and integrates with the existing governance topology (council vote before applying). The SAGA pattern in the Jr executor already provides rollback capability — this design should build on that.

## Task

Create a design document for the federation's update delivery system. Covers artifact signing, update channels, pull-based delivery, rollback, air-gap support, and Longhouse integration. This is a design document — no code.

## Steps

1. Create the output file at `/ganuda/docs/business/UPDATE-DELIVERY-SYSTEM-MAR09-2026.md`.
2. Add a header section with document metadata: date, author (Jr executor), version (1.0), review status (DRAFT), design constraint references (DC-7 Noyawisgi for transformation, DC-10 Reflex Principle for tiered response).
3. Write an **Overview** section explaining the update delivery problem: how do N federation nodes across M customer environments receive updates securely, verifiably, and with governance approval?
4. Write a **Signed Artifacts** section:
   - Signing method: GPG signatures (primary) and cosign/sigstore (secondary/future)
   - Artifact format: tarball with manifest (file list + SHA256 hashes) + detached signature
   - Key management: federation signing key (rotated annually), public key shipped with installation
   - Verification: every node verifies signature before unpacking, reject unsigned artifacts
   - Chain of trust: signing key itself signed by root key held offline
5. Write an **Update Channels** section:
   - Stable: production-ready, council-approved, minimum 72-hour soak in beta
   - Beta: feature-complete, passed automated tests, available for early adopters
   - Nightly: automated builds, no stability guarantee, development use only
   - Channel selection: per-node configuration, default is Stable
   - Channel promotion: Nightly -> Beta requires automated test pass; Beta -> Stable requires council vote
6. Write a **Pull-Based Delivery** section:
   - Nodes poll update server on configurable interval (default: daily for Stable, 6h for Beta, 1h for Nightly)
   - Update server is a simple HTTPS endpoint serving manifests and artifacts
   - No push capability — federation never initiates connections to customer nodes
   - Manifest check: node downloads manifest first (small), compares versions, only downloads artifact if newer
   - Bandwidth consideration: delta updates where possible (future enhancement)
7. Write a **Rollback Capability** section:
   - Pre-update snapshot: preserve current state before applying update
   - SAGA pattern integration: each update step has a compensating action
   - Automatic rollback triggers: service health check fails within 5 minutes of update
   - Manual rollback: CLI command to revert to previous version
   - Rollback depth: maintain last 3 versions for rollback
   - Reference existing Jr executor SAGA pattern implementation
8. Write an **Air-Gap Support** section:
   - Offline bundle: downloadable package containing artifacts + signatures + manifests
   - USB transfer: signed bundle can be transferred via USB drive
   - Offline verification: signature verification works without network access (public key is local)
   - Bundle creation tool: CLI that packages specific version for offline delivery
   - Audit trail: air-gap updates still logged locally in thermal memory
9. Write a **Governance Integration** section:
   - Update proposal: when a new update is available, create a Longhouse proposal
   - Council vote: council reviews changelog, votes on applying the update
   - Auto-apply rules: security patches can be auto-applied if council has pre-approved security channel (DC-10 reflex tier)
   - Scheduled maintenance window: updates apply during configured maintenance window after approval
   - Notification: Slack/Telegram notification on update availability, vote result, and application status
10. Write an **Architecture Diagram** section (ASCII art) showing: Update Server -> Manifest Check -> Download -> Verify Signature -> Council Vote -> Apply -> Health Check -> Rollback if unhealthy.
11. Write a **Security Considerations** section: supply chain attacks, key compromise procedures, update server availability (CDN), man-in-the-middle prevention.

## Acceptance Criteria

- Output file exists at `/ganuda/docs/business/UPDATE-DELIVERY-SYSTEM-MAR09-2026.md`
- Signed artifact format is fully specified (signing method, verification steps)
- Three update channels defined with promotion criteria
- Pull-based model is explicit — no push capability
- Rollback mechanism integrates with existing SAGA pattern
- Air-gap mode is fully described with offline verification
- Governance integration uses Longhouse voting
- ASCII architecture diagram is included

## Constraints

- No code changes — design document only
- Pull-based only — the federation NEVER pushes to customer nodes
- Must work in air-gap environments (Enterprise tier requirement)
- Must integrate with existing governance topology, not create a parallel approval system
- Do not specify implementation language or framework — keep it architecture-level
- Reference existing federation patterns (SAGA, Longhouse, Fire Guard health checks) rather than inventing new ones
