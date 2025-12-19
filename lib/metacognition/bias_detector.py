#!/usr/bin/env python3
"""
Bias Detector - Identifies cognitive biases in Council reasoning

Detects patterns that may indicate:
- Confirmation bias
- Anchoring bias
- Availability heuristic
- Groupthink
- Sunk cost fallacy
- Recency bias

For Seven Generations.
"""

import re
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class DetectedBias:
    """A detected bias instance"""
    bias_type: str
    description: str
    trigger: str
    context: str
    severity: str  # low, medium, high
    confidence: float  # How confident we are this is actually a bias


class BiasDetector:
    """
    Detects cognitive biases in reasoning
    
    Usage:
        detector = BiasDetector()
        biases = detector.analyze_response(response_text, specialist_votes)
        
        for bias in biases:
            print(f"{bias.bias_type}: {bias.description}")
    """
    
    # Bias patterns with signals and descriptions
    BIAS_PATTERNS = {
        'confirmation_bias': {
            'signals': [
                r'confirms? (what|our|the) (we )?(expected|believed|thought)',
                r'as (we )?(predicted|expected|anticipated)',
                r'this (supports|validates|confirms)',
                r'consistent with (our|the) (view|belief|expectation)',
                r'proves? (we|I) (was|were) right'
            ],
            'description': 'Favoring information that confirms existing beliefs',
            'base_severity': 'medium'
        },
        'anchoring_bias': {
            'signals': [
                r'starting (from|with|at)',
                r'based on (the )?(initial|first|original)',
                r'adjusting (from|based on)',
                r'relative to (the )?(original|initial|starting)',
                r'compared to (the )?(baseline|original)'
            ],
            'description': 'Over-relying on first piece of information',
            'base_severity': 'medium'
        },
        'availability_heuristic': {
            'signals': [
                r'recently (saw|encountered|experienced|happened)',
                r'(common|typical|usual) (example|case|scenario)',
                r'remember(s)? (when|the time)',
                r'(just|recently) (last|this) (week|month|time)',
                r'comes? to mind'
            ],
            'description': 'Overweighting easily recalled information',
            'base_severity': 'low'
        },
        'groupthink': {
            'signals': [
                r'(all|every|each) specialists? agree',
                r'unanimous(ly)?',
                r'no (concerns?|objections?|dissent)',
                r'everyone (agrees?|thinks?|believes?)',
                r'consensus (was )?(reached|achieved|clear)'
            ],
            'description': 'Excessive consensus without critical evaluation',
            'base_severity': 'medium'
        },
        'sunk_cost': {
            'signals': [
                r'already (invested|spent|committed)',
                r'come? this far',
                r"can't abandon (now|this)",
                r'too (late|far|much invested) to',
                r'waste (the|all) (effort|time|resources)'
            ],
            'description': 'Continuing due to past investment rather than future value',
            'base_severity': 'high'
        },
        'recency_bias': {
            'signals': [
                r'(just|recently) happened',
                r'(most )?recent (event|data|example)',
                r'latest (information|data|news)',
                r'(this|last) (morning|week|month)',
                r'fresh (in|on) (our )?(mind|memory)'
            ],
            'description': 'Overweighting recent events over historical patterns',
            'base_severity': 'low'
        },
        'authority_bias': {
            'signals': [
                r'(the )?expert(s)? (said|say|believe)',
                r'according to (the )?(authority|expert|leader)',
                r'(senior|experienced) (member|specialist) (said|thinks)',
                r'(we )?(should|must) (trust|defer to)',
                r'(they|he|she) (know|knows) (best|better)'
            ],
            'description': 'Overvaluing opinions based on authority rather than merit',
            'base_severity': 'medium'
        },
        'hindsight_bias': {
            'signals': [
                r'(obviously|clearly) (going|was going) to happen',
                r'(should|could) have (seen|known|predicted)',
                r'(was|were) (inevitable|predictable|obvious)',
                r'knew (it )?(all along|from the start)',
                r'in (retrospect|hindsight)'
            ],
            'description': 'Believing past events were predictable',
            'base_severity': 'low'
        }
    }
    
    def __init__(self):
        # Compile regex patterns for efficiency
        self._compiled_patterns = {}
        for bias_type, pattern_data in self.BIAS_PATTERNS.items():
            self._compiled_patterns[bias_type] = [
                re.compile(p, re.IGNORECASE) 
                for p in pattern_data['signals']
            ]
    
    def analyze_response(self, 
                        response_text: str, 
                        specialist_votes: List[Dict] = None) -> List[DetectedBias]:
        """
        Analyze response for potential biases
        
        Args:
            response_text: The synthesized response text
            specialist_votes: List of specialist vote dicts with 'recommendation', 'confidence', etc.
            
        Returns:
            List of DetectedBias instances
        """
        detected = []
        
        # Check text patterns
        for bias_type, patterns in self._compiled_patterns.items():
            pattern_data = self.BIAS_PATTERNS[bias_type]
            
            for pattern in patterns:
                matches = pattern.finditer(response_text)
                for match in matches:
                    # Extract context around the match
                    start = max(0, match.start() - 50)
                    end = min(len(response_text), match.end() + 50)
                    context = response_text[start:end]
                    
                    detected.append(DetectedBias(
                        bias_type=bias_type,
                        description=pattern_data['description'],
                        trigger=match.group(),
                        context=f"...{context}...",
                        severity=pattern_data['base_severity'],
                        confidence=0.7  # Pattern match confidence
                    ))
        
        # Check for groupthink via vote analysis
        if specialist_votes:
            groupthink = self._check_groupthink(specialist_votes)
            if groupthink:
                detected.append(groupthink)
        
        # Deduplicate (same bias type, similar context)
        detected = self._deduplicate(detected)
        
        return detected
    
    def _check_groupthink(self, votes: List[Dict]) -> Optional[DetectedBias]:
        """Check if all specialists gave same recommendation without dissent"""
        if not votes or len(votes) < 3:
            return None
        
        # Extract recommendations
        recommendations = []
        confidences = []
        concerns = []
        
        for vote in votes:
            if 'recommendation' in vote:
                recommendations.append(vote['recommendation'])
            if 'confidence' in vote:
                confidences.append(vote['confidence'])
            if 'concerns' in vote:
                concerns.extend(vote['concerns'])
        
        # Check for unanimous agreement
        unique_recommendations = set(recommendations)
        
        if len(unique_recommendations) == 1 and len(recommendations) >= 5:
            # All agree - check if there were concerns
            if not concerns:
                return DetectedBias(
                    bias_type='groupthink',
                    description='All specialists unanimous with no concerns raised',
                    trigger='unanimous_vote_no_concerns',
                    context=f"{len(recommendations)} specialists all recommended: {list(unique_recommendations)[0]}",
                    severity='medium',
                    confidence=0.8
                )
            elif len(concerns) < 2:
                return DetectedBias(
                    bias_type='groupthink',
                    description='Near-unanimous agreement with minimal dissent',
                    trigger='near_unanimous_vote',
                    context=f"{len(recommendations)} specialists agreed, only {len(concerns)} concern(s)",
                    severity='low',
                    confidence=0.6
                )
        
        # Check for suspiciously high confidence across all
        if confidences and len(confidences) >= 5:
            avg_confidence = sum(confidences) / len(confidences)
            if avg_confidence > 0.9:
                return DetectedBias(
                    bias_type='groupthink',
                    description='Unusually high confidence across all specialists',
                    trigger='high_unanimous_confidence',
                    context=f"Average confidence {avg_confidence:.2f} across {len(confidences)} specialists",
                    severity='low',
                    confidence=0.5
                )
        
        return None
    
    def _deduplicate(self, biases: List[DetectedBias]) -> List[DetectedBias]:
        """Remove duplicate bias detections"""
        seen = set()
        unique = []
        
        for bias in biases:
            key = (bias.bias_type, bias.trigger[:20])  # Dedupe by type and trigger start
            if key not in seen:
                seen.add(key)
                unique.append(bias)
        
        return unique
    
    def get_bias_summary(self, biases: List[DetectedBias]) -> Dict:
        """Generate summary of detected biases"""
        if not biases:
            return {
                'total_detected': 0,
                'types': [],
                'severity_breakdown': {},
                'recommendation': 'No biases detected - reasoning appears balanced'
            }
        
        # Count by type and severity
        type_counts = {}
        severity_counts = {'low': 0, 'medium': 0, 'high': 0}
        
        for bias in biases:
            type_counts[bias.bias_type] = type_counts.get(bias.bias_type, 0) + 1
            severity_counts[bias.severity] += 1
        
        # Generate recommendation
        if severity_counts['high'] > 0:
            recommendation = 'High-severity bias detected - recommend careful review'
        elif severity_counts['medium'] > 2:
            recommendation = 'Multiple medium-severity biases - consider alternative viewpoints'
        elif len(biases) > 3:
            recommendation = 'Several potential biases flagged - verify reasoning'
        else:
            recommendation = 'Minor bias signals - likely acceptable'
        
        return {
            'total_detected': len(biases),
            'types': list(type_counts.keys()),
            'type_counts': type_counts,
            'severity_breakdown': severity_counts,
            'most_common': max(type_counts, key=type_counts.get) if type_counts else None,
            'recommendation': recommendation
        }


# Quick test
if __name__ == '__main__':
    print("Testing BiasDetector...")
    
    detector = BiasDetector()
    
    # Test response with embedded biases
    test_response = """
    Based on the initial assessment from last week, this confirms what we expected.
    All specialists agree that we should proceed. The recent incident just happened
    yesterday, which is fresh on our minds. We've already invested significant effort
    into this project, so we can't abandon it now. The expert said this is the right
    approach, and obviously this was going to happen eventually.
    """
    
    # Simulate specialist votes (unanimous)
    test_votes = [
        {'specialist': 'crawdad', 'recommendation': 'PROCEED', 'confidence': 0.92, 'concerns': []},
        {'specialist': 'gecko', 'recommendation': 'PROCEED', 'confidence': 0.88, 'concerns': []},
        {'specialist': 'turtle', 'recommendation': 'PROCEED', 'confidence': 0.90, 'concerns': []},
        {'specialist': 'eagle_eye', 'recommendation': 'PROCEED', 'confidence': 0.91, 'concerns': []},
        {'specialist': 'spider', 'recommendation': 'PROCEED', 'confidence': 0.89, 'concerns': []},
        {'specialist': 'raven', 'recommendation': 'PROCEED', 'confidence': 0.87, 'concerns': []},
        {'specialist': 'peace_chief', 'recommendation': 'PROCEED', 'confidence': 0.90, 'concerns': []},
    ]
    
    biases = detector.analyze_response(test_response, test_votes)
    
    print(f"\nDetected {len(biases)} potential biases:")
    for bias in biases:
        print(f"  - {bias.bias_type} ({bias.severity}): {bias.trigger}")
    
    summary = detector.get_bias_summary(biases)
    print(f"\nSummary:")
    print(f"  Types: {summary['types']}")
    print(f"  Severity: {summary['severity_breakdown']}")
    print(f"  Recommendation: {summary['recommendation']}")
    
    print("\n✅ BiasDetector working!")
