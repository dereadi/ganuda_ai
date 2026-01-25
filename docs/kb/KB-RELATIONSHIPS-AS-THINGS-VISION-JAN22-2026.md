# KB: Relationships as Things - Vision Architecture Implications

**Source:** Charles Simon, Future AI Society
**Date:** January 22, 2026
**Relevance:** VLM Integration, Knowledge Representation

## Core Insight

Traditional AI approaches fail at cognition because:
- **Neural networks**: Recognize patterns, not things
- **LLMs**: Predict tokens, don't understand meaning
- **Graphs**: Store objects but miss relationship metadata

**The Breakthrough:** Treat relationships as first-class things (nodes), not just edges.

## Key Concepts

### What Current AI Misses
1. **Provenance** - Where knowledge came from
2. **Context** - Under what conditions it applies
3. **Conditionals** - If-then relationships
4. **Temporal State** - History vs current state
5. **Confidence** - How certain we are

### Example: "Pho can play outside if the weather is sunny"
- Requires storing the conditional clause separately from current state
- Requires tracking state changes over time
- Three-year-old understands this; current AI struggles

## Application to Tribal Vision (VLM)

### Current VLM Output
```json
{
  "description": "Person detected near door",
  "camera_id": "front_door"
}
```

### Enhanced with Relationships-as-Things
```
Thing: Person_001
  - detected_at: front_door_camera
  - timestamp: 2026-01-22T08:00:00
  - confidence: 0.92
  - spatial_relation: near(Door_001)
  - temporal_relation: not_present(5_minutes_ago)

Relationship: near(Person_001, Door_001)
  - distance_estimate: 2m
  - provenance: vlm_inference
  - confidence: 0.85

Conditional: Alert IF Person AND NOT authorized_person
  - applies_when: after_hours
  - action: notify_security
```

### Implementation Implications

1. **VLM Output Enrichment**
   - Extract entities (things) from descriptions
   - Identify spatial relationships (near, inside, above)
   - Track temporal changes between frames

2. **Knowledge Graph Integration**
   - Store VLM detections in UKS-like structure
   - Relationships get their own nodes with metadata
   - Enable queries like "show all unauthorized access attempts"

3. **Conditional Alerting**
   - Define rules as relationship graphs
   - Evaluate against current state
   - Track provenance of alerts

## Connection to Cherokee AI Architecture

### Thermal Memory Enhancement
Current thermal memory stores facts. Enhanced version stores:
- Facts (things)
- Relationships between facts (also things)
- Metadata on relationships (provenance, confidence, time)

### Council Integration
Specialists can reason about relationships:
- Crawdad: Security implications of spatial relationships
- Eagle Eye: Temporal patterns in detections
- Turtle: Long-term relationship patterns (7 generations)

## UKS (Universal Knowledge Store)
- Open source from Future AI Society
- Single data structure for things AND relationships
- Biologically plausible (cortical columns)
- Inheritance with exceptions built-in

## Next Steps for Implementation

1. **Phase 1**: Enhance VLM to extract entities and relationships
2. **Phase 2**: Store in graph structure with relationship-as-thing model
3. **Phase 3**: Build conditional alerting on relationship graph
4. **Phase 4**: Temporal reasoning across frame sequences

## References
- Future AI Society: https://futureaisociety.org
- Brain Simulator III: Open source project
- Video: "Relationships as Things" (Part 1 of 2)
- Part 2 focuses on sequences and time

---
*"Intelligence isn't just about what exists. It's also about what happens."*
