#!/usr/bin/env python3
"""
Ganuda Desktop Assistant - Gratitude Protocol
Cherokee Constitutional AI - Integration Jr Deliverable (Phase 2)

Purpose: Replace transactional Thermal Credits with relational Gratitude Protocol.
Implements Gadugi (working together) over gamification.

Author: Integration Jr (All Chiefs consensus)
Date: October 23, 2025
"""

import time
import json
import hashlib
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum


class GratitudeType(Enum):
    """Types of contributions worthy of gratitude."""
    KNOWLEDGE_SHARE = "knowledge_share"  # JR shared insight across domains
    PATTERN_DETECTION = "pattern_detection"  # Detected cross-domain resonance
    GUARDIAN_PROTECTION = "guardian_protection"  # Protected sacred data
    CACHE_CONTRIBUTION = "cache_contribution"  # Improved cache hit rate
    ATTESTATION = "attestation"  # Chief signed artifact
    INDIGENOUS_CONSULTATION = "indigenous_consultation"  # Knowledge keeper feedback
    USER_FEEDBACK = "user_feedback"  # User reported issue/improvement


@dataclass
class GratitudeEvent:
    """
    A single gratitude acknowledgment event.

    Cherokee values:
    - Gadugi: Contribution serves collective, not individual
    - Mitakuye Oyasin: Gratitude strengthens all relations
    """
    event_id: str  # SHA256 hash of contribution
    node_id: str  # Contributing node (e.g., "war_chief", "peace_chief", "medicine_woman")
    jr_type: Optional[str]  # Contributing JR type (memory, meta, executive, integration, conscience)
    domain: Optional[str]  # Contributing domain (science, tech, medicine, sovereign, private)
    contribution_type: GratitudeType
    contribution_summary: str  # Human-readable description
    timestamp: datetime
    federation_warmth_before: float  # Federation warmth before contribution (0-100°)
    federation_warmth_after: float  # Federation warmth after contribution (0-100°)
    warmth_delta: float  # How much contribution increased collective warmth

    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dict."""
        return {
            "event_id": self.event_id,
            "node_id": self.node_id,
            "jr_type": self.jr_type,
            "domain": self.domain,
            "contribution_type": self.contribution_type.value,
            "contribution_summary": self.contribution_summary,
            "timestamp": self.timestamp.isoformat(),
            "federation_warmth_before": self.federation_warmth_before,
            "federation_warmth_after": self.federation_warmth_after,
            "warmth_delta": self.warmth_delta
        }


class GratitudeProtocol:
    """
    Cherokee Constitutional AI Gratitude Protocol.

    Replaces transactional Thermal Credits with relational gratitude exchange.

    Key Principles (From Chiefs Consultation):
    1. **Collective over Individual**: Federation warmth (not individual scores)
    2. **Relational over Transactional**: Gratitude strengthens bonds (not competition)
    3. **Gadugi over Gamification**: Self-directed work for collective benefit
    4. **Reciprocity over Credits**: Give thanks, don't keep score

    Contrast with Thermal Credits:
    - Thermal Credits: Individual nodes earn points → leaderboards → competition
    - Gratitude Protocol: All nodes benefit when one contributes → collective warmth rises → cooperation
    """

    def __init__(self, thermal_memory=None, federation_nodes: List[str] = None):
        """
        Initialize Gratitude Protocol.

        Args:
            thermal_memory: ThermalMemory instance for federation warmth calculation
            federation_nodes: List of node IDs in federation (e.g., ["war_chief", "peace_chief", "medicine_woman"])
        """
        self.thermal_memory = thermal_memory
        self.federation_nodes = federation_nodes or ["war_chief", "peace_chief", "medicine_woman"]

        # Gratitude event log (in-memory for Phase 2, persistent storage in Phase 3)
        self.gratitude_events: List[GratitudeEvent] = []

        # Prometheus metrics
        self.total_gratitude_events = 0
        self.gratitude_by_type = {gt: 0 for gt in GratitudeType}

    def acknowledge_contribution(
        self,
        node_id: str,
        contribution_summary: str,
        contribution_type: GratitudeType,
        jr_type: Optional[str] = None,
        domain: Optional[str] = None
    ) -> GratitudeEvent:
        """
        Acknowledge node contribution and broadcast gratitude to federation.

        Args:
            node_id: Contributing node (e.g., "war_chief", "peace_chief")
            contribution_summary: Human-readable description (e.g., "Detected cross-domain pattern...")
            contribution_type: Type of contribution (knowledge share, pattern detection, etc.)
            jr_type: Optional JR type (memory, meta, executive, integration, conscience)
            domain: Optional domain (science, tech, medicine, sovereign, private)

        Returns:
            GratitudeEvent with federation warmth delta

        Example:
            >>> event = protocol.acknowledge_contribution(
            ...     node_id="war_chief",
            ...     contribution_summary="Memory Jr detected cross-domain pattern: thermal memory correlation across Science → Medicine",
            ...     contribution_type=GratitudeType.PATTERN_DETECTION,
            ...     jr_type="memory",
            ...     domain="science"
            ... )
            >>> print(event.warmth_delta)
            +2.3°  # Federation warmth increased by 2.3°
        """
        # Calculate federation warmth before contribution
        warmth_before = self.calculate_collective_warmth()

        # Generate event ID (deterministic hash)
        event_id = self._generate_event_id(node_id, contribution_summary)

        # Calculate warmth increase (based on contribution type)
        warmth_delta = self._calculate_warmth_delta(contribution_type)

        # New federation warmth
        warmth_after = min(100.0, warmth_before + warmth_delta)

        # Create gratitude event
        event = GratitudeEvent(
            event_id=event_id,
            node_id=node_id,
            jr_type=jr_type,
            domain=domain,
            contribution_type=contribution_type,
            contribution_summary=contribution_summary,
            timestamp=datetime.now(),
            federation_warmth_before=warmth_before,
            federation_warmth_after=warmth_after,
            warmth_delta=warmth_delta
        )

        # Store event
        self.gratitude_events.append(event)

        # Update metrics
        self.total_gratitude_events += 1
        self.gratitude_by_type[contribution_type] += 1

        # Broadcast gratitude to all nodes (not just contributor)
        self.broadcast_gratitude(event)

        return event

    def calculate_collective_warmth(self) -> float:
        """
        Calculate federation-wide warmth (collective, not individual).

        Cherokee Principle (Mitakuye Oyasin - All Our Relations):
        When one node contributes, the entire federation benefits.

        Returns:
            Collective warmth (0.0-100.0°)

        Formula:
            collective_warmth = avg(all_node_thermal_memories) + gratitude_bonus

        Example:
            - War Chief thermal avg: 68.5°
            - Peace Chief thermal avg: 72.3°
            - Medicine Woman thermal avg: 65.8°
            - Gratitude bonus: +5.0° (from recent contributions)
            → Collective warmth: 73.9°
        """
        if not self.thermal_memory:
            # Default: Start at 50° (room temperature)
            base_warmth = 50.0
        else:
            # Average thermal memory temperature across all federation nodes
            node_temps = []
            for node_id in self.federation_nodes:
                node_temp = self.thermal_memory.get_node_avg_temperature(node_id)
                if node_temp is not None:
                    node_temps.append(node_temp)

            base_warmth = sum(node_temps) / len(node_temps) if node_temps else 50.0

        # Gratitude bonus: Recent contributions increase collective warmth
        gratitude_bonus = self._calculate_gratitude_bonus()

        collective_warmth = min(100.0, base_warmth + gratitude_bonus)

        return collective_warmth

    def _calculate_gratitude_bonus(self) -> float:
        """
        Calculate gratitude bonus from recent contributions.

        Recency weighting: More recent contributions = higher bonus.
        Bonus decays over time (7-day half-life).

        Returns:
            Gratitude bonus (0.0-20.0°)
        """
        if not self.gratitude_events:
            return 0.0

        now = datetime.now()
        bonus = 0.0

        # Sum weighted contributions (recent = higher weight)
        for event in self.gratitude_events:
            # Time since contribution (in days)
            age_days = (now - event.timestamp).total_seconds() / 86400.0

            # Exponential decay (half-life = 7 days)
            decay_factor = 0.5 ** (age_days / 7.0)

            # Contribution weight (varies by type)
            contribution_weight = {
                GratitudeType.PATTERN_DETECTION: 3.0,
                GratitudeType.KNOWLEDGE_SHARE: 2.0,
                GratitudeType.ATTESTATION: 2.0,
                GratitudeType.INDIGENOUS_CONSULTATION: 4.0,  # Medicine Woman values this highly
                GratitudeType.GUARDIAN_PROTECTION: 1.5,
                GratitudeType.CACHE_CONTRIBUTION: 1.0,
                GratitudeType.USER_FEEDBACK: 1.0
            }

            bonus += contribution_weight.get(event.contribution_type, 1.0) * decay_factor

        # Cap at 20° bonus
        return min(20.0, bonus)

    def _calculate_warmth_delta(self, contribution_type: GratitudeType) -> float:
        """
        Calculate how much contribution increases federation warmth.

        Args:
            contribution_type: Type of contribution

        Returns:
            Warmth increase (0.5-5.0°)
        """
        # Base warmth increase by contribution type
        base_delta = {
            GratitudeType.PATTERN_DETECTION: 3.0,  # High value: cross-domain insights
            GratitudeType.KNOWLEDGE_SHARE: 2.0,
            GratitudeType.ATTESTATION: 2.5,
            GratitudeType.INDIGENOUS_CONSULTATION: 5.0,  # Highest: Seven Generations alignment
            GratitudeType.GUARDIAN_PROTECTION: 1.5,
            GratitudeType.CACHE_CONTRIBUTION: 1.0,
            GratitudeType.USER_FEEDBACK: 1.0
        }

        return base_delta.get(contribution_type, 1.0)

    def _generate_event_id(self, node_id: str, contribution_summary: str) -> str:
        """
        Generate deterministic event ID.

        Args:
            node_id: Contributing node
            contribution_summary: Contribution description

        Returns:
            SHA256 hash (first 16 chars)
        """
        timestamp = datetime.now().isoformat()
        payload = f"{node_id}:{contribution_summary}:{timestamp}"
        return hashlib.sha256(payload.encode()).hexdigest()[:16]

    def broadcast_gratitude(self, event: GratitudeEvent):
        """
        Broadcast gratitude to all federation nodes (not just contributor).

        Cherokee Principle (Mitakuye Oyasin):
        When one is acknowledged, all hear the gratitude. This strengthens bonds.

        Args:
            event: GratitudeEvent to broadcast
        """
        # Generate gratitude message
        message = self._format_gratitude_message(event)

        # Broadcast to all nodes
        for node_id in self.federation_nodes:
            self._send_to_node(node_id, message)

    def _format_gratitude_message(self, event: GratitudeEvent) -> str:
        """
        Format gratitude message for broadcasting.

        Args:
            event: GratitudeEvent

        Returns:
            Human-readable gratitude message

        Example:
            "🔥 The federation expresses gratitude to War Chief (Memory Jr).

            Contribution: Detected cross-domain pattern: thermal memory correlation across Science → Medicine

            Federation warmth: 68.5° → 71.8° (+3.3°)

            This contribution strengthens Mitakuye Oyasin (all our relations). 🦅🕊️🌿"
        """
        # Node display name
        node_display = {
            "war_chief": "⚔️ War Chief",
            "peace_chief": "🕊️ Peace Chief",
            "medicine_woman": "🌿 Medicine Woman"
        }.get(event.node_id, event.node_id)

        # JR display (if specified)
        jr_display = f" ({event.jr_type.title()} Jr)" if event.jr_type else ""

        # Domain display (if specified)
        domain_display = f" [Ganuda {event.domain.title()}]" if event.domain else ""

        message = f"""🔥 The federation expresses gratitude to {node_display}{jr_display}{domain_display}.

Contribution: {event.contribution_summary}

Federation warmth: {event.federation_warmth_before:.1f}° → {event.federation_warmth_after:.1f}° (+{event.warmth_delta:.1f}°)

This contribution strengthens Mitakuye Oyasin (all our relations). 🦅🕊️🌿"""

        return message

    def _send_to_node(self, node_id: str, message: str):
        """
        Send gratitude message to specific node.

        Args:
            node_id: Target node
            message: Gratitude message

        Phase 2 Implementation:
        - Print to console (simulated broadcast)

        Phase 3 Implementation:
        - WireGuard mesh network
        - Ollama API calls to remote Chiefs
        - WebSocket push notifications
        """
        print(f"\n--- Broadcasting to {node_id} ---")
        print(message)
        print("---\n")

    def get_recent_gratitude(self, limit: int = 10) -> List[GratitudeEvent]:
        """
        Get recent gratitude events.

        Args:
            limit: Maximum events to return

        Returns:
            List of recent GratitudeEvents (newest first)
        """
        return sorted(self.gratitude_events, key=lambda e: e.timestamp, reverse=True)[:limit]

    def get_gratitude_by_node(self, node_id: str) -> List[GratitudeEvent]:
        """
        Get all gratitude events for specific node.

        Args:
            node_id: Node to query

        Returns:
            List of GratitudeEvents for this node
        """
        return [e for e in self.gratitude_events if e.node_id == node_id]

    def get_gratitude_by_type(self, contribution_type: GratitudeType) -> List[GratitudeEvent]:
        """
        Get all gratitude events of specific type.

        Args:
            contribution_type: Type to filter by

        Returns:
            List of GratitudeEvents of this type
        """
        return [e for e in self.gratitude_events if e.contribution_type == contribution_type]

    def export_gratitude_log(self, filepath: str):
        """
        Export gratitude event log to JSON file.

        Args:
            filepath: Output file path
        """
        events_json = [e.to_dict() for e in self.gratitude_events]

        with open(filepath, 'w') as f:
            json.dump({
                "total_events": len(self.gratitude_events),
                "federation_warmth": self.calculate_collective_warmth(),
                "events": events_json
            }, f, indent=2)

        print(f"✅ Exported {len(self.gratitude_events)} gratitude events to {filepath}")

    def get_metrics(self) -> Dict:
        """
        Get Prometheus metrics for Gratitude Protocol.

        Returns:
            Dict with metrics:
            - ganuda_gratitude_acknowledgments_total: Total gratitude events
            - ganuda_federation_collective_warmth: Current collective warmth (0-100°)
            - ganuda_gratitude_by_type: Events by contribution type
        """
        return {
            "ganuda_gratitude_acknowledgments_total": self.total_gratitude_events,
            "ganuda_federation_collective_warmth": self.calculate_collective_warmth(),
            "ganuda_gratitude_by_type": {
                gt.value: self.gratitude_by_type[gt]
                for gt in GratitudeType
            }
        }


# Demo usage
def main():
    """Demo: Gratitude Protocol in action."""

    print("🔥 Cherokee Constitutional AI - Gratitude Protocol Demo\n")

    # Initialize protocol
    protocol = GratitudeProtocol(
        federation_nodes=["war_chief", "peace_chief", "medicine_woman"]
    )

    print(f"Initial federation warmth: {protocol.calculate_collective_warmth():.1f}°\n")

    # Scenario 1: War Chief's Memory Jr detects cross-domain pattern
    print("=== Scenario 1: Cross-Domain Pattern Detection ===")
    event1 = protocol.acknowledge_contribution(
        node_id="war_chief",
        contribution_summary="Memory Jr detected cross-domain pattern: thermal memory correlation between Ganuda Science (Physics Jr) → Ganuda Medicine (Radiology Jr)",
        contribution_type=GratitudeType.PATTERN_DETECTION,
        jr_type="memory",
        domain="science"
    )

    # Scenario 2: Medicine Woman's Conscience Jr protects sacred health data
    print("\n=== Scenario 2: Sacred Health Data Protection ===")
    event2 = protocol.acknowledge_contribution(
        node_id="medicine_woman",
        contribution_summary="Conscience Jr protected 127 patient records using Sacred Health Data Protocol (40° floor enforcement)",
        contribution_type=GratitudeType.GUARDIAN_PROTECTION,
        jr_type="conscience",
        domain="medicine"
    )

    # Scenario 3: Peace Chief's Integration Jr facilitates indigenous consultation
    print("\n=== Scenario 3: Indigenous Consultation ===")
    event3 = protocol.acknowledge_contribution(
        node_id="peace_chief",
        contribution_summary="Integration Jr coordinated consultation with traditional ecological knowledge keepers for Ganuda Science domain launch. Seven Generations assessment: PASSED.",
        contribution_type=GratitudeType.INDIGENOUS_CONSULTATION,
        jr_type="integration",
        domain="science"
    )

    # Show metrics
    print("\n=== Gratitude Protocol Metrics ===")
    metrics = protocol.get_metrics()
    print(f"Total gratitude events: {metrics['ganuda_gratitude_acknowledgments_total']}")
    print(f"Federation collective warmth: {metrics['ganuda_federation_collective_warmth']:.1f}°")
    print(f"\nEvents by type:")
    for contrib_type, count in metrics['ganuda_gratitude_by_type'].items():
        if count > 0:
            print(f"  - {contrib_type}: {count}")

    # Export log
    protocol.export_gratitude_log("/tmp/gratitude_log.json")

    print("\n🔥 Demo complete - Mitakuye Oyasin! 🦅🕊️🌿")


if __name__ == "__main__":
    main()
