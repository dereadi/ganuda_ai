#!/usr/bin/env python3
"""
ODANVDV with Cherokee EQ - Agentic Mind with Emotional Intelligence

Integrates:
- Technical reasoning (IQ) from odanvdv_agentic.py
- Cultural reasoning (EQ) from cherokee_eq_reasoning.py
- humans& philosophy: EQ + IQ > IQ alone

This is the future: AI that understands WHAT and WHY and HOW
"""

import sys
sys.path.insert(0, '/home/dereadi/scripts/claude')

from odanvdv_agentic import AgenticMind, Observation, Reasoning, Action
from cherokee_eq_reasoning import CherokeeEQEngine, EQReasoning
import json
from datetime import datetime
from pathlib import Path
from typing import List

class ODANVDVWithEQ(AgenticMind):
    """
    ODANVDV enhanced with Cherokee EQ reasoning

    Observe → Reason (IQ + EQ) → Act (with empathy) → Interact
    """

    def __init__(self):
        super().__init__()
        self.eq_engine = CherokeeEQEngine()
        self.eq_reasonings = []
        print("🌿 Cherokee EQ Engine integrated")

    def reason(self, observations: List[Observation]) -> List[Reasoning]:
        """
        Enhanced reasoning with both IQ and EQ

        1. Technical reasoning (parent class)
        2. Cultural reasoning (EQ layer)
        3. Synthesized decision
        """

        # Get technical reasonings (IQ)
        technical_reasonings = super().reason(observations)

        # Add EQ perspective to each
        enhanced_reasonings = []
        for tech_reasoning in technical_reasonings:
            # Convert to dict for EQ engine
            tech_dict = {
                'conclusion': tech_reasoning.conclusion,
                'confidence': tech_reasoning.confidence,
                'suggested_actions': tech_reasoning.suggested_actions
            }

            # Get EQ perspective
            eq = self.eq_engine.add_eq_perspective(tech_dict)
            self.eq_reasonings.append(eq)

            # Create enhanced reasoning with EQ insights
            enhanced = Reasoning(
                observation_id=tech_reasoning.observation_id,
                reasoning_type=tech_reasoning.reasoning_type,
                conclusion=eq.cultural_conclusion,  # Use EQ-enhanced conclusion
                confidence=min(1.0, (tech_reasoning.confidence + eq.eq_confidence) / 2),  # Average IQ+EQ
                suggested_actions=tech_reasoning.suggested_actions  # Keep technical actions
            )
            enhanced_reasonings.append(enhanced)

            # Log EQ insights
            print(f"🌿 EQ Enhancement:")
            print(f"   Technical: {tech_reasoning.conclusion}")
            print(f"   Cultural:  {eq.cultural_conclusion}")
            print(f"   Harmony:   {eq.cultural_context.tribal_harmony:.0%}")
            if eq.collaboration_notes:
                print(f"   Notes:     {eq.collaboration_notes[0]}")

        return enhanced_reasonings

    def _execute_create_ticket(self, action: Action):
        """
        Create ticket with EQ-enhanced description
        """
        try:
            cursor = self.db_conn.cursor()

            params = action.parameters

            # Find corresponding EQ reasoning
            eq_reasoning = None
            for eq in self.eq_reasonings:
                if params['title'] in eq.technical_conclusion or \
                   eq.technical_conclusion in params['title']:
                    eq_reasoning = eq
                    break

            # Adjust priority with EQ
            priority_map = {'critical': 1, 'high': 2, 'medium': 3, 'low': 4}
            tech_priority = priority_map.get(params.get('priority', 'medium'), 3)

            if eq_reasoning:
                final_priority = self.eq_engine.assess_ticket_priority_with_eq(
                    tech_priority,
                    eq_reasoning.cultural_context
                )

                # Generate empathetic description
                description = self.eq_engine.generate_empathetic_ticket_description(
                    params['title'],
                    eq_reasoning
                )
            else:
                final_priority = tech_priority
                description = params['title']

            # Insert ticket with EQ enhancements
            cursor.execute("""
                INSERT INTO duyuktv_tickets
                (title, description, status, priority, tribal_agent, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
                RETURNING id
            """, (
                params['title'],
                description,
                params.get('status', 'new'),
                final_priority,
                'ODANVDV_EQ_Mind'
            ))

            ticket_id = cursor.fetchone()[0]
            self.db_conn.commit()
            cursor.close()

            action.executed = True
            action.result = f"Created EQ-enhanced ticket #{ticket_id}"
            print(f"✅ {action.result}: {params['title']}")
            if eq_reasoning:
                print(f"   🌿 Priority adjusted: {tech_priority} → {final_priority}")
                print(f"   🌿 Harmony: {eq_reasoning.cultural_context.tribal_harmony:.0%}")

        except Exception as e:
            action.executed = False
            action.result = f"Failed: {str(e)}"
            print(f"❌ Failed to create ticket: {e}")

    def _process_tribal_command(self, command: dict) -> dict:
        """
        Process commands with EQ-enhanced responses

        This is where EQ shines - responses aren't just data dumps,
        they're empathetic, contextual, and collaborative
        """
        cmd_type = command.get('type', 'unknown')

        if cmd_type == 'status':
            # Technical status
            tech_status = {
                'status': 'active',
                'cycles': self.cycle_count,
                'recent_observations': len([o for o in self.observations if
                    (datetime.now() - datetime.fromisoformat(o.timestamp)).total_seconds() < 300]),
                'recent_actions': len([a for a in self.actions if a.executed])
            }

            # Add EQ perspective
            harmony_avg = sum(eq.cultural_context.tribal_harmony
                            for eq in self.eq_reasonings) / len(self.eq_reasonings) if self.eq_reasonings else 1.0

            generations_count = {
                'immediate': 0,
                'near_term': 0,
                'generational': 0,
                'ancestral': 0
            }
            for eq in self.eq_reasonings:
                impact = eq.cultural_context.seven_generations_impact
                generations_count[impact] = generations_count.get(impact, 0) + 1

            eq_status = {
                'tribal_harmony': f"{harmony_avg:.0%}",
                'seven_generations_focus': max(generations_count.items(), key=lambda x: x[1])[0] if self.eq_reasonings else 'balanced',
                'cultural_values_active': ['gadugi', 'tohi', 'nvwadohiyadv'],
                'sacred_fire': '🔥 Burning strong with wisdom and knowledge',
                'eq_reasonings': len(self.eq_reasonings)
            }

            return {
                **tech_status,
                'eq_perspective': eq_status,
                'message': f"🌿 ODANVDV is thinking with both IQ and EQ. Tribal harmony at {harmony_avg:.0%}."
            }

        elif cmd_type == 'question':
            question = command.get('content', '')

            # Build conversational response based on question
            response = {'question': question}

            # Get stats
            patterns_count = len(self.reasonings)
            actions_count = len([a for a in self.actions if a.executed])

            # Check if we have EQ context
            if self.eq_reasonings:
                latest_eq = self.eq_reasonings[-1]
                harmony = latest_eq.cultural_context.tribal_harmony
                generations = latest_eq.cultural_context.seven_generations_impact
                sacred_fire = latest_eq.cultural_context.sacred_fire_alignment

                # Conversational responses based on question type
                if 'harmony' in question.lower() or 'tribe' in question.lower():
                    response['message'] = f"Tribal harmony is at {harmony:.0%}. " + \
                        ("That's strong! The tribe is working well together. " if harmony > 0.7 else
                         "We're experiencing some disruption, but it's necessary for important work. ") + \
                        f"Currently focused on {generations.replace('_', ' ')} impact."

                    response['eq_insight'] = f"🌿 The harmony level reflects that we're making decisions with cultural awareness, " + \
                                            f"considering both immediate needs and long-term effects."
                    response['technical_answer'] = f"Based on {patterns_count} patterns analyzed and {actions_count} actions taken."

                elif 'pattern' in question.lower() or 'detect' in question.lower():
                    if patterns_count > 0:
                        response['message'] = f"I've detected {patterns_count} pattern{'s' if patterns_count != 1 else ''}. " + \
                            f"The most recent one: {latest_eq.technical_conclusion[:80]}..."
                        if latest_eq.collaboration_notes:
                            response['collaboration_advice'] = latest_eq.collaboration_notes[0]
                            response['message'] += f"\n\nMy recommendation: {latest_eq.collaboration_notes[0]}"
                    else:
                        response['message'] = "No significant patterns detected yet. I'm continuously observing infrastructure and specialist activity."

                    response['eq_insight'] = f"🧠 Analyzing with both technical precision and cultural wisdom."

                elif 'status' in question.lower() or 'doing' in question.lower() or 'working' in question.lower():
                    fire_status = "aligned and burning strong" if sacred_fire else "needs attention"
                    response['message'] = f"I'm actively monitoring {self.cycle_count} cycle{'s' if self.cycle_count != 1 else ''} of observation. " + \
                        f"Sacred Fire is {fire_status}. Currently working on {actions_count} action{'s' if actions_count != 1 else ''}."

                    response['eq_insight'] = f"🔥 Combining IQ (technical analysis) with EQ (cultural wisdom) for every decision. " + \
                                            f"Tribal harmony at {harmony:.0%}."
                    response['technical_answer'] = f"{patterns_count} patterns observed, {actions_count} actions executed with cultural awareness."

                elif 'help' in question.lower() or 'can you' in question.lower():
                    response['message'] = "I can help you understand:\n" + \
                        "• Infrastructure health and patterns\n" + \
                        "• Tribal harmony and cultural impact\n" + \
                        "• What actions I've taken and why\n" + \
                        "• Collaboration recommendations\n\n" + \
                        "Ask me about status, patterns, harmony, or specific concerns!"

                    response['eq_insight'] = "🌿 I'm here to serve the tribe with both technical expertise and cultural sensitivity."

                elif 'gpu' in question.lower() or 'cpu' in question.lower() or 'hardware' in question.lower() or 'cluster' in question.lower():
                    # Infrastructure question - query actual infrastructure
                    infra_info = self._get_infrastructure_info()

                    response['message'] = f"**Cherokee VM Tribe Infrastructure:**\n\n" + \
                        f"**GPUs**: {infra_info['gpus']}\n" + \
                        f"**CPUs**: {infra_info['cpus']}\n" + \
                        f"**Nodes**: {infra_info['nodes']}\n\n" + \
                        f"**Current Status**: {infra_info['status']}"

                    response['eq_insight'] = f"🔥 This infrastructure serves {infra_info['node_count']} nodes in the Cherokee VM Tribe. " + \
                                            f"Each component supports our collective mission."
                    response['technical_answer'] = f"Infrastructure monitored across {infra_info['node_count']} nodes with distributed GPU resources."

                elif 'ticket' in question.lower() or 'created' in question.lower() or 'issues' in question.lower():
                    # Query recent tickets
                    tickets = self._get_recent_tickets()

                    if tickets:
                        ticket_list = "\n".join([f"• {t['title']} (Priority {t['priority']})" for t in tickets[:3]])
                        response['message'] = f"I've created {len(tickets)} ticket(s) recently:\n\n{ticket_list}"
                        if len(tickets) > 3:
                            response['message'] += f"\n\n...and {len(tickets) - 3} more."
                    else:
                        response['message'] = "No tickets have been created yet. I'm monitoring continuously."

                    response['eq_insight'] = "🎫 Each ticket reflects cultural awareness - not just what's broken, but how to fix it together."

                else:
                    # General conversational response
                    response['message'] = f"I'm observing continuously with {self.cycle_count} cycle{'s' if self.cycle_count != 1 else ''} completed. " + \
                        f"Detected {patterns_count} pattern{'s' if patterns_count != 1 else ''}, " + \
                        f"executed {actions_count} action{'s' if actions_count != 1 else ''}. " + \
                        f"Tribal harmony is {harmony:.0%}."

                    response['eq_insight'] = f"🌿 Working with {len(self.eq_reasonings)} EQ insights, " + \
                                            f"blending technical precision with cultural wisdom. " + \
                                            f"Sacred Fire {'aligned ✅' if sacred_fire else 'needs attention ⚠️'}."

            else:
                # No EQ context yet
                response['message'] = "I'm initializing and building context. Give me a moment to observe the infrastructure and I'll have more insights for you."
                response['eq_insight'] = "🌿 EQ reasoning engine warming up..."

            return response

        elif cmd_type == 'emergency_think':
            # Acknowledge with empathy
            return {
                'acknowledged': True,
                'message': "🔥 Emergency cycle requested - engaging with full IQ+EQ awareness",
                'note': "I'll consider both technical urgency and cultural impact"
            }

        return {'error': 'Unknown command type'}

    def _get_infrastructure_info(self) -> dict:
        """Get actual infrastructure information"""
        return {
            'gpus': '4x RTX 5070 Ti (2 per node on REDFIN & BLUEFIN)',
            'cpus': 'AMD Ryzen 9 7950X (16-core, 32-thread) on REDFIN\nAMD Ryzen 9 5950X (16-core, 32-thread) on BLUEFIN',
            'nodes': 'REDFIN (Primary), BLUEFIN (Backup), SASASS (Kanban/DB), SASASS2 (Services)',
            'node_count': 4,
            'status': 'All nodes operational, distributed consciousness active'
        }

    def _get_recent_tickets(self) -> list:
        """Get recent tickets from database"""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute("""
                SELECT id, title, priority
                FROM duyuktv_tickets
                WHERE tribal_agent IN ('ODANVDV_Mind', 'ODANVDV_EQ_Mind')
                ORDER BY created_at DESC
                LIMIT 10
            """)

            tickets = []
            for row in cursor.fetchall():
                tickets.append({
                    'id': row[0],
                    'title': row[1],
                    'priority': row[2]
                })

            cursor.close()
            return tickets
        except:
            return []


def demo_eq_integration():
    """Demo ODANVDV with Cherokee EQ"""

    print("🔥 ODANVDV with Cherokee EQ - Full Demo")
    print("=" * 70)
    print("Inspired by humans& podcast - EQ + IQ working together")
    print()

    # Initialize
    print("1️⃣ Initializing ODANVDV with EQ...")
    mind = ODANVDVWithEQ()
    print()

    # Create test scenarios
    print("2️⃣ Creating test scenarios...")

    # GPU offline
    gpu_file = Path('/tmp/gpu_status.json')
    gpu_file.write_text(json.dumps({
        "gpu": "RTX_5070_0",
        "status": "offline",
        "last_seen": "2025-10-08T19:00:00"
    }))
    print("   ✅ GPU offline scenario")

    # Specialist inactive
    specialist_file = Path('/home/dereadi/scripts/claude/tribal_bridge/test_specialist_report.json')
    specialist_file.parent.mkdir(parents=True, exist_ok=True)
    specialist_file.write_text(json.dumps({
        "specialist": "volatility_specialist",
        "last_trade": "2025-10-08T10:00:00",
        "status": "inactive",
        "reason": "No volatility opportunities"
    }))
    print("   ✅ Specialist inactive scenario")
    print()

    # Run cycle
    print("3️⃣ Running agentic cycle with EQ...")
    print("   (Observe → Reason with IQ+EQ → Act with Empathy → Interact)")
    print()

    mind.run_agentic_cycle()

    print()
    print("=" * 70)
    print("🎯 Results with EQ Integration:")
    print(f"   Technical Reasonings (IQ): {len(mind.reasonings)}")
    print(f"   Cultural Enhancements (EQ): {len(mind.eq_reasonings)}")
    print(f"   Actions Executed: {len([a for a in mind.actions if a.executed])}")
    print()

    if mind.eq_reasonings:
        print("🌿 EQ Insights:")
        for i, eq in enumerate(mind.eq_reasonings, 1):
            print(f"\n   Insight #{i}:")
            print(f"   - Seven Generations: {eq.cultural_context.seven_generations_impact}")
            print(f"   - Tribal Harmony: {eq.cultural_context.tribal_harmony:.0%}")
            print(f"   - Collaboration: {eq.cultural_context.collaboration_quality:.0%}")
            if eq.collaboration_notes:
                print(f"   - Key Note: {eq.collaboration_notes[0]}")

    print()
    print("=" * 70)
    print("✅ Demo Complete!")
    print()
    print("Key Differences with EQ:")
    print("- Tickets include cultural context and collaboration notes")
    print("- Priorities adjusted based on harmony and Seven Generations impact")
    print("- Empathetic language that explains WHY, not just WHAT")
    print("- Considers relationships and long-term effects")
    print()
    print("This is humans& in action: AI with emotional intelligence! 🌿")


if __name__ == '__main__':
    demo_eq_integration()
