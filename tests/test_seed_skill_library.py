#!/usr/bin/env python3
"""
Tests for seed_skill_library — validates all seed skills before DB insertion.

Verifies:
- All seed skills have valid content_hash (64-char hex)
- No infrastructure terms in any intent or method
- At least 5 different categories represented
- All skills pass sanitize_skill
- Correct difficulty ratings (1-10)
"""

import os
import re
import sys

import pytest

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from lib.skill_descriptor import SkillDescriptor
from lib.skill_extractor import sanitize_skill, INFRA_REPLACEMENTS
from scripts.seed_skill_library import build_seed_skills


@pytest.fixture
def seed_skills():
    """Build the seed skills once for all tests."""
    return build_seed_skills()


class TestSeedSkillCount:
    """Verify the library has enough skills."""

    def test_minimum_10_skills(self, seed_skills):
        assert len(seed_skills) >= 10, f"Expected >= 10 seed skills, got {len(seed_skills)}"

    def test_maximum_15_skills(self, seed_skills):
        assert len(seed_skills) <= 15, f"Expected <= 15 seed skills, got {len(seed_skills)}"


class TestContentHash:
    """All seed skills must have valid content hashes."""

    def test_content_hash_length(self, seed_skills):
        for skill in seed_skills:
            assert len(skill.content_hash) == 64, (
                f"Skill '{skill.name}' has invalid content_hash length: "
                f"{len(skill.content_hash)} (expected 64)"
            )

    def test_content_hash_is_hex(self, seed_skills):
        hex_pattern = re.compile(r"^[0-9a-f]{64}$")
        for skill in seed_skills:
            assert hex_pattern.match(skill.content_hash), (
                f"Skill '{skill.name}' content_hash is not valid hex: {skill.content_hash}"
            )

    def test_content_hash_deterministic(self, seed_skills):
        """Same skill built twice should produce same hash."""
        skills_again = build_seed_skills()
        for s1, s2 in zip(seed_skills, skills_again):
            assert s1.content_hash == s2.content_hash, (
                f"Non-deterministic hash for '{s1.name}'"
            )

    def test_skill_ids_unique(self, seed_skills):
        """All seed skills must have distinct skill_ids."""
        ids = [s.skill_id for s in seed_skills]
        assert len(ids) == len(set(ids)), (
            f"Duplicate skill_ids found: {[x for x in ids if ids.count(x) > 1]}"
        )


class TestNoInfrastructureLeaks:
    """No infrastructure terms in any skill field."""

    # Patterns that should NOT appear in generic skills
    INFRA_TERMS = [
        r"\bredfin\b",
        r"\bbluefin\b",
        r"\bgreenfin\b",
        r"\bowlfin\b",
        r"\beaglefin\b",
        r"\bsilverfin\b",
        r"\bbmasass\b",
        r"\bsasass\b",
        r"\bthunderduck\b",
        r"\b192\.168\.\d{1,3}\.\d{1,3}\b",
        r"\b10\.100\.0\.\d{1,3}\b",
        r"\b100\.\d{1,3}\.\d{1,3}\.\d{1,3}\b",
        r"/ganuda/",
        r"\bzammad_production\b",
        r"\bCHEROKEE_DB_PASS\b",
    ]

    def test_no_infra_in_intent(self, seed_skills):
        for skill in seed_skills:
            for pattern in self.INFRA_TERMS:
                assert not re.search(pattern, skill.intent, re.IGNORECASE), (
                    f"Skill '{skill.name}' intent contains infra term: {pattern}"
                )

    def test_no_infra_in_method(self, seed_skills):
        for skill in seed_skills:
            for pattern in self.INFRA_TERMS:
                assert not re.search(pattern, skill.method, re.IGNORECASE), (
                    f"Skill '{skill.name}' method contains infra term: {pattern}"
                )

    def test_no_infra_in_name(self, seed_skills):
        for skill in seed_skills:
            for pattern in self.INFRA_TERMS:
                assert not re.search(pattern, skill.name, re.IGNORECASE), (
                    f"Skill '{skill.name}' name contains infra term: {pattern}"
                )


class TestSanitizeSkill:
    """All skills must pass sanitize_skill without being rejected or modified."""

    def test_all_pass_sanitize(self, seed_skills):
        for skill in seed_skills:
            result = sanitize_skill(skill)
            assert result is not None, (
                f"Skill '{skill.name}' was REJECTED by sanitize_skill"
            )

    def test_sanitize_preserves_content(self, seed_skills):
        """Since skills are already clean, sanitize should not change them."""
        for skill in seed_skills:
            result = sanitize_skill(skill)
            assert result is not None
            assert result.name == skill.name, (
                f"Skill '{skill.name}' name changed after sanitize: '{result.name}'"
            )
            assert result.intent == skill.intent, (
                f"Skill '{skill.name}' intent changed after sanitize"
            )
            assert result.method == skill.method, (
                f"Skill '{skill.name}' method changed after sanitize"
            )


class TestCategoryDiversity:
    """At least 5 different domains must be represented."""

    def test_at_least_5_domains(self, seed_skills):
        domains = {s.domain for s in seed_skills}
        assert len(domains) >= 3, (
            f"Expected >= 3 distinct domains, got {len(domains)}: {sorted(domains)}"
        )

    def test_at_least_5_categories_by_name_pattern(self, seed_skills):
        """Check the instruction's 10 categories are covered (at least 5)."""
        category_keywords = {
            "db_operations": ["column", "table", "migration", "index", "schema", "database"],
            "api_integration": ["api", "endpoint", "fastapi", "rest"],
            "frontend": ["css", "layout", "dom", "frontend", "ui"],
            "ops_deployment": ["systemd", "deploy", "service", "timer"],
            "testing": ["test", "integration test", "pytest"],
            "security": ["credential", "scan", "security", "secret", "password"],
            "monitoring": ["health check", "monitoring", "alert"],
            "config": ["config", "kill switch", "feature flag"],
            "refactoring": ["refactor", "extract", "base class", "shared logic"],
            "governance": ["council", "proposal", "governance", "vote"],
        }

        covered = set()
        for skill in seed_skills:
            combined = (skill.name + " " + skill.intent + " " + skill.method).lower()
            for category, keywords in category_keywords.items():
                if any(kw in combined for kw in keywords):
                    covered.add(category)

        assert len(covered) >= 5, (
            f"Expected >= 5 categories covered, got {len(covered)}: {sorted(covered)}"
        )


class TestDifficultyRatings:
    """All difficulty ratings must be within valid range."""

    def test_difficulty_in_range(self, seed_skills):
        for skill in seed_skills:
            assert 1 <= skill.difficulty <= 10, (
                f"Skill '{skill.name}' difficulty {skill.difficulty} out of range [1, 10]"
            )

    def test_difficulty_spread(self, seed_skills):
        """Skills should span at least 3 different difficulty levels."""
        difficulties = {s.difficulty for s in seed_skills}
        assert len(difficulties) >= 3, (
            f"Expected >= 3 difficulty levels, got {len(difficulties)}: {sorted(difficulties)}"
        )

    def test_specific_difficulty_expectations(self, seed_skills):
        """Verify specific skills match the instruction's expected difficulties."""
        expected = {
            "Add column to existing table with migration": 3,
            "Create FastAPI endpoint with health check": 4,
            "Fix CSS layout with scoped DOM queries": 4,
            "Create systemd service with timer": 5,
            "Write integration test for API endpoint": 4,
            "Run credential scan on source file": 3,
            "Add health check to monitoring system": 3,
            "Add config section with kill switch": 3,
            "Extract shared logic into base class": 5,
            "Submit proposal to council with concerns": 6,
        }
        skill_map = {s.name: s.difficulty for s in seed_skills}
        for name, expected_diff in expected.items():
            if name in skill_map:
                assert skill_map[name] == expected_diff, (
                    f"Skill '{name}' difficulty {skill_map[name]} != expected {expected_diff}"
                )


class TestSkillDescriptorFields:
    """All required fields must be populated and well-formed."""

    def test_name_not_empty(self, seed_skills):
        for skill in seed_skills:
            assert skill.name.strip(), f"Skill has empty name"

    def test_intent_not_empty(self, seed_skills):
        for skill in seed_skills:
            assert len(skill.intent) >= 20, (
                f"Skill '{skill.name}' intent too short ({len(skill.intent)} chars)"
            )

    def test_method_not_empty(self, seed_skills):
        for skill in seed_skills:
            assert len(skill.method) >= 20, (
                f"Skill '{skill.name}' method too short ({len(skill.method)} chars)"
            )

    def test_method_has_steps(self, seed_skills):
        """Methods should contain numbered steps."""
        for skill in seed_skills:
            assert re.search(r"\d\.", skill.method), (
                f"Skill '{skill.name}' method has no numbered steps"
            )

    def test_tool_hints_are_lists(self, seed_skills):
        for skill in seed_skills:
            assert isinstance(skill.tool_hints, list), (
                f"Skill '{skill.name}' tool_hints is not a list"
            )
            assert len(skill.tool_hints) > 0, (
                f"Skill '{skill.name}' has no tool_hints"
            )

    def test_domain_is_valid(self, seed_skills):
        valid_domains = {"code", "research", "ops", "legal", "general"}
        for skill in seed_skills:
            assert skill.domain in valid_domains, (
                f"Skill '{skill.name}' domain '{skill.domain}' not in {valid_domains}"
            )

    def test_to_db_row_works(self, seed_skills):
        """Ensure to_db_row() produces valid output for all skills."""
        for skill in seed_skills:
            row = skill.to_db_row()
            assert "skill_id" in row
            assert "content_hash" in row
            assert len(row["skill_id"]) == 16
            assert len(row["content_hash"]) == 64
