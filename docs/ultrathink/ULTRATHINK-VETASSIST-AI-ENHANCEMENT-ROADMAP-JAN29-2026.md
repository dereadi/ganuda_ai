# ULTRATHINK: VetAssist AI Enhancement Roadmap
**Date**: January 29, 2026
**Author**: TPM Council
**Council Confidence**: 84.3%

## Executive Summary

VetAssist is currently functional for basic claims workflow (wizard, file uploads, research queries). Based on cutting-edge AI research, three enhancement areas would dramatically improve veteran outcomes:

1. **MedGemma Integration** - Medical document understanding
2. **Enhanced RAG Pipeline** - 38 CFR and VA regulations
3. **Evidence Gap Analysis** - Multimodal document assessment

## Current VetAssist State

### Working Features
- User authentication (5 test accounts verified)
- Claims wizard (21-526EZ, ITF, etc.)
- File upload/attachment
- Research query submission
- Scratchpad notes
- Dashboard with claims/files/research display

### Test Data Examples (from /ganuda/vetassist/test_uploads/)

| User | Document Type | Key Conditions |
|------|--------------|----------------|
| Marcus Johnson | VA Medical Summary | PTSD, TBI, Knee DJD, Hearing Loss |
| Sarah Williams | DD-2796 Post-Deployment | Back pain, Anxiety, Tinnitus |
| David Chen | Service Treatment Records | Shoulder, Sleep Apnea, Eczema |
| Maria Rodriguez | Buddy Statement | MST-related PTSD, Headaches |
| James Thompson | DD-2807-1 Separation | Knee, Back, Depression |

---

## Enhancement 1: MedGemma Integration

### What is MedGemma 1.5?
Google's open-source medical AI model (January 2026) optimized for:
- Medical text comprehension
- EHR interpretation (90% accuracy on QA benchmarks)
- Structured data extraction from clinical notes
- Image analysis (radiology, pathology)

### VetAssist Integration Points

#### A. Document Upload Processing
When veteran uploads STRs or VA medical records:
```
1. OCR extraction (if PDF/image)
2. MedGemma processes text
3. Extract: conditions, dates, providers, treatments
4. Auto-populate claims wizard fields
```

#### B. Condition Identification
From Marcus's VA Medical Summary:
```
Input: "Post-Traumatic Stress Disorder (PTSD) - Service Connected
        First diagnosed: 2014
        Current severity: Moderate-Severe"

MedGemma Output:
{
  "condition": "PTSD",
  "icd_code": "F43.10",
  "diagnostic_code": "9411",
  "onset_date": "2014",
  "severity": "moderate-severe",
  "service_connected": true
}
```

#### C. Nexus Statement Assistance
From Maria's buddy statement, MedGemma could identify:
- Timeline: "early 2014" change in demeanor
- Symptoms: "withdrawn, difficulty sleeping, panic attacks"
- Causation language: "directly related to military service"

### Implementation Approach
1. Deploy MedGemma on redfin AI cluster (has GPU resources)
2. Create `/api/v1/ai/analyze-document` endpoint
3. Queue document analysis jobs through existing research queue
4. Store extracted metadata in vetassist_pii on goldfin

---

## Enhancement 2: RAG for VA Regulations

### Current Gap
Veterans researching their claims lack easy access to:
- 38 CFR rating criteria
- M21-1 Adjudication Manual
- BVA precedent decisions

### Proposed Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Veteran Query  │────▶│  Vector Search   │────▶│  Knowledge      │
│  "PTSD rating   │     │  (ChromaDB)      │     │  Graph (Neo4j)  │
│   criteria"     │     │                  │     │                 │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                │                        │
                                ▼                        ▼
                        ┌──────────────────┐     ┌─────────────────┐
                        │  38 CFR Chunks   │────▶│  Related        │
                        │  with Citations  │     │  Provisions     │
                        └──────────────────┘     └─────────────────┘
```

### Data Sources to Ingest
1. **38 CFR Part 4** - Rating schedule (all diagnostic codes)
2. **38 CFR Part 3** - Adjudication rules
3. **M21-1** - VA Adjudication Manual
4. **BVA Decisions** - Board of Veterans Appeals precedents

### Example RAG Response
Query: "What evidence is needed for sleep apnea claim?"

Response:
```
Under 38 CFR § 4.97, Diagnostic Code 6847, sleep apnea is rated based on:

- 100%: Chronic respiratory failure with carbon dioxide retention
        or cor pulmonale, or requires tracheostomy
- 50%:  Requires use of breathing assistance device such as CPAP
- 30%:  Persistent day-time hypersomnolence
- 0%:   Asymptomatic but with documented sleep disorder

EVIDENCE NEEDED:
1. Current sleep study (polysomnography)
2. CPAP prescription/usage records
3. Service treatment records showing onset during service
4. Nexus statement linking condition to service

Citation: 38 CFR § 4.97, DC 6847 (2025)
```

### Implementation Approach
1. Scrape/download 38 CFR from eCFR.gov
2. Chunk with semantic boundaries (by section/subsection)
3. Embed using text-embedding-3-large or equivalent
4. Store in ChromaDB on bluefin
5. Build knowledge graph linking DCs to body systems
6. Create `/api/v1/research/regulations` endpoint

---

## Enhancement 3: Evidence Gap Analysis

### Problem Statement
Veterans often submit incomplete claims lacking:
- Medical nexus opinions
- Buddy/lay statements
- Current diagnosis documentation
- Service connection evidence

### AI Solution: Evidence Completeness Checker

When veteran's claim package is analyzed:
```
CLAIM: PTSD (DC 9411)
UPLOADED EVIDENCE:
  ✓ DD-214 (service dates confirmed)
  ✓ VA Medical Summary (current diagnosis)
  ✓ Service Treatment Records (in-service treatment)
  ⚠ Missing: Independent Medical Opinion (IMO)
  ⚠ Missing: Buddy Statement corroborating stressor

RECOMMENDATIONS:
1. Obtain buddy statement from fellow service member
   who witnessed stressor event
2. Consider private IMO linking PTSD to service
3. Request C&P exam through VA
```

### Multimodal Capabilities
For uploaded images (X-rays, scans):
- GLM-4.5V or Qwen2.5-VL could analyze
- Identify relevant findings
- Cross-reference with claimed conditions

### Implementation Approach
1. Build evidence checklist per claim type
2. Parse uploaded documents for evidence types
3. Compare against checklist
4. Generate gap report with recommendations
5. Create `/api/v1/claims/{id}/evidence-gaps` endpoint

---

## Implementation Roadmap

### Phase 1: Foundation (2 weeks)
- [ ] Set up MedGemma on redfin cluster
- [ ] Create document analysis queue
- [ ] Build basic OCR pipeline for PDFs
- [ ] Jr Instruction: JR-VETASSIST-MEDGEMMA-SETUP

### Phase 2: RAG Pipeline (3 weeks)
- [ ] Download and chunk 38 CFR
- [ ] Set up ChromaDB vector store
- [ ] Build retrieval pipeline
- [ ] Integrate with research endpoint
- [ ] Jr Instruction: JR-VETASSIST-RAG-REGULATIONS

### Phase 3: Evidence Analysis (2 weeks)
- [ ] Define evidence checklists per form type
- [ ] Build document classifier
- [ ] Create gap analysis logic
- [ ] Add UI for recommendations
- [ ] Jr Instruction: JR-VETASSIST-EVIDENCE-ANALYSIS

### Phase 4: Integration & Testing (1 week)
- [ ] End-to-end testing with test accounts
- [ ] Performance optimization
- [ ] Security review (PII handling)
- [ ] Documentation

---

## Council Concerns Addressed

1. **PII Protection**: All document analysis happens on goldfin (PII VLAN)
2. **Model Accuracy**: MedGemma benchmarked at 90% - still needs human review
3. **Regulatory Currency**: RAG pipeline must auto-update when CFR changes
4. **Veteran Trust**: AI suggestions framed as "recommendations" not "decisions"

---

## Resource Requirements

| Component | Node | Resources |
|-----------|------|-----------|
| MedGemma | redfin | GPU (A100), 40GB VRAM |
| ChromaDB | bluefin | 50GB SSD, 16GB RAM |
| Neo4j | bluefin | 20GB SSD, 8GB RAM |
| Document Queue | bluefin | Existing research queue |

---

## Success Metrics

1. **Document Processing**: 80% of uploads auto-extract conditions
2. **RAG Relevance**: 90% of regulation queries return useful citations
3. **Evidence Gaps**: 70% of identified gaps lead to claim improvement
4. **Veteran Satisfaction**: Measured through post-claim surveys

---

## Next Steps

1. Create JR instructions for each phase
2. Submit Council vote for resource allocation
3. Assign Jrs to implementation tracks
4. Set up monitoring dashboards

**TPM Note**: This roadmap positions VetAssist as a leading AI-assisted claims platform while maintaining veteran trust through transparency and human oversight.
