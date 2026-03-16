"""
Tests for SkillSelector — UCB1 + Curriculum skill selection.
Cherokee AI Federation — SkillRL-05

All DB interactions are mocked. Tests cover:
1. UCB exploration (equal stats → all selected)
2. Curriculum bias (weak > strong)
3. Auto-quarantine (Coyote condition)
4. No quarantine under min uses
5. Integrity check (Eagle Eye)
6. Domain filtering
"""

import hashlib
import json
import sys
import os
from unittest.mock import MagicMock, patch, call

import pytest

# Ensure lib is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))

from skill_selector import SkillSelector, EXPLORATION_WEIGHT, QUARANTINE_THRESHOLD, QUARANTINE_MIN_USES


def _make_skill_row(
    skill_id="sk1",
    name="Test Skill",
    intent="Test intent",
    method="Test method",
    difficulty=3,
    tool_hints=None,
    domain="general",
    total_uses=10,
    successful_uses=7,
    total_reward=7.0,
    avg_latency_ms=100,
    status="active",
    content_hash=None,
):
    """Helper to create a mock skill_library row."""
    if tool_hints is None:
        tool_hints = json.dumps(["pytest"])
    elif isinstance(tool_hints, list):
        tool_hints = json.dumps(tool_hints)

    if content_hash is None:
        # Compute valid content_hash
        hints_list = json.loads(tool_hints) if isinstance(tool_hints, str) else tool_hints
        raw = intent + "||" + method + "||" + "|".join(sorted(hints_list))
        content_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()

    return {
        "skill_id": skill_id,
        "name": name,
        "intent": intent,
        "method": method,
        "difficulty": difficulty,
        "tool_hints": tool_hints,
        "domain": domain,
        "content_hash": content_hash,
        "total_uses": total_uses,
        "successful_uses": successful_uses,
        "total_reward": total_reward,
        "avg_latency_ms": avg_latency_ms,
        "status": status,
    }


def _mock_conn_with_skills(skills):
    """Create a mock connection whose cursor returns the given skill rows."""
    conn = MagicMock()
    cursor = MagicMock()
    conn.cursor.return_value = cursor
    cursor.fetchall.return_value = skills
    cursor.fetchone.return_value = None
    return conn


class TestUCBExploration:
    """Test 1: 5 skills with equal stats -> all 5 selected."""

    def test_equal_stats_all_selected(self):
        skills = [
            _make_skill_row(
                skill_id=f"sk{i}",
                name=f"Skill {i}",
                intent=f"Intent {i}",
                method=f"Method {i}",
                total_uses=10,
                successful_uses=7,
                total_reward=7.0,
            )
            for i in range(5)
        ]
        conn = _mock_conn_with_skills(skills)

        with patch("skill_selector.SkillProficiency") as MockProf:
            MockProf.return_value.get_score.return_value = 0.5
            selector = SkillSelector(conn)
            result = selector.select_skills("general", "any task", max_skills=5)

        assert len(result) == 5
        selected_ids = {s["skill_id"] for s in result}
        assert selected_ids == {"sk0", "sk1", "sk2", "sk3", "sk4"}


class TestCurriculumBias:
    """Test 2: Weak category skill scores higher than strong category equivalent."""

    def test_weak_category_beats_strong(self):
        weak_skill = _make_skill_row(
            skill_id="weak",
            name="Weak Skill",
            intent="weak intent",
            method="weak method",
            tool_hints=["pytest"],
            total_uses=10,
            successful_uses=5,
            total_reward=5.0,
        )
        strong_skill = _make_skill_row(
            skill_id="strong",
            name="Strong Skill",
            intent="strong intent",
            method="strong method",
            tool_hints=["psycopg2"],
            total_uses=10,
            successful_uses=5,
            total_reward=5.0,
        )
        conn = _mock_conn_with_skills([weak_skill, strong_skill])

        with patch("skill_selector.SkillProficiency") as MockProf:
            def get_score_side_effect(domain, category):
                if category == "testing":
                    return 0.2  # weak
                elif category == "db_operations":
                    return 0.9  # strong
                return 0.5

            MockProf.return_value.get_score.side_effect = get_score_side_effect
            selector = SkillSelector(conn)
            result = selector.select_skills("general", "any task", max_skills=2)

        # Weak category skill should be first (higher curriculum weight)
        assert result[0]["skill_id"] == "weak"
        assert result[0]["curriculum_weight"] > result[1]["curriculum_weight"]


class TestAutoQuarantine:
    """Test 3: 1 success / 6 uses -> quarantined after update."""

    def test_quarantine_on_poor_success_rate(self):
        conn = MagicMock()
        cursor = MagicMock()
        conn.cursor.return_value = cursor

        # After update: total_uses=6, successful_uses=1
        cursor.fetchone.return_value = {
            "total_uses": 6,
            "successful_uses": 1,
            "name": "Bad Skill",
            "domain": "general",
            "tool_hints": json.dumps(["pytest"]),
        }

        with patch("skill_selector.SkillProficiency") as MockProf:
            MockProf.return_value.update.return_value = 0.3
            selector = SkillSelector(conn)
            selector.update_reward("sk_bad", "general", reward=0.1, success=False)

        # Should have called UPDATE to quarantine
        all_execute_calls = cursor.execute.call_args_list
        quarantine_calls = [
            c for c in all_execute_calls
            if "status = 'quarantine'" in str(c)
        ]
        assert len(quarantine_calls) > 0, "Expected quarantine UPDATE call"


class TestNoQuarantineUnderThreshold:
    """Test 4: 1 success / 3 uses -> NOT quarantined (min 5 uses)."""

    def test_no_quarantine_below_min_uses(self):
        conn = MagicMock()
        cursor = MagicMock()
        conn.cursor.return_value = cursor

        # After update: total_uses=3, successful_uses=1 (rate=0.33 > 0.3 doesn't matter, under min uses)
        cursor.fetchone.return_value = {
            "total_uses": 3,
            "successful_uses": 1,
            "name": "New Skill",
            "domain": "general",
            "tool_hints": json.dumps(["pytest"]),
        }

        with patch("skill_selector.SkillProficiency") as MockProf:
            MockProf.return_value.update.return_value = 0.4
            selector = SkillSelector(conn)
            selector.update_reward("sk_new", "general", reward=0.2, success=False)

        # Should NOT have quarantine call
        all_execute_calls = cursor.execute.call_args_list
        quarantine_calls = [
            c for c in all_execute_calls
            if "status = 'quarantine'" in str(c)
        ]
        assert len(quarantine_calls) == 0, "Should NOT quarantine with < 5 uses"


class TestIntegrityCheck:
    """Test 5: Corrupted content_hash -> skill excluded from selection."""

    def test_corrupted_hash_excluded(self):
        good_skill = _make_skill_row(
            skill_id="good",
            name="Good Skill",
            intent="good intent",
            method="good method",
            total_uses=10,
            successful_uses=7,
            total_reward=7.0,
        )
        bad_skill = _make_skill_row(
            skill_id="bad",
            name="Bad Skill",
            intent="bad intent",
            method="bad method",
            total_uses=10,
            successful_uses=7,
            total_reward=7.0,
            content_hash="deadbeef_corrupted_hash",
        )
        conn = _mock_conn_with_skills([good_skill, bad_skill])

        with patch("skill_selector.SkillProficiency") as MockProf:
            MockProf.return_value.get_score.return_value = 0.5
            selector = SkillSelector(conn)
            result = selector.select_skills("general", "any task", max_skills=5)

        selected_ids = {s["skill_id"] for s in result}
        assert "good" in selected_ids
        assert "bad" not in selected_ids


class TestDomainFiltering:
    """Test 6: Skills in wrong domain excluded."""

    def test_wrong_domain_excluded(self):
        # The SQL query filters by domain, so we simulate the DB only returning matching rows.
        # A "code" domain skill should NOT appear when querying "ops".
        code_skill = _make_skill_row(
            skill_id="code1",
            name="Code Skill",
            domain="code",
            total_uses=10,
            successful_uses=8,
            total_reward=8.0,
        )
        ops_skill = _make_skill_row(
            skill_id="ops1",
            name="Ops Skill",
            domain="ops",
            tool_hints=["systemd"],
            total_uses=10,
            successful_uses=6,
            total_reward=6.0,
        )
        general_skill = _make_skill_row(
            skill_id="gen1",
            name="General Skill",
            domain="general",
            total_uses=10,
            successful_uses=5,
            total_reward=5.0,
        )

        # When querying for "ops", DB returns ops + general (not code)
        conn = _mock_conn_with_skills([ops_skill, general_skill])

        with patch("skill_selector.SkillProficiency") as MockProf:
            MockProf.return_value.get_score.return_value = 0.5
            selector = SkillSelector(conn)
            result = selector.select_skills("ops", "deploy a service", max_skills=5)

        selected_ids = {s["skill_id"] for s in result}
        assert "code1" not in selected_ids
        assert "ops1" in selected_ids
        assert "gen1" in selected_ids

        # Verify the SQL was called with 'ops' domain
        cursor = conn.cursor.return_value
        sql_call = cursor.execute.call_args
        assert "ops" in sql_call[0][1]
