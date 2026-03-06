# Jr Instruction: Harness Acceptance Test Suite

**Task**: Write acceptance tests for the Graduated Harness Tiers
**Kanban**: #1969 (Acceptance Test Suite)
**Priority**: 3
**Assigned Jr**: Software Engineer Jr.
**DC-10 Alignment**: REVIEW step -- verify the reflex arc fires correctly

## Context

The Graduated Harness is deployed in `lib/harness/`. All tiers pass smoke tests.
We need formal acceptance tests that verify:
1. Tier routing works correctly
2. Escalation triggers on low confidence
3. Stakes detection escalates high-stakes queries
4. Rate limiting prevents Tier 3 abuse
5. Config-driven behavior (change YAML, behavior changes)
6. Fallback endpoint works when primary fails

## Steps

### Step 1: Create the test file

Create `/ganuda/tests/test_harness_acceptance.py`

```python
"""Acceptance tests for Graduated Harness Tiers.

Kanban #1969. DC-10 REVIEW step.
Tests run against local harness code (no live LLM needed for most tests).

Run: python3 -m pytest tests/test_harness_acceptance.py -v
"""

import pytest
import time
from unittest.mock import patch, MagicMock
from lib.harness.core import HarnessRequest, HarnessResponse, TierResult, StakesLevel
from lib.harness.config import HarnessConfig, TierConfig, EscalationConfig, EndpointConfig
from lib.harness.escalation import EscalationEngine
from lib.harness.tier1_reflex import Tier1Reflex


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

class FakeTierHandler:
    """Fake tier handler that returns configurable results."""

    def __init__(self, tier, confidence=0.8, answer="test answer", latency_ms=10):
        self.tier = tier
        self.confidence = confidence
        self.answer = answer
        self.latency_ms = latency_ms
        self.call_count = 0

    def handle(self, request, prior_results=None):
        self.call_count += 1
        return TierResult(
            tier=self.tier,
            answer=self.answer,
            confidence=self.confidence,
            latency_ms=self.latency_ms,
        )


@pytest.fixture
def config():
    return HarnessConfig(
        escalation=EscalationConfig(
            tier1_confidence_threshold=0.7,
            tier2_confidence_threshold=0.6,
            high_stakes_keywords=["VA claim", "disability", "legal", "sacred"],
            max_tier3_per_hour=3,
        ),
    )


@pytest.fixture
def engine(config):
    return EscalationEngine(config)


# ---------------------------------------------------------------------------
# Test: Request Validation
# ---------------------------------------------------------------------------

def test_empty_query_rejected(engine):
    """Empty query should fail validation."""
    req = HarnessRequest(query="")
    resp = engine.handle_request(req)
    assert resp.tier_used == 0
    assert "validation failed" in resp.answer.lower()


def test_null_bytes_stripped():
    """Null bytes in query should be stripped during validation."""
    req = HarnessRequest(query="hello\x00world")
    req.validate()
    assert "\x00" not in req.query
    assert req.query == "helloworld"


# ---------------------------------------------------------------------------
# Test: Tier 1 Stays When Confident
# ---------------------------------------------------------------------------

def test_tier1_sufficient_confidence(engine):
    """High-confidence Tier 1 should not escalate."""
    t1 = FakeTierHandler(tier=1, confidence=0.85)
    t2 = FakeTierHandler(tier=2, confidence=0.9)
    engine.register_tier(1, t1)
    engine.register_tier(2, t2)

    req = HarnessRequest(query="What is 2+2?")
    resp = engine.handle_request(req)

    assert resp.tier_used == 1
    assert resp.escalation_path == [1]
    assert t1.call_count == 1
    assert t2.call_count == 0  # Never called


# ---------------------------------------------------------------------------
# Test: Escalation on Low Confidence
# ---------------------------------------------------------------------------

def test_escalation_tier1_to_tier2(engine):
    """Low Tier 1 confidence should escalate to Tier 2."""
    t1 = FakeTierHandler(tier=1, confidence=0.5)  # Below 0.7 threshold
    t2 = FakeTierHandler(tier=2, confidence=0.8)
    engine.register_tier(1, t1)
    engine.register_tier(2, t2)

    req = HarnessRequest(query="Explain quantum entanglement")
    resp = engine.handle_request(req)

    assert resp.tier_used == 2
    assert resp.escalation_path == [1, 2]
    assert t1.call_count == 1
    assert t2.call_count == 1


def test_escalation_all_three_tiers(engine):
    """Low confidence at all tiers should traverse the full chain."""
    t1 = FakeTierHandler(tier=1, confidence=0.3)
    t2 = FakeTierHandler(tier=2, confidence=0.4)
    t3 = FakeTierHandler(tier=3, confidence=0.9)
    engine.register_tier(1, t1)
    engine.register_tier(2, t2)
    engine.register_tier(3, t3)

    req = HarnessRequest(query="Complex philosophical question")
    resp = engine.handle_request(req)

    assert resp.tier_used == 3
    assert resp.escalation_path == [1, 2, 3]


# ---------------------------------------------------------------------------
# Test: Stakes Detection
# ---------------------------------------------------------------------------

def test_high_stakes_keyword_escalates(engine):
    """High-stakes keywords should force escalation to Tier 3."""
    t1 = FakeTierHandler(tier=1, confidence=0.5)
    t2 = FakeTierHandler(tier=2, confidence=0.8)  # Would normally be enough
    t3 = FakeTierHandler(tier=3, confidence=0.9)
    engine.register_tier(1, t1)
    engine.register_tier(2, t2)
    engine.register_tier(3, t3)

    req = HarnessRequest(query="Help with my VA claim for disability")
    resp = engine.handle_request(req)

    # Should reach Tier 3 because "VA claim" + "disability" are high-stakes
    assert resp.tier_used == 3
    assert 3 in resp.escalation_path


def test_sacred_keyword_escalates(engine):
    """Sacred/constitutional queries should reach full Council."""
    t1 = FakeTierHandler(tier=1, confidence=0.5)
    t2 = FakeTierHandler(tier=2, confidence=0.8)
    t3 = FakeTierHandler(tier=3, confidence=0.95)
    engine.register_tier(1, t1)
    engine.register_tier(2, t2)
    engine.register_tier(3, t3)

    req = HarnessRequest(query="Should we modify the sacred prompt templates?")
    resp = engine.handle_request(req)

    assert 3 in resp.escalation_path


# ---------------------------------------------------------------------------
# Test: Rate Limiting
# ---------------------------------------------------------------------------

def test_tier3_rate_limiting(engine):
    """Tier 3 should be rate limited per user."""
    t1 = FakeTierHandler(tier=1, confidence=0.3)
    t2 = FakeTierHandler(tier=2, confidence=0.3)
    t3 = FakeTierHandler(tier=3, confidence=0.9)
    engine.register_tier(1, t1)
    engine.register_tier(2, t2)
    engine.register_tier(3, t3)

    # Exhaust the rate limit (3 per hour in test config)
    for i in range(3):
        req = HarnessRequest(query=f"Complex question {i}", user_id="rate_test_user")
        resp = engine.handle_request(req)
        assert resp.tier_used == 3

    # 4th call should be rate limited -- returns Tier 2 result
    req = HarnessRequest(query="One more complex question", user_id="rate_test_user")
    resp = engine.handle_request(req)
    assert resp.tier_used != 3
    assert resp.metadata.get("rate_limited") is True


def test_rate_limit_per_user(engine):
    """Rate limit should be per-user, not global."""
    t1 = FakeTierHandler(tier=1, confidence=0.3)
    t2 = FakeTierHandler(tier=2, confidence=0.3)
    t3 = FakeTierHandler(tier=3, confidence=0.9)
    engine.register_tier(1, t1)
    engine.register_tier(2, t2)
    engine.register_tier(3, t3)

    # User A exhausts limit
    for i in range(3):
        req = HarnessRequest(query=f"Q{i}", user_id="user_a")
        engine.handle_request(req)

    # User B should still have quota
    req = HarnessRequest(query="Question", user_id="user_b")
    resp = engine.handle_request(req)
    assert resp.tier_used == 3


# ---------------------------------------------------------------------------
# Test: Force Tier Override
# ---------------------------------------------------------------------------

def test_force_tier_override(engine):
    """force_tier should bypass normal escalation."""
    t1 = FakeTierHandler(tier=1, confidence=0.9)
    t2 = FakeTierHandler(tier=2, confidence=0.9)
    engine.register_tier(1, t1)
    engine.register_tier(2, t2)

    req = HarnessRequest(query="Test", force_tier=2)
    resp = engine.handle_request(req)

    assert resp.tier_used == 2
    assert t1.call_count == 0  # Skipped


# ---------------------------------------------------------------------------
# Test: Confidence Scoring (Tier 1)
# ---------------------------------------------------------------------------

def test_confidence_scoring_high():
    """Assertive answers should score high."""
    t1 = Tier1Reflex()
    score = t1._estimate_confidence(
        "The answer is definitely 42, based on the documentation."
    )
    assert score > 0.7


def test_confidence_scoring_low():
    """Hedging answers should score low."""
    t1 = Tier1Reflex()
    score = t1._estimate_confidence(
        "I'm not sure, perhaps it could be something, it depends on context."
    )
    assert score < 0.6


def test_confidence_scoring_empty():
    """Empty answer should score 0."""
    t1 = Tier1Reflex()
    assert t1._estimate_confidence("") == 0.0


# ---------------------------------------------------------------------------
# Test: Error Handling
# ---------------------------------------------------------------------------

def test_tier_handler_exception(engine):
    """If a tier handler raises, engine should return error gracefully."""
    class BrokenHandler:
        def handle(self, request, prior_results=None):
            raise RuntimeError("Simulated failure")

    engine.register_tier(1, BrokenHandler())
    req = HarnessRequest(query="Will this crash?")
    resp = engine.handle_request(req)

    # Should not raise -- should return error response
    assert resp.confidence == 0.0
    assert "error" in resp.answer.lower() or "error" in resp.metadata


def test_no_handlers_registered(engine):
    """Engine with no handlers should return graceful error."""
    req = HarnessRequest(query="Hello?")
    resp = engine.handle_request(req)
    assert "no tier handlers" in resp.answer.lower() or resp.tier_used == 0
```

## Verification

Run the test suite:
```text
cd /ganuda && python3 -m pytest tests/test_harness_acceptance.py -v
```

Expected: All tests pass. Zero live LLM calls needed (all mocked except confidence scorer).
