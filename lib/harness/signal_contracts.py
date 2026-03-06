"""
Cross-Scale Signal Contracts — Spider's concern as a feature.

Defines how Signals aggregate, filter, and re-classify when
crossing scale boundaries in the SRE+C hierarchy:

  Function -> Service -> Node -> Federation

Each boundary has a contract that specifies:
  - Aggregation: how many function signals combine into one service signal
  - Filtering: which signals are absorbed vs propagated
  - Reclassification: urgency may change at each boundary
  - Retention: what metadata survives the crossing

DC-11: The interface is conserved. The contracts define the boundaries.
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from lib.harness.sre_protocol import Signal, Urgency

logger = logging.getLogger("harness.contracts")


@dataclass
class SignalContract:
    """Contract for signals crossing a scale boundary.

    Defines rules for how signals from a lower scale are
    aggregated into signals at the next scale up.
    """
    source_scale: str          # e.g., "function", "service", "node"
    target_scale: str          # e.g., "service", "node", "federation"
    # How many source signals before aggregating into one target signal
    aggregation_window: int = 10
    # Time window for aggregation (seconds)
    aggregation_period: float = 60.0
    # Minimum source urgency to propagate (lower urgency is absorbed)
    min_propagation_urgency: Urgency = Urgency.PAUSE
    # Urgency reclassification rules
    urgency_map: Dict[str, Urgency] = field(default_factory=dict)
    # Metadata keys that survive the crossing
    retained_metadata: List[str] = field(default_factory=lambda: [
        "source", "threat_level", "error_type",
    ])

    def should_propagate(self, signal: Signal) -> bool:
        """Should this signal cross the boundary?"""
        urgency_order = {
            Urgency.DELIBERATE: 0,
            Urgency.PAUSE: 1,
            Urgency.REFLEX: 2,
            Urgency.STRATEGIC: 3,
        }
        signal_level = urgency_order.get(signal.urgency, 0)
        min_level = urgency_order.get(self.min_propagation_urgency, 0)
        return signal_level >= min_level

    def reclassify_urgency(self, source_urgency: Urgency) -> Urgency:
        """Reclassify urgency when crossing the boundary."""
        return self.urgency_map.get(source_urgency.value, source_urgency)


class SignalAggregator:
    """Aggregates signals at a scale boundary per contract rules.

    Collects signals from the source scale and emits aggregated
    signals at the target scale when thresholds are met.
    """

    def __init__(self, contract: SignalContract):
        self.contract = contract
        self._buffer: List[Signal] = []
        self._window_start: float = time.time()

    def ingest(self, signal: Signal) -> Optional[Signal]:
        """Ingest a source-scale signal. Returns aggregated target-scale signal if threshold met."""
        # Filter: does this signal propagate?
        if not self.contract.should_propagate(signal):
            logger.debug(
                "Signal %s absorbed at %s->%s boundary (urgency %s < %s)",
                signal.signal_id, self.contract.source_scale,
                self.contract.target_scale, signal.urgency.value,
                self.contract.min_propagation_urgency.value,
            )
            return None

        self._buffer.append(signal)

        # Check aggregation threshold
        now = time.time()
        window_elapsed = now - self._window_start

        if (
            len(self._buffer) >= self.contract.aggregation_window
            or window_elapsed >= self.contract.aggregation_period
        ):
            return self._emit_aggregated()

        return None

    def _emit_aggregated(self) -> Signal:
        """Emit an aggregated signal from buffered source signals."""
        if not self._buffer:
            return Signal(
                source=self.contract.source_scale,
                content={"count": 0, "summary": "empty window"},
                urgency=Urgency.DELIBERATE,
            )

        # Determine highest urgency in the batch
        urgency_order = [Urgency.DELIBERATE, Urgency.PAUSE, Urgency.REFLEX, Urgency.STRATEGIC]
        max_urgency = Urgency.DELIBERATE
        for sig in self._buffer:
            if urgency_order.index(sig.urgency) > urgency_order.index(max_urgency):
                max_urgency = sig.urgency

        # Reclassify for target scale
        target_urgency = self.contract.reclassify_urgency(max_urgency)

        # Aggregate metadata
        retained = {}
        for key in self.contract.retained_metadata:
            values = set()
            for sig in self._buffer:
                if key in sig.metadata:
                    values.add(str(sig.metadata[key]))
                if isinstance(sig.content, dict) and key in sig.content:
                    values.add(str(sig.content[key]))
            if values:
                retained[key] = list(values)

        aggregated = Signal(
            source=f"{self.contract.source_scale}_aggregator",
            content={
                "count": len(self._buffer),
                "window_seconds": time.time() - self._window_start,
                "source_scale": self.contract.source_scale,
                "target_scale": self.contract.target_scale,
                "max_source_urgency": max_urgency.value,
                "summary": retained,
            },
            urgency=target_urgency,
            metadata={
                "aggregated_from": [s.signal_id for s in self._buffer[:10]],
                "boundary": f"{self.contract.source_scale}->{self.contract.target_scale}",
            },
        )

        # Reset buffer
        self._buffer = []
        self._window_start = time.time()

        logger.info(
            "Emitted aggregated signal at %s->%s: count=%d, urgency=%s",
            self.contract.source_scale, self.contract.target_scale,
            aggregated.content["count"], target_urgency.value,
        )

        return aggregated


# --- Default contracts ---

FUNCTION_TO_SERVICE = SignalContract(
    source_scale="function",
    target_scale="service",
    aggregation_window=10,
    aggregation_period=60.0,
    min_propagation_urgency=Urgency.PAUSE,
    urgency_map={
        "reflex": Urgency.PAUSE,      # Function reflex -> service pause
        "pause": Urgency.DELIBERATE,   # Function pause -> service deliberate
        "deliberate": Urgency.DELIBERATE,
        "strategic": Urgency.STRATEGIC,
    },
)

SERVICE_TO_NODE = SignalContract(
    source_scale="service",
    target_scale="node",
    aggregation_window=5,
    aggregation_period=300.0,
    min_propagation_urgency=Urgency.PAUSE,
    urgency_map={
        "reflex": Urgency.REFLEX,      # Service reflex stays reflex at node
        "pause": Urgency.PAUSE,
        "deliberate": Urgency.DELIBERATE,
        "strategic": Urgency.STRATEGIC,
    },
)

NODE_TO_FEDERATION = SignalContract(
    source_scale="node",
    target_scale="federation",
    aggregation_window=3,
    aggregation_period=600.0,
    min_propagation_urgency=Urgency.DELIBERATE,
    urgency_map={
        "reflex": Urgency.PAUSE,       # Node reflex -> federation pause
        "pause": Urgency.DELIBERATE,   # Node pause -> federation deliberate
        "deliberate": Urgency.STRATEGIC,
        "strategic": Urgency.STRATEGIC,
    },
)