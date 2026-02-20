#!/usr/bin/env python3
"""
Council Browser Agent — Playwright MCP integration for Cherokee AI Federation.

Uses mcp-use + LangChain to give the Council web browsing capability
via Playwright MCP server tools on sasass (tunneled to localhost:8931).

Council vote #69d636ba (PROCEED, 0.844, 7/7 unanimous).
"""

import os
import json
import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# MCP server connection - tunneled from sasass via SSH
MCP_SSE_URL = os.environ.get("MCP_SSE_URL", "http://localhost:8931/sse")

# vLLM endpoint for LLM reasoning
VLLM_BASE_URL = os.environ.get("VLLM_BASE_URL", "http://192.168.132.223:8000/v1")
VLLM_MODEL = os.environ.get("VLLM_MODEL", "/ganuda/models/qwen2.5-72b-instruct-awq")
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
        from mcp_use import MCPClient, MCPAgent
        from langchain_openai import ChatOpenAI

        # Connect to Playwright MCP server via tunnel
        mcp_config = {
            "mcpServers": {
                "playwright": {
                    "url": MCP_SSE_URL
                }
            }
        }

        client = MCPClient.from_dict(mcp_config)

        # Use local Qwen 72B for reasoning
        llm = ChatOpenAI(
            base_url=VLLM_BASE_URL,
            model=VLLM_MODEL,
            api_key=VLLM_API_KEY,
            temperature=0.1,
            max_tokens=4096
        )

        # Create the agent
        agent = MCPAgent(llm=llm, client=client, max_steps=max(max_steps, 30))

        # Build the browsing task with explicit tool guidance
        task = f"Use the browser_navigate tool to go to {url} then use browser_snapshot to get the page content. {prompt}"

        # Execute
        result = await agent.run(task)

        await client.close_all_sessions()

        return {
            "result": result,
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
        prompt=f"Find the top {max_results} results. For each, extract the title, URL, and a brief summary. Then provide an overall synthesis.",
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

    logging.basicConfig(level=logging.INFO)

    if sys.argv[1] == "--search":
        query = " ".join(sys.argv[2:])
        result = asyncio.run(search_and_summarize(query))
    else:
        url = sys.argv[1]
        prompt = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "Summarize the main content of this page."
        result = asyncio.run(browse_url(url, prompt))

    print(json.dumps(result, indent=2))
