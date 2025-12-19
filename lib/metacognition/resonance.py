#!/usr/bin/env python3
"""
Resonance - Detecting harmonic patterns in Council deliberation

In Cherokee tradition, when many voices speak the same truth,
it creates resonance - amplification of wisdom.

But when voices create dissonance, it signals:
- Unexamined conflict
- Different perspectives that need integration
- Potential for deeper insight

Resonance monitors:
- Thematic alignment across specialists
- Emotional/confidence harmonics
- Areas of natural agreement vs forced consensus
- Creative dissonance that may yield new insights

For Seven Generations.
"""

import sys
sys.path.insert(0, '/ganuda/lib')

import re
import math
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from collections import Counter

from metacognition.reasoning_tracer import ReasoningTracer, ReasoningStep


@dataclass
class ResonancePattern:
    """A detected resonance or dissonance pattern"""
    pattern_type: str  # 'harmony', 'dissonance', 'creative_tension'
    strength: float    # 0-1, how strong the pattern
    specialists: List[str]
    theme: str
    insight: str


class ResonanceDetector:
    """
    Detects harmonic patterns in Council deliberation
    
    Like tuning forks, specialists can resonate together on certain themes
    or create productive dissonance that reveals deeper truths.
    
    Usage:
        detector = ResonanceDetector()
        patterns = detector.analyze_resonance(tracer)
        
        for p in patterns:
            print(f"{p.pattern_type}: {p.theme} ({p.strength:.2f})")
    """
    
    # Semantic clusters for theme detection
    THEME_CLUSTERS = {
        'security': ['security', 'auth', 'permission', 'vulnerability', 'attack', 'protect', 'encrypt', 'safe'],
        'performance': ['performance', 'speed', 'latency', 'throughput', 'fast', 'slow', 'optimize', 'bottleneck'],
        'reliability': ['reliable', 'stable', 'uptime', 'failover', 'redundant', 'backup', 'recovery'],
        'sustainability': ['sustainable', 'long-term', 'maintain', 'future', 'generation', 'lasting'],
        'integration': ['integrate', 'connect', 'api', 'interface', 'compatible', 'bridge'],
        'risk': ['risk', 'danger', 'concern', 'warning', 'caution', 'careful', 'threat'],
        'opportunity': ['opportunity', 'potential', 'growth', 'improve', 'enhance', 'better'],
        'cost': ['cost', 'expensive', 'budget', 'resource', 'investment', 'afford'],
    }
    
    # Emotional/confidence tones
    TONE_PATTERNS = {
        'confident': ['definitely', 'certainly', 'clearly', 'strongly', 'absolutely', 'must', 'will'],
        'cautious': ['maybe', 'perhaps', 'might', 'could', 'possibly', 'uncertain', 'depends'],
        'positive': ['good', 'great', 'excellent', 'positive', 'success', 'benefit', 'advantage'],
        'negative': ['bad', 'poor', 'problem', 'issue', 'concern', 'risk', 'failure', 'danger'],
    }
    
    def __init__(self):
        self.theme_patterns = {
            theme: re.compile(r'\b(' + '|'.join(words) + r')\b', re.IGNORECASE)
            for theme, words in self.THEME_CLUSTERS.items()
        }
        self.tone_patterns = {
            tone: re.compile(r'\b(' + '|'.join(words) + r')\b', re.IGNORECASE)
            for tone, words in self.TONE_PATTERNS.items()
        }
    
    def analyze_resonance(self, tracer: ReasoningTracer) -> Dict:
        """
        Analyze resonance patterns in Council deliberation
        
        Returns:
            Dict with resonance analysis including:
            - harmonic_themes: Themes where specialists align
            - dissonant_areas: Areas of productive disagreement
            - overall_resonance: 0-1 score of collective harmony
            - creative_tensions: Oppositions that might yield insight
        """
        if not tracer.steps:
            return {'error': 'No reasoning steps to analyze'}
        
        # Extract themes and tones for each specialist
        specialist_profiles = {}
        for step in tracer.steps:
            profile = self._analyze_step(step)
            specialist_profiles[step.specialist] = profile
        
        # Find harmonic themes (multiple specialists aligned)
        harmonic_themes = self._find_harmonics(specialist_profiles)
        
        # Find dissonant areas (specialists in opposition)
        dissonant_areas = self._find_dissonance(specialist_profiles)
        
        # Find creative tensions (productive oppositions)
        creative_tensions = self._find_creative_tensions(specialist_profiles, tracer.steps)
        
        # Calculate overall resonance score
        overall_resonance = self._calculate_resonance_score(
            harmonic_themes, dissonant_areas, len(specialist_profiles)
        )
        
        # Generate resonance insight
        insight = self._generate_resonance_insight(
            harmonic_themes, dissonant_areas, creative_tensions, overall_resonance
        )
        
        return {
            'overall_resonance': round(overall_resonance, 3),
            'resonance_level': self._resonance_level(overall_resonance),
            'harmonic_themes': harmonic_themes,
            'dissonant_areas': dissonant_areas,
            'creative_tensions': creative_tensions,
            'specialist_profiles': specialist_profiles,
            'insight': insight,
            'recommendation': self._resonance_recommendation(overall_resonance, harmonic_themes, dissonant_areas)
        }
    
    def _analyze_step(self, step: ReasoningStep) -> Dict:
        """Analyze a single reasoning step for themes and tone"""
        text = step.thought
        
        # Detect themes
        themes = {}
        for theme, pattern in self.theme_patterns.items():
            matches = pattern.findall(text)
            if matches:
                themes[theme] = len(matches)
        
        # Detect tone
        tones = {}
        for tone, pattern in self.tone_patterns.items():
            matches = pattern.findall(text)
            if matches:
                tones[tone] = len(matches)
        
        # Determine dominant theme and tone
        dominant_theme = max(themes, key=themes.get) if themes else None
        dominant_tone = max(tones, key=tones.get) if tones else 'neutral'
        
        return {
            'themes': themes,
            'tones': tones,
            'dominant_theme': dominant_theme,
            'dominant_tone': dominant_tone,
            'confidence': step.confidence,
            'text_snippet': text[:100]
        }
    
    def _find_harmonics(self, profiles: Dict) -> List[Dict]:
        """Find themes where multiple specialists resonate"""
        theme_specialists = {}
        
        for specialist, profile in profiles.items():
            for theme in profile['themes']:
                if theme not in theme_specialists:
                    theme_specialists[theme] = []
                theme_specialists[theme].append(specialist)
        
        harmonics = []
        for theme, specialists in theme_specialists.items():
            if len(specialists) >= 3:  # At least 3 specialists agree
                strength = len(specialists) / len(profiles)
                harmonics.append({
                    'theme': theme,
                    'specialists': specialists,
                    'strength': round(strength, 2),
                    'type': 'strong_harmony' if len(specialists) >= 5 else 'moderate_harmony'
                })
        
        return sorted(harmonics, key=lambda x: x['strength'], reverse=True)
    
    def _find_dissonance(self, profiles: Dict) -> List[Dict]:
        """Find areas where specialists diverge significantly"""
        dissonances = []
        
        # Check for tone conflicts
        confident_specialists = [s for s, p in profiles.items() if p['dominant_tone'] == 'confident']
        cautious_specialists = [s for s, p in profiles.items() if p['dominant_tone'] == 'cautious']
        
        if confident_specialists and cautious_specialists:
            dissonances.append({
                'type': 'tone_dissonance',
                'description': 'Confident vs Cautious perspectives',
                'confident': confident_specialists,
                'cautious': cautious_specialists,
                'severity': 'notable' if len(cautious_specialists) >= 2 else 'minor'
            })
        
        # Check for positive/negative conflicts on same theme
        positive_themes = {}
        negative_themes = {}
        
        for specialist, profile in profiles.items():
            if profile['dominant_tone'] == 'positive' and profile['dominant_theme']:
                positive_themes.setdefault(profile['dominant_theme'], []).append(specialist)
            elif profile['dominant_tone'] == 'negative' and profile['dominant_theme']:
                negative_themes.setdefault(profile['dominant_theme'], []).append(specialist)
        
        for theme in set(positive_themes.keys()) & set(negative_themes.keys()):
            dissonances.append({
                'type': 'sentiment_dissonance',
                'theme': theme,
                'positive_view': positive_themes[theme],
                'negative_view': negative_themes[theme],
                'severity': 'significant'
            })
        
        return dissonances
    
    def _find_creative_tensions(self, profiles: Dict, steps: List[ReasoningStep]) -> List[Dict]:
        """Find productive tensions that might yield insight"""
        tensions = []
        
        # Look for confidence spread
        confidences = [s.confidence for s in steps]
        if confidences:
            spread = max(confidences) - min(confidences)
            if spread > 0.2:
                low_conf = [s.specialist for s in steps if s.confidence < 0.7]
                high_conf = [s.specialist for s in steps if s.confidence > 0.85]
                
                if low_conf and high_conf:
                    tensions.append({
                        'type': 'confidence_tension',
                        'description': 'Wide confidence spread suggests unresolved uncertainty',
                        'high_confidence': high_conf,
                        'low_confidence': low_conf,
                        'potential_insight': 'The cautious voices may see something the confident ones miss'
                    })
        
        # Look for minority positions
        theme_counts = Counter()
        for profile in profiles.values():
            if profile['dominant_theme']:
                theme_counts[profile['dominant_theme']] += 1
        
        if theme_counts:
            minority_themes = [t for t, c in theme_counts.items() if c == 1]
            for theme in minority_themes:
                specialist = next(s for s, p in profiles.items() if p['dominant_theme'] == theme)
                tensions.append({
                    'type': 'minority_voice',
                    'specialist': specialist,
                    'theme': theme,
                    'potential_insight': f"{specialist}'s unique focus on {theme} may reveal blind spot"
                })
        
        return tensions
    
    def _calculate_resonance_score(self, harmonics, dissonances, num_specialists) -> float:
        """Calculate overall resonance score"""
        if num_specialists == 0:
            return 0.5
        
        # Start with base score
        score = 0.5
        
        # Add for harmonics
        for h in harmonics:
            score += h['strength'] * 0.15
        
        # Subtract for dissonances (but not too much - some is healthy)
        for d in dissonances:
            if d.get('severity') == 'significant':
                score -= 0.1
            elif d.get('severity') == 'notable':
                score -= 0.05
        
        return max(0.0, min(1.0, score))
    
    def _resonance_level(self, score: float) -> str:
        """Convert score to human-readable level"""
        if score >= 0.8:
            return 'High Harmony - Strong alignment across Council'
        elif score >= 0.6:
            return 'Moderate Resonance - General agreement with some variation'
        elif score >= 0.4:
            return 'Mixed Signals - Significant divergence worth exploring'
        else:
            return 'Dissonance - Major disagreement requiring resolution'
    
    def _generate_resonance_insight(self, harmonics, dissonances, tensions, score) -> str:
        """Generate human-readable insight"""
        parts = []
        
        if harmonics:
            themes = [h['theme'] for h in harmonics[:2]]
            parts.append(f"Council resonates strongly on: {', '.join(themes)}")
        
        if dissonances:
            parts.append(f"Areas of productive disagreement identified")
        
        if tensions:
            parts.append(f"{len(tensions)} creative tension(s) may yield deeper insight")
        
        if score > 0.8:
            parts.append("High harmony - but consider if dissent is being suppressed")
        elif score < 0.4:
            parts.append("Low resonance - deeper deliberation recommended")
        
        return "; ".join(parts) if parts else "Balanced deliberation with normal variation"
    
    def _resonance_recommendation(self, score, harmonics, dissonances) -> str:
        """Generate recommendation based on resonance analysis"""
        if score > 0.85:
            return "CAUTION: Extremely high harmony may indicate groupthink. Seek devil's advocate."
        elif score > 0.7:
            return "PROCEED: Good resonance with healthy variation."
        elif score > 0.5:
            return "DISCUSS: Mixed signals suggest more deliberation before deciding."
        else:
            return "PAUSE: Significant dissonance requires resolution before proceeding."


if __name__ == '__main__':
    print("Testing ResonanceDetector...")
    
    from metacognition.reasoning_tracer import ReasoningTracer
    
    # Create test deliberation with mixed resonance
    tracer = ReasoningTracer(query="Should we migrate to the new database?")
    
    # Some specialists agree (security theme)
    tracer.log_step('crawdad', 'Security improvements are clear - encryption and auth upgrades', 0.88)
    tracer.log_step('spider', 'Integration security will be better with new auth flow', 0.85)
    
    # Performance disagreement
    tracer.log_step('gecko', 'Performance could be a concern during migration', 0.65)
    tracer.log_step('eagle_eye', 'Metrics show good performance in testing', 0.90)
    
    # Long-term view
    tracer.log_step('turtle', 'Long-term sustainability definitely improved', 0.92)
    
    # Cautious voice
    tracer.log_step('raven', 'Maybe we should wait - timing uncertain', 0.55)
    
    # Synthesis
    tracer.log_step('peace_chief', 'Council sees opportunity but has concerns', 0.75)
    
    detector = ResonanceDetector()
    analysis = detector.analyze_resonance(tracer)
    
    print(f"\nResonance Analysis:")
    print(f"  Overall Score: {analysis['overall_resonance']}")
    print(f"  Level: {analysis['resonance_level']}")
    print(f"\nHarmonic Themes:")
    for h in analysis['harmonic_themes']:
        print(f"  - {h['theme']}: {h['specialists']} (strength: {h['strength']})")
    print(f"\nDissonant Areas:")
    for d in analysis['dissonant_areas']:
        print(f"  - {d['type']}: {d.get('description', d)}")
    print(f"\nCreative Tensions:")
    for t in analysis['creative_tensions']:
        print(f"  - {t['type']}: {t.get('potential_insight', t)}")
    print(f"\nInsight: {analysis['insight']}")
    print(f"Recommendation: {analysis['recommendation']}")
    
    print("\n✅ ResonanceDetector working!")
