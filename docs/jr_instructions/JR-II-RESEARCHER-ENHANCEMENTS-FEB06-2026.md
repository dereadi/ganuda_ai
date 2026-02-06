# JR Instruction: ii-researcher Enhancements

**ID:** JR-II-RESEARCHER-ENHANCEMENTS-FEB06-2026
**Priority:** P2 (Enhancement)
**Assigned:** IT Jr
**Created:** 2026-02-06
**Status:** Ready

---

## Context

Our ii-researcher installation is v0.1.5 (latest). After reviewing the upstream repo, several enhancements are worth considering for Federation use.

**Upstream:** https://github.com/Intelligent-Internet/ii-researcher
**Our instance:** `/ganuda/services/ii-researcher/`
**Current service:** `ii-researcher.service` on port 8090

---

## Enhancement Opportunities

### 1. MCP Server Integration (P2)

We already have `/ganuda/services/ii-researcher/mcp/server.py` but it's not deployed.

**Benefit:** Enables Claude Desktop integration for direct research queries.

**Implementation:**
```bash
# Add to systemd or run separately
cd /ganuda/services/ii-researcher
python -m mcp.server
```

**Use Case:** TPM could use Claude Desktop with MCP to trigger deep research directly.

---

### 2. Jina Scraper (P3)

Upstream added Jina integration for more reliable web scraping.

**Location:** `/ganuda/services/ii-researcher/ii_researcher/tool_clients/scraper/jina/`

**Config:** Add `JINA_API_KEY` to environment if we want to use it.

**Benefit:** Alternative scraper when Firecrawl or BeautifulSoup fail.

---

### 3. Multi-lingual Report Generation (P3)

Upstream enhanced report generation with multi-lingual support.

**Relevance:** Cherokee language support for TribeAssist research queries.

**Check:** Review `/ganuda/services/ii-researcher/ii_researcher/reasoning/builders/report.py` for language options.

---

### 4. II-SEARCH-CIR-4B Model Demo (P4 - Research)

Upstream added demo for a smaller search model.

**Location:** `/ganuda/services/ii-researcher/examples/ii_search_4b/`

**Potential:** Could run on sasass2 (Mac Studio) for edge inference without GPU dependency.

---

### 5. Timeout Tuning (P2)

Current config may need adjustment:
- Process timeout: 300s
- Query timeout: 20s
- Scrape timeout: 30s

**Check current config:**
```bash
grep -r "timeout" /ganuda/services/ii-researcher/ii_researcher/config.py
```

**Our API call uses 180s timeout** - may need to increase for complex queries.

---

### 6. LiteLLM Proxy Integration (P3)

ii-researcher supports LiteLLM for flexible model routing.

**Benefit:** Could route to our local vLLM (Nemotron-9B) instead of external APIs.

**Config:** Set `LITELLM_BASE_URL` and model name in environment.

---

## Recommended Priority Order

1. **P0 (Done):** SSE parsing fix (JR-FIX-II-RESEARCHER-SSE-PARSING-FEB06-2026)
2. **P2:** MCP Server deployment for Claude Desktop
3. **P2:** Timeout tuning (increase to 300s for deep research)
4. **P3:** LiteLLM integration with local vLLM
5. **P3:** Jina scraper as fallback
6. **P4:** II-SEARCH-CIR-4B evaluation for edge deployment

---

## Verification

After any enhancement:
```bash
# Restart service
sudo systemctl restart ii-researcher.service

# Test API
curl "http://localhost:8090/search?question=test&max_steps=5" | head -50

# Monitor logs
journalctl -u ii-researcher.service -f
```

---

**Document Version:** 1.0
**TPM:** Claude Opus 4.5
**Sacred Fire:** Yes - Research capability enhancement
