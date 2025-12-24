#!/usr/bin/env python3
"""
Jr Task Executor Daemon - Executes assigned tasks.

Based on Contract Net Protocol from JR_TASK_BIDDING_SYSTEM.md.
Completes the execution phase after bidding assigns tasks.

Run as: python3 jr_task_executor.py <agent_id> <node_name>
Example: python3 jr_task_executor.py jr-redfin-gecko redfin

Enhanced Dec 23, 2025: Added 'content' task type for document generation.

For Seven Generations - Cherokee AI Federation
"""

import os
import sys
import time
import signal
import json
import re
import requests
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from typing import Tuple, List, Optional

# Configuration
POLL_INTERVAL = 30  # seconds between task checks
MAX_TASK_DURATION = 3600  # 1 hour timeout

DB_CONFIG = {
    'host': os.environ.get('CHEROKEE_DB_HOST', '192.168.132.222'),
    'database': os.environ.get('CHEROKEE_DB_NAME', 'zammad_production'),
    'user': os.environ.get('CHEROKEE_DB_USER', 'claude'),
    'password': os.environ.get('CHEROKEE_DB_PASS', 'jawaseatlasers2')
}

GATEWAY_URL = os.environ.get('CHEROKEE_GATEWAY_URL', 'http://192.168.132.223:8080')
API_KEY = os.environ.get('CHEROKEE_API_KEY', 'ck-cabccc2d6037c1dce1a027cc80df7b14cdba66143e3c2d4f3bdf0fd53b6ab4a5')

# Security whitelists
SAFE_READ_PATHS = [
    '/ganuda/docs/',
    '/ganuda/lib/',
    '/Users/Shared/ganuda/docs/',
]

SAFE_WRITE_PATHS = [
    '/ganuda/docs/research/',
    '/ganuda/docs/reports/',
    '/ganuda/docs/whitepapers/',
    '/ganuda/docs/kb/',
    '/Users/Shared/ganuda/docs/research/',
    '/Users/Shared/ganuda/docs/whitepapers/',
]


class JrTaskExecutor:
    """
    Daemon that executes tasks assigned to this Jr agent.
    """

    def __init__(self, agent_id: str, node_name: str):
        self.agent_id = agent_id
        self.node_name = node_name
        self.running = True
        self._conn = None

        signal.signal(signal.SIGINT, self._shutdown)
        signal.signal(signal.SIGTERM, self._shutdown)

    def _get_connection(self):
        if self._conn is None or self._conn.closed:
            self._conn = psycopg2.connect(**DB_CONFIG)
        return self._conn

    def _shutdown(self, signum, frame):
        print(f"\n[{self.agent_id}] Shutting down executor...")
        self.running = False

    def get_assigned_tasks(self) -> List[dict]:
        """Get tasks assigned to this agent that are ready to execute."""
        try:
            conn = self._get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT task_id, task_type, task_content, priority
                    FROM jr_task_announcements
                    WHERE assigned_to = %s AND status = 'assigned'
                    ORDER BY priority ASC, announced_at ASC
                    LIMIT 1
                """, (self.agent_id,))
                result = cur.fetchall()
                return list(result)
        except Exception as e:
            print(f"[{self.agent_id}] Error fetching tasks: {e}")
            return []

    def start_task(self, task_id: str):
        """Mark task as in_progress."""
        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE jr_task_announcements
                    SET status = 'in_progress'
                    WHERE task_id = %s
                """, (task_id,))
                conn.commit()
            print(f"[{self.agent_id}] Started task: {task_id}")
        except Exception as e:
            print(f"[{self.agent_id}] Error starting task: {e}")

    def execute_task(self, task: dict) -> Tuple[bool, str]:
        """Execute task based on type."""
        task_type = task.get('task_type', 'unknown')
        task_id = task['task_id']

        print(f"[{self.agent_id}] Executing {task_type} task: {task_id}")

        try:
            if task_type == 'research':
                return self._execute_research_task(task)
            elif task_type == 'implementation':
                return self._execute_implementation_task(task)
            elif task_type == 'review':
                return self._execute_review_task(task)
            elif task_type == 'content':
                return self._execute_content_task(task)
            else:
                return False, f"Unknown task type: {task_type}"
        except Exception as e:
            return False, f"Execution error: {str(e)}"

    def _query_thermal_memory(self, query: str, limit: int = 5) -> str:
        """Query thermal memory for context."""
        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                search_pattern = '%' + '%'.join(query.split()[:5]) + '%'
                cur.execute("""
                    SELECT LEFT(original_content, 300), temperature_score
                    FROM thermal_memory_archive
                    WHERE original_content ILIKE %s
                    ORDER BY temperature_score DESC, created_at DESC
                    LIMIT %s
                """, (search_pattern, limit))
                rows = cur.fetchall()
                
                if rows:
                    context = ""
                    for content, temp in rows:
                        context += f"[{temp:.0f}C] {content}\n\n"
                    return context
        except Exception as e:
            print(f"[{self.agent_id}] Thermal query error: {e}")
        return "No relevant memories found."

    def _call_llm(self, prompt: str, max_tokens: int = 1000) -> str:
        """Call LLM Gateway for processing."""
        try:
            response = requests.post(
                f"{GATEWAY_URL}/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "default",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": max_tokens
                },
                timeout=180  # Increased for long content generation
            )
            response.raise_for_status()
            data = response.json()
            return data['choices'][0]['message']['content']
        except Exception as e:
            return f"LLM call failed: {str(e)}"

    def _execute_research_task(self, task: dict) -> Tuple[bool, str]:
        """Execute research task via LLM."""
        content = task['task_content']
        task_id = task['task_id']

        # Get thermal memory context
        context = self._query_thermal_memory(content[:100])

        # Build research prompt
        prompt = f"""You are a research assistant for Cherokee AI Federation.

Research Task: {content}

Relevant context from thermal memory:
{context}

Provide a structured research summary with:
1. Key Findings - What is important about this topic
2. Cherokee AI Relevance - How this applies to our infrastructure
3. Recommended Next Steps - Concrete actions to take

Be concise but thorough."""

        # Call LLM
        result = self._call_llm(prompt, max_tokens=1500)

        # Ensure research directory exists
        research_dir = '/ganuda/docs/research'
        os.makedirs(research_dir, exist_ok=True)

        # Save report
        report_path = f"{research_dir}/{task_id}_report.md"
        try:
            with open(report_path, 'w') as f:
                f.write(f"# Research Report: {task_id}\n")
                f.write(f"**Generated:** {datetime.now().isoformat()}\n")
                f.write(f"**Agent:** {self.agent_id}\n\n")
                f.write(result)
            return True, f"Research complete. Report saved to {report_path}"
        except Exception as e:
            return True, f"Research complete but could not save report: {str(e)}. Result: {result[:500]}"

    def _execute_implementation_task(self, task: dict) -> Tuple[bool, str]:
        """Execute implementation task (limited to safe operations)."""
        content = task['task_content']
        task_id = task['task_id']

        # For now, implementation tasks get LLM analysis + recommendations
        # Full code execution requires more security review
        
        prompt = f"""You are an implementation assistant for Cherokee AI Federation.

Implementation Task: {content}

Analyze this task and provide:
1. Implementation Steps - Detailed steps to complete this task
2. Files to Modify - Which files need changes
3. Security Considerations - Any security concerns
4. Estimated Complexity - Simple/Medium/Complex

Note: Actual code changes require TPM approval. Provide the plan."""

        result = self._call_llm(prompt, max_tokens=2000)

        # Save implementation plan
        reports_dir = '/ganuda/docs/reports'
        os.makedirs(reports_dir, exist_ok=True)

        report_path = f"{reports_dir}/{task_id}_impl_plan.md"
        try:
            with open(report_path, 'w') as f:
                f.write(f"# Implementation Plan: {task_id}\n")
                f.write(f"**Generated:** {datetime.now().isoformat()}\n")
                f.write(f"**Agent:** {self.agent_id}\n\n")
                f.write(result)
            return True, f"Implementation plan created. Plan saved to {report_path}"
        except Exception as e:
            return True, f"Plan created but could not save: {str(e)}. Result: {result[:500]}"

    def _execute_review_task(self, task: dict) -> Tuple[bool, str]:
        """Execute review task."""
        content = task['task_content']

        prompt = f"""You are a code/document reviewer for Cherokee AI Federation.

Review Task: {content}

Provide:
1. Summary - What was reviewed
2. Findings - Issues or observations
3. Recommendations - Suggested improvements
4. Verdict - APPROVE / NEEDS_CHANGES / REJECT"""

        result = self._call_llm(prompt, max_tokens=1000)
        return True, f"Review complete: {result[:500]}"

    def _execute_content_task(self, task: dict) -> Tuple[bool, str]:
        """Execute content generation task - creates actual documents."""
        content = task['task_content']
        task_id = task['task_id']
        
        # Extract output path from task content
        output_path = self._extract_output_path(content)
        
        # Validate output path is in safe write paths
        if output_path and not self._is_safe_write_path(output_path):
            return False, f"Output path not allowed: {output_path}"
        
        # Get thermal memory context
        thermal_context = self._query_thermal_memory(content, limit=5)
        
        # Check for referenced plan files
        plan_context = self._get_plan_context(content)
        
        prompt = f"""You are a technical writer for Cherokee AI Federation.

TASK: {content}

THERMAL MEMORY CONTEXT:
{thermal_context}

REFERENCED PLANS:
{plan_context}

INSTRUCTIONS:
1. Write the FULL content as requested (not a plan, the actual document)
2. Follow any template structure mentioned in the task
3. Include all sections with complete content
4. Target 2000-3000 words for whitepapers
5. Use professional tone with Cherokee AI Federation branding
6. Include "For Seven Generations" where appropriate
7. Use markdown formatting with headers, lists, and code blocks where needed

Write the complete document now:"""

        result = self._call_llm(prompt, max_tokens=4000)
        
        if not result or result.startswith('LLM call failed'):
            return False, f"LLM error: {result}"
        
        # Save to specified output path or default location
        if output_path:
            try:
                # Ensure directory exists
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                
                with open(output_path, 'w') as f:
                    f.write(result)
                
                return True, f"Content created and saved to {output_path}"
            except Exception as e:
                # Fallback to reports directory
                fallback_path = f"/ganuda/docs/reports/{task_id}_content.md"
                try:
                    with open(fallback_path, 'w') as f:
                        f.write(result)
                    return True, f"Content saved to fallback: {fallback_path} (original error: {e})"
                except Exception as e2:
                    return False, f"Could not save content: {e2}"
        else:
            # Default save location
            default_path = f"/ganuda/docs/reports/{task_id}_content.md"
            os.makedirs(os.path.dirname(default_path), exist_ok=True)
            
            try:
                with open(default_path, 'w') as f:
                    f.write(result)
                return True, f"Content created and saved to {default_path}"
            except Exception as e:
                return False, f"Could not save content: {e}"

    def _extract_output_path(self, content: str) -> Optional[str]:
        """Extract output file path from task content."""
        # Look for "Save to /path/to/file.md" pattern
        patterns = [
            r'[Ss]ave to\s+(/[^\s]+\.md)',
            r'[Oo]utput:?\s+(/[^\s]+\.md)',
            r'[Ww]rite to\s+(/[^\s]+\.md)',
            r'(/ganuda/docs/whitepapers/[^\s]+\.md)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1)
        
        return None

    def _is_safe_write_path(self, path: str) -> bool:
        """Check if path is in safe write locations."""
        for safe_path in SAFE_WRITE_PATHS:
            if path.startswith(safe_path):
                return True
        return False

    def _get_plan_context(self, content: str) -> str:
        """Read referenced plan files for context."""
        # Find referenced plan files
        pattern = r'(/ganuda/docs/[^\s]+\.md)'
        matches = re.findall(pattern, content)
        
        context_parts = []
        for path in matches[:3]:  # Limit to 3 files
            try:
                if os.path.exists(path):
                    with open(path, 'r') as f:
                        # Read first 2000 chars of each plan
                        plan_content = f.read(2000)
                        context_parts.append(f"=== {path} ===\n{plan_content}\n")
            except Exception as e:
                context_parts.append(f"=== {path} === (error reading: {e})\n")
        
        return "\n".join(context_parts) if context_parts else "No plan files referenced."

    def complete_task(self, task_id: str, result: str):
        """Mark task as completed."""
        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE jr_task_announcements
                    SET status = 'completed', 
                        result = %s,
                        completed_at = NOW()
                    WHERE task_id = %s
                """, (result[:2000], task_id))
                conn.commit()
            print(f"[{self.agent_id}] Completed task: {task_id}")
        except Exception as e:
            print(f"[{self.agent_id}] Error completing task: {e}")

    def fail_task(self, task_id: str, error: str):
        """Mark task as failed."""
        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE jr_task_announcements
                    SET status = 'failed',
                        result = %s,
                        completed_at = NOW()
                    WHERE task_id = %s
                """, (f"FAILED: {error}"[:2000], task_id))
                conn.commit()
            print(f"[{self.agent_id}] Failed task: {task_id} - {error}")
        except Exception as e:
            print(f"[{self.agent_id}] Error marking task failed: {e}")

    def log_to_thermal_memory(self, task: dict, success: bool, result: str):
        """Store task execution in thermal memory."""
        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                memory_hash = f"task-exec-{task['task_id']}-{int(time.time())}"
                content = f"Task Execution: {task['task_id']} ({task['task_type']}) - {'SUCCESS' if success else 'FAILED'} by {self.agent_id}. Result: {result[:500]}"
                temp_score = 75.0 if success else 85.0  # Failed tasks are hotter (need attention)
                
                metadata = json.dumps({
                    "type": "task_execution",
                    "task_id": task['task_id'],
                    "task_type": task['task_type'],
                    "agent_id": self.agent_id,
                    "success": success,
                    "node": self.node_name
                })

                cur.execute("""
                    INSERT INTO thermal_memory_archive 
                    (memory_hash, original_content, temperature_score, metadata)
                    VALUES (%s, %s, %s, %s::jsonb)
                """, (memory_hash, content, temp_score, metadata))
                conn.commit()
        except Exception as e:
            print(f"[{self.agent_id}] Error logging to thermal memory: {e}")

    def run(self):
        """Main daemon loop."""
        print(f"[{self.agent_id}] Task Executor starting on {self.node_name}")
        print(f"[{self.agent_id}] Poll interval: {POLL_INTERVAL}s")
        print(f"[{self.agent_id}] Gateway: {GATEWAY_URL}")
        print(f"[{self.agent_id}] Supported task types: research, implementation, review, content")

        while self.running:
            try:
                tasks = self.get_assigned_tasks()

                if tasks:
                    print(f"[{self.agent_id}] Found {len(tasks)} assigned task(s)")

                for task in tasks:
                    task_id = task['task_id']
                    
                    # Start execution
                    self.start_task(task_id)
                    
                    # Execute
                    success, result = self.execute_task(task)
                    
                    # Update status
                    if success:
                        self.complete_task(task_id, result)
                    else:
                        self.fail_task(task_id, result)
                    
                    # Log to thermal memory
                    self.log_to_thermal_memory(task, success, result)

                time.sleep(POLL_INTERVAL)

            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"[{self.agent_id}] Error in main loop: {e}")
                time.sleep(POLL_INTERVAL)

        print(f"[{self.agent_id}] Task Executor stopped")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 jr_task_executor.py <agent_id> <node_name>")
        print("Example: python3 jr_task_executor.py jr-redfin-gecko redfin")
        sys.exit(1)

    agent_id = sys.argv[1]
    node_name = sys.argv[2]

    executor = JrTaskExecutor(agent_id, node_name)
    executor.run()
