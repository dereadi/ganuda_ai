# Jr Instruction: VetAssist RAG System for VA Regulations

## Priority: HIGH
## Estimated Effort: Large
## Category: ML/Backend

---

## Objective

Build a Retrieval-Augmented Generation (RAG) system for VA regulations to provide accurate, citation-backed guidance on disability claims. Target: 100% citation accuracy (no hallucinated legal references).

---

## Research Basis

- LexRAG: First benchmark for multi-turn legal consultation RAG
- LegalBench-RAG: Evaluates retrieval accuracy in legal domain
- VA 27% error rate on evidence extraction - we must do better
- Hallucination mitigation critical for legal/regulatory advice

Reference: `/ganuda/docs/ultrathink/ULTRATHINK-VETASSIST-AI-ENHANCEMENTS-JAN2026.md`

---

## Target Documents

| Document | Source | Priority |
|----------|--------|----------|
| 38 CFR Part 4 | eCFR.gov | CRITICAL |
| M21-1 Manual | VA.gov | HIGH |
| BVA Decisions | VA.gov/vbaw | HIGH |
| Rating Schedule | 38 CFR | CRITICAL |
| Fast Letters | VA internal | MEDIUM |

---

## Implementation

### Step 1: Install pgvector on Bluefin

**Run on bluefin (192.168.132.222):**

```bash
# Install pgvector extension
sudo apt-get install postgresql-16-pgvector

# Enable in database
PGPASSWORD=jawaseatlasers2 psql -h localhost -U claude -d triad_federation -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

### Step 2: Create Vector Store Schema

**File:** `/ganuda/vetassist/backend/app/db/migrations/004_rag_vector_store.sql`

```sql
-- RAG Vector Store for VA Regulations
-- Cherokee AI Federation

-- Enable pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- Document chunks with embeddings
CREATE TABLE IF NOT EXISTS vetassist_rag_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Source identification
    source_type VARCHAR(50) NOT NULL,  -- cfr, m21, bva, etc.
    source_id VARCHAR(100) NOT NULL,   -- e.g., "38cfr4.71a"
    source_title TEXT,
    source_url TEXT,

    -- Content
    chunk_text TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,      -- Order within document

    -- Embedding (1536 for OpenAI, 384 for MiniLM)
    embedding vector(384),

    -- Metadata
    section_number VARCHAR(50),
    effective_date DATE,
    keywords TEXT[],

    -- Tracking
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(source_type, source_id, chunk_index)
);

-- Index for vector similarity search
CREATE INDEX IF NOT EXISTS idx_rag_embedding
ON vetassist_rag_chunks
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Index for filtering
CREATE INDEX IF NOT EXISTS idx_rag_source ON vetassist_rag_chunks(source_type);
CREATE INDEX IF NOT EXISTS idx_rag_keywords ON vetassist_rag_chunks USING gin(keywords);

-- Knowledge graph for condition relationships
CREATE TABLE IF NOT EXISTS vetassist_condition_graph (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Condition info
    diagnostic_code VARCHAR(10) NOT NULL,
    condition_name TEXT NOT NULL,

    -- Related regulations
    cfr_sections TEXT[],
    rating_criteria JSONB,

    -- Relationships
    related_conditions TEXT[],  -- Other DCs often claimed together
    secondary_to TEXT[],        -- Conditions this is secondary to

    -- Metadata
    body_system VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(diagnostic_code)
);

-- Citation tracking for hallucination prevention
CREATE TABLE IF NOT EXISTS vetassist_rag_citations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query_id UUID NOT NULL,
    chunk_id UUID REFERENCES vetassist_rag_chunks(id),
    citation_text TEXT NOT NULL,
    relevance_score FLOAT,
    verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Step 3: Document Ingestion Pipeline

**File:** `/ganuda/vetassist/backend/app/services/rag_ingestion.py`

```python
"""
RAG Document Ingestion Pipeline
Parses and embeds VA regulatory documents.
"""
import os
import re
import hashlib
from typing import List, Dict, Optional
from dataclasses import dataclass
import httpx
from sentence_transformers import SentenceTransformer
import psycopg2
from psycopg2.extras import execute_values

# Embedding model (384 dimensions, fast)
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
CHUNK_SIZE = 500  # tokens
CHUNK_OVERLAP = 50

@dataclass
class DocumentChunk:
    source_type: str
    source_id: str
    source_title: str
    source_url: str
    chunk_text: str
    chunk_index: int
    section_number: Optional[str] = None
    keywords: List[str] = None


class RAGIngestionService:
    """Ingests and embeds regulatory documents."""

    def __init__(self):
        self.model = SentenceTransformer(EMBEDDING_MODEL)
        self.db_config = {
            'host': '192.168.132.222',
            'database': 'triad_federation',
            'user': 'claude',
            'password': 'jawaseatlasers2'
        }

    def chunk_document(self, text: str, source_type: str, source_id: str,
                      source_title: str, source_url: str) -> List[DocumentChunk]:
        """Split document into overlapping chunks."""
        # Simple sentence-based chunking
        sentences = re.split(r'(?<=[.!?])\s+', text)
        chunks = []
        current_chunk = []
        current_length = 0

        for sentence in sentences:
            sentence_length = len(sentence.split())
            if current_length + sentence_length > CHUNK_SIZE and current_chunk:
                chunk_text = ' '.join(current_chunk)
                chunks.append(DocumentChunk(
                    source_type=source_type,
                    source_id=source_id,
                    source_title=source_title,
                    source_url=source_url,
                    chunk_text=chunk_text,
                    chunk_index=len(chunks),
                    keywords=self._extract_keywords(chunk_text)
                ))
                # Keep overlap
                overlap_sentences = current_chunk[-2:] if len(current_chunk) > 2 else []
                current_chunk = overlap_sentences
                current_length = sum(len(s.split()) for s in current_chunk)

            current_chunk.append(sentence)
            current_length += sentence_length

        # Final chunk
        if current_chunk:
            chunks.append(DocumentChunk(
                source_type=source_type,
                source_id=source_id,
                source_title=source_title,
                source_url=source_url,
                chunk_text=' '.join(current_chunk),
                chunk_index=len(chunks),
                keywords=self._extract_keywords(' '.join(current_chunk))
            ))

        return chunks

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from chunk text."""
        # Simple keyword extraction - diagnostic codes, ratings
        keywords = []

        # Diagnostic codes (e.g., 9411, 5242)
        dc_matches = re.findall(r'\b(\d{4})\b', text)
        keywords.extend([f"DC{dc}" for dc in dc_matches])

        # Rating percentages
        rating_matches = re.findall(r'(\d{1,3})\s*percent', text.lower())
        keywords.extend([f"{r}%" for r in rating_matches])

        return list(set(keywords))

    def embed_chunks(self, chunks: List[DocumentChunk]) -> List[tuple]:
        """Generate embeddings for chunks."""
        texts = [c.chunk_text for c in chunks]
        embeddings = self.model.encode(texts, show_progress_bar=True)

        return [(c, emb.tolist()) for c, emb in zip(chunks, embeddings)]

    def store_chunks(self, chunks_with_embeddings: List[tuple]):
        """Store chunks and embeddings in database."""
        conn = psycopg2.connect(**self.db_config)
        cur = conn.cursor()

        data = [
            (
                c.source_type, c.source_id, c.source_title, c.source_url,
                c.chunk_text, c.chunk_index, emb, c.section_number, c.keywords
            )
            for c, emb in chunks_with_embeddings
        ]

        execute_values(cur, """
            INSERT INTO vetassist_rag_chunks
            (source_type, source_id, source_title, source_url,
             chunk_text, chunk_index, embedding, section_number, keywords)
            VALUES %s
            ON CONFLICT (source_type, source_id, chunk_index) DO UPDATE SET
                chunk_text = EXCLUDED.chunk_text,
                embedding = EXCLUDED.embedding,
                updated_at = NOW()
        """, data, template="""
            (%(source_type)s, %(source_id)s, %(source_title)s, %(source_url)s,
             %(chunk_text)s, %(chunk_index)s, %(embedding)s::vector,
             %(section_number)s, %(keywords)s)
        """)

        conn.commit()
        cur.close()
        conn.close()

    async def ingest_cfr_section(self, cfr_section: str):
        """
        Ingest a section of 38 CFR.

        Example: ingest_cfr_section("38/4")  # Part 4 - Rating Schedule
        """
        url = f"https://www.ecfr.gov/api/versioner/v1/full/{cfr_section}.xml"
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            # TODO: Parse XML and extract sections
            pass


# CLI for ingestion
if __name__ == "__main__":
    import sys
    service = RAGIngestionService()

    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        with open(file_path, 'r') as f:
            text = f.read()
        chunks = service.chunk_document(
            text,
            source_type="cfr",
            source_id="38cfr4",
            source_title="38 CFR Part 4 - Rating Schedule",
            source_url="https://www.ecfr.gov/current/title-38/part-4"
        )
        embedded = service.embed_chunks(chunks)
        service.store_chunks(embedded)
        print(f"Ingested {len(chunks)} chunks")
```

### Step 4: RAG Query Service

**File:** `/ganuda/vetassist/backend/app/services/rag_query.py`

```python
"""
RAG Query Service
Retrieves relevant regulatory context for user queries.
"""
from typing import List, Dict, Optional
from dataclasses import dataclass
from sentence_transformers import SentenceTransformer
import psycopg2
from psycopg2.extras import RealDictCursor

EMBEDDING_MODEL = "all-MiniLM-L6-v2"
TOP_K = 5  # Number of chunks to retrieve


@dataclass
class RetrievedChunk:
    chunk_id: str
    source_type: str
    source_id: str
    source_title: str
    source_url: str
    chunk_text: str
    similarity_score: float


class RAGQueryService:
    """Retrieves relevant regulatory context for queries."""

    def __init__(self):
        self.model = SentenceTransformer(EMBEDDING_MODEL)
        self.db_config = {
            'host': '192.168.132.222',
            'database': 'triad_federation',
            'user': 'claude',
            'password': 'jawaseatlasers2'
        }

    def retrieve(self, query: str, source_types: List[str] = None,
                top_k: int = TOP_K) -> List[RetrievedChunk]:
        """
        Retrieve relevant chunks for a query.

        Args:
            query: User's question
            source_types: Filter by source (cfr, m21, bva)
            top_k: Number of results to return
        """
        # Generate query embedding
        query_embedding = self.model.encode(query).tolist()

        conn = psycopg2.connect(**self.db_config)
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # Build query with optional source filter
        sql = """
            SELECT id, source_type, source_id, source_title, source_url,
                   chunk_text, 1 - (embedding <=> %s::vector) as similarity
            FROM vetassist_rag_chunks
        """
        params = [query_embedding]

        if source_types:
            sql += " WHERE source_type = ANY(%s)"
            params.append(source_types)

        sql += " ORDER BY embedding <=> %s::vector LIMIT %s"
        params.extend([query_embedding, top_k])

        cur.execute(sql, params)
        rows = cur.fetchall()
        cur.close()
        conn.close()

        return [
            RetrievedChunk(
                chunk_id=str(row['id']),
                source_type=row['source_type'],
                source_id=row['source_id'],
                source_title=row['source_title'],
                source_url=row['source_url'],
                chunk_text=row['chunk_text'],
                similarity_score=row['similarity']
            )
            for row in rows
        ]

    def build_context(self, chunks: List[RetrievedChunk]) -> str:
        """Build context string from retrieved chunks."""
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            context_parts.append(
                f"[Source {i}: {chunk.source_title}]\n"
                f"{chunk.chunk_text}\n"
                f"[Citation: {chunk.source_url}]\n"
            )
        return "\n---\n".join(context_parts)

    def query_with_context(self, user_query: str) -> Dict:
        """
        Full RAG query: retrieve context and format for LLM.
        """
        chunks = self.retrieve(user_query)
        context = self.build_context(chunks)

        return {
            "query": user_query,
            "context": context,
            "chunks": chunks,
            "citations": [
                {"title": c.source_title, "url": c.source_url}
                for c in chunks
            ]
        }


# Convenience function
def rag_query(query: str, source_types: List[str] = None) -> Dict:
    """Query RAG system for regulatory context."""
    service = RAGQueryService()
    return service.query_with_context(query)
```

### Step 5: API Endpoint

**File:** `/ganuda/vetassist/backend/app/api/v1/endpoints/rag.py`

```python
"""
RAG API Endpoints
"""
from fastapi import APIRouter, Query
from typing import List, Optional
from pydantic import BaseModel

from app.services.rag_query import RAGQueryService

router = APIRouter()


class RAGQueryRequest(BaseModel):
    query: str
    source_types: Optional[List[str]] = None
    top_k: int = 5


class RAGQueryResponse(BaseModel):
    query: str
    context: str
    citations: List[dict]


@router.post("/query", response_model=RAGQueryResponse)
async def query_regulations(request: RAGQueryRequest):
    """
    Query VA regulations using RAG.

    Returns relevant regulatory context with citations.
    """
    service = RAGQueryService()
    chunks = service.retrieve(
        request.query,
        source_types=request.source_types,
        top_k=request.top_k
    )
    context = service.build_context(chunks)

    return RAGQueryResponse(
        query=request.query,
        context=context,
        citations=[
            {"title": c.source_title, "url": c.source_url, "score": c.similarity_score}
            for c in chunks
        ]
    )


@router.get("/sources")
async def list_sources():
    """List available regulatory sources."""
    return {
        "sources": [
            {"type": "cfr", "name": "38 CFR - VA Regulations"},
            {"type": "m21", "name": "M21-1 Adjudication Manual"},
            {"type": "bva", "name": "BVA Case Decisions"},
        ]
    }
```

---

## Dependencies

```bash
pip install sentence-transformers psycopg2-binary
```

---

## Verification

1. Install pgvector on bluefin
2. Run migration to create tables
3. Ingest test document:
```bash
python -m app.services.rag_ingestion /path/to/38cfr_part4.txt
```
4. Test query:
```python
from app.services.rag_query import rag_query
result = rag_query("What is the rating criteria for PTSD?")
print(result['context'])
print(result['citations'])
```

---

## Success Criteria

- [ ] pgvector installed and working
- [ ] Vector store tables created
- [ ] 38 CFR Part 4 ingested
- [ ] Query retrieval working
- [ ] Citations included in all responses
- [ ] API endpoint functional

---

*Cherokee AI Federation - For Seven Generations*
