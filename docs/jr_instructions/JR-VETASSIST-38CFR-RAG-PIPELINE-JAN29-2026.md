# JR Instruction: VetAssist 38 CFR RAG Pipeline

**Date**: January 29, 2026
**Assigned To**: Infrastructure Jr
**Priority**: P1
**Estimated Effort**: 3 weeks

## Objective
Build a RAG (Retrieval Augmented Generation) pipeline for VA regulations (38 CFR) to provide veterans with accurate, cited answers about rating criteria and claims requirements.

## Background
Veterans need easy access to 38 CFR rating criteria, M21-1 Adjudication Manual, and BVA precedent decisions. Current research queries lack regulatory specificity.

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Veteran Query  │────▶│  Vector Search   │────▶│  Knowledge      │
│  "PTSD rating"  │     │  (ChromaDB)      │     │  Graph (Neo4j)  │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                │                        │
                                ▼                        ▼
                        ┌──────────────────────────────────────┐
                        │  Response with Citations             │
                        │  "Under 38 CFR § 4.130, DC 9411..." │
                        └──────────────────────────────────────┘
```

## Implementation Steps

### Step 1: Download 38 CFR
```bash
ssh dereadi@192.168.132.222  # bluefin
mkdir -p /ganuda/data/regulations
cd /ganuda/data/regulations

# Download from eCFR.gov
curl -o 38cfr_part3.xml "https://www.ecfr.gov/api/versioner/v1/full/current/title-38.xml?part=3"
curl -o 38cfr_part4.xml "https://www.ecfr.gov/api/versioner/v1/full/current/title-38.xml?part=4"
```

### Step 2: Set Up ChromaDB
```bash
pip install chromadb
```

Create `/ganuda/services/rag/chromadb_setup.py`:
```python
import chromadb
from chromadb.config import Settings

client = chromadb.Client(Settings(
    chroma_db_impl="duckdb+parquet",
    persist_directory="/ganuda/data/chromadb"
))

collection = client.create_collection(
    name="va_regulations",
    metadata={"hnsw:space": "cosine"}
)
```

### Step 3: Chunk and Embed 38 CFR
Create `/ganuda/services/rag/ingest_regulations.py`:
- Parse XML structure
- Chunk by section/subsection (preserve context)
- Add metadata: title, part, section, subsection
- Embed using text-embedding model
- Store in ChromaDB

Chunk example:
```python
{
    "id": "38cfr_4.130_9411",
    "text": "9411 Post-traumatic stress disorder...",
    "metadata": {
        "title": "38",
        "part": "4",
        "section": "4.130",
        "diagnostic_code": "9411",
        "body_system": "mental_disorders"
    }
}
```

### Step 4: Build Knowledge Graph (Neo4j)
```bash
# On bluefin
docker run -d --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -v /ganuda/data/neo4j:/data \
  -e NEO4J_AUTH=neo4j/vetassist2026 \
  neo4j:latest
```

Create relationships:
- Diagnostic Code -> Body System
- Diagnostic Code -> Rating Percentages
- Diagnostic Code -> Required Evidence
- Diagnostic Code -> Related Conditions

### Step 5: Create RAG Endpoint
Add to VetAssist backend `/api/v1/research/regulations`:

```python
@router.post("/regulations")
async def query_regulations(query: str, session_id: int):
    # 1. Embed query
    # 2. Search ChromaDB for relevant chunks
    # 3. Enrich with Neo4j relationships
    # 4. Generate response with citations
    # 5. Return structured result
```

### Step 6: Response Format
```json
{
    "query": "What evidence is needed for sleep apnea claim?",
    "answer": "Under 38 CFR § 4.97, Diagnostic Code 6847...",
    "citations": [
        {
            "source": "38 CFR § 4.97",
            "diagnostic_code": "6847",
            "text": "Sleep apnea syndromes..."
        }
    ],
    "rating_criteria": {
        "100": "Chronic respiratory failure...",
        "50": "Requires CPAP...",
        "30": "Persistent hypersomnolence...",
        "0": "Asymptomatic..."
    },
    "evidence_required": [
        "Sleep study (polysomnography)",
        "CPAP prescription",
        "Service treatment records",
        "Nexus statement"
    ]
}
```

## Verification
1. Query: "What is the rating for PTSD?"
   - Should return DC 9411 with 0%, 10%, 30%, 50%, 70%, 100% criteria
2. Query: "What evidence for sleep apnea?"
   - Should return DC 6847 requirements
3. Query: "TBI rating criteria"
   - Should return DC 8045 with residual criteria

Test with all conditions from test users:
- Marcus: PTSD, TBI, Knee DJD, Hearing Loss
- Sarah: Back pain, Tinnitus
- David: Sleep Apnea, Eczema
- James: Knee, Back, Depression

## Security Notes
- 38 CFR is public data, no PII concerns
- Query logs stored in non-PII database
- Rate limiting on endpoint

## Deliverables
- [ ] 38 CFR downloaded and parsed
- [ ] ChromaDB deployed with embeddings
- [ ] Neo4j knowledge graph populated
- [ ] RAG endpoint functional
- [ ] Test queries return accurate citations
- [ ] UI integration for regulation lookup
