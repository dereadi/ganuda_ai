#!/usr/bin/env python3
"""
Council Integration - Adds metacognition to Council votes

Wraps the existing Council vote flow with:
- Reasoning tracing
- Bias detection  
- Uncertainty calibration
- Coyote's observation

For Seven Generations.
"""

import sys
sys.path.insert(0, '/ganuda/lib')

import json
import hashlib
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from typing import Dict, List, Optional

from metacognition.reasoning_tracer import ReasoningTracer
from metacognition.bias_detector import BiasDetector
from metacognition.uncertainty_calibrator import UncertaintyCalibrator
from metacognition.coyote import Coyote
from metacognition.resonance import ResonanceDetector
import os


class MetacognitiveCouncil:
    """
    Wraps Council deliberation with metacognitive monitoring
    
    Usage:
        mc = MetacognitiveCouncil(db_config)
        
        # During council vote
        mc.start_deliberation(question, context)
        
        # As each specialist responds
        mc.record_specialist_response('crawdad', response, confidence)
        
        # After synthesis
        result = mc.complete_deliberation(synthesis, votes)
        
        # Result includes metacognition section
    """
    
    def __init__(self, db_config: Dict):
        self.db_config = db_config
        self.tracer: Optional[ReasoningTracer] = None
        self.coyote = Coyote()
        self.calibrator = UncertaintyCalibrator()
        self.bias_detector = BiasDetector()
        self.resonance = ResonanceDetector()
        
    def start_deliberation(self, question: str, context: str = None):
        """Start tracking a new deliberation"""
        self.tracer = ReasoningTracer(query=question, context=context)
        return self.tracer.session_id
    
    def record_specialist_response(self, 
                                   specialist: str, 
                                   response: str, 
                                   confidence: float = 0.8,
                                   concerns: List[str] = None):
        """Record a specialist's response"""
        if not self.tracer:
            raise ValueError("Deliberation not started - call start_deliberation first")
        
        flags = []
        if concerns:
            flags.append('concern')
            for concern in concerns:
                self.tracer.mark_uncertainty(
                    topic=concern[:50],
                    reason=f"{specialist} raised concern",
                    confidence_impact=-0.05
                )
        
        self.tracer.log_step(
            specialist=specialist,
            thought=response[:500],
            confidence=confidence,
            flags=flags,
            metadata={'concerns': concerns or []}
        )
    
    def complete_deliberation(self,
                             synthesis: str,
                             votes: List[Dict] = None,
                             raw_confidence: float = 0.8) -> Dict:
        """
        Complete deliberation and generate metacognitive analysis
        
        Returns enhanced result with metacognition section
        """
        if not self.tracer:
            raise ValueError("Deliberation not started")
        
        # Detect biases in synthesis
        biases = self.bias_detector.analyze_response(synthesis, votes)
        for bias in biases:
            self.tracer.detect_bias(bias.bias_type, bias.trigger, bias.severity)
        
        # Identify knowledge gaps
        gaps = self.calibrator.identify_knowledge_gaps(self.tracer.query, synthesis)
        for gap in gaps:
            self.tracer.mark_uncertainty(gap.signal, gap.suggested_action)
        
        # Calibrate confidence
        agreement = self.tracer.calculate_agreement()
        calibration = self.calibrator.calibrate_confidence(
            raw_confidence=raw_confidence,
            topic=self._extract_topic(self.tracer.query),
            specialist_agreement=agreement,
            uncertainty_count=len(self.tracer.uncertainty_markers)
        )
        
        # Analyze resonance patterns
        resonance_patterns = self.resonance.analyze_resonance(self.tracer)
        resonance_summary = self._summarize_resonance(resonance_patterns)
        
        # Get Coyote's observation
        coyote_insight = self.coyote.observe_deliberation(self.tracer, synthesis, votes)
        
        # Get full metacognitive summary
        meta_summary = self.tracer.get_metacognitive_summary()
        
        # Store in database
        decision_hash = self._store_reflection(
            synthesis=synthesis,
            calibration=calibration,
            coyote_insight=coyote_insight,
            meta_summary=meta_summary,
            votes=votes
        )
        
        return {
            'decision_hash': decision_hash,
            'calibrated_confidence': calibration.calibrated_confidence,
            'confidence_level': calibration.level,
            'confidence_caveat': calibration.caveat,
            'metacognition': {
                'session_id': self.tracer.session_id,
                'reasoning_steps': meta_summary['reasoning']['total_steps'],
                'specialists_consulted': meta_summary['reasoning']['specialists_consulted'],
                'biases_detected': len(biases),
                'bias_types': list(set(b.bias_type for b in biases)),
                'uncertainty_areas': len(gaps),
                'agreement_level': round(agreement, 3),
                'self_assessment': meta_summary['assessment']['self_assessment'],
                'metacognitive_score': coyote_insight['metacognitive_score']
            },
            'resonance': resonance_summary,
            'coyote': {
                'says': coyote_insight['coyote_says'],
                'wisdom': coyote_insight['coyote_wisdom'],
                'uncomfortable_question': coyote_insight['uncomfortable_question'],
                'recommendation': coyote_insight['recommendation']
            }
        }
    
    def _summarize_resonance(self, resonance_result: Dict) -> Dict:
        """Summarize resonance patterns for API response"""
        if not resonance_result:
            return {
                'level': 'neutral',
                'score': 0.5,
                'harmony_count': 0,
                'dissonance_count': 0,
                'creative_tensions': 0,
                'patterns': [],
                'insight': 'No resonance analysis available'
            }
        
        # Extract from resonance detector output
        harmonic = resonance_result.get('harmonic_themes', [])
        dissonant = resonance_result.get('dissonant_areas', [])
        tensions = resonance_result.get('creative_tensions', [])
        
        # Map resonance level
        level_text = resonance_result.get('resonance_level', '')
        if 'Strong Alignment' in level_text:
            level = 'harmonic'
        elif 'Mixed' in level_text or 'divergence' in level_text.lower():
            level = 'mixed'
        elif 'Dissonance' in level_text or 'conflict' in level_text.lower():
            level = 'dissonant'
        else:
            level = 'neutral'
        
        # Build patterns list
        patterns = []
        for h in harmonic[:2]:
            patterns.append({
                'type': 'harmony',
                'theme': h.get('theme', 'unknown'),
                'specialists': h.get('specialists', []),
                'strength': h.get('strength', 0.5)
            })
        for t in tensions[:2]:
            patterns.append({
                'type': 'creative_tension',
                'theme': t.get('theme', 'unknown'),
                'specialist': t.get('specialist', 'unknown'),
                'insight': t.get('potential_insight', '')
            })
        
        return {
            'level': level,
            'score': resonance_result.get('overall_resonance', 0.5),
            'harmony_count': len(harmonic),
            'dissonance_count': len(dissonant),
            'creative_tensions': len(tensions),
            'patterns': patterns,
            'insight': resonance_result.get('insight', 'Council in neutral alignment'),
            'recommendation': resonance_result.get('recommendation', '')
        }

    def _extract_topic(self, query: str) -> str:
        """Extract topic from query"""
        query_lower = query.lower()
        if 'deploy' in query_lower or 'release' in query_lower:
            return 'deployment'
        elif 'security' in query_lower or 'auth' in query_lower:
            return 'security'
        elif 'performance' in query_lower or 'speed' in query_lower:
            return 'performance'
        elif 'config' in query_lower or 'setting' in query_lower:
            return 'configuration'
        return 'default'
    
    def _store_reflection(self, synthesis, calibration, coyote_insight, meta_summary, votes) -> str:
        """Store reflection in database"""
        decision_hash = hashlib.sha256(
            f"{self.tracer.session_id}:{datetime.now().isoformat()}".encode()
        ).hexdigest()[:32]
        
        try:
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor()
            
            cur.execute("""
                INSERT INTO decision_reflections
                (decision_hash, session_id, query, response, confidence, calibrated_confidence,
                 biases_detected, uncertainty_areas, specialist_votes, reasoning_trace,
                 coyote_observation, metacognitive_score)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                decision_hash,
                self.tracer.session_id,
                self.tracer.query[:500],
                synthesis[:2000],
                meta_summary['assessment']['base_confidence'],
                calibration.calibrated_confidence,
                json.dumps(meta_summary['biases']),
                json.dumps(meta_summary['uncertainty']),
                json.dumps(votes or []),
                json.dumps(meta_summary),
                json.dumps(coyote_insight),
                coyote_insight['metacognitive_score']['score']
            ))
            
            # Store Coyote's wisdom if significant
            if coyote_insight['metacognitive_score']['score'] < 70:
                cur.execute("""
                    INSERT INTO coyote_wisdom_archive
                    (decision_hash, uncomfortable_question, coyote_says, wisdom_quote)
                    VALUES (%s, %s, %s, %s)
                """, (
                    decision_hash,
                    coyote_insight['uncomfortable_question'],
                    coyote_insight['coyote_says'],
                    coyote_insight['coyote_wisdom']
                ))
            
            conn.commit()
            cur.close()
            conn.close()
            
        except Exception as e:
            print(f"[METACOGNITION STORE ERROR] {e}")
        
        return decision_hash


# Quick integration function for existing gateway
def add_metacognition_to_council_response(
    question: str,
    responses: Dict[str, str],
    consensus: str,
    concerns: List[str],
    confidence: float,
    db_config: Dict
) -> Dict:
    """
    Quick function to add metacognition to existing council vote
    
    Args:
        question: The original question
        responses: Dict of specialist -> response
        consensus: Peace Chief synthesis
        concerns: List of concerns raised
        confidence: Raw confidence score
        db_config: Database config
        
    Returns:
        Metacognition section to add to response
    """
    mc = MetacognitiveCouncil(db_config)
    mc.start_deliberation(question)
    
    # Record each specialist
    for specialist, response in responses.items():
        # Extract concerns for this specialist
        spec_concerns = [c for c in concerns if specialist in c.lower()]
        conf = 0.7 if spec_concerns else 0.85
        mc.record_specialist_response(specialist, response, conf, spec_concerns)
    
    # Build votes list
    votes = [
        {'specialist': s, 'recommendation': 'PROCEED' if not concerns else 'CAUTION', 'confidence': 0.85}
        for s in responses.keys()
    ]
    
    # Complete and return metacognition
    return mc.complete_deliberation(consensus, votes, confidence)


if __name__ == '__main__':
    print("Testing MetacognitiveCouncil...")
    
    # Test config
    db_config = {
        'host': '192.168.132.222',
        'port': 5432,
        'database': 'zammad_production',
        'user': 'claude',
        'password': os.environ.get('CHEROKEE_DB_PASS', '')
    }
    
    # Simulate council vote
    mc = MetacognitiveCouncil(db_config)
    mc.start_deliberation("Should we deploy the new gateway version?")
    
    mc.record_specialist_response('crawdad', 'Security audit passed', 0.92)
    mc.record_specialist_response('gecko', 'Performance is acceptable', 0.88)
    mc.record_specialist_response('turtle', 'Long-term impact looks positive', 0.85)
    mc.record_specialist_response('eagle_eye', 'Metrics are healthy', 0.90)
    mc.record_specialist_response('spider', 'Integrations tested', 0.87)
    mc.record_specialist_response('raven', 'Strategic timing good', 0.82)
    mc.record_specialist_response('peace_chief', 'Consensus to proceed', 0.88)
    
    synthesis = "Based on council review, deployment is recommended. All specialists concur."
    
    result = mc.complete_deliberation(synthesis, raw_confidence=0.88)
    
    print(f"\nMetacognitive Analysis:")
    print(f"  Decision Hash: {result['decision_hash']}")
    print(f"  Calibrated Confidence: {result['calibrated_confidence']}")
    print(f"  Level: {result['confidence_level']}")
    print(f"  Caveat: {result['confidence_caveat']}")
    print(f"\n  Metacognition:")
    print(f"    Steps: {result['metacognition']['reasoning_steps']}")
    print(f"    Biases: {result['metacognition']['biases_detected']}")
    print(f"    Score: {result['metacognition']['metacognitive_score']}")
    print(f"\n  Coyote Says: {result['coyote']['says'][:100]}...")
    print(f"  Question: {result['coyote']['uncomfortable_question']}")
    
    print("\n✅ MetacognitiveCouncil working!")
