# ULTRATHINK: VetAssist Sprint 3 Architecture
## Date: January 20, 2026
## Cherokee AI Federation - For Seven Generations

---

## Council Vote Summary

**Confidence**: 87.2% (High)
**Concerns**: 4 specialists flagged concerns (Raven/Strategy, Peace Chief/Consensus, Gecko/Perf, Turtle/7-Gen)

### Top 3 Priorities Selected:
1. **Document OCR/AI extraction** - Extract data from uploaded medical records, DD-214s, buddy statements
2. **Condition auto-mapping to CFR codes** - Map veteran-described conditions to 38 CFR diagnostic codes
3. **Evidence checklist generator** - Generate personalized evidence requirements for each claimed condition

---

## Architecture Decisions

### 1. Document OCR/AI Extraction

**Purpose**: Veterans upload medical records, DD-214s, and other documents. System extracts structured data automatically.

**Architecture**:
```
Upload → OCR Engine → AI Extraction → Structured Data → Wizard Pre-fill
```

**Implementation**:
- **OCR Layer**: Use Tesseract OCR or docTR (transformer-based) for text extraction
- **AI Extraction**: Use vLLM (Qwen2.5-Coder-32B) to parse extracted text into structured fields
- **Document Types**:
  - DD-214: Service dates, branch, MOS, discharge type
  - Medical Records: Diagnoses, treatment dates, providers
  - Buddy Statements: Relationship, observations, dates
  - Nexus Letters: Doctor credentials, medical opinion, rationale

**API Endpoint**:
```
POST /api/v1/wizard/{session_id}/extract
  - file: UploadFile
  - document_type: enum (dd214, medical, buddy, nexus)
Returns: Extracted fields + confidence scores
```

**Database**:
```sql
CREATE TABLE vetassist_extracted_documents (
    id SERIAL PRIMARY KEY,
    session_id UUID REFERENCES vetassist_wizard_sessions(session_id),
    document_type VARCHAR(50),
    original_file_id INT REFERENCES vetassist_wizard_files(id),
    extracted_data JSONB,
    confidence_score FLOAT,
    reviewed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 2. Condition Auto-Mapping to CFR Codes

**Purpose**: Map veteran-described conditions to 38 CFR diagnostic codes for accurate claim filing.

**Architecture**:
```
Veteran Input → NLP Matching → CFR Code Lookup → Rating Criteria Display
```

**Data Source**: 38 CFR Part 4 - Schedule for Rating Disabilities
- 15+ body systems
- 800+ diagnostic codes
- Rating percentages (0%, 10%, 20%, ... 100%)

**Implementation**:
- **Condition Database**: Pre-built table of conditions with synonyms
- **Semantic Search**: Use embeddings for fuzzy matching ("bad back" → "lumbosacral strain" → Code 5237)
- **VA.gov API Integration**: Leverage official VA APIs if available

**API Endpoint**:
```
POST /api/v1/conditions/map
  - description: str (veteran's description)
  - body_system: Optional[str]
Returns: Matched conditions with CFR codes, rating criteria, evidence requirements
```

**Database**:
```sql
CREATE TABLE vetassist_cfr_conditions (
    id SERIAL PRIMARY KEY,
    diagnostic_code VARCHAR(10) UNIQUE,
    condition_name VARCHAR(255),
    body_system VARCHAR(100),
    synonyms TEXT[],
    rating_criteria JSONB,  -- {0: "criteria", 10: "criteria", ...}
    evidence_requirements TEXT[],
    dbq_form VARCHAR(50),   -- Associated DBQ form number
    embedding VECTOR(384)   -- For semantic search
);
```

### 3. Evidence Checklist Generator

**Purpose**: Generate personalized checklist of evidence needed for each claimed condition.

**Architecture**:
```
Claimed Conditions → CFR Requirements → Evidence Types → Checklist
```

**Evidence Types**:
- **Service Connection**: DD-214, service records, in-service treatment records
- **Current Diagnosis**: Recent medical records, DBQ, diagnosis letter
- **Nexus Evidence**: IMO, buddy statements, continuity evidence
- **Severity Evidence**: Treatment records, work impact statements, ADL limitations

**Implementation**:
- Pull evidence requirements from `vetassist_cfr_conditions` table
- Generate prioritized checklist based on claim strength analysis
- Track what evidence has been uploaded vs. what's missing
- Provide guidance on how to obtain missing evidence

**API Endpoint**:
```
GET /api/v1/wizard/{session_id}/evidence-checklist
Returns: Categorized checklist with status, priority, guidance
```

---

## Specialist Concerns

### Raven (Strategy):
"Consider phased rollout. Document OCR is high-value but complex. Start with DD-214 extraction which has standardized format, then expand to medical records."

### Turtle (7-Gen):
"Document extraction must preserve veteran privacy. Extracted PII should be encrypted at rest and purged after session completion unless veteran explicitly consents to retention for future claims."

### Gecko (Performance):
"OCR + AI extraction will be compute-intensive. Consider async processing with progress callbacks. Don't block wizard flow on extraction completion."

### Peace Chief (Consensus):
"Ensure CFR mapping can be overridden by veteran. Auto-suggestions are helpful but veterans know their conditions - don't force algorithmic categorization."

---

## VA.gov API Integration

**Opportunity**: VA maintains APIs for benefits claims, health records, and veteran verification.

**Relevant APIs**:
- VA Forms Library API - Form metadata and field requirements
- Benefits Intake API - Direct submission pathway
- Health API - FHIR-based health records (if veteran-authorized)

**Action**: Research VA.gov developer portal for available integrations.

---

## Implementation Priority

1. **Week 1**: CFR Conditions database (static data, foundational)
2. **Week 2**: Condition mapping API (depends on CFR database)
3. **Week 3**: Evidence checklist generator (depends on mapping)
4. **Week 4**: Document OCR/extraction (parallel track, complex)

---

## For Seven Generations

These features directly serve veteran welfare by:
- Reducing claim filing complexity
- Ensuring correct diagnostic codes (avoid underclaiming)
- Providing clear guidance on evidence requirements
- Accelerating the claims process

The Cherokee value of "going to water" (cleansing, renewal) applies - we help veterans navigate the cleansing process of claiming what they are owed for their service.

---

*Council Vote ID: 215a9e2dda944d25*
*Generated: 2026-01-20*
