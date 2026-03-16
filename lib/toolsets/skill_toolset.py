"""SkillToolSet — SkillRL learned skills as callable tools.

Read tools: list_available_skills, apply_skill, get_skill_method

Exposes learned skills from the skill_library to Jr task execution via
the ToolSet ring pattern. Includes Peace Chief library cap enforcement
(max 500 active skills).

Council vote #b91e297a508525c3 (SkillRL Epic).
SkillRL-07: ToolSet Ring.
"""

import json
import logging
from .base import ToolSet, ToolDescriptor, get_db_connection

logger = logging.getLogger(__name__)


class SkillToolSet(ToolSet):
    domain = "skillrl"

    def __init__(self, conn=None):
        """
        Initialize SkillToolSet.

        Args:
            conn: Optional psycopg2 connection. If None, uses get_db_connection()
                  per-call (same pattern as ThermalToolSet/KanbanToolSet).
        """
        self._ext_conn = conn
        self._loaded_skills = {}  # skill_id -> skill dict

    @property
    def conn(self):
        """Get DB connection — use provided or create per-call."""
        if self._ext_conn is not None:
            return self._ext_conn
        return get_db_connection()

    def _get_selector(self):
        """Lazy-init selector with current connection."""
        import sys
        import os
        lib_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if lib_dir not in sys.path:
            sys.path.insert(0, lib_dir)
        from skill_selector import SkillSelector
        return SkillSelector(self.conn)

    def get_tools(self) -> list:
        return [
            ToolDescriptor(
                name="list_available_skills",
                description=(
                    "List all loaded skills with UCB scores, proficiency, "
                    "and difficulty. Use to see what learned patterns are "
                    "available for the current task."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "domain_filter": {
                            "type": "string",
                            "description": "Optional domain to filter by",
                        },
                    },
                },
                safety_class="read",
            ),
            ToolDescriptor(
                name="apply_skill",
                description=(
                    "Apply a learned skill's method to the current context. "
                    "Returns actionable instructions the Jr can follow."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "skill_id": {
                            "type": "string",
                            "description": "The skill ID to apply",
                        },
                        "context": {
                            "type": "string",
                            "description": "Current task context to apply the skill to",
                        },
                    },
                    "required": ["skill_id"],
                },
                safety_class="read",
            ),
            ToolDescriptor(
                name="get_skill_method",
                description=(
                    "Get full detail for a skill: method, tool hints, "
                    "difficulty, compound status, parent skills."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "skill_id": {
                            "type": "string",
                            "description": "The skill ID to inspect",
                        },
                    },
                    "required": ["skill_id"],
                },
                safety_class="read",
            ),
        ]

    def load_skills_for_task(self, domain: str, task_description: str) -> list:
        """
        Pre-load relevant skills via selector before task execution.

        Enforces Peace Chief library cap (max 500 active skills).
        Stores selected skills in _loaded_skills dict.

        Args:
            domain: Skill domain (e.g., 'general', 'code', 'ops').
            task_description: Description of the task.

        Returns:
            list[dict]: Selected skills.
        """
        # Peace Chief condition: library cap enforcement
        self._enforce_library_cap()

        # Select skills via UCB1 bandit
        selector = self._get_selector()
        skills = selector.select_skills(domain, task_description)

        # Store in _loaded_skills
        self._loaded_skills = {}
        for skill in skills:
            self._loaded_skills[skill["skill_id"]] = skill

        logger.info(
            "[SKILL_TOOLSET] Loaded %d skills for domain=%s",
            len(self._loaded_skills), domain,
        )
        return skills

    def _enforce_library_cap(self):
        """Peace Chief condition: auto-retire lowest reward skill if over 500 active."""
        try:
            cur = self.conn.cursor()
            cur.execute(
                "SELECT COUNT(*) FROM skill_library WHERE status = 'active'"
            )
            active_count = cur.fetchone()[0]

            if active_count > 500:
                cur.execute("""
                    UPDATE skill_library SET status = 'retired',
                        retired_at = NOW(), retire_reason = 'cap_overflow'
                    WHERE id = (
                        SELECT id FROM skill_library
                        WHERE status = 'active' AND total_uses > 10
                        ORDER BY total_reward / GREATEST(total_uses, 1) ASC
                        LIMIT 1
                    )
                """)
                self.conn.commit()
                logger.info(
                    "[SKILL_TOOLSET] Library cap: retired 1 skill (was %d active)",
                    active_count,
                )
            cur.close()
        except Exception as e:
            logger.warning("[SKILL_TOOLSET] Library cap check failed: %s", e)

    def list_available_skills(self, domain_filter: str = "") -> dict:
        """List all loaded skills with scores."""
        if not self._loaded_skills:
            return {
                "count": 0,
                "skills": [],
                "message": (
                    "No skills loaded. Call load_skills_for_task first, "
                    "or no active skills match the current domain."
                ),
            }

        skills_out = []
        for sid, skill in self._loaded_skills.items():
            if domain_filter and skill.get("domain") != domain_filter:
                continue
            skills_out.append({
                "skill_id": sid,
                "name": skill.get("name", ""),
                "intent": skill.get("intent", ""),
                "difficulty": skill.get("difficulty", 0),
                "domain": skill.get("domain", "general"),
                "ucb_score": round(skill.get("ucb_score", 0.0), 4),
                "final_score": round(skill.get("final_score", 0.0), 4),
                "total_uses": skill.get("total_uses", 0),
                "successful_uses": skill.get("successful_uses", 0),
            })

        return {
            "count": len(skills_out),
            "skills": skills_out,
        }

    def apply_skill(self, skill_id: str, context: str = "") -> dict:
        """Apply a skill's method to the current context."""
        skill = self._loaded_skills.get(skill_id)
        if not skill:
            return {
                "error": f"Skill '{skill_id}' not found in loaded skills. "
                         f"Available: {list(self._loaded_skills.keys())}",
            }

        tool_hints = skill.get("tool_hints", [])
        if isinstance(tool_hints, str):
            try:
                tool_hints = json.loads(tool_hints)
            except (json.JSONDecodeError, TypeError):
                tool_hints = []

        return {
            "skill_id": skill_id,
            "name": skill.get("name", ""),
            "method": skill.get("method", ""),
            "tool_hints": tool_hints,
            "context": context,
            "instructions": (
                f"Apply the following method to your current task:\n\n"
                f"{skill.get('method', '')}\n\n"
                f"Context: {context or 'No specific context provided.'}\n\n"
                f"Suggested tools: {', '.join(tool_hints) if tool_hints else 'none'}"
            ),
        }

    def get_skill_method(self, skill_id: str) -> dict:
        """Get full skill detail."""
        skill = self._loaded_skills.get(skill_id)
        if not skill:
            return {
                "error": f"Skill '{skill_id}' not found in loaded skills. "
                         f"Available: {list(self._loaded_skills.keys())}",
            }

        tool_hints = skill.get("tool_hints", [])
        if isinstance(tool_hints, str):
            try:
                tool_hints = json.loads(tool_hints)
            except (json.JSONDecodeError, TypeError):
                tool_hints = []

        parent_skills = skill.get("parent_skills", [])
        if isinstance(parent_skills, str):
            try:
                parent_skills = json.loads(parent_skills)
            except (json.JSONDecodeError, TypeError):
                parent_skills = []

        return {
            "skill_id": skill_id,
            "name": skill.get("name", ""),
            "intent": skill.get("intent", ""),
            "method": skill.get("method", ""),
            "difficulty": skill.get("difficulty", 0),
            "domain": skill.get("domain", "general"),
            "tool_hints": tool_hints,
            "is_compound": skill.get("is_compound", False),
            "parent_skills": parent_skills,
            "total_uses": skill.get("total_uses", 0),
            "successful_uses": skill.get("successful_uses", 0),
        }
