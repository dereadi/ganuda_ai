#!/usr/bin/env python3
"""
Research Client - Token-efficient wrapper for ii-researcher.

Consumes the SSE stream internally and returns only the final answer,
discarding verbose reasoning tokens to save on LLM token usage.

For Seven Generations - Cherokee AI Federation
"""

import os
import json
import httpx
from typing import Optional, Dict, List, Any
from dataclasses import dataclass

II_RESEARCHER_URL = os.environ.get("II_RESEARCHER_URL", "http://localhost:8090")


@dataclass
class ResearchResult:
    """Structured research result."""
    answer: str
    sources: List[Dict[str, str]]
    confidence: float
    search_time_ms: int
    error: Optional[str] = None


class ResearchClient:
    """
    Token-efficient client for ii-researcher.

    Consumes the full SSE stream but only returns the final answer,
    discarding intermediate reasoning to save tokens.
    """

    def __init__(self, base_url: str = II_RESEARCHER_URL, timeout: float = 120.0):
        self.base_url = base_url
        self.timeout = timeout

    def search(
        self,
        query: str,
        max_steps: int = 5,
        verbose: bool = False
    ) -> ResearchResult:
        """
        Perform a research query and return only the final answer.

        Args:
            query: The research question
            max_steps: Maximum reasoning steps (default 5 for efficiency)
            verbose: If True, print reasoning steps (for debugging)

        Returns:
            ResearchResult with answer, sources, confidence
        """
        import time
        start_time = time.time()

        try:
            # Stream the response
            with httpx.Client(timeout=self.timeout) as client:
                with client.stream(
                    "GET",
                    f"{self.base_url}/search",
                    params={"question": query, "max_steps": max_steps}
                ) as response:
                    response.raise_for_status()

                    final_answer = ""
                    sources = []
                    reasoning_tokens = 0

                    for line in response.iter_lines():
                        if not line or not line.startswith("data: "):
                            continue

                        try:
                            data = json.loads(line[6:])  # Strip "data: " prefix
                            event_type = data.get("type", "")

                            if verbose:
                                print(f"[{event_type}] {str(data.get('data', ''))[:100]}")

                            # Count reasoning tokens (for metrics)
                            if event_type == "reasoning":
                                reasoning_tokens += len(str(data.get("data", {}).get("reasoning", "")))

                            # Capture the final report/answer (ii-researcher uses "writing_report")
                            elif event_type == "writing_report":
                                report_data = data.get("data", {})
                                if isinstance(report_data, dict):
                                    # final_report is cumulative, use = not +=
                                    final_answer = report_data.get("final_report", "")
                                else:
                                    final_answer = str(report_data)

                            # Capture completion event
                            elif event_type == "complete":
                                complete_data = data.get("data", {})
                                if isinstance(complete_data, dict):
                                    # Extract final report if present (ii-researcher uses "final_report")
                                    if "final_report" in complete_data:
                                        final_answer = complete_data["final_report"]
                                    elif "report" in complete_data:
                                        final_answer = complete_data["report"]
                                    # Extract sources if present
                                    if "sources" in complete_data:
                                        sources = complete_data["sources"]

                            # Handle errors
                            elif event_type == "error":
                                error_msg = data.get("data", {}).get("message", "Unknown error")
                                return ResearchResult(
                                    answer="",
                                    sources=[],
                                    confidence=0.0,
                                    search_time_ms=int((time.time() - start_time) * 1000),
                                    error=error_msg
                                )

                        except json.JSONDecodeError:
                            continue

                    search_time = int((time.time() - start_time) * 1000)

                    # If no structured answer, use accumulated report
                    if not final_answer:
                        final_answer = "No answer generated. Try a more specific query."

                    return ResearchResult(
                        answer=final_answer.strip(),
                        sources=sources,
                        confidence=0.8 if sources else 0.5,
                        search_time_ms=search_time
                    )

        except httpx.TimeoutException:
            return ResearchResult(
                answer="",
                sources=[],
                confidence=0.0,
                search_time_ms=int((time.time() - start_time) * 1000),
                error="Research request timed out"
            )
        except httpx.HTTPError as e:
            return ResearchResult(
                answer="",
                sources=[],
                confidence=0.0,
                search_time_ms=int((time.time() - start_time) * 1000),
                error=f"HTTP error: {str(e)}"
            )
        except Exception as e:
            return ResearchResult(
                answer="",
                sources=[],
                confidence=0.0,
                search_time_ms=int((time.time() - start_time) * 1000),
                error=f"Unexpected error: {str(e)}"
            )

    def health_check(self) -> bool:
        """Check if ii-researcher is available."""
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(f"{self.base_url}/")
                return response.status_code == 200
        except:
            return False


# Convenience function for simple usage
def research(query: str, max_steps: int = 5) -> Dict[str, Any]:
    """
    Quick research function - returns dict with answer.

    Usage:
        from lib.research_client import research
        result = research("What is the VA rating for tinnitus?")
        print(result["answer"])
    """
    client = ResearchClient()
    result = client.search(query, max_steps=max_steps)

    return {
        "answer": result.answer,
        "sources": result.sources,
        "confidence": result.confidence,
        "search_time_ms": result.search_time_ms,
        "error": result.error
    }


if __name__ == "__main__":
    # Self-test
    print("Research Client Self-Test")
    print("=" * 50)

    client = ResearchClient()

    # Health check
    print(f"ii-researcher available: {client.health_check()}")

    # Test search
    print("\nSearching: 'What is the capital of France?'")
    result = client.search("What is the capital of France?", max_steps=3)

    if result.error:
        print(f"Error: {result.error}")
    else:
        print(f"Answer: {result.answer[:200]}...")
        print(f"Sources: {len(result.sources)}")
        print(f"Confidence: {result.confidence}")
        print(f"Time: {result.search_time_ms}ms")

    print("=" * 50)
    print("FOR SEVEN GENERATIONS")
