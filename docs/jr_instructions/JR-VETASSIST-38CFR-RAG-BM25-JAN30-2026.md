# Jr Instruction: VetAssist 38 CFR RAG with BM25 Retriever

**Date:** 2026-01-30
**Priority:** Tier 1 — High Impact
**Council Vote:** `23589699dd7b4a97` (confidence 0.873)
**Assigned To:** Software Engineer Jr.
**Depends On:** Existing RAG endpoints and Council chat service

## Objective

Integrate parsed 38 CFR (Code of Federal Regulations) Part 4 (Schedule for Rating Disabilities) into VetAssist's chat RAG pipeline using BM25 retrieval, so the Council chat can ground responses in actual VA regulatory text.

## Background

- VetAssist has existing RAG endpoints but no regulatory data source
- `eregs/regulations-parser` (CC0 license, 18F project) parses federal regulations into structured data
- LegalBench-RAG research finding: BM25 outperforms dense retrievers for legal text retrieval
- 38 CFR Part 4 contains the VA's Schedule for Rating Disabilities — the core reference for all disability claims
- Current chat has no regulatory grounding — responses are based on LLM training data only

## Steps

### Step 1: Install dependencies

```bash
cd /ganuda/vetassist/backend
source venv/bin/activate
pip install rank-bm25 nltk
pip freeze > requirements.txt
```

### Step 2: Download and parse 38 CFR Part 4

**File to create:** `/ganuda/vetassist/backend/app/services/cfr_parser.py`

This service should:
1. Download 38 CFR Part 4 from the eCFR API (public, no auth required):
   ```
   GET https://www.ecfr.gov/api/versioner/v1/full/current/title-38.xml?part=4
   ```
   or use the JSON endpoint:
   ```
   GET https://www.ecfr.gov/api/renderer/v1/content/enhanced/current/title-38/chapter-I/part-4
   ```
2. Parse the XML/JSON into structured sections
3. Each section should be a document chunk with:
   - `section_number` (e.g., "4.71a")
   - `title` (e.g., "Schedule of ratings—musculoskeletal system")
   - `text` (the regulation text)
   - `diagnostic_codes` (list of codes in this section)
4. Store parsed sections to JSON file: `/ganuda/vetassist/backend/app/data/cfr_part4_sections.json`

**Directory to create:** `/ganuda/vetassist/backend/app/data/`

### Step 3: Build BM25 index

**File to create:** `/ganuda/vetassist/backend/app/services/cfr_retriever.py`

This service should:
1. Load parsed CFR sections from the JSON file
2. Build a BM25 index using `rank_bm25.BM25Okapi`
3. Tokenize using NLTK word tokenizer with lowercasing
4. Provide a `retrieve(query: str, top_k: int = 5)` method that:
   - Tokenizes the query
   - Runs BM25 retrieval
   - Returns top_k sections with scores
5. Cache the index in memory (load once at startup)
6. Include a `refresh()` method to reload from JSON

```python
from rank_bm25 import BM25Okapi
from nltk.tokenize import word_tokenize

class CFRRetriever:
    def __init__(self, sections_path: str):
        self.sections = json.load(open(sections_path))
        corpus = [word_tokenize(s['text'].lower()) for s in self.sections]
        self.bm25 = BM25Okapi(corpus)

    def retrieve(self, query: str, top_k: int = 5) -> list:
        tokens = word_tokenize(query.lower())
        scores = self.bm25.get_scores(tokens)
        top_indices = scores.argsort()[-top_k:][::-1]
        return [
            {**self.sections[i], 'bm25_score': float(scores[i])}
            for i in top_indices if scores[i] > 0
        ]
```

### Step 4: Integrate with chat RAG pipeline

**File to modify:** `/ganuda/vetassist/backend/app/services/chat_service.py` (or RAG service)

Before sending a user question to the Council chat LLM:
1. Run the question through the CFR retriever
2. If relevant sections found (BM25 score > threshold), include them as context
3. Format the context as:
   ```
   REGULATORY CONTEXT (38 CFR Part 4):

   Section 4.71a — Schedule of ratings—musculoskeletal system:
   [section text]

   Section 4.130 — Schedule of ratings—mental disorders:
   [section text]
   ```
4. Append to the system prompt or user context before LLM call
5. Log retrieval with `[RAG-CFR]` prefix including query, top section numbers, and top BM25 score

### Step 5: Add CFR search API endpoint

**File to modify:** `/ganuda/vetassist/backend/app/api/endpoints/` (appropriate router)

Add endpoint for direct CFR search:
```
GET /api/regulations/search?q=knee+injury&top_k=5
Response: { "results": [ { "section_number": "4.71a", "title": "...", "text": "...", "bm25_score": 12.3 } ] }
```

This allows the frontend to show "Relevant Regulations" in the UI.

### Step 6: Add frontend regulations panel

**File to create/modify:** In the chat interface or a new regulations page

Show a collapsible "Relevant Regulations" panel when the chat response includes CFR context:
- Section number and title as header
- Expandable text content
- Link to full section on ecfr.gov
- Visual indicator that the response is grounded in regulations

### Step 7: Schedule periodic CFR refresh

**File to create:** `/ganuda/vetassist/backend/app/services/cfr_updater.py`

A script that can be run periodically (monthly) to re-download and re-parse 38 CFR Part 4:
1. Fetch latest from eCFR API
2. Compare with existing parsed data
3. Update JSON file if changed
4. Log changes with `[CFR-UPDATE]` prefix

This can be triggered manually or via cron — regulations don't change frequently.

## Security Requirements (Crawdad)

- eCFR API is public and free — no authentication needed, no PII involved
- CFR text is public domain (US government works)
- BM25 retrieval is local computation — no external API calls at query time
- Parsed CFR data stored as JSON on disk, not in database (no PII contamination risk)

## Verification

1. Run CFR parser → verify JSON file has sections with diagnostic codes
2. Query BM25 with "knee injury rating" → verify musculoskeletal sections returned
3. Send chat message about PTSD rating → verify chat response includes 38 CFR 4.130 context
4. Check logs for `[RAG-CFR]` entries with section numbers
5. Verify `/api/regulations/search` returns relevant results

## For Seven Generations

Grounding VetAssist responses in actual federal regulations means veterans receive accurate, verifiable guidance rather than general advice. This builds trust and improves claim outcomes.
