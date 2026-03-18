# Jr Instruction: Arxiv Crawler — 12 Missing Research Categories

**Ticket**: ARXIV-EXPAND-EPIC
**Council Vote**: Turtle slate vote, 5-2 (Raven/Coyote dissent on Forgetting deferred, not on this ticket)
**Estimated SP**: 3
**Assigned**: Raven
**Depends On**: None (arxiv_crawler.py already handles 24 search terms)

---

## Objective

The arxiv crawler currently tracks 24 search terms across ~12 arxiv categories. The federation's research surface has expanded — SkillRL, experience banks, breadcrumb memory, tokenized proxies, combinatorial auctions, and sovereign inference are all active work areas. Several domains are not covered by the current SEARCH_QUERIES list. Add 12 new search terms that map to active federation work, with proper category filters to control noise.

## Current State

**File**: `/ganuda/services/research_monitor/arxiv_crawler.py` (lines 34-61)
**24 terms** already configured with category filters.
**Architecture**: search → save → assess (via Raven on gateway) → notify TPM (score ≥70) → thermalize.
**Known issue**: 227 papers with relevance_score=0 (assessment failures). `--assess-pending` mode exists to retry.

Adding new terms requires ONLY editing the SEARCH_QUERIES list. The pipeline (fetch, assess, store, thermalize, noise tracking) handles everything automatically.

## New Search Terms (12)

Add these to SEARCH_QUERIES in `/ganuda/services/research_monitor/arxiv_crawler.py` after line 61:

```python
# ── Wave 3: Federation expansion (Mar 16 2026) ──
{"term": "experience replay reinforcement learning agent", "categories": ["cs.AI", "cs.LG"]},
{"term": "skill library reusable policy", "categories": ["cs.AI", "cs.RO", "cs.LG"]},
{"term": "tokenization privacy preserving inference", "categories": ["cs.CR", "cs.CL"]},
{"term": "multi-armed bandit model selection", "categories": ["cs.LG", "cs.AI"]},
{"term": "graph retrieval augmented generation knowledge", "categories": ["cs.CL", "cs.IR", "cs.AI"]},
{"term": "thermal memory decay forgetting neural", "categories": ["cs.AI", "cs.NE", "cs.LG"]},
{"term": "air gapped secure inference deployment", "categories": ["cs.CR", "cs.DC"]},
{"term": "sovereign AI local inference edge", "categories": ["cs.DC", "cs.CY"]},
{"term": "council governance multi-agent voting", "categories": ["cs.MA", "cs.AI", "cs.GT"]},
{"term": "self-improving agent autonomous learning", "categories": ["cs.AI", "cs.LG"]},
{"term": "speculative decoding parallel generation", "categories": ["cs.CL", "cs.DC"]},
{"term": "persistent memory context window management", "categories": ["cs.CL", "cs.AI"]},
```

### Mapping to Active Work

| Search Term | Federation Connection |
|-------------|----------------------|
| experience replay RL agent | SkillRL + Experience Bank (XSKILL pattern) |
| skill library reusable policy | SkillRL epic — skill extraction and reuse |
| tokenization privacy preserving | Consultation Ring — tokenized air-gap proxy |
| multi-armed bandit model selection | UCB Bandit in consultation ring |
| graph RAG knowledge | GraphRAG epic (backlog) |
| thermal memory decay forgetting | Forgetting epic (next up per Raven/Coyote) |
| air gapped secure inference | Patent brief #7 — DoD/HIPAA/ITAR deployments |
| sovereign AI local inference | North Star — sovereign intelligence |
| council governance multi-agent voting | Council topology, specialist_council.py |
| self-improving agent autonomous | SkillRL + PreFlect self-critique |
| speculative decoding | Inference optimization on redfin/sasass2 |
| persistent memory context | Breadcrumb memory, 50 First Dates problem |

## Implementation

### Step 1: Add Search Terms

In `/ganuda/services/research_monitor/arxiv_crawler.py`, add the 12 new entries to the SEARCH_QUERIES list after the existing Wave 2 entries (after line 61).

### Step 2: Verify Noise Tracking

The existing `compute_noise_ratios()` function (lines 294-336) automatically tracks per-term noise. No code changes needed. After 7 days, check noise ratios for new terms:

```sql
-- Check noise ratios after first week
SELECT search_term,
       COUNT(*) as total,
       COUNT(*) FILTER (WHERE relevance_score < 20) as noise,
       ROUND(COUNT(*) FILTER (WHERE relevance_score < 20)::numeric / COUNT(*)::numeric, 2) as noise_ratio
FROM ai_research_papers,
     jsonb_array_elements_text(search_terms_matched) as search_term
WHERE crawled_at > NOW() - INTERVAL '7 days'
GROUP BY search_term
ORDER BY noise_ratio DESC;
```

### Step 3: Verify Auto-Disable Safety

The existing `check_auto_disable()` function (lines 339-372) flags terms with zero relevant papers after 30 days. This safety net catches bad search terms automatically. No changes needed.

## Verification

1. **Term count**: After edit, `len(SEARCH_QUERIES)` should be 36
2. **Crawl test**: Run `python arxiv_crawler.py` manually. Verify new terms produce results
3. **Assessment test**: Verify Raven scores new papers (check `relevance_score > 0` for new terms)
4. **Noise check**: After 7 days, verify no new term has noise_ratio > 80%
5. **Thermal**: Verify crawl summary thermal includes updated search_terms count (36)

## What NOT To Do

- Do NOT modify the assessment prompt — Raven's scoring criteria are general enough
- Do NOT change the crawl schedule — daily 6 AM is fine for 36 terms (adds ~2 min to crawl)
- Do NOT remove existing search terms — only add
- Do NOT add more than 12 terms — Coyote noise gate. Prove these work first
- Do NOT change rate limiting (3 sec between queries) — arxiv API courtesy
