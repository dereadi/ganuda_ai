#!/usr/bin/env python3
"""
Tests for SkillRL-04 — Proficiency Tracker (EMA Curriculum Learning)

Tests cover:
    1. EMA convergence: repeated success approaches 1.0
    2. EMA decay: repeated low reward pulls score down
    3. New category: unseen category returns 0.5
    4. Weakest sorting: get_weakest returns lowest-scored categories first
    5. Proficiency vector: get_vector returns all categories with correct scores
"""

import sys

sys.path.insert(0, "/ganuda")

import pytest
from unittest.mock import MagicMock, patch
from decimal import Decimal

from lib.skill_proficiency import SkillProficiency, ALPHA, DEFAULT_SCORE


def _make_mock_conn():
    """Create a mock psycopg2 connection with cursor support."""
    conn = MagicMock()
    cursor = MagicMock()
    conn.cursor.return_value = cursor
    return conn, cursor


class TestEMAConvergence:
    """Test 1: Update 10 times with reward=1.0, success=True → score approaches 1.0"""

    def test_ema_converges_toward_one(self):
        """Repeated successful high-reward updates should push score toward 1.0."""
        conn, cursor = _make_mock_conn()

        # Track score across updates — start with unseen (0.5)
        score = DEFAULT_SCORE

        # Each call to get_score returns the current score, then update computes new
        # We simulate the EMA math directly to verify convergence
        for _ in range(10):
            new_signal = 1.0  # reward=1.0, success=True
            score = (1 - ALPHA) * score + ALPHA * new_signal

        # After 10 updates with reward=1.0 from 0.5 start, should be close to 1.0
        assert score > 0.95, f"Score should converge toward 1.0, got {score}"

        # Now verify the class does the same math
        prof = SkillProficiency(conn)
        running_score = DEFAULT_SCORE

        for i in range(10):
            # Mock get_score to return current running score
            cursor.fetchone.return_value = {"proficiency_score": Decimal(str(running_score))}
            new_score = prof.update("general", "math", reward=1.0, success=True)
            running_score = new_score

        assert abs(running_score - score) < 1e-10
        assert running_score > 0.95


class TestEMADecay:
    """Test 2: Start at 0.8, update with reward=0.2 five times → score drops."""

    def test_ema_decays_with_low_reward(self):
        conn, cursor = _make_mock_conn()
        prof = SkillProficiency(conn)

        # Start at 0.8
        running_score = 0.8

        for _ in range(5):
            cursor.fetchone.return_value = {"proficiency_score": Decimal(str(running_score))}
            new_signal = 0.2  # reward=0.2, success=True
            expected = (1 - ALPHA) * running_score + ALPHA * new_signal
            new_score = prof.update("general", "debugging", reward=0.2, success=True)
            assert abs(new_score - expected) < 1e-10
            running_score = new_score

        # Score should have dropped significantly from 0.8
        assert running_score < 0.5, f"Score should decay below 0.5, got {running_score}"

    def test_failure_halves_signal(self):
        """Failure should use reward * 0.5 as the signal."""
        conn, cursor = _make_mock_conn()
        prof = SkillProficiency(conn)

        # Start at 0.5
        cursor.fetchone.return_value = {"proficiency_score": Decimal("0.5")}

        # reward=0.8, success=False → signal = 0.8 * 0.5 = 0.4
        new_score = prof.update("general", "testing", reward=0.8, success=False)
        expected = (1 - ALPHA) * 0.5 + ALPHA * 0.4
        assert abs(new_score - expected) < 1e-10


class TestNewCategory:
    """Test 3: get_score for unknown category returns 0.5."""

    def test_unseen_category_returns_default(self):
        conn, cursor = _make_mock_conn()
        prof = SkillProficiency(conn)

        # No row found in DB
        cursor.fetchone.return_value = None

        score = prof.get_score("general", "never_seen_before")
        assert score == 0.5

    def test_default_score_constant(self):
        """DEFAULT_SCORE should be 0.5."""
        assert DEFAULT_SCORE == 0.5

    def test_alpha_constant(self):
        """ALPHA should be 0.3."""
        assert ALPHA == 0.3


class TestWeakestSorting:
    """Test 4: Insert 5 categories with different scores → get_weakest returns lowest first."""

    def test_get_weakest_returns_sorted_by_score(self):
        conn, cursor = _make_mock_conn()
        prof = SkillProficiency(conn)

        # Simulate DB returning rows sorted by proficiency_score ASC
        # (the SQL ORDER BY handles this, we verify the class returns them as-is)
        mock_rows = [
            {"domain": "general", "category": "error_handling", "proficiency_score": Decimal("0.15"),
             "total_attempts": 5, "successful_attempts": 1, "last_updated": "2026-03-15"},
            {"domain": "general", "category": "networking", "proficiency_score": Decimal("0.30"),
             "total_attempts": 4, "successful_attempts": 1, "last_updated": "2026-03-15"},
            {"domain": "general", "category": "file_io", "proficiency_score": Decimal("0.45"),
             "total_attempts": 6, "successful_attempts": 3, "last_updated": "2026-03-15"},
            {"domain": "general", "category": "api_calls", "proficiency_score": Decimal("0.60"),
             "total_attempts": 3, "successful_attempts": 2, "last_updated": "2026-03-15"},
            {"domain": "general", "category": "testing", "proficiency_score": Decimal("0.75"),
             "total_attempts": 8, "successful_attempts": 6, "last_updated": "2026-03-15"},
        ]
        cursor.fetchall.return_value = mock_rows

        weakest = prof.get_weakest("general", limit=5)

        assert len(weakest) == 5
        # Verify sorted ascending by proficiency_score
        scores = [w["proficiency_score"] for w in weakest]
        assert scores == sorted(scores)
        # Weakest first
        assert weakest[0]["category"] == "error_handling"
        assert weakest[-1]["category"] == "testing"

    def test_get_weakest_respects_limit(self):
        conn, cursor = _make_mock_conn()
        prof = SkillProficiency(conn)

        cursor.fetchall.return_value = [
            {"domain": "general", "category": "a", "proficiency_score": Decimal("0.1"),
             "total_attempts": 3, "successful_attempts": 0, "last_updated": "2026-03-15"},
            {"domain": "general", "category": "b", "proficiency_score": Decimal("0.2"),
             "total_attempts": 4, "successful_attempts": 1, "last_updated": "2026-03-15"},
        ]

        weakest = prof.get_weakest("general", limit=2)
        assert len(weakest) == 2


class TestProficiencyVector:
    """Test 5: Insert 3 categories → get_vector returns all three with correct scores."""

    def test_get_vector_returns_all_categories(self):
        conn, cursor = _make_mock_conn()
        prof = SkillProficiency(conn)

        cursor.fetchall.return_value = [
            {"category": "api_calls", "proficiency_score": Decimal("0.72")},
            {"category": "file_io", "proficiency_score": Decimal("0.45")},
            {"category": "testing", "proficiency_score": Decimal("0.88")},
        ]

        vector = prof.get_vector("general")

        assert len(vector) == 3
        assert "api_calls" in vector
        assert "file_io" in vector
        assert "testing" in vector
        assert abs(vector["api_calls"] - 0.72) < 1e-10
        assert abs(vector["file_io"] - 0.45) < 1e-10
        assert abs(vector["testing"] - 0.88) < 1e-10

    def test_get_vector_empty_domain(self):
        conn, cursor = _make_mock_conn()
        prof = SkillProficiency(conn)

        cursor.fetchall.return_value = []
        vector = prof.get_vector("nonexistent")
        assert vector == {}

    def test_get_vector_returns_floats(self):
        """Values should be float, not Decimal."""
        conn, cursor = _make_mock_conn()
        prof = SkillProficiency(conn)

        cursor.fetchall.return_value = [
            {"category": "math", "proficiency_score": Decimal("0.55")},
        ]

        vector = prof.get_vector("general")
        assert isinstance(vector["math"], float)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
