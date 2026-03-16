# Jr Instruction: Arxiv Crawler — Expand to 24 Search Categories

**Epic**: ARXIV-EXPAND-EPIC (Cognitive Gaps Mar 15 2026)
**Council Vote**: Approved as Priority #2 in cognitive gap analysis
**Estimated SP**: 3
**Target File**: `/ganuda/services/research_monitor/arxiv_crawler.py`

---

## Objective

The arxiv crawler currently tracks 12 search terms but misses 12 research areas directly relevant to the federation's architecture, products, and design constraints. Expand coverage and fix the assessment pipeline.

## Current State

- 922 papers captured (Dec 2025 — Mar 2026)
- 12 search terms, 3 papers per query per run
- 227 papers (25%) have relevance_score = 0 (assessment failures)
- No arxiv category filtering (searches `all:` which adds noise)

## New Search Terms (12 additions)

Each maps to a Design Constraint or active project:

| # | Search Term | Maps To | Arxiv Category |
|---|------------|---------|----------------|
| 1 | federated learning inference | Federation architecture | cs.DC, cs.LG |
| 2 | energy efficient AI inference | DC-9 Waste Heat | cs.AR, cs.PF |
| 3 | episodic memory neural network | DC-14 Three-Body Memory | cs.AI, cs.NE |
| 4 | AI governance alignment safety | Council/Longhouse | cs.AI, cs.CY |
| 5 | retrieval augmented generation | Thermal memory search | cs.CL, cs.IR |
| 6 | edge distributed inference heterogeneous | Multi-node fleet | cs.DC, cs.AR |
| 7 | self-organizing autonomous systems | DC-7 Noyawisgi | cs.MA, cs.AI |
| 8 | clinical NLP veteran health | VetAssist | cs.CL |
| 9 | indigenous data sovereignty | Tribal Sovereign Cloud | cs.CY |
| 10 | tool use function calling LLM | ToolSet rings | cs.CL, cs.AI |
| 11 | model quantization efficient LLM | MLX/BitNet fleet | cs.LG, cs.AR |
| 12 | combinatorial auction matching | OneChronos/DC-10 | cs.GT, cs.AI |

## Design — Council Concerns as Features

### Crawdad (Security)
- Search terms MUST NOT contain internal node names, IP addresses, or architecture-specific jargon.
- All 24 terms reviewed: none expose internal details. ✓

### Eagle Eye (Signal-to-Noise)
- Add `noise_ratio` tracking per search term: `(papers_scored_below_20) / (total_papers_for_term)`.
- If a term's noise ratio exceeds 80% over 30 days, flag it in dawn mist for review.
- Store noise_ratio in a new column or metadata field on the search term config.

### Raven (Assessment Pipeline Fix)
- **CRITICAL**: 227 papers have relevance_score = 0. Investigate why assessment fails.
- Likely cause: Raven assessment prompt exceeds context window or vLLM timeout on batch assessment.
- Fix: Add retry logic for failed assessments. Run `assess_pending` mode on backlog.
- Add a dawn mist alert if unassessed papers exceed 50.

### Coyote (Justification Gate)
- Every search term must map to a DC or active project (see table above). ✓
- If a term produces 0 relevant papers (score ≥70) after 30 days, auto-disable it and log why.
- No vanity terms — every category must earn its slot.

### Turtle (Noise Reduction)
- Add arxiv category filters to each search term (see Category column above).
- This reduces results from `all:` (everything) to domain-specific papers.
- Expected noise reduction: 40-60%.

## Implementation

### Step 1: Add new search terms

In the crawler's search term configuration (likely a list or dict in `arxiv_crawler.py`), add the 12 new terms with their category filters.

### Step 2: Add category filtering

Modify the arxiv API query to include category constraints. The arxiv API supports `cat:cs.AI` syntax:
```
search_query=all:{term}+AND+(cat:cs.AI+OR+cat:cs.CL)
```

### Step 3: Add noise ratio tracking

After each crawl run, compute noise_ratio per term and store it. Add to the paper metadata or a separate tracking table.

### Step 4: Fix assessment backlog

- Identify why 227 papers have score 0
- Add retry logic with smaller batch sizes
- Run assessment on the existing backlog
- Add dawn mist alert: `if unassessed_count > 50: alert("Raven assessment backlog growing")`

### Step 5: Auto-disable low-value terms

Add a monthly check (can run in the existing crawler timer):
```python
if term_relevant_count == 0 and term_age_days > 30:
    disable_term(term, reason="zero_relevant_papers_30d")
    logger.info(f"[ARXIV] Auto-disabled term '{term}': no relevant papers in 30 days")
```

## Acceptance Criteria

1. Crawler searches 24 terms (12 existing + 12 new)
2. Each term has arxiv category filter
3. Noise ratio tracked per term
4. Assessment backlog (227 papers) cleared or retry mechanism in place
5. Dawn mist alert for unassessed papers >50
6. Auto-disable for zero-relevance terms after 30 days
7. No internal architecture details in any search term

## What NOT To Do

- Do NOT increase crawl rate beyond 36 papers/day (arxiv rate limits)
- Do NOT delete existing search terms — only add new ones
- Do NOT change the assessment criteria — just fix the pipeline that runs them
- Do NOT store full paper PDFs — abstracts and metadata only (DC-9)
