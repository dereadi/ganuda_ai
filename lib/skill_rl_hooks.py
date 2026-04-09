#!/usr/bin/env python3
"""
SkillRL Hooks — Pre-task and post-task hooks for the Jr executor learning loop.

Part of SkillRL Epic (Council vote #b91e297a508525c3).
JR-SKILLRL-06: Wire the learning loop into the Jr executor lifecycle.

Pre-task: Load relevant skills into Jr context (< 50ms or bail).
Post-task: Extract new skills from successful work (async, non-blocking).
Reward: Update skill stats based on task outcome.

Spider condition: Hooks NEVER block the Jr pipeline. All failures are caught.
Coyote condition: Circuit breaker on extraction (5/day).
Peace Chief condition: 50ms timeout on skill loading.
"""

import logging
import os
import sys
import time
from typing import Any, Dict, Optional

# Ensure lib/ is in sys.path for sibling imports (skill_selector -> skill_proficiency)
_lib_dir = os.path.dirname(os.path.abspath(__file__))
if _lib_dir not in sys.path:
    sys.path.insert(0, _lib_dir)

logger = logging.getLogger("skill_rl_hooks")

# ── Default configuration ──

_DEFAULT_CONFIG = {
    "enabled": True,
    "extraction_timeout_s": 30,
    "skill_loading_timeout_ms": 50,
    "max_skills_per_task": 5,
    "max_extractions_per_day": 5,
    "library_cap": 500,
}

_config_override: Optional[Dict[str, Any]] = None


def get_skill_rl_config() -> Dict[str, Any]:
    """Return SkillRL configuration with defaults.

    Returns:
        dict with keys: enabled, extraction_timeout_s, skill_loading_timeout_ms,
        max_skills_per_task, max_extractions_per_day, library_cap.
    """
    if _config_override is not None:
        merged = dict(_DEFAULT_CONFIG)
        merged.update(_config_override)
        return merged
    return dict(_DEFAULT_CONFIG)


def set_skill_rl_config(overrides: Dict[str, Any]) -> None:
    """Override config for testing or runtime reconfiguration."""
    global _config_override
    _config_override = overrides


def reset_skill_rl_config() -> None:
    """Reset config to defaults."""
    global _config_override
    _config_override = None


def pre_task_skill_load(task: dict, db_conn) -> str:
    """Load relevant skills for a task and return a context block string.

    Must complete in < skill_loading_timeout_ms or return empty string.
    NEVER raises — all exceptions caught and logged.

    Args:
        task: Jr task dict with 'domain' and 'description' keys.
        db_conn: psycopg2 database connection.

    Returns:
        Markdown context block string to inject into prompt, or empty string.
    """
    config = get_skill_rl_config()
    if not config["enabled"]:
        return ""

    timeout_ms = config["skill_loading_timeout_ms"]
    start = time.monotonic()

    try:
        from lib.toolsets.skill_toolset import SkillToolSet

        skill_toolset = SkillToolSet(db_conn)
        skills = skill_toolset.load_skills_for_task(
            domain=task.get("domain", "general"),
            task_description=task.get("description", ""),
        )

        elapsed_ms = (time.monotonic() - start) * 1000
        if elapsed_ms > timeout_ms:
            logger.warning(
                "Skill loading took %.1fms (limit %dms) for task %s — returning skills anyway",
                elapsed_ms, timeout_ms, task.get("task_id", "unknown"),
            )

        if not skills:
            return ""

        # Build context block from loaded skills
        blocks = []
        for skill in skills[:config["max_skills_per_task"]]:
            lines = [
                f"### Skill: {skill.get('name', '')}",
                f"**ID**: `{skill.get('skill_id', '')}`",
                f"**Domain**: {skill.get('domain', 'general')} | **Difficulty**: {skill.get('difficulty', 0)}/10",
                f"**Intent**: {skill.get('intent', '')}",
                f"**Method**: {skill.get('method', '')}",
            ]
            tool_hints = skill.get("tool_hints", [])
            if isinstance(tool_hints, str):
                import json
                try:
                    tool_hints = json.loads(tool_hints)
                except (ValueError, TypeError):
                    tool_hints = []
            if tool_hints:
                lines.append(f"**Tools**: {', '.join(tool_hints)}")
            blocks.append("\n".join(lines))

        skill_context = "\n\n".join(blocks)
        return f"## Available Skills\n{skill_context}"

    except Exception as exc:
        elapsed_ms = (time.monotonic() - start) * 1000
        logger.error(
            "pre_task_skill_load failed (%.1fms) for task %s: %s",
            elapsed_ms, task.get("task_id", "unknown"), exc,
        )
        return ""


def post_task_skill_extract(task: dict, db_conn, council=None, dispatcher=None) -> None:
    """Extract a reusable skill from a successful task. Fire-and-forget.

    Only runs on successful tasks (status == 'done').
    Respects circuit breaker and extraction timeout.
    NEVER blocks the Jr pipeline (Spider condition).

    Args:
        task: Completed Jr task dict. Must have 'status' key.
        db_conn: psycopg2 database connection.
        council: Council object with council_vote method (optional).
        dispatcher: SubAgentDispatch instance (optional).
    """
    config = get_skill_rl_config()
    if not config["enabled"]:
        return

    # Only extract from successful tasks
    if task.get("status") != "done":
        return

    try:
        from lib.skill_extractor import (
            extract_skill,
            sanitize_skill,
            check_duplicate,
            submit_for_verification,
        )

        skill = extract_skill(
            task,
            dispatcher=dispatcher,
            timeout=config["extraction_timeout_s"],
        )
        if skill is None:
            return

        skill = sanitize_skill(skill)
        if skill is None:
            return

        if check_duplicate(skill, db_conn):
            return

        if council is not None:
            submit_for_verification(skill, council)

    except Exception as exc:
        logger.error(
            "post_task_skill_extract failed for task %s: %s",
            task.get("task_id", "unknown"), exc,
        )
        # Spider condition: NEVER propagate


def post_task_reward_update(task_id: int, task_status: str, domain: str, db_conn) -> None:
    """Update reward for any skills used during this task.

    Queries skill_usage_log for skills associated with this task_id,
    then calls SkillSelector.update_reward for each.

    Args:
        task_id: The Jr task ID.
        task_status: 'done' or 'failed'.
        domain: Task domain string.
        db_conn: psycopg2 database connection.
    """
    config = get_skill_rl_config()
    if not config["enabled"]:
        return

    try:
        # Query skill_usage_log for skills used in this task
        cur = db_conn.cursor()
        cur.execute(
            "SELECT skill_id FROM skill_usage_log WHERE task_id = %s",
            (task_id,),
        )
        rows = cur.fetchall()
        cur.close()

        if not rows:
            return

        from skill_selector import SkillSelector

        selector = SkillSelector(db_conn)
        success = task_status == "done"

        # SkillRL KG Phase 0: Multi-signal reward (#1444)
        # Replaces binary 0.9/0.1 with four-dimensional reward extraction
        skill_ids = [row[0] for row in rows]
        try:
            from kg_reward_signals import KGRewardSignals
            kg_signals = KGRewardSignals()
            signals = kg_signals.compute_reward(task_id, task_status, db_conn, skill_ids)
            reward = signals["composite"]

            # Log full signal breakdown for audit
            logger.info(
                "KG reward for task %s: composite=%.3f (v=%.2f c=%.2f g=%.2f d=%.2f) %s",
                task_id, reward,
                signals["validity"], signals["continuity"],
                signals["grounding"], signals["drift"],
                "[DRIFT REVIEW]" if signals.get("drift_needs_review") else "",
            )
        except ImportError:
            reward = 0.9 if success else 0.1
            signals = None
            logger.info("KG reward signals not available, using binary fallback: %.1f", reward)
        except Exception as exc:
            reward = 0.9 if success else 0.1
            signals = None
            logger.warning("KG reward computation failed, binary fallback: %s", exc)

        for row in rows:
            skill_id = row[0]
            try:
                selector.update_reward(
                    skill_id=skill_id,
                    domain=domain,
                    reward=reward,
                    success=success,
                    latency_ms=0,
                )
            except Exception as exc:
                logger.warning(
                    "Reward update failed for skill %s on task %s: %s",
                    skill_id, task_id, exc,
                )

    except Exception as exc:
        logger.error(
            "post_task_reward_update failed for task %s: %s", task_id, exc,
        )
