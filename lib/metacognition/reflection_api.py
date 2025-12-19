#!/usr/bin/env python3
"""
Reflection API - Endpoints for metacognitive reflection

Provides:
- /v1/metacognition/reflect - Generate insights from past decisions
- /v1/metacognition/calibrate - Check confidence calibration
- /v1/metacognition/coyote - Get Coyote's current observations

For Seven Generations.
"""

import sys
sys.path.insert(0, '/ganuda/lib')

import json
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import Counter


class ReflectionEngine:
    """
    Generates metacognitive reflections from past decisions
    """
    
    def __init__(self, db_config: Dict):
        self.db_config = db_config
    
    def reflect(self, topic: str = None, days: int = 30) -> Dict:
        """
        Generate reflection on past decisions
        
        Args:
            topic: Optional topic filter
            days: Number of days to look back
            
        Returns:
            Reflection report with insights
        """
        conn = psycopg2.connect(**self.db_config)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get decisions
        if topic:
            cur.execute("""
                SELECT * FROM decision_reflections
                WHERE created_at > NOW() - INTERVAL '%s days'
                AND query ILIKE %s
                ORDER BY created_at DESC
            """, (days, f'%{topic}%'))
        else:
            cur.execute("""
                SELECT * FROM decision_reflections
                WHERE created_at > NOW() - INTERVAL '%s days'
                ORDER BY created_at DESC
            """, (days,))
        
        decisions = cur.fetchall()
        
        # Get outcomes if any
        cur.execute("""
            SELECT * FROM decision_reflections
            WHERE outcome IS NOT NULL
            AND created_at > NOW() - INTERVAL '%s days'
        """, (days,))
        outcomes = cur.fetchall()
        
        # Get Coyote's wisdom
        cur.execute("""
            SELECT coyote_says, wisdom_quote, uncomfortable_question
            FROM coyote_wisdom_archive
            WHERE created_at > NOW() - INTERVAL '%s days'
            ORDER BY created_at DESC LIMIT 10
        """, (days,))
        coyote_archive = cur.fetchall()
        
        cur.close()
        conn.close()
        
        return self._generate_reflection_report(decisions, outcomes, coyote_archive, days, topic)
    
    def _generate_reflection_report(self, decisions, outcomes, coyote_archive, days, topic) -> Dict:
        """Generate the reflection report"""
        
        if not decisions:
            return {
                'period_days': days,
                'topic': topic,
                'total_decisions': 0,
                'message': 'No decisions found for this period',
                'timestamp': datetime.now().isoformat()
            }
        
        # Analyze patterns
        bias_counts = Counter()
        scores = []
        confidence_errors = []
        
        for d in decisions:
            # Count biases
            biases = d.get('biases_detected') or {}
            if isinstance(biases, str):
                biases = json.loads(biases)
            for bias in biases.get('types', []):
                bias_counts[bias] += 1
            
            # Collect scores
            if d.get('metacognitive_score'):
                scores.append(d['metacognitive_score'])
            
            # Confidence calibration
            if d.get('confidence') and d.get('calibrated_confidence'):
                confidence_errors.append(
                    abs(d['confidence'] - d['calibrated_confidence'])
                )
        
        # Calculate success rate from outcomes
        if outcomes:
            successes = sum(1 for o in outcomes if o.get('outcome_success'))
            success_rate = successes / len(outcomes)
        else:
            success_rate = None
        
        # Generate insights
        insights = self._generate_insights(bias_counts, scores, confidence_errors, success_rate)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(bias_counts, scores, success_rate)
        
        return {
            'period_days': days,
            'topic': topic,
            'total_decisions': len(decisions),
            'timestamp': datetime.now().isoformat(),
            
            'metrics': {
                'avg_metacognitive_score': round(sum(scores)/len(scores), 1) if scores else None,
                'min_score': min(scores) if scores else None,
                'max_score': max(scores) if scores else None,
                'success_rate': round(success_rate, 3) if success_rate else 'No outcomes recorded'
            },
            
            'bias_analysis': {
                'total_biases_detected': sum(bias_counts.values()),
                'most_common': bias_counts.most_common(3),
                'all_types': dict(bias_counts)
            },
            
            'confidence_calibration': {
                'avg_error': round(sum(confidence_errors)/len(confidence_errors), 3) if confidence_errors else None,
                'assessment': self._assess_calibration(confidence_errors)
            },
            
            'insights': insights,
            'recommendations': recommendations,
            
            'coyote_archive': [
                {
                    'says': c['coyote_says'][:200] if c.get('coyote_says') else None,
                    'wisdom': c['wisdom_quote'],
                    'question': c['uncomfortable_question']
                }
                for c in (coyote_archive or [])[:5]
            ]
        }
    
    def _generate_insights(self, bias_counts, scores, confidence_errors, success_rate) -> List[str]:
        """Generate human-readable insights"""
        insights = []
        
        if bias_counts:
            most_common = bias_counts.most_common(1)[0]
            insights.append(f"Most frequent bias: {most_common[0]} ({most_common[1]} occurrences)")
        
        if scores:
            avg_score = sum(scores) / len(scores)
            if avg_score < 60:
                insights.append("Low average metacognitive score indicates reasoning quality concerns")
            elif avg_score > 80:
                insights.append("High metacognitive scores suggest sound reasoning patterns")
        
        if confidence_errors:
            avg_error = sum(confidence_errors) / len(confidence_errors)
            if avg_error > 0.15:
                insights.append("Confidence calibration shows significant drift - predictions often off")
            elif avg_error < 0.05:
                insights.append("Confidence is well-calibrated - predictions match outcomes")
        
        if success_rate is not None:
            if success_rate > 0.85:
                insights.append("High success rate on recorded outcomes")
            elif success_rate < 0.6:
                insights.append("Lower success rate suggests reviewing decision patterns")
        
        if not insights:
            insights.append("Insufficient data for detailed insights")
        
        return insights
    
    def _generate_recommendations(self, bias_counts, scores, success_rate) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        if 'groupthink' in bias_counts and bias_counts['groupthink'] > 2:
            recommendations.append("Actively seek dissenting opinions in Council deliberations")
        
        if 'confirmation_bias' in bias_counts and bias_counts['confirmation_bias'] > 2:
            recommendations.append("Challenge initial assumptions more rigorously")
        
        if 'sunk_cost' in bias_counts:
            recommendations.append("Evaluate decisions based on future value, not past investment")
        
        if scores and sum(scores)/len(scores) < 70:
            recommendations.append("Increase deliberation time for complex decisions")
        
        if not recommendations:
            recommendations.append("Continue current practices - reasoning appears healthy")
        
        return recommendations
    
    def _assess_calibration(self, errors) -> str:
        """Assess confidence calibration quality"""
        if not errors:
            return "Insufficient data"
        
        avg = sum(errors) / len(errors)
        if avg < 0.05:
            return "Excellent - predictions match reality closely"
        elif avg < 0.1:
            return "Good - minor calibration adjustments needed"
        elif avg < 0.15:
            return "Fair - consider recalibrating confidence estimates"
        else:
            return "Poor - confidence estimates significantly off"
    
    def get_calibration_stats(self, topic: str = None) -> Dict:
        """Get detailed calibration statistics"""
        conn = psycopg2.connect(**self.db_config)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        if topic:
            cur.execute("""
                SELECT topic, 
                       AVG(predicted_confidence) as avg_predicted,
                       AVG(actual_accuracy) as avg_actual,
                       AVG(calibration_error) as avg_error,
                       COUNT(*) as sample_size
                FROM calibration_history
                WHERE topic = %s
                GROUP BY topic
            """, (topic,))
        else:
            cur.execute("""
                SELECT topic,
                       AVG(predicted_confidence) as avg_predicted,
                       AVG(actual_accuracy) as avg_actual,
                       AVG(calibration_error) as avg_error,
                       COUNT(*) as sample_size
                FROM calibration_history
                GROUP BY topic
            """)
        
        results = cur.fetchall()
        cur.close()
        conn.close()
        
        return {
            'topic': topic,
            'by_topic': [dict(r) for r in results],
            'timestamp': datetime.now().isoformat()
        }


if __name__ == '__main__':
    print("Testing ReflectionEngine...")
    
    db_config = {
        'host': '192.168.132.222',
        'port': 5432,
        'database': 'zammad_production',
        'user': 'claude',
        'password': 'jawaseatlasers2'
    }
    
    engine = ReflectionEngine(db_config)
    
    # Generate reflection
    reflection = engine.reflect(days=30)
    
    print(f"\nReflection Report:")
    print(f"  Period: {reflection['period_days']} days")
    print(f"  Decisions: {reflection['total_decisions']}")
    print(f"  Avg Score: {reflection['metrics']['avg_metacognitive_score']}")
    print(f"  Biases: {reflection['bias_analysis']['total_biases_detected']}")
    print(f"\nInsights:")
    for insight in reflection['insights']:
        print(f"  - {insight}")
    print(f"\nRecommendations:")
    for rec in reflection['recommendations']:
        print(f"  - {rec}")
    
    print("\n✅ ReflectionEngine working!")
