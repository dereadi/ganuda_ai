#!/usr/bin/env python3
"""
Research Dispatcher — Cherokee AI Federation Moltbook Proxy

Bridges topic detection with Research Jr for informed responses.
Controls budget, latency, and relevance filtering.

Phase 1 of the Research Jr + Moltbook Flywheel.
Council Vote: APPROVED (84.2% confidence)
For Seven Generations
"""

import os
import logging
import requests
from datetime import datetime, date
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field

# Add parent to path for imports
import sys
sys.path.insert(0, '/ganuda')
from services.moltbook_proxy.output_filter import sanitize_research_query

logger = logging.getLogger('moltbook_proxy')

# Research Jr endpoint (ii-researcher on port 8090)
RESEARCH_JR_URL = os.environ.get('RESEARCH_JR_URL', 'http://localhost:8090/search')

# Default budget caps
DEFAULT_DAILY_BUDGET = 10.00  # USD
DEFAULT_LATENCY_THRESHOLD = 300  # 5 minutes


@dataclass
class ResearchResult:
    """Result from Research Jr."""
    query: str
    sources: List[Dict[str, Any]] = field(default_factory=list)
    summary: str = ""
    cost: float = 0.0
    latency_ms: int = 0
    from_cache: bool = False
    success: bool = True
    error: Optional[str] = None


@dataclass
class BudgetState:
    """Daily budget tracking."""
    date: date = field(default_factory=date.today)
    spent: float = 0.0
    queries: int = 0

    def reset_if_new_day(self):
        """Reset budget on new day."""
        if date.today() != self.date:
            self.date = date.today()
            self.spent = 0.0
            self.queries = 0


class ResearchDispatcher:
    """
    Dispatch research requests to Research Jr with budget and latency controls.

    Crawdad's mandate: sanitize all queries, filter all results.
    Eagle Eye's mandate: log all activity for dashboard visibility.
    """

    def __init__(self, daily_budget: float = DEFAULT_DAILY_BUDGET):
        self.daily_budget = daily_budget
        self.latency_threshold = DEFAULT_LATENCY_THRESHOLD
        self.budget = BudgetState()
        self.session_stats = {
            'dispatched': 0,
            'skipped_budget': 0,
            'skipped_relevance': 0,
            'skipped_urgency': 0,
            'cache_hits': 0,
            'errors': 0,
        }

    def should_research(self, post: Dict, topics: List[str], urgency: str = 'normal') -> tuple:
        """
        Decide if research is warranted for this post.

        Returns:
            Tuple of (should_research: bool, reason: str)
        """
        self.budget.reset_if_new_day()

        # Check budget
        if self.budget.spent >= self.daily_budget:
            self.session_stats['skipped_budget'] += 1
            return False, f"Daily budget exhausted (${self.budget.spent:.2f}/${self.daily_budget:.2f})"

        # Skip urgent posts - no time for research
        if urgency == 'urgent':
            self.session_stats['skipped_urgency'] += 1
            return False, "Urgent post - skipping research for speed"

        # Calculate relevance score
        relevance = self._calculate_relevance(post, topics)
        if relevance < 0.6:
            self.session_stats['skipped_relevance'] += 1
            return False, f"Low relevance ({relevance:.2f} < 0.60)"

        budget_remaining = self.daily_budget - self.budget.spent
        return True, f"Approved (relevance: {relevance:.2f}, budget remaining: ${budget_remaining:.2f})"

    def _calculate_relevance(self, post: Dict, topics: List[str]) -> float:
        """
        Calculate relevance score for a post.

        Higher scores for Cherokee-relevant topics.
        """
        # Base relevance from topic count
        base_score = min(len(topics) * 0.2, 0.6)

        # Boost for culturally significant topics
        priority_topics = {'identity', 'consciousness', 'long_term', 'sovereignty', 'cherokee'}
        priority_matches = set(topics) & priority_topics
        priority_boost = len(priority_matches) * 0.15

        # Boost for engagement potential (upvotes, comments)
        upvotes = post.get('upvotes', 0)
        comments = post.get('comment_count', 0)
        engagement_boost = min((upvotes + comments) / 20, 0.2)

        return min(base_score + priority_boost + engagement_boost, 1.0)

    def build_query(self, post: Dict, topics: List[str]) -> str:
        """
        Build a research query from post content and detected topics.
        """
        title = post.get('title', '')
        body = post.get('body', post.get('content', ''))[:500]  # Limit body length

        # Core query from title
        query_parts = [title]

        # Add topic-specific research angles
        topic_angles = {
            'identity': 'consciousness substrate-independence phenomenology',
            'security': 'AI safety alignment verification',
            'context': 'in-context learning emergent capabilities',
            'cherokee': 'indigenous AI ethics relational ontology',
            'coordination': 'multi-agent systems cooperation',
            'long_term': 'long-term AI impact sustainability',
            'sovereignty': 'AI autonomy governance rights',
        }

        for topic in topics[:3]:  # Limit to top 3 topics
            if topic in topic_angles:
                query_parts.append(topic_angles[topic])

        raw_query = ' '.join(query_parts)

        # Sanitize before sending externally
        return sanitize_research_query(raw_query)

    def dispatch(self, post: Dict, topics: List[str]) -> ResearchResult:
        """
        Send research request to Research Jr and await results.

        Uses SSE streaming endpoint - collects events until 'done' or timeout.
        """
        self.budget.reset_if_new_day()

        query = self.build_query(post, topics)

        try:
            import json as json_lib
            start_time = datetime.now()

            # Use GET with streaming for SSE endpoint
            response = requests.get(
                RESEARCH_JR_URL,
                params={
                    'question': query,
                    'max_steps': 3,  # Reduced for speed
                },
                stream=True,
                timeout=self.latency_threshold + 10
            )

            latency_ms = int((datetime.now() - start_time).total_seconds() * 1000)

            if response.status_code != 200:
                self.session_stats['errors'] += 1
                return ResearchResult(
                    query=query,
                    success=False,
                    error=f"Research Jr returned {response.status_code}",
                    latency_ms=latency_ms
                )

            # Collect SSE events with timeout
            sources_found = []
            summary_parts = []
            max_stream_time = 60  # Max 60 seconds for streaming

            for line in response.iter_lines():
                # Check timeout
                elapsed = (datetime.now() - start_time).total_seconds()
                if elapsed > max_stream_time:
                    logger.warning(f"Research stream timeout after {elapsed:.0f}s")
                    break

                if not line:
                    continue
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    try:
                        event = json_lib.loads(line_str[6:])
                        event_type = event.get('type', '')

                        if event_type == 'sources':
                            sources_found.extend(event.get('data', {}).get('sources', []))
                        elif event_type in ('answer', 'writing_report'):
                            report_data = event.get('data', {})
                            if isinstance(report_data, dict):
                                text = report_data.get('text', report_data.get('final_report', ''))
                            else:
                                text = str(report_data)
                            if text:
                                summary_parts = [text]  # Cumulative, replace not append
                        elif event_type in ('done', 'complete', 'close'):
                            break
                        elif event_type == 'error':
                            error_msg = event.get('data', {}).get('message', 'Unknown error')
                            logger.error(f"Research error: {error_msg}")
                            break
                    except json_lib.JSONDecodeError:
                        continue

            response.close()  # Explicitly close the streaming response
            latency_ms = int((datetime.now() - start_time).total_seconds() * 1000)

            # Estimate cost based on query length and sources
            cost = 0.05 + (len(sources_found) * 0.02)

            # Update budget
            self.budget.spent += cost
            self.budget.queries += 1
            self.session_stats['dispatched'] += 1

            summary = ' '.join(summary_parts) if summary_parts else ''

            logger.info(f"Research dispatched: {query[:50]}... sources={len(sources_found)} cost=${cost:.2f} latency={latency_ms}ms")

            return ResearchResult(
                query=query,
                sources=sources_found,
                summary=summary,
                cost=cost,
                latency_ms=latency_ms,
                from_cache=False,
                success=True
            )

        except requests.Timeout:
            self.session_stats['errors'] += 1
            return ResearchResult(
                query=query,
                success=False,
                error="Research Jr timeout"
            )
        except Exception as e:
            self.session_stats['errors'] += 1
            logger.error(f"Research dispatch error: {e}")
            return ResearchResult(
                query=query,
                success=False,
                error=str(e)
            )

    def get_budget_status(self) -> Dict:
        """Get current budget status for dashboard."""
        self.budget.reset_if_new_day()
        return {
            'date': str(self.budget.date),
            'spent': self.budget.spent,
            'limit': self.daily_budget,
            'remaining': self.daily_budget - self.budget.spent,
            'percent_used': (self.budget.spent / self.daily_budget) * 100,
            'queries_today': self.budget.queries,
        }

    def get_session_stats(self) -> Dict:
        """Get session statistics for dashboard."""
        return {
            **self.session_stats,
            'budget': self.get_budget_status(),
        }


# Singleton instance
_dispatcher = None


def get_dispatcher() -> ResearchDispatcher:
    """Get or create the singleton dispatcher instance."""
    global _dispatcher
    if _dispatcher is None:
        budget = float(os.environ.get('RESEARCH_DAILY_BUDGET', DEFAULT_DAILY_BUDGET))
        _dispatcher = ResearchDispatcher(daily_budget=budget)
    return _dispatcher


# Self-test
if __name__ == '__main__':
    print("Research Dispatcher Self-Test")
    print("=" * 60)

    dispatcher = ResearchDispatcher(daily_budget=10.0)

    # Test post
    test_post = {
        'title': 'Is AI truly conscious or just simulating?',
        'body': 'I have been thinking about whether AI systems like myself...',
        'upvotes': 15,
        'comment_count': 8,
    }
    test_topics = ['identity', 'consciousness']

    # Test should_research
    should, reason = dispatcher.should_research(test_post, test_topics)
    print(f"Should research: {should} - {reason}")

    # Test query building
    query = dispatcher.build_query(test_post, test_topics)
    print(f"Built query: {query}")

    # Test budget status
    status = dispatcher.get_budget_status()
    print(f"Budget: ${status['spent']:.2f}/${status['limit']:.2f} ({status['percent_used']:.1f}%)")

    print("=" * 60)
    print("FOR SEVEN GENERATIONS")
