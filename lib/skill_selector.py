"""
skill_selector: UCB1 Bandit + Curriculum Weighting for SkillRL
Cherokee AI Federation — SkillRL-05

Selects which skills to inject into Jr task context using:
- UCB1 (Upper Confidence Bound) for exploration/exploitation balance
- Inverse proficiency weighting so weak categories get more practice
- Auto-quarantine (Coyote condition) for consistently failing skills
- Content hash integrity check (Eagle Eye condition)

From the Agentic Proposing paper: UCB1 = mean_reward + c * sqrt(ln(N) / n)

Usage:
    from ganuda_db import get_connection
    conn = get_connection()
    selector = SkillSelector(conn)
    skills = selector.select_skills("general", "Write a test for X")
"""

import json
import logging
import math
from datetime import datetime

import psycopg2.extras
import requests

from skill_proficiency import SkillProficiency

logger = logging.getLogger(__name__)

# UCB1 exploration constant (sqrt(2), standard)
EXPLORATION_WEIGHT = 1.41

# Coyote condition: auto-quarantine thresholds
QUARANTINE_THRESHOLD = 0.3
QUARANTINE_MIN_USES = 5

# Category inference mappings
_CATEGORY_HINTS = {
    "db_operations": ["psycopg2", "sql", "database", "postgres", "query", "cursor"],
    "api_integration": ["requests", "api", "http", "rest", "fetch", "endpoint"],
    "frontend": ["css", "html", "react", "template", "dom", "style"],
    "ops_deployment": ["systemd", "deploy", "caddy", "nginx", "docker", "service"],
    "testing": ["pytest", "test", "assert", "mock", "unittest", "coverage"],
}


class SkillSelector:
    """UCB1 bandit skill selector with curriculum weighting."""

    def __init__(self, conn):
        """
        Initialize with a psycopg2 database connection.

        Args:
            conn: A psycopg2 connection object (caller manages lifecycle).
        """
        self.conn = conn
        self.proficiency = SkillProficiency(conn)

    def select_skills(self, domain: str, task_description: str, max_skills: int = 5) -> list:
        """
        Select top-k skills for a domain using UCB1 + curriculum weighting.

        Args:
            domain: Skill domain (e.g., 'general', 'code', 'ops').
            task_description: Description of the task (for future relevance scoring).
            max_skills: Maximum number of skills to return.

        Returns:
            list[dict]: Selected skills sorted by final_score descending.
        """
        cur = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            """
            SELECT skill_id, name, intent, method, difficulty, tool_hints,
                   domain, content_hash, total_uses, successful_uses,
                   total_reward, avg_latency_ms, status
            FROM skill_library
            WHERE status = 'active' AND domain IN (%s, 'general')
            """,
            (domain,),
        )
        rows = cur.fetchall()
        cur.close()

        if not rows:
            return []

        # Total uses across all fetched skills (for UCB1 N)
        total_n = sum(r["total_uses"] for r in rows)
        if total_n == 0:
            total_n = 1  # avoid ln(0)

        scored = []
        for row in rows:
            skill = dict(row)

            # Eagle Eye integrity check: verify content_hash
            if not self._verify_integrity(skill):
                logger.warning(
                    "Eagle Eye: content_hash mismatch for skill %s (%s). Auto-quarantining.",
                    skill["skill_id"], skill["name"],
                )
                self._quarantine_skill(skill["skill_id"])
                continue

            n = skill["total_uses"]
            if n == 0:
                # Unseen skill gets maximum exploration bonus
                ucb_score = 1.0 + EXPLORATION_WEIGHT * math.sqrt(math.log(max(total_n, 1)))
            else:
                mean_reward = float(skill["total_reward"]) / float(n)
                ucb_score = mean_reward + EXPLORATION_WEIGHT * math.sqrt(
                    math.log(total_n) / n
                )

            # Curriculum weight: weak categories get boosted
            category = self._infer_category(skill)
            prof_score = self.proficiency.get_score(domain, category)
            curriculum_weight = 1.0 + (1.0 - prof_score)

            final_score = ucb_score * curriculum_weight

            skill["ucb_score"] = ucb_score
            skill["curriculum_weight"] = curriculum_weight
            skill["final_score"] = final_score
            skill["category"] = category

            scored.append(skill)

        # Sort by final_score descending, return top-k
        scored.sort(key=lambda s: s["final_score"], reverse=True)
        return scored[:max_skills]

    def select_skills_semantic(self, task_description: str, max_skills: int = 5) -> list:
        """
        Select skills by embedding similarity to the task description.
        Combines semantic relevance with UCB1 scoring.

        This is the Trace2Skill-validated approach: match new tasks to
        skills distilled from similar past execution traces using continuous
        embeddings, not text matching.

        Args:
            task_description: The task to find skills for.
            max_skills: Maximum number of skills to return.

        Returns:
            list[dict]: Selected skills sorted by combined score.
        """
        # Get task embedding
        try:
            resp = requests.post(
                "http://192.168.132.224:8003/v1/embeddings",
                json={"texts": [task_description[:2000]]},
                timeout=10,
            )
            resp.raise_for_status()
            task_embedding = resp.json()["embeddings"][0]
        except Exception as e:
            logger.warning(f"Semantic skill selection failed (embedding): {e}. Falling back to domain selection.")
            return self.select_skills("general", task_description, max_skills)

        # Find skills with closest method_embedding via pgvector
        cur = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SET ivfflat.probes = 10")
        cur.execute(
            """
            SELECT skill_id, name, intent, method, difficulty, tool_hints,
                   domain, content_hash, total_uses, successful_uses,
                   total_reward, avg_latency_ms, status, transferability, source_type,
                   1 - (method_embedding <=> %s::vector) as semantic_similarity
            FROM skill_library
            WHERE status = 'active' AND method_embedding IS NOT NULL
            ORDER BY method_embedding <=> %s::vector
            LIMIT %s
            """,
            (str(task_embedding), str(task_embedding), max_skills * 3),  # Fetch 3x for UCB1 filtering
        )
        rows = cur.fetchall()
        cur.close()

        if not rows:
            return self.select_skills("general", task_description, max_skills)

        # Score with UCB1 + semantic similarity + transferability
        total_n = sum(r["total_uses"] for r in rows)
        if total_n == 0:
            total_n = 1

        scored = []
        for row in rows:
            skill = dict(row)
            n = skill["total_uses"]
            semantic_sim = float(skill.get("semantic_similarity", 0))
            transferability = float(skill.get("transferability", 0))

            if n == 0:
                ucb_score = 1.0 + EXPLORATION_WEIGHT * math.sqrt(math.log(max(total_n, 1)))
            else:
                mean_reward = float(skill["total_reward"]) / float(n)
                ucb_score = mean_reward + EXPLORATION_WEIGHT * math.sqrt(
                    math.log(total_n) / n
                )

            # Combined score: semantic relevance × UCB1 × transferability boost
            # Semantic similarity is the primary signal (Trace2Skill validated)
            # UCB1 handles exploration/exploitation
            # Transferability boosts generalizable skills
            transfer_boost = 1.0 + (transferability * 0.5)
            final_score = semantic_sim * ucb_score * transfer_boost

            skill["ucb_score"] = ucb_score
            skill["semantic_similarity"] = semantic_sim
            skill["transfer_boost"] = transfer_boost
            skill["final_score"] = final_score
            skill["selection_method"] = "semantic"

            scored.append(skill)

        scored.sort(key=lambda s: s["final_score"], reverse=True)
        selected = scored[:max_skills]

        if selected:
            logger.info(
                f"Semantic skill selection: {len(selected)} skills, "
                f"top={selected[0]['name']} (sim={selected[0]['semantic_similarity']:.3f}, "
                f"score={selected[0]['final_score']:.3f})"
            )

        return selected

    def update_reward(
        self,
        skill_id: str,
        domain: str,
        reward: float,
        success: bool,
        latency_ms: int = 0,
    ) -> None:
        """
        Update skill stats after use and check for auto-quarantine.

        Args:
            skill_id: The skill's ID.
            domain: Skill domain.
            reward: Reward signal (0.0 to 1.0).
            success: Whether the task succeeded.
            latency_ms: Execution latency in milliseconds.
        """
        now = datetime.now()
        cur = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # Update skill_library stats
        cur.execute(
            """
            UPDATE skill_library SET
                total_uses = total_uses + 1,
                successful_uses = successful_uses + %s,
                total_reward = total_reward + %s,
                avg_latency_ms = CASE
                    WHEN total_uses = 0 THEN %s
                    ELSE (avg_latency_ms * total_uses + %s) / (total_uses + 1)
                END,
                last_used = %s
            WHERE skill_id = %s
            RETURNING total_uses, successful_uses, name, domain, tool_hints
            """,
            (
                1 if success else 0,
                reward,
                latency_ms,
                latency_ms,
                now,
                skill_id,
            ),
        )
        updated = cur.fetchone()
        self.conn.commit()

        if updated is None:
            logger.error("update_reward: skill_id %s not found in skill_library", skill_id)
            cur.close()
            return

        # Update proficiency via EMA
        category = self._infer_category(dict(updated))
        self.proficiency.update(domain, category, reward, success)

        # Log to skill_usage_log
        cur.execute(
            """
            INSERT INTO skill_usage_log (skill_id, domain, reward, success, latency_ms, used_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (skill_id, domain, reward, success, latency_ms, now),
        )
        self.conn.commit()

        # Coyote condition: auto-quarantine check
        total_uses = updated["total_uses"]
        successful_uses = updated["successful_uses"]

        if total_uses >= QUARANTINE_MIN_USES:
            success_rate = successful_uses / total_uses
            if success_rate < QUARANTINE_THRESHOLD:
                logger.warning(
                    "Coyote quarantine: skill %s (%s) success_rate=%.2f after %d uses. Quarantining.",
                    skill_id, updated["name"], success_rate, total_uses,
                )
                self._quarantine_skill(skill_id)

        cur.close()

    def get_stats(self, domain: str) -> list:
        """
        Return all skills for a domain with scores for monitoring.

        Args:
            domain: Skill domain to query.

        Returns:
            list[dict]: Skills with UCB scores, proficiency, and usage counts.
        """
        cur = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            """
            SELECT skill_id, name, intent, domain, tool_hints, status,
                   total_uses, successful_uses, total_reward, avg_latency_ms, last_used
            FROM skill_library
            WHERE domain IN (%s, 'general')
            ORDER BY total_uses DESC
            """,
            (domain,),
        )
        rows = cur.fetchall()
        cur.close()

        total_n = sum(r["total_uses"] for r in rows)
        if total_n == 0:
            total_n = 1

        result = []
        for row in rows:
            skill = dict(row)
            n = skill["total_uses"]
            if n == 0:
                ucb_score = 1.0 + EXPLORATION_WEIGHT * math.sqrt(math.log(max(total_n, 1)))
            else:
                mean_reward = float(skill["total_reward"]) / float(n)
                ucb_score = mean_reward + EXPLORATION_WEIGHT * math.sqrt(
                    math.log(total_n) / n
                )

            category = self._infer_category(skill)
            prof_score = self.proficiency.get_score(domain, category)
            curriculum_weight = 1.0 + (1.0 - prof_score)

            skill["ucb_score"] = ucb_score
            skill["curriculum_weight"] = curriculum_weight
            skill["final_score"] = ucb_score * curriculum_weight
            skill["category"] = category
            skill["proficiency_score"] = prof_score

            result.append(skill)

        return result

    def _infer_category(self, skill: dict) -> str:
        """
        Infer skill category from tool_hints and domain.

        Args:
            skill: Skill dict with tool_hints and domain fields.

        Returns:
            str: Inferred category string.
        """
        hints = skill.get("tool_hints", [])
        if isinstance(hints, str):
            try:
                hints = json.loads(hints)
            except (json.JSONDecodeError, TypeError):
                hints = []

        hints_lower = [h.lower() for h in hints]

        for category, keywords in _CATEGORY_HINTS.items():
            for keyword in keywords:
                for hint in hints_lower:
                    if keyword in hint:
                        return category

        # Default to domain
        return skill.get("domain", "general")

    def _verify_integrity(self, skill: dict) -> bool:
        """
        Eagle Eye: verify content_hash matches computed hash.

        Args:
            skill: Skill dict from DB with intent, method, tool_hints, content_hash.

        Returns:
            bool: True if hash matches, False if corrupted.
        """
        intent = skill.get("intent", "")
        method = skill.get("method", "")
        tool_hints = skill.get("tool_hints", [])
        if isinstance(tool_hints, str):
            try:
                tool_hints = json.loads(tool_hints)
            except (json.JSONDecodeError, TypeError):
                tool_hints = []

        import hashlib
        raw = intent + "||" + method + "||" + "|".join(sorted(tool_hints))
        computed = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        return computed == skill.get("content_hash", "")

    def _quarantine_skill(self, skill_id: str) -> None:
        """
        Set a skill's status to 'quarantine' in the database.

        Args:
            skill_id: The skill's ID to quarantine.
        """
        cur = self.conn.cursor()
        cur.execute(
            "UPDATE skill_library SET status = 'quarantine' WHERE skill_id = %s",
            (skill_id,),
        )
        self.conn.commit()
        cur.close()
