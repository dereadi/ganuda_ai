"""
Harness Core -- Request/Response models and tier result types.

These dataclasses are the shared language across all three tiers.
Every tier returns a HarnessResponse. The escalation engine reads
confidence and stakes to decide whether to promote to the next tier.

Design note: dataclasses over Pydantic for zero external dependencies.
The harness core must be importable on any node without pip install.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Any
import time
import uuid


class StakesLevel(str, Enum):
    """Stakes classification for escalation decisions.

    Coyote rule: humans underestimate stakes.
    When in doubt, escalate. Cost of over-escalation < cost of under-escalation.
    """
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class HarnessRequest:
    """Unified request object for all harness tiers.

    Attributes:
        query: The user's question or instruction.
        context: Arbitrary context dict (calendar data, email metadata, etc.).
        user_id: For personalization and rate limiting (Deer requirement).
        session_id: For conversation continuity across requests.
        request_id: Unique ID for tracing. Auto-generated if not provided.
        force_tier: Only for testing -- production NEVER sets this.
        metadata: Additional metadata for routing decisions.
    """
    query: str
    context: Dict[str, Any] = field(default_factory=dict)
    user_id: str = "default"
    session_id: str = ""
    request_id: str = ""
    force_tier: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.request_id:
            self.request_id = uuid.uuid4().hex[:16]
        if not self.session_id:
            self.session_id = uuid.uuid4().hex[:16]

    def validate(self) -> List[str]:
        """Validate request fields. Returns list of error messages (empty = valid).

        Crawdad requirement: input validation at every tier boundary.
        """
        errors = []
        if not self.query or not isinstance(self.query, str):
            errors.append("query must be a non-empty string")
        if len(self.query) > 50000:
            errors.append("query exceeds maximum length of 50000 characters")
        if self.force_tier is not None and self.force_tier not in (1, 2, 3):
            errors.append("force_tier must be 1, 2, or 3")
        if not isinstance(self.context, dict):
            errors.append("context must be a dict")
        # Sanitize: strip null bytes from query (injection prevention)
        if isinstance(self.query, str):
            self.query = self.query.replace('\x00', '')
        return errors


@dataclass
class TierResult:
    """Result from a single tier's processing.

    Used internally by the escalation engine to track per-tier outcomes.
    The final HarnessResponse is built from the last tier's result plus
    the full escalation path.
    """
    tier: int
    answer: str
    confidence: float
    latency_ms: float
    stakes: StakesLevel = StakesLevel.LOW
    diversity_score: Optional[float] = None
    council_vote_id: Optional[str] = None
    specialist_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HarnessResponse:
    """Unified response from the harness.

    Every request gets exactly one HarnessResponse, regardless of how many
    tiers it passed through. The escalation_path shows the journey.

    Attributes:
        answer: The final answer text.
        tier_used: The tier that produced the final answer (1, 2, or 3).
        confidence: Confidence score from the final tier (0.0 - 1.0).
        escalation_path: List of tiers traversed, e.g. [1, 2] means T1 escalated to T2.
        latency_ms: Total wall-clock latency across all tiers.
        diversity_score: Specialist diversity metric (Tier 2+ only, Elisi requirement).
        council_vote_id: Council vote reference (Tier 3 only).
        request_id: Echoed from the request for tracing.
        metadata: Tier-specific metadata and escalation reasoning.
    """
    answer: str
    tier_used: int
    confidence: float
    escalation_path: List[int] = field(default_factory=list)
    latency_ms: float = 0.0
    diversity_score: Optional[float] = None
    council_vote_id: Optional[str] = None
    request_id: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict for JSON responses."""
        return {
            "answer": self.answer,
            "tier_used": self.tier_used,
            "confidence": self.confidence,
            "escalation_path": self.escalation_path,
            "latency_ms": round(self.latency_ms, 2),
            "diversity_score": self.diversity_score,
            "council_vote_id": self.council_vote_id,
            "request_id": self.request_id,
            "metadata": self.metadata,
        }