# ULTRATHINK: Sprint 3 Integration Testing Strategy
## Date: January 21, 2026
## Cherokee AI Federation - For Seven Generations

---

## Executive Summary

Sprint 3 has implemented three core features for VetAssist:
1. **Document OCR/AI Extraction** - Extract evidence from uploaded medical records
2. **CFR Condition Mapping** - Map veteran conditions to 38 CFR diagnostic codes
3. **Evidence Checklist Generator** - Create personalized evidence requirements

All features have code deployed but require comprehensive integration testing before expanding the CFR database (9 → 800+ conditions). Council vote (ID: 1092bfcd53726375) recommends testing first.

---

## Council Concerns to Address

### Crawdad [SECURITY CONCERN]
**Issue**: Document handling involves sensitive veteran PII
**Testing Required**:
- Verify uploaded documents are not persisted beyond session
- Confirm PII extraction is not logged in plaintext
- Test file type validation (prevent malicious uploads)
- Verify max file size enforcement (25MB limit)
- Test for path traversal attacks in filename handling

### Gecko [PERF CONCERN]
**Issue**: OCR + AI extraction is compute-intensive
**Testing Required**:
- Measure document processing time (target: < 30s per document)
- Test concurrent upload handling
- Verify vLLM is available for AI extraction fallback
- Monitor memory usage during PDF processing (PyMuPDF)
- Test batch processing endpoint performance

---

## Feature Analysis

### Feature 1: Document OCR/AI Extraction

**Endpoints**:
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/documents/extract` | POST | Extract evidence from single document |
| `/api/v1/documents/batch` | POST | Batch extract from multiple documents |
| `/api/v1/documents/supported-types` | GET | List supported file formats |

**Service**: `medical_document_processor.py`

**Capabilities**:
- PDF text extraction via PyMuPDF (fitz)
- PDF → Image conversion for vision processing
- Diagnosis extraction (regex + ICD code detection)
- Treatment extraction
- Nexus signal detection (strong/moderate/weak)
- Document type classification

**Test Scenarios**:
1. Upload valid PDF with medical text → expect diagnoses extracted
2. Upload valid PDF with nexus language → expect nexus signals found
3. Upload 30MB file → expect 400 error (file too large)
4. Upload .exe disguised as PDF → expect rejection
5. Upload image (JPG/PNG) → expect text extraction attempt
6. Concurrent uploads (3 simultaneous) → expect all processed

**Sample Test Documents Needed**:
- Mock DD-214 (standardized format)
- Mock medical record with ICD codes
- Mock nexus letter with "at least as likely as not" language
- Mock DBQ form

### Feature 2: CFR Condition Mapping

**Endpoints**:
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/conditions/map` | POST | Map description to CFR codes |
| `/api/v1/conditions/body-systems` | GET | List body systems |
| `/api/v1/conditions/{code}` | GET | Get specific condition details |

**Database Table**: `vetassist_cfr_conditions` (9 rows currently)

**Current Conditions**:
- 5237: Lumbosacral or Cervical Strain
- 5242: Degenerative Arthritis of the Spine
- 9411: Post-Traumatic Stress Disorder (PTSD)
- 6260: Tinnitus
- 6100: Hearing Loss
- (4 more)

**Test Scenarios**:
1. Map "back pain" → expect 5237 (Lumbosacral Strain)
2. Map "PTSD" → expect 9411
3. Map "ringing in ears" → expect 6260 (Tinnitus)
4. Map "unknown condition xyz" → expect empty or low-confidence match
5. Filter by body_system="Musculoskeletal" → expect only MSK conditions
6. Get details for code 5237 → expect full rating criteria returned

**Response Validation**:
- Each match includes diagnostic_code, condition_name, body_system
- Rating criteria includes percentages (0%, 10%, 20%, etc.)
- Evidence requirements list is populated
- DBQ form reference included where applicable

### Feature 3: Evidence Checklist Generator

**Endpoint**:
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/wizard/{session_id}/evidence-checklist` | GET | Generate checklist for session |

**Database Tables**:
- `vetassist_evidence_checklists` - Session-specific checklists
- `vetassist_checklist_items` - Individual checklist items

**Service**: `evidence_service.py`

**Evidence Categories**:
1. Service Connection (DD-214, STRs, Personnel Records)
2. Current Diagnosis (Medical Records, DBQ, Diagnosis Letter)
3. Nexus Evidence (Nexus Letter, Buddy Statements, Continuity)
4. Severity Evidence (Treatment Records, Work Impact, ADL)

**Test Scenarios**:
1. Get checklist for session with claimed PTSD → expect mental health-specific items
2. Get checklist for session with back condition → expect MSK-specific items
3. Get checklist for new session (no conditions) → expect base required items
4. Mark checklist item complete → verify status persists
5. Check that checklist prioritizes required vs. optional items

---

## Integration Test Plan

### Phase 1: Endpoint Availability (Smoke Tests)
```
Test ID: SMOKE-001
- Verify all 6 endpoints return 2xx or valid error
- No 500 errors on valid requests
- Authentication not blocking (if applicable)
```

### Phase 2: Security Tests (Crawdad Priority)
```
Test ID: SEC-001 - File Type Validation
- Upload PDF → accept
- Upload JPG/PNG/TIFF → accept
- Upload .exe → reject
- Upload file with double extension (document.pdf.exe) → reject

Test ID: SEC-002 - File Size Limits
- Upload 24MB file → accept
- Upload 26MB file → reject with 400

Test ID: SEC-003 - Path Traversal
- Filename: "../../../etc/passwd" → sanitize or reject
- Filename: "test.pdf; rm -rf /" → sanitize

Test ID: SEC-004 - PII Handling
- Verify extracted data not logged to plaintext logs
- Verify temp files cleaned up after processing
```

### Phase 3: Performance Tests (Gecko Priority)
```
Test ID: PERF-001 - Single Document Processing
- Upload 5-page PDF → measure processing time
- Target: < 30 seconds
- Monitor CPU/memory during processing

Test ID: PERF-002 - Concurrent Uploads
- Upload 3 documents simultaneously
- All should complete without timeout
- No deadlocks or resource contention

Test ID: PERF-003 - Condition Mapping Speed
- Map 100 different descriptions in sequence
- Target: < 100ms average per request
```

### Phase 4: Functional Tests
```
Test ID: FUNC-001 - Document Extraction Accuracy
- Upload sample DD-214 → verify service dates extracted
- Upload sample medical record → verify diagnoses found
- Upload sample nexus letter → verify opinion language detected

Test ID: FUNC-002 - Condition Mapping Accuracy
- Test all 9 existing conditions with various descriptions
- Verify match_score > 0.5 for accurate matches
- Verify rating_criteria contains valid percentages

Test ID: FUNC-003 - Evidence Checklist Generation
- Create wizard session with claimed conditions
- Generate checklist → verify condition-specific items appear
- Verify category priorities (service_connection first)
```

### Phase 5: End-to-End Flow
```
Test ID: E2E-001 - Complete Claim Flow
1. Start wizard session
2. Enter veteran info + condition description
3. Map condition to CFR code
4. Upload supporting document
5. Extract evidence from document
6. Generate evidence checklist
7. Verify all components integrate correctly
```

---

## Test Data Requirements

### Sample Documents (create mock data)
1. `mock_dd214.pdf` - Standard DD-214 format with recognizable fields
2. `mock_medical_record.pdf` - Contains diagnosis + ICD codes
3. `mock_nexus_letter.pdf` - Contains "at least as likely as not" language
4. `mock_dbq_ptsd.pdf` - DBQ form for mental health

### Test Database State
- Ensure 9 CFR conditions are populated
- Create test wizard session(s)
- Seed checklist templates

---

## Success Criteria

| Metric | Target | Current |
|--------|--------|---------|
| Endpoint availability | 100% | TBD |
| Security tests passing | 100% | TBD |
| Performance under 30s | 100% | TBD |
| Functional accuracy | > 80% | TBD |
| E2E flow completion | 100% | TBD |

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| OCR fails on low-quality scans | Medium | Medium | Provide user guidance on scan quality |
| vLLM unavailable during extraction | Low | High | Implement graceful fallback |
| CFR mapping returns wrong code | Medium | High | Add human review step |
| Large files cause timeout | Medium | Medium | Implement async processing |

---

## Recommendation

**Execute testing in this order**:
1. Phase 1 (Smoke) - 30 mins
2. Phase 2 (Security) - 2 hours
3. Phase 3 (Performance) - 1 hour
4. Phase 4 (Functional) - 2 hours
5. Phase 5 (E2E) - 1 hour

**After testing passes**: Proceed with CFR database expansion (800+ conditions)

---

## For Seven Generations

This testing ensures:
- Veterans' sensitive documents are handled securely
- The system performs reliably under load
- Condition mapping provides accurate guidance
- Evidence checklists help veterans build stronger claims

Quality testing now prevents errors that could harm veterans later.

---

*Council Vote Reference: 1092bfcd53726375*
*Generated: 2026-01-21*
