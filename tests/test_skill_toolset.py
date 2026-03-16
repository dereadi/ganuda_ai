"""
Tests for SkillToolSet — SkillRL ToolSet Ring.
Cherokee AI Federation — SkillRL-07

All DB interactions are mocked. Tests cover:
1. Tool registration: correct tools returned
2. list_available_skills: JSON with scores
3. apply_skill: method with context
4. get_skill_method: full detail
5. Unknown skill: error response
6. Library cap: 501 active -> one auto-retired
7. Empty library: helpful message
"""

import json
import sys
import os
from unittest.mock import MagicMock, patch, call

import pytest

# Ensure lib is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))


def _make_mock_conn():
    """Create a mock DB connection."""
    conn = MagicMock()
    cursor = MagicMock()
    conn.cursor.return_value = cursor
    cursor.fetchone.return_value = (0,)  # default: 0 active skills for cap check
    cursor.fetchall.return_value = []
    return conn


def _make_skill_dict(
    skill_id="sk_test",
    name="Test Skill",
    intent="Test intent for pattern",
    method="Step 1: do X. Step 2: do Y.",
    difficulty=3,
    tool_hints=None,
    domain="general",
    total_uses=10,
    successful_uses=7,
    total_reward=7.0,
    ucb_score=1.5,
    final_score=2.25,
    is_compound=False,
    parent_skills=None,
):
    """Helper to build a skill dict as returned by SkillSelector.select_skills."""
    if tool_hints is None:
        tool_hints = ["pytest", "psycopg2"]
    if parent_skills is None:
        parent_skills = []
    return {
        "skill_id": skill_id,
        "name": name,
        "intent": intent,
        "method": method,
        "difficulty": difficulty,
        "tool_hints": json.dumps(tool_hints) if isinstance(tool_hints, list) else tool_hints,
        "domain": domain,
        "total_uses": total_uses,
        "successful_uses": successful_uses,
        "total_reward": total_reward,
        "ucb_score": ucb_score,
        "final_score": final_score,
        "is_compound": is_compound,
        "parent_skills": json.dumps(parent_skills) if isinstance(parent_skills, list) else parent_skills,
    }


class TestToolRegistration:
    """Test 1: SkillToolSet has correct tools."""

    def test_has_three_tools(self):
        conn = _make_mock_conn()
        with patch("skill_selector.SkillProficiency"):
            from toolsets.skill_toolset import SkillToolSet
            ts = SkillToolSet(conn)
            tools = ts.get_tools()

        assert len(tools) == 3
        names = {t.name for t in tools}
        assert names == {"list_available_skills", "apply_skill", "get_skill_method"}

    def test_all_tools_are_read(self):
        conn = _make_mock_conn()
        with patch("skill_selector.SkillProficiency"):
            from toolsets.skill_toolset import SkillToolSet
            ts = SkillToolSet(conn)
            tools = ts.get_tools()

        for tool in tools:
            assert tool.safety_class == "read"

    def test_domain_is_skillrl(self):
        conn = _make_mock_conn()
        with patch("skill_selector.SkillProficiency"):
            from toolsets.skill_toolset import SkillToolSet
            ts = SkillToolSet(conn)

        assert ts.domain == "skillrl"


class TestListAvailableSkills:
    """Test 2: list_available_skills returns JSON with scores."""

    def test_returns_loaded_skills_with_scores(self):
        conn = _make_mock_conn()
        with patch("skill_selector.SkillProficiency"):
            from toolsets.skill_toolset import SkillToolSet
            ts = SkillToolSet(conn)

        # Manually load skills (bypass selector)
        ts._loaded_skills = {
            "sk1": _make_skill_dict(skill_id="sk1", name="Skill One", ucb_score=1.5, final_score=2.25),
            "sk2": _make_skill_dict(skill_id="sk2", name="Skill Two", ucb_score=1.2, final_score=1.8),
        }

        result = ts.list_available_skills()

        assert result["count"] == 2
        assert len(result["skills"]) == 2

        # Check fields present
        first = result["skills"][0]
        assert "skill_id" in first
        assert "name" in first
        assert "ucb_score" in first
        assert "final_score" in first
        assert "difficulty" in first
        assert "domain" in first


class TestApplySkill:
    """Test 3: apply_skill returns method with context."""

    def test_returns_method_and_context(self):
        conn = _make_mock_conn()
        with patch("skill_selector.SkillProficiency"):
            from toolsets.skill_toolset import SkillToolSet
            ts = SkillToolSet(conn)

        ts._loaded_skills = {
            "sk_apply": _make_skill_dict(
                skill_id="sk_apply",
                name="Apply Skill",
                method="Step 1: read the file. Step 2: parse JSON.",
                tool_hints=["Read", "json.loads"],
            ),
        }

        result = ts.apply_skill(skill_id="sk_apply", context="Parsing config.json")

        assert result["skill_id"] == "sk_apply"
        assert "method" in result
        assert "Step 1" in result["method"]
        assert result["context"] == "Parsing config.json"
        assert "instructions" in result
        assert "Parsing config.json" in result["instructions"]
        assert isinstance(result["tool_hints"], list)

    def test_apply_via_execute(self):
        """Verify dispatch through base class execute works."""
        conn = _make_mock_conn()
        with patch("skill_selector.SkillProficiency"):
            from toolsets.skill_toolset import SkillToolSet
            ts = SkillToolSet(conn)

        ts._loaded_skills = {
            "sk_exec": _make_skill_dict(skill_id="sk_exec", method="Do the thing"),
        }

        result = ts.execute("apply_skill", {"skill_id": "sk_exec", "context": "test"})
        assert result.success is True
        assert result.data["skill_id"] == "sk_exec"


class TestGetSkillMethod:
    """Test 4: get_skill_method returns full detail."""

    def test_returns_full_detail(self):
        conn = _make_mock_conn()
        with patch("skill_selector.SkillProficiency"):
            from toolsets.skill_toolset import SkillToolSet
            ts = SkillToolSet(conn)

        ts._loaded_skills = {
            "sk_detail": _make_skill_dict(
                skill_id="sk_detail",
                name="Detailed Skill",
                intent="Why this works",
                method="How to do it",
                difficulty=7,
                domain="code",
                tool_hints=["grep", "sed"],
                is_compound=True,
                parent_skills=["sk_parent1", "sk_parent2"],
            ),
        }

        result = ts.get_skill_method(skill_id="sk_detail")

        assert result["skill_id"] == "sk_detail"
        assert result["name"] == "Detailed Skill"
        assert result["intent"] == "Why this works"
        assert result["method"] == "How to do it"
        assert result["difficulty"] == 7
        assert result["domain"] == "code"
        assert result["is_compound"] is True
        assert isinstance(result["tool_hints"], list)
        assert isinstance(result["parent_skills"], list)
        assert "sk_parent1" in result["parent_skills"]


class TestUnknownSkill:
    """Test 5: Unknown skill returns error response."""

    def test_apply_unknown_skill(self):
        conn = _make_mock_conn()
        with patch("skill_selector.SkillProficiency"):
            from toolsets.skill_toolset import SkillToolSet
            ts = SkillToolSet(conn)

        ts._loaded_skills = {
            "sk_real": _make_skill_dict(skill_id="sk_real"),
        }

        result = ts.apply_skill(skill_id="sk_nonexistent")
        assert "error" in result
        assert "sk_nonexistent" in result["error"]

    def test_get_method_unknown_skill(self):
        conn = _make_mock_conn()
        with patch("skill_selector.SkillProficiency"):
            from toolsets.skill_toolset import SkillToolSet
            ts = SkillToolSet(conn)

        ts._loaded_skills = {}

        result = ts.get_skill_method(skill_id="sk_ghost")
        assert "error" in result
        assert "sk_ghost" in result["error"]


class TestLibraryCap:
    """Test 6: 501 active skills -> one auto-retired."""

    def test_cap_enforcement_retires_one(self):
        conn = _make_mock_conn()
        cursor = conn.cursor.return_value
        # First call to fetchone returns count of 501
        cursor.fetchone.return_value = (501,)
        # select_skills returns empty (we just care about the cap logic)
        cursor.fetchall.return_value = []

        with patch("skill_selector.SkillProficiency"):
            from toolsets.skill_toolset import SkillToolSet
            ts = SkillToolSet(conn)

            ts.load_skills_for_task("general", "test task")

        # Check that the retirement UPDATE was executed
        all_calls = cursor.execute.call_args_list
        retire_calls = [
            c for c in all_calls
            if "status = 'retired'" in str(c) and "cap_overflow" in str(c)
        ]
        assert len(retire_calls) >= 1, (
            f"Expected cap_overflow retirement UPDATE. Calls: {[str(c)[:100] for c in all_calls]}"
        )

    def test_no_retirement_under_cap(self):
        conn = _make_mock_conn()
        cursor = conn.cursor.return_value
        # 499 active — under cap
        cursor.fetchone.return_value = (499,)
        cursor.fetchall.return_value = []

        with patch("skill_selector.SkillProficiency"):
            from toolsets.skill_toolset import SkillToolSet
            ts = SkillToolSet(conn)

            ts.load_skills_for_task("general", "test task")

        all_calls = cursor.execute.call_args_list
        retire_calls = [
            c for c in all_calls
            if "status = 'retired'" in str(c) and "cap_overflow" in str(c)
        ]
        assert len(retire_calls) == 0, "Should NOT retire when under cap"


class TestEmptyLibrary:
    """Test 7: Empty library returns helpful message."""

    def test_empty_list_returns_message(self):
        conn = _make_mock_conn()
        with patch("skill_selector.SkillProficiency"):
            from toolsets.skill_toolset import SkillToolSet
            ts = SkillToolSet(conn)

        # No skills loaded
        ts._loaded_skills = {}

        result = ts.list_available_skills()

        assert result["count"] == 0
        assert len(result["skills"]) == 0
        assert "message" in result
        assert "No skills loaded" in result["message"]
