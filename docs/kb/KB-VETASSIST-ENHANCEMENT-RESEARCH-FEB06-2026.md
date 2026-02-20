# KB: VetAssist Enhancement Research — GitHub Projects & AI Papers

**Date:** 2026-02-06
**Author:** TPM (Claude Opus 4.5)
**Category:** Research / VetAssist / AI Integration
**Council Vote:** Conditional Approve (79.4%, audit hash: 0cc1c5d0138a8d6d)

---

## Executive Summary

Comprehensive research into open-source GitHub projects and 2024-2026 AI research papers for enhancing VetAssist. Identified 25+ relevant projects and 20+ papers across crisis detection, medical NER, legal RAG, form automation, and fairness monitoring.

**Key Finding:** No open-source VA disability calculator exists — must build from 38 CFR rating tables.

---

## GitHub Projects — High Priority

### Legal Document RAG

| Project | License | Stars | Key Features | VetAssist Fit |
|---------|---------|-------|--------------|---------------|
| [legalRAG](https://github.com/arulkumarann/legalRAG) | Apache 2.0 | Active | Pinecone + LangChain + Llama 3.3 | 38 CFR parsing ✅ |
| [Legal-Document-Assistant](https://github.com/lixx21/legal-document-assistant) | Permissive | Active | PostgreSQL + Elasticsearch + Airflow | Enterprise-ready |
| [RAGFlow](https://github.com/infiniflow/ragflow) | MIT | Growing | Agent capabilities + RAG | Scalable foundation |
| [RAG-based Legal Assistant](https://github.com/sougaaat/RAG-based-Legal-Assistant) | Open | Specialized | BM25 + semantic + reciprocal rank fusion | Advanced retrieval |

**Recommendation:** Start with legalRAG (Apache 2.0) for 38 CFR integration.

---

### Crisis Detection NLP

| Project | Key Features | Notes |
|---------|--------------|-------|
| [SafePost](https://github.com/gjoshi22/SafePost-Suicidal-Text-Detection) | Suicidal ideation detection, mental health chatbot | Fine-tune on veteran language |
| [SDCNL](https://github.com/ayaanzhaque/SDCNL) | ICANN 2021 publication, Reddit-trained | Academic-grade |
| [depression-suicidal-ideation-detection-NLP-flask](https://github.com/anubhavmishra123/depression-suicidal-ideation-detection-NLP-flask) | Flask API, ready to deploy | Lightweight |
| [suicidal-text-detection (gohjiayi)](https://github.com/gohjiayi/suicidal-text-detection) | Transformer-based | Modern architecture |

**Current Status:** VetAssist crisis detection is adequate per user guidance. These are Phase 3+ enhancements if needed.

---

### Medical Record Extraction & OCR

| Project | License | Key Features | VetAssist Fit |
|---------|---------|--------------|---------------|
| [medical-data-extraction](https://github.com/abhijeetk597/medical-data-extraction) | Check | FastAPI + OCR + NLP + LLM summarization | FAX document processing ✅ |
| [MedExtract](https://github.com/Soma4141/MedExtract-Intelligent-OCR-for-Accurate-Medical-Data-Extraction-) | Check | Classification + structured output | VA form processing ✅ |
| [Medical-OCR-Data-Extraction](https://github.com/Tanguy9862/Medical-OCR-Data-Extraction) | Check | 2,000+ files processed | Production-proven |

---

### Medical NLP & Entity Recognition

| Project | License | Key Features | VetAssist Fit |
|---------|---------|--------------|---------------|
| [BioBERT](https://github.com/dmis-lab/biobert) | MIT | Biomedical pre-training, NER, relation extraction | Condition extraction ✅ |
| [BlueBERT](https://huggingface.co/bionlp/bluebert_pubmed_mimic_uncased_L-12_H-768_A-12) | Open | PubMed + MIMIC-III training | Best medical NER |
| [spark-nlp-workshop (Clinical)](https://github.com/JohnSnowLabs/spark-nlp-workshop) | Check | John Snow Labs clinical models | Enterprise scale |
| [Medical-Data-NER-with-BERT](https://github.com/ZunainAliAzam/Medical-Data-NER-with-BERT) | Check | Step-by-step fine-tuning guide | Implementation reference |

**Recommendation:** BlueBERT for condition extraction (Phase 2).

---

### PDF Form Automation

| Project | License | Key Features | VetAssist Fit |
|---------|---------|--------------|---------------|
| [PyPDFForm](https://github.com/chinapandaman/PyPDFForm) | MIT | Python form filling, field inspection | VA form auto-fill ✅ |
| [pdfforms](https://github.com/altaurog/pdfforms) | Check | CSV batch processing, US tax forms | Batch processing |
| [pdf-fill-form](https://github.com/tpisto/pdf-fill-form) | Check | Node.js alternative | If Node.js preferred |

**Status:** PyPDFForm selected for Phase 1 (Jr #599 queued).

---

## AI Research Papers — Key Findings

### Crisis Detection & Mental Health (P0 - Safety)

| Paper | Finding | Application |
|-------|---------|-------------|
| [Detecting PTSD in Clinical Interviews](https://arxiv.org/abs/2504.01216) (April 2025) | Mental-RoBERTa significantly outperforms general models (AUPRC=0.758) | PTSD screening pipeline |
| [Fine-tuned Multiclass Classifier](https://arxiv.org/abs/2511.04698) (Nov 2024) | Mental-RoBERTa F1=0.87 for 6-class mental health | Multi-condition classification |
| [AI-Driven Mental Health Surveillance](https://www.mdpi.com/2504-2289/9/1/16) (2024) | Reduced crisis triage from 9 hours to 8-13 minutes | Real-time chat monitoring |
| [SPAADE-DR Dataset](https://arxiv.org/html/2412.03796v1) (Dec 2024) | LLM-annotated dataset for PTSD, anxiety, depression, suicidal ideation | Training data |

**Key Model:** Mental-RoBERTa — domain-specific, high accuracy, explainable.

---

### Legal Document Understanding (P1 - Accuracy)

| Paper | Finding | Application |
|-------|---------|-------------|
| [Knowledge Graphs + RAG for Legal](https://arxiv.org/html/2502.20364v1) (Feb 2025) | Vector stores + KGs + hierarchical NMF for legal norms | CFR knowledge graph |
| [LRAGE Evaluation](https://arxiv.org/html/2504.01840v1) | Multi-round RAG achieves 78.67% recall | Eligibility determination |
| [Legal RAG Hallucinations](https://dho.stanford.edu/wp-content/uploads/Legal_RAG_Hallucinations.pdf) | 58-80% hallucination in general LLMs on legal tasks | **Must use RAG grounding** |
| [Automated Legal Knowledge Graph](https://arxiv.org/html/2508.06368v1) | Document → NLP → ontology → KG construction | Automated CFR ingestion |

**Critical:** General LLMs hallucinate 58-80% on legal tasks. RAG grounding mandatory.

---

### Medical Document Extraction (P0 - Efficiency)

| Paper | Finding | Application |
|-------|---------|-------------|
| [Accurate Medical NER](https://arxiv.org/abs/2412.08255) (Dec 2024) | BlueBERT outperforms general BERT on medical NER | Condition extraction |
| [Clinical NER with BERT + RAG](https://www.mdpi.com/2079-9282/14/18/3676) | Dictionary-infused RAG improves extraction | Hybrid approach |
| [JAMIA Systematic Review](https://academic.oup.com/jamia/advance-article/doi/10.1093/jamia/ocaf176/8287208) | BERT dominates clinical NLP; 57.7% information extraction focus | Architecture guidance |

**Key Model:** BlueBERT — pre-trained on PubMed + MIMIC-III, best for medical domains.

---

### Conversational AI for Benefits (P1 - UX)

| Paper | Finding | Application |
|-------|---------|-------------|
| [SuDoSys](https://arxiv.org/html/2411.10681v1) (Nov 2024) | Stage-aware multi-turn dialogue, WHO PM+ guidelines | Benefits wizard structure |
| [AI-Powered Rules as Code](https://digitalgovernmenthub.org/publications/ai-powered-rules-as-code-experiments-with-public-benefits-policy/) | Must digitize source policies; humans-in-loop critical | CFR rules engine |
| [FAFSA AI Assistant](https://www.studentaid.gov/) (Dec 2024) | Real-world government AI deployment lessons | Benchmark reference |

**Pattern:** Stage-aware dialogue + rules-as-code + human review.

---

### Fairness & Bias Detection (P1 - Compliance)

| Paper | Finding | Application |
|-------|---------|-------------|
| [Bias in Healthcare AI](https://www.nature.com/articles/s41746-025-01503-7) (2025) | Explicit vs implicit bias; algorithmic preprocessing mitigations | Audit framework |
| [AI Fairness Survey](https://journals.plos.org/digitalhealth/article?id=10.1371/journal.pdig.0000864) | Lifecycle fairness: conception → development → deployment → surveillance | Monitoring pipeline |
| [Algorithmic Bias in Public Health](https://pmc.ncbi.nlm.nih.gov/articles/PMC12325396/) | "Silent threat to equity" in underserved populations | Equity outcomes |

**Requirement:** Continuous fairness monitoring across veteran demographics.

---

## Critical Gaps Identified

| Gap | Impact | Recommendation |
|-----|--------|----------------|
| No open-source VA disability calculator | Must build custom | Use 38 CFR rating tables |
| No 38 CFR-specific RAG | General legal RAG exists | Fine-tune legalRAG on CFR corpus |
| No veteran-specific NLP models | General medical models available | Fine-tune BlueBERT on VA terminology |
| No nexus letter analysis tools | Critical for claims | Develop custom templates + LLM |

---

## Integration Priority Matrix

| Phase | Enhancement | Dependency | Risk | Status |
|-------|-------------|------------|------|--------|
| **1** | Crisis Resources Tab | None | None | Jr #598 queued |
| **1** | PyPDFForm Integration | None | Low | Jr #599 queued |
| **2** | BlueBERT Medical NER | GPU hosting | Medium | Pending security review |
| **2** | legalRAG for 38 CFR | Vector DB | Medium | Pending architecture |
| **3** | Fairness Monitoring | Baseline metrics | Low | After Phase 2 |
| **3** | Multi-round RAG Validation | Phase 2 RAG | Low | After Phase 2 |

---

## License Compliance Summary

| License | Projects | Commercial Use | Notes |
|---------|----------|----------------|-------|
| MIT | PyPDFForm, RAGFlow, BioBERT | ✅ Yes | Permissive |
| Apache 2.0 | legalRAG, TorchIO | ✅ Yes | Permissive |
| AGPL | Orbeon Forms | ⚠️ Check | May require source release |
| Unspecified | Many crisis detection repos | ⚠️ Check | Verify before integration |

**Policy:** Prioritize MIT/Apache 2.0 for minimum licensing risk.

---

## Related Documents

- Ultrathink: `ULTRATHINK-VETASSIST-PHASE1-ENHANCEMENTS-FEB06-2026.md`
- Jr Instructions: `JR-VETASSIST-CRISIS-RESOURCES-TAB-FEB06-2026.md`, `JR-VETASSIST-PYPDFFORM-INTEGRATION-FEB06-2026.md`
- Previous Research: `KB-VETASSIST-AI-ENHANCEMENT-RESEARCH-JAN29-2026.md`

---

## References

### GitHub Repositories
- https://github.com/arulkumarann/legalRAG
- https://github.com/infiniflow/ragflow
- https://github.com/dmis-lab/biobert
- https://github.com/chinapandaman/PyPDFForm
- https://github.com/gjoshi22/SafePost-Suicidal-Text-Detection
- https://github.com/abhijeetk597/medical-data-extraction

### arXiv Papers
- https://arxiv.org/abs/2504.01216 (PTSD Detection)
- https://arxiv.org/abs/2511.04698 (Mental Health Classification)
- https://arxiv.org/abs/2412.08255 (Medical NER)
- https://arxiv.org/html/2502.20364v1 (Legal Knowledge Graphs)
- https://arxiv.org/html/2411.10681v1 (SuDoSys Dialogue)

### Government & Standards
- VA Forms: https://www.va.gov/find-forms/
- 38 CFR: https://www.ecfr.gov/current/title-38
- Veterans Crisis Line: https://www.veteranscrisisline.net/

---

*For Seven Generations — Knowledge preserved for future enhancement cycles.*
