"""
SRE Circuit Breakers — Eagle Eye's concern as a feature.

Prevents cascading failures between SRE scales.
Each breaker tracks failure rate and trips when threshold exceeded.

States:
  CLOSED: Normal operation. Requests flow through.
  OPEN: Tripped. Requests fail-fast or route to fallback.
  HALF_OPEN: Testing recovery. Limited requests allowed through.

DC-10: Autonomy at each timescale.
DC-11: Same breaker pattern at every scale boundary.
"""

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional

logger = logging.getLogger("harness.circuit_breaker")


class BreakerState(str, Enum):
    CLOSED = "closed"        # Normal operation
    OPEN = "open"            # Tripped — fail fast
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class CircuitBreaker:
    """Circuit breaker for an SRE scale boundary.

    Usage:
        breaker = CircuitBreaker(name='claude_backend', failure_threshold=5)

        if breaker.allow_request():
            try:
                result = call_claude(...)
                breaker.record_success()
            except Exception:
                breaker.record_failure()
        else:
            result = call_local_fallback(...)
    """
    name: str
    failure_threshold: int = 5       # Failures before tripping
    recovery_timeout: float = 60.0   # Seconds before trying half-open
    half_open_max: int = 2           # Max requests in half-open state

    # Internal state
    state: BreakerState = BreakerState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: float = 0.0
    last_state_change: float = 0.0
    _half_open_attempts: int = 0

    def allow_request(self) -> bool:
        """Should the next request be allowed through?"""
        if self.state == BreakerState.CLOSED:
            return True

        if self.state == BreakerState.OPEN:
            # Check if recovery timeout has elapsed
            if time.time() - self.last_failure_time >= self.recovery_timeout:
                self._transition(BreakerState.HALF_OPEN)
                self._half_open_attempts = 0
                return True
            return False

        if self.state == BreakerState.HALF_OPEN:
            if self._half_open_attempts < self.half_open_max:
                self._half_open_attempts += 1
                return True
            return False

        return False

    def record_success(self) -> None:
        """Record a successful request."""
        self.success_count += 1

        if self.state == BreakerState.HALF_OPEN:
            # Recovery confirmed — close the breaker
            self._transition(BreakerState.CLOSED)
            self.failure_count = 0
            logger.info("Circuit breaker '%s' recovered -> CLOSED", self.name)

    def record_failure(self) -> None:
        """Record a failed request."""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.state == BreakerState.HALF_OPEN:
            # Recovery failed — re-open
            self._transition(BreakerState.OPEN)
            logger.warning(
                "Circuit breaker '%s' recovery failed -> OPEN", self.name
            )

        elif self.state == BreakerState.CLOSED:
            if self.failure_count >= self.failure_threshold:
                self._transition(BreakerState.OPEN)
                logger.warning(
                    "Circuit breaker '%s' tripped (%d failures) -> OPEN",
                    self.name, self.failure_count,
                )

    def reset(self) -> None:
        """Manual reset (requires operator or Council)."""
        self._transition(BreakerState.CLOSED)
        self.failure_count = 0
        logger.info("Circuit breaker '%s' manually reset -> CLOSED", self.name)

    def status(self) -> Dict:
        """Return current breaker status."""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure": self.last_failure_time,
            "recovery_timeout": self.recovery_timeout,
        }

    def _transition(self, new_state: BreakerState) -> None:
        """Transition to a new state."""
        old_state = self.state
        self.state = new_state
        self.last_state_change = time.time()
        logger.debug(
            "Circuit breaker '%s': %s -> %s",
            self.name, old_state.value, new_state.value,
        )


class BreakerRegistry:
    """Registry of all circuit breakers in the system.

    Provides a single place to check breaker status and manage
    breakers across all SRE scale boundaries.
    """

    def __init__(self):
        self._breakers: Dict[str, CircuitBreaker] = {}

    def register(self, breaker: CircuitBreaker) -> None:
        """Register a circuit breaker."""
        self._breakers[breaker.name] = breaker
        logger.info("Registered circuit breaker: %s", breaker.name)

    def get(self, name: str) -> Optional[CircuitBreaker]:
        """Get a breaker by name."""
        return self._breakers.get(name)

    def status_all(self) -> Dict[str, Dict]:
        """Return status of all breakers."""
        return {name: b.status() for name, b in self._breakers.items()}

    def any_open(self) -> bool:
        """Are any breakers currently open?"""
        return any(
            b.state == BreakerState.OPEN for b in self._breakers.values()
        )


# --- Default breakers for the federation ---

def create_default_breakers() -> BreakerRegistry:
    """Create the default set of circuit breakers."""
    registry = BreakerRegistry()

    registry.register(CircuitBreaker(
        name="claude_backend",
        failure_threshold=3,
        recovery_timeout=120.0,
    ))

    registry.register(CircuitBreaker(
        name="tier1_reflex",
        failure_threshold=5,
        recovery_timeout=30.0,
    ))

    registry.register(CircuitBreaker(
        name="tier2_deliberation",
        failure_threshold=3,
        recovery_timeout=60.0,
    ))

    registry.register(CircuitBreaker(
        name="bmasass_deepseek",
        failure_threshold=3,
        recovery_timeout=180.0,
    ))

    registry.register(CircuitBreaker(
        name="valence_evaluator",
        failure_threshold=10,
        recovery_timeout=300.0,
    ))

    return registry