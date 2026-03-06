"""
Tier 3 Council -- Full ethos invocation for high-stakes queries.

Wires the existing SpecialistCouncil pipeline into the Graduated Harness
TierHandler protocol. This module adds NO new council logic -- it delegates
entirely to specialist_council.py.

Constitutional: Fixed star topology (Thermal #82856). Cannot be changed.
Raven requirement: Tier 3 is the moat. Protect it.
Latency target: <120s p95.

Council Vote: #2c2fa88a53817307 (Graduated Harness APPROVED)
Longhouse: #b940f09b18605c97 (UNANIMOUS)
"""

import logging
import time
from typing import Optional, List, Dict, Any

from lib.harness.core import HarnessRequest, TierResult, StakesLevel
from lib.harness.config import TierConfig, load_harness_config

logger = logging.getLogger("harness.tier3")


class Tier3Council:
    """Full council invocation tier -- all 7+ specialists.

    Wraps SpecialistCouncil.vote() to conform to the TierHandler protocol.
    The escalation engine calls handle() when Tier 1 and/or Tier 2 confidence
    is insufficient, or when high-stakes keywords are detected.

    Usage:
        config = load_harness_config()
        tier3 = Tier3Council(config.tier3)
        result = tier3.handle(request, prior_results=[t1_result, t2_result])
    """

    def __init__(self, tier_config: Optional[TierConfig] = None):
        if tier_config is None:
            full_config = load_harness_config()
            tier_config = full_config.tier3
        self.config = tier_config

    def handle(
        self,
        request: HarnessRequest,
        prior_results: Optional[List[TierResult]] = None,
    ) -> TierResult:
        """Invoke the full specialist council for a request.

        Args:
            request: The harness request to process.
            prior_results: Results from Tier 1 and/or Tier 2 (passed as
                escalation context so specialists can see what was already tried).

        Returns:
            TierResult with council consensus, confidence, vote ID, and
            specialist count.
        """
        start_time = time.time()

        # --- Input validation (Crawdad requirement) ---
        errors = request.validate()
        if errors:
            return TierResult(
                tier=3,
                answer="Input validation failed: " + "; ".join(errors),
                confidence=0.0,
                latency_ms=0.0,
                stakes=StakesLevel.HIGH,
                metadata={"validation_errors": errors},
            )

        # --- Build council query with escalation context ---
        council_query = self._build_council_query(request, prior_results)

        # --- Determine council type and high_stakes flag ---
        high_stakes = True  # Tier 3 is always high stakes (it was escalated here)
        council_type = request.metadata.get("council_type", "inner")

        # --- Invoke the specialist council ---
        try:
            from lib.specialist_council import SpecialistCouncil

            max_tokens = self.config.primary_endpoint.max_tokens
            council = SpecialistCouncil(max_tokens=max_tokens)
            vote = council.vote(
                council_query,
                include_responses=True,
                high_stakes=high_stakes,
                council_type=council_type,
            )
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            logger.error(
                "Tier 3 council invocation failed for %s: %s",
                request.request_id, e,
            )
            return TierResult(
                tier=3,
                answer="Council invocation failed: " + str(e),
                confidence=0.0,
                latency_ms=latency_ms,
                stakes=StakesLevel.HIGH,
                metadata={"error": str(e)},
            )

        latency_ms = (time.time() - start_time) * 1000

        # --- Extract diversity score (if available) ---
        diversity_score = self._get_diversity_score(vote)

        # --- Map CouncilVote to TierResult ---
        specialist_count = len(vote.responses) if vote.responses else 0

        # Build metadata with full context for audit trail
        metadata = {
            "consensus": vote.consensus,
            "recommendation": vote.recommendation,
            "concerns": vote.concerns,
            "council_type": council_type,
            "specialist_count": specialist_count,
            "high_stakes": high_stakes,
        }

        # Include escalation context in metadata (Two Wolves: full audit trail)
        if prior_results:
            metadata["escalation_context"] = {
                "tiers_tried": [r.tier for r in prior_results],
                "prior_confidences": [r.confidence for r in prior_results],
                "prior_answers_truncated": [
                    r.answer[:200] if r.answer else "" for r in prior_results
                ],
            }

        # Include specialist names if responses are available
        if vote.responses:
            metadata["specialists"] = [
                {"name": r.name, "role": r.role, "has_concern": r.has_concern}
                for r in vote.responses
            ]

        result = TierResult(
            tier=3,
            answer=vote.consensus,
            confidence=vote.confidence,
            latency_ms=latency_ms,
            stakes=StakesLevel.HIGH,
            diversity_score=diversity_score,
            council_vote_id=vote.audit_hash,
            specialist_count=specialist_count,
            metadata=metadata,
        )

        logger.info(
            "Tier 3 complete: confidence=%.3f, specialists=%d, vote=%s, "
            "latency=%.0fms [%s]",
            vote.confidence,
            specialist_count,
            vote.audit_hash,
            latency_ms,
            request.request_id,
        )

        return result

    def _build_council_query(
        self,
        request: HarnessRequest,
        prior_results: Optional[List[TierResult]],
    ) -> str:
        """Build the council query, enriching with escalation context.

        When prior tiers have already attempted the query, their answers
        and confidence levels are included so specialists can build on
        (or disagree with) earlier reasoning.
        """
        query = request.query

        # Add request context if present
        if request.context:
            context_lines = []
            for key, value in request.context.items():
                context_lines.append(f"- {key}: {value}")
            if context_lines:
                query = query + "\n\nAdditional context:\n" + "\n".join(context_lines)

        # Add escalation context from prior tiers
        if prior_results:
            escalation_lines = [
                "\n\n--- Escalation Context (prior tier attempts) ---"
            ]
            for pr in prior_results:
                tier_label = {1: "Tier 1 (Reflex)", 2: "Tier 2 (Deliberation)"}.get(
                    pr.tier, f"Tier {pr.tier}"
                )
                escalation_lines.append(
                    f"\n{tier_label} (confidence: {pr.confidence:.3f}):\n"
                    f"{pr.answer[:500]}"
                )
            escalation_lines.append(
                "\nThe above attempts did not meet confidence thresholds. "
                "Please provide a thorough, high-confidence council analysis."
            )
            query = query + "\n".join(escalation_lines)

        return query

    def _get_diversity_score(self, vote) -> Optional[float]:
        """Extract diversity score from a council vote.

        Calls the diversity checker if responses are available.
        Returns None if diversity cannot be computed.
        """
        if not vote.responses or len(vote.responses) < 2:
            return None

        try:
            from lib.council_diversity_check import check_diversity
            diversity = check_diversity(vote.responses, vote.audit_hash)
            if diversity:
                return diversity.overall_diversity
        except Exception as e:
            logger.warning("Diversity check failed (non-fatal): %s", e)

        return None