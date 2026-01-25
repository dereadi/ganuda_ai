# KB Article: VetAssist AI Enhancement Initiative
## Cherokee AI Federation
### KB-2026-0120-001

---

## Summary

Council-approved initiative to integrate cutting-edge AI capabilities into VetAssist based on 2025-2026 AI research analysis. Four enhancement areas prioritized by council vote (84.3% confidence).

---

## Enhancement Priorities

| Priority | Enhancement | Target Accuracy | Jr Instruction |
|----------|-------------|-----------------|----------------|
| 1 (CRITICAL) | Crisis Detection Upgrade | 93-98% | `JR-VETASSIST-CRISIS-DETECTION-UPGRADE.md` |
| 2 (HIGH) | RAG for VA Regulations | 100% citations | `JR-VETASSIST-RAG-REGULATIONS.md` |
| 2 (HIGH) | MedGemma Document AI | 85% extraction | `JR-VETASSIST-MEDGEMMA-DOCS.md` |
| 3 (MEDIUM) | Predictive Rating | 92% accuracy | `JR-VETASSIST-RATING-PREDICTION.md` |

---

## Research Foundation

### Crisis Detection (PMC/MDPI 2024, RoBERTa-CNN)
- Current: Keyword matching (~70% estimated)
- Target: RoBERTa-CNN with 98% accuracy
- Key: LIME explainability for transparency
- Safety: Always show Veterans Crisis Line (988, Press 1)

### RAG System (LexRAG, LegalBench-RAG)
- Target documents: 38 CFR Part 4, M21-1 Manual, BVA Decisions
- Requires: pgvector on bluefin PostgreSQL
- Critical: 100% citation accuracy (no hallucinations)

### MedGemma Document Understanding (Google Research)
- Extracts: Diagnoses, treatments, nexus signals
- Supports: PDF, images (including handwritten)
- Reference: Taiwan NHIA processed 30,000+ pathology reports

### Rating Prediction (Springer 2025)
- Algorithm: Random Forest (92% accuracy on 597K records)
- Features: Condition type, evidence strength, history
- Ethics: Always estimate with confidence intervals, never guarantee

---

## Key Documents

- **Research**: `/ganuda/docs/research/AI-RESEARCH-VETASSIST-ENHANCEMENT-JAN2026.md`
- **ULTRATHINK**: `/ganuda/docs/ultrathink/ULTRATHINK-VETASSIST-AI-ENHANCEMENTS-JAN2026.md`
- **Jr Instructions**: `/ganuda/docs/jr_instructions/JR-VETASSIST-*.md`

---

## Council Vote Record

- **Question**: VetAssist AI Enhancement priorities
- **Result**: REVIEW REQUIRED (84.3% confidence)
- **Consensus**: Crisis detection prioritized for veteran safety
- **Concerns**: Security (data handling), Performance, Strategy, 7-Gen impact
- **Date**: January 20-21, 2026

---

## Dependencies

### Infrastructure
- pgvector extension on bluefin PostgreSQL
- GPU inference on redfin (Blackwell)
- Sentence-transformers for embeddings

### Python Packages
```
transformers>=4.35.0
torch>=2.0.0
lime>=0.2.0
sentence-transformers
psycopg2-binary
PyMuPDF (fitz)
pillow
httpx
scikit-learn
```

---

## Security Considerations (Crawdad)

1. All medical documents encrypted at rest (AES-256)
2. PII tokenization before ML processing
3. No training on user data without consent
4. Audit logging for document access
5. HIPAA compliance review required

---

## Seven Generations Impact (Turtle)

- **Gen 1-2**: Prevent veteran suicides NOW, reduce claim prep time
- **Gen 3-4**: Accurate guidance prevents bad claims, handle all formats
- **Gen 5-7**: Data foundation for continuous improvement, VA integration ready

---

## Known Issues

### Jr Worker Execution (As of Jan 2026)
Workers mark tasks complete without generating code due to RLM parsing issue. Detailed Jr instruction files contain full implementation guidance for manual engineering or future automated execution.

Task IDs in queue: 203-206 (assigned to it_triad_jr)

---

## Related KB Articles

- KB-VETASSIST-VA-OAUTH-SESSION-MANAGEMENT (pending)
- KB-VETASSIST-CFR-CONDITIONS-DATABASE

---

*Cherokee AI Federation - For Seven Generations*
