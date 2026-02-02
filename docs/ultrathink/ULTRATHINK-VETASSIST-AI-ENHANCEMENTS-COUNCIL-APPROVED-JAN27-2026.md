# ULTRATHINK: VetAssist AI Enhancements - Council Approved

**Date:** 2026-01-27
**Author:** TPM via Claude Code (Opus 4.5)
**Council Vote:** b942f2dcad0496e1
**Confidence:** 70%
**Status:** PROCEED WITH CAUTION

---

## Executive Summary

The Cherokee AI Council evaluated 5 proposed AI enhancements for VetAssist based on January 2026 research findings. The council approved a prioritized implementation order with two concerns flagged (7-Gen sustainability, GPU performance).

## Council Vote Summary

| Specialist | Vote | Key Concern |
|------------|------|-------------|
| Peace Chief | APPROVE | Break LLMD into phases |
| Turtle | APPROVE w/ CONCERN | 7GEN - bias/privacy risks |
| Gecko | APPROVE w/ CONCERN | PERF - GPU capacity |
| Crawdad | APPROVE | Security review required |
| Raven | APPROVE | Strategic alignment good |
| Spider | APPROVE | Integration feasible |
| Eagle Eye | APPROVE | Add accuracy metrics |

---

## Approved Enhancement Order

### Phase 1: Quick Wins (This Sprint)

#### 1.1 Fax-Quality Image Preprocessing
**Priority:** P2 → Elevated to IMMEDIATE
**Effort:** Low
**Council Support:** Unanimous

**Problem:** Research shows 38.8% F1 score drop on fax-distorted documents. VA documents often arrive via fax with noise, skew, and compression artifacts.

**Solution:** Add preprocessing pipeline before OCR/VLM extraction:
1. Deskew detection and correction
2. Noise reduction (median filter)
3. Contrast normalization
4. Binarization with adaptive thresholding

**Implementation:**
```
Upload → Fax Preprocessing → OCR/VLM → Extraction
              ↓
         [deskew, denoise, normalize, binarize]
```

**Files to Create:**
- `/ganuda/vetassist/backend/app/services/image_preprocessor.py`

**Dependencies:** OpenCV, scikit-image (likely already installed)

---

#### 1.2 Audit Trail for AI-Generated Content
**Priority:** P3 → Elevated to P2
**Effort:** Low
**Council Support:** Strong

**Problem:** Veterans need to trust AI-generated content. EU AI Act requires documentation of AI decision-making.

**Solution:** Add metadata tracking to all AI outputs:
1. Which model generated the content
2. Confidence scores
3. Source documents referenced
4. Timestamp and version

**Implementation:**
```python
class AIAuditTrail:
    content_id: str
    generated_by: str  # "qwen2.5-32b", "ocr-tesseract", etc.
    confidence: float
    sources: List[str]  # document IDs referenced
    timestamp: datetime
    model_version: str
```

**Database Schema:**
```sql
CREATE TABLE vetassist_ai_audit_trail (
    id SERIAL PRIMARY KEY,
    session_id UUID,
    content_type VARCHAR(50),  -- 'nexus_template', 'evidence_gap', 'condition_map'
    generated_by VARCHAR(100),
    confidence FLOAT,
    sources JSONB,
    input_hash VARCHAR(64),  -- SHA256 of input for reproducibility
    output_preview TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Files to Modify:**
- `/ganuda/vetassist/backend/app/services/nexus_template_generator.py`
- `/ganuda/vetassist/backend/app/services/evidence_gap_analyzer.py`
- `/ganuda/vetassist/backend/app/api/v1/endpoints/conditions.py`

---

### Phase 2: Core Upgrades (Next Sprint)

#### 2.1 Qwen 2.5-VL Document Extraction
**Priority:** P1
**Effort:** Medium
**Council Support:** Strong (with GPU capacity verification)

**Problem:** Current OCR pipeline struggles with:
- Handwritten annotations
- Complex table structures
- Multi-column layouts
- Low-quality scans

**Solution:** Replace OCR with Qwen 2.5-VL vision-language model:
- 72B parameter model rivals GPT-4o on document understanding
- Native support for form field extraction
- 128K context window handles multi-page documents

**Gecko's Concern - GPU Capacity:**
Current redfin GPU (96GB Blackwell) runs Qwen 2.5-Coder-32B for text.
Adding VL model requires:
- Option A: Time-slice between models (switch on demand)
- Option B: Use smaller Qwen 2.5-VL-7B for documents
- Option C: Offload document processing to sasass/sasass2 Mac Studios

**Recommended:** Option B - Use Qwen 2.5-VL-7B initially, upgrade if needed.

**Implementation:**
```
Document Upload
      ↓
Fax Preprocessing (Phase 1.1)
      ↓
Qwen 2.5-VL-7B Extraction
      ↓
Structured Output (JSON)
      ↓
Validation + Audit Trail (Phase 1.2)
```

**Files to Create:**
- `/ganuda/vetassist/backend/app/services/vlm_document_extractor.py`

**Files to Modify:**
- `/ganuda/vetassist/backend/app/services/document_processor.py`
- `/ganuda/vetassist/backend/app/api/v1/endpoints/documents.py`

---

#### 2.2 Summary Augmented Chunking (SAC) for CFR RAG
**Priority:** P2
**Effort:** Medium
**Council Support:** Moderate

**Problem:** Current RAG retrieval sometimes returns wrong regulatory sections. Veterans get incorrect CFR citations.

**Solution:** Implement SAC from legal AI research:
1. Generate summary for each CFR section chunk
2. Store summary embeddings alongside content embeddings
3. Query matches both summary and content
4. Re-rank results by summary relevance

**Implementation:**
```
CFR Section → Chunk → Generate Summary → Embed Both
                              ↓
Query → Embed → Match Summary + Content → Re-rank → Return
```

**Database Changes:**
```sql
ALTER TABLE vetassist_rag_chunks
ADD COLUMN summary TEXT,
ADD COLUMN summary_embedding VECTOR(384);
```

**Files to Modify:**
- `/ganuda/vetassist/backend/app/services/rag_ingestion.py`
- `/ganuda/vetassist/backend/app/services/rag_query.py`

---

### Phase 3: Advanced Features (Future Sprint)

#### 3.1 LLMD-Style Temporal Parsing
**Priority:** P1 (deferred to phases)
**Effort:** High
**Council Support:** Conditional - must be broken into sub-tasks

**Turtle's Concern:** High effort may divert resources. Break into phases.

**Problem:** Veterans have 10+ years of medical records across multiple facilities. Need to map symptoms to service dates for service-connection proof.

**Solution:** Implement LLMD-inspired temporal parsing in phases:

**Phase 3.1a: Temporal Entity Extraction**
- Extract dates, symptoms, diagnoses from medical records
- Store as structured timeline

**Phase 3.1b: Service Period Mapping**
- Map extracted events to service dates from DD-214
- Classify: IN_SERVICE, POST_SERVICE_1YR, POST_SERVICE

**Phase 3.1c: Continuity Analysis**
- Identify gaps in treatment
- Flag chronic vs acute conditions
- Generate service-connection strength score

**Files to Create:**
- `/ganuda/vetassist/backend/app/services/temporal_parser.py`
- `/ganuda/vetassist/backend/app/services/service_period_mapper.py`
- `/ganuda/vetassist/backend/app/services/continuity_analyzer.py`

---

## Security Requirements (Crawdad)

All enhancements must include:

1. **Model Security Review**
   - Audit new model dependencies
   - Scan for known vulnerabilities
   - Test for prompt injection resistance

2. **Data Protection**
   - Encrypt intermediate processing files
   - Secure temporary storage with auto-deletion
   - HIPAA compliance for medical data

3. **Access Control**
   - Audit trail accessible only to session owner
   - Model outputs logged but PII redacted in logs

---

## Performance Metrics (Eagle Eye)

Track for each enhancement:

| Metric | Baseline | Target |
|--------|----------|--------|
| Document extraction accuracy | ~70% | >90% |
| Fax document F1 score | 0.62 | >0.85 |
| CFR retrieval precision@5 | ~0.75 | >0.90 |
| Processing time per document | 15s | <10s |
| Audit trail coverage | 0% | 100% |

---

## JR Assignment Plan

| JR ID | Enhancement | Assigned To | Priority |
|-------|-------------|-------------|----------|
| JR-AI-001 | Fax Image Preprocessing | software_jr | P2 |
| JR-AI-002 | AI Audit Trail Schema | software_jr | P2 |
| JR-AI-003 | AI Audit Trail Integration | software_jr | P2 |
| JR-AI-004 | Qwen 2.5-VL Setup | infrastructure_jr | P1 |
| JR-AI-005 | VLM Document Extractor | software_jr | P1 |
| JR-AI-006 | SAC for CFR RAG | software_jr | P2 |
| JR-AI-007 | Temporal Entity Extraction | research_jr | P1 |

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| GPU overload with VLM | Medium | High | Use 7B model, monitor utilization |
| Model bias in extraction | Low | High | Audit trail + human review option |
| Privacy leak in audit logs | Low | Critical | PII redaction in logs |
| SAC increases latency | Medium | Medium | Cache summary embeddings |

---

## Seven Generations Consideration (Turtle)

**For the next 175 years:**
- Audit trail ensures AI decisions are explainable to future reviewers
- Open-source model preference (Qwen) avoids vendor lock-in
- Phased LLMD approach builds sustainable infrastructure
- Privacy-first design protects veteran data for generations

---

**FOR SEVEN GENERATIONS**

Cherokee AI Federation - Council Vote b942f2dcad0496e1
