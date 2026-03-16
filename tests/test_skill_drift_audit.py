"""
Tests for skill_drift_audit — SkillRL-09 Drift Audit Timer.
Cherokee AI Federation

All DB interactions are mocked. Tests cover:
1. Integrity pass: all hashes match -> zero failures
2. Integrity fail: mismatched hash -> quarantine triggered
3. NEVER_SEND catch: skill with node name -> flagged
4. Cold pruning: skill 31 days old, never used -> retired
5. Report format: output matches expected JSON schema
"""

import hashlib
import json
import os
import sys
from datetime import datetime, timedelta
from unittest.mock import MagicMock, call, patch

import pytest

# Ensure scripts and lib are importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))

from skill_drift_audit import (
    check_dc_violations,
    check_never_send,
    compute_content_hash,
    run_audit,
)


def _make_skill_row(
    skill_id="sk1",
    name="Test Skill",
    intent="Use pytest for unit testing",
    method="Run pytest with -v flag on the test directory",
    tool_hints=None,
    domain="code",
    total_uses=5,
    successful_uses=4,
    total_reward=4.0,
    last_used=None,
    created_at=None,
    status="active",
    content_hash=None,
):
    """Helper to build a mock skill_library row dict."""
    if tool_hints is None:
        tool_hints = json.dumps(["pytest"])
    elif isinstance(tool_hints, list):
        tool_hints = json.dumps(tool_hints)

    if created_at is None:
        created_at = datetime.now() - timedelta(days=5)

    if content_hash is None:
        content_hash = compute_content_hash(intent, method, tool_hints)

    return {
        "skill_id": skill_id,
        "name": name,
        "intent": intent,
        "method": method,
        "tool_hints": tool_hints,
        "domain": domain,
        "content_hash": content_hash,
        "total_uses": total_uses,
        "successful_uses": successful_uses,
        "total_reward": total_reward,
        "last_used": last_used,
        "created_at": created_at,
        "status": status,
    }


def _build_mock_conn(active_skills, cold_retired=None, proficiency_rows=None, status_counts=None):
    """
    Build a mock psycopg2 connection that returns data for each query in run_audit.

    Query order in run_audit:
    1. SELECT ... FROM skill_library WHERE status = 'active'  -> active_skills
    2. (potential UPDATE calls for quarantine — no fetchall)
    3. UPDATE ... cold pruning RETURNING  -> cold_retired
    4. SELECT ... FROM skill_proficiency  -> proficiency_rows
    5. SELECT status, COUNT(*) FROM skill_library GROUP BY status -> status_counts
    """
    if cold_retired is None:
        cold_retired = []
    if proficiency_rows is None:
        proficiency_rows = [
            {"domain": "code", "category": "frontend", "score": 0.32},
            {"domain": "ops", "category": "monitoring", "score": 0.41},
        ]
    if status_counts is None:
        active_count = len(active_skills) - len(cold_retired)
        status_counts = [
            {"status": "active", "cnt": max(active_count, 0)},
            {"status": "candidate", "cnt": 2},
            {"status": "quarantine", "cnt": 0},
        ]

    conn = MagicMock()
    cursor = MagicMock()
    conn.cursor.return_value = cursor

    # fetchall is called multiple times in sequence
    cursor.fetchall.side_effect = [
        active_skills,       # 1. active skills query
        cold_retired,        # 3. cold pruning RETURNING
        proficiency_rows,    # 4. proficiency query
        status_counts,       # 5. status counts query
    ]

    return conn, cursor


class TestIntegrityPass:
    """Test 1: All hashes match -> zero failures."""

    def test_integrity_all_match(self):
        skill1 = _make_skill_row(skill_id="sk1", name="Skill A")
        skill2 = _make_skill_row(skill_id="sk2", name="Skill B",
                                  intent="Deploy with systemd",
                                  method="Create .service and .timer files")

        conn, cursor = _build_mock_conn([skill1, skill2])
        report = run_audit(conn)

        assert report["integrity_checked"] == 2
        assert report["integrity_failures"] == 0
        # No quarantine UPDATEs should have been called for integrity
        # (there may be cold pruning UPDATE but not integrity quarantine)
        update_calls = [
            c for c in cursor.execute.call_args_list
            if "quarantine" in str(c).lower() and "SET status" in str(c)
        ]
        assert len(update_calls) == 0


class TestIntegrityFail:
    """Test 2: Mismatched hash -> quarantine triggered."""

    def test_integrity_mismatch_quarantines(self):
        skill = _make_skill_row(skill_id="sk_bad", name="Corrupted Skill")
        # Corrupt the hash
        skill["content_hash"] = "0000000000000000000000000000000000000000000000000000000000000000"

        conn, cursor = _build_mock_conn(
            [skill],
            status_counts=[
                {"status": "active", "cnt": 0},
                {"status": "candidate", "cnt": 0},
                {"status": "quarantine", "cnt": 1},
            ],
        )
        report = run_audit(conn)

        assert report["integrity_checked"] == 1
        assert report["integrity_failures"] == 1

        # Verify quarantine UPDATE was executed
        quarantine_calls = [
            c for c in cursor.execute.call_args_list
            if "quarantine" in str(c) and "UPDATE" in str(c)
        ]
        assert len(quarantine_calls) >= 1


class TestNeverSendCatch:
    """Test 3: Skill with node name -> flagged and quarantined."""

    def test_never_send_node_name_flagged(self):
        # Skill with valid hash but containing a node name in the method
        skill = _make_skill_row(
            skill_id="sk_leak",
            name="Leaky Skill",
            intent="Deploy service correctly",
            method="SSH into redfin and restart the service",
        )

        conn, cursor = _build_mock_conn(
            [skill],
            status_counts=[
                {"status": "active", "cnt": 0},
                {"status": "candidate", "cnt": 0},
                {"status": "quarantine", "cnt": 1},
            ],
        )
        report = run_audit(conn)

        assert report["never_send_violations"] == 1
        # Verify quarantine UPDATE was executed
        quarantine_calls = [
            c for c in cursor.execute.call_args_list
            if "quarantine" in str(c) and "UPDATE" in str(c)
        ]
        assert len(quarantine_calls) >= 1

    def test_never_send_patterns_detect_ips(self):
        """Verify check_never_send catches IPs and internal paths."""
        assert len(check_never_send("Connect to 192.168.132.222")) > 0
        assert len(check_never_send("Read /ganuda/config/secrets.env")) > 0
        assert len(check_never_send("Use 10.100.0.3 for WireGuard")) > 0
        assert len(check_never_send("Safe text with no leaks")) == 0


class TestColdPruning:
    """Test 4: Skill 31 days old, never used -> retired."""

    def test_cold_skill_retired(self):
        old_skill = _make_skill_row(
            skill_id="sk_cold",
            name="Ancient Unused Skill",
            last_used=None,
            created_at=datetime.now() - timedelta(days=31),
        )

        # The cold pruning UPDATE RETURNING gives us the retired skill
        cold_retired = [{"skill_id": "sk_cold", "name": "Ancient Unused Skill"}]

        conn, cursor = _build_mock_conn(
            [old_skill],
            cold_retired=cold_retired,
            status_counts=[
                {"status": "active", "cnt": 0},
                {"status": "retired", "cnt": 1},
                {"status": "candidate", "cnt": 0},
                {"status": "quarantine", "cnt": 0},
            ],
        )
        report = run_audit(conn)

        assert report["cold_skills_retired"] == 1

        # Verify the cold pruning UPDATE was in the executed queries
        cold_calls = [
            c for c in cursor.execute.call_args_list
            if "cold_30d" in str(c)
        ]
        assert len(cold_calls) == 1


class TestReportFormat:
    """Test 5: Output matches expected JSON schema."""

    REQUIRED_KEYS = {
        "timestamp",
        "integrity_checked",
        "integrity_failures",
        "never_send_violations",
        "dc_violations_flagged",
        "cold_skills_retired",
        "active_skills",
        "candidate_skills",
        "quarantined_skills",
        "weakest_categories",
    }

    def test_report_has_all_keys(self):
        skill = _make_skill_row()
        conn, cursor = _build_mock_conn([skill])
        report = run_audit(conn)

        assert set(report.keys()) == self.REQUIRED_KEYS

    def test_report_weakest_categories_schema(self):
        skill = _make_skill_row()
        conn, cursor = _build_mock_conn([skill])
        report = run_audit(conn)

        for entry in report["weakest_categories"]:
            assert "domain" in entry
            assert "category" in entry
            assert "proficiency" in entry
            assert isinstance(entry["proficiency"], float)

    def test_report_serializable(self):
        """Report must be JSON-serializable."""
        skill = _make_skill_row()
        conn, cursor = _build_mock_conn([skill])
        report = run_audit(conn)

        serialized = json.dumps(report)
        deserialized = json.loads(serialized)
        assert deserialized["integrity_checked"] == report["integrity_checked"]

    def test_dc_violations_flagged_not_quarantined(self):
        """DC violations should flag but NOT quarantine."""
        skill = _make_skill_row(
            skill_id="sk_dc",
            name="Cloud Lover",
            intent="Use cloud services",
            method="Migrate to AWS for better scaling",
        )

        conn, cursor = _build_mock_conn([skill])
        report = run_audit(conn)

        assert report["dc_violations_flagged"] == 1
        # Should NOT be quarantined (only flagged)
        assert report["integrity_failures"] == 0


class TestHelperFunctions:
    """Unit tests for helper functions."""

    def test_compute_content_hash_matches_descriptor(self):
        """Verify our hash computation matches SkillDescriptor.content_hash."""
        intent = "Test intent"
        method = "Test method"
        hints = ["tool_a", "tool_b"]
        raw = intent + "||" + method + "||" + "|".join(sorted(hints))
        expected = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        assert compute_content_hash(intent, method, hints) == expected

    def test_compute_content_hash_with_json_string(self):
        """Handles tool_hints as JSON string."""
        hints_list = ["b", "a"]
        hints_json = json.dumps(hints_list)
        assert compute_content_hash("i", "m", hints_json) == compute_content_hash("i", "m", hints_list)

    def test_check_dc_violations(self):
        assert len(check_dc_violations("migrate to AWS")) > 0
        assert len(check_dc_violations("chmod 777 /tmp")) > 0
        assert len(check_dc_violations("move fast and break things")) > 0
        assert len(check_dc_violations("use brute force")) > 0
        assert len(check_dc_violations("normal safe method")) == 0
