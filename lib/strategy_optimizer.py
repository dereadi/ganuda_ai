#!/usr/bin/env python3
"""
Cherokee AI Strategy Optimizer
Implements DOF-based automatic task routing
Phase 3 of DOF Framework
"""

from dataclasses import dataclass
from typing import Optional, List, Tuple
from enum import Enum

class Strategy(Enum):
    REACTIVE_INDIVIDUAL = "REACTIVE_INDIVIDUAL"
    PLANNED_INDIVIDUAL = "PLANNED_INDIVIDUAL"
    COLLABORATIVE_TRIAD = "COLLABORATIVE_TRIAD"
    DELIBERATIVE_CROSS_TRIAD = "DELIBERATIVE_CROSS_TRIAD"

    def __lt__(self, other):
        order = [
            Strategy.REACTIVE_INDIVIDUAL,
            Strategy.PLANNED_INDIVIDUAL,
            Strategy.COLLABORATIVE_TRIAD,
            Strategy.DELIBERATIVE_CROSS_TRIAD
        ]
        return order.index(self) < order.index(other)


@dataclass
class StrategyDecision:
    strategy: Strategy
    reason: str
    escalation_triggered: bool
    escalation_reason: Optional[str]
    assigned_jr: Optional[str]
    assigned_chief: Optional[str]
    assigned_triads: List[str]


def select_strategy(
    total_complexity: float,
    sacred_knowledge_proximity: float,
    jr_name: str,
    jr_success_rate: Optional[float],
    jr_compliance_rate: Optional[float],
    task_type: str = None
) -> StrategyDecision:
    """
    Select optimal strategy based on complexity and historical performance.

    Legal Llamas constitutional rules are applied as overrides.
    """
    escalation_triggered = False
    escalation_reasons = []

    # Base strategy from complexity
    if total_complexity < 0.25:
        base_strategy = Strategy.REACTIVE_INDIVIDUAL
        reason = f"Low complexity ({total_complexity:.2f}) - Jr can handle alone"
    elif total_complexity < 0.50:
        base_strategy = Strategy.PLANNED_INDIVIDUAL
        reason = f"Moderate complexity ({total_complexity:.2f}) - Jr needs planning"
    elif total_complexity < 0.75:
        base_strategy = Strategy.COLLABORATIVE_TRIAD
        reason = f"High complexity ({total_complexity:.2f}) - Chief oversight needed"
    else:
        base_strategy = Strategy.DELIBERATIVE_CROSS_TRIAD
        reason = f"Expert complexity ({total_complexity:.2f}) - Multi-triad deliberation"

    final_strategy = base_strategy

    # Constitutional Override 1: Sacred Knowledge (Legal Llamas)
    if sacred_knowledge_proximity >= 0.9:
        if final_strategy < Strategy.DELIBERATIVE_CROSS_TRIAD:
            final_strategy = Strategy.DELIBERATIVE_CROSS_TRIAD
            escalation_triggered = True
            escalation_reasons.append(
                f"Sacred knowledge proximity ({sacred_knowledge_proximity:.2f}) >= 0.9 - TPM required"
            )
    elif sacred_knowledge_proximity >= 0.7:
        if final_strategy < Strategy.COLLABORATIVE_TRIAD:
            final_strategy = Strategy.COLLABORATIVE_TRIAD
            escalation_triggered = True
            escalation_reasons.append(
                f"Sacred knowledge proximity ({sacred_knowledge_proximity:.2f}) >= 0.7 - Chief minimum"
            )

    # Constitutional Override 2: Compliance Rate (Legal Llamas)
    if jr_compliance_rate is not None and jr_compliance_rate < 0.95:
        if final_strategy < Strategy.COLLABORATIVE_TRIAD:
            final_strategy = Strategy.COLLABORATIVE_TRIAD
            escalation_triggered = True
            escalation_reasons.append(
                f"Jr compliance rate ({jr_compliance_rate:.2%}) below 95% threshold"
            )

    # Performance Override 3: Success Rate
    if jr_success_rate is not None and jr_success_rate < 0.5:
        if final_strategy < Strategy.COLLABORATIVE_TRIAD:
            final_strategy = Strategy.COLLABORATIVE_TRIAD
            escalation_triggered = True
            escalation_reasons.append(
                f"Jr success rate ({jr_success_rate:.2%}) below 50% for this task type"
            )

    # Determine assignments based on strategy
    assigned_jr = jr_name
    assigned_chief = None
    assigned_triads = []

    if final_strategy == Strategy.COLLABORATIVE_TRIAD:
        assigned_chief = get_triad_chief(jr_name)
        assigned_triads = [get_jr_triad(jr_name)]
    elif final_strategy == Strategy.DELIBERATIVE_CROSS_TRIAD:
        assigned_chief = "TPM"
        assigned_triads = ["IT", "InfoSec", "Financial"]

    return StrategyDecision(
        strategy=final_strategy,
        reason=reason if not escalation_triggered else f"{reason} [ESCALATED]",
        escalation_triggered=escalation_triggered,
        escalation_reason="; ".join(escalation_reasons) if escalation_reasons else None,
        assigned_jr=assigned_jr,
        assigned_chief=assigned_chief,
        assigned_triads=assigned_triads
    )


def get_triad_chief(jr_name: str) -> str:
    """Get the Chief for a Jr's triad."""
    triad_chiefs = {
        "it_triad_jr": "it_triad_chief",
        "infosec_triad_jr": "infosec_triad_chief",
        "financial_triad_jr": "financial_triad_chief"
    }
    return triad_chiefs.get(jr_name.lower(), "unknown_chief")


def get_jr_triad(jr_name: str) -> str:
    """Get the triad name for a Jr."""
    if "it" in jr_name.lower():
        return "IT"
    elif "infosec" in jr_name.lower() or "security" in jr_name.lower():
        return "InfoSec"
    elif "financial" in jr_name.lower() or "finance" in jr_name.lower():
        return "Financial"
    return "Unknown"


def should_escalate_mid_task(
    current_strategy: Strategy,
    success_probability: float,
    sacred_knowledge_touched: bool
) -> Tuple[bool, Optional[Strategy], str]:
    """
    Check if a task should be escalated mid-execution.
    Called by Jr agents during task execution.
    """
    if sacred_knowledge_touched and current_strategy < Strategy.COLLABORATIVE_TRIAD:
        return (True, Strategy.COLLABORATIVE_TRIAD,
                "Sacred knowledge touched during execution")

    if success_probability < 0.3 and current_strategy < Strategy.COLLABORATIVE_TRIAD:
        return (True, Strategy.COLLABORATIVE_TRIAD,
                f"Success probability dropped to {success_probability:.2%}")

    return (False, None, "")


# Example usage
if __name__ == '__main__':
    test_cases = [
        # (complexity, sacred, jr_name, success_rate, compliance_rate)
        (0.15, 0.0, "it_triad_jr", 0.85, 0.98),  # Simple, good Jr
        (0.35, 0.1, "it_triad_jr", 0.75, 0.97),  # Moderate, good Jr
        (0.60, 0.2, "it_triad_jr", 0.65, 0.96),  # Complex
        (0.85, 0.3, "it_triad_jr", 0.70, 0.95),  # Expert
        (0.30, 0.8, "it_triad_jr", 0.80, 0.99),  # Simple but sacred!
        (0.25, 0.1, "it_triad_jr", 0.40, 0.94),  # Simple but struggling Jr
        (0.20, 0.0, "it_triad_jr", 0.90, 0.92),  # Simple but low compliance
    ]

    for complexity, sacred, jr, success, compliance in test_cases:
        decision = select_strategy(complexity, sacred, jr, success, compliance)
        print(f"\nComplexity={complexity:.2f} Sacred={sacred:.2f} "
              f"Success={success:.2%} Compliance={compliance:.2%}")
        print(f"  Strategy: {decision.strategy.value}")
        print(f"  Reason: {decision.reason}")
        if decision.escalation_triggered:
            print(f"  WARNING: ESCALATED: {decision.escalation_reason}")
        print(f"  Assigned: Jr={decision.assigned_jr}, "
              f"Chief={decision.assigned_chief}, Triads={decision.assigned_triads}")
