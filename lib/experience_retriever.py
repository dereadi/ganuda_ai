"""
Experience Retriever — queries thermal memory for relevant strategic knowledge.

Uses greenfin's embedding service (:8003) for vector similarity search.
Returns top-k experiences above cosine threshold for injection into Jr task prompts.

Council vote #fb526dd2212e09a7 — APPROVED WITH CONDITIONS:
  - Coyote: cosine >0.7, max 5 experiences, embedding similarity only
  - Crawdad: sacred_pattern=true NEVER injected, Phase 1 read-only
  - Spider: 500ms hard timeout, graceful degradation
  - Turtle: kill switch via config/env
  - Gecko: +9% CPU, +150MB RAM, +100ms latency — within budget

For Seven Generations
"""

import httpx
import logging
from typing import List, Dict

logger = logging.getLogger('experience_retriever')

# Greenfin embedding service (BGE-large-en-v1.5, 1024 dims)
EMBEDDING_SERVICE = "http://192.168.132.224:8003"
SIMILARITY_THRESHOLD = 0.7    # Coyote gate: reject weak matches
MAX_EXPERIENCES = 5           # Coyote gate: max entries per task
RETRIEVAL_TIMEOUT_S = 0.5    # Spider gate: 500ms hard timeout


class ExperienceRetriever:
    """Retrieve relevant experiences from thermal memory for Jr task augmentation."""

    def __init__(self, enabled: bool = True):
        self.enabled = enabled  # Turtle kill switch
        self._client = httpx.Client(timeout=RETRIEVAL_TIMEOUT_S)

    def retrieve(self, task_description: str) -> List[Dict]:
        """
        Retrieve relevant experiences for a task.

        Uses greenfin's /v1/search endpoint which handles:
        1. Embedding the query text
        2. pgvector cosine similarity against thermal_memory_archive
        3. Filtering by threshold
        4. Returning top-k matches

        Returns list of dicts with keys: content, temperature, similarity, id
        Returns empty list if disabled, timed out, or no matches above threshold.
        """
        if not self.enabled:
            return []

        try:
            # Single call — search endpoint embeds + searches in one round trip
            response = self._client.post(
                f"{EMBEDDING_SERVICE}/v1/search",
                json={
                    "query": task_description[:2000],  # Truncate long descriptions
                    "table": "thermal_memory_archive",
                    "column": "original_content",
                    "embedding_column": "embedding",
                    "limit": MAX_EXPERIENCES * 2,  # Over-fetch, then filter
                    "threshold": SIMILARITY_THRESHOLD,
                }
            )
            response.raise_for_status()
            raw = response.json()
            # API returns a plain list of dicts, not {"results": [...]}
            results = raw if isinstance(raw, list) else raw.get("results", [])

            # Filter: never inject sacred memories (Crawdad)
            experiences = []
            for r in results:
                if not isinstance(r, dict):
                    continue
                if r.get("sacred_pattern", False):
                    continue
                if len(experiences) >= MAX_EXPERIENCES:
                    break
                experiences.append({
                    "content": r.get("content", "")[:500],
                    "temperature": r.get("temperature_score", 50),
                    "similarity": r.get("similarity", 0),
                    "id": r.get("id", "unknown"),
                    "tags": [],
                })

            if experiences:
                logger.info(
                    f"Retrieved {len(experiences)} experiences for task "
                    f"(top similarity: {experiences[0]['similarity']:.3f})"
                )
            return experiences

        except httpx.TimeoutException:
            logger.warning("Experience retrieval timed out (500ms) — skipping")
            return []
        except Exception as e:
            logger.warning(f"Experience retrieval failed: {e} — skipping gracefully")
            return []

    def format_for_prompt(self, experiences: List[Dict]) -> str:
        """Format retrieved experiences as non-prescriptive prompt guidance."""
        if not experiences:
            return ""

        lines = ["\n## Prior Experiences (non-prescriptive — adapt or override as needed)\n"]
        for i, exp in enumerate(experiences, 1):
            sim_pct = f"{exp['similarity']:.0%}" if isinstance(exp['similarity'], float) else str(exp['similarity'])
            lines.append(
                f"**Experience {i}** (relevance: {sim_pct}, temp: {exp['temperature']}):"
            )
            lines.append(f"  {exp['content']}")
            if exp.get('tags'):
                tags = exp['tags'] if isinstance(exp['tags'], list) else []
                if tags:
                    lines.append(f"  Tags: {', '.join(str(t) for t in tags)}")
            lines.append("")

        return "\n".join(lines)

    def close(self):
        self._client.close()
