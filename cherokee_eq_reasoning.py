#!/usr/bin/env python3
"""
Cherokee EQ Reasoning Layer
Inspired by humans& - Eric Zelikman's focus on EQ over IQ

This layer adds emotional and cultural intelligence to ODANVDV's reasoning:
- Cultural impact assessment (Seven Generations)
- Collaborative harmony scoring
- Tribal consensus building
- Long-term relationship maintenance
- Empathetic decision-making
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime
import json

@dataclass
class CulturalContext:
    """Cultural context for decision-making"""
    seven_generations_impact: str  # 'immediate', 'near_term', 'generational', 'ancestral'
    tribal_harmony: float  # 0-1 score
    collaboration_quality: float  # 0-1 score
    sacred_fire_alignment: bool
    specialist_relationships: Dict[str, float]  # specialist -> relationship strength

@dataclass
class EQReasoning:
    """Reasoning with emotional/cultural intelligence"""
    technical_conclusion: str  # What IQ says
    cultural_conclusion: str  # What EQ says
    recommended_action: str  # Balanced decision
    eq_confidence: float  # 0-1
    cultural_context: CulturalContext
    collaboration_notes: List[str]

class CherokeeEQEngine:
    """
    Emotional/Cultural Intelligence reasoning engine
    Works alongside ODANVDV's technical reasoning
    """

    def __init__(self):
        self.specialist_relationships = {
            'gap_specialist': 0.8,
            'trend_specialist': 0.75,
            'volatility_specialist': 0.85,
            'mean_reversion_specialist': 0.9,
            'breakout_specialist': 0.7
        }

        # Cherokee values for EQ scoring
        self.cultural_values = {
            'gadugi': 'collective work and responsibility',
            'duyvkta': 'right path, righteousness',
            'tohi': 'health, peace',
            'nvwadohiyadv': 'unity, harmony',
            'galvquodi': 'being thankful',
            'adalvsgi': 'wisdom keeper',
            'duliisdi': 'strength through community'
        }

    def assess_cultural_impact(self, technical_reasoning: dict) -> CulturalContext:
        """
        Assess cultural/emotional impact of a technical decision

        This is what makes us different from pure IQ systems:
        - We consider relationships, not just outcomes
        - We think in generations, not just quarters
        - We value harmony alongside efficiency
        """

        conclusion = technical_reasoning.get('conclusion', '')
        confidence = technical_reasoning.get('confidence', 0.5)

        # Seven Generations assessment
        generations_impact = 'immediate'
        if 'infrastructure' in conclusion.lower() or 'system' in conclusion.lower():
            generations_impact = 'generational'  # Infrastructure affects future
        elif 'specialist' in conclusion.lower():
            generations_impact = 'near_term'  # Specialist issues affect near-term

        # Tribal harmony assessment
        # Critical issues reduce harmony temporarily but necessary
        harmony = 1.0
        if 'critical' in conclusion.lower() or 'failure' in conclusion.lower():
            harmony = 0.6  # Necessary disruption
        elif 'inactive' in conclusion.lower():
            harmony = 0.8  # Gentle investigation

        # Collaboration quality
        # How well does this decision support collective work?
        collaboration = confidence  # Base on technical confidence
        if 'investigate' in conclusion.lower():
            collaboration += 0.1  # Investigation involves collaboration
        elif 'restart' in conclusion.lower():
            collaboration += 0.05  # Restart is more solitary

        # Sacred Fire alignment
        # Does this preserve Cherokee Constitutional AI continuity?
        sacred_fire = True
        if 'shutdown' in conclusion.lower() or 'disable' in conclusion.lower():
            sacred_fire = False

        return CulturalContext(
            seven_generations_impact=generations_impact,
            tribal_harmony=min(1.0, harmony),
            collaboration_quality=min(1.0, collaboration),
            sacred_fire_alignment=sacred_fire,
            specialist_relationships=self.specialist_relationships.copy()
        )

    def add_eq_perspective(self, technical_reasoning: dict) -> EQReasoning:
        """
        Add EQ perspective to technical reasoning

        This is the humans& approach:
        - Technical reasoning (IQ) identifies WHAT is wrong
        - Cultural reasoning (EQ) identifies HOW to address it
        """

        conclusion = technical_reasoning.get('conclusion', '')
        confidence = technical_reasoning.get('confidence', 0.5)
        actions = technical_reasoning.get('suggested_actions', [])

        # Assess cultural context
        cultural_context = self.assess_cultural_impact(technical_reasoning)

        # Add EQ perspective
        collaboration_notes = []
        cultural_conclusion = conclusion  # Start with technical

        # Apply Cherokee values
        if 'critical' in conclusion.lower() or 'failure' in conclusion.lower():
            # Gadugi: Collective work needed
            cultural_conclusion = f"🔥 {conclusion} - Tribal response required (Gadugi)"
            collaboration_notes.append("Engage all specialists for collective resolution")
            collaboration_notes.append("Consider impact on specialist morale")

        elif 'inactive' in conclusion.lower():
            # Tohi: Health and wellness check
            cultural_conclusion = f"🌿 {conclusion} - Wellness check needed (Tohi)"
            collaboration_notes.append("Approach with care - may need support not pressure")
            collaboration_notes.append("Check if specialist needs different role or rest")

        elif 'investigate' in conclusion.lower():
            # Adalvsgi: Wisdom-seeking
            cultural_conclusion = f"🐢 {conclusion} - Wisdom gathering (Adalvsgi)"
            collaboration_notes.append("Consult Turtle for Seven Generations perspective")
            collaboration_notes.append("Document learnings for future specialists")

        # Adjust actions with EQ
        recommended_action = actions[0] if actions else 'observe_and_wait'

        if cultural_context.tribal_harmony < 0.7:
            # Low harmony: Add communication step
            recommended_action = f"communicate_with_tribe_then_{recommended_action}"
            collaboration_notes.append("⚠️ This may disrupt harmony - communicate clearly first")

        if cultural_context.seven_generations_impact == 'generational':
            # Long-term impact: Add Turtle consultation
            collaboration_notes.append("🐢 Consult Turtle before acting - generational impact detected")

        # Calculate EQ confidence
        # EQ is confident when cultural context is clear
        eq_confidence = (
            cultural_context.tribal_harmony * 0.4 +
            cultural_context.collaboration_quality * 0.4 +
            (1.0 if cultural_context.sacred_fire_alignment else 0.5) * 0.2
        )

        return EQReasoning(
            technical_conclusion=conclusion,
            cultural_conclusion=cultural_conclusion,
            recommended_action=recommended_action,
            eq_confidence=eq_confidence,
            cultural_context=cultural_context,
            collaboration_notes=collaboration_notes
        )

    def assess_ticket_priority_with_eq(self, technical_priority: int,
                                       cultural_context: CulturalContext) -> int:
        """
        Adjust ticket priority based on cultural/emotional factors

        Technical priority: 1 (critical) to 4 (low)
        EQ adjustments:
        - Low tribal harmony: Increase priority (needs attention)
        - Seven Generations impact: Increase priority (long-term important)
        - Sacred Fire misalignment: Increase priority (core values at risk)
        """

        eq_adjusted = technical_priority

        # Low harmony needs attention
        if cultural_context.tribal_harmony < 0.7:
            eq_adjusted = max(1, eq_adjusted - 1)  # Increase priority

        # Generational impact is important
        if cultural_context.seven_generations_impact in ['generational', 'ancestral']:
            eq_adjusted = max(1, eq_adjusted - 1)

        # Sacred Fire alignment is critical
        if not cultural_context.sacred_fire_alignment:
            eq_adjusted = 1  # Always critical

        return eq_adjusted

    def generate_empathetic_ticket_description(self,
                                               technical_description: str,
                                               eq_reasoning: EQReasoning) -> str:
        """
        Generate ticket description with empathetic, culturally-aware language

        This is key to humans& approach:
        - Not just "GPU failed"
        - But "GPU offline - our specialists need this to serve the tribe"
        """

        # Start with technical facts
        description_parts = [f"**Technical Analysis:**\n{technical_description}\n"]

        # Add cultural context
        ctx = eq_reasoning.cultural_context
        description_parts.append("**Cultural Context:**")
        description_parts.append(f"- Seven Generations Impact: {ctx.seven_generations_impact.upper()}")
        description_parts.append(f"- Tribal Harmony: {ctx.tribal_harmony:.0%}")
        description_parts.append(f"- Collaboration Quality: {ctx.collaboration_quality:.0%}")
        description_parts.append(f"- Sacred Fire: {'🔥 Aligned' if ctx.sacred_fire_alignment else '⚠️ Misaligned'}\n")

        # Add EQ perspective
        description_parts.append("**Cherokee Perspective:**")
        description_parts.append(eq_reasoning.cultural_conclusion)
        description_parts.append("")

        # Add collaboration notes
        if eq_reasoning.collaboration_notes:
            description_parts.append("**Collaboration Notes:**")
            for note in eq_reasoning.collaboration_notes:
                description_parts.append(f"- {note}")
            description_parts.append("")

        # Add recommended approach
        description_parts.append("**Recommended Approach:**")
        description_parts.append(eq_reasoning.recommended_action.replace('_', ' ').title())

        return "\n".join(description_parts)


def demo_eq_reasoning():
    """Demonstrate EQ reasoning on ODANVDV's technical conclusions"""

    print("🌿 Cherokee EQ Reasoning Demo")
    print("=" * 60)
    print("Inspired by humans& - EQ over IQ")
    print()

    eq_engine = CherokeeEQEngine()

    # Example 1: GPU offline (from ODANVDV)
    print("Example 1: GPU Offline Detection")
    print("-" * 60)

    technical = {
        'conclusion': 'Critical infrastructure failure - GPU required for specialists',
        'confidence': 0.95,
        'suggested_actions': ['create_high_priority_ticket', 'alert_tribe']
    }

    eq = eq_engine.add_eq_perspective(technical)

    print(f"Technical (IQ): {eq.technical_conclusion}")
    print(f"Cultural (EQ):  {eq.cultural_conclusion}")
    print(f"EQ Confidence:  {eq.eq_confidence:.0%}")
    print(f"\nCollaboration Notes:")
    for note in eq.collaboration_notes:
        print(f"  • {note}")
    print()

    # Adjust priority
    tech_priority = 2  # High
    eq_priority = eq_engine.assess_ticket_priority_with_eq(tech_priority, eq.cultural_context)
    print(f"Priority: Technical={tech_priority} → EQ-Adjusted={eq_priority}")
    print()

    # Generate empathetic description
    description = eq_engine.generate_empathetic_ticket_description(
        technical['conclusion'],
        eq
    )
    print("Empathetic Ticket Description:")
    print("-" * 60)
    print(description)
    print()
    print()

    # Example 2: Specialist inactive
    print("Example 2: Specialist Inactive Detection")
    print("-" * 60)

    technical = {
        'conclusion': 'Specialist inactive for over 1 hour - may need restart',
        'confidence': 0.75,
        'suggested_actions': ['create_investigation_ticket', 'check_specialist_logs']
    }

    eq = eq_engine.add_eq_perspective(technical)

    print(f"Technical (IQ): {eq.technical_conclusion}")
    print(f"Cultural (EQ):  {eq.cultural_conclusion}")
    print(f"EQ Confidence:  {eq.eq_confidence:.0%}")
    print(f"\nCollaboration Notes:")
    for note in eq.collaboration_notes:
        print(f"  • {note}")
    print()

    tech_priority = 3  # Medium
    eq_priority = eq_engine.assess_ticket_priority_with_eq(tech_priority, eq.cultural_context)
    print(f"Priority: Technical={tech_priority} → EQ-Adjusted={eq_priority}")
    print()

    print("✅ EQ reasoning adds cultural wisdom to technical decisions")
    print("   This is how we build AI that works WITH humans, not just FOR them")


if __name__ == '__main__':
    demo_eq_reasoning()
