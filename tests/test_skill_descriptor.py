#!/usr/bin/env python3
"""
Tests for SkillDescriptor — SkillRL-02.

6 tests covering: deterministic IDs, content hashing, composition,
round-trip serialization, and tool description format.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from lib.skill_descriptor import SkillDescriptor, compose_skills


def _make_skill(name="test_skill", intent="Test intent", method="Test method",
                difficulty=3, tool_hints=None, domain="code"):
    return SkillDescriptor(
        name=name,
        intent=intent,
        method=method,
        difficulty=difficulty,
        tool_hints=tool_hints or ["bash", "grep"],
        domain=domain,
        source_task_id=42,
    )


class TestSkillDescriptor:
    """All 6 required tests for SkillRL-02."""

    def test_deterministic_skill_id(self):
        """Same intent+method always produces same skill_id."""
        s1 = _make_skill(intent="find files", method="use glob")
        s2 = _make_skill(intent="find files", method="use glob",
                         name="different_name", tool_hints=["other"])
        assert s1.skill_id == s2.skill_id
        assert len(s1.skill_id) == 16

    def test_different_content_different_id(self):
        """Changing intent changes skill_id."""
        s1 = _make_skill(intent="find files", method="use glob")
        s2 = _make_skill(intent="search code", method="use glob")
        assert s1.skill_id != s2.skill_id

    def test_content_hash_includes_tool_hints(self):
        """Changing tool_hints changes content_hash but NOT skill_id."""
        s1 = _make_skill(intent="find files", method="use glob",
                         tool_hints=["bash"])
        s2 = _make_skill(intent="find files", method="use glob",
                         tool_hints=["bash", "grep"])
        # Same intent+method => same skill_id
        assert s1.skill_id == s2.skill_id
        # Different tool_hints => different content_hash
        assert s1.content_hash != s2.content_hash

    def test_composition(self):
        """Two difficulty-3 skills compose into difficulty-4 compound with both parent IDs."""
        s1 = _make_skill(name="skill_a", intent="intent_a", method="method_a",
                         difficulty=3, tool_hints=["bash"])
        s2 = _make_skill(name="skill_b", intent="intent_b", method="method_b",
                         difficulty=3, tool_hints=["grep"])

        compound = compose_skills(
            [s1, s2],
            name="compound_skill",
            intent="combined intent",
            method="combined method",
        )

        # max(3,3) + 2 - 1 = 4
        assert compound.difficulty == 4
        assert compound.is_compound is True
        assert s1.skill_id in compound.parent_skills
        assert s2.skill_id in compound.parent_skills
        assert len(compound.parent_skills) == 2
        # Tool hints merged
        assert "bash" in compound.tool_hints
        assert "grep" in compound.tool_hints

    def test_round_trip(self):
        """from_db_row(skill.to_db_row()) produces identical descriptor."""
        original = _make_skill()
        row = original.to_db_row()
        restored = SkillDescriptor.from_db_row(row)

        assert restored.name == original.name
        assert restored.intent == original.intent
        assert restored.method == original.method
        assert restored.difficulty == original.difficulty
        assert restored.tool_hints == original.tool_hints
        assert restored.domain == original.domain
        assert restored.is_compound == original.is_compound
        assert restored.parent_skills == original.parent_skills
        assert restored.source_task_id == original.source_task_id
        # Derived properties must also match
        assert restored.skill_id == original.skill_id
        assert restored.content_hash == original.content_hash

    def test_tool_description_format(self):
        """to_tool_description() returns valid OpenAI function format."""
        s = _make_skill(name="file search", intent="Find relevant files",
                        method="Use glob patterns")
        desc = s.to_tool_description()

        assert desc["type"] == "function"
        assert "function" in desc
        func = desc["function"]
        assert "name" in func
        assert "description" in func
        assert "parameters" in func
        assert func["parameters"]["type"] == "object"
        assert "properties" in func["parameters"]
        assert "required" in func["parameters"]
        # Name should be snake_case
        assert func["name"] == "file_search"
        assert func["description"] == "Find relevant files"
