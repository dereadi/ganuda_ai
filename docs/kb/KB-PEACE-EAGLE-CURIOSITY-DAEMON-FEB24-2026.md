# KB: Peace Eagle — Council Curiosity Daemon

**Created:** Feb 24, 2026
**Kanban:** #1890
**Jr Task:** #906 (completed, 5/24 steps succeeded, 19 failed)
**Script:** `/ganuda/scripts/council_curiosity.py`
**Thermal:** #114244 (research crawl: 22 papers, 17 high-relevance)

---

## What It Does

Peace Eagle is the federation's forward-looking eye. It gives the Council autonomy to identify knowledge gaps and discover research that could help the cluster grow.

**Pipeline:**
1. **Gather** — queries federation state: failed Jr tasks, low-confidence council votes, open kanban items, known research backlog
2. **Ask** — sends context to Council via gateway, asks "what should we research RIGHT NOW?"
3. **Search** — executes Council-directed searches on arxiv (papers) and GitHub (repos)
4. **Summarize** — each finding summarized by gateway for federation relevance
5. **Store** — findings stored in thermal_memory_archive with tags, temperature 50, memory_type="research"

## Design Decisions

- **Council-directed, not random**: The Council sees federation failures and gaps, then decides what to research. Not a blind crawler.
- **Source-aware**: Council specifies "arxiv:" or "github:" prefix to direct search type.
- **Specialist-tagged**: Each finding tagged with which specialist cares most (Chief, Raven, Deer, etc.).
- **Idempotent**: ON CONFLICT DO NOTHING on memory_hash prevents duplicate findings.
- **Rate-limited**: 3-second sleep between arxiv requests (kind to their API).
- **Dry-run mode**: `--dry-run` queries Council but skips research execution.

## Current Status

First run had issues — 19/24 steps failed during Jr execution. Likely causes:
- Gateway timeout during council query (temp_score 95 alerts seen in thermal memory around same time)
- arxiv API namespace parsing in XML (atom namespace prefix)
- GitHub API rate limiting without auth token

**Needs:** Debug and re-run. Owl (#907) will catch this automatically.

## Architecture

```
Federation State (DB) → Council Query → Research Execution → Summarization → Thermal Memory
                         ↑                                      ↑
                    cherokee-council                      Qwen2.5-72B
                    via gateway:8080                      via gateway:8080
```

## Naming

Peace Eagle — the Cherokee peace chief's bird. Watches the horizon for what's coming. Complements Owl, who watches the trail behind.

## Related

- **Owl (Debt Reckoning):** KB-OWL-DEBT-RECKONING-FEB24-2026.md
- **Anti-80/20 Principle:** Sprint hard but stop to verify. Peace Eagle looks forward, Owl looks backward. Both required.
- **RL2F Phase 0:** Self-Refine loop uses similar gateway + thermal pattern.
