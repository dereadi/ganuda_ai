#!/usr/bin/env python3
"""
SkillDescriptor — Atomic unit of learned capability for SkillRL.

Provides a standard format for representing skills, composing them,
hashing them, and converting them for tool injection.

Part of SkillRL Epic (Council vote #b91e297a508525c3).
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
import hashlib
import json


@dataclass
class SkillDescriptor:
    """A learned skill extracted from successful Jr task completions."""

    name: str
    intent: str           # WHY the pattern works (reasoning principle)
    method: str           # HOW to apply the pattern (construction procedure)
    difficulty: int       # 1-10 complexity rating
    tool_hints: List[str] = field(default_factory=list)
    domain: str = "general"  # code, research, ops, legal, general
    is_compound: bool = False
    parent_skills: List[str] = field(default_factory=list)
    source_task_id: Optional[int] = None

    @property
    def skill_id(self) -> str:
        """Deterministic ID: SHA256(intent || method)[:16]. Same pattern = same skill."""
        raw = self.intent + "||" + self.method
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

    @property
    def content_hash(self) -> str:
        """Integrity hash including tool_hints for Eagle Eye validation."""
        raw = self.intent + "||" + self.method + "||" + "|".join(sorted(self.tool_hints))
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def to_tool_description(self) -> Dict[str, Any]:
        """Convert to OpenAI function-calling format for context injection."""
        return {
            "type": "function",
            "function": {
                "name": self.name.lower().replace(" ", "_"),
                "description": self.intent,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "method": {
                            "type": "string",
                            "description": self.method,
                        }
                    },
                    "required": ["method"],
                },
            },
        }

    def to_context_block(self) -> str:
        """Render as skill MD block for context window."""
        lines = [
            f"### Skill: {self.name}",
            f"**ID**: `{self.skill_id}`",
            f"**Domain**: {self.domain} | **Difficulty**: {self.difficulty}/10",
            f"**Intent**: {self.intent}",
            f"**Method**: {self.method}",
        ]
        if self.tool_hints:
            lines.append(f"**Tools**: {', '.join(self.tool_hints)}")
        if self.is_compound and self.parent_skills:
            lines.append(f"**Composed from**: {', '.join(self.parent_skills)}")
        return "\n".join(lines)

    def to_db_row(self) -> Dict[str, Any]:
        """Dict ready for INSERT into skill_library table."""
        return {
            "skill_id": self.skill_id,
            "name": self.name,
            "intent": self.intent,
            "method": self.method,
            "difficulty": self.difficulty,
            "tool_hints": json.dumps(self.tool_hints),
            "domain": self.domain,
            "is_compound": self.is_compound,
            "parent_skills": json.dumps(self.parent_skills),
            "source_task_id": self.source_task_id,
            "content_hash": self.content_hash,
        }

    @classmethod
    def from_db_row(cls, row: Dict[str, Any]) -> "SkillDescriptor":
        """Reconstruct a SkillDescriptor from a DB row dict."""
        tool_hints = row.get("tool_hints", "[]")
        if isinstance(tool_hints, str):
            tool_hints = json.loads(tool_hints)

        parent_skills = row.get("parent_skills", "[]")
        if isinstance(parent_skills, str):
            parent_skills = json.loads(parent_skills)

        return cls(
            name=row["name"],
            intent=row["intent"],
            method=row["method"],
            difficulty=row["difficulty"],
            tool_hints=tool_hints,
            domain=row.get("domain", "general"),
            is_compound=row.get("is_compound", False),
            parent_skills=parent_skills,
            source_task_id=row.get("source_task_id"),
        )


def compose_skills(
    skills: List[SkillDescriptor],
    name: str,
    intent: str,
    method: str,
) -> SkillDescriptor:
    """Combine 2+ atomic skills into a compound skill.

    Difficulty = max(parent difficulties) + len(parents) - 1, capped at 10.
    Tool hints are merged (deduplicated). Parent skill_ids recorded.
    """
    if len(skills) < 2:
        raise ValueError("compose_skills requires at least 2 skills")

    raw_difficulty = max(s.difficulty for s in skills) + len(skills) - 1
    difficulty = min(raw_difficulty, 10)

    # Merge tool hints, preserving order but deduplicating
    seen = set()
    merged_hints = []
    for s in skills:
        for hint in s.tool_hints:
            if hint not in seen:
                seen.add(hint)
                merged_hints.append(hint)

    # Collect all domains; use most common or first
    domains = [s.domain for s in skills]
    domain = max(set(domains), key=domains.count)

    return SkillDescriptor(
        name=name,
        intent=intent,
        method=method,
        difficulty=difficulty,
        tool_hints=merged_hints,
        domain=domain,
        is_compound=True,
        parent_skills=[s.skill_id for s in skills],
        source_task_id=None,
    )
