# JR Instruction: RAG Embedding Service Setup

**JR ID:** JR-RAG-002
**Priority:** P2
**Created:** 2026-01-27
**Author:** TPM via Claude Code
**Council Vote:** 31653da1507b46ec
**Assigned To:** Infrastructure Jr.
**Depends On:** JR-RAG-001
**Effort:** Low

## Problem Statement

VetAssist RAG needs an embedding model to convert text chunks into vectors for similarity search. We'll use sentence-transformers with MiniLM-L6-v2 (384 dimensions, ~90MB model, fast inference).

## Required Implementation

### 1. Install Dependencies

```bash
cd /ganuda/vetassist/backend
source venv/bin/activate

# Install sentence-transformers (includes torch)
pip install sentence-transformers

# Verify installation
python3 -c "from sentence_transformers import SentenceTransformer; print('OK')"
```

### 2. Embedding Service

CREATE: `/ganuda/vetassist/backend/app/services/embedding_service.py`

```python
"""
Embedding Service for VetAssist RAG.
Council Approved: 2026-01-27 (Vote 31653da1507b46ec)

Uses sentence-transformers MiniLM-L6-v2 for efficient text embeddings.
"""

import logging
from typing import List, Union
import numpy as np

logger = logging.getLogger(__name__)

# Lazy load model to avoid slow startup
_model = None
MODEL_NAME = 'all-MiniLM-L6-v2'
EMBEDDING_DIM = 384


def get_model():
    """Get or initialize the embedding model (lazy loading)."""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        logger.info(f"[Embedding] Loading model: {MODEL_NAME}")
        _model = SentenceTransformer(MODEL_NAME)
        logger.info(f"[Embedding] Model loaded: {EMBEDDING_DIM} dimensions")
    return _model


def embed_text(text: str) -> List[float]:
    """
    Generate embedding for a single text string.

    Args:
        text: Input text to embed

    Returns:
        List of floats (384 dimensions)
    """
    model = get_model()
    embedding = model.encode(text, convert_to_numpy=True)
    return embedding.tolist()


def embed_texts(texts: List[str], batch_size: int = 32) -> List[List[float]]:
    """
    Generate embeddings for multiple texts (batched for efficiency).

    Args:
        texts: List of input texts
        batch_size: Batch size for encoding

    Returns:
        List of embeddings (each 384 dimensions)
    """
    model = get_model()
    embeddings = model.encode(texts, batch_size=batch_size, convert_to_numpy=True)
    return embeddings.tolist()


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    a = np.array(vec1)
    b = np.array(vec2)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


class EmbeddingService:
    """
    Service class for embedding operations with database integration.
    """

    def __init__(self):
        self.model = None

    def _ensure_model(self):
        if self.model is None:
            self.model = get_model()

    def embed(self, text: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        """Embed text or list of texts."""
        self._ensure_model()
        if isinstance(text, str):
            return embed_text(text)
        return embed_texts(text)

    def embed_and_store(self, chunk_id: int, content: str) -> bool:
        """
        Embed content and store in database.

        Args:
            chunk_id: ID of the RAG chunk
            content: Text content to embed

        Returns:
            True if successful
        """
        from app.core.database_config import get_db_connection

        embedding = embed_text(content)

        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE vetassist_rag_chunks
                    SET embedding = %s,
                        processed_at = NOW(),
                        processed_by = %s
                    WHERE id = %s
                """, (embedding, MODEL_NAME, chunk_id))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"[Embedding] Failed to store embedding for chunk {chunk_id}: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def search(self, query: str, top_k: int = 5, source_type: str = None) -> List[dict]:
        """
        Search for similar chunks using vector similarity.

        Args:
            query: Search query text
            top_k: Number of results to return
            source_type: Optional filter by source type

        Returns:
            List of matching chunks with scores
        """
        from app.core.database_config import get_db_connection

        query_embedding = embed_text(query)

        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                if source_type:
                    cur.execute("""
                        SELECT id, source_type, source_id, cfr_section, content,
                               1 - (embedding <=> %s::vector) as similarity
                        FROM vetassist_rag_chunks
                        WHERE embedding IS NOT NULL
                          AND source_type = %s
                        ORDER BY embedding <=> %s::vector
                        LIMIT %s
                    """, (query_embedding, source_type, query_embedding, top_k))
                else:
                    cur.execute("""
                        SELECT id, source_type, source_id, cfr_section, content,
                               1 - (embedding <=> %s::vector) as similarity
                        FROM vetassist_rag_chunks
                        WHERE embedding IS NOT NULL
                        ORDER BY embedding <=> %s::vector
                        LIMIT %s
                    """, (query_embedding, query_embedding, top_k))

                columns = [desc[0] for desc in cur.description]
                return [dict(zip(columns, row)) for row in cur.fetchall()]
        finally:
            conn.close()


# Singleton instance
_embedding_service = None

def get_embedding_service() -> EmbeddingService:
    """Get or create the embedding service singleton."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
```

## Verification

```bash
cd /ganuda/vetassist/backend

# 1. Test embedding generation
python3 -c "
import sys
sys.path.insert(0, '.')
from app.services.embedding_service import embed_text, embed_texts

# Single text
emb = embed_text('PTSD disability rating criteria')
print(f'✓ Single embedding: {len(emb)} dimensions')

# Batch
texts = ['hearing loss', 'tinnitus', 'back pain']
embs = embed_texts(texts)
print(f'✓ Batch embeddings: {len(embs)} texts, {len(embs[0])} dims each')
"

# 2. Test similarity
python3 -c "
import sys
sys.path.insert(0, '.')
from app.services.embedding_service import embed_text, cosine_similarity

e1 = embed_text('PTSD post traumatic stress disorder')
e2 = embed_text('anxiety mental health condition')
e3 = embed_text('broken leg fracture')

sim_related = cosine_similarity(e1, e2)
sim_unrelated = cosine_similarity(e1, e3)

print(f'✓ PTSD vs anxiety: {sim_related:.3f} (should be higher)')
print(f'✓ PTSD vs broken leg: {sim_unrelated:.3f} (should be lower)')
"
```

---

FOR SEVEN GENERATIONS
