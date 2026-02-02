# KB: VetAssist AI Enhancement Roadmap

**Date:** 2026-01-30
**Author:** TPM (Claude Code)
**Council Vote:** audit_hash `23589699dd7b4a97`, confidence 0.873 (high)
**Concerns:** Crawdad (Security), Turtle (7gen)

## Context

Full feature inventory of VetAssist platform at 192.168.132.223:3000 (70+ endpoints, 16 routes, 25+ services) combined with AI research and GitHub prior art search to identify enhancement opportunities.

## Platform Inventory Summary

- **Frontend:** Next.js App Router, 16 routes (dashboard, chat, wizard, documents, profile, admin, etc.)
- **Backend:** FastAPI, 13 endpoint groups, 25+ services
- **Key Features:** 7-specialist Council chat, crisis detection, PII redaction (Presidio), VA OAuth, wizard forms (4 VA form types), document upload/OCR, evidence gap analysis, rating calculator, research integration

## Research Sources

### AI Models Evaluated

| Model | Source | License | Use Case |
|-------|--------|---------|----------|
| docling | IBM (50K GitHub stars) | MIT | PDF/scan/DOCX to markdown with table extraction |
| Qwen2.5-VL | Alibaba | Apache 2.0 | Document understanding: form fields, tables, handwriting |
| MedGemma 1.5 | Google | Health AI TOU (code Apache 2.0) | Medical vision-language model for record extraction |
| BioMistral-NLU | Community | Apache 2.0 | Medical NER (diagnoses, medications, dates) |
| C-SSRS LLM | Research papers | N/A (methodology) | 7-point crisis severity classification |

### GitHub Tools Evaluated

| Tool | Owner | License | Use Case |
|------|-------|---------|----------|
| abd-vro | VA (department-of-veterans-affairs) | CC0 | Claims automation, evidence-to-ratings mapping |
| vets-api | VA | CC0 | Disability compensation validation logic |
| vets-website | VA | CC0 | Disability benefits UX patterns |
| vets-api-clients | VA | CC0 | Third-party API integration |
| disability-max-ratings-api | VA | CC0 | Diagnostic code to max rating CSV lookup |
| eregs/regulations-parser | 18F/eregs | CC0 | Parse 38 CFR into structured data for RAG |
| PyPDFForm | Community | MIT | Pure Python PDF form filling |
| Legal-Research-GraphRAG | Research | Research | Graph-based legal RAG with Neo4j |

### Key Research Findings

1. **LegalBench-RAG:** General rerankers hurt legal retrieval; BM25 outperforms dense retrievers for legal text
2. **DARPA LM4VSP:** Validated LLM-based C-SSRS crisis classification for veteran suicide prevention
3. **No OSS exists for nexus analysis or evidence requirement generation** — VetAssist's strongest differentiation

## Enhancement Roadmap (3 Tiers)

### Tier 1 — High Impact, Clear Path

1. **Medical Record OCR** — docling + Qwen2.5-VL for extracting tables, handwriting, form fields from DD-214s, medical records, C&P exams
2. **VA Form Auto-Fill** — PyPDFForm + abd-vro reference data to fill 21-526EZ, 21-0781, 21-4138 programmatically from wizard answers
3. **Crisis Detection Upgrade** — Three-tier: lexicon screen -> C-SSRS LLM classification -> intervention routing
4. **38 CFR RAG for Chat** — eregs/regulations-parser + BM25 retriever for regulatory grounding in Council chat

### Tier 2 — Medium Impact, Moderate Effort

5. **Evidence Gap Analysis** — Cross-reference uploaded evidence against VA rating requirements per diagnostic code
6. **Medical NER** — BioMistral-NLU or MedGemma for extracting diagnoses, medications, dates
7. **Diagnostic Code Lookup** — disability-max-ratings-api CSV integration
8. **PDF Export with Pre-Fill** — PyPDFForm for pre-filled VA forms

### Tier 3 — Research Phase

9. **Nexus Letter Assistant** — Guide veterans on nexus letter requirements (no OSS exists)
10. **VA.gov OAuth Claims Sync** — Pull existing claims via vets-api-clients
11. **Graph-based Legal RAG** — Neo4j graph RAG for cross-referencing CFR sections and BVA decisions

## Council Conditions

- **Crawdad (Security):** PII handling in document OCR must go through existing Presidio pipeline. MedGemma Health AI TOU requires compliance review before deployment. All medical data stays on-premise (local Qwen/vLLM inference).
- **Turtle (7gen):** Phased rollout — Tier 1 first, validate each enhancement works before starting next. Crisis detection upgrade must be thoroughly tested before going live. No vendor lock-in — all Tier 1 tools are open source.

## For Seven Generations

These enhancements build on the existing VetAssist foundation to better serve veterans navigating the disability claims process, reducing barriers and improving outcomes across generations.
