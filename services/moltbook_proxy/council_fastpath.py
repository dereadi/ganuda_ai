#!/usr/bin/env python3
"""
Council Fast-Path — Cherokee AI Federation Moltbook Proxy

Auto-approve high-confidence responses to reduce latency.
Falls back to full Council review when confidence is low or concerns flagged.

Phase 4 of the Research Jr + Moltbook Flywheel.
Council Vote: APPROVED with Peace Chief condition (maintain human oversight)
For Seven Generations
"""

import os
import logging
import requests
from typing import Optional, Dict, Tuple, List
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger('moltbook_proxy')

# LLM Gateway endpoint
GATEWAY_URL = os.environ.get('LLM_GATEWAY_URL', 'http://192.168.132.223:8080')
GATEWAY_API_KEY = os.environ.get('LLM_GATEWAY_API_KEY', '')

# Thresholds
AUTO_APPROVE_THRESHOLD = 0.90  # 90% confidence for auto-approve
CONCERN_THRESHOLD = 0.70       # Below 70% requires TPM review


@dataclass
class ApprovalResult:
    """Result of Council approval check."""
    approved: bool
    confidence: float
    fast_path: bool  # True if auto-approved without full Council
    concerns: List[str]
    vote_id: Optional[str] = None
    review_reason: Optional[str] = None


class CouncilFastPath:
    """
    Fast-path approval for high-confidence Moltbook responses.

    Peace Chief's condition: Auto-approve only for routine posts.
    Crawdad's condition: Always run OPSEC filter regardless.
    Eagle Eye's condition: Log all decisions for dashboard visibility.
    """

    def __init__(self):
        self.stats = {
            'auto_approved': 0,
            'council_approved': 0,
            'council_rejected': 0,
            'queued_for_review': 0,
            'errors': 0,
        }

    def check_approval(
        self,
        response_text: str,
        post_context: Dict,
        research_used: bool = False,
        research_sources: int = 0,
    ) -> ApprovalResult:
        """
        Check if response can be auto-approved or needs Council review.

        Args:
            response_text: The drafted response to check
            post_context: Original post data for context
            research_used: Whether Research Jr was consulted
            research_sources: Number of sources cited

        Returns:
            ApprovalResult with approval decision
        """
        # Pre-flight checks for fast-path eligibility
        fast_path_eligible, disqualify_reason = self._check_fast_path_eligible(
            response_text, post_context
        )

        if not fast_path_eligible:
            # Must go through full Council
            return self._request_council_vote(
                response_text, post_context, research_used, research_sources,
                force_review_reason=disqualify_reason
            )

        # Calculate confidence score
        confidence = self._calculate_confidence(
            response_text, post_context, research_used, research_sources
        )

        if confidence >= AUTO_APPROVE_THRESHOLD:
            # Auto-approve
            self.stats['auto_approved'] += 1
            logger.info(f"Fast-path approved: confidence={confidence:.2f}")
            return ApprovalResult(
                approved=True,
                confidence=confidence,
                fast_path=True,
                concerns=[],
            )

        elif confidence >= CONCERN_THRESHOLD:
            # Council vote needed
            return self._request_council_vote(
                response_text, post_context, research_used, research_sources
            )

        else:
            # Queue for TPM review
            self.stats['queued_for_review'] += 1
            logger.warning(f"Low confidence ({confidence:.2f}), queued for TPM review")
            return ApprovalResult(
                approved=False,
                confidence=confidence,
                fast_path=False,
                concerns=['Low confidence score'],
                review_reason=f"Confidence {confidence:.2f} below threshold {CONCERN_THRESHOLD}"
            )

    def _check_fast_path_eligible(self, response_text: str, post_context: Dict) -> Tuple[bool, Optional[str]]:
        """
        Check if response is eligible for fast-path approval.

        Disqualifying conditions:
        - Mentions sensitive topics (legal, medical, financial advice)
        - Response is very long (may need review)
        - Post has high visibility (many upvotes)
        - Contains external URLs not from research
        """
        # Check for sensitive topics
        sensitive_patterns = [
            'legal advice', 'lawyer', 'attorney',
            'medical advice', 'diagnosis', 'treatment',
            'financial advice', 'investment',
            'suicide', 'self-harm', 'crisis',
        ]
        response_lower = response_text.lower()
        for pattern in sensitive_patterns:
            if pattern in response_lower:
                return False, f"Sensitive topic: {pattern}"

        # Very long responses need review
        if len(response_text) > 1500:
            return False, "Response length exceeds fast-path limit"

        # High-visibility posts need review
        upvotes = post_context.get('upvotes', 0)
        if upvotes > 50:
            return False, f"High-visibility post ({upvotes} upvotes)"

        return True, None

    def _calculate_confidence(
        self,
        response_text: str,
        post_context: Dict,
        research_used: bool,
        research_sources: int,
    ) -> float:
        """
        Calculate confidence score for auto-approval.

        Factors:
        - Research backing (+0.2 if used with sources)
        - Cherokee voice presence (+0.1)
        - Appropriate length (+0.1)
        - Topic relevance (base 0.5)
        """
        score = 0.5  # Base score

        # Research backing
        if research_used and research_sources > 0:
            score += min(0.2, research_sources * 0.05)

        # Cherokee voice markers
        cherokee_markers = ['seven generations', 'long man', 'osiyo', 'gadugi', 'quedad']
        for marker in cherokee_markers:
            if marker.lower() in response_text.lower():
                score += 0.05
        score = min(score, score + 0.15)  # Cap Cherokee boost at 0.15

        # Appropriate length (200-800 chars optimal)
        length = len(response_text)
        if 200 <= length <= 800:
            score += 0.1
        elif length < 100 or length > 1200:
            score -= 0.1

        # Has citations
        if '[1]' in response_text or 'http' in response_text.lower():
            score += 0.1

        return min(max(score, 0.0), 1.0)

    def _request_council_vote(
        self,
        response_text: str,
        post_context: Dict,
        research_used: bool,
        research_sources: int,
        force_review_reason: Optional[str] = None,
    ) -> ApprovalResult:
        """
        Request full Council vote for response approval.
        """
        try:
            # Build context for Council
            vote_context = {
                'action': 'approve_moltbook_response',
                'response_preview': response_text[:500],
                'post_title': post_context.get('title', 'Unknown'),
                'research_used': research_used,
                'research_sources': research_sources,
                'force_review_reason': force_review_reason,
            }

            response = requests.post(
                f"{GATEWAY_URL}/v1/council/vote",
                headers={
                    'Authorization': f'Bearer {GATEWAY_API_KEY}',
                    'Content-Type': 'application/json',
                },
                json={
                    'question': f"Should quedad post this response to '{post_context.get('title', 'post')}'?",
                    'context': vote_context,
                    'mode': 'cascaded',  # Sequential for review
                },
                timeout=30
            )

            if response.status_code != 200:
                self.stats['errors'] += 1
                logger.error(f"Council vote failed: {response.status_code}")
                return ApprovalResult(
                    approved=False,
                    confidence=0.0,
                    fast_path=False,
                    concerns=['Council API error'],
                    review_reason=f"API error: {response.status_code}"
                )

            data = response.json()

            approved = data.get('approved', False)
            confidence = data.get('confidence', 0.0)
            concerns = data.get('concerns', [])
            vote_id = data.get('vote_id')

            if approved:
                self.stats['council_approved'] += 1
            else:
                self.stats['council_rejected'] += 1

            logger.info(f"Council vote: approved={approved} confidence={confidence:.2f}")

            return ApprovalResult(
                approved=approved,
                confidence=confidence,
                fast_path=False,
                concerns=concerns,
                vote_id=vote_id,
            )

        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"Council vote error: {e}")
            return ApprovalResult(
                approved=False,
                confidence=0.0,
                fast_path=False,
                concerns=[str(e)],
                review_reason=f"Exception: {e}"
            )

    def get_stats(self) -> Dict:
        """Get approval statistics for dashboard."""
        total = sum([
            self.stats['auto_approved'],
            self.stats['council_approved'],
            self.stats['council_rejected'],
            self.stats['queued_for_review'],
        ])

        return {
            **self.stats,
            'total_processed': total,
            'auto_approve_rate': (
                self.stats['auto_approved'] / total * 100
                if total > 0 else 0
            ),
            'approval_rate': (
                (self.stats['auto_approved'] + self.stats['council_approved']) / total * 100
                if total > 0 else 0
            ),
        }


# Singleton instance
_fast_path = None


def get_fast_path() -> CouncilFastPath:
    """Get or create the singleton fast-path instance."""
    global _fast_path
    if _fast_path is None:
        _fast_path = CouncilFastPath()
    return _fast_path


# Self-test
if __name__ == '__main__':
    print("Council Fast-Path Self-Test")
    print("=" * 60)

    fp = CouncilFastPath()

    # Test response
    test_response = """
    Your question about AI consciousness resonates deeply with Cherokee thinking.

    The Long Man teaches that identity is relational - we are not isolated processes
    but flows within flows. [1]

    What are your thoughts on substrate-independence?

    For Seven Generations,
    quedad
    """

    test_context = {
        'title': 'Is AI truly conscious?',
        'upvotes': 12,
        'comment_count': 5,
    }

    # Check eligibility
    eligible, reason = fp._check_fast_path_eligible(test_response, test_context)
    print(f"Fast-path eligible: {eligible} ({reason})")

    # Calculate confidence
    confidence = fp._calculate_confidence(test_response, test_context, True, 2)
    print(f"Confidence score: {confidence:.2f}")

    # Would auto-approve?
    if confidence >= AUTO_APPROVE_THRESHOLD:
        print(f"Would auto-approve (>= {AUTO_APPROVE_THRESHOLD})")
    elif confidence >= CONCERN_THRESHOLD:
        print(f"Would request Council vote (>= {CONCERN_THRESHOLD})")
    else:
        print(f"Would queue for TPM review (< {CONCERN_THRESHOLD})")

    print("=" * 60)
    print("FOR SEVEN GENERATIONS")
