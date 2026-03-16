# Jr Instruction: SkillRL Experience Bank — Wire Thermal Memory as Strategic Knowledge

**Epic**: SKILLRL-EPIC (augmentation, not new epic)
**Council Vote**: #fb526dd2212e09a7 (0.757, APPROVED WITH CONDITIONS — Coyote dissent on noise, Crawdad RBAC deferred)
**Estimated SP**: 3
**Depends On**: SkillRL base Jr instructions (JR-SKILLRL-01 through JR-SKILLRL-09)
**Academic Basis**: XSKILL (HKUST, Mar 12 2026) + "Automating Skill Acquisition from GitHub Repos" (ECNU, Mar 12 2026). Thermalized as #128241, #128242.

---

## Objective

Add an **experience retrieval layer** to the Jr executor's task planning. The XSKILL paper proved that skills alone don't improve agent performance (66→66 on visual toolbench), but experiences push it to 74. Our thermal memory (19,800+ entries) IS the experience bank — we just need to wire retrieval into the execution path.

**Skills** = how to do a workflow (SkillRL skill library — already being built)
**Experiences** = when X failed, try Y instead (thermal memory — already exists, needs retrieval)

Together they attack different failure modes and are not interchangeable.

## Design — Council Concerns as Features

### Coyote (Noise Dissent — ACCEPTED, ADDRESSED)
- 19,800 thermals without smart retrieval = noise cannon. AGREED.
- Experience retrieval MUST use embedding similarity via greenfin's embedding service (port 8003), NOT raw SQL scan.
- Cosine similarity threshold: **>0.7** — reject weak matches.
- Max **5 experience entries** injected per Jr task. Not the whole bank.
- If no experiences score >0.7, inject NOTHING. Silence is better than noise.

### Crawdad (Security — DEFERRED to Phase 2)
- Phase 1: experience retrieval is READ-ONLY on already-thermalized data. No new write paths.
- Phase 2 (if earned): RBAC on thermal queries, content trust scoring, anomaly detection on retrieval patterns.
- NEVER inject experiences with `is_sacred = true` into Jr task context — sacred memories are painted on walls, not task guidance.

### Spider (Single Point of Failure)
- Experience retrieval queries greenfin's embedding service, NOT bluefin's PostgreSQL directly.
- Greenfin already hosts the embedding service at :8003 — no new infrastructure.
- 500ms hard timeout on retrieval. If greenfin is slow or down, skip experience injection gracefully. Jr task runs without it — degraded but functional.

### Raven (Displacement)
- This is +3 SP ON TOP of existing SkillRL queue, not in front of it.
- SkillRL Jr instructions 01-09 execute first. This augments, not displaces.
- If SkillRL is delayed, this can still be wired independently — thermal memory and Jr executor already exist.

### Turtle (Flexibility)
- Experience injection is NON-PRESCRIPTIVE guidance (per XSKILL design). Jr agent can follow, adapt, or override.
- Injected as a "Prior Experiences" section in the task prompt, not as hard constraints.
- Kill switch: `experience_retrieval.enabled: false` in config.yaml → no thermal queries, no injection.

### Gecko (Resource Budget)
- +9% CPU on Jr tasks (embedding query overhead)
- +150MB RAM per task (experience context in prompt)
- +100ms latency per thermal query (greenfin embedding service)
- All within budget. Gecko cleared.

## Implementation

### Step 1: Experience Retriever Module

Create `/ganuda/lib/experience_retriever.py`:

```python
"""
Experience Retriever — queries thermal memory for relevant strategic knowledge.

Uses greenfin's embedding service (:8003) for vector similarity search.
Returns top-k experiences above cosine threshold for injection into Jr task prompts.
"""

import httpx
import asyncio
import logging
from typing import List, Dict, Optional

logger = logging.getLogger('experience_retriever')

EMBEDDING_SERVICE = "http://192.168.132.224:8003"
SIMILARITY_THRESHOLD = 0.7    # Coyote gate: reject weak matches
MAX_EXPERIENCES = 5           # Coyote gate: max entries per task
RETRIEVAL_TIMEOUT_MS = 500    # Spider gate: hard timeout
DB_HOST = "192.168.132.222"   # bluefin (thermal_memory_archive)


class ExperienceRetriever:
    """Retrieve relevant experiences from thermal memory for Jr task augmentation."""

    def __init__(self, enabled: bool = True):
        self.enabled = enabled  # Turtle kill switch
        self._client = httpx.AsyncClient(timeout=RETRIEVAL_TIMEOUT_MS / 1000.0)

    async def retrieve(self, task_description: str, task_type: str = None) -> List[Dict]:
        """
        Retrieve relevant experiences for a task.

        Returns list of dicts with keys: content, temperature, similarity_score, source
        Returns empty list if disabled, timed out, or no matches above threshold.
        """
        if not self.enabled:
            return []

        try:
            # Step 1: Embed the task description
            embed_response = await self._client.post(
                f"{EMBEDDING_SERVICE}/embed",
                json={"text": task_description}
            )
            embed_response.raise_for_status()
            task_embedding = embed_response.json()["embedding"]

            # Step 2: Vector similarity search against thermal memory embeddings
            # Use the embedding service's search endpoint if available,
            # otherwise fall back to direct DB query with pgvector
            search_response = await self._client.post(
                f"{EMBEDDING_SERVICE}/search",
                json={
                    "embedding": task_embedding,
                    "collection": "thermal_memory_archive",
                    "top_k": MAX_EXPERIENCES * 2,  # Over-fetch, then filter
                    "threshold": SIMILARITY_THRESHOLD,
                    "filters": {
                        "is_sacred": False,  # Crawdad: never inject sacred memories
                    }
                }
            )
            search_response.raise_for_status()
            results = search_response.json().get("results", [])

            # Step 3: Filter and format
            experiences = []
            for r in results[:MAX_EXPERIENCES]:
                experiences.append({
                    "content": r["content"][:500],  # Truncate long memories
                    "temperature": r.get("temperature_score", 50),
                    "similarity": r.get("similarity", 0),
                    "source": r.get("metadata", {}).get("source", "unknown"),
                    "tags": r.get("metadata", {}).get("tags", []),
                })

            if experiences:
                logger.info(f"Retrieved {len(experiences)} experiences for task "
                           f"(top similarity: {experiences[0]['similarity']:.3f})")
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
            lines.append(f"**Experience {i}** (relevance: {exp['similarity']:.0%}, "
                        f"temp: {exp['temperature']}):")
            lines.append(f"  {exp['content']}")
            if exp.get('tags'):
                lines.append(f"  Tags: {', '.join(exp['tags'])}")
            lines.append("")

        return "\n".join(lines)

    async def close(self):
        await self._client.aclose()
```

### Step 2: Wire into Jr Executor

In `/ganuda/jr_executor/jr_task_executor.py`, add experience retrieval before task execution:

```python
# At top with imports:
from lib.experience_retriever import ExperienceRetriever

# In __init__:
self.experience_retriever = ExperienceRetriever(
    enabled=config.get('experience_retrieval', {}).get('enabled', True)
)

# In execute_task(), before building the task prompt:
experiences = await self.experience_retriever.retrieve(
    task_description=task.get('description', ''),
    task_type=task.get('task_type', None)
)
experience_context = self.experience_retriever.format_for_prompt(experiences)

# Inject into prompt (non-prescriptive, after task description):
if experience_context:
    task_prompt = task_prompt + experience_context
    # Log for Langfuse trace
    if self._current_trace:
        self._current_trace.update(metadata={
            "experiences_injected": len(experiences),
            "top_experience_similarity": experiences[0]["similarity"] if experiences else 0,
        })
```

### Step 3: Experience Extraction from Jr Task Results

After a Jr task completes (success OR failure), extract experience insights and thermalize:

```python
# In execute_task(), after completion:
if task_result.get('status') == 'failed':
    experience_content = (
        f"EXPERIENCE: Task type '{task_type}' failed. "
        f"Error: {task_result.get('error', 'unknown')[:200]}. "
        f"Context: {task.get('description', '')[:200]}. "
        f"Attempted approach: {task_result.get('steps_completed', 'unknown')}."
    )
    # Thermalize at temperature 55 (warm but not hot — operational learning)
    await self._thermalize(experience_content, temperature=55, tags=['experience', 'failure_mode', task_type])

elif task_result.get('status') == 'completed' and task_result.get('difficulty', 'normal') == 'hard':
    experience_content = (
        f"EXPERIENCE: Task type '{task_type}' succeeded (was marked hard). "
        f"Approach: {task_result.get('approach_summary', 'unknown')[:200]}. "
        f"Key insight: {task_result.get('key_insight', 'none')[:200]}."
    )
    await self._thermalize(experience_content, temperature=55, tags=['experience', 'success_pattern', task_type])
```

### Step 4: Config Addition

In `/ganuda/lib/harness/config.yaml`:

```yaml
experience_retrieval:
  enabled: true                    # Turtle kill switch
  embedding_service: "http://192.168.132.224:8003"
  similarity_threshold: 0.7       # Coyote gate
  max_experiences: 5              # Coyote gate
  timeout_ms: 500                 # Spider gate
  extract_from_results: true      # Write new experiences after task completion
  sacred_filter: true             # Crawdad: never inject sacred memories
```

## Verification

1. **Retrieval test**: Run experience retriever with a known task description that has thermal matches. Verify cosine similarity scores >0.7 for relevant matches.
2. **Noise test** (Coyote): Run with a completely unrelated task description. Verify ZERO experiences returned (all below threshold).
3. **Timeout test** (Spider): Block greenfin:8003 temporarily. Verify Jr task runs without experiences (degraded but functional).
4. **Injection test**: Execute a Jr task with experience retrieval enabled. Verify Langfuse trace shows `experiences_injected` metadata.
5. **Kill switch test** (Turtle): Set `experience_retrieval.enabled: false`. Verify no thermal queries, no prompt injection.
6. **Sacred filter test** (Crawdad): Verify no experiences with `is_sacred = true` appear in retrieval results.
7. **Extraction test**: Fail a Jr task intentionally. Verify a new thermal memory with tag `experience` and `failure_mode` is created.

## Acceptance Criteria

1. ExperienceRetriever module exists and passes unit tests
2. Jr executor queries thermal memory before task execution via embedding similarity
3. Top 5 experiences injected as non-prescriptive guidance in task prompt
4. Failed and hard-succeeded tasks generate new experience entries
5. Langfuse traces show experience injection metadata
6. Config kill switch works (enabled: false → no queries)
7. 500ms timeout enforced — no Jr task degradation if greenfin is slow
8. Sacred memories never appear in experience retrieval results

## What NOT To Do

- Do NOT scan all 19,800 thermals with raw SQL — use embedding similarity (Coyote)
- Do NOT inject more than 5 experiences per task — context window budget
- Do NOT make experience retrieval a blocking dependency — if it fails, task runs without it
- Do NOT inject sacred memories into Jr task context — they're painted on walls, not task guidance (Crawdad)
- Do NOT create a new database or service — use existing embedding service on greenfin and thermal_memory_archive on bluefin
- Do NOT modify SkillRL Jr instructions 01-09 — this augments, it doesn't replace
- Do NOT add RBAC or content trust model yet — that's Phase 2 if this earns its slot
