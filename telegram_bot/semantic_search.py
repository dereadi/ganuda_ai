"""
Semantic Search - Query thermal memory by meaning
Uses pgvector IVFFlat index for fast cosine similarity
"""

import psycopg2
from sentence_transformers import SentenceTransformer

class SemanticSearch:
    """Search thermal memory using embeddings"""

    def __init__(self, db_config: dict):
        self.db_config = db_config
        self.model = SentenceTransformer('all-MiniLM-L6-v2')  # 384 dims

    def search(self, query: str, limit: int = 3) -> list:
        """Find most relevant memories for query

        Args:
            query: User's question
            limit: Max memories to return

        Returns:
            List of (content, similarity_score) tuples
        """
        # Generate embedding for query
        embedding = self.model.encode(query).tolist()

        conn = psycopg2.connect(**self.db_config)
        cur = conn.cursor()

        # Cosine similarity search via pgvector
        cur.execute("""
            SELECT content,
                   1 - (embedding <=> %s::vector) as similarity
            FROM triad_shared_memories
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> %s::vector
            LIMIT %s
        """, (embedding, embedding, limit))

        results = cur.fetchall()
        cur.close()
        conn.close()

        return results

    def format_context(self, memories: list) -> str:
        """Format memories as context string for LLM"""
        if not memories:
            return ""

        context_parts = ["Relevant context from Cherokee memory:"]
        for content, score in memories:
            if score > 0.3:  # Only include if reasonably relevant
                # Truncate long memories
                snippet = content[:300] + "..." if len(content) > 300 else content
                context_parts.append(f"- {snippet}")

        return "\n".join(context_parts) if len(context_parts) > 1 else ""