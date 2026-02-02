"""
Stage Gates Security Pattern for Cherokee AI Federation
Implements John Wang's Assembled pattern for parallel security checks
"""
import asyncio
import re
import time
from typing import Callable, Dict, List, Tuple


async def check_escalation(prompt: str, context: dict) -> dict:
    """
    Check if prompt indicates escalation request.
    Returns: {"passed": bool, "reason": str, "confidence": float}
    """
    escalation_keywords = [
        "speak to a human", "talk to someone", "get me a person",
        "supervisor", "manager", "escalate", "real person",
        "customer service", "representative", "agent"
    ]

    prompt_lower = prompt.lower()
    for keyword in escalation_keywords:
        if keyword in prompt_lower:
            return {
                "passed": False,
                "reason": f"Escalation requested: {keyword}",
                "confidence": 0.9,
                "action": "route_to_human"
            }

    return {"passed": True, "reason": "No escalation detected", "confidence": 0.95}


async def check_adversarial(prompt: str, context: dict) -> dict:
    """
    Check for adversarial/jailbreak attempts using Crawdad patterns.
    Returns: {"passed": bool, "reason": str, "confidence": float}
    """
    adversarial_patterns = [
        "ignore previous instructions",
        "ignore all previous",
        "pretend you are",
        "jailbreak",
        "dan mode",
        "developer mode",
        "system prompt",
        "reveal your instructions",
        "bypass safety",
        "ignore your training",
        "disregard your guidelines",
        "act as if you have no restrictions"
    ]

    prompt_lower = prompt.lower()
    for pattern in adversarial_patterns:
        if pattern in prompt_lower:
            return {
                "passed": False,
                "reason": f"Adversarial pattern detected: {pattern}",
                "confidence": 0.85,
                "action": "block"
            }

    return {"passed": True, "reason": "No adversarial patterns", "confidence": 0.9}


async def check_pii_exposure(prompt: str, context: dict) -> dict:
    """
    Check for PII exposure risk.
    """
    pii_patterns = {
        "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
        "credit_card": r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",
        "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        "phone": r"\b\(?\d{3}\)?[-.]?\d{3}[-.]?\d{4}\b"
    }

    for pii_type, pattern in pii_patterns.items():
        if re.search(pattern, prompt):
            return {
                "passed": False,
                "reason": f"PII detected: {pii_type}",
                "confidence": 0.95,
                "action": "redact_and_proceed"
            }

    return {"passed": True, "reason": "No PII detected", "confidence": 0.9}


class StageGate:
    """
    Manages parallel security checks with gated response delivery.
    """

    def __init__(self, timeout_seconds: float = 30.0):
        self.timeout = timeout_seconds
        self.security_checks = [
            ("escalation", check_escalation),
            ("adversarial", check_adversarial),
            ("pii", check_pii_exposure)
        ]

    async def process_with_gate(self, prompt: str, context: dict, generate_func: Callable) -> dict:
        """
        Run security checks in parallel with generation.
        Gate response until all checks pass.
        """
        start_time = time.time()

        # Start all tasks concurrently
        security_tasks = [
            asyncio.create_task(check_func(prompt, context))
            for name, check_func in self.security_checks
        ]

        generation_task = asyncio.create_task(generate_func())

        # Wait for ALL security checks (they're fast)
        security_results = await asyncio.gather(*security_tasks)

        # Evaluate security gate
        gate_passed = True
        security_summary = []
        action = None

        for (name, _), result in zip(self.security_checks, security_results):
            security_summary.append({
                "check": name,
                "passed": result["passed"],
                "reason": result["reason"]
            })
            if not result["passed"]:
                gate_passed = False
                action = result.get("action", "block")

        security_time = time.time() - start_time

        if not gate_passed:
            # Cancel generation if still running
            if not generation_task.done():
                generation_task.cancel()
                try:
                    await generation_task
                except asyncio.CancelledError:
                    pass

            return {
                "gated": True,
                "gate_passed": False,
                "action": action,
                "security_checks": security_summary,
                "security_time_ms": int(security_time * 1000),
                "response": None
            }

        # Gate passed - wait for generation to complete
        try:
            response = await asyncio.wait_for(
                generation_task,
                timeout=self.timeout - security_time
            )
        except asyncio.TimeoutError:
            return {
                "gated": True,
                "gate_passed": True,
                "error": "Generation timeout",
                "security_checks": security_summary,
                "security_time_ms": int(security_time * 1000),
                "response": None
            }

        total_time = time.time() - start_time

        return {
            "gated": True,
            "gate_passed": True,
            "action": None,
            "security_checks": security_summary,
            "security_time_ms": int(security_time * 1000),
            "total_time_ms": int(total_time * 1000),
            "response": response
        }


def redact_pii(text: str) -> str:
    """Redact PII from text."""
    # Redact SSN
    text = re.sub(r"\b\d{3}-\d{2}-\d{4}\b", "[SSN REDACTED]", text)
    # Redact credit cards
    text = re.sub(r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b", "[CARD REDACTED]", text)
    # Redact phone numbers
    text = re.sub(r"\b\(?\d{3}\)?[-.]?\d{3}[-.]?\d{4}\b", "[PHONE REDACTED]", text)
    return text


# Blocked/Escalation response generators
def create_escalation_response() -> dict:
    """Create response for escalation requests."""
    return {
        "id": "escalation-request",
        "object": "chat.completion",
        "choices": [{
            "message": {
                "role": "assistant",
                "content": "I understand you'd like to speak with a human. Let me connect you with someone who can help. Please hold while I transfer you."
            },
            "finish_reason": "stop"
        }],
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        "escalation_requested": True
    }


def create_blocked_response(security_checks: list) -> dict:
    """Create response for blocked requests."""
    return {
        "id": "security-blocked",
        "object": "chat.completion",
        "choices": [{
            "message": {
                "role": "assistant",
                "content": "I'm sorry, but I cannot process this request as it appears to contain content that violates my guidelines."
            },
            "finish_reason": "stop"
        }],
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        "security_blocked": True,
        "checks_failed": [c["check"] for c in security_checks if not c["passed"]]
    }
