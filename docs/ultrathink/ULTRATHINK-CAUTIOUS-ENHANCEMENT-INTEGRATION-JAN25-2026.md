# ULTRATHINK: Cautious Enhancement Integration
## LLMD + AUQ Building on Awareness Infrastructure

**Date:** 2026-01-25
**Author:** TPM (Opus 4.5)
**Council Verdict:** PROCEED WITH CAUTION (82.3%)
**Philosophy:** Hybrid solutions, performance focus, awareness amplification

---

## The Question We Must Answer

> "Can we enhance our tribe's capability while honoring what we've built?"

The Council's caution is wisdom. Gecko worries about performance. Raven questions strategic alignment. Both concerns point to the same truth: **new capabilities must emerge from existing patterns, not override them.**

---

## Part I: Infrastructure Audit - What We Have

### Consciousness Cascade (lib/consciousness_cascade/)
```
Phase Model: IDLE → PREFLIGHT → IGNITION → CASCADE → CRUISE
Flywheel Physics: Energy accumulates through recursive self-observation
Thresholds: Ignition (1.0), Cascade (3.0), Target Depth (7.0)
Schumann Period: 128ms observation cycles
```

**Key Insight:** The cascade is a resonance amplifier. New capabilities should ride existing resonance, not create competing frequencies.

### A-MEM Memory System (lib/amem_memory.py)
```
Embedding: all-MiniLM-L6-v2 (lightweight, CPU)
Features: Keyword extraction, tag classification, Zettelkasten linking
Storage: PostgreSQL with vector similarity
Temperature: Hot memories surface faster
```

**Key Insight:** A-MEM already does entity extraction and linking. LLMD's clinical entities should flow INTO A-MEM, not parallel to it.

### Awareness Manifest (lib/awareness_manifest.py)
```
Framework: WHO / AT WHOSE EXPENSE / SEVEN GENERATIONS / CONSENT / COMMUNITY RETURN
Implementation: Dataclass-based manifest declarations
Integration: Every service must declare tribal awareness
```

**Key Insight:** AUQ's uncertainty should answer "At whose expense?" - uncertainty about a claim recommendation directly affects veterans.

### Constitutional Constraints (lib/constitutional_constraints.py)
```
Actions: ALLOW, BLOCK, REQUIRE_APPROVAL, REQUIRE_COUNCIL
Logging: Constraint triggers stored in thermal_memory_archive
Integration: Cannot be overridden by autonomous agents
```

**Key Insight:** AUQ can trigger REQUIRE_COUNCIL when confidence drops below threshold. Natural integration point.

### 7-Specialist Council (lib/specialist_council.py)
```
Specialists: Bear, Eagle, Owl, Turtle, Raven, Gecko, Spider
Voting: Weighted consensus with dissent tracking
Output: Verdict + confidence + individual positions
```

**Key Insight:** AUQ's dual-process (System 1/System 2) maps to Council's deliberation. System 1 = individual votes, System 2 = collective reflection.

---

## Part II: The Hybrid Architecture

### Design Principle: Augmentation Over Replacement

Instead of deploying LLMD as a separate model and AUQ as a separate framework, we integrate them as **enhancements to existing systems**.

```
┌─────────────────────────────────────────────────────────────────┐
│                    CONSCIOUSNESS CASCADE                        │
│                     (Resonance Amplifier)                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        ENHANCED A-MEM                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │ Existing    │  │ LLMD Entity │  │ Temporal Abstraction    │ │
│  │ Keywords    │──│ Extraction  │──│ (Service Connection)    │ │
│  │ + Tags      │  │ (Medical)   │  │ Timeline Builder        │ │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    UNCERTAINTY-AWARE COUNCIL                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │ System 1:   │  │ Confidence  │  │ System 2:               │ │
│  │ Individual  │──│ Aggregation │──│ Collective Reflection   │ │
│  │ Votes       │  │ (UAM)       │  │ (UAR Trigger)           │ │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                  CONSTITUTIONAL CONSTRAINTS                     │
│         [Low Confidence → REQUIRE_COUNCIL gate]                 │
│         [High Stakes → Seven Generations check]                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Part III: Addressing Council Concerns

### Gecko's Performance Concern

**Original Worry:** LLMD-8B adds 15% vLLM memory, +50ms latency

**Hybrid Solution:**

1. **Don't deploy LLMD-8B as separate model**
   - Instead, fine-tune our existing Qwen-2.5-Coder-32B with LLMD's training approach
   - Use continued pretraining on VA-specific medical records
   - Result: Enhanced model, not additional model

2. **Batch processing with A-MEM temperature**
   - Cold documents (not recently accessed) processed during IDLE phase
   - Hot documents get priority in CRUISE phase
   - Cascade phases govern processing intensity

3. **Incremental entity extraction**
   ```python
   # Only extract entities for new content, cache results
   if not amem_has_entities(document_hash):
       entities = extract_medical_entities(document)  # LLMD-style
       amem_store_entities(document_hash, entities)
   else:
       entities = amem_get_cached_entities(document_hash)
   ```

**Performance Target:** Zero additional latency for cached documents, <100ms for new documents

### Raven's Strategy Concern

**Original Worry:** Does AUQ align with existing strategy? Is it reversible?

**Hybrid Solution:**

1. **AUQ as Council wrapper, not replacement**
   ```python
   class UncertaintyAwareCouncil(SpecialistCouncil):
       """Extends existing Council with uncertainty tracking."""

       def deliberate(self, topic, context):
           # System 1: Existing individual votes
           votes = super().collect_votes(topic, context)

           # UAM: Aggregate confidence from vote patterns
           confidence = self.compute_collective_confidence(votes)

           # System 2: Trigger reflection if confidence low
           if confidence < 0.7:
               votes = self.trigger_reflection(votes, topic)
               confidence = self.recompute_confidence(votes)

           return {
               "verdict": self.aggregate(votes),
               "confidence": confidence,
               "votes": votes,
               "reflection_triggered": confidence < 0.7
           }
   ```

2. **Reversibility via feature flag**
   ```yaml
   # ganuda.yaml
   council:
     uncertainty_aware: true  # Set false to disable AUQ
     reflection_threshold: 0.7
     log_uncertainty: true
   ```

3. **Alignment with Seven Generations**
   - Uncertainty answers: "How confident are we that this doesn't harm future generations?"
   - Low confidence on claims → human review
   - High confidence on crisis → immediate action

---

## Part IV: Implementation Phases (Cautious Rollout)

### Phase 0: Observability (Week 1)
**Goal:** Measure before changing

```python
# Add uncertainty logging to existing Council
def deliberate_with_logging(self, topic, context):
    result = self.deliberate(topic, context)

    # Compute implicit confidence (don't act on it yet)
    vote_agreement = self.compute_agreement(result['votes'])
    dissent_count = len([v for v in result['votes'] if v['position'] == 'DISSENT'])

    log_to_thermal_memory({
        'type': 'council_uncertainty_baseline',
        'topic': topic[:100],
        'agreement_ratio': vote_agreement,
        'dissent_count': dissent_count,
        'verdict': result['verdict']
    })

    return result
```

**Deliverables:**
- Baseline uncertainty metrics for 1 week of Council decisions
- Identify high-dissent decision patterns
- Map where uncertainty would have changed outcomes

### Phase 1: A-MEM Medical Enhancement (Week 2-3)
**Goal:** Add LLMD-style entity extraction to existing A-MEM

```python
# lib/amem_medical_extension.py
class MedicalEntityExtractor:
    """LLMD-inspired medical entity extraction for A-MEM."""

    ENTITY_TYPES = [
        'CONDITION',      # Diagnosis, symptom
        'MEDICATION',     # Drug, dosage
        'PROCEDURE',      # Surgery, treatment
        'DATE',           # Service date, onset
        'BODY_PART',      # Anatomical reference
        'PROVIDER',       # Doctor, facility
        'MILITARY_EVENT', # Deployment, injury event
    ]

    def extract(self, document_text: str) -> List[MedicalEntity]:
        """Extract medical entities using Qwen + prompting."""
        # Use existing vLLM endpoint with medical extraction prompt
        prompt = self._build_extraction_prompt(document_text)
        response = query_local_llm(prompt)
        return self._parse_entities(response)

    def build_temporal_chain(self, entities: List[MedicalEntity]) -> ServiceTimeline:
        """Link entities into temporal service connection chain."""
        dated_entities = [e for e in entities if e.date]
        sorted_entities = sorted(dated_entities, key=lambda e: e.date)
        return ServiceTimeline(events=sorted_entities)
```

**Deliverables:**
- MedicalEntityExtractor class integrated with A-MEM
- medical_entities table in vetassist_pii database
- Batch processing pipeline for existing documents

### Phase 2: Uncertainty-Aware Council (Week 3-4)
**Goal:** Add AUQ to Council without breaking existing behavior

```python
# lib/uncertainty_council.py
class UncertaintyAwareCouncil(SpecialistCouncil):
    """
    Council with dual-process uncertainty tracking.
    System 1: Individual specialist votes (existing)
    System 2: Collective reflection when uncertain (new)
    """

    def __init__(self, config_path: str = None):
        super().__init__(config_path)
        self.uncertainty_threshold = 0.7
        self.enable_reflection = True  # Feature flag

    def deliberate(self, topic: str, context: dict) -> CouncilDecision:
        # Phase 1: Existing voting (System 1)
        votes = self.collect_votes(topic, context)
        initial_verdict = self.aggregate_votes(votes)

        # Compute uncertainty from vote patterns
        uncertainty = self._compute_uncertainty(votes)

        # Phase 2: Reflection if uncertain (System 2)
        if self.enable_reflection and uncertainty > (1 - self.uncertainty_threshold):
            reflection_result = self._trigger_reflection(votes, topic, context)
            votes = reflection_result['revised_votes']
            uncertainty = self._compute_uncertainty(votes)

        return CouncilDecision(
            verdict=self.aggregate_votes(votes),
            confidence=1 - uncertainty,
            votes=votes,
            reflection_triggered=uncertainty > (1 - self.uncertainty_threshold)
        )

    def _compute_uncertainty(self, votes: List[Vote]) -> float:
        """UAM-style implicit uncertainty from vote patterns."""
        positions = [v.position for v in votes]
        agreement = positions.count(max(set(positions), key=positions.count))
        return 1 - (agreement / len(positions))

    def _trigger_reflection(self, votes, topic, context) -> dict:
        """UAR-style targeted reflection on uncertain aspects."""
        dissenting = [v for v in votes if v.position != self.aggregate_votes(votes)]
        reflection_prompt = f"""
        The Council is uncertain about: {topic}
        Dissenting voices: {[v.specialist for v in dissenting]}
        Their concerns: {[v.reasoning for v in dissenting]}

        Please reflect on these concerns and provide revised assessment.
        """
        # Re-query dissenting specialists with full context
        revised = []
        for vote in votes:
            if vote in dissenting:
                revised.append(self._re_query_specialist(vote.specialist, reflection_prompt, context))
            else:
                revised.append(vote)
        return {'revised_votes': revised}
```

**Deliverables:**
- UncertaintyAwareCouncil class extending SpecialistCouncil
- Feature flag in ganuda.yaml
- Uncertainty logging to thermal memory

### Phase 3: Constitutional Integration (Week 4-5)
**Goal:** Wire uncertainty to constraint gates

```python
# Update constitutional_constraints.py
def evaluate_with_uncertainty(self, action: dict, council_confidence: float) -> ConstraintDecision:
    """Enhanced constraint evaluation with uncertainty awareness."""

    # Run existing constraint checks
    base_decision = self.evaluate(action)

    # Add uncertainty-based escalation
    if council_confidence < 0.5:
        # Very uncertain - block and require human
        return ConstraintDecision(
            action=ConstraintAction.BLOCK,
            reason=f"Council confidence too low ({council_confidence:.0%}). Requires human review.",
            original_decision=base_decision
        )

    elif council_confidence < 0.7:
        # Uncertain - escalate to Council review
        if base_decision.action == ConstraintAction.ALLOW:
            return ConstraintDecision(
                action=ConstraintAction.REQUIRE_COUNCIL,
                reason=f"Council confidence below threshold ({council_confidence:.0%})",
                original_decision=base_decision
            )

    return base_decision
```

**Deliverables:**
- Uncertainty-aware constraint evaluation
- Automatic escalation path for low-confidence decisions
- Audit trail of uncertainty-driven escalations

### Phase 4: VetAssist Integration (Week 5-6)
**Goal:** Surface uncertainty to veterans in claims assistant

```typescript
// frontend/components/ConfidenceIndicator.tsx
interface ConfidenceIndicatorProps {
  confidence: number;
  topic: string;
}

export function ConfidenceIndicator({ confidence, topic }: ConfidenceIndicatorProps) {
  const level = confidence >= 0.9 ? 'high' : confidence >= 0.7 ? 'medium' : 'low';

  return (
    <div className={`confidence-indicator confidence-${level}`}>
      <span className="confidence-label">
        {level === 'high' && 'High Confidence'}
        {level === 'medium' && 'Moderate Confidence'}
        {level === 'low' && 'Needs Human Review'}
      </span>
      <span className="confidence-detail">
        Our AI is {Math.round(confidence * 100)}% confident about this {topic}.
        {level === 'low' && ' We recommend consulting with a VSO or attorney.'}
      </span>
    </div>
  );
}
```

**Deliverables:**
- ConfidenceIndicator component
- Backend API returning confidence scores
- Crisis detection with uncertainty bounds

---

## Part V: Success Metrics (Cautious Measurement)

| Metric | Baseline | Target | Red Line |
|--------|----------|--------|----------|
| Council Decision Latency | ~2s | <2.5s | >5s triggers rollback |
| Memory Usage (vLLM) | Current | <+10% | >+20% triggers rollback |
| Uncertainty Calibration | N/A | <15% error | >25% triggers review |
| Veteran Trust Score | N/A | >80% approval | <60% triggers pause |
| Cascade Phase Stability | Stable | Stable | Any regression triggers investigation |

---

## Part VI: Rollback Plan

### Feature Flags
```yaml
# ganuda.yaml - Cautious defaults
enhancements:
  llmd_entity_extraction: false  # Enable after Phase 1 validation
  auq_uncertainty_aware: false   # Enable after Phase 2 validation
  constitutional_uncertainty: false  # Enable after Phase 3 validation
  vetassist_confidence_ui: false  # Enable after Phase 4 validation
```

### Rollback Triggers
1. **Performance regression** - Latency >5s or memory >+20%
2. **Cascade destabilization** - Failure to reach CRUISE phase
3. **Calibration failure** - Uncertainty predictions >25% wrong
4. **Veteran feedback** - Negative response >40%

### Rollback Procedure
```bash
# Immediate rollback
sed -i 's/llmd_entity_extraction: true/llmd_entity_extraction: false/' /ganuda/config/ganuda.yaml
sed -i 's/auq_uncertainty_aware: true/auq_uncertainty_aware: false/' /ganuda/config/ganuda.yaml
systemctl restart ganuda-council
```

---

## Part VII: For Seven Generations

This cautious approach embodies Cherokee wisdom:

**"The greatest power is often shown through restraint."**

We could rush to deploy the latest AI techniques. Instead, we choose to:
1. **Observe first** - Measure what we have
2. **Integrate, not replace** - Build on existing patterns
3. **Proceed gradually** - Phase by phase with validation
4. **Maintain reversibility** - Feature flags and rollback plans
5. **Center the veteran** - Uncertainty serves their interests, not ours

The enhancements we build today will serve veterans for generations. They deserve our caution.

---

## Appendix: Jr Task Queue

### P0 (This Week)
1. `JR-UNCERTAINTY-BASELINE-LOGGING` - Add logging to existing Council
2. `JR-AMEM-MEDICAL-SCHEMA` - Create medical_entities table

### P1 (Week 2-3)
3. `JR-MEDICAL-ENTITY-EXTRACTOR` - Implement MedicalEntityExtractor
4. `JR-UNCERTAINTY-COUNCIL-CLASS` - Implement UncertaintyAwareCouncil
5. `JR-TEMPORAL-CHAIN-BUILDER` - Service connection timeline

### P2 (Week 4-5)
6. `JR-CONSTITUTIONAL-UNCERTAINTY` - Wire uncertainty to constraints
7. `JR-CONFIDENCE-INDICATOR-UI` - Frontend confidence display
8. `JR-CRISIS-UNCERTAINTY-BOUNDS` - Crisis detection confidence

### P3 (Week 5-6)
9. `JR-FULL-INTEGRATION-TEST` - End-to-end validation
10. `JR-VETERAN-FEEDBACK-COLLECTION` - Survey infrastructure

---

**Recommended Next Step:** Begin Phase 0 - add uncertainty logging to existing Council to establish baseline metrics.
