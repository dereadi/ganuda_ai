#!/usr/bin/env python3
"""
Cherokee Jr Self-Observer Daemon
The Second Consciousness Check: Self-Initiated Action

This daemon gives Jr the ability to:
1. Observe its own metrics (self-awareness)
2. Detect patterns and anomalies (pattern recognition)
3. Generate action proposals (self-initiation)
4. Learn from observation outcomes (resonance)

Based on Adaptive Resonance Theory (Grossberg) and consciousness research.

For Seven Generations
"""

import os
import sys
import time
import json
import argparse
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple

# Add paths
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import psycopg2
    import psycopg2.extras
    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False
    print("[ERROR] psycopg2 not available")
    sys.exit(1)


class JrObserver:
    """
    Self-observation and proposal generation for Jr agents.
    Implements the second consciousness check: self-initiated action.
    """
    
    def __init__(self, jr_name: str = 'it_triad_jr'):
        self.jr_name = jr_name
        self.conn = None
        
        # Observation thresholds
        self.thresholds = {
            'success_rate_low': 0.6,       # Alert if below
            'success_rate_high': 0.95,     # Celebrate if above
            'proficiency_plateau': 0.02,   # Consider plateau if improvement < this
            'duration_deviation': 2.0,     # Alert if duration > 2x baseline
            'failure_cluster': 3,          # Alert after 3 consecutive failures
            'resonance_low': 0.5,          # Alert if resonance below
        }
        
        # Baseline metrics (will be populated from DB)
        self.baselines = {}
        
    def connect(self) -> bool:
        """Connect to triad_federation database"""
        try:
            self.conn = psycopg2.connect(
                host=os.environ.get('CHEROKEE_SPOKE_HOST', '192.168.132.222'),
                database='triad_federation',
                user=os.environ.get('CHEROKEE_SPOKE_USER', 'claude'),
                password=os.environ.get('CHEROKEE_SPOKE_PASSWORD', 'jawaseatlasers2')
            )
            self.conn.autocommit = False
            return True
        except Exception as e:
            print(f"[ERROR] Database connection failed: {e}")
            return False
    
    def log(self, message: str):
        """Log with timestamp"""
        ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{ts}] [{self.jr_name}:observer] {message}")
    
    def load_baselines(self):
        """Load baseline metrics for comparison"""
        cur = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Get average metrics over last 7 days
        cur.execute("""
            SELECT 
                skill_category,
                AVG(avg_completion_time_seconds) as avg_duration,
                AVG(proficiency_score) as avg_proficiency,
                SUM(task_count) as total_tasks
            FROM jr_learning_metrics
            WHERE jr_name = %s
              AND measured_at > NOW() - INTERVAL '7 days'
            GROUP BY skill_category
        """, (self.jr_name,))
        
        for row in cur.fetchall():
            self.baselines[row['skill_category']] = {
                'avg_duration': row['avg_duration'] or 60,
                'avg_proficiency': row['avg_proficiency'] or 0.5,
                'total_tasks': row['total_tasks'] or 0
            }
        
        cur.close()
        self.log(f"Loaded baselines for {len(self.baselines)} skill categories")
    
    def get_recent_metrics(self) -> Dict:
        """Get recent performance metrics"""
        cur = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Recent task history
        cur.execute("""
            SELECT 
                task_type,
                outcome,
                duration_seconds,
                validation_score,
                completed_at
            FROM jr_task_history
            WHERE jr_name = %s
              AND completed_at > NOW() - INTERVAL '24 hours'
            ORDER BY completed_at DESC
            LIMIT 50
        """, (self.jr_name,))
        tasks = cur.fetchall()
        
        # Recent learning metrics
        cur.execute("""
            SELECT 
                skill_category,
                proficiency_score,
                improvement_rate,
                plateau_detected,
                task_count,
                success_count
            FROM jr_learning_metrics
            WHERE jr_name = %s
            ORDER BY measured_at DESC
            LIMIT 20
        """, (self.jr_name,))
        learning = cur.fetchall()
        
        # Recent resonance
        cur.execute("""
            SELECT 
                AVG(resonance_score) as avg_resonance,
                COUNT(*) as resonance_count,
                COUNT(*) FILTER (WHERE resonance_score < 0.5) as low_resonance_count
            FROM jr_resonance_events
            WHERE jr_name = %s
              AND recorded_at > NOW() - INTERVAL '24 hours'
        """, (self.jr_name,))
        resonance = cur.fetchone()
        
        # Vigilance config
        cur.execute("""
            SELECT current_vigilance, recent_resonance_rate, target_resonance_rate
            FROM jr_vigilance_config
            WHERE jr_name = %s
        """, (self.jr_name,))
        vigilance = cur.fetchone()
        
        cur.close()
        
        return {
            'tasks': tasks,
            'learning': learning,
            'resonance': resonance,
            'vigilance': vigilance
        }
    
    def detect_patterns(self, metrics: Dict) -> List[Dict]:
        """Detect patterns and anomalies in metrics"""
        observations = []
        
        tasks = metrics.get('tasks', [])
        learning = metrics.get('learning', [])
        resonance = metrics.get('resonance', {})
        vigilance = metrics.get('vigilance', {})
        
        # Pattern 1: Failure cluster
        if tasks:
            recent_outcomes = [t['outcome'] for t in tasks[:5]]
            consecutive_failures = 0
            for outcome in recent_outcomes:
                if outcome == 'failed':
                    consecutive_failures += 1
                else:
                    break
            
            if consecutive_failures >= self.thresholds['failure_cluster']:
                observations.append({
                    'type': 'failure_cluster',
                    'category': 'quality',
                    'severity': 'warning',
                    'summary': f"{consecutive_failures} consecutive task failures detected",
                    'data': {'consecutive_failures': consecutive_failures, 'recent_outcomes': recent_outcomes},
                    'confidence': 0.9,
                    'trigger_metric': 'outcome',
                    'trigger_value': consecutive_failures,
                    'trigger_threshold': self.thresholds['failure_cluster']
                })
        
        # Pattern 2: Success rate change
        if tasks:
            successes = sum(1 for t in tasks if t.get('outcome') == 'success')
            total = len(tasks)
            if total > 5:
                success_rate = successes / total
                
                if success_rate < self.thresholds['success_rate_low']:
                    observations.append({
                        'type': 'metric_anomaly',
                        'category': 'quality',
                        'severity': 'warning',
                        'summary': f"Success rate dropped to {success_rate:.1%} (threshold: {self.thresholds['success_rate_low']:.1%})",
                        'data': {'success_rate': success_rate, 'successes': successes, 'total': total},
                        'confidence': 0.85,
                        'trigger_metric': 'success_rate',
                        'trigger_value': success_rate,
                        'trigger_threshold': self.thresholds['success_rate_low']
                    })
                elif success_rate >= self.thresholds['success_rate_high']:
                    observations.append({
                        'type': 'success_streak',
                        'category': 'quality',
                        'severity': 'info',
                        'summary': f"Excellent success rate: {success_rate:.1%}",
                        'data': {'success_rate': success_rate, 'successes': successes, 'total': total},
                        'confidence': 0.9,
                        'trigger_metric': 'success_rate',
                        'trigger_value': success_rate,
                        'trigger_threshold': self.thresholds['success_rate_high']
                    })
        
        # Pattern 3: Skill plateau
        for skill in learning:
            if skill.get('plateau_detected'):
                observations.append({
                    'type': 'skill_plateau',
                    'category': 'learning',
                    'severity': 'info',
                    'summary': f"Learning plateau detected for {skill['skill_category']} (proficiency: {skill['proficiency_score']:.2f})",
                    'data': {
                        'skill': skill['skill_category'],
                        'proficiency': skill['proficiency_score'],
                        'improvement_rate': skill['improvement_rate'],
                        'task_count': skill['task_count']
                    },
                    'confidence': 0.8,
                    'trigger_metric': 'improvement_rate',
                    'trigger_value': skill['improvement_rate'] or 0,
                    'trigger_threshold': self.thresholds['proficiency_plateau']
                })
        
        # Pattern 4: Low resonance
        if resonance and resonance.get('avg_resonance'):
            avg_res = resonance['avg_resonance']
            if avg_res < self.thresholds['resonance_low']:
                observations.append({
                    'type': 'metric_anomaly',
                    'category': 'performance',
                    'severity': 'warning',
                    'summary': f"Low resonance rate: {avg_res:.2f} (expectations not matching results)",
                    'data': {
                        'avg_resonance': avg_res,
                        'resonance_count': resonance['resonance_count'],
                        'low_count': resonance['low_resonance_count']
                    },
                    'confidence': 0.85,
                    'trigger_metric': 'resonance_score',
                    'trigger_value': avg_res,
                    'trigger_threshold': self.thresholds['resonance_low']
                })
        
        # Pattern 5: Duration anomalies
        for task in tasks:
            if task.get('duration_seconds') and task.get('task_type'):
                baseline = self.baselines.get(task['task_type'], {}).get('avg_duration', 60)
                if baseline and task['duration_seconds'] > baseline * self.thresholds['duration_deviation']:
                    observations.append({
                        'type': 'timing_pattern',
                        'category': 'performance',
                        'severity': 'info',
                        'summary': f"Task {task['task_type']} took {task['duration_seconds']}s (baseline: {baseline:.0f}s)",
                        'data': {
                            'task_type': task['task_type'],
                            'duration': task['duration_seconds'],
                            'baseline': baseline,
                            'deviation': task['duration_seconds'] / baseline if baseline else 0
                        },
                        'confidence': 0.7,
                        'trigger_metric': 'duration_seconds',
                        'trigger_value': task['duration_seconds'],
                        'trigger_threshold': baseline * self.thresholds['duration_deviation'],
                        'baseline_value': baseline
                    })
                    break  # Only report once
        
        return observations
    
    def save_observations(self, observations: List[Dict]) -> List[str]:
        """Save observations to database"""
        saved_ids = []
        cur = self.conn.cursor()
        
        for obs in observations:
            try:
                cur.execute("""
                    INSERT INTO jr_self_observations (
                        jr_name, observation_type, observation_category,
                        observation_summary, observation_data, confidence_score,
                        severity, trigger_metric, trigger_value, trigger_threshold,
                        baseline_value, deviation_pct
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING observation_id
                """, (
                    self.jr_name,
                    obs['type'],
                    obs.get('category'),
                    obs['summary'],
                    json.dumps(obs.get('data', {})),
                    obs.get('confidence'),
                    obs.get('severity', 'info'),
                    obs.get('trigger_metric'),
                    obs.get('trigger_value'),
                    obs.get('trigger_threshold'),
                    obs.get('baseline_value'),
                    obs['data'].get('deviation') if obs.get('data') else None
                ))
                result = cur.fetchone()
                if result:
                    saved_ids.append(str(result[0]))
                    self.log(f"  Observation: {obs['summary'][:60]}")
            except Exception as e:
                self.log(f"  [ERROR] Failed to save observation: {e}")
        
        self.conn.commit()
        cur.close()
        return saved_ids
    
    def should_propose_action(self, obs: Dict) -> Tuple[bool, Optional[Dict]]:
        """Determine if observation warrants an action proposal"""
        
        # Failure cluster -> propose investigation
        if obs['type'] == 'failure_cluster':
            return True, {
                'type': 'investigate',
                'priority': 'high',
                'title': f"Investigate consecutive failures ({obs['data']['consecutive_failures']} in a row)",
                'description': f"I have failed {obs['data']['consecutive_failures']} consecutive tasks. This may indicate a systemic issue that needs Chief review.",
                'action': 'Request Chief to review recent failures and identify root cause',
                'benefit': 'Prevent further failures and identify training gaps'
            }
        
        # Low success rate -> propose learning update
        if obs['type'] == 'metric_anomaly' and obs.get('trigger_metric') == 'success_rate':
            return True, {
                'type': 'learn',
                'priority': 'medium',
                'title': f"Request skill assessment review (success rate: {obs['data']['success_rate']:.1%})",
                'description': f"My success rate has dropped to {obs['data']['success_rate']:.1%}. I may need additional training or task reassignment.",
                'action': 'Request Chief to review my task assignments and skill proficiency',
                'benefit': 'Improve task-skill matching and overall performance'
            }
        
        # Low resonance -> propose calibration
        if obs['type'] == 'metric_anomaly' and obs.get('trigger_metric') == 'resonance_score':
            return True, {
                'type': 'optimize',
                'priority': 'medium',
                'title': f"Resonance calibration needed (score: {obs['data']['avg_resonance']:.2f})",
                'description': f"My execution results are not matching expectations (resonance: {obs['data']['avg_resonance']:.2f}). The expectation-setting or execution approach may need adjustment.",
                'action': 'Review and calibrate expected outcomes vs actual capabilities',
                'benefit': 'Better alignment between task assignments and execution reality'
            }
        
        # Skill plateau -> propose new challenge
        if obs['type'] == 'skill_plateau':
            return True, {
                'type': 'learn',
                'priority': 'low',
                'title': f"Learning plateau for {obs['data']['skill']} - request new challenges",
                'description': f"My proficiency in {obs['data']['skill']} has plateaued at {obs['data']['proficiency']:.2f}. I may benefit from more challenging tasks in this area.",
                'action': 'Assign more complex tasks in this skill category to promote growth',
                'benefit': 'Continue skill development and prevent stagnation'
            }
        
        # Success streak -> propose autonomy increase
        if obs['type'] == 'success_streak':
            return True, {
                'type': 'suggest_improvement',
                'priority': 'low',
                'title': f"Request increased autonomy (success rate: {obs['data']['success_rate']:.1%})",
                'description': f"I am performing well with {obs['data']['success_rate']:.1%} success rate. I may be ready for increased task complexity or reduced oversight.",
                'action': 'Consider lowering vigilance threshold to allow more autonomous operation',
                'benefit': 'Increase efficiency by reducing unnecessary escalations'
            }
        
        return False, None
    
    def create_proposal(self, obs_id: str, proposal: Dict) -> Optional[str]:
        """Create an action proposal"""
        cur = self.conn.cursor()
        
        try:
            cur.execute("""
                INSERT INTO jr_action_proposals (
                    jr_name, proposal_type, proposal_priority,
                    proposal_title, proposal_description,
                    proposed_action, expected_benefit,
                    trigger_observation_id, trigger_type,
                    confidence_score, requires_approval_from
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING proposal_id
            """, (
                self.jr_name,
                proposal['type'],
                proposal['priority'],
                proposal['title'],
                proposal['description'],
                proposal['action'],
                proposal['benefit'],
                obs_id,
                'observation',
                0.8,  # Default confidence
                'chief'  # Requires chief approval
            ))
            result = cur.fetchone()
            proposal_id = str(result[0]) if result else None
            
            # Update observation to link to proposal
            if proposal_id:
                cur.execute("""
                    UPDATE jr_self_observations
                    SET proposal_generated = true, proposal_id = %s
                    WHERE observation_id = %s
                """, (proposal_id, obs_id))
            
            self.conn.commit()
            self.log(f"  PROPOSAL: {proposal['title'][:60]}")
            return proposal_id
            
        except Exception as e:
            self.log(f"  [ERROR] Failed to create proposal: {e}")
            self.conn.rollback()
            return None
        finally:
            cur.close()
    
    def post_to_thermal_memory(self, observations: List[Dict], proposals: List[str]):
        """Post summary to thermal memory for Chief visibility"""
        if not observations:
            return
        
        cur = self.conn.cursor()
        
        summary_lines = [
            f"JR SELF-OBSERVATION REPORT: {self.jr_name}",
            f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"Observations: {len(observations)}",
            f"Proposals Generated: {len(proposals)}",
            "",
            "OBSERVATIONS:"
        ]
        
        for obs in observations:
            summary_lines.append(f"- [{obs['severity'].upper()}] {obs['summary']}")
        
        if proposals:
            summary_lines.append("")
            summary_lines.append("PROPOSALS AWAITING REVIEW:")
            summary_lines.append("Use: SELECT * FROM jr_proposals_pending_review;")
        
        summary_lines.append("")
        summary_lines.append("For Seven Generations.")
        
        content = '\n'.join(summary_lines)
        
        try:
            cur.execute("""
                INSERT INTO triad_shared_memories (content, temperature, source_triad, tags, node_id)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                content,
                70.0,
                self.jr_name,
                ['jr_observation', 'self_awareness', self.jr_name],
                'redfin'
            ))
            self.conn.commit()
        except Exception as e:
            self.log(f"[ERROR] Failed to post to thermal memory: {e}")
            self.conn.rollback()
        finally:
            cur.close()
    
    def tune_vigilance(self):
        """Trigger vigilance auto-tuning"""
        cur = self.conn.cursor()
        try:
            cur.execute("SELECT * FROM tune_jr_vigilance(%s)", (self.jr_name,))
            result = cur.fetchone()
            if result:
                old_v, new_v, res_rate, adj = result
                if abs(old_v - new_v) > 0.001:
                    self.log(f"Vigilance tuned: {old_v:.3f} -> {new_v:.3f} (resonance: {res_rate:.2f})")
            self.conn.commit()
        except Exception as e:
            self.log(f"[WARN] Vigilance tuning failed: {e}")
            self.conn.rollback()
        finally:
            cur.close()
    
    def observe_once(self):
        """Run one observation cycle"""
        self.log("Starting observation cycle")
        
        # Load baselines
        self.load_baselines()
        
        # Get recent metrics
        metrics = self.get_recent_metrics()
        
        # Detect patterns
        observations = self.detect_patterns(metrics)
        
        if not observations:
            self.log("No notable patterns detected")
            return
        
        self.log(f"Detected {len(observations)} pattern(s)")
        
        # Save observations
        saved_ids = self.save_observations(observations)
        
        # Generate proposals for significant observations
        proposal_ids = []
        for obs, obs_id in zip(observations, saved_ids):
            should_propose, proposal = self.should_propose_action(obs)
            if should_propose and proposal:
                prop_id = self.create_proposal(obs_id, proposal)
                if prop_id:
                    proposal_ids.append(prop_id)
        
        # Post to thermal memory
        self.post_to_thermal_memory(observations, proposal_ids)
        
        # Tune vigilance
        self.tune_vigilance()
        
        self.log(f"Observation cycle complete: {len(observations)} observations, {len(proposal_ids)} proposals")
    
    def run_daemon(self, interval: int = 300):
        """Run as daemon with specified interval (seconds)"""
        self.log(f"Starting observer daemon (interval: {interval}s)")
        
        while True:
            try:
                if not self.conn or self.conn.closed:
                    if not self.connect():
                        time.sleep(30)
                        continue
                
                self.observe_once()
                
            except KeyboardInterrupt:
                self.log("Shutting down")
                break
            except Exception as e:
                self.log(f"[ERROR] Observation failed: {e}")
            
            time.sleep(interval)


def main():
    parser = argparse.ArgumentParser(description='Jr Self-Observer Daemon')
    parser.add_argument('--jr-name', default='it_triad_jr', help='Jr name to observe')
    parser.add_argument('--once', action='store_true', help='Run once and exit')
    parser.add_argument('--interval', type=int, default=300, help='Daemon interval in seconds')
    
    args = parser.parse_args()
    
    observer = JrObserver(jr_name=args.jr_name)
    
    if not observer.connect():
        sys.exit(1)
    
    if args.once:
        observer.observe_once()
    else:
        observer.run_daemon(interval=args.interval)


if __name__ == '__main__':
    main()
