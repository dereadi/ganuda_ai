#!/usr/bin/env python3
"""
Skill Extractor — Post-task analysis to harvest reusable skills from completed Jr work.

Part of SkillRL Epic (Council vote #b91e297a508525c3).
JR-SKILLRL-03: The INPUT side of the learning loop.

DC-9: Internal reflection stays local (redfin_vllm).
Spider condition: 30-second timeout, non-blocking. Failure never blocks Jr pipeline.
Coyote condition: Circuit breaker at 5 extractions per 24-hour window.
"""

import json
import logging
import re
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from lib.skill_descriptor import SkillDescriptor

logger = logging.getLogger("skill_extractor")

# ── NEVER_SEND patterns: hard rejection if found in skill intent/method ──
NEVER_SEND_PATTERNS = [
    r"CHEROKEE_DB_PASS",
    r"secrets\.env",
    r"\.pem\b",
    r"-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----",
    r"password\s*=\s*\S+",
]

# ── Infrastructure terms to strip (replace with generic placeholders) ──
INFRA_REPLACEMENTS = [
    # Node names
    (r"\bredfin\b", "primary GPU node"),
    (r"\bbluefin\b", "database node"),
    (r"\bgreenfin\b", "bridge node"),
    (r"\bowlfin\b", "DMZ web node"),
    (r"\beaglefin\b", "DMZ backup node"),
    (r"\bsilverfin\b", "identity node"),
    (r"\bbmasass\b", "mobile compute node"),
    (r"\bsasass2?\b", "auxiliary compute node"),
    (r"\bthunderduck\b", "auxiliary compute node"),
    # LAN IPs
    (r"\b192\.168\.\d{1,3}\.\d{1,3}\b", "<LAN_IP>"),
    # WireGuard IPs
    (r"\b10\.100\.0\.\d{1,3}\b", "<WG_IP>"),
    # Tailscale IPs
    (r"\b100\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", "<TS_IP>"),
    # Internal paths
    (r"/ganuda/[\w/.\-]+", "<internal_path>"),
]

# ── Extraction prompt template ──
EXTRACTION_PROMPT = """You are a skill extractor for a software federation.

A Jr engineer just completed a task successfully. Analyze the task
and its outcome to determine if a REUSABLE SKILL emerged.

A skill is reusable if:
1. The SAME PATTERN could apply to future, different tasks
2. It's not just "I edited a file" — it's a transferable technique
3. It has clear intent (WHY), method (HOW), and tool requirements
4. Difficulty is >= 3 (trivial patterns are not worth tracking)

Task Title: {title}
Task Description: {description}
Acceptance Criteria: {acceptance_criteria}
Files Modified: {files_modified}
Steps Completed: {steps_summary}

If a reusable skill emerged, respond with JSON:
{{
    "skill_found": true,
    "name": "short descriptive name",
    "intent": "the reasoning principle — WHY this pattern works",
    "method": "step-by-step procedure — HOW to apply this pattern",
    "difficulty": <3-10>,
    "tool_hints": ["tool1", "tool2"],
    "domain": "code|research|ops|legal|general",
    "reasoning": "why you believe this is reusable"
}}

If NO reusable skill emerged, respond:
{{
    "skill_found": false,
    "reasoning": "why no skill was extracted"
}}

IMPORTANT: Do NOT include any specific server names, IP addresses, file paths,
database names, or credentials in the skill description. Keep it generic and
transferable."""


class CircuitBreaker:
    """Track extraction count per day. Trips after max_per_day extractions."""

    def __init__(self, max_per_day: int = 5):
        self.max_per_day = max_per_day
        self._timestamps: List[float] = []

    def allow(self) -> bool:
        """Check if an extraction is allowed right now."""
        cutoff = time.time() - 86400  # 24 hours
        self._timestamps = [t for t in self._timestamps if t > cutoff]
        return len(self._timestamps) < self.max_per_day

    def record(self):
        """Record an extraction."""
        self._timestamps.append(time.time())

    @property
    def count_today(self) -> int:
        cutoff = time.time() - 86400
        self._timestamps = [t for t in self._timestamps if t > cutoff]
        return len(self._timestamps)


# Module-level circuit breaker instance
_circuit_breaker = CircuitBreaker(max_per_day=5)


def get_circuit_breaker() -> CircuitBreaker:
    """Access the module-level circuit breaker."""
    return _circuit_breaker


def _parse_json(text: str, default: Any = None) -> Any:
    """Parse JSON from model output, handling markdown fencing."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [line for line in lines if not line.strip().startswith("```")]
        text = "\n".join(lines).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        for start_char, end_char in [("{", "}"), ("[", "]")]:
            start = text.find(start_char)
            end = text.rfind(end_char)
            if start != -1 and end != -1 and end > start:
                try:
                    return json.loads(text[start:end + 1])
                except json.JSONDecodeError:
                    continue
        logger.warning("Failed to parse JSON from model output: %s", text[:200])
        return default


def _check_never_send(text: str) -> List[str]:
    """Check text for NEVER_SEND patterns. Returns list of violations."""
    violations = []
    for pattern in NEVER_SEND_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            violations.append(f"NEVER_SEND: {pattern}")
    return violations


def _strip_infra_terms(text: str) -> str:
    """Replace infrastructure terms with generic placeholders."""
    result = text
    for pattern, replacement in INFRA_REPLACEMENTS:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    return result


def extract_skill(
    task: dict,
    dispatcher=None,
    timeout: float = 30.0,
) -> Optional[SkillDescriptor]:
    """Extract a reusable skill from a completed Jr task.

    Args:
        task: Dict with keys: title, description, acceptance_criteria,
              files_modified, steps_summary, and optionally task_id.
        dispatcher: SubAgentDispatch instance (or mock). If None, attempts
                    to create one from sub_agent_dispatch.
        timeout: Max seconds for model dispatch (Spider condition: 30s default).

    Returns:
        SkillDescriptor if a reusable skill was found, None otherwise.
    """
    breaker = get_circuit_breaker()
    if not breaker.allow():
        logger.warning(
            "Circuit breaker tripped: %d extractions in 24h (max %d). Skipping.",
            breaker.count_today, breaker.max_per_day,
        )
        return None

    # Build prompt from task metadata
    prompt = EXTRACTION_PROMPT.format(
        title=task.get("title", ""),
        description=task.get("description", ""),
        acceptance_criteria=task.get("acceptance_criteria", ""),
        files_modified=task.get("files_modified", ""),
        steps_summary=task.get("steps_summary", ""),
    )

    # Dispatch to local model
    if dispatcher is None:
        from lib.sub_agent_dispatch import SubAgentDispatch
        dispatcher = SubAgentDispatch()

    result = dispatcher.dispatch(
        prompt=prompt,
        system="You are a skill extraction engine. Return only valid JSON.",
        node="redfin_vllm",
        temperature=0.3,
        max_tokens=1024,
        timeout=timeout,
    )

    if not result["ok"]:
        logger.warning("Skill extraction dispatch failed: %s", result["text"])
        return None

    parsed = _parse_json(result["text"])
    if parsed is None or not parsed.get("skill_found", False):
        logger.info("No reusable skill found in task: %s", task.get("title", "unknown"))
        return None

    # Validate required fields
    required = ["name", "intent", "method", "difficulty"]
    for field in required:
        if field not in parsed:
            logger.warning("Extracted skill missing required field: %s", field)
            return None

    difficulty = parsed["difficulty"]
    if not isinstance(difficulty, int) or difficulty < 3:
        logger.info("Skill difficulty too low (%s), skipping.", difficulty)
        return None

    skill = SkillDescriptor(
        name=parsed["name"],
        intent=parsed["intent"],
        method=parsed["method"],
        difficulty=min(max(difficulty, 1), 10),
        tool_hints=parsed.get("tool_hints", []),
        domain=parsed.get("domain", "general"),
        source_task_id=task.get("task_id"),
    )

    breaker.record()
    return skill


def sanitize_skill(skill: SkillDescriptor) -> Optional[SkillDescriptor]:
    """Sanitize a skill descriptor before library insertion.

    1. Check intent and method for NEVER_SEND patterns — reject if found.
    2. Strip infrastructure terms (node names, IPs, internal paths).
    3. Return sanitized copy (original is not mutated).

    Returns None if NEVER_SEND violation detected.
    """
    # Check NEVER_SEND in intent and method
    for field_name, field_value in [("intent", skill.intent), ("method", skill.method)]:
        violations = _check_never_send(field_value)
        if violations:
            logger.warning(
                "Skill '%s' REJECTED — NEVER_SEND violation in %s: %s",
                skill.name, field_name, violations,
            )
            return None

    # Strip infrastructure terms
    sanitized_intent = _strip_infra_terms(skill.intent)
    sanitized_method = _strip_infra_terms(skill.method)
    sanitized_name = _strip_infra_terms(skill.name)

    # Build new descriptor with sanitized fields
    return SkillDescriptor(
        name=sanitized_name,
        intent=sanitized_intent,
        method=sanitized_method,
        difficulty=skill.difficulty,
        tool_hints=skill.tool_hints,
        domain=skill.domain,
        is_compound=skill.is_compound,
        parent_skills=skill.parent_skills,
        source_task_id=skill.source_task_id,
    )


def check_duplicate(skill: SkillDescriptor, db_conn) -> bool:
    """Check if a skill with the same skill_id already exists in skill_library.

    Returns True if duplicate found, False otherwise.
    """
    try:
        cur = db_conn.cursor()
        cur.execute(
            "SELECT 1 FROM skill_library WHERE skill_id = %s LIMIT 1",
            (skill.skill_id,),
        )
        exists = cur.fetchone() is not None
        cur.close()
        return exists
    except Exception as exc:
        logger.warning("Duplicate check failed: %s — treating as non-duplicate.", exc)
        return False


def submit_for_verification(skill: SkillDescriptor, council) -> dict:
    """Submit a candidate skill to the council for verification.

    Args:
        skill: The SkillDescriptor to verify.
        council: Object with a council_vote(proposal, max_tokens) method.

    Returns:
        {"status": str, "confidence": float, "reason": str}
    """
    proposal = (
        f"SKILL VERIFICATION: '{skill.name}'\n"
        f"Domain: {skill.domain} | Difficulty: {skill.difficulty}/10\n"
        f"Intent: {skill.intent}\n"
        f"Method: {skill.method}\n"
        f"Tool Hints: {', '.join(skill.tool_hints) if skill.tool_hints else 'none'}\n"
        f"Skill ID: {skill.skill_id}\n\n"
        f"Should this skill be added to the active skill library?"
    )

    try:
        vote_result = council.council_vote(proposal, max_tokens=200)
    except Exception as exc:
        # Turtle condition: council unreachable → candidate status (never auto-active)
        logger.warning("Council unreachable for skill '%s': %s — defaulting to candidate.", skill.name, exc)
        return {"status": "candidate", "confidence": 0.0, "reason": f"council unreachable: {exc}"}

    consent = vote_result.get("consent", False)
    confidence = vote_result.get("confidence", 0.0)
    reason = vote_result.get("reason", "")

    if consent and confidence > 0.5:
        return {"status": "active", "confidence": confidence, "reason": reason}
    elif consent:
        return {"status": "candidate", "confidence": confidence, "reason": reason}
    else:
        # Dissent or sacred_dissent
        return {"status": "rejected", "confidence": confidence, "reason": reason}
