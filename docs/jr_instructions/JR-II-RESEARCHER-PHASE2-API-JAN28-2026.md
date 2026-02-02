# JR Instruction: ii-researcher Phase 2 - API Integration

**JR ID:** JR-II-RESEARCHER-PHASE2-API-JAN28-2026
**Priority:** P2
**Assigned To:** Software Engineer Jr.
**Council Vote:** 166956a7959c2232
**Ultrathink:** ULTRATHINK-II-RESEARCHER-INTEGRATION-JAN28-2026.md
**Depends On:** JR-II-RESEARCHER-PHASE1-INSTALL-JAN28-2026

---

## Objective

Create unified research interface and integrate ii-researcher with Telegram Chief, LLM Gateway, and VetAssist.

---

## Critical: Token Efficiency

**IMPORTANT:** ii-researcher streams verbose reasoning output (thinking, search queries, intermediate steps). This burns tokens fast when connected to Jrs or other LLM consumers.

The research client MUST:
1. Consume the full SSE stream internally
2. Parse for the "complete" event containing the final report
3. Return ONLY the final answer + sources + confidence
4. Discard all intermediate reasoning tokens

Provide two endpoints:
- `/v1/research` - Returns just final answer (default, token-efficient)
- `/v1/research/stream` - Returns full reasoning stream (debugging only)

---

## Steps

### 1. Create Research Client Library

Create `/ganuda/lib/research_client.py`:

```python
#!/usr/bin/env python3
"""
Research Client - Unified interface to ii-researcher.

Provides simple API for all Cherokee products to perform web research.

For Seven Generations - Cherokee AI Federation
"""

import httpx
from typing import Optional, Dict, List, Any
import asyncio

II_RESEARCHER_URL = "http://localhost:8090"

class ResearchClient:
    """Client for ii-researcher deep search."""

    def __init__(self, base_url: str = II_RESEARCHER_URL):
        self.base_url = base_url

    async def search(
        self,
        query: str,
        max_sources: int = 5,
        depth: str = "standard"
    ) -> Dict[str, Any]:
        """
        Perform a research query.

        Args:
            query: The research question
            max_sources: Maximum sources to retrieve (1-20)
            depth: "standard" or "deep"

        Returns:
            Dict with answer, sources, confidence, search_time_ms
        """
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/search",
                json={
                    "query": query,
                    "max_results": max_sources,
                    "depth": depth
                }
            )
            response.raise_for_status()
            return response.json()

    async def health_check(self) -> bool:
        """Check if ii-researcher is available."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/health")
                return response.status_code == 200
        except:
            return False

# Synchronous wrapper for simple scripts
def search_sync(query: str, max_sources: int = 5) -> Dict:
    """Synchronous search wrapper."""
    client = ResearchClient()
    return asyncio.run(client.search(query, max_sources))
```

### 2. Add Research Route to LLM Gateway

Create `/ganuda/services/llm_gateway/routes/research.py`:

```python
#!/usr/bin/env python3
"""
Research route for LLM Gateway.

Exposes ii-researcher via /v1/research endpoint.

For Seven Generations - Cherokee AI Federation
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import httpx
import time

router = APIRouter()

II_RESEARCHER_URL = "http://localhost:8090"

class ResearchRequest(BaseModel):
    query: str
    max_sources: Optional[int] = 5
    depth: Optional[str] = "standard"
    output_format: Optional[str] = "summary"

class Source(BaseModel):
    url: str
    title: str
    snippet: str

class ResearchResponse(BaseModel):
    answer: str
    sources: List[Source]
    confidence: float
    search_time_ms: int

@router.post("/v1/research", response_model=ResearchResponse)
async def research(request: ResearchRequest):
    """
    Perform web research using ii-researcher.

    Returns synthesized answer with sources and confidence score.
    """
    start_time = time.time()

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{II_RESEARCHER_URL}/search",
                json={
                    "query": request.query,
                    "max_results": request.max_sources,
                    "depth": request.depth
                }
            )
            response.raise_for_status()
            result = response.json()
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Research request timed out")
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"ii-researcher error: {str(e)}")

    search_time = int((time.time() - start_time) * 1000)

    return ResearchResponse(
        answer=result.get("answer", "No answer generated"),
        sources=[Source(**s) for s in result.get("sources", [])],
        confidence=result.get("confidence", 0.5),
        search_time_ms=search_time
    )

@router.get("/v1/research/health")
async def research_health():
    """Check ii-researcher health."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{II_RESEARCHER_URL}/health")
            return {"status": "healthy" if response.status_code == 200 else "unhealthy"}
    except:
        return {"status": "unavailable"}
```

### 3. Integrate with Telegram Chief

Add to `/ganuda/telegram_bot/telegram_chief.py` command handler:

```python
# Add to imports
from lib.research_client import ResearchClient

# Add /research command handler
async def research_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /research command for web research."""
    query = ' '.join(context.args)
    if not query:
        await update.message.reply_text("Usage: /research <your question>")
        return

    # Send searching indicator
    msg = await update.message.reply_text("🔍 Researching...")

    try:
        client = ResearchClient()
        result = await client.search(query, max_sources=5)

        # Format response
        response = f"📊 **Research Results**\n\n{result['answer']}\n\n"
        response += "**Sources:**\n"
        for i, source in enumerate(result['sources'][:5], 1):
            response += f"{i}. [{source['title']}]({source['url']})\n"
        response += f"\n_Confidence: {result['confidence']:.0%}_"

        await msg.edit_text(response, parse_mode='Markdown')
    except Exception as e:
        await msg.edit_text(f"❌ Research failed: {str(e)}")
```

### 4. Create VetAssist Research Panel

Add research component to VetAssist frontend:

```javascript
// /ganuda/vetassist/frontend/src/components/ResearchPanel.jsx
import React, { useState } from 'react';

export function ResearchPanel() {
  const [query, setQuery] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSearch = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/research', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, max_sources: 5 })
      });
      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.error('Research failed:', error);
    }
    setLoading(false);
  };

  return (
    <div className="research-panel">
      <h3>VA Research Assistant</h3>
      <input
        type="text"
        placeholder="Ask about VA benefits, ratings, regulations..."
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />
      <button onClick={handleSearch} disabled={loading}>
        {loading ? 'Searching...' : 'Search'}
      </button>
      {result && (
        <div className="research-result">
          <p>{result.answer}</p>
          <ul>
            {result.sources.map((s, i) => (
              <li key={i}><a href={s.url}>{s.title}</a></li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
```

---

## Verification

```bash
# Test research client
python3 -c "from lib.research_client import search_sync; print(search_sync('VA disability rating'))"

# Test gateway endpoint
curl -X POST http://localhost:8080/v1/research \
  -H "Content-Type: application/json" \
  -d '{"query": "VA tinnitus rating percentage"}'

# Test Telegram command
# Send /research VA sleep apnea secondary to PTSD to bot
```

---

## Notes

- httpx is used for async HTTP calls (install with pip if not present)
- Timeout is set to 60s for deep research queries
- Rate limiting will be added in Phase 3

---

FOR SEVEN GENERATIONS
