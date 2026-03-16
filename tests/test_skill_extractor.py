#!/usr/bin/env python3
"""
Tests for Skill Extractor (JR-SKILLRL-03).

Tests extraction, sanitization, duplicate detection, circuit breaker,
and council submission — all with mocked DB and model dispatch.
"""

import json
import sys
import time
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, "/ganuda")

from lib.skill_descriptor import SkillDescriptor
from lib.skill_extractor import (
    CircuitBreaker,
    check_duplicate,
    extract_skill,
    get_circuit_breaker,
    sanitize_skill,
    submit_for_verification,
    _strip_infra_terms,
    _check_never_send,
)


# ── Fixtures ──

def _make_task(**overrides):
    """Build a sample completed Jr task dict."""
    task = {
        "task_id": 42,
        "title": "Implement health check endpoint",
        "description": "Add /health endpoint that returns service status and uptime.",
        "acceptance_criteria": "GET /health returns 200 with JSON body containing status and uptime_seconds.",
        "files_modified": "api/routes.py, api/health.py",
        "steps_summary": "1. Created health.py module. 2. Added route in routes.py. 3. Wrote tests.",
    }
    task.update(overrides)
    return task


def _make_skill(**overrides):
    """Build a sample SkillDescriptor."""
    defaults = {
        "name": "Health Check Pattern",
        "intent": "Expose service liveness via a lightweight HTTP endpoint",
        "method": "Create a /health route returning JSON with status and uptime",
        "difficulty": 4,
        "tool_hints": ["fastapi", "pytest"],
        "domain": "ops",
        "source_task_id": 42,
    }
    defaults.update(overrides)
    return SkillDescriptor(**defaults)


def _mock_dispatcher(response_json: dict, ok: bool = True):
    """Create a mock dispatcher that returns a canned response."""
    dispatcher = MagicMock()
    dispatcher.dispatch.return_value = {
        "ok": ok,
        "text": json.dumps(response_json),
        "node": "redfin_vllm",
        "latency_ms": 150,
    }
    return dispatcher


# ── Test: Sanitization strips node names ──

def test_sanitize_strips_node_names():
    """Infrastructure node names are replaced with generic placeholders."""
    skill = _make_skill(
        intent="Deploy the service on redfin using vLLM",
        method="SSH into bluefin, copy files from greenfin, restart on owlfin",
    )
    result = sanitize_skill(skill)
    assert result is not None
    assert "redfin" not in result.intent
    assert "bluefin" not in result.method
    assert "greenfin" not in result.method
    assert "owlfin" not in result.method
    # Verify placeholders are present
    assert "primary GPU node" in result.intent
    assert "database node" in result.method
    assert "bridge node" in result.method
    assert "DMZ web node" in result.method


# ── Test: Sanitization strips IP addresses ──

def test_sanitize_strips_ip_addresses():
    """LAN, WireGuard, and Tailscale IPs are replaced with placeholders."""
    skill = _make_skill(
        intent="Connect to 192.168.132.222 for database access",
        method="Use 10.100.0.2 for WireGuard, fallback to 100.103.27.106 via Tailscale",
    )
    result = sanitize_skill(skill)
    assert result is not None
    assert "192.168.132.222" not in result.intent
    assert "10.100.0.2" not in result.method
    assert "100.103.27.106" not in result.method
    assert "<LAN_IP>" in result.intent
    assert "<WG_IP>" in result.method
    assert "<TS_IP>" in result.method


# ── Test: NEVER_SEND violation returns None ──

def test_never_send_rejects_skill():
    """Skills containing NEVER_SEND patterns (passwords, secrets) are rejected entirely."""
    skill = _make_skill(
        intent="Configure database with password = s3cret123",
        method="Set DB credentials in the config",
    )
    result = sanitize_skill(skill)
    assert result is None


def test_never_send_rejects_secrets_env():
    """Skills referencing secrets.env are rejected."""
    skill = _make_skill(
        method="Read credentials from secrets.env and inject into runtime",
    )
    result = sanitize_skill(skill)
    assert result is None


# ── Test: Duplicate detection works ──

def test_check_duplicate_found():
    """Duplicate detection returns True when skill_id exists in DB."""
    skill = _make_skill()
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = (1,)  # Row exists

    assert check_duplicate(skill, mock_conn) is True
    mock_cursor.execute.assert_called_once()
    mock_cursor.close.assert_called_once()


def test_check_duplicate_not_found():
    """Duplicate detection returns False when skill_id is new."""
    skill = _make_skill()
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = None

    assert check_duplicate(skill, mock_conn) is False


def test_check_duplicate_db_error():
    """DB errors during duplicate check default to non-duplicate (fail open for extraction)."""
    skill = _make_skill()
    mock_conn = MagicMock()
    mock_conn.cursor.side_effect = Exception("connection refused")

    assert check_duplicate(skill, mock_conn) is False


# ── Test: Circuit breaker trips after max extractions ──

def test_circuit_breaker_trips():
    """Circuit breaker blocks extractions after max_per_day is reached."""
    breaker = CircuitBreaker(max_per_day=3)
    assert breaker.allow() is True

    breaker.record()
    breaker.record()
    breaker.record()
    assert breaker.count_today == 3
    assert breaker.allow() is False


def test_circuit_breaker_resets_after_24h():
    """Circuit breaker resets after timestamps age past 24 hours."""
    breaker = CircuitBreaker(max_per_day=2)
    # Inject old timestamps (25 hours ago)
    old_time = time.time() - 90000
    breaker._timestamps = [old_time, old_time]

    assert breaker.allow() is True
    assert breaker.count_today == 0


def test_circuit_breaker_blocks_extraction():
    """extract_skill returns None when circuit breaker is tripped."""
    breaker = get_circuit_breaker()
    original_max = breaker.max_per_day
    original_timestamps = breaker._timestamps[:]

    try:
        breaker.max_per_day = 0  # Trip immediately
        breaker._timestamps = [time.time()]

        task = _make_task()
        result = extract_skill(task, dispatcher=MagicMock())
        assert result is None
    finally:
        breaker.max_per_day = original_max
        breaker._timestamps = original_timestamps


# ── Test: Valid extraction produces correct SkillDescriptor ──

def test_valid_extraction():
    """A successful extraction returns a well-formed SkillDescriptor."""
    breaker = get_circuit_breaker()
    original_timestamps = breaker._timestamps[:]

    try:
        # Clear the breaker so extraction is allowed
        breaker._timestamps = []

        model_response = {
            "skill_found": True,
            "name": "Health Endpoint Pattern",
            "intent": "Expose service liveness for monitoring",
            "method": "Create /health route returning JSON with status, uptime, version",
            "difficulty": 5,
            "tool_hints": ["fastapi", "pytest"],
            "domain": "ops",
            "reasoning": "Health checks are reusable across all services",
        }
        dispatcher = _mock_dispatcher(model_response)
        task = _make_task()

        skill = extract_skill(task, dispatcher=dispatcher)
        assert skill is not None
        assert isinstance(skill, SkillDescriptor)
        assert skill.name == "Health Endpoint Pattern"
        assert skill.intent == "Expose service liveness for monitoring"
        assert skill.difficulty == 5
        assert skill.domain == "ops"
        assert skill.source_task_id == 42
        assert "fastapi" in skill.tool_hints
    finally:
        breaker._timestamps = original_timestamps


def test_extraction_no_skill_found():
    """When the model says no skill was found, extract_skill returns None."""
    breaker = get_circuit_breaker()
    original_timestamps = breaker._timestamps[:]

    try:
        breaker._timestamps = []

        model_response = {
            "skill_found": False,
            "reasoning": "Just a config tweak, not a transferable pattern",
        }
        dispatcher = _mock_dispatcher(model_response)
        task = _make_task(title="Fix typo in config")

        result = extract_skill(task, dispatcher=dispatcher)
        assert result is None
    finally:
        breaker._timestamps = original_timestamps


def test_extraction_dispatch_failure():
    """When dispatch fails, extract_skill returns None without crashing."""
    breaker = get_circuit_breaker()
    original_timestamps = breaker._timestamps[:]

    try:
        breaker._timestamps = []

        dispatcher = MagicMock()
        dispatcher.dispatch.return_value = {
            "ok": False,
            "text": "timeout",
            "node": "redfin_vllm",
            "latency_ms": 30000,
        }
        task = _make_task()

        result = extract_skill(task, dispatcher=dispatcher)
        assert result is None
    finally:
        breaker._timestamps = original_timestamps


# ── Test: Council submission ──

def test_submit_active_on_high_confidence():
    """Council consent + confidence > 0.5 sets status to active."""
    skill = _make_skill()
    council = MagicMock()
    council.council_vote.return_value = {
        "consent": True, "confidence": 0.85, "reason": "Clear reusable pattern",
    }
    result = submit_for_verification(skill, council)
    assert result["status"] == "active"
    assert result["confidence"] == 0.85


def test_submit_candidate_on_low_confidence():
    """Council consent + confidence <= 0.5 sets status to candidate."""
    skill = _make_skill()
    council = MagicMock()
    council.council_vote.return_value = {
        "consent": True, "confidence": 0.35, "reason": "Uncertain applicability",
    }
    result = submit_for_verification(skill, council)
    assert result["status"] == "candidate"


def test_submit_rejected_on_dissent():
    """Council dissent sets status to rejected."""
    skill = _make_skill()
    council = MagicMock()
    council.council_vote.return_value = {
        "consent": False, "confidence": 0.7, "reason": "Too specific to be reusable",
    }
    result = submit_for_verification(skill, council)
    assert result["status"] == "rejected"


def test_submit_candidate_on_council_unreachable():
    """Turtle condition: council timeout defaults to candidate, never auto-active."""
    skill = _make_skill()
    council = MagicMock()
    council.council_vote.side_effect = TimeoutError("council unreachable")

    result = submit_for_verification(skill, council)
    assert result["status"] == "candidate"
    assert result["confidence"] == 0.0


# ── Test: Sanitization preserves clean skills ──

def test_sanitize_clean_skill_passes():
    """A skill with no infrastructure terms passes sanitization unchanged."""
    skill = _make_skill(
        intent="Create a health check endpoint for HTTP services",
        method="Add a /health route that returns JSON with status field",
    )
    result = sanitize_skill(skill)
    assert result is not None
    assert result.intent == skill.intent
    assert result.method == skill.method


# ── Test: Internal path stripping ──

def test_sanitize_strips_internal_paths():
    """Paths containing /ganuda/ are replaced with <internal_path>."""
    skill = _make_skill(
        method="Edit /ganuda/lib/some_module.py and add the new function",
    )
    result = sanitize_skill(skill)
    assert result is not None
    assert "/ganuda/" not in result.method
    assert "<internal_path>" in result.method
