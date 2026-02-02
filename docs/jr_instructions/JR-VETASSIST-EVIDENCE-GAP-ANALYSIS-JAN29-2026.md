# JR Instruction: VetAssist Evidence Gap Analysis

**Date**: January 29, 2026
**Assigned To**: Software Engineer Jr
**Priority**: P2
**Estimated Effort**: 2 weeks

## Objective
Build an AI-powered evidence gap analyzer that reviews veteran claim packages and identifies missing documentation, incomplete nexus language, or weak evidence.

## Background
Veterans often submit incomplete claims lacking:
- Medical nexus opinions linking conditions to service
- Buddy/lay statements corroborating events
- Current diagnosis documentation
- Service connection evidence

Early identification of gaps improves claim outcomes.

## Implementation Steps

### Step 1: Define Evidence Checklists
Create `/ganuda/vetassist/backend/app/data/evidence_checklists.json`:

```json
{
  "PTSD_9411": {
    "required": [
      "Current diagnosis from qualified provider",
      "In-service stressor evidence",
      "Nexus statement linking PTSD to stressor"
    ],
    "strongly_recommended": [
      "Buddy statement corroborating stressor",
      "Service treatment records showing symptoms",
      "VA treatment records showing ongoing care"
    ],
    "helpful": [
      "Personal statement describing impact",
      "Employment records showing functional impairment"
    ]
  },
  "TBI_8045": {
    "required": [
      "Documentation of TBI event",
      "Current residuals assessment",
      "Nexus to service"
    ],
    ...
  }
}
```

### Step 2: Document Classifier
Create `/ganuda/vetassist/backend/app/services/document_classifier.py`:

Classify uploaded documents into types:
- DD-214 (Service dates)
- STR (Service Treatment Records)
- VA Medical Records
- Private Medical Records
- Buddy/Lay Statement
- Nexus Letter/IMO
- C&P Exam Report

Use keywords and structure:
```python
DOCUMENT_PATTERNS = {
    "dd214": ["dd form 214", "certificate of release", "discharge"],
    "str": ["service treatment", "medical record", "chronological"],
    "buddy": ["lay statement", "buddy statement", "21-10210"],
    "nexus": ["medical opinion", "nexus", "more likely than not"],
    ...
}
```

### Step 3: Gap Analysis Logic
Create `/ganuda/vetassist/backend/app/services/evidence_analyzer.py`:

```python
class EvidenceAnalyzer:
    def analyze_claim(self, claim_id: int) -> GapReport:
        # 1. Get claimed conditions
        conditions = self.get_conditions(claim_id)

        # 2. Get uploaded documents
        documents = self.get_documents(claim_id)

        # 3. Classify documents
        classified = [self.classify(doc) for doc in documents]

        # 4. Check against checklists
        gaps = []
        for condition in conditions:
            checklist = self.get_checklist(condition.diagnostic_code)
            gaps.extend(self.find_gaps(checklist, classified))

        # 5. Generate recommendations
        return self.generate_report(gaps)
```

### Step 4: Create API Endpoint
Add `/api/v1/claims/{claim_id}/evidence-gaps`:

```python
@router.get("/{claim_id}/evidence-gaps")
async def analyze_evidence_gaps(claim_id: int, db: Session):
    analyzer = EvidenceAnalyzer()
    report = analyzer.analyze_claim(claim_id)
    return {
        "claim_id": claim_id,
        "completeness_score": report.score,
        "gaps": report.gaps,
        "recommendations": report.recommendations
    }
```

### Step 5: Response Format
```json
{
    "claim_id": 1,
    "conditions": ["PTSD (9411)", "TBI (8045)"],
    "completeness_score": 65,
    "uploaded_documents": [
        {"type": "dd214", "status": "verified"},
        {"type": "va_medical", "status": "verified"}
    ],
    "gaps": [
        {
            "condition": "PTSD (9411)",
            "missing": "Buddy statement corroborating stressor",
            "severity": "strongly_recommended",
            "recommendation": "Obtain statement from fellow service member who witnessed or can confirm the stressor event"
        },
        {
            "condition": "TBI (8045)",
            "missing": "Current residuals assessment",
            "severity": "required",
            "recommendation": "Request C&P examination or obtain private neurological evaluation"
        }
    ],
    "next_steps": [
        "Request C&P exam for TBI residuals assessment",
        "Contact battle buddy for lay statement",
        "Obtain recent treatment records from VA clinic"
    ]
}
```

### Step 6: UI Integration
Add to dashboard:
- "Check Evidence" button on claim detail page
- Visual completeness meter (0-100%)
- Gap list with severity indicators (red/yellow/green)
- Downloadable checklist PDF

## Verification
Test with sample claims:

1. **Marcus Johnson** (PTSD, TBI, Knee, Hearing)
   - Has VA Medical Summary
   - Gaps: Buddy statements, nexus letters

2. **Maria Rodriguez** (MST-related)
   - Has buddy statement
   - Gaps: Medical diagnosis, nexus opinion

3. **David Chen** (Sleep Apnea, Eczema)
   - Has STRs showing diagnosis
   - Gaps: Current treatment records

## Deliverables
- [ ] Evidence checklists for top 20 conditions
- [ ] Document classifier working
- [ ] Gap analysis endpoint functional
- [ ] UI showing completeness score
- [ ] Recommendations generating correctly
- [ ] Test with all 5 sample users
