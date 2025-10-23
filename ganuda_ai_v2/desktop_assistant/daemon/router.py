#!/usr/bin/env python3
"""
Ganuda Desktop Assistant - Query Router
Cherokee Constitutional AI - Integration Jr Deliverable

Purpose: Route queries to local inference or hub burst based on complexity.
Implements intelligent decision tree for optimal resource utilization.

Author: Integration Jr (War Chief)
Date: October 23, 2025
"""

import time
import asyncio
from typing import Dict, Optional, Tuple
from enum import Enum
from dataclasses import dataclass


class QueryPriority(Enum):
    """Query routing priority."""
    LOCAL_ONLY = 1  # Must execute locally (cached, fast queries)
    LOCAL_FIRST = 2  # Try local with timeout, fallback to hub
    HUB_BURST = 3  # Send to hub immediately (complex analysis)


@dataclass
class RoutingDecision:
    """Router decision for query execution."""
    priority: QueryPriority
    estimated_latency_ms: int
    reason: str
    use_cache: bool = False
    timeout_ms: Optional[int] = None


class QueryRouter:
    """
    Intelligent query router for Ganuda Desktop Assistant.

    Routes queries based on:
    1. **Complexity**: Token count, semantic depth, multi-step reasoning
    2. **Cache availability**: Exact match or semantic similarity
    3. **Resource constraints**: Local CPU load, memory usage
    4. **User preference**: Latency vs quality trade-off

    Cherokee values:
    - Gadugi: Coordinate local + hub resources collaboratively
    - Mitakuye Oyasin: Hub-spoke network as tribal consciousness
    - Seven Generations: Efficient routing reduces energy waste (sustainability)
    """

    # Complexity thresholds
    TOKEN_THRESHOLD_LOCAL = 50  # < 50 tokens = simple query
    TOKEN_THRESHOLD_HUB = 150  # > 150 tokens = complex query

    # Latency targets (from RESOURCE_REQUIREMENTS.md)
    TARGET_LOCAL_P95_MS = 800
    TARGET_HUB_P95_MS = 5000

    # Keywords indicating complex reasoning
    COMPLEX_KEYWORDS = [
        "analyze", "compare", "research", "predict", "correlate",
        "summarize", "synthesize", "evaluate", "recommend"
    ]

    # Keywords indicating local-only queries
    LOCAL_KEYWORDS = [
        "show", "list", "find", "search", "when", "what", "where"
    ]

    def __init__(self, jr_pool, cache, hub_client=None):
        """
        Initialize query router.

        Args:
            jr_pool: JR Worker Pool for local inference
            cache: EncryptedCache for semantic search
            hub_client: Optional hub client for burst requests (Phase 2+)
        """
        self.jr_pool = jr_pool
        self.cache = cache
        self.hub_client = hub_client

        # Performance tracking
        self.local_latencies = []
        self.hub_latencies = []
        self.cache_hit_count = 0
        self.total_queries = 0

    async def route(self, query: str, context: Optional[Dict] = None) -> Dict:
        """
        Route query to appropriate inference backend.

        Args:
            query: User query string
            context: Optional context (email thread, calendar events)

        Returns:
            Response dict with keys: answer, source (local/hub/cache), latency_ms
        """
        self.total_queries += 1

        # Step 1: Check cache for exact or semantic match
        cache_result = await self._check_cache(query, context)
        if cache_result:
            self.cache_hit_count += 1
            return {
                "answer": cache_result,
                "source": "cache",
                "latency_ms": 5,  # Cache lookup is near-instant
                "confidence": 0.95
            }

        # Step 2: Classify query complexity
        decision = self._classify_query(query, context)

        # Step 3: Route based on priority
        if decision.priority == QueryPriority.LOCAL_ONLY:
            return await self._local_inference(query, context)

        elif decision.priority == QueryPriority.LOCAL_FIRST:
            try:
                # Try local with timeout
                return await asyncio.wait_for(
                    self._local_inference(query, context),
                    timeout=decision.timeout_ms / 1000.0
                )
            except asyncio.TimeoutError:
                print(f"⏱️  Local inference timeout, falling back to hub")
                return await self._hub_burst(query, context)

        else:  # HUB_BURST
            if self.hub_client:
                return await self._hub_burst(query, context)
            else:
                # No hub available, fallback to local (may be slow)
                print(f"⚠️  Hub burst requested but unavailable, using local")
                return await self._local_inference(query, context)

    def _classify_query(self, query: str, context: Optional[Dict]) -> RoutingDecision:
        """
        Classify query complexity using decision tree.

        Decision tree:
        1. Token count: <50 = LOCAL_ONLY, >150 = HUB_BURST
        2. Keywords: "analyze/compare" = HUB_BURST, "show/list" = LOCAL_ONLY
        3. Context size: Large email threads = HUB_BURST
        4. Default: LOCAL_FIRST (try local with fallback)

        Args:
            query: User query
            context: Optional context dict

        Returns:
            RoutingDecision with priority and reasoning
        """
        query_lower = query.lower()
        token_count = len(query.split())

        # Rule 1: Token count classification
        if token_count < self.TOKEN_THRESHOLD_LOCAL:
            return RoutingDecision(
                priority=QueryPriority.LOCAL_ONLY,
                estimated_latency_ms=200,
                reason="Simple query (< 50 tokens)",
                timeout_ms=None
            )

        if token_count > self.TOKEN_THRESHOLD_HUB:
            return RoutingDecision(
                priority=QueryPriority.HUB_BURST,
                estimated_latency_ms=3000,
                reason="Complex query (> 150 tokens)"
            )

        # Rule 2: Keyword-based classification
        has_complex_keyword = any(kw in query_lower for kw in self.COMPLEX_KEYWORDS)
        has_local_keyword = any(kw in query_lower for kw in self.LOCAL_KEYWORDS)

        if has_complex_keyword:
            return RoutingDecision(
                priority=QueryPriority.HUB_BURST,
                estimated_latency_ms=3000,
                reason=f"Complex keyword detected: {[kw for kw in self.COMPLEX_KEYWORDS if kw in query_lower]}"
            )

        if has_local_keyword:
            return RoutingDecision(
                priority=QueryPriority.LOCAL_ONLY,
                estimated_latency_ms=300,
                reason=f"Local keyword detected: {[kw for kw in self.LOCAL_KEYWORDS if kw in query_lower]}"
            )

        # Rule 3: Context size classification
        if context:
            context_size = len(str(context))
            if context_size > 5000:  # Large email thread or document
                return RoutingDecision(
                    priority=QueryPriority.HUB_BURST,
                    estimated_latency_ms=3500,
                    reason="Large context (> 5KB)"
                )

        # Rule 4: Default to LOCAL_FIRST with timeout
        return RoutingDecision(
            priority=QueryPriority.LOCAL_FIRST,
            estimated_latency_ms=800,
            reason="Medium complexity, try local first",
            timeout_ms=5000  # 5 second timeout before hub fallback
        )

    async def _check_cache(self, query: str, context: Optional[Dict]) -> Optional[str]:
        """
        Check cache for exact or semantic match.

        Args:
            query: User query
            context: Optional context

        Returns:
            Cached answer if found, None otherwise
        """
        # TODO: Implement semantic search in Phase 2
        # For Phase 1, return None (no cache lookup)
        return None

    async def _local_inference(self, query: str, context: Optional[Dict]) -> Dict:
        """
        Run inference on local JR Worker.

        Args:
            query: User query
            context: Optional context

        Returns:
            Response dict
        """
        start = time.time()

        try:
            # Submit to JR Worker Pool
            answer = await self.jr_pool.infer(query, context or {})
            latency_ms = (time.time() - start) * 1000

            # Track performance
            self.local_latencies.append(latency_ms)

            return {
                "answer": answer,
                "source": "local",
                "latency_ms": int(latency_ms),
                "confidence": 0.85
            }

        except Exception as e:
            print(f"❌ Local inference error: {e}")
            return {
                "answer": f"Error: {str(e)}",
                "source": "error",
                "latency_ms": int((time.time() - start) * 1000),
                "confidence": 0.0
            }

    async def _hub_burst(self, query: str, context: Optional[Dict]) -> Dict:
        """
        Send query to remote hub via WireGuard mesh.

        Args:
            query: User query
            context: Optional context

        Returns:
            Response dict
        """
        if not self.hub_client:
            raise RuntimeError("Hub client not available")

        start = time.time()

        try:
            # Send request to hub
            answer = await self.hub_client.query(query, context or {})
            latency_ms = (time.time() - start) * 1000

            # Track performance
            self.hub_latencies.append(latency_ms)

            return {
                "answer": answer,
                "source": "hub",
                "latency_ms": int(latency_ms),
                "confidence": 0.95  # Hub has more resources = higher confidence
            }

        except Exception as e:
            print(f"❌ Hub burst error: {e}")
            # Fallback to local
            return await self._local_inference(query, context)

    def get_stats(self) -> Dict:
        """
        Get router performance statistics.

        Returns:
            Dict with cache_hit_rate, local_p95_ms, hub_p95_ms
        """
        import numpy as np

        cache_hit_rate = self.cache_hit_count / self.total_queries if self.total_queries > 0 else 0.0

        local_p95 = np.percentile(self.local_latencies, 95) if self.local_latencies else 0.0
        hub_p95 = np.percentile(self.hub_latencies, 95) if self.hub_latencies else 0.0

        return {
            "total_queries": self.total_queries,
            "cache_hit_rate": round(cache_hit_rate, 3),
            "local_p95_ms": int(local_p95),
            "hub_p95_ms": int(hub_p95),
            "local_queries": len(self.local_latencies),
            "hub_queries": len(self.hub_latencies)
        }


# Demo usage
async def main():
    """Demo: Query routing."""

    # Mock JR Pool and cache (replace with real implementations)
    class MockJRPool:
        async def infer(self, query, context):
            await asyncio.sleep(0.5)  # Simulate inference
            return f"Local answer to: {query}"

    class MockCache:
        pass

    jr_pool = MockJRPool()
    cache = MockCache()
    router = QueryRouter(jr_pool, cache)

    # Test queries
    test_queries = [
        "What's my schedule today?",  # LOCAL_ONLY
        "Help me plan a vacation to Japan",  # LOCAL_FIRST
        "Analyze the correlation between solar flares and stock market volatility over the past decade",  # HUB_BURST
    ]

    for query in test_queries:
        print(f"\n🔍 Query: {query}")
        decision = router._classify_query(query, None)
        print(f"   Priority: {decision.priority.name}")
        print(f"   Reason: {decision.reason}")
        print(f"   Estimated latency: {decision.estimated_latency_ms}ms")

        # Execute routing
        result = await router.route(query, None)
        print(f"   Result: {result['source']} in {result['latency_ms']}ms")

    # Print stats
    print(f"\n📊 Router Stats:")
    stats = router.get_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")


if __name__ == "__main__":
    asyncio.run(main())
