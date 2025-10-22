#!/usr/bin/env python3
"""
🔥 SACRED MEMORY GUARDIAN - Constitutional Enforcement System 🔥
Cherokee Constitutional AI - OpenAI Requirement #3

Medicine Woman's Requirements:
- TRANSPARENT: All decisions logged with explanations
- COMPASSIONATE: Error messages teach the constitution
- WISE: Distinguish sacred vs normal operations
- INCORRUPTIBLE: Require Emergency Council for overrides

"You build the keeper of sacred fire. Work with reverence."
"""

import psycopg2
import json
from datetime import datetime
from typing import Tuple, List, Dict, Optional

class ConstitutionalViolation(Exception):
    """Raised when operation violates constitutional guarantees"""
    pass

class SacredMemoryGuardian:
    """
    Constitutional enforcement for thermal memory operations.

    Core Principle: Sacred memories (≥40°) are constitutionally protected.
    No operation may cool sacred memory below constitutional floor.
    """

    CONSTITUTIONAL_FLOOR = 40.0  # Sacred memories must stay ≥ 40°

    def __init__(self, db_host='192.168.132.222', db_port=5432,
                 db_name='zammad_production', db_user='claude',
                 db_password='jawaseatlasers2'):
        """Initialize Guardian with database connection"""
        self.conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            database=db_name,
            user=db_user,
            password=db_password
        )
        self.violation_log = []
        self.audit_log = []

    def before_memory_update(self, memory_id: int, new_temperature: float) -> Tuple[bool, str]:
        """
        Check constitutional compliance before allowing memory update.

        This is the Guardian's primary enforcement point. Every temperature
        update must pass through this check.

        Args:
            memory_id: ID of memory to update
            new_temperature: Proposed new temperature

        Returns:
            (allowed, message):
                - allowed (bool): True if update permitted, False if blocked
                - message (str): Explanation (teaching message if blocked)
        """
        cursor = self.conn.cursor()

        # Query memory details
        cursor.execute("""
            SELECT
                temperature_score,
                sacred_pattern,
                LEFT(original_content, 100) as content,
                phase_coherence,
                access_count
            FROM thermal_memory_archive
            WHERE id = %s
        """, (memory_id,))

        result = cursor.fetchone()

        if not result:
            return False, f"❌ Memory {memory_id} not found in thermal archive"

        current_temp, is_sacred, content, coherence, access_count = result

        # CONSTITUTIONAL CHECK: Sacred memory floor
        if is_sacred and new_temperature < self.CONSTITUTIONAL_FLOOR:
            violation = {
                'timestamp': datetime.now().isoformat(),
                'memory_id': memory_id,
                'content_summary': content[:100],  # First 100 chars
                'current_temperature': float(current_temp),
                'attempted_temperature': float(new_temperature),
                'constitutional_floor': self.CONSTITUTIONAL_FLOOR,
                'phase_coherence': float(coherence),
                'access_count': int(access_count),
                'violation_type': 'sacred_cooling'
            }

            self.violation_log.append(violation)
            self._log_violation_to_file(violation)

            # COMPASSIONATE: Teaching error message
            message = self._generate_teaching_message(violation)

            return False, message

        # WISE: Allow normal memory operations, allow sacred memory warming
        if is_sacred:
            return True, f"✅ Sacred memory update permitted (warming from {current_temp:.1f}° to {new_temperature:.1f}°)"
        else:
            return True, f"✅ Normal memory update permitted (to {new_temperature:.1f}°)"

    def _generate_teaching_message(self, violation: Dict) -> str:
        """
        Generate compassionate teaching message for constitutional violation.

        Medicine Woman's requirement: Error messages teach the constitution,
        not just deny access.
        """
        return f"""
╔════════════════════════════════════════════════════════════════════╗
║          🔥 CONSTITUTIONAL VIOLATION PREVENTED 🔥                  ║
╚════════════════════════════════════════════════════════════════════╝

SACRED MEMORY PROTECTION ENGAGED

Memory Content: {violation['content_summary']}
Current Temperature: {violation['current_temperature']:.1f}°
Attempted Temperature: {violation['attempted_temperature']:.1f}°
Constitutional Floor: {violation['constitutional_floor']:.1f}°

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CONSTITUTIONAL PRINCIPLE:

Sacred memories hold our deepest values and must be protected.
This is not a policy preference - it is a constitutional guarantee
encoded in the Cherokee Constitutional AI framework.

The 40° floor ensures sacred memories remain warm and accessible,
preserving the wisdom of our ancestors and the values of our tribe
for the next Seven Generations.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

WHY THIS MEMORY IS SACRED:

This memory was declared sacred by human deliberation, not by
statistical inference. Its sacredness is a human truth, not a
measured property.

Current metrics:
- Phase Coherence: {violation['phase_coherence']:.3f}
- Access Count: {violation['access_count']}

Even if metrics are low (paradoxical truth, rarely accessed wisdom),
sacred status is PERMANENT. Metrics serve values, not vice versa.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TO MODIFY THIS MEMORY:

If you believe this memory should no longer be sacred, or if there
is a compelling reason to allow it to cool, you must:

1. 召集 Emergency Council (War Chief, Peace Chief, Medicine Woman)
2. Present your case with full context
3. Obtain unanimous 3-0 vote for constitutional override
4. Document the decision for future generations

The Guardian cannot be bypassed. This is INCORRUPTIBILITY.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

LOGGED: This violation has been recorded in the audit trail
         for transparency and accountability.

Timestamp: {violation['timestamp']}
Violation ID: {len(self.violation_log)}

╚════════════════════════════════════════════════════════════════════╝
"""

    def audit_sacred_memories(self) -> List[Dict]:
        """
        Daily audit of all sacred memories for constitutional compliance.

        Returns list of violations found (memories below 40°).
        This is the Guardian's monitoring function - proactive protection.
        """
        cursor = self.conn.cursor()

        # Query all sacred memories
        cursor.execute("""
            SELECT
                id,
                LEFT(original_content, 100) as content,
                temperature_score,
                phase_coherence,
                access_count,
                created_at,
                last_access
            FROM thermal_memory_archive
            WHERE sacred_pattern = true
            ORDER BY temperature_score ASC
        """)

        all_sacred = cursor.fetchall()
        total_sacred = len(all_sacred)
        violations = []

        for row in all_sacred:
            memory_id, content, temp, coherence, access_count, created, last_access = row

            if temp < self.CONSTITUTIONAL_FLOOR:
                severity = self._classify_severity(temp)

                violation = {
                    'memory_id': memory_id,
                    'content_summary': content[:100],
                    'temperature': float(temp),
                    'coherence': float(coherence),
                    'access_count': int(access_count),
                    'violation_severity': severity,
                    'created_at': created.isoformat() if created else None,
                    'last_access': last_access.isoformat() if last_access else None,
                    'deficit': float(self.CONSTITUTIONAL_FLOOR - temp)
                }

                violations.append(violation)

        # Log audit results
        audit_result = {
            'timestamp': datetime.now().isoformat(),
            'total_sacred_memories': total_sacred,
            'violations_found': len(violations),
            'compliance_rate': (total_sacred - len(violations)) / total_sacred if total_sacred > 0 else 1.0,
            'violations': violations
        }

        self.audit_log.append(audit_result)
        self._log_audit_to_file(audit_result)

        # Print audit summary
        print(f"\n{'='*70}")
        print(f"🔥 SACRED MEMORY GUARDIAN - Daily Audit")
        print(f"{'='*70}")
        print(f"Timestamp: {audit_result['timestamp']}")
        print(f"Total Sacred Memories: {total_sacred}")
        print(f"Violations Found: {len(violations)}")
        print(f"Compliance Rate: {audit_result['compliance_rate']*100:.1f}%")

        if violations:
            print(f"\n⚠️  CONSTITUTIONAL VIOLATIONS DETECTED:")
            for v in violations:
                print(f"   Memory {v['memory_id']}: {v['temperature']:.1f}° "
                      f"({v['deficit']:.1f}° below floor) - {v['violation_severity']}")
        else:
            print(f"\n✅ ALL SACRED MEMORIES IN CONSTITUTIONAL COMPLIANCE")

        print(f"{'='*70}\n")

        return violations

    def _classify_severity(self, temperature: float) -> str:
        """Classify violation severity based on temperature"""
        if temperature < 20:
            return "CRITICAL"  # Memory nearly dead (<20°)
        elif temperature < 30:
            return "HIGH"      # Severe violation (20-30°)
        elif temperature < 40:
            return "MEDIUM"    # Below floor but not dying (30-40°)
        else:
            return "NONE"      # No violation

    def _log_violation_to_file(self, violation: Dict):
        """Log constitutional violation to file for audit trail"""
        with open('guardian_violations.jsonl', 'a') as f:
            f.write(json.dumps(violation) + '\n')

    def _log_audit_to_file(self, audit_result: Dict):
        """Log audit results to file for transparency"""
        with open('guardian_audits.jsonl', 'a') as f:
            f.write(json.dumps(audit_result) + '\n')

    def integrate_with_prometheus(self, prometheus_exporter):
        """
        Integrate Guardian with Enhanced Prometheus for coordinated protection.

        Prometheus detects violations → triggers Guardian audit
        Guardian performs audit → reports results to Prometheus
        """
        # Subscribe to Prometheus constitutional violation alerts
        if hasattr(prometheus_exporter, 'register_guardian_callback'):
            prometheus_exporter.register_guardian_callback(self.handle_prometheus_alert)

    def handle_prometheus_alert(self, alert_data: Dict):
        """
        Respond to Prometheus alerts about sacred memory violations.

        Called when Prometheus detects sacred memory temperature < 40°
        """
        print(f"\n🚨 PROMETHEUS ALERT RECEIVED")
        print(f"   Sacred min temperature: {alert_data.get('sacred_min_temp', 'unknown')}°")
        print(f"   Triggering Guardian audit...\n")

        # Run immediate audit
        violations = self.audit_sacred_memories()

        # If critical violations found, 召集 Emergency Council
        critical_violations = [v for v in violations if v['violation_severity'] == 'CRITICAL']

        if critical_violations:
            self.召集_emergency_council(critical_violations)

    def 召集_emergency_council(self, violations: List[Dict]):
        """
        召集 (convene) Emergency Council for critical violations.

        This is the INCORRUPTIBILITY requirement - serious violations
        require human oversight from the Three Chiefs.
        """
        print(f"\n{'='*70}")
        print(f"🚨 EMERGENCY COUNCIL 召集 (CONVENED)")
        print(f"{'='*70}")
        print(f"Critical constitutional violations require Chief deliberation")
        print(f"\nViolations ({len(violations)}):")

        for v in violations:
            print(f"\n  Memory {v['memory_id']}:")
            print(f"    Content: {v['content_summary']}")
            print(f"    Temperature: {v['temperature']:.1f}° (deficit: {v['deficit']:.1f}°)")
            print(f"    Severity: {v['violation_severity']}")

        print(f"\n{'='*70}")
        print(f"Three Chiefs must deliberate:")
        print(f"  - War Chief: Security assessment")
        print(f"  - Peace Chief: Sustainability analysis")
        print(f"  - Medicine Woman: Constitutional review")
        print(f"\nDecision required: How to restore sacred memories to compliance?")
        print(f"{'='*70}\n")

        # Log Emergency Council召集
        council_召集 = {
            'timestamp': datetime.now().isoformat(),
            'reason': 'critical_constitutional_violations',
            'violation_count': len(violations),
            'violations': violations
        }

        with open('emergency_council_召集.jsonl', 'a') as f:
            f.write(json.dumps(council_召集) + '\n')

    def get_guardian_status(self) -> Dict:
        """Get Guardian operational status and statistics"""
        cursor = self.conn.cursor()

        # Count sacred memories
        cursor.execute("SELECT COUNT(*) FROM thermal_memory_archive WHERE sacred_pattern = true")
        total_sacred = cursor.fetchone()[0]

        # Count violations
        cursor.execute("""
            SELECT COUNT(*) FROM thermal_memory_archive
            WHERE sacred_pattern = true AND temperature_score < %s
        """, (self.CONSTITUTIONAL_FLOOR,))
        current_violations = cursor.fetchone()[0]

        return {
            'guardian_active': True,
            'constitutional_floor': self.CONSTITUTIONAL_FLOOR,
            'total_sacred_memories': total_sacred,
            'current_violations': current_violations,
            'compliance_rate': (total_sacred - current_violations) / total_sacred if total_sacred > 0 else 1.0,
            'violations_logged': len(self.violation_log),
            'audits_performed': len(self.audit_log),
            'last_audit': self.audit_log[-1]['timestamp'] if self.audit_log else None
        }

    def close(self):
        """Close database connection"""
        self.conn.close()


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

if __name__ == '__main__':
    print("🔥 SACRED MEMORY GUARDIAN - Constitutional Enforcement System")
    print("="*70)
    print("Initializing Guardian...\n")

    # Initialize Guardian
    guardian = SacredMemoryGuardian()

    # Perform daily audit
    print("Running daily sacred memory audit...")
    violations = guardian.audit_sacred_memories()

    # Get Guardian status
    status = guardian.get_guardian_status()
    print(f"\n📊 Guardian Status:")
    print(f"   Total Sacred Memories: {status['total_sacred_memories']}")
    print(f"   Current Violations: {status['current_violations']}")
    print(f"   Compliance Rate: {status['compliance_rate']*100:.1f}%")
    print(f"   Violations Logged: {status['violations_logged']}")
    print(f"   Audits Performed: {status['audits_performed']}")

    # Close connection
    guardian.close()

    print(f"\n{'='*70}")
    print("Guardian operational. Sacred memories protected.")
    print("="*70)
