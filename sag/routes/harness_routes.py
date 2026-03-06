"""Harness query route -- the front door for DC-10 reflex arc.

Routes incoming queries through the Graduated Harness Tiers.
Tier 1 (Reflex) -> Tier 2 (Deliberation) -> Tier 3 (Council)
Escalation is automatic based on confidence and stakes.

Longhouse #7e55951691481b0c (DC-10 ratified, UNANIMOUS)
"""

import logging
from flask import Blueprint, request, jsonify
from sag.routes.auth import require_api_key

from lib.harness.core import HarnessRequest
from lib.harness.config import load_harness_config
from lib.harness.escalation import EscalationEngine
from lib.harness.tier1_reflex import Tier1Reflex
from lib.harness.tier2_deliberation import Tier2Deliberation
from lib.harness.tier3_council import Tier3Council

logger = logging.getLogger("sag.harness")

harness_bp = Blueprint("harness", __name__)

# Initialize engine once at module load (not per-request)
_engine = None


def _get_engine():
    """Lazy-init the escalation engine with all three tiers."""
    global _engine
    if _engine is not None:
        return _engine

    config = load_harness_config()
    engine = EscalationEngine(config)

    if config.tier1.enabled:
        engine.register_tier(1, Tier1Reflex(config.tier1))
    if config.tier2.enabled:
        engine.register_tier(2, Tier2Deliberation(config.tier2))
    if config.tier3.enabled:
        engine.register_tier(3, Tier3Council(config.tier3))

    _engine = engine
    logger.info("Harness escalation engine initialized with %d tiers", len(engine._tier_handlers))
    return _engine


@harness_bp.route("/v1/harness/query", methods=["POST"])
@require_api_key
def harness_query():
    """Process a query through the graduated harness tiers.

    Request body (JSON):
        query (str, required): The question or instruction.
        context (dict, optional): Additional context for the query.
        user_id (str, optional): User identifier. Defaults to "default".
        session_id (str, optional): Session identifier for continuity.
        force_tier (int, optional): Force a specific tier (testing only).

    Response (JSON):
        answer (str): The response text.
        tier_used (int): Which tier produced the final answer.
        confidence (float): Confidence score (0.0 - 1.0).
        escalation_path (list[int]): Tiers traversed.
        latency_ms (float): Total processing time.
        request_id (str): Unique request identifier for tracing.
    """
    data = request.get_json(silent=True)
    if not data or "query" not in data:
        return jsonify({"error": "Missing required field: query"}), 400

    harness_request = HarnessRequest(
        query=data["query"],
        context=data.get("context", {}),
        user_id=data.get("user_id", "default"),
        session_id=data.get("session_id", ""),
        force_tier=data.get("force_tier"),
        metadata=data.get("metadata", {}),
    )

    engine = _get_engine()
    response = engine.handle_request(harness_request)

    return jsonify(response.to_dict()), 200


@harness_bp.route("/v1/harness/health", methods=["GET"])
def harness_health():
    """Health check for the harness subsystem."""
    engine = _get_engine()
    tiers_registered = sorted(engine._tier_handlers.keys())
    return jsonify({
        "status": "ok",
        "tiers_registered": tiers_registered,
        "tier_count": len(tiers_registered),
    }), 200