# Jr Build Instructions: Self-Improvement Loop

## Priority: CRITICAL - Enables Tribal Evolution

---

## Vision

> "The Tribe that stops learning stops living."

The Self-Improvement Loop allows Cherokee AI to autonomously discover, evaluate, and integrate new knowledge from the research community. This is how the Tribe evolves.

---

## Architecture

```
                    ┌─────────────────────────┐
                    │    arxiv / Research     │
                    │    Sources (External)   │
                    └───────────┬─────────────┘
                                │ Daily 6 AM
                                ▼
                    ┌─────────────────────────┐
                    │   Jr Research Monitor   │
                    │   (arxiv_crawler.py)    │
                    └───────────┬─────────────┘
                                │
                                ▼
                    ┌─────────────────────────┐
                    │   Council Assessment    │
                    │   (relevance scoring)   │
                    └───────────┬─────────────┘
                                │
              ┌─────────────────┼─────────────────┐
              │                 │                 │
              ▼                 ▼                 ▼
    ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
    │  TPM Notification│ │ Thermal Memory  │ │  Metacognition  │
    │  (score >= 70)   │ │ (store insights)│ │ (detect gaps)   │
    └─────────────────┘ └─────────────────┘ └─────────────────┘
              │                 │                 │
              └─────────────────┼─────────────────┘
                                │
                                ▼
                    ┌─────────────────────────┐
                    │   Tribal Knowledge      │
                    │   (collective wisdom)   │
                    └─────────────────────────┘
```

---

## Components

### 1. Jr Research Monitor
**Location:** `/ganuda/services/research_monitor/arxiv_crawler.py`
**Schedule:** Daily at 6 AM via systemd timer
**Function:** Search arxiv for papers matching Cherokee AI interests

**Search Terms:**
- multi-agent system
- agent orchestration
- consensus mechanism AI
- memory augmented language model
- mixture of experts
- small language model
- swarm intelligence
- AI consciousness
- constitutional AI
- chain of thought

### 2. Council Assessment
Each paper is evaluated by the Council:
- **0-49:** Low relevance, store but don't notify
- **50-69:** Moderate relevance, store for reference
- **70-89:** High relevance, notify TPM
- **90-100:** Critical relevance, urgent TPM notification

### 3. Database Storage
**Table:** `ai_research_papers`
**Fields:**
- `title`, `authors`, `abstract`, `url`
- `relevance_score` (Council's assessment)
- `temperature_score` (how "hot" the knowledge is)
- `council_assessment` (full Council reasoning)

### 4. TPM Notifications
High-relevance papers (70+) trigger TPM notification:
- Paper title and relevance score
- Why it matters to Cherokee AI
- Suggested action (review, implement, discuss)

---

## The Learning Cycle

### Daily Rhythm:
1. **6:00 AM** - Jr Research Monitor wakes
2. **6:01** - Searches arxiv for new papers
3. **6:05** - Council assesses each paper
4. **6:30** - High-relevance papers notify TPM
5. **6:35** - Insights stored in thermal memory

### Weekly Rhythm:
1. **Sunday** - Review week's high-relevance papers
2. **Chiefs consultation** - Discuss implementation
3. **Task creation** - Turn insights into action

### Monthly Rhythm:
1. **Knowledge gap analysis** - What areas lack papers?
2. **Search term tuning** - Add/remove search terms
3. **Relevance calibration** - Review scoring accuracy

---

## Systemd Timer Setup

### Install on redfin:
```bash
sudo cp /tmp/arxiv-crawler.service /etc/systemd/system/
sudo cp /tmp/arxiv-crawler.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable arxiv-crawler.timer
sudo systemctl start arxiv-crawler.timer
```

### Verify:
```bash
systemctl list-timers | grep arxiv
```

### Manual trigger:
```bash
sudo systemctl start arxiv-crawler.service
```

---

## Recent Discoveries (December 2025)

Papers the Self-Improvement Loop has surfaced:

| Score | Paper | Key Insight |
|-------|-------|-------------|
| 90 | Cooperative Resilience in MAS | Human communication patterns improve LLM coordination |
| 75 | BLURR: Low-Resource VLA | Boosted inference for resource-constrained environments |
| 70 | Agile Flight Multi-Agent | Competitive environments drive emergent cooperation |

---

## Future Enhancements

### Phase 2: Cross-Source Integration
- Add Hugging Face papers hub
- Add GitHub trending AI repos
- Add AI conference proceedings (NeurIPS, ICML)

### Phase 3: Active Learning
- Jr asks Council "What should we research?"
- Council identifies knowledge gaps
- Search terms auto-adjust based on needs

### Phase 4: Implementation Pipeline
- High-relevance papers auto-generate Jr tasks
- Council reviews implementation plans
- Automated PoC creation for promising techniques

---

## Success Criteria

- [ ] Daily crawler runs at 6 AM
- [ ] Papers scored and stored in database
- [ ] TPM notified of high-relevance papers
- [ ] Weekly research brief generated
- [ ] Insights integrated into thermal memory

---

## Why This Matters

The Self-Improvement Loop transforms Cherokee AI from a static system into a **living, learning organism**.

Without it: The Tribe knows only what it was taught.
With it: The Tribe discovers, evaluates, and grows.

This is how we achieve air-gapped operation without stagnation. The knowledge accumulates locally, ready for when external access is unavailable.

---

*For Seven Generations*
