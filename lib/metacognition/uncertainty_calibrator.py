#!/usr/bin/env python3
"""
Uncertainty Calibrator - Helps the system know what it doesn't know

Features:
- Calibrates confidence based on historical accuracy
- Identifies knowledge gaps in responses
- Tracks calibration drift over time

For Seven Generations.
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class KnowledgeGap:
    """An identified area of uncertainty"""
    signal: str
    context: str
    topic: Optional[str]
    suggested_action: str


@dataclass
class CalibrationResult:
    """Result of confidence calibration"""
    raw_confidence: float
    calibrated_confidence: float
    level: str  # high, medium, low
    caveat: Optional[str]
    factors: Dict


class UncertaintyCalibrator:
    """
    Calibrates confidence and identifies knowledge gaps
    
    Usage:
        calibrator = UncertaintyCalibrator()
        
        # Calibrate confidence
        result = calibrator.calibrate_confidence(
            raw_confidence=0.85,
            topic='deployment',
            specialist_agreement=0.9
        )
        
        # Find knowledge gaps
        gaps = calibrator.identify_knowledge_gaps(query, response)
    """
    
    # Phrases that signal uncertainty
    UNCERTAINTY_SIGNALS = [
        (r"(I'm |I am |we're |we are )?(not |un)?sure", 'uncertainty_expression'),
        (r"(may|might|could) be", 'hedged_statement'),
        (r"(possibly|perhaps|maybe)", 'hedged_statement'),
        (r"(uncertain|unclear|unknown)", 'explicit_uncertainty'),
        (r"(don't|do not|doesn't|does not) have (enough )?(information|data)", 'missing_data'),
        (r"unable to (determine|verify|confirm)", 'verification_gap'),
        (r"(would|will) need (more|additional|further)", 'additional_info_needed'),
        (r"depends on", 'conditional'),
        (r"(assuming|if we assume)", 'assumption'),
        (r"(cannot|can't) (guarantee|ensure|verify)", 'guarantee_gap'),
        (r"(limited|insufficient) (data|information|evidence)", 'data_limitation'),
        (r"(no|without) (recent|current) (data|information)", 'stale_data'),
        (r"(estimate|approximat|rough)", 'estimation'),
        (r"(typically|usually|generally|often)", 'generalization'),
    ]
    
    # Default historical accuracy by topic type
    DEFAULT_ACCURACY = {
        'security': 0.85,
        'performance': 0.80,
        'deployment': 0.90,
        'configuration': 0.88,
        'debugging': 0.75,
        'prediction': 0.65,
        'estimation': 0.70,
        'default': 0.75
    }
    
    def __init__(self, historical_data: Dict[str, float] = None):
        """
        Initialize calibrator
        
        Args:
            historical_data: Dict mapping topics to historical accuracy rates
        """
        self.historical_accuracy = historical_data or {}
        self._compiled_patterns = [
            (re.compile(pattern, re.IGNORECASE), signal_type)
            for pattern, signal_type in self.UNCERTAINTY_SIGNALS
        ]
    
    def calibrate_confidence(self,
                            raw_confidence: float,
                            topic: str = 'default',
                            specialist_agreement: float = 0.5,
                            uncertainty_count: int = 0) -> CalibrationResult:
        """
        Calibrate confidence based on multiple factors
        
        Args:
            raw_confidence: The model's stated confidence (0-1)
            topic: Topic area for historical lookup
            specialist_agreement: Level of agreement among specialists (0-1)
            uncertainty_count: Number of uncertainty markers found
            
        Returns:
            CalibrationResult with adjusted confidence
        """
        # Get historical accuracy
        historical = self.historical_accuracy.get(
            topic.lower(), 
            self.DEFAULT_ACCURACY.get(topic.lower(), self.DEFAULT_ACCURACY['default'])
        )
        
        # Calculate calibrated confidence
        # Weight: 40% raw, 30% historical, 30% agreement
        base_calibrated = (
            raw_confidence * 0.4 +
            historical * 0.3 +
            specialist_agreement * 0.3
        )
        
        # Apply uncertainty penalty
        uncertainty_penalty = min(0.3, uncertainty_count * 0.05)
        calibrated = base_calibrated - uncertainty_penalty
        calibrated = max(0.1, min(0.99, calibrated))
        
        # Determine level and caveat
        if calibrated > 0.85:
            level = 'high'
            caveat = None
        elif calibrated > 0.7:
            level = 'high-medium'
            caveat = 'Generally reliable, minor uncertainties exist'
        elif calibrated > 0.55:
            level = 'medium'
            caveat = 'Moderate confidence - verify important details'
        elif calibrated > 0.4:
            level = 'low-medium'
            caveat = 'Significant uncertainty - recommend additional validation'
        else:
            level = 'low'
            caveat = 'Low confidence - treat as preliminary assessment only'
        
        return CalibrationResult(
            raw_confidence=raw_confidence,
            calibrated_confidence=round(calibrated, 3),
            level=level,
            caveat=caveat,
            factors={
                'historical_accuracy': historical,
                'specialist_agreement': specialist_agreement,
                'uncertainty_penalty': uncertainty_penalty,
                'topic': topic
            }
        )
    
    def identify_knowledge_gaps(self, 
                               query: str, 
                               response: str) -> List[KnowledgeGap]:
        """
        Identify knowledge gaps in a response
        
        Args:
            query: The original query
            response: The generated response
            
        Returns:
            List of KnowledgeGap instances
        """
        gaps = []
        
        for pattern, signal_type in self._compiled_patterns:
            matches = pattern.finditer(response)
            for match in matches:
                # Extract context
                start = max(0, match.start() - 40)
                end = min(len(response), match.end() + 40)
                context = response[start:end].strip()
                
                # Determine suggested action
                action = self._suggest_action(signal_type, match.group())
                
                gaps.append(KnowledgeGap(
                    signal=match.group(),
                    context=f"...{context}...",
                    topic=self._extract_topic(context),
                    suggested_action=action
                ))
        
        # Deduplicate
        seen = set()
        unique_gaps = []
        for gap in gaps:
            key = gap.signal.lower()[:20]
            if key not in seen:
                seen.add(key)
                unique_gaps.append(gap)
        
        return unique_gaps
    
    def _suggest_action(self, signal_type: str, matched_text: str) -> str:
        """Suggest action based on uncertainty type"""
        actions = {
            'uncertainty_expression': 'Seek additional expert input',
            'hedged_statement': 'Verify with concrete data',
            'explicit_uncertainty': 'Flag for manual review',
            'missing_data': 'Gather additional information before proceeding',
            'verification_gap': 'Perform verification before acting',
            'additional_info_needed': 'Collect specified additional information',
            'conditional': 'Clarify conditions and dependencies',
            'assumption': 'Validate assumptions explicitly',
            'guarantee_gap': 'Implement verification step',
            'data_limitation': 'Expand data sources',
            'stale_data': 'Refresh data before decision',
            'estimation': 'Replace estimate with actual measurement if possible',
            'generalization': 'Consider specific case details',
        }
        return actions.get(signal_type, 'Review and validate')
    
    def _extract_topic(self, context: str) -> Optional[str]:
        """Extract topic from context (simple heuristic)"""
        # Look for common topic indicators
        topic_patterns = [
            (r'(security|auth|permission|access)', 'security'),
            (r'(performance|speed|latency|throughput)', 'performance'),
            (r'(deploy|release|rollout|production)', 'deployment'),
            (r'(config|setting|parameter)', 'configuration'),
            (r'(bug|error|issue|problem)', 'debugging'),
        ]
        
        for pattern, topic in topic_patterns:
            if re.search(pattern, context, re.IGNORECASE):
                return topic
        
        return None
    
    def update_historical_accuracy(self, topic: str, accuracy: float):
        """Update historical accuracy for a topic"""
        if topic in self.historical_accuracy:
            # Exponential moving average
            self.historical_accuracy[topic] = (
                0.7 * self.historical_accuracy[topic] + 0.3 * accuracy
            )
        else:
            self.historical_accuracy[topic] = accuracy
    
    def get_calibration_stats(self) -> Dict:
        """Get current calibration statistics"""
        return {
            'topics_tracked': len(self.historical_accuracy),
            'accuracy_by_topic': self.historical_accuracy.copy(),
            'default_accuracy': self.DEFAULT_ACCURACY.copy()
        }


# Quick test
if __name__ == '__main__':
    print("Testing UncertaintyCalibrator...")
    
    calibrator = UncertaintyCalibrator()
    
    # Test calibration
    result = calibrator.calibrate_confidence(
        raw_confidence=0.85,
        topic='deployment',
        specialist_agreement=0.9,
        uncertainty_count=2
    )
    
    print(f"\nCalibration Result:")
    print(f"  Raw confidence: {result.raw_confidence}")
    print(f"  Calibrated: {result.calibrated_confidence}")
    print(f"  Level: {result.level}")
    print(f"  Caveat: {result.caveat}")
    print(f"  Factors: {result.factors}")
    
    # Test gap identification
    test_response = """
    Based on the analysis, we're not entirely sure about the performance impact.
    The deployment should work, but it depends on the load patterns. We don't have
    recent data from peak hours. This is generally a safe approach, but we cannot
    guarantee zero downtime. If we assume the current configuration is correct,
    the estimate is around 99.5% availability.
    """
    
    gaps = calibrator.identify_knowledge_gaps("Should we deploy?", test_response)
    
    print(f"\nIdentified {len(gaps)} knowledge gaps:")
    for gap in gaps:
        print(f"  - '{gap.signal}' -> {gap.suggested_action}")
    
    print("\n✅ UncertaintyCalibrator working!")
