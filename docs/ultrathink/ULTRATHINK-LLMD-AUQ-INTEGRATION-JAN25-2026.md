# ULTRATHINK: LLMD + AUQ Integration for VetAssist

**Date:** 2026-01-25
**Author:** TPM (Opus 4.5)
**Council Verdict:** PROCEED WITH CAUTION (82.3% confidence)
**Concerns:** Performance (Gecko), Strategy (Raven)

---

## Executive Summary

The Council approved adopting LLMD (Longitudinal Medical Records) and AUQ (Agentic Uncertainty Quantification) with caution. This ultrathink details the implementation roadmap addressing Council concerns.

---

## Enhancement #1: LLMD (Longitudinal Medical Records)

### What It Does
- Analyzes medical records spanning 10+ years, 140+ care sites
- Clinical named-entity recognition and ontology mapping
- Temporal abstraction (identifies continuous medication periods, treatment timelines)
- Outperforms GPT-4o on production medical record tasks

### VetAssist Application
- **DD-214 Correlation**: Links discharge records to subsequent medical documentation
- **Service Connection**: Builds temporal evidence chains for disability claims
- **Multi-Source Fusion**: Handles VA, DoD, and private provider record fragmentation
- **Entity Normalization**: Resolves inconsistent terminology across sources

### Gecko's Performance Concern - ADDRESSED
```
Mitigation Strategy:
1. Deploy LLMD-8B (not larger variants) - fits in existing vLLM memory
2. Use async batch processing for non-interactive document analysis
3. Cache entity mappings to avoid re-inference
4. Run during off-peak hours for bulk processing

Expected Impact:
- +15% vLLM memory usage (8B model)
- +50ms latency for medical document classification
- Batch processing: 100 documents/hour sustainable
```

### Implementation Phases

**Phase 1 (Week 1-2): Model Integration**
- Download LLMD-8B weights to /ganuda/models/
- Add to vLLM model registry
- Create /api/v1/medical/analyze endpoint
- Basic entity extraction pipeline

**Phase 2 (Week 3-4): VetAssist Integration**
- Connect to DocumentProcessor service
- Add medical_records document type to classifier
- Integrate with evidence_tracker.py
- Store extracted entities in vetassist_pii.medical_entities table

**Phase 3 (Week 5-6): Temporal Analysis**
- Implement service connection timeline builder
- Link DD-214 events to medical conditions
- Generate "nexus letter" evidence summaries

---

## Enhancement #2: AUQ (Agentic Uncertainty Quantification)

### What It Does
- Dual-process framework (System 1: implicit confidence, System 2: explicit reflection)
- Training-free - wraps existing LLM endpoints
- Prevents "Spiral of Hallucination" where early errors propagate
- Verbalized uncertainty aligned with Council voting patterns

### VetAssist Application
- **Claims Assessment**: Confidence bounds on disability rating predictions
- **Crisis Detection**: High-certainty suicide risk indicator identification
- **Evidence Gaps**: Quantified uncertainty about missing documentation
- **Legal Safety**: Audit trail of confidence levels for claims decisions

### Raven's Strategy Concern - ADDRESSED
```
Strategic Alignment:
1. AUQ complements Constitutional Constraints - adds confidence layer
2. Integrates with existing Council voting confidence patterns
3. Non-invasive: wraps endpoints, doesn't replace models
4. Reversible: can disable without code changes

Risk Mitigation:
- Start with crisis detection (highest stakes)
- Expand to claims assessment after validation
- Log all uncertainty signals for audit
```

### Implementation Phases

**Phase 1 (Week 1): Core Integration**
- Implement UncertaintyWrapper class around vLLM completions
- Add uncertainty_score to API responses
- Create /api/v1/inference/uncertain endpoint

**Phase 2 (Week 2-3): VetAssist Integration**
- Wrap crisis_detection.py with AUQ
- Add confidence thresholds to evidence_analyzer.py
- Display uncertainty in EvidenceGapPanel component

**Phase 3 (Week 4): Council Integration**
- Weight specialist votes by UAM confidence
- Add uncertainty to Constitutional Constraints gates
- Implement "request human review" trigger at low confidence

---

## Duplo Inventory Updates

```sql
-- LLMD: Longitudinal Medical Records
INSERT INTO ai_technique_inventory (
    name, layer, version, description,
    requires_multiple_passes, memory_intensive, latency_sensitive,
    synergizes_with, conflicts_with
) VALUES (
    'LLMD', 'inference', '8B-v1',
    'Medical record temporal analysis with entity extraction. Trained on 10+ year longitudinal data.',
    FALSE, TRUE, FALSE,
    '["Thermal Memory", "A-MEM", "DocumentProcessor"]'::jsonb,
    '[]'::jsonb
);

-- AUQ: Agentic Uncertainty Quantification
INSERT INTO ai_technique_inventory (
    name, layer, version, description,
    requires_multiple_passes, memory_intensive, latency_sensitive,
    synergizes_with, conflicts_with
) VALUES (
    'AUQ', 'reasoning', '1.0',
    'Training-free uncertainty quantification. Dual-process confidence tracking.',
    FALSE, FALSE, TRUE,
    '["Constitutional Constraints", "7-Specialist Council", "Crisis Detection"]'::jsonb,
    '[]'::jsonb
);
```

---

## Jr Task Breakdown

### High Priority (P1)
1. **LLMD-MODEL-DOWNLOAD**: Download LLMD-8B to /ganuda/models/
2. **LLMD-VLLM-REGISTER**: Add LLMD to vLLM model registry
3. **AUQ-WRAPPER-IMPL**: Implement UncertaintyWrapper class
4. **VETASSIST-CRISIS-AUQ**: Wrap crisis detection with AUQ

### Medium Priority (P2)
5. **LLMD-MEDICAL-ENDPOINT**: Create /api/v1/medical/analyze
6. **LLMD-ENTITY-TABLE**: Create medical_entities table
7. **AUQ-CONFIDENCE-UI**: Add uncertainty display to frontend
8. **LLMD-DOCPROCESSOR**: Integrate with DocumentProcessor

### Lower Priority (P3)
9. **LLMD-TIMELINE-BUILDER**: Service connection timeline
10. **AUQ-COUNCIL-WEIGHT**: Council vote confidence weighting
11. **LLMD-NEXUS-GENERATOR**: Evidence summary generator

---

## Kanban Board Entries

```
BACKLOG:
- [ ] LLMD model download and registration
- [ ] AUQ wrapper implementation
- [ ] Medical entity extraction endpoint

TODO:
- [ ] Crisis detection AUQ integration
- [ ] Evidence analyzer confidence thresholds

IN PROGRESS:
(to be moved when work starts)

DONE:
- [x] Council approval obtained
- [x] Ultrathink completed
```

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| LLMD Entity Accuracy | >90% | Validation against gold standard VA records |
| AUQ Calibration | <10% error | Predicted confidence vs actual correctness |
| Crisis Detection Precision | >95% | No false positives for suicide risk |
| Claims Assessment Coverage | 80% | Records with confidence scores |

---

## For Seven Generations

Veterans' children and grandchildren often need service records for hereditary conditions. LLMD enables multi-generational medical record understanding, while AUQ ensures we never mislead families about the confidence of our assessments.

---

## Next Steps

1. TPM approval to proceed
2. Create Jr instructions for P1 tasks
3. Update kanban board
4. Begin LLMD model download

**Estimated Timeline:** 6 weeks to full integration
