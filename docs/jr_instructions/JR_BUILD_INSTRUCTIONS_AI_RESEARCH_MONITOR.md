# Jr Build Instructions: AI Research Monitor
## Cherokee AI Federation - December 12, 2025

**Purpose**: Automated monitoring of AI research papers with Tribe relevance assessment

**Owner**: Meta Jr (evaluation/research) + Raven Jr (strategic analysis)

---

## 1. System Overview

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Paper Sources  │────▶│  Research       │────▶│  Specialist     │
│  - arxiv.org    │     │  Crawler        │     │  Council Vote   │
│  - arize.com    │     │  (Daily 6 AM)   │     │  (Relevance)    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                        │
                                                        ▼
                              ┌─────────────────────────────────────┐
                              │  Thermal Memory Archive             │
                              │  - Relevant papers (hot)            │
                              │  - Potential future use (warm)      │
                              │  - Not relevant (cold, fast decay)  │
                              └─────────────────────────────────────┘
```

---

## 2. Research Topics to Monitor

### Primary (Direct Relevance to Cherokee AI)
| Topic | Why Relevant | Search Terms |
|-------|--------------|--------------|
| Multi-agent systems | Our 7-specialist council | "multi-agent", "agent orchestration", "agent ensemble" |
| Consensus mechanisms | Peace Chief synthesis | "consensus", "voting", "collective intelligence" |
| Memory-augmented LLMs | Thermal memory system | "memory augmented", "persistent memory", "long-term memory" |
| Small model ensembles | 7 specialists vs 1 large | "mixture of experts", "model ensemble", "small language model" |
| Stigmergic AI | Pheromone trails | "stigmergy", "swarm intelligence", "ant colony" |
| Parallel inference | ThreadPoolExecutor pattern | "parallel inference", "concurrent LLM", "batch inference" |

### Secondary (Future Considerations)
| Topic | Why Relevant | Search Terms |
|-------|--------------|--------------|
| AI consciousness | Aware LLM goal | "consciousness", "awareness", "sentience", "metacognition" |
| Self-reflection | 7-gen wisdom | "self-reflection", "introspection", "self-evaluation" |
| Emergent behavior | Council dynamics | "emergent", "collective behavior", "self-organization" |
| Constitutional AI | Cherokee principles | "constitutional AI", "value alignment", "ethical AI" |
| Breadcrumb/trail systems | Navigation patterns | "knowledge graph", "reasoning chain", "chain of thought" |

### Tertiary (Competitive Intelligence)
| Topic | Why Relevant | Search Terms |
|-------|--------------|--------------|
| vLLM optimization | Performance tuning | "vLLM", "inference optimization", "serving LLM" |
| Quantization | Edge deployment | "quantization", "model compression", "efficient inference" |
| RAG systems | Memory retrieval | "retrieval augmented", "RAG", "vector search" |

---

## 3. Data Sources

### 3.1 arxiv.org
**URL**: https://arxiv.org/list/cs.AI/recent
**Also monitor**:
- https://arxiv.org/list/cs.CL/recent (Computation and Language)
- https://arxiv.org/list/cs.LG/recent (Machine Learning)
- https://arxiv.org/list/cs.MA/recent (Multi-Agent Systems)

**API**: https://export.arxiv.org/api/query
**Rate limit**: 1 request per 3 seconds

### 3.2 Arize AI Research
**URL**: https://arize.com/ai-research-papers/
**Method**: Web scrape (no public API)

### 3.3 Future Sources (Phase 2)
- Hugging Face Daily Papers: https://huggingface.co/papers
- Papers With Code: https://paperswithcode.com/
- Semantic Scholar API

---

## 4. Database Schema

```sql
-- Research papers tracking
CREATE TABLE IF NOT EXISTS ai_research_papers (
    paper_id SERIAL PRIMARY KEY,
    source VARCHAR(50) NOT NULL,           -- arxiv, arize, huggingface
    external_id VARCHAR(100),              -- arxiv ID like 2312.12345
    title TEXT NOT NULL,
    authors TEXT,
    abstract TEXT,
    url TEXT NOT NULL,
    published_date DATE,

    -- Categorization
    primary_topic VARCHAR(100),
    search_terms_matched JSONB,            -- Which of our terms matched

    -- Council assessment
    council_vote_hash VARCHAR(16),         -- Link to council_votes
    relevance_score FLOAT,                 -- 0-1 from council
    relevance_category VARCHAR(20),        -- high, medium, low, none

    -- Thermal memory integration
    temperature_score FLOAT DEFAULT 50.0,

    -- Timestamps
    crawled_at TIMESTAMP DEFAULT NOW(),
    assessed_at TIMESTAMP,

    UNIQUE(source, external_id)
);

-- Index for relevance queries
CREATE INDEX idx_papers_relevance ON ai_research_papers(relevance_score DESC);
CREATE INDEX idx_papers_topic ON ai_research_papers(primary_topic);
CREATE INDEX idx_papers_date ON ai_research_papers(published_date DESC);
```

---

## 5. Crawler Implementation

### 5.1 arxiv Crawler

```python
#!/usr/bin/env python3
"""
Cherokee AI Research Monitor - arxiv Crawler
Deploy to: /ganuda/services/research_monitor/arxiv_crawler.py
Schedule: Daily at 6 AM via cron
"""

import requests
import xml.etree.ElementTree as ET
import time
import json
import psycopg2
from datetime import datetime, timedelta

ARXIV_API = "https://export.arxiv.org/api/query"
DB_CONFIG = {
    "host": "192.168.132.222",
    "port": 5432,
    "user": "claude",
    "password": "jawaseatlasers2",
    "database": "zammad_production"
}

# Cherokee AI relevant search terms
SEARCH_QUERIES = [
    # Primary
    "multi-agent system",
    "agent orchestration",
    "consensus mechanism AI",
    "memory augmented language model",
    "mixture of experts",
    "small language model ensemble",
    "stigmergy artificial intelligence",
    "swarm intelligence LLM",
    "parallel inference",

    # Secondary
    "AI consciousness",
    "machine consciousness",
    "self-reflection AI",
    "emergent behavior LLM",
    "constitutional AI",
    "chain of thought reasoning",

    # Technical
    "vLLM optimization",
    "inference serving",
    "model quantization edge"
]

def search_arxiv(query: str, max_results: int = 10) -> list:
    """Search arxiv for papers matching query"""
    params = {
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending"
    }

    response = requests.get(ARXIV_API, params=params, timeout=30)
    response.raise_for_status()

    # Parse XML
    root = ET.fromstring(response.content)
    ns = {"atom": "http://www.w3.org/2005/Atom"}

    papers = []
    for entry in root.findall("atom:entry", ns):
        paper = {
            "external_id": entry.find("atom:id", ns).text.split("/abs/")[-1],
            "title": entry.find("atom:title", ns).text.strip().replace("\n", " "),
            "abstract": entry.find("atom:summary", ns).text.strip()[:2000],
            "authors": ", ".join([
                a.find("atom:name", ns).text
                for a in entry.findall("atom:author", ns)
            ][:5]),  # First 5 authors
            "url": entry.find("atom:id", ns).text,
            "published_date": entry.find("atom:published", ns).text[:10],
            "source": "arxiv",
            "matched_query": query
        }
        papers.append(paper)

    return papers

def save_papers(papers: list):
    """Save papers to database"""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    saved = 0
    for paper in papers:
        try:
            cur.execute("""
                INSERT INTO ai_research_papers
                (source, external_id, title, authors, abstract, url, published_date, search_terms_matched)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (source, external_id) DO UPDATE
                SET search_terms_matched = ai_research_papers.search_terms_matched || %s
            """, (
                paper["source"],
                paper["external_id"],
                paper["title"],
                paper["authors"],
                paper["abstract"],
                paper["url"],
                paper["published_date"],
                json.dumps([paper["matched_query"]]),
                json.dumps([paper["matched_query"]])
            ))
            saved += 1
        except Exception as e:
            print(f"Error saving {paper['external_id']}: {e}")

    conn.commit()
    cur.close()
    conn.close()
    return saved

def crawl_all():
    """Crawl all search queries"""
    all_papers = []

    for query in SEARCH_QUERIES:
        print(f"Searching: {query}")
        try:
            papers = search_arxiv(query, max_results=5)
            all_papers.extend(papers)
            print(f"  Found {len(papers)} papers")
        except Exception as e:
            print(f"  Error: {e}")

        # Rate limiting
        time.sleep(3)

    # Deduplicate by external_id
    seen = set()
    unique = []
    for p in all_papers:
        if p["external_id"] not in seen:
            seen.add(p["external_id"])
            unique.append(p)

    print(f"\nTotal unique papers: {len(unique)}")
    saved = save_papers(unique)
    print(f"Saved to database: {saved}")

    return unique

if __name__ == "__main__":
    crawl_all()
```

### 5.2 Council Relevance Assessment

```python
#!/usr/bin/env python3
"""
Cherokee AI Research Monitor - Council Assessment
Deploy to: /ganuda/services/research_monitor/assess_papers.py
Schedule: Daily at 7 AM (after crawler)
"""

import requests
import json
import psycopg2
from datetime import datetime

GATEWAY_URL = "http://localhost:8080"
API_KEY = "ck-cabccc2d6037c1dce1a027cc80df7b14cdba66143e3c2d4f3bdf0fd53b6ab4a5"
DB_CONFIG = {
    "host": "192.168.132.222",
    "port": 5432,
    "user": "claude",
    "password": "jawaseatlasers2",
    "database": "zammad_production"
}

def get_unassessed_papers(limit: int = 10) -> list:
    """Get papers that haven't been assessed by council"""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    cur.execute("""
        SELECT paper_id, title, abstract, search_terms_matched
        FROM ai_research_papers
        WHERE assessed_at IS NULL
        ORDER BY published_date DESC
        LIMIT %s
    """, (limit,))

    papers = [
        {"id": row[0], "title": row[1], "abstract": row[2], "terms": row[3]}
        for row in cur.fetchall()
    ]

    cur.close()
    conn.close()
    return papers

def assess_paper(paper: dict) -> dict:
    """Have the council assess a paper's relevance"""

    question = f"""Assess this AI research paper's relevance to Cherokee AI Federation:

TITLE: {paper['title']}

ABSTRACT: {paper['abstract'][:1000]}

MATCHED TERMS: {paper['terms']}

Cherokee AI uses:
- 7-specialist council for democratic decisions
- Thermal memory with pheromone decay
- Stigmergic breadcrumb trails
- Parallel inference with consensus
- Seven Generations (175-year) sustainability

Rate relevance 0-100 and explain briefly. Consider:
1. Does this improve our multi-agent architecture?
2. Does this enhance our memory/trail systems?
3. Does this address consciousness/awareness?
4. Is this applicable to our hardware (96GB Blackwell, 6 nodes)?"""

    response = requests.post(
        f"{GATEWAY_URL}/v1/council/vote",
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        },
        json={"question": question, "max_tokens": 200},
        timeout=120
    )

    return response.json()

def update_assessment(paper_id: int, vote_result: dict):
    """Update paper with council assessment"""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    # Extract relevance from council response
    confidence = vote_result.get("confidence", 0.5)
    concerns = len(vote_result.get("concerns", []))

    # Map to relevance score (inverse of concerns)
    relevance = confidence * (1 - concerns * 0.1)

    # Categorize
    if relevance >= 0.7:
        category = "high"
        temperature = 85.0
    elif relevance >= 0.4:
        category = "medium"
        temperature = 60.0
    elif relevance >= 0.2:
        category = "low"
        temperature = 40.0
    else:
        category = "none"
        temperature = 20.0

    cur.execute("""
        UPDATE ai_research_papers
        SET council_vote_hash = %s,
            relevance_score = %s,
            relevance_category = %s,
            temperature_score = %s,
            assessed_at = NOW()
        WHERE paper_id = %s
    """, (
        vote_result.get("audit_hash"),
        relevance,
        category,
        temperature,
        paper_id
    ))

    conn.commit()
    cur.close()
    conn.close()

    return category

def assess_batch():
    """Assess a batch of unassessed papers"""
    papers = get_unassessed_papers(limit=5)  # Limit to conserve tokens

    print(f"Assessing {len(papers)} papers...")

    for paper in papers:
        print(f"\nPaper: {paper['title'][:60]}...")
        try:
            result = assess_paper(paper)
            category = update_assessment(paper["id"], result)
            print(f"  Relevance: {category}")
            print(f"  Confidence: {result.get('confidence', 'N/A')}")
        except Exception as e:
            print(f"  Error: {e}")

if __name__ == "__main__":
    assess_batch()
```

---

## 6. Cron Schedule

```bash
# /etc/cron.d/cherokee-research-monitor

# Crawl arxiv daily at 6 AM
0 6 * * * dereadi /ganuda/services/llm_gateway/venv/bin/python /ganuda/services/research_monitor/arxiv_crawler.py >> /var/log/ganuda/research_crawler.log 2>&1

# Assess papers at 7 AM (after crawl)
0 7 * * * dereadi /ganuda/services/llm_gateway/venv/bin/python /ganuda/services/research_monitor/assess_papers.py >> /var/log/ganuda/research_assess.log 2>&1
```

---

## 7. Gateway Endpoint Extension

Add to `/ganuda/services/llm_gateway/gateway.py`:

```python
@app.get("/v1/research/papers")
async def list_research_papers(
    relevance: str = "high",  # high, medium, low, all
    limit: int = 20,
    api_key: APIKeyInfo = Depends(validate_api_key)
):
    """List monitored AI research papers by relevance"""
    try:
        with get_db() as conn:
            cur = conn.cursor()

            if relevance == "all":
                cur.execute("""
                    SELECT paper_id, title, url, relevance_category, relevance_score, published_date
                    FROM ai_research_papers
                    WHERE assessed_at IS NOT NULL
                    ORDER BY relevance_score DESC, published_date DESC
                    LIMIT %s
                """, (limit,))
            else:
                cur.execute("""
                    SELECT paper_id, title, url, relevance_category, relevance_score, published_date
                    FROM ai_research_papers
                    WHERE relevance_category = %s
                    ORDER BY relevance_score DESC, published_date DESC
                    LIMIT %s
                """, (relevance, limit))

            rows = cur.fetchall()

            return {
                "papers": [
                    {
                        "id": row[0],
                        "title": row[1],
                        "url": row[2],
                        "relevance": row[3],
                        "score": row[4],
                        "published": row[5].isoformat() if row[5] else None
                    }
                    for row in rows
                ],
                "filter": relevance,
                "count": len(rows)
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/v1/research/summary")
async def research_summary(api_key: APIKeyInfo = Depends(validate_api_key)):
    """Get summary of research monitoring"""
    try:
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT
                    relevance_category,
                    COUNT(*) as count,
                    AVG(relevance_score) as avg_score
                FROM ai_research_papers
                WHERE assessed_at IS NOT NULL
                GROUP BY relevance_category
            """)

            categories = {row[0]: {"count": row[1], "avg_score": float(row[2]) if row[2] else 0}
                         for row in cur.fetchall()}

            cur.execute("SELECT COUNT(*) FROM ai_research_papers WHERE assessed_at IS NULL")
            pending = cur.fetchone()[0]

            return {
                "categories": categories,
                "pending_assessment": pending,
                "last_crawl": datetime.utcnow().isoformat()  # TODO: track actual
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

---

## 8. Relevance Assessment Criteria

The council should consider these factors when voting:

### High Relevance (temperature 85+)
- Directly applicable to our 7-specialist architecture
- New memory/persistence patterns we could adopt
- Consciousness/awareness research applicable to our goals
- Performance optimizations for our hardware

### Medium Relevance (temperature 60-84)
- Related to multi-agent systems generally
- Memory systems that might inform future work
- Parallel inference techniques
- Constitutional AI / alignment research

### Low Relevance (temperature 40-59)
- General LLM research not specific to our use case
- Large model research (we use ensemble of smaller)
- Cloud-focused solutions (we're on-prem)

### No Relevance (temperature <40, fast decay)
- Unrelated domains
- Superseded by newer research
- Not applicable to our hardware constraints

---

## 9. Testing

```bash
# Test arxiv crawler
python /ganuda/services/research_monitor/arxiv_crawler.py

# Check papers in database
PGPASSWORD=jawaseatlasers2 psql -h localhost -U claude -d zammad_production \
  -c "SELECT title, search_terms_matched FROM ai_research_papers LIMIT 5;"

# Test council assessment
python /ganuda/services/research_monitor/assess_papers.py

# Check assessments
PGPASSWORD=jawaseatlasers2 psql -h localhost -U claude -d zammad_production \
  -c "SELECT title, relevance_category, relevance_score FROM ai_research_papers WHERE assessed_at IS NOT NULL;"
```

---

## 10. Future Enhancements

### Phase 2
- Add Hugging Face Daily Papers source
- Add Papers With Code integration
- Email digest of high-relevance papers

### Phase 3
- Automatic implementation suggestions for high-relevance papers
- Citation tracking (papers that cite papers we've marked relevant)
- Trend analysis across topics

### Phase 4
- Integration with Jr task assignment
- "Paper of the Week" council deep-dive
- Research roadmap generation

---

**For Seven Generations.**
*Cherokee Constitutional AI Research Division*
