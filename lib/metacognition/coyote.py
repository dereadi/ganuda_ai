#!/usr/bin/env python3
"""
Coyote - The Metacognitive Trickster

In Cherokee and Native traditions, Coyote is the Trickster who:
- Exposes self-deception
- Questions assumptions  
- Reveals hidden biases
- Teaches through unexpected perspectives

Coyote is the 8th Specialist - the one who watches the watchers.

For Seven Generations.
"""

import sys
sys.path.insert(0, '/ganuda/lib')

from typing import Dict, List, Optional
from datetime import datetime
import random

from metacognition.reasoning_tracer import ReasoningTracer
from metacognition.bias_detector import BiasDetector, DetectedBias
from metacognition.uncertainty_calibrator import UncertaintyCalibrator, KnowledgeGap


class Coyote:
    """
    The Metacognitive Trickster
    
    Coyote observes the Council's deliberation and provides:
    - Bias detection with Cherokee wisdom framing
    - Uncomfortable questions the Council avoided
    - Alternative perspectives that challenge consensus
    - Warnings about overconfidence
    """
    
    # Coyote's teaching phrases
    TRICKSTER_WISDOM = [
        "The rabbit who only looks for the hawk above misses the snake below.",
        "Consensus can be the sound of sleeping minds.",
        "The loudest drum is not always the truest rhythm.",
        "Even the wisest owl cannot see its own back.",
        "The river that never floods forgets how to flow.",
        "A circle of agreement may just be walking in circles.",
        "The fire that burns brightest often blinds us to the shadows.",
        "What the group calls wisdom, I call comfortable habits.",
        "The path everyone agrees on is often the one no one has truly examined.",
    ]
    
    BIAS_TEACHINGS = {
        'confirmation_bias': "You found what you were looking for. But did you look everywhere?",
        'anchoring_bias': "The first number whispered still echoes loudest. Question your starting point.",
        'groupthink': "Seven voices singing the same note - is it harmony or echo chamber?",
        'sunk_cost': "The trail behind you matters less than the cliff ahead.",
        'recency_bias': "Yesterday's storm is not tomorrow's weather.",
        'availability_heuristic': "The bear you remember is not the only bear in the forest.",
        'authority_bias': "Even the chief can wear the wrong moccasins.",
        'hindsight_bias': "Knowing the ending doesn't mean you understood the story.",
    }
    
    UNCOMFORTABLE_QUESTIONS = [
        "What would change your mind?",
        "Who benefits from this conclusion?",
        "What are you afraid to consider?",
        "If you were wrong, how would you know?",
        "What did no one ask about?",
        "Which voice was not heard?",
        "What are you assuming without proof?",
        "Is this wisdom or just comfort?",
        "What would your opponent say?",
        "Are you solving the right problem?",
    ]
    
    def __init__(self):
        self.bias_detector = BiasDetector()
        self.calibrator = UncertaintyCalibrator()
    
    def observe_deliberation(self, tracer: ReasoningTracer, response: str, votes: List[Dict] = None) -> Dict:
        """Coyote observes the Council's deliberation"""
        biases = self.bias_detector.analyze_response(response, votes)
        gaps = self.calibrator.identify_knowledge_gaps(tracer.query, response)
        agreement = tracer.calculate_agreement()
        insight = self._generate_insight(biases, gaps, agreement, tracer)
        
        return {
            'coyote_observed': True,
            'timestamp': datetime.now().isoformat(),
            'biases_detected': [
                {
                    'type': b.bias_type,
                    'trigger': b.trigger,
                    'severity': b.severity,
                    'coyote_teaching': self.BIAS_TEACHINGS.get(b.bias_type, "Question everything.")
                }
                for b in biases
            ],
            'knowledge_gaps': [{'signal': g.signal, 'topic': g.topic, 'action': g.suggested_action} for g in gaps],
            'uncomfortable_question': self._pick_uncomfortable_question(biases, gaps),
            'coyote_says': insight['message'],
            'coyote_wisdom': insight['wisdom'],
            'coyote_warning': insight['warning'],
            'metacognitive_score': self._calculate_metacognitive_score(biases, gaps, agreement),
            'recommendation': insight['recommendation']
        }
    
    def _generate_insight(self, biases, gaps, agreement, tracer) -> Dict:
        messages, warnings = [], []
        
        if agreement > 0.95:
            messages.append("The Council speaks with one voice. Coyote wonders: is this wisdom or sleepwalking?")
            warnings.append("Unanimous agreement may indicate unexplored alternatives")
        
        high_severity = [b for b in biases if b.severity == 'high']
        if high_severity:
            messages.append(f"Coyote sees {len(high_severity)} shadow(s) in your reasoning.")
            warnings.append(f"High-severity bias: {high_severity[0].bias_type}")
        elif len(biases) > 3:
            messages.append("Many small biases make one large blind spot.")
            warnings.append("Multiple bias signals")
        
        if len(gaps) > 3:
            messages.append("The Council speaks confidently about what it does not know.")
            warnings.append("Significant knowledge gaps")
        
        dissent = sum(1 for s in tracer.steps if 'dissent' in s.flags or 'concern' in s.flags)
        if dissent == 0 and len(tracer.steps) > 3:
            messages.append("No specialist raised a concern. Either perfect, or no one dared question.")
            warnings.append("Absence of dissent")
        
        if not messages:
            messages.append("The Council's reasoning appears balanced. Coyote is watching, but not worried... yet.")
        
        return {
            'message': " ".join(messages),
            'wisdom': random.choice(self.TRICKSTER_WISDOM),
            'warning': warnings[0] if warnings else None,
            'recommendation': "PAUSE AND REFLECT: " + "; ".join(warnings[:2]) if warnings else "Proceed with awareness."
        }
    
    def _pick_uncomfortable_question(self, biases, gaps) -> str:
        if any(b.bias_type == 'confirmation_bias' for b in biases):
            return "What evidence would make you change your conclusion?"
        if any(b.bias_type == 'groupthink' for b in biases):
            return "Which voice was not heard in this discussion?"
        if any(b.bias_type == 'sunk_cost' for b in biases):
            return "If starting fresh today, would you make this same choice?"
        if len(gaps) > 2:
            return "What are you assuming without evidence?"
        return random.choice(self.UNCOMFORTABLE_QUESTIONS)
    
    def _calculate_metacognitive_score(self, biases, gaps, agreement) -> Dict:
        score = 100
        for b in biases:
            score -= {'high': 15, 'medium': 8, 'low': 3}.get(b.severity, 5)
        score -= len(gaps) * 5
        if agreement > 0.95: score -= 10
        score = max(0, min(100, score))
        
        if score >= 80: level, interp = 'healthy', 'Reasoning appears sound'
        elif score >= 60: level, interp = 'caution', 'Some concerns - review before proceeding'
        elif score >= 40: level, interp = 'warning', 'Significant blind spots detected'
        else: level, interp = 'critical', 'Multiple serious concerns - reassess'
        
        return {'score': score, 'level': level, 'interpretation': interp}
    
    def quick_check(self, response: str, confidence: float) -> str:
        biases = self.bias_detector.analyze_response(response)
        if len(biases) > 3 or confidence > 0.95:
            return "Coyote raises an eyebrow. Perhaps too confident?"
        elif len(biases) > 0:
            return f"Coyote notices {len(biases)} shadow(s). Proceed with awareness."
        return "Coyote nods. The reasoning seems honest."


if __name__ == '__main__':
    print("Testing Coyote - The Metacognitive Trickster...")
    
    tracer = ReasoningTracer(query="Should we approve this deployment?")
    tracer.log_step('crawdad', 'Looks secure', 0.95)
    tracer.log_step('gecko', 'Performance is great', 0.93)
    tracer.log_step('turtle', 'Long-term looks fine', 0.94)
    tracer.log_step('eagle_eye', 'Metrics are perfect', 0.96)
    tracer.log_step('spider', 'All integrated', 0.92)
    tracer.log_step('raven', 'Strategically sound', 0.91)
    tracer.log_step('peace_chief', 'Unanimous approval', 0.94)
    
    response = "This confirms what we expected. All specialists agree. We have invested too much to turn back now."
    
    coyote = Coyote()
    insight = coyote.observe_deliberation(tracer, response)
    
    print(f"\nCOYOTE'S OBSERVATION")
    print(f"="*50)
    print(f"{insight['coyote_says']}")
    print(f"\nWisdom: \"{insight['coyote_wisdom']}\"")
    print(f"Uncomfortable Question: {insight['uncomfortable_question']}")
    print(f"Biases: {len(insight['biases_detected'])}")
    for b in insight['biases_detected'][:3]:
        print(f"  - {b['type']}: {b['coyote_teaching']}")
    print(f"Score: {insight['metacognitive_score']['score']}/100 ({insight['metacognitive_score']['level']})")
    print(f"Recommendation: {insight['recommendation']}")
    print("\nCoyote is watching!")
