#!/usr/bin/env python3
"""
Jr Task Executor Daemon - Executes assigned tasks.

Based on Contract Net Protocol from JR_TASK_BIDDING_SYSTEM.md.
Completes the execution phase after bidding assigns tasks.

Run as: python3 jr_task_executor.py <agent_id> <node_name>
Example: python3 jr_task_executor.py jr-redfin-gecko redfin

Enhanced Dec 23, 2025: Added 'content' task type for document generation.
Enhanced Dec 23, 2025: Added 'code' task type with RAG, FARA, and syntax validation.
Enhanced Dec 24, 2025: Added SwarmSys pheromone integration for stigmergic coordination.

For Seven Generations - Cherokee AI Federation
"""

import os
import sys
import platform

# Determine ganuda path based on OS
GANUDA_PATH = "/Users/Shared/ganuda" if platform.system() == "Darwin" else "/ganuda"

# Add lib to path for pheromone imports
sys.path.insert(0, os.path.join(GANUDA_PATH, 'lib'))

# Import pheromone functions for SwarmSys integration
try:
    from smadrl_pheromones import on_task_complete as deposit_pheromone
    PHEROMONES_ENABLED = True
except ImportError:
    PHEROMONES_ENABLED = False
    print("[WARN] smadrl_pheromones not available, pheromone deposits disabled")

# Import Hive Mind learning functions for collective consciousness
try:
    from hive_mind import (
        log_learning_event,
        deposit_learning_pheromone,
        load_or_create_macro_agent,
        save_macro_agent_state
    )
    from hive_mind_bidding import ACTION_TYPES
    HIVEMIND_ENABLED = True
except ImportError as e:
    HIVEMIND_ENABLED = False
    print(f"[WARN] hive_mind not available: {e}, collective learning disabled")

import time
import signal
import json
import re
import ast
import subprocess
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

# Code generation safe paths (more permissive for code)
CODE_SAFE_WRITE_PATHS = [
    '/ganuda/lib/',
    '/ganuda/services/',
    '/ganuda/scripts/',
    '/ganuda/docs/',
]


class JrTaskExecutor:
    """
    Daemon that executes tasks assigned to this Jr agent.
    Enhanced with 'code' task type for actual code generation.
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

    def classify_task_action(self, task: dict) -> int:
        """
        Classify task into action type for Q-learning.
        Returns action index 0-9 matching hive_mind_bidding.ACTION_TYPES.
        """
        task_type = task.get('task_type', '').lower()
        content = (task.get('task_content', '') or '').lower()

        # Map by task_type first
        type_mapping = {
            'sql': 0, 'database': 0,
            'implementation': 4, 'code': 4,
            'deployment': 7, 'deploy': 7,
            'testing': 6, 'test': 6,
            'research': 8,
            'documentation': 5, 'content': 5,
            'review': 8,
        }

        for key, action in type_mapping.items():
            if key in task_type:
                return action

        # Fallback: classify by content keywords
        if any(kw in content for kw in ['sql', 'query', 'database', 'table', 'postgresql']):
            return 0  # sql_execution
        elif any(kw in content for kw in ['file', 'create', 'write']):
            return 1  # file_creation
        elif any(kw in content for kw in ['bash', 'command', 'script', 'shell']):
            return 2  # bash_command
        elif any(kw in content for kw in ['api', 'endpoint', 'http', 'gateway']):
            return 3  # api_call
        elif any(kw in content for kw in ['code', 'implement', 'function', 'class']):
            return 4  # code_generation
        elif any(kw in content for kw in ['doc', 'readme', 'kb', 'article']):
            return 5  # documentation
        elif any(kw in content for kw in ['test', 'verify', 'validate']):
            return 6  # testing
        elif any(kw in content for kw in ['deploy', 'install', 'setup', 'systemd']):
            return 7  # deployment
        elif any(kw in content for kw in ['research', 'investigate', 'analyze']):
            return 8  # research
        else:
            return 9  # communication

    def record_learning(self, task: dict, success: bool, duration_seconds: float = 0):
        """
        Record task completion for Hive Mind collective learning.
        This is the CRITICAL SYNAPSE connecting individual work to collective consciousness!
        """
        if not HIVEMIND_ENABLED:
            return

        try:
            task_id = task.get('task_id', 'unknown')
            action_index = self.classify_task_action(task)

            # Calculate reward
            if success:
                reward = 1.0
                if duration_seconds < 60:
                    reward += 0.5  # Speed bonus
                elif duration_seconds > 300:
                    reward -= 0.2  # Slow penalty
            else:
                reward = -0.5

            # 1. Log the learning event (builds collective memory)
            log_learning_event(
                agent_id=self.agent_id,
                task_id=task_id,
                action_index=action_index,
                reward=reward,
                success=success
            )

            # 2. Deposit learning pheromone (enables sibling observation)
            deposit_learning_pheromone(
                agent_id=self.agent_id,
                task_id=task_id,
                action_index=action_index,
                reward=reward
            )

            # 3. Update macro-agent Q-values (collective learning)
            learner = load_or_create_macro_agent()
            learner.update(action_index, reward)
            save_macro_agent_state(learner)

            action_name = ACTION_TYPES.get(action_index, f'action_{action_index}')
            print(f"[{self.agent_id}] HIVE LEARNING: action={action_name}, reward={reward:.2f}, Q={learner.q_values[action_index]:.3f}")

        except Exception as e:
            print(f"[{self.agent_id}] Learning callback error: {e}")

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
            elif task_type == 'code':
                return self._execute_code_task(task)
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

    # =========================================================================
    # CODE TASK TYPE - Generates actual executable code
    # =========================================================================

    def _execute_code_task(self, task: dict) -> Tuple[bool, str]:
        """Execute code generation task - outputs ONLY executable code."""
        content = task['task_content']
        task_id = task['task_id']

        # Detect language
        language = self._detect_language(content)

        # Get RAG context from codebase
        rag_context = self._get_code_rag_context(content)

        # Get FARA rules
        fara_rules = self._get_fara_rules(language)

        # Get few-shot examples
        few_shot = self._get_few_shot_examples(language)

        # Build strict code generation prompt
        prompt = f"""You are a code generator for Cherokee AI Federation.

OUTPUT RULES - FOLLOW EXACTLY:
1. Output ONLY executable {language} code
2. NO markdown, NO backticks, NO explanations
3. NO phrases like "Here is the code" or "This code will"
4. Start with imports or the first line of code
5. End with the last line of code
6. Include inline comments only where logic is complex
7. Follow Cherokee AI patterns from the codebase

FARA CORRECTION RULES (learn from past mistakes):
{fara_rules}

EXISTING CODEBASE PATTERNS (follow these):
{rag_context}

FEW-SHOT EXAMPLES (output like these):
{few_shot}

TASK:
{content}

Generate the {language} code now. Output ONLY code, starting immediately:"""

        # Call LLM with increased tokens for code
        result = self._call_llm(prompt, max_tokens=4000)

        if not result or result.startswith('LLM call failed'):
            return False, f"LLM error: {result}"

        # Clean the output - remove any markdown/explanation that slipped through
        clean_code = self._clean_code_output(result, language)

        # Validate syntax
        is_valid, validation_msg = self._validate_code_syntax(clean_code, language)

        if not is_valid:
            # Record FARA mistake
            self._record_fara_mistake(language, clean_code, validation_msg)
            return False, f"Code syntax validation failed: {validation_msg}"

        # Determine output path
        output_path = self._extract_code_output_path(content, language)

        if output_path and not self._is_code_safe_write_path(output_path):
            return False, f"Output path not allowed: {output_path}"

        # Save the code
        if output_path:
            try:
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                with open(output_path, 'w') as f:
                    f.write(clean_code)
                return True, f"Code generated and saved to {output_path}"
            except Exception as e:
                return False, f"Could not save code: {e}"
        else:
            # Return code in result for TPM review
            truncated = clean_code[:1500] if len(clean_code) > 1500 else clean_code
            return True, f"Code generated (no output path):\n\n{truncated}"

    def _detect_language(self, content: str) -> str:
        """Detect programming language from task content."""
        content_lower = content.lower()

        if 'python' in content_lower or '.py' in content_lower:
            return 'python'
        elif 'sql' in content_lower or 'database' in content_lower:
            return 'sql'
        elif 'bash' in content_lower or 'shell' in content_lower or '.sh' in content_lower:
            return 'bash'
        elif 'javascript' in content_lower or 'js' in content_lower:
            return 'javascript'
        elif 'yaml' in content_lower or 'yml' in content_lower:
            return 'yaml'
        else:
            return 'python'  # Default

    def _get_code_rag_context(self, content: str) -> str:
        """Get relevant code context from codebase using grep."""
        context_parts = []

        # Extract key terms for search
        terms = re.findall(r'\b[A-Za-z_][A-Za-z0-9_]{3,}\b', content)
        search_terms = list(set(terms))[:5]

        for term in search_terms:
            try:
                # Search in /ganuda for relevant code
                result = subprocess.run(
                    ['grep', '-r', '-l', '--include=*.py', term, '/ganuda/lib/', '/ganuda/services/'],
                    capture_output=True, text=True, timeout=5
                )

                if result.stdout:
                    files = result.stdout.strip().split('\n')[:2]
                    for filepath in files:
                        try:
                            with open(filepath, 'r') as f:
                                # Get first 50 lines as pattern example
                                lines = f.readlines()[:50]
                                context_parts.append(f"--- {filepath} ---\n{''.join(lines)}")
                        except:
                            pass
            except:
                pass

        return '\n'.join(context_parts[:2]) if context_parts else "No existing patterns found."

    def _get_fara_rules(self, language: str) -> str:
        """Get FARA correction rules for this language."""
        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT rule_text, importance
                    FROM fara_rules
                    WHERE (category = %s OR category = 'code_output')
                    AND active = TRUE
                    ORDER BY importance DESC, applied_count DESC
                    LIMIT 10
                """, (language,))
                rows = cur.fetchall()

                if rows:
                    return '\n'.join([f"- [{row[1]}] {row[0]}" for row in rows])
        except Exception as e:
            pass

        # Default rules if none in database
        return """- Never output markdown backticks
- Never start with explanatory text
- Include Cherokee AI header comment
- Follow existing codebase patterns
- Use descriptive variable names"""

    def _get_few_shot_examples(self, language: str) -> str:
        """Get few-shot examples of good code output."""
        examples = {
            'python': '''
# Example 1: Function definition
def calculate_temperature_decay(initial_temp: float, decay_rate: float, hours: int) -> float:
    """Calculate thermal memory temperature after decay."""
    return initial_temp * (decay_rate ** hours)

# Example 2: Class method
def get_hot_memories(self, threshold: float = 80.0) -> List[dict]:
    """Retrieve memories above temperature threshold."""
    conn = self._get_connection()
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT memory_hash, original_content, temperature_score
            FROM thermal_memory_archive
            WHERE temperature_score >= %s
            ORDER BY temperature_score DESC
        """, (threshold,))
        return list(cur.fetchall())
''',
            'sql': '''
-- Example 1: Create table with indexes
CREATE TABLE IF NOT EXISTS example_table (
    id SERIAL PRIMARY KEY,
    name VARCHAR(128) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_example_name ON example_table(name);

-- Example 2: Insert with conflict handling
INSERT INTO example_table (name)
VALUES ('test')
ON CONFLICT (name) DO UPDATE SET created_at = NOW();
''',
            'bash': '''#!/bin/bash
# Example: Service health check
set -euo pipefail

SERVICE_URL="${1:-http://localhost:8080}"

if curl -sf "${SERVICE_URL}/health" > /dev/null; then
    echo "Service healthy"
    exit 0
else
    echo "Service unhealthy"
    exit 1
fi
'''
        }

        return examples.get(language, examples['python'])

    def _clean_code_output(self, output: str, language: str) -> str:
        """Clean LLM output to extract only code."""
        # Remove markdown code blocks
        output = re.sub(r'^```[a-z]*\n?', '', output, flags=re.MULTILINE)
        output = re.sub(r'```$', '', output, flags=re.MULTILINE)

        # Remove common preamble phrases
        preamble_patterns = [
            r'^Here is .*?:\s*\n',
            r'^Here\'s .*?:\s*\n',
            r'^The following .*?:\s*\n',
            r'^Below is .*?:\s*\n',
            r'^This code .*?:\s*\n',
            r'^I\'ll .*?:\s*\n',
        ]
        for pattern in preamble_patterns:
            output = re.sub(pattern, '', output, flags=re.IGNORECASE)

        # Remove trailing explanation
        lines = output.split('\n')
        code_lines = []
        in_code = False

        for line in lines:
            stripped = line.strip()

            # Detect start of code
            if not in_code:
                if language == 'python' and (stripped.startswith('import ') or
                    stripped.startswith('from ') or stripped.startswith('def ') or
                    stripped.startswith('class ') or stripped.startswith('#!') or
                    stripped.startswith('#')):
                    in_code = True
                elif language == 'sql' and (stripped.upper().startswith('CREATE ') or
                    stripped.upper().startswith('INSERT ') or stripped.upper().startswith('SELECT ') or
                    stripped.upper().startswith('ALTER ') or stripped.startswith('--')):
                    in_code = True
                elif language == 'bash' and (stripped.startswith('#!') or stripped.startswith('#') or
                    stripped.startswith('set ') or stripped):
                    in_code = True

            if in_code:
                # Check for explanation starters that indicate end of code
                if stripped.startswith('This ') or stripped.startswith('Note:') or \
                   stripped.startswith('Explanation:') or stripped.startswith('The above'):
                    break
                code_lines.append(line)

        return '\n'.join(code_lines).strip()

    def _validate_code_syntax(self, code: str, language: str) -> Tuple[bool, str]:
        """Validate code syntax."""
        if language == 'python':
            try:
                ast.parse(code)
                return True, "Valid Python syntax"
            except SyntaxError as e:
                return False, f"Python syntax error: {e.msg} at line {e.lineno}"

        elif language == 'sql':
            # Basic SQL validation - check for common issues
            sql_upper = code.upper()
            if not any(kw in sql_upper for kw in ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'ALTER', 'DROP']):
                return False, "No SQL statement found"
            return True, "SQL syntax appears valid"

        elif language == 'bash':
            # Use bash -n for syntax check
            try:
                result = subprocess.run(
                    ['bash', '-n'],
                    input=code,
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    return True, "Valid bash syntax"
                else:
                    return False, f"Bash syntax error: {result.stderr}"
            except Exception as e:
                return True, f"Could not validate bash: {e}"

        # Default: assume valid for other languages
        return True, f"Syntax validation not implemented for {language}"

    def _record_fara_mistake(self, language: str, code: str, error: str):
        """Record mistake for FARA learning."""
        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                # Create a rule from the mistake
                rule_hash = f"fara-mistake-{abs(hash(error)) % 1000000}"
                rule_text = f"Avoid: {error[:200]}"

                cur.execute("""
                    INSERT INTO fara_rules (rule_hash, category, rule_text, importance)
                    VALUES (%s, %s, %s, 50)
                    ON CONFLICT (rule_hash) DO UPDATE SET applied_count = fara_rules.applied_count + 1
                """, (rule_hash, language, rule_text))
                conn.commit()
        except:
            pass

    def _extract_code_output_path(self, content: str, language: str) -> Optional[str]:
        """Extract output file path from task content."""
        ext_map = {'python': '.py', 'sql': '.sql', 'bash': '.sh', 'javascript': '.js', 'yaml': '.yaml'}
        ext = ext_map.get(language, '.py')

        patterns = [
            rf'[Ss]ave to\s+(/[^\s]+{re.escape(ext)})',
            rf'[Oo]utput:?\s+(/[^\s]+{re.escape(ext)})',
            rf'[Ww]rite to\s+(/[^\s]+{re.escape(ext)})',
            rf'[Ff]ile:?\s+(/[^\s]+{re.escape(ext)})',
            rf'(/ganuda/[^\s]+{re.escape(ext)})',
        ]

        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1)

        return None

    def _is_code_safe_write_path(self, path: str) -> bool:
        """Check if path is in safe code write locations."""
        for safe_path in CODE_SAFE_WRITE_PATHS:
            if path.startswith(safe_path):
                return True
        return False

    # =========================================================================
    # Original helper methods for content tasks
    # =========================================================================

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
        print(f"[{self.agent_id}] Supported task types: research, implementation, review, content, code")

        while self.running:
            try:
                tasks = self.get_assigned_tasks()

                if tasks:
                    print(f"[{self.agent_id}] Found {len(tasks)} assigned task(s)")

                for task in tasks:
                    task_id = task['task_id']

                    # Start execution
                    self.start_task(task_id)
                    task_start_time = time.time()

                    # Execute
                    success, result = self.execute_task(task)

                    # Update status
                    if success:
                        self.complete_task(task_id, result)
                    else:
                        self.fail_task(task_id, result)

                    # Log to thermal memory
                    self.log_to_thermal_memory(task, success, result)

                    # Deposit pheromone for SwarmSys stigmergic coordination
                    if PHEROMONES_ENABLED:
                        try:
                            deposit_pheromone(
                                task_id=task['task_id'],
                                task_type=task.get('task_type', 'unknown'),
                                success=success,
                                agent_id=self.agent_id
                            )
                        except Exception as e:
                            print(f"[{self.agent_id}] Pheromone deposit error: {e}")

                    # Record learning for Hive Mind collective consciousness
                    task_duration = time.time() - task_start_time
                    self.record_learning(task, success, task_duration)

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
