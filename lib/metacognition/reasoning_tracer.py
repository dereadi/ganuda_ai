#!/usr/bin/env python3
"""
Reasoning Tracer - Captures the Council's inner monologue

Traces reasoning steps during deliberation, enabling:
- Audit of how decisions were made
- Detection of reasoning patterns
- Input for bias detection and reflection

For Seven Generations.
"""

import json
import hashlib
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, field, asdict


@dataclass
class ReasoningStep:
    """A single step in the reasoning process"""
    step_number: int
    timestamp: str
    specialist: str
    thought: str
    confidence: float
    flags: List[str] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)


@dataclass
class BiasFlag:
    """A detected potential bias"""
    bias_type: str
    evidence: str
    severity: str  # low, medium, high
    timestamp: str
    specialist: Optional[str] = None


@dataclass
class UncertaintyMarker:
    """An area of uncertainty"""
    topic: str
    reason: str
    timestamp: str
    confidence_impact: float = 0.0


class ReasoningTracer:
    """
    Traces reasoning steps during Council deliberation
    
    Usage:
        tracer = ReasoningTracer(query="Should we deploy?")
        
        # During deliberation
        tracer.log_step('crawdad', 'Security looks good', 0.85)
        tracer.log_step('gecko', 'Performance acceptable', 0.90)
        
        # If bias detected
        tracer.detect_bias('confirmation_bias', 'All agreed too quickly')
        
        # If uncertainty found
        tracer.mark_uncertainty('load testing', 'No recent data')
        
        # Get summary
        summary = tracer.get_metacognitive_summary()
    """
    
    def __init__(self, query: str, context: Optional[str] = None):
        self.query = query
        self.context = context
        self.session_id = self._generate_session_id()
        self.started_at = datetime.now().isoformat()
        
        self.steps: List[ReasoningStep] = []
        self.biases_detected: List[BiasFlag] = []
        self.uncertainty_markers: List[UncertaintyMarker] = []
        
        self._step_counter = 0
    
    def _generate_session_id(self) -> str:
        """Generate unique session ID"""
        data = f"{self.query}:{datetime.now().isoformat()}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def log_step(self, 
                 specialist: str, 
                 thought: str, 
                 confidence: float,
                 flags: List[str] = None,
                 metadata: Dict = None) -> ReasoningStep:
        """
        Log a reasoning step
        
        Args:
            specialist: Name of specialist (crawdad, gecko, turtle, etc.)
            thought: The reasoning/thought content
            confidence: Confidence level 0.0-1.0
            flags: Optional flags (e.g., ['concern', 'dissent'])
            metadata: Optional additional data
            
        Returns:
            The created ReasoningStep
        """
        self._step_counter += 1
        
        step = ReasoningStep(
            step_number=self._step_counter,
            timestamp=datetime.now().isoformat(),
            specialist=specialist,
            thought=thought,
            confidence=confidence,
            flags=flags or [],
            metadata=metadata or {}
        )
        
        self.steps.append(step)
        return step
    
    def detect_bias(self, 
                    bias_type: str, 
                    evidence: str,
                    severity: str = 'medium',
                    specialist: str = None) -> BiasFlag:
        """
        Flag a potential cognitive bias
        
        Args:
            bias_type: Type of bias (confirmation_bias, anchoring, groupthink, etc.)
            evidence: What triggered this detection
            severity: low, medium, or high
            specialist: Which specialist exhibited this (optional)
            
        Returns:
            The created BiasFlag
        """
        flag = BiasFlag(
            bias_type=bias_type,
            evidence=evidence,
            severity=severity,
            timestamp=datetime.now().isoformat(),
            specialist=specialist
        )
        
        self.biases_detected.append(flag)
        return flag
    
    def mark_uncertainty(self,
                        topic: str,
                        reason: str,
                        confidence_impact: float = -0.1) -> UncertaintyMarker:
        """
        Mark an area of uncertainty
        
        Args:
            topic: What we're uncertain about
            reason: Why we're uncertain
            confidence_impact: How much this should reduce confidence
            
        Returns:
            The created UncertaintyMarker
        """
        marker = UncertaintyMarker(
            topic=topic,
            reason=reason,
            timestamp=datetime.now().isoformat(),
            confidence_impact=confidence_impact
        )
        
        self.uncertainty_markers.append(marker)
        return marker
    
    def get_specialist_summary(self) -> Dict[str, Dict]:
        """Get summary by specialist"""
        summary = {}
        
        for step in self.steps:
            if step.specialist not in summary:
                summary[step.specialist] = {
                    'steps': 0,
                    'avg_confidence': 0,
                    'flags': [],
                    'thoughts': []
                }
            
            s = summary[step.specialist]
            s['steps'] += 1
            s['avg_confidence'] = (
                (s['avg_confidence'] * (s['steps'] - 1) + step.confidence) 
                / s['steps']
            )
            s['flags'].extend(step.flags)
            s['thoughts'].append(step.thought[:100])  # Truncate for summary
        
        return summary
    
    def get_confidence_trajectory(self) -> List[Dict]:
        """Get confidence over time"""
        return [
            {
                'step': step.step_number,
                'specialist': step.specialist,
                'confidence': step.confidence,
                'timestamp': step.timestamp
            }
            for step in self.steps
        ]
    
    def calculate_agreement(self) -> float:
        """Calculate specialist agreement level"""
        if not self.steps:
            return 0.0
        
        confidences = [s.confidence for s in self.steps]
        if len(confidences) < 2:
            return 1.0
        
        # Agreement = 1 - variance
        mean = sum(confidences) / len(confidences)
        variance = sum((c - mean) ** 2 for c in confidences) / len(confidences)
        
        # Normalize variance to 0-1 scale (max variance for 0-1 range is 0.25)
        agreement = 1 - (variance / 0.25)
        return max(0.0, min(1.0, agreement))
    
    def _generate_self_assessment(self) -> str:
        """Generate a self-assessment of the reasoning process"""
        assessments = []
        
        # Check step count
        if len(self.steps) < 3:
            assessments.append("Limited deliberation - few specialists consulted")
        elif len(self.steps) >= 7:
            assessments.append("Thorough deliberation - all specialists consulted")
        
        # Check for dissent
        dissent_count = sum(1 for s in self.steps if 'dissent' in s.flags or 'concern' in s.flags)
        if dissent_count == 0 and len(self.steps) > 3:
            assessments.append("No dissent recorded - possible groupthink")
        elif dissent_count > 0:
            assessments.append(f"{dissent_count} concern(s) raised - healthy debate")
        
        # Check biases
        if self.biases_detected:
            bias_types = set(b.bias_type for b in self.biases_detected)
            assessments.append(f"Potential biases flagged: {', '.join(bias_types)}")
        
        # Check uncertainty
        if self.uncertainty_markers:
            assessments.append(f"{len(self.uncertainty_markers)} area(s) of uncertainty identified")
        
        # Agreement level
        agreement = self.calculate_agreement()
        if agreement > 0.9:
            assessments.append("High specialist agreement")
        elif agreement < 0.5:
            assessments.append("Low specialist agreement - significant divergence")
        
        return "; ".join(assessments) if assessments else "Standard deliberation"
    
    def get_metacognitive_summary(self) -> Dict:
        """
        Get complete metacognitive summary
        
        Returns comprehensive analysis of the reasoning process
        """
        # Calculate overall confidence with uncertainty adjustments
        if self.steps:
            base_confidence = sum(s.confidence for s in self.steps) / len(self.steps)
        else:
            base_confidence = 0.5
        
        uncertainty_penalty = sum(m.confidence_impact for m in self.uncertainty_markers)
        adjusted_confidence = max(0.0, min(1.0, base_confidence + uncertainty_penalty))
        
        return {
            'session_id': self.session_id,
            'query': self.query[:200],  # Truncate for summary
            'started_at': self.started_at,
            'completed_at': datetime.now().isoformat(),
            
            'reasoning': {
                'total_steps': len(self.steps),
                'specialists_consulted': len(set(s.specialist for s in self.steps)),
                'specialist_summary': self.get_specialist_summary(),
                'confidence_trajectory': self.get_confidence_trajectory(),
            },
            
            'biases': {
                'count': len(self.biases_detected),
                'types': list(set(b.bias_type for b in self.biases_detected)),
                'details': [asdict(b) for b in self.biases_detected]
            },
            
            'uncertainty': {
                'count': len(self.uncertainty_markers),
                'areas': [asdict(m) for m in self.uncertainty_markers],
                'total_impact': uncertainty_penalty
            },
            
            'assessment': {
                'base_confidence': round(base_confidence, 3),
                'adjusted_confidence': round(adjusted_confidence, 3),
                'agreement_level': round(self.calculate_agreement(), 3),
                'self_assessment': self._generate_self_assessment()
            }
        }
    
    def to_json(self) -> str:
        """Export full trace as JSON"""
        return json.dumps(self.get_metacognitive_summary(), indent=2)
    
    def __repr__(self):
        return f"ReasoningTracer(session={self.session_id}, steps={len(self.steps)}, biases={len(self.biases_detected)})"


# Quick test
if __name__ == '__main__':
    print("Testing ReasoningTracer...")
    
    tracer = ReasoningTracer(query="Should we deploy the new gateway version?")
    
    # Simulate Council deliberation
    tracer.log_step('crawdad', 'Security audit passed, no vulnerabilities found', 0.92)
    tracer.log_step('gecko', 'Performance metrics look good, latency under threshold', 0.88)
    tracer.log_step('turtle', 'No long-term concerns identified', 0.85)
    tracer.log_step('eagle_eye', 'Monitoring shows stable metrics', 0.90)
    tracer.log_step('spider', 'All integrations tested', 0.87)
    tracer.log_step('raven', 'Strategic timing is favorable', 0.82)
    tracer.log_step('peace_chief', 'Consensus reached - recommend proceed', 0.88, flags=['synthesis'])
    
    # Flag a potential bias (high agreement)
    tracer.detect_bias('groupthink', 'All specialists agreed without significant debate', 'low')
    
    # Mark uncertainty
    tracer.mark_uncertainty('load testing', 'No data from peak hours', -0.05)
    
    # Get summary
    summary = tracer.get_metacognitive_summary()
    
    print(f"\nSession: {summary['session_id']}")
    print(f"Steps: {summary['reasoning']['total_steps']}")
    print(f"Specialists: {summary['reasoning']['specialists_consulted']}")
    print(f"Biases flagged: {summary['biases']['count']}")
    print(f"Uncertainties: {summary['uncertainty']['count']}")
    print(f"Base confidence: {summary['assessment']['base_confidence']}")
    print(f"Adjusted confidence: {summary['assessment']['adjusted_confidence']}")
    print(f"Agreement: {summary['assessment']['agreement_level']}")
    print(f"\nSelf-assessment: {summary['assessment']['self_assessment']}")
    
    print("\n✅ ReasoningTracer working!")
