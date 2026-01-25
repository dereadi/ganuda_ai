# KB: VLM Optic Nerve Architecture

**Date:** January 22, 2026
**Status:** Jr Instructions Created, Queued for Implementation

## Overview

The Cherokee AI Federation vision system mirrors biological visual processing:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         OPTIC NERVE ARCHITECTURE                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   BIOLOGICAL              CHEROKEE AI                                       │
│   ──────────              ───────────                                       │
│                                                                             │
│   Retina          ──►     Camera Frames                                     │
│   Optic Nerve     ──►     Bluefin VLM (Qwen2-VL-7B, RTX 5070)              │
│   V1/V2 Cortex    ──►     Entity Extractor + Relationship Storer           │
│   Association     ──►     Clause Evaluator (thermal_clauses)               │
│   Prefrontal      ──►     Redfin Brain (Qwen2.5-32B, RTX 5090)             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Data Flow

| Stage | Component | Location | Output |
|-------|-----------|----------|--------|
| 1 | Camera | Various | JPEG frames |
| 2 | VLM Describe | Bluefin:8090 | Text description |
| 3 | Entity Extractor | Bluefin | Things + Relationships |
| 4 | Relationship Storer | Bluefin | thermal_relationships records |
| 5 | Clause Evaluator | Bluefin | Triggered actions |
| 6 | Brain Escalation | Redfin:8080 | Decisions |

## Key Components

### 1. VLM Service (vlm-bluefin.service)
- Port: 8090
- Model: Qwen2-VL-7B-Instruct
- GPU: RTX 5070 (12GB)
- Endpoint: `/v1/vlm/describe`

### 2. Entity Extractor (vlm_entity_extractor.py)
- Parses VLM description
- Uses redfin LLM for precise extraction
- Returns: Entities, Relationships, Anomaly flag

### 3. Relationship Storer (vlm_relationship_storer.py)
- Creates thermal_memory_archive entries for entities
- Creates thermal_relationships with provenance='vlm'
- Atomic transactions

### 4. Clause Evaluator (vlm_clause_evaluator.py)
- Evaluates thermal_clauses against new relationships
- Determines action: none, log, alert, escalate
- Escalates to redfin brain when needed

### 5. Optic Nerve Pipeline (vlm_optic_nerve.py)
- Orchestrates complete flow
- API endpoint: `/v1/optic/process`
- Returns VisionResult with all stages

## Database Tables

```sql
-- Entities stored as memories
thermal_memory_archive (type='vlm_entity')

-- Relationships between entities
thermal_relationships (provenance='vlm')

-- Conditional rules
thermal_clauses (clause_type='if_then')
```

## Escalation Criteria

Events escalated to redfin brain:
- Novel situations (no matching clause)
- High-stakes detections (priority <= 2)
- Clauses with `escalate_on_trigger=true`
- Anomalies detected
- Low confidence requiring reasoning

## Cultural Note

Architecture honors Creek (Muscogee) wisdom alongside Cherokee principles.
Erika Hammontree connection noted.

## Jr Tasks Queued

| ID | Task | Status |
|----|------|--------|
| 257 | VLM Entity Extractor | Assigned |
| 258 | VLM Relationship Storer | Assigned |
| 259 | VLM Clause Evaluator | Assigned |
| 260 | VLM Optic Nerve Pipeline | Assigned |

## For Seven Generations

This architecture enables:
- Visual understanding that builds knowledge over time
- Pattern recognition across generations of frames
- Wisdom accumulation in thermal memory
- Contextual decision-making like biological vision
