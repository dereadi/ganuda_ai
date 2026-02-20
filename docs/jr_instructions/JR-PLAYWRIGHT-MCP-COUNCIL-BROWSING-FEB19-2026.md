# Jr Instruction: Playwright MCP Server — Council Web Browsing

**Kanban:** #1839
**Council Vote:** #69d636ba (PROCEED, 0.844, 7/7 unanimous)
**Priority:** 3
**Assigned Jr:** Software Engineer Jr.
**Long Man Phase:** BUILD

---

## Overview

Deploy a Playwright MCP server that gives the Council the ability to browse the web autonomously. This wires Playwright's 19+ browser tools (navigate, click, fill, screenshot, etc.) into our existing LLM infrastructure via `mcp-use` + LangChain, pointed at Qwen 72B on redfin:8000.

The MCP server runs on sasass (which has a display for headed mode when needed). The Python integration layer runs on redfin alongside the gateway.

---

## Step 1: Create the MCP browser agent wrapper

Create `/ganuda/services/browser_agent/council_browser.py`

```python
#!/usr/bin/env python3
"""
Council Browser Agent — Playwright MCP integration for Cherokee AI Federation.

Uses mcp-use + LangChain to give the Council web browsing capability
via Playwright MCP server tools. Points at local Qwen 72B on redfin:8000.

Council vote #69d636da (PROCEED, 0.844, 7/7 unanimous).
"""

import os
import json
import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# MCP server connection config
MCP_SERVER_HOST = os.environ.get("MCP_SERVER_HOST", "192.168.132.241")
MCP_SERVER_PORT = int(os.environ.get("MCP_SERVER_PORT", "8931"))

# vLLM endpoint for LLM reasoning
VLLM_BASE_URL = os.environ.get("VLLM_BASE_URL", "http://192.168.132.223:8000/v1")
VLLM_MODEL = os.environ.get("VLLM_MODEL", "Qwen/Qwen2.5-72B-Instruct-AWQ")
VLLM_API_KEY = os.environ.get("VLLM_API_KEY", "not-needed")


async def browse_url(url: str, prompt: str, max_steps: int = 10) -> dict:
    """
    Browse a URL and extract information using the Council's LLM.

    Args:
        url: The URL to browse
        prompt: What to look for / extract from the page
        max_steps: Maximum number of browser interaction steps

    Returns:
        dict with 'result', 'steps_taken', 'urls_visited', 'timestamp'
    """
    try:
        from mcp_use import MCPClient
        from langchain_openai import ChatOpenAI

        # Connect to Playwright MCP server
        mcp_config = {
            "mcpServers": {
                "playwright": {
                    "url": f"http://{MCP_SERVER_HOST}:{MCP_SERVER_PORT}/sse"
                }
            }
        }

        client = MCPClient(mcp_config)

        # Use local Qwen 72B for reasoning
        llm = ChatOpenAI(
            base_url=VLLM_BASE_URL,
            model=VLLM_MODEL,
            api_key=VLLM_API_KEY,
            temperature=0.1,
            max_tokens=4096
        )

        # Create the agent
        from mcp_use import create_react_agent
        agent = create_react_agent(llm, client)

        # Build the browsing task
        task = f"Navigate to {url} and {prompt}"

        # Execute
        result = await agent.ainvoke({"input": task})

        return {
            "result": result.get("output", ""),
            "steps_taken": len(result.get("intermediate_steps", [])),
            "urls_visited": [url],
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success"
        }

    except ImportError as e:
        logger.error(f"Missing dependency: {e}. Install: pip install mcp-use langchain-openai")
        return {
            "result": f"Missing dependency: {e}",
            "status": "error",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Browser agent error: {e}")
        return {
            "result": str(e),
            "status": "error",
            "timestamp": datetime.utcnow().isoformat()
        }


async def search_and_summarize(query: str, max_results: int = 5) -> dict:
    """
    Search the web and summarize findings using Council LLM.

    Args:
        query: Search query
        max_results: Number of results to process

    Returns:
        dict with 'summary', 'sources', 'timestamp'
    """
    search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
    result = await browse_url(
        url=search_url,
        prompt=f"Find the top {max_results} results for this search query. For each result, extract the title, URL, and a brief summary of the content. Then provide an overall synthesis.",
        max_steps=15
    )

    return {
        "query": query,
        "summary": result.get("result", ""),
        "sources": result.get("urls_visited", []),
        "timestamp": datetime.utcnow().isoformat(),
        "status": result.get("status", "unknown")
    }


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python council_browser.py <url> [prompt]")
        print("       python council_browser.py --search <query>")
        sys.exit(1)

    if sys.argv[1] == "--search":
        query = " ".join(sys.argv[2:])
        result = asyncio.run(search_and_summarize(query))
    else:
        url = sys.argv[1]
        prompt = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "Summarize the main content of this page."
        result = asyncio.run(browse_url(url, prompt))

    print(json.dumps(result, indent=2))
```

---

## Step 2: Create the gateway endpoint for browser requests

File: `/ganuda/scripts/cherokee_council_gateway.py`

<<<<<<< SEARCH
@app.route("/health", methods=["GET"])
def health():
=======
@app.route("/v1/browser/browse", methods=["POST"])
def browser_browse():
    """Browse a URL using Playwright MCP + Council LLM."""
    import asyncio
    data = request.get_json()
    url = data.get("url", "")
    prompt = data.get("prompt", "Summarize the main content of this page.")
    max_steps = data.get("max_steps", 10)

    if not url:
        return jsonify({"error": "url is required"}), 400

    try:
        from services.browser_agent.council_browser import browse_url
        result = asyncio.run(browse_url(url, prompt, max_steps))
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/v1/browser/search", methods=["POST"])
def browser_search():
    """Search the web and summarize using Playwright MCP + Council LLM."""
    import asyncio
    data = request.get_json()
    query = data.get("query", "")
    max_results = data.get("max_results", 5)

    if not query:
        return jsonify({"error": "query is required"}), 400

    try:
        from services.browser_agent.council_browser import search_and_summarize
        result = asyncio.run(search_and_summarize(query, max_results))
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/health", methods=["GET"])
def health():
>>>>>>> REPLACE

---

## Manual Steps (TPM)

These steps require sudo or node-specific access. Do NOT put these in bash code blocks.

### On sasass (192.168.132.241):

1. Install Playwright MCP server:
```text
npm install -g @playwright/mcp@latest
npx playwright install chromium
```

2. Start the MCP server (test):
```text
npx @playwright/mcp@latest --port 8931 --headless --browser chromium
```

3. For persistent service, create a launchd plist at:
   `/Users/Shared/ganuda/services/browser_agent/com.cherokee.playwright-mcp.plist`

### On redfin:

4. Install Python dependencies:
```text
source /ganuda/home/dereadi/cherokee_venv/bin/activate
pip install mcp-use langchain-openai
```

5. Test the browser agent:
```text
cd /ganuda && python3 -c "
from services.browser_agent.council_browser import browse_url
import asyncio
result = asyncio.run(browse_url('https://news.ycombinator.com', 'List the top 5 stories'))
print(result)
"
```

6. Restart the gateway after Sr applies the endpoint:
```text
sudo systemctl restart llm-gateway
```

7. Test the gateway endpoint:
```text
curl -X POST http://localhost:8080/v1/browser/browse \
  -H "Content-Type: application/json" \
  -d '{"url": "https://news.ycombinator.com", "prompt": "List the top 3 stories"}'
```

---

## Acceptance Criteria

- [ ] `council_browser.py` created at `/ganuda/services/browser_agent/`
- [ ] `browse_url()` connects to Playwright MCP via mcp-use
- [ ] `search_and_summarize()` wraps search + browse
- [ ] Gateway has `/v1/browser/browse` and `/v1/browser/search` endpoints
- [ ] Uses Qwen 72B on redfin:8000 for LLM reasoning (NOT external API)
- [ ] CLI mode works: `python council_browser.py <url> [prompt]`
- [ ] No hardcoded credentials — all config via environment variables
