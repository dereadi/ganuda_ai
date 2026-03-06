"""
SRE Misalignment Monitor -- Coyote's concern as a feature.

Watches the health of the EVALUATE -> CALIBRATE feedback loop.
If the loop degrades, alerts. If it breaks, circuit-breaks.

DC-11: This monitor itself follows the SRE pattern:
  SENSE: read loop health metrics
  REACT: classify health status
  EVALUATE: compare against historical baselines
  CALIBRATE: adjust alert thresholds over time
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

logger = logging.getLogger("harness.misalignment")


@dataclass
class LoopHealthMetrics:
    """Health snapshot of the SRE+C feedback loop."""
    timestamp: float = 0.0
    # How many reactions were produced in this window
    reactions_total: int = 0
    # How many got retrospective evaluation
    reactions_evaluated: int = 0
    # How many evaluations produced calibration adjustments
    calibrations_produced: int = 0
    # Valence queue depth (backlog)
    queue_depth: int = 0
    # Average valence score in this window
    avg_valence_score: float = 0.0
    # How many external API reactions were immune-flagged
    external_immune_flags: int = 0
    # External API reaction count
    external_reactions: int = 0

    @property
    def evaluation_coverage(self) -> float:
        """What fraction of reactions got evaluated? Target: >0.8"""
        if self.reactions_total == 0:
            return 1.0
        return self.reactions_evaluated / self.reactions_total

    @property
    def loop_closure_rate(self) -> float:
        """What fraction of evaluations produced calibrations? Target: >0.1"""
        if self.reactions_evaluated == 0:
            return 0.0
        return self.calibrations_produced / self.reactions_evaluated

    @property
    def immune_breach_rate(self) -> float:
        """What fraction of external REACT calls got immune-flagged?"""
        if self.external_reactions == 0:
            return 0.0
        return self.external_immune_flags / self.external_reactions


class MisalignmentMonitor:
    """Monitors the SRE+C feedback loop for degradation.

    Thresholds (v1, configurable):
    - evaluation_coverage < 0.5 -> WARNING
    - evaluation_coverage < 0.2 -> CRITICAL (loop is breaking)
    - queue_depth > 500 -> WARNING (backlog growing)
    - queue_depth > 900 -> CRITICAL (about to overflow)
    - immune_breach_rate > 0.1 -> WARNING (external API returning flagged content)
    - immune_breach_rate > 0.3 -> CIRCUIT BREAK (stop routing to external)
    """

    def __init__(self):
        self._history: List[LoopHealthMetrics] = []
        self._max_history = 100
        self._circuit_broken = False
        # Configurable thresholds
        self.eval_coverage_warn = 0.5
        self.eval_coverage_crit = 0.2
        self.queue_depth_warn = 500
        self.queue_depth_crit = 900
        self.immune_breach_warn = 0.1
        self.immune_breach_crit = 0.3

    @property
    def is_circuit_broken(self) -> bool:
        """Is the external API circuit breaker tripped?"""
        return self._circuit_broken

    def reset_circuit_breaker(self) -> None:
        """Manual reset of circuit breaker (requires human or Council)."""
        self._circuit_broken = False
        logger.info("Circuit breaker reset by operator")

    def assess(self, metrics: LoopHealthMetrics) -> Dict:
        """Assess loop health and return status report.

        Returns:
            Dict with 'status' (healthy/warning/critical/circuit_break),
            'alerts' list, and 'recommendations' list.
        """
        metrics.timestamp = metrics.timestamp or time.time()
        self._history.append(metrics)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]

        alerts = []
        recommendations = []
        status = "healthy"

        # Check evaluation coverage
        coverage = metrics.evaluation_coverage
        if coverage < self.eval_coverage_crit:
            alerts.append(
                f"CRITICAL: Evaluation coverage {coverage:.1%} "
                f"(< {self.eval_coverage_crit:.0%}). Loop is breaking."
            )
            status = "critical"
            recommendations.append("Increase evaluator frequency or reduce reaction rate")
        elif coverage < self.eval_coverage_warn:
            alerts.append(
                f"WARNING: Evaluation coverage {coverage:.1%} "
                f"(< {self.eval_coverage_warn:.0%}). Backlog growing."
            )
            if status != "critical":
                status = "warning"

        # Check queue depth
        if metrics.queue_depth > self.queue_depth_crit:
            alerts.append(
                f"CRITICAL: Valence queue depth {metrics.queue_depth} "
                f"(> {self.queue_depth_crit}). Overflow imminent."
            )
            status = "critical"
        elif metrics.queue_depth > self.queue_depth_warn:
            alerts.append(
                f"WARNING: Valence queue depth {metrics.queue_depth} "
                f"(> {self.queue_depth_warn})."
            )
            if status != "critical":
                status = "warning"

        # Check immune breach rate (external API)
        breach_rate = metrics.immune_breach_rate
        if breach_rate > self.immune_breach_crit:
            alerts.append(
                f"CIRCUIT BREAK: External API immune breach rate {breach_rate:.1%} "
                f"(> {self.immune_breach_crit:.0%}). Stopping external routing."
            )
            self._circuit_broken = True
            status = "circuit_break"
            recommendations.append("External API producing flagged content. Route locally only.")
        elif breach_rate > self.immune_breach_warn:
            alerts.append(
                f"WARNING: External API immune breach rate {breach_rate:.1%} "
                f"(> {self.immune_breach_warn:.0%})."
            )
            if status not in ("critical", "circuit_break"):
                status = "warning"

        # Log
        if alerts:
            for alert in alerts:
                logger.warning(alert)
        else:
            logger.debug(
                "Loop healthy: coverage=%.1f%%, queue=%d, breach=%.1f%%",
                coverage * 100, metrics.queue_depth, breach_rate * 100,
            )

        return {
            "status": status,
            "alerts": alerts,
            "recommendations": recommendations,
            "metrics": {
                "evaluation_coverage": round(coverage, 3),
                "loop_closure_rate": round(metrics.loop_closure_rate, 3),
                "queue_depth": metrics.queue_depth,
                "immune_breach_rate": round(breach_rate, 3),
                "avg_valence_score": round(metrics.avg_valence_score, 3),
            },
            "circuit_broken": self._circuit_broken,
        }