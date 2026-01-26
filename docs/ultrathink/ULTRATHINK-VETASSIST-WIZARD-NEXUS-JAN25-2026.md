# ULTRATHINK: VetAssist Claim Wizard + Nexus Letter Assistant

**Date:** 2026-01-25
**Author:** TPM (Opus 4.5)
**Council Verdict:** APPROVED (7-0)
**Key Requirement:** Robust validation and testing

---

## Council Feedback Summary

All seven specialists approved with emphasis on safeguards:

| Specialist | Vote | Key Concern |
|------------|------|-------------|
| Turtle | APPROVE | Enhance veteran support |
| Raven | APPROVE | Streamline processes |
| Crawdad | APPROVE | Critical for efficiency and accuracy |
| Gecko | APPROVE | **Robust testing and validation crucial** |
| Eagle Eye | APPROVE | **Robust validation to mitigate risks** |
| Spider | APPROVE | **Critical safeguards for accuracy** |
| Peace Chief | APPROVE | **Robust validation processes** |

**Consensus:** Proceed with implementation, but validation is non-negotiable.

---

## Feature 1: Claim Wizard Form Selection

### The Problem

Veterans must choose the correct VA form:
- **VA 21-526EZ**: Original disability compensation claim
- **VA 20-0995**: Supplemental claim (new evidence for denied claim)
- **VA 20-0996**: Higher-level review (same evidence, different reviewer)
- **VA 10182**: Board of Veterans' Appeals

**Wrong form = 6+ month delay** in veteran benefits.

### Decision Tree Logic

```
START
│
├─ Is this your FIRST claim for this condition?
│   ├─ YES → VA 21-526EZ (Original Claim)
│   └─ NO → Continue
│
├─ Was your previous claim DENIED or rated lower than expected?
│   ├─ NO (still pending) → Wait for decision
│   └─ YES → Continue
│
├─ Do you have NEW EVIDENCE not previously submitted?
│   ├─ YES → VA 20-0995 (Supplemental Claim)
│   └─ NO → Continue
│
├─ Do you believe the VA made a CLEAR ERROR in reviewing your evidence?
│   ├─ YES → VA 20-0996 (Higher-Level Review)
│   └─ NO → Continue
│
├─ Has it been MORE than 1 year since decision?
│   ├─ YES (outside appeal window) → VA 20-0995 with new evidence
│   └─ NO → VA 10182 (Board Appeal)
│
END
```

### Implementation Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    CLAIM WIZARD FLOW                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Step 1: Claim History                                          │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ • Have you filed for this condition before?              │   │
│  │ • What was the outcome? (denied/approved/pending)        │   │
│  │ • When was the decision? (date picker)                   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                           ↓                                     │
│  Step 2: Evidence Assessment                                    │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ • Do you have new medical evidence?                      │   │
│  │ • Do you have buddy statements not previously submitted? │   │
│  │ • Did VA fail to consider evidence you submitted?        │   │
│  └─────────────────────────────────────────────────────────┘   │
│                           ↓                                     │
│  Step 3: Form Recommendation (with explanation)                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ RECOMMENDED: VA 20-0995 (Supplemental Claim)             │   │
│  │                                                          │   │
│  │ WHY: You have new evidence (medical records from 2025)   │   │
│  │ that was not part of your original 2023 claim.           │   │
│  │                                                          │   │
│  │ [Download Form] [Continue to Evidence Checklist]         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Validation Safeguards (Per Council)

1. **Never auto-submit** - Always show recommendation with explanation
2. **Confidence indicator** - Show why this form was recommended
3. **Edge case warnings** - Flag complex situations for VSO consultation
4. **Audit logging** - Track all recommendations for review
5. **Human override** - Veteran can always choose different form

### Database Schema

```sql
-- Form recommendation tracking
CREATE TABLE IF NOT EXISTS wizard_form_recommendations (
    id SERIAL PRIMARY KEY,
    session_id UUID NOT NULL,

    -- Decision inputs
    is_first_claim BOOLEAN,
    previous_outcome VARCHAR(50),  -- 'denied', 'approved', 'pending'
    decision_date DATE,
    has_new_evidence BOOLEAN,
    evidence_types TEXT[],
    clear_error_claimed BOOLEAN,

    -- Recommendation
    recommended_form VARCHAR(20) NOT NULL,  -- '526EZ', '0995', '0996', '10182'
    confidence_score FLOAT,
    recommendation_reason TEXT,

    -- Validation
    edge_case_flags TEXT[],
    vso_consultation_recommended BOOLEAN DEFAULT FALSE,

    -- User action
    user_accepted BOOLEAN,
    user_selected_form VARCHAR(20),
    override_reason TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## Feature 2: Nexus Letter Assistant

### The Problem

A nexus letter is a medical opinion connecting:
- **In-service event** (injury, exposure, stressor)
- **Current disability** (diagnosis, symptoms)
- **Causal link** ("at least as likely as not")

Most veterans don't know:
1. What evidence they need
2. How to present timeline clearly
3. What gaps exist in their documentation

### Nexus Letter Template Structure

```
┌─────────────────────────────────────────────────────────────────┐
│                    NEXUS LETTER TEMPLATE                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  HEADER                                                         │
│  • Veteran Name: [AUTO-FILLED FROM PROFILE]                     │
│  • Claimed Condition: [FROM WIZARD]                             │
│  • Date: [CURRENT]                                              │
│                                                                 │
│  SECTION 1: SERVICE HISTORY                                     │
│  • Service Dates: [FROM DD-214]                                 │
│  • Duty Stations: [EXTRACTED]                                   │
│  • Relevant MOS/Duties: [USER INPUT]                            │
│                                                                 │
│  SECTION 2: IN-SERVICE EVENTS                                   │
│  [POPULATED FROM medical_entities WHERE service_connection_relevant = TRUE]
│  • Date: [entity_date]                                          │
│  • Event: [entity_text]                                         │
│  • Documentation: [document source]                             │
│                                                                 │
│  SECTION 3: CURRENT CONDITION                                   │
│  • Diagnosis: [FROM CONDITIONS DB]                              │
│  • Symptoms: [USER INPUT]                                       │
│  • Functional Limitations: [USER INPUT]                         │
│                                                                 │
│  SECTION 4: MEDICAL OPINION (FOR PROVIDER TO COMPLETE)          │
│  "Based on my review of the veteran's medical records and       │
│   examination, it is my medical opinion that [CONDITION]        │
│   is at least as likely as not (50% or greater probability)     │
│   caused by or related to [IN-SERVICE EVENT]."                  │
│                                                                 │
│  SECTION 5: RATIONALE (FOR PROVIDER)                            │
│  [SUGGESTED POINTS BASED ON EVIDENCE]                           │
│  • Timeline supports service connection                         │
│  • Medical literature supports causal link                      │
│  • No intervening cause identified                              │
│                                                                 │
│  SIGNATURE BLOCK                                                │
│  Provider Name: _____________                                   │
│  License/Credentials: _____________                             │
│  Date: _____________                                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Evidence Gap Detection

```python
class EvidenceGapAnalyzer:
    """Analyze medical records for nexus letter completeness."""

    REQUIRED_EVIDENCE = {
        'service_connection': [
            'in_service_event',      # Must have documented event during service
            'current_diagnosis',     # Must have current medical diagnosis
            'continuity_of_care',    # Should show ongoing treatment
        ],
        'presumptive': [
            'qualifying_service',    # Vietnam, Gulf War, etc.
            'qualifying_condition',  # Agent Orange conditions, etc.
            'diagnosis_timeframe',   # Within presumptive period
        ]
    }

    def analyze(self, entities: List[MedicalEntity], claim_type: str) -> GapAnalysis:
        """
        Analyze entities for evidence completeness.
        Returns gaps with severity and suggestions.
        """
        gaps = []

        # Check for in-service event documentation
        service_events = [e for e in entities if e.service_connection_relevant]
        if not service_events:
            gaps.append(Gap(
                type='missing_in_service_event',
                severity='critical',
                description='No documented in-service event found',
                suggestion='Upload service treatment records, buddy statements, or incident reports'
            ))

        # Check for current diagnosis
        current_dx = [e for e in entities
                      if e.entity_type == 'CONDITION'
                      and e.entity_date and e.entity_date.year >= 2024]
        if not current_dx:
            gaps.append(Gap(
                type='missing_current_diagnosis',
                severity='critical',
                description='No recent diagnosis documentation found',
                suggestion='Obtain current medical evaluation documenting your condition'
            ))

        # Check for continuity
        # ... additional gap detection logic

        return GapAnalysis(gaps=gaps, completeness_score=self._score(gaps))
```

### Implementation Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                  NEXUS LETTER ASSISTANT                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  INPUT LAYER                                                    │
│  ├─ Uploaded Documents → OCR → medical_entities table           │
│  ├─ DD-214 Parser → Service dates, duty stations                │
│  ├─ Conditions Database → CFR diagnostic codes                  │
│  └─ User Input → Symptoms, functional limitations               │
│                           ↓                                     │
│  ANALYSIS LAYER                                                 │
│  ├─ Entity Extraction (existing document_processor)             │
│  ├─ Temporal Mapping (service_connection_timeline)              │
│  ├─ Gap Detection (EvidenceGapAnalyzer)                         │
│  └─ Strength Scoring (nexus_strength field)                     │
│                           ↓                                     │
│  OUTPUT LAYER                                                   │
│  ├─ Nexus Letter Template (populated)                           │
│  ├─ Evidence Gap Panel (EvidenceGapPanel.tsx - exists)          │
│  ├─ Timeline Visualization                                      │
│  └─ Confidence Indicator (per AUQ integration)                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Validation Safeguards (Per Council)

1. **Templates only** - Never generate actual medical opinions
2. **Provider signature required** - Clear that doctor must sign
3. **Disclaimer prominent** - "This is a template, not legal/medical advice"
4. **Gap severity levels** - Critical vs suggested improvements
5. **VSO referral** - Recommend VSO for complex cases
6. **Audit trail** - Log all generated templates

---

## Jr Task Breakdown

### Claim Wizard Form Selection (3 tasks)

#### Task 1: Form Selection Decision Engine
**Assigned:** Software Engineer Jr.
**Priority:** P1
**Deliverables:**
- `/ganuda/vetassist/backend/app/services/form_selector.py`
- Decision tree implementation
- Unit tests for all paths

#### Task 2: Wizard UI Steps
**Assigned:** Software Engineer Jr.
**Priority:** P1
**Deliverables:**
- `/ganuda/vetassist/frontend/components/wizard/ClaimHistoryStep.tsx`
- `/ganuda/vetassist/frontend/components/wizard/EvidenceAssessmentStep.tsx`
- `/ganuda/vetassist/frontend/components/wizard/FormRecommendationStep.tsx`

#### Task 3: Form Recommendation API
**Assigned:** Software Engineer Jr.
**Priority:** P1
**Deliverables:**
- `/ganuda/vetassist/backend/app/api/v1/endpoints/form_selection.py`
- Database migration for wizard_form_recommendations
- Audit logging integration

### Nexus Letter Assistant (3 tasks)

#### Task 4: Evidence Gap Analyzer
**Assigned:** Software Engineer Jr.
**Priority:** P1
**Deliverables:**
- `/ganuda/vetassist/backend/app/services/evidence_gap_analyzer.py`
- Gap detection logic
- Severity scoring
- Integration with medical_entities table

#### Task 5: Nexus Template Generator
**Assigned:** Software Engineer Jr.
**Priority:** P2
**Deliverables:**
- `/ganuda/vetassist/backend/app/services/nexus_template_generator.py`
- Template population from entities
- PDF export capability

#### Task 6: Nexus UI Components
**Assigned:** Software Engineer Jr.
**Priority:** P2
**Deliverables:**
- `/ganuda/vetassist/frontend/components/nexus/NexusLetterBuilder.tsx`
- `/ganuda/vetassist/frontend/components/nexus/TimelineVisualization.tsx`
- Integration with existing EvidenceGapPanel

---

## Database Migrations

```sql
-- Migration: wizard_form_recommendations
-- File: /ganuda/vetassist/backend/migrations/005_wizard_form_recommendations.sql

CREATE TABLE IF NOT EXISTS wizard_form_recommendations (
    id SERIAL PRIMARY KEY,
    session_id UUID NOT NULL,

    -- Decision inputs
    is_first_claim BOOLEAN,
    previous_outcome VARCHAR(50),
    decision_date DATE,
    has_new_evidence BOOLEAN,
    evidence_types TEXT[],
    clear_error_claimed BOOLEAN,

    -- Recommendation
    recommended_form VARCHAR(20) NOT NULL,
    confidence_score FLOAT,
    recommendation_reason TEXT,

    -- Validation flags
    edge_case_flags TEXT[],
    vso_consultation_recommended BOOLEAN DEFAULT FALSE,

    -- User action
    user_accepted BOOLEAN,
    user_selected_form VARCHAR(20),
    override_reason TEXT,

    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_wizard_form_session ON wizard_form_recommendations(session_id);
CREATE INDEX idx_wizard_form_recommended ON wizard_form_recommendations(recommended_form);

-- Migration: nexus_letter_templates
-- File: /ganuda/vetassist/backend/migrations/006_nexus_letter_templates.sql

CREATE TABLE IF NOT EXISTS nexus_letter_templates (
    id SERIAL PRIMARY KEY,
    session_id UUID NOT NULL,

    -- Template content
    veteran_name VARCHAR(200),
    claimed_condition VARCHAR(500),
    service_dates DATERANGE,

    -- Populated sections (JSON for flexibility)
    service_history JSONB,
    in_service_events JSONB,
    current_condition JSONB,
    suggested_rationale TEXT[],

    -- Analysis results
    evidence_gap_analysis JSONB,
    completeness_score FLOAT,
    nexus_strength FLOAT,

    -- Status
    status VARCHAR(50) DEFAULT 'draft',  -- draft, exported, signed
    exported_at TIMESTAMP,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_nexus_session ON nexus_letter_templates(session_id);
CREATE INDEX idx_nexus_condition ON nexus_letter_templates(claimed_condition);
```

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Form Selection Accuracy | >95% | Compare to VSO recommendations |
| Gap Detection Recall | >90% | Catch critical missing evidence |
| Template Completeness | >80% | Auto-populated fields |
| User Override Rate | <20% | Low override = good recommendations |
| VSO Referral Appropriate | >95% | Complex cases flagged correctly |

---

## For Seven Generations

These tools serve veterans who sacrificed for our nation. A wrong form delays their benefits. A missing nexus point weakens their claim.

We build with care because the veteran on the other end may be:
- Struggling financially while waiting for benefits
- Dealing with service-connected health issues
- Supporting a family that depends on VA compensation

Our code must honor their service.

---

## Next Steps

1. Create Jr instructions for Tasks 1-6
2. Queue tasks in work queue
3. Deploy database migrations
4. Monitor Jr execution
5. Integration testing before release
