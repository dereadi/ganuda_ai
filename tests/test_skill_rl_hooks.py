#!/usr/bin/env python3
"""
Tests for SkillRL Hooks (JR-SKILLRL-06).

Tests pre-task skill loading, post-task extraction, reward feedback,
pipeline isolation, kill switch, and loading timeout — all with mocks.
"""

import sys
import time
from unittest.mock import MagicMock, patch, call

import pytest

sys.path.insert(0, "/ganuda")

from lib.skill_rl_hooks import (
    get_skill_rl_config,
    set_skill_rl_config,
    reset_skill_rl_config,
    pre_task_skill_load,
    post_task_skill_extract,
    post_task_reward_update,
)


# ── Fixtures ──

@pytest.fixture(autouse=True)
def _reset_config():
    """Reset config before and after each test."""
    reset_skill_rl_config()
    yield
    reset_skill_rl_config()


def _make_task(**overrides):
    """Build a sample Jr task dict."""
    task = {
        "task_id": 42,
        "title": "Implement health check endpoint",
        "description": "Add /health endpoint that returns service status.",
        "domain": "code",
        "status": "done",
        "acceptance_criteria": "GET /health returns 200",
        "files_modified": "api/routes.py",
        "steps_summary": "1. Created health.py. 2. Added route.",
    }
    task.update(overrides)
    return task


def _make_mock_skills():
    """Return a list of mock skill dicts as returned by SkillToolSet.load_skills_for_task."""
    return [
        {
            "skill_id": "abc123",
            "name": "Health Check Pattern",
            "intent": "Provide a standard health check endpoint",
            "method": "1. Create /health route. 2. Return JSON status.",
            "difficulty": 4,
            "domain": "code",
            "tool_hints": ["pytest", "fastapi"],
            "ucb_score": 1.5,
            "final_score": 2.1,
            "total_uses": 3,
            "successful_uses": 2,
        },
    ]


# ── Test 1: Pre-task skill injection ──

def test_pre_task_skill_injection():
    """Mock skills loaded -> verify context block returned."""
    mock_toolset = MagicMock()
    mock_toolset.load_skills_for_task.return_value = _make_mock_skills()

    mock_cls = MagicMock(return_value=mock_toolset)

    db_conn = MagicMock()
    task = _make_task()

    with patch.dict("sys.modules", {}):
        with patch("lib.skill_rl_hooks._import_skill_toolset", return_value=mock_cls, create=True):
            pass

    # Patch at the import location inside the function
    with patch("lib.toolsets.skill_toolset.SkillToolSet", mock_cls):
        result = pre_task_skill_load(task, db_conn)

    assert "## Available Skills" in result
    assert "Health Check Pattern" in result
    assert "abc123" in result
    assert "pytest, fastapi" in result


# ── Test 2: Post-task extraction ──

def test_post_task_extraction():
    """Mock successful task -> verify extractor pipeline called."""
    from lib.skill_descriptor import SkillDescriptor

    mock_skill = SkillDescriptor(
        name="Test Skill",
        intent="Test intent",
        method="Test method",
        difficulty=5,
    )

    task = _make_task(status="done")
    db_conn = MagicMock()
    council = MagicMock()

    with patch("lib.skill_extractor.extract_skill", return_value=mock_skill) as mock_extract, \
         patch("lib.skill_extractor.sanitize_skill", side_effect=lambda s: s) as mock_sanitize, \
         patch("lib.skill_extractor.check_duplicate", return_value=False) as mock_dup, \
         patch("lib.skill_extractor.submit_for_verification") as mock_submit:
        post_task_skill_extract(task, db_conn, council=council)

        mock_extract.assert_called_once()
        mock_sanitize.assert_called_once_with(mock_skill)
        mock_dup.assert_called_once_with(mock_skill, db_conn)
        mock_submit.assert_called_once_with(mock_skill, council)


# ── Test 3: Failed task skip ──

def test_failed_task_skip():
    """Failed task -> extractor NOT called."""
    task = _make_task(status="failed")
    db_conn = MagicMock()

    with patch("lib.skill_extractor.extract_skill") as mock_extract:
        post_task_skill_extract(task, db_conn)
        mock_extract.assert_not_called()


# ── Test 4: Pipeline isolation ──

def test_pipeline_isolation():
    """Extraction raises exception -> hook catches, doesn't propagate."""
    task = _make_task(status="done")
    db_conn = MagicMock()

    with patch("lib.skill_extractor.extract_skill", side_effect=RuntimeError("kaboom")):
        # Must NOT raise
        post_task_skill_extract(task, db_conn)


# ── Test 5: Reward feedback ──

def test_reward_feedback():
    """Task used skills -> verify update_reward called."""
    mock_selector = MagicMock()

    db_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = [("skill_abc",), ("skill_def",)]
    db_conn.cursor.return_value = mock_cursor

    with patch("skill_selector.SkillSelector", return_value=mock_selector):
        post_task_reward_update(
            task_id=42,
            task_status="done",
            domain="code",
            db_conn=db_conn,
        )

    assert mock_selector.update_reward.call_count == 2
    first_call = mock_selector.update_reward.call_args_list[0]
    assert first_call == call(
        skill_id="skill_abc",
        domain="code",
        reward=0.9,
        success=True,
        latency_ms=0,
    )
    second_call = mock_selector.update_reward.call_args_list[1]
    assert second_call == call(
        skill_id="skill_def",
        domain="code",
        reward=0.9,
        success=True,
        latency_ms=0,
    )


# ── Test 6: Kill switch ──

def test_kill_switch_pre_task():
    """enabled=False -> no skills loaded."""
    set_skill_rl_config({"enabled": False})

    db_conn = MagicMock()
    task = _make_task()

    with patch("lib.toolsets.skill_toolset.SkillToolSet") as MockSkillToolSet:
        result = pre_task_skill_load(task, db_conn)

    assert result == ""
    MockSkillToolSet.assert_not_called()


def test_kill_switch_post_task():
    """enabled=False -> no extraction."""
    set_skill_rl_config({"enabled": False})

    task = _make_task(status="done")
    db_conn = MagicMock()

    with patch("lib.skill_extractor.extract_skill") as mock_extract:
        post_task_skill_extract(task, db_conn)
        mock_extract.assert_not_called()


def test_kill_switch_reward():
    """enabled=False -> no reward update."""
    set_skill_rl_config({"enabled": False})

    db_conn = MagicMock()

    post_task_reward_update(42, "done", "code", db_conn)

    db_conn.cursor.assert_not_called()


# ── Test 7: Loading timeout ──

def test_loading_timeout_logs_warning():
    """Mock slow load -> verify returns result but warning is logged."""
    def slow_load(domain, task_description):
        time.sleep(0.1)  # 100ms — exceeds 50ms timeout
        return _make_mock_skills()

    mock_toolset = MagicMock()
    mock_toolset.load_skills_for_task.side_effect = slow_load
    mock_cls = MagicMock(return_value=mock_toolset)

    db_conn = MagicMock()
    task = _make_task()

    with patch("lib.toolsets.skill_toolset.SkillToolSet", mock_cls), \
         patch("lib.skill_rl_hooks.logger") as mock_logger:
        result = pre_task_skill_load(task, db_conn)

    # Skills are still returned (non-blocking design), but warning logged
    assert isinstance(result, str)
    # Verify warning was logged about timeout
    mock_logger.warning.assert_called()
    warning_msg = mock_logger.warning.call_args[0][0]
    assert "took" in warning_msg.lower() or "loading" in warning_msg.lower()


# ── Test: get_skill_rl_config defaults ──

def test_config_defaults():
    """Verify default config values."""
    config = get_skill_rl_config()
    assert config["enabled"] is True
    assert config["extraction_timeout_s"] == 30
    assert config["skill_loading_timeout_ms"] == 50
    assert config["max_skills_per_task"] == 5
    assert config["max_extractions_per_day"] == 5
    assert config["library_cap"] == 500


def test_config_override():
    """Config override merges with defaults."""
    set_skill_rl_config({"enabled": False, "library_cap": 100})
    config = get_skill_rl_config()
    assert config["enabled"] is False
    assert config["library_cap"] == 100
    assert config["extraction_timeout_s"] == 30  # default preserved
