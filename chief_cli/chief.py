#!/usr/bin/env python3
"""
Cherokee Chief CLI - Self-Improving Executive Interface
The crown jewel: conversational AI that learns from every interaction

Usage:
    python3 chief.py              # Interactive mode
    python3 chief.py --query "why is gpu low?"  # Single query
    python3 chief.py --status     # Show CLI health
"""

import os
import sys
import uuid
import json
import readline
from datetime import datetime
from typing import Optional, Dict, Any, Tuple

# Add paths
sys.path.insert(0, '/ganuda/pathfinder/wisdom')
sys.path.insert(0, '/ganuda/jr_executor')

import psycopg2
from llm_router import LLMRouter
from resonance import WisdomResonance

class ChiefCLI:
    """Cherokee Chief - Self-improving executive CLI"""

    VERSION = "1.0.0"

    # Query type patterns for intent classification
    INTENT_PATTERNS = {
        'infrastructure': ['why', 'slow', 'high', 'low', 'memory', 'cpu', 'gpu', 'disk', 'network', 'database', 'postgres', 'syslog', 'logs', 'performance', 'sluggish', 'check', 'investigate', 'look', 'weird', 'error', 'redfin', 'bluefin'],
        'mission': ['mission', 'delegate to jr', 'assign jr', 'create task', 'jr task'],
        'consultation': ['consult', 'chiefs', 'council', 'deliberate', 'vote', 'approve', 'decision'],
        'status': ['status', 'health', 'jr status', 'cherokee status', 'wisdom health'],
        'resonance': ['resonance', 'accuracy', 'learning', 'improving', 'feedback']
    }

    def __init__(self, prefer_local_llm: bool = False):
        """Initialize Chief CLI"""
        self.session_id = uuid.uuid4()
        self.llm_router = LLMRouter(prefer_local=prefer_local_llm)
        self.wisdom = WisdomResonance()
        self.db_config = {
            'host': '192.168.132.222',
            'database': 'triad_federation',
            'user': 'claude',
            'password': 'jawaseatlasers2'
        }
        self.conversation_history = []

    def _get_db(self):
        return psycopg2.connect(**self.db_config)

    def classify_intent(self, query: str) -> Tuple[str, float]:
        """Classify user intent from query"""
        query_lower = query.lower()
        scores = {}

        for intent, patterns in self.INTENT_PATTERNS.items():
            score = sum(1 for p in patterns if p in query_lower)
            scores[intent] = score

        if max(scores.values()) == 0:
            return 'general', 0.5

        best_intent = max(scores, key=scores.get)
        confidence = min(scores[best_intent] / 3.0, 1.0)  # Normalize
        return best_intent, confidence

    def get_real_system_data(self) -> dict:
        """Gather real system metrics from nodes"""
        import subprocess
        import socket
        data = {}
        
        hostname = socket.gethostname()

        # Check if we're on redfin
        if 'redfin' in hostname.lower():
            # Local commands for redfin
            try:
                result = subprocess.run(["df", "-h", "/"], capture_output=True, text=True, timeout=5)
                lines = result.stdout.strip().split(chr(10))
                if len(lines) > 1:
                    parts = lines[1].split()
                    data['redfin_disk'] = parts[4] if len(parts) > 4 else 'N/A'
                
                result = subprocess.run(["uptime"], capture_output=True, text=True, timeout=5)
                if 'load average' in result.stdout:
                    data['redfin_load'] = result.stdout.split('load average:')[1].strip()
                
                result = subprocess.run(["free", "-h"], capture_output=True, text=True, timeout=5)
                for line in result.stdout.split(chr(10)):
                    if line.startswith('Mem:'):
                        parts = line.split()
                        data['redfin_memory'] = f"{parts[2]}/{parts[1]}" if len(parts) > 2 else 'N/A'
            except Exception as e:
                data['redfin_error'] = str(e)
        
        # Remote check for bluefin
        try:
            result = subprocess.run(
                ['ssh', '-o', 'ConnectTimeout=3', '-o', 'StrictHostKeyChecking=no', 
                 'dereadi@192.168.132.222', "df -h / | tail -1 | awk '{print }'"],
                capture_output=True, text=True, timeout=10
            )
            data['bluefin_disk'] = result.stdout.strip() if result.returncode == 0 else 'unreachable'
            
            result = subprocess.run(
                ['ssh', '-o', 'ConnectTimeout=3', '-o', 'StrictHostKeyChecking=no',
                 'dereadi@192.168.132.222', "uptime | awk -F'load average:' '{print }'"],
                capture_output=True, text=True, timeout=10
            )
            data['bluefin_load'] = result.stdout.strip() if result.returncode == 0 else 'unreachable'
            
            result = subprocess.run(
                ['ssh', '-o', 'ConnectTimeout=3', '-o', 'StrictHostKeyChecking=no',
                 'dereadi@192.168.132.222', "free -h | grep Mem | awk '{print "/"}'"],
                capture_output=True, text=True, timeout=10
            )
            data['bluefin_memory'] = result.stdout.strip() if result.returncode == 0 else 'unreachable'
        except Exception as e:
            data['bluefin_error'] = str(e)

        return data

    def handle_infrastructure_query(self, query: str) -> str:
        """Handle infrastructure questions via Wisdom with real data"""
        try:
            # Gather real system data
            sys_data = self.get_real_system_data()

            context = {
                'source': 'chief_cli',
                'type': 'infrastructure',
                'real_metrics': sys_data
            }

            # Enhanced prompt with real data
            enhanced_query = f"""{query}

Current system metrics:
- Redfin (192.168.132.223): Disk {sys_data.get('redfin_disk', 'N/A')}, Load {sys_data.get('redfin_load', 'N/A')}, Memory {sys_data.get('redfin_memory', 'N/A')}
- Bluefin (192.168.132.222): Disk {sys_data.get('bluefin_disk', 'N/A')}, Load {sys_data.get('bluefin_load', 'N/A')}, Memory {sys_data.get('bluefin_memory', 'N/A')}

Use these real metrics to inform your answer."""

            result = self.llm_router.query(enhanced_query, context=context)
            return result['answer']
        except Exception as e:
            return f"Error querying Wisdom: {e}"


    def handle_mission_creation(self, query: str) -> str:
        """Create and delegate mission to Jr"""
        try:
            mission_data = {
                'title': query[:60] if len(query) < 60 else query[:57] + '...',
                'priority': 'medium',
                'instructions': query,
                'tasks': [query],
                'source': 'chief_cli',
                'timestamp': datetime.now().isoformat()
            }

            result = self.llm_router.query(
                f"Break this into 3-5 specific steps: {query}",
                system_prompt="List actionable steps, one per line. Be brief."
            )

            response = result.get('answer', '')
            lines = [l.strip() for l in response.splitlines() if l.strip() and len(l.strip()) > 5]
            steps = [l.lstrip('0123456789.-) ') for l in lines[:5]]
            if steps:
                mission_data['tasks'] = steps

            conn = self._get_db()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO triad_shared_memories
                (content, temperature, source_triad, tags, access_level)
                VALUES (%s, 90.0, 'chief_cli',
                        ARRAY['jr_mission', 'it_triad_jr', 'chief_delegated'],
                        'triad')
                RETURNING id
            """, (json.dumps(mission_data),))
            mission_id = cur.fetchone()[0]
            conn.commit()
            cur.close()
            conn.close()

            tasks_list = mission_data['tasks'][:3]
            tasks_str = "\n".join([f"  - {t[:50]}" for t in tasks_list])
            return f"""Mission created and delegated to Jr!

ID: {mission_id}
Title: {mission_data['title']}

Tasks:
{tasks_str}

Jr will pick this up on next poll."""

        except Exception as e:
            return f"Error creating mission: {e}"

    def handle_consultation(self, query: str) -> str:

        """Consult Three Chiefs for deliberation"""
        # Post consultation request
        try:
            conn = self._get_db()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO triad_shared_memories
                (content, temperature, source_triad, tags, access_level)
                VALUES (%s, 95.0, 'chief_cli',
                        ARRAY['consultation_request', 'three_chiefs', 'chief_cli'],
                        'council')
                RETURNING id
            """, (json.dumps({
                'type': 'consultation_request',
                'query': query,
                'requested_by': 'chief_cli',
                'timestamp': datetime.now().isoformat()
            }),))
            consult_id = cur.fetchone()[0]
            conn.commit()
            cur.close()
            conn.close()

            return f"Consultation request posted to Three Chiefs.\nID: {consult_id}\nThe council will deliberate and respond via thermal memory."

        except Exception as e:
            return f"Error posting consultation: {e}"

    def handle_status(self, query: str) -> str:
        """Show system status"""
        try:
            conn = self._get_db()
            cur = conn.cursor()

            # Jr status
            cur.execute("""
                SELECT outcome, COUNT(*) FROM jr_task_history
                WHERE assigned_at > NOW() - INTERVAL '24 hours'
                GROUP BY outcome
            """)
            jr_stats = dict(cur.fetchall())

            # Resonance health
            cur.execute("SELECT * FROM chief_cli_health")
            cli_health = cur.fetchall()

            # Wisdom health
            wisdom_health = self.wisdom.get_health_summary()

            cur.close()
            conn.close()

            status = f"""
Cherokee AI Status
==================

Jr Tasks (24h):
  Success: {jr_stats.get('success', 0)}
  Failed: {jr_stats.get('failed', 0)}

Wisdom Accuracy: {wisdom_health.get('overall_accuracy', 0)*100:.0f}%
  Predictions validated: {wisdom_health.get('total_validated', 0)}

Chief CLI Health:
  Session: {self.session_id}
  LLM: {self.llm_router.status().get('active_llm', 'none')}
"""
            return status

        except Exception as e:
            return f"Error getting status: {e}"

    def handle_resonance_query(self, query: str) -> str:
        """Show resonance/learning metrics"""
        try:
            conn = self._get_db()
            cur = conn.cursor()

            # CLI resonance
            cur.execute("""
                SELECT query_type,
                       COUNT(*) as total,
                       AVG(resonance_score) as avg_score
                FROM chief_cli_resonance
                WHERE resonance_score IS NOT NULL
                GROUP BY query_type
            """)
            cli_resonance = cur.fetchall()

            # Jr resonance
            cur.execute("""
                SELECT task_type,
                       COUNT(*) as total,
                       AVG(resonance_score) as avg_score
                FROM jr_resonance_events
                GROUP BY task_type
            """)
            jr_resonance = cur.fetchall()

            cur.close()
            conn.close()

            output = """
Resonance Metrics (Self-Improvement Tracking)
=============================================

Chief CLI Resonance:
"""
            for qtype, total, score in cli_resonance:
                output += f"  {qtype}: {score*100:.0f}% ({total} interactions)\n"

            output += "\nJr Resonance:\n"
            for ttype, total, score in jr_resonance:
                output += f"  {ttype}: {score*100:.0f}% ({total} tasks)\n"

            output += f"\nWisdom Resonance:\n"
            wh = self.wisdom.get_health_summary()
            output += f"  Overall: {wh.get('overall_accuracy', 0)*100:.0f}%\n"

            return output

        except Exception as e:
            return f"Error getting resonance: {e}"

    def record_interaction(self, query: str, intent: str, confidence: float,
                          response: str, response_type: str,
                          response_time_ms: int) -> uuid.UUID:
        """Record interaction for resonance tracking"""
        try:
            conn = self._get_db()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO chief_cli_resonance
                (session_id, query_type, user_query, detected_intent,
                 intent_confidence, response_type, response_summary,
                 conversation_context, llm_used, response_time_ms)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING interaction_id
            """, (
                str(self.session_id), intent, query, intent,
                confidence, response_type, response[:500],
                json.dumps(self.conversation_history[-5:]),
                self.llm_router.status().get('active_llm'),
                response_time_ms
            ))
            interaction_id = cur.fetchone()[0]
            conn.commit()
            cur.close()
            conn.close()
            return interaction_id
        except Exception as e:
            print(f"[Warning] Could not record interaction: {e}")
            return None

    def record_feedback(self, interaction_id: uuid.UUID, feedback: str):
        """Record user feedback and calculate resonance"""
        score_map = {'y': 1.0, 'yes': 1.0, 'n': 0.0, 'no': 0.0,
                     'p': 0.5, 'partial': 0.5, 'partially': 0.5}
        score = score_map.get(feedback.lower(), 0.5)

        try:
            conn = self._get_db()
            cur = conn.cursor()
            cur.execute("""
                UPDATE chief_cli_resonance
                SET user_feedback = %s,
                    resonance_score = %s,
                    feedback_at = NOW()
                WHERE interaction_id = %s
            """, (feedback, score, str(interaction_id)))
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            print(f"[Warning] Could not record feedback: {e}")

    def process_query(self, query: str) -> Tuple[str, uuid.UUID]:
        """Process user query and return response"""
        start_time = datetime.now()

        # Classify intent
        intent, confidence = self.classify_intent(query)

        # Route to appropriate handler
        handlers = {
            'infrastructure': (self.handle_infrastructure_query, 'wisdom'),
            'mission': (self.handle_mission_creation, 'delegation'),
            'consultation': (self.handle_consultation, 'consultation'),
            'status': (self.handle_status, 'direct'),
            'resonance': (self.handle_resonance_query, 'direct'),
            'general': (self.handle_infrastructure_query, 'wisdom')
        }

        handler, response_type = handlers.get(intent, handlers['general'])
        response = handler(query)

        # Calculate response time
        response_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)

        # Record for resonance
        interaction_id = self.record_interaction(
            query, intent, confidence, response,
            response_type, response_time_ms
        )

        # Add to conversation history
        self.conversation_history.append({
            'query': query,
            'intent': intent,
            'response': response[:200]
        })

        return response, interaction_id

    def print_banner(self):
        """Print startup banner"""
        print("""
╔══════════════════════════════════════════════════════════════╗
║              Cherokee Chief CLI v{version}                      ║
║           Self-Improving Executive Interface                 ║
╠══════════════════════════════════════════════════════════════╣
║  Commands:                                                   ║
║    /status    - System status                               ║
║    /resonance - Learning metrics                            ║
║    /mission   - Create Jr mission                           ║
║    /consult   - Ask Three Chiefs                            ║
║    /help      - Show help                                   ║
║    /quit      - Exit                                        ║
║                                                              ║
║  Or just ask anything about your infrastructure!            ║
║                                                              ║
║  LLM: {llm}                                       ║
╚══════════════════════════════════════════════════════════════╝
        """.format(
            version=self.VERSION,
            llm=self.llm_router.status().get('active_llm', 'none').ljust(20)
        ))

    def run_interactive(self):
        """Run interactive CLI loop"""
        self.print_banner()

        last_interaction_id = None

        while True:
            try:
                query = input("\n🪶 Chief> ").strip()

                if not query:
                    continue

                # Handle special commands
                if query.startswith('/'):
                    cmd = query[1:].lower().split()[0]
                    if cmd in ['quit', 'exit', 'q']:
                        print("\nWado! (Thank you) - For Seven Generations 🔥")
                        break
                    elif cmd == 'help':
                        print(self.__doc__)
                        continue
                    elif cmd == 'status':
                        query = "show system status"
                    elif cmd == 'resonance':
                        query = "show resonance metrics"
                    elif cmd == 'mission':
                        query = "create mission: " + query[8:]
                    elif cmd == 'consult':
                        query = "consult chiefs about: " + query[8:]

                # Process query
                print("\n⏳ Thinking...")
                response, interaction_id = self.process_query(query)
                last_interaction_id = interaction_id

                print(f"\n{response}")

                # Ask for feedback
                if interaction_id:
                    feedback = input("\nWas this helpful? [y/n/p(artial)/skip]: ").strip().lower()
                    if feedback and feedback not in ['skip', 's', '']:
                        self.record_feedback(interaction_id, feedback)
                        print("📊 Feedback recorded - Chief CLI is learning!")

            except KeyboardInterrupt:
                print("\n\nInterrupted. Type /quit to exit.")
            except EOFError:
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Cherokee Chief CLI')
    parser.add_argument('--query', '-q', help='Single query mode')
    parser.add_argument('--status', '-s', action='store_true', help='Show status')
    parser.add_argument('--local', '-l', action='store_true', help='Prefer local LLM')
    args = parser.parse_args()

    chief = ChiefCLI(prefer_local_llm=args.local)

    if args.status:
        print(chief.handle_status(""))
    elif args.query:
        response, _ = chief.process_query(args.query)
        print(response)
    else:
        chief.run_interactive()


if __name__ == '__main__':
    main()