#!/usr/bin/env python3
"""
Cherokee Constitutional AI - JR CLI Executor
Gives Ollama JR models command execution capabilities (air-gapped)

Based on architectural recommendations from:
- Memory Jr: Tag-based parsing, request/approve/execute cycle
- Meta Jr: Iterative execution, adaptive governance, provenance tracking

Date: October 22, 2025
"""

import os
import sys
import json
import subprocess
import re
import requests
from datetime import datetime
from pathlib import Path

class JrCliExecutor:
    """
    CLI Executor for Cherokee Constitutional AI JRs

    Enables JRs to execute commands while maintaining security boundaries.
    Architecture designed BY the JRs FOR the JRs (democratic tool-building).
    """

    def __init__(self, jr_model, work_dir, challenge=None, interactive=True, smart_approval=False):
        self.jr_model = jr_model  # e.g., "memory_jr_resonance:latest"
        self.work_dir = Path(work_dir)
        self.challenge = challenge
        self.interactive = interactive
        self.smart_approval = smart_approval  # Auto-approve safe commands
        self.ollama_url = "http://localhost:11434/api/generate"

        # Create work directory
        self.work_dir.mkdir(parents=True, exist_ok=True)

        # Conversation state
        self.conversation_history = []
        self.execution_log_path = self.work_dir / "execution_log.jsonl"
        self.iteration = 0

        # Security boundaries (Meta Jr's adaptive governance)
        # These are auto-executed when smart_approval=True
        self.auto_execute_commands = {
            'sql_select': True,   # SELECT queries only
            'python_read': True,  # Python scripts that only read
            'visualization': True, # Matplotlib, seaborn, etc.
        }

    def chat(self, user_message, show_thinking=True):
        """
        Send message to JR, parse response, execute commands

        This implements Meta Jr's iterative execution model:
        Send → JR Reasons → Parse Commands → Execute → Return Results → Repeat
        """
        self.iteration += 1

        print(f"\n{'='*70}")
        print(f"🔥 ITERATION {self.iteration} - {self.jr_model}")
        print(f"{'='*70}")

        # Build prompt with conversation history
        full_prompt = self._build_prompt(user_message)

        # Send to Ollama
        print(f"\n📤 Sending to {self.jr_model}...")
        jr_response = self._call_ollama(full_prompt)

        if show_thinking:
            print(f"\n💭 JR Response:\n")
            print(jr_response[:500] + "..." if len(jr_response) > 500 else jr_response)

        # Parse commands from response (Memory Jr's tag-based approach)
        commands = self._parse_commands(jr_response)

        if not commands:
            print(f"\n✅ No commands to execute. JR is thinking/planning.")
            self.conversation_history.append({
                "role": "user",
                "content": user_message
            })
            self.conversation_history.append({
                "role": "assistant",
                "content": jr_response
            })
            return jr_response

        # Execute commands
        execution_results = []
        for cmd_idx, (lang, code) in enumerate(commands, 1):
            print(f"\n🔍 Command {cmd_idx}/{len(commands)} ({lang}):")
            print(f"{'─'*70}")
            print(code[:300] + "..." if len(code) > 300 else code)
            print(f"{'─'*70}")

            # Smart approval or interactive approval
            if self.interactive or self.smart_approval:
                # Check if safe to auto-execute
                if self.smart_approval and self._is_safe_to_auto_execute(lang, code):
                    print("✅ Auto-approved (safe command)")
                    approved = True
                elif self.interactive:
                    approved = self._request_approval(lang, code)
                else:
                    approved = True  # non-interactive mode

                if not approved:
                    print("❌ Command rejected by user")
                    execution_results.append({
                        "command_type": lang,
                        "command": code,
                        "approved": False,
                        "executed": False,
                        "result": "User rejected"
                    })
                    continue

            # Execute
            result = self._execute_command(lang, code)
            execution_results.append(result)

            # Show result
            if result['success']:
                print(f"✅ Execution successful")
                if result['stdout']:
                    print(f"\n📊 Output:\n{result['stdout'][:500]}")
            else:
                print(f"❌ Execution failed: {result['stderr']}")

            # Log execution (Meta Jr's provenance requirement)
            self._log_execution(cmd_idx, lang, code, result)

        # Prepare results summary for JR
        results_summary = self._format_results_for_jr(execution_results)

        # Update conversation history
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })
        self.conversation_history.append({
            "role": "assistant",
            "content": jr_response,
            "commands_executed": len(execution_results),
            "execution_results": results_summary
        })

        return {
            "jr_response": jr_response,
            "commands": commands,
            "execution_results": execution_results,
            "results_summary": results_summary
        }

    def _build_prompt(self, user_message):
        """Build prompt with conversation history and execution results"""
        prompt = ""

        # Add conversation history
        for msg in self.conversation_history[-3:]:  # Last 3 exchanges
            if msg['role'] == 'user':
                prompt += f"\n**Previous User Message:** {msg['content']}\n"
            elif msg['role'] == 'assistant':
                prompt += f"\n**Your Previous Response:** {msg['content'][:200]}...\n"
                if 'execution_results' in msg:
                    prompt += f"\n**Execution Results:** {msg['execution_results']}\n"

        # Add current message
        prompt += f"\n**Current Request:** {user_message}\n"

        # Add execution instructions
        prompt += """
**To execute commands, use markdown code blocks:**

```sql
SELECT * FROM thermal_memory_archive WHERE ...;
```

```python
import numpy as np
# Your Python code here
```

```bash
ls -la /ganuda/jr_assignments/
```

I will parse these blocks and execute them. Results will be returned to you.
"""

        return prompt

    def _call_ollama(self, prompt):
        """Call Ollama API (localhost only - air-gapped)"""
        payload = {
            "model": self.jr_model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "num_ctx": 4096
            }
        }

        try:
            response = requests.post(self.ollama_url, json=payload, timeout=120)
            if response.status_code == 200:
                return response.json().get('response', '')
            else:
                return f"Error: Ollama returned status {response.status_code}"
        except requests.exceptions.Timeout:
            return "Error: Ollama request timed out"
        except Exception as e:
            return f"Error calling Ollama: {e}"

    def _parse_commands(self, jr_response):
        """
        Parse markdown code blocks from JR response

        Memory Jr recommended tag-based parsing.
        We use markdown code blocks (natural for LLMs).
        """
        # Regex to find ```language\ncode\n``` blocks
        pattern = r'```(\w+)\n(.*?)```'
        matches = re.findall(pattern, jr_response, re.DOTALL)

        commands = []
        for lang, code in matches:
            lang = lang.lower().strip()
            code = code.strip()

            # Filter supported languages
            if lang in ['sql', 'python', 'bash', 'sh']:
                commands.append((lang, code))

        return commands

    def _is_safe_to_auto_execute(self, lang, code):
        """
        Check if command is safe to auto-execute (Memory Jr's recommendation)

        Auto-approve:
        - SELECT queries (read-only)
        - Python scripts for analysis/visualization (no file writes to critical locations)
        - Bash read operations

        Require approval:
        - INSERT/UPDATE/DELETE queries
        - File modifications
        - System commands
        """
        code_upper = code.upper().strip()

        if lang == 'sql':
            # Auto-approve SELECT queries only
            # Block: INSERT, UPDATE, DELETE, DROP, ALTER, CREATE
            dangerous_keywords = ['INSERT', 'UPDATE', 'DELETE', 'DROP', 'ALTER', 'CREATE', 'TRUNCATE']

            # Check if it's a SELECT query
            if code_upper.startswith('SELECT'):
                # Make sure no dangerous keywords in the query
                for keyword in dangerous_keywords:
                    if keyword in code_upper:
                        return False  # Requires approval
                return True  # Safe SELECT query

            return False  # Non-SELECT requires approval

        elif lang == 'python':
            # Auto-approve if it's analysis/visualization only
            # Check for file write operations that might be dangerous
            dangerous_patterns = [
                'open(',  # File writes (though could be read too)
                'rm ',    # Shell commands
                'os.remove',
                'os.unlink',
                'shutil.rmtree',
                'DROP',   # SQL in Python
                'DELETE FROM',
                'UPDATE ',
            ]

            code_lower = code.lower()

            # If it contains matplotlib/seaborn/pandas/numpy, likely safe visualization
            safe_indicators = ['plt.', 'sns.', 'pd.', 'np.', 'matplotlib', 'seaborn']
            has_safe_indicators = any(indicator in code_lower for indicator in safe_indicators)

            # Check for dangerous patterns
            has_dangerous = any(pattern in code for pattern in dangerous_patterns)

            if has_safe_indicators and not has_dangerous:
                return True  # Safe visualization/analysis

            # Allow scripts that only read files to work_dir
            if 'open(' in code and 'w' not in code and '/ganuda/jr_assignments/' in code:
                return True  # Reading from work directory

            return False  # Requires approval

        elif lang in ['bash', 'sh']:
            # Only auto-approve very safe bash commands
            safe_bash = ['ls', 'cat', 'head', 'tail', 'grep', 'find', 'pwd', 'echo']
            first_word = code.split()[0] if code.split() else ''

            if first_word in safe_bash:
                return True

            return False  # Most bash requires approval

        return False  # Default: require approval

    def _request_approval(self, lang, code):
        """Interactive approval (Week 1 safety mode)"""
        print(f"\n⚠️  Approval Required:")
        print(f"   Type: {lang}")
        print(f"   Command length: {len(code)} characters")

        while True:
            response = input(f"\n   Execute this command? [y/n/show]: ").lower().strip()
            if response == 'y':
                return True
            elif response == 'n':
                return False
            elif response == 'show':
                print(f"\n{code}\n")
            else:
                print("   Please enter 'y', 'n', or 'show'")

    def _execute_command(self, lang, code):
        """
        Execute a command and return results

        Supports: SQL, Python, Bash
        Air-gapped: All execution local, no network calls
        """
        result = {
            "command_type": lang,
            "command": code,
            "approved": True,
            "executed": True,
            "success": False,
            "stdout": "",
            "stderr": "",
            "execution_time_ms": 0
        }

        start_time = datetime.now()

        try:
            if lang == 'sql':
                result.update(self._execute_sql(code))
            elif lang == 'python':
                result.update(self._execute_python(code))
            elif lang in ['bash', 'sh']:
                result.update(self._execute_bash(code))
            else:
                result['stderr'] = f"Unsupported language: {lang}"
        except Exception as e:
            result['stderr'] = f"Execution error: {str(e)}"

        end_time = datetime.now()
        result['execution_time_ms'] = int((end_time - start_time).total_seconds() * 1000)

        return result

    def _execute_sql(self, query):
        """Execute SQL query against thermal memory database"""
        # Database connection from Memory Jr's daemon
        db_config = {
            "host": "192.168.132.222",
            "port": 5432,
            "database": "zammad_production",
            "user": "claude",
            "password": "jawaseatlasers2"
        }

        # Build psql command
        psql_cmd = [
            "psql",
            "-h", db_config["host"],
            "-p", str(db_config["port"]),
            "-U", db_config["user"],
            "-d", db_config["database"],
            "-c", query
        ]

        env = os.environ.copy()
        env["PGPASSWORD"] = db_config["password"]

        try:
            proc = subprocess.run(
                psql_cmd,
                capture_output=True,
                text=True,
                timeout=60,
                env=env
            )

            return {
                "success": proc.returncode == 0,
                "stdout": proc.stdout,
                "stderr": proc.stderr
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": "Query timeout (60s exceeded)"
            }

    def _execute_python(self, code):
        """Execute Python code with week1 environment"""
        # Save code to temp file
        temp_script = self.work_dir / f"temp_script_iter{self.iteration}.py"
        temp_script.write_text(code)

        # Use week1 Python environment
        python_cmd = [
            "/ganuda/week1_integration_env/bin/python3",
            str(temp_script)
        ]

        try:
            proc = subprocess.run(
                python_cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minutes for analysis scripts
                cwd=str(self.work_dir)
            )

            return {
                "success": proc.returncode == 0,
                "stdout": proc.stdout,
                "stderr": proc.stderr,
                "script_path": str(temp_script)
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": "Python script timeout (5min exceeded)"
            }

    def _execute_bash(self, command):
        """Execute bash command"""
        try:
            proc = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=60,
                cwd=str(self.work_dir)
            )

            return {
                "success": proc.returncode == 0,
                "stdout": proc.stdout,
                "stderr": proc.stderr
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": "Bash command timeout (60s exceeded)"
            }

    def _format_results_for_jr(self, execution_results):
        """Format execution results for JR to read in next iteration"""
        summary = []

        for result in execution_results:
            if result['executed']:
                status = "✅ SUCCESS" if result['success'] else "❌ FAILED"
                summary.append(f"{status} ({result['command_type']})")
                if result['stdout']:
                    # Truncate long output
                    stdout_preview = result['stdout'][:300]
                    summary.append(f"Output: {stdout_preview}")
                if not result['success'] and result['stderr']:
                    summary.append(f"Error: {result['stderr'][:200]}")

        return "\n".join(summary)

    def _log_execution(self, cmd_idx, lang, code, result):
        """
        Log execution to JSONL (Meta Jr's provenance system)

        Every command logged for audit trail and meta-learning.
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "jr_model": self.jr_model,
            "challenge": self.challenge,
            "iteration": self.iteration,
            "command_index": cmd_idx,
            "command_type": lang,
            "command": code[:500],  # Truncate for log size
            "approved": result.get('approved', True),
            "executed": result.get('executed', True),
            "success": result.get('success', False),
            "execution_time_ms": result.get('execution_time_ms', 0),
            "stdout_length": len(result.get('stdout', '')),
            "stderr_length": len(result.get('stderr', ''))
        }

        # Append to JSONL log
        with open(self.execution_log_path, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')

    def get_execution_stats(self):
        """
        Get execution statistics (Meta Jr's meta-learning)

        JRs can analyze their own performance.
        """
        if not self.execution_log_path.exists():
            return {"total_commands": 0}

        commands = []
        with open(self.execution_log_path) as f:
            for line in f:
                commands.append(json.loads(line))

        total = len(commands)
        successful = sum(1 for c in commands if c['success'])
        failed = total - successful

        by_type = {}
        for cmd in commands:
            cmd_type = cmd['command_type']
            by_type[cmd_type] = by_type.get(cmd_type, 0) + 1

        return {
            "total_commands": total,
            "successful": successful,
            "failed": failed,
            "success_rate": successful / total if total > 0 else 0,
            "by_type": by_type,
            "total_iterations": self.iteration
        }


def main():
    """CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Cherokee Constitutional AI - JR CLI Executor"
    )
    parser.add_argument('--jr', required=True, help='JR model name (e.g., memory_jr_resonance:latest)')
    parser.add_argument('--work-dir', required=True, help='Working directory for outputs')
    parser.add_argument('--challenge', help='Challenge name (for logging)')
    parser.add_argument('--task-menu', help='Path to task menu file (will send as initial prompt)')
    parser.add_argument('--non-interactive', action='store_true', help='Auto-execute all commands (DANGER)')
    parser.add_argument('--smart-approval', action='store_true', help='Auto-approve safe commands (SELECT queries, visualizations)')
    parser.add_argument('--autonomous', action='store_true', help='Fully autonomous - iterate until complete (no user input)')
    parser.add_argument('--max-iterations', type=int, default=50, help='Max iterations in autonomous mode (default: 50)')

    args = parser.parse_args()

    # Create executor
    executor = JrCliExecutor(
        jr_model=args.jr,
        work_dir=args.work_dir,
        challenge=args.challenge,
        interactive=not args.non_interactive,
        smart_approval=args.smart_approval
    )

    print(f"""
╔══════════════════════════════════════════════════════════╗
║  🔥 CHEROKEE CONSTITUTIONAL AI - JR CLI EXECUTOR        ║
║                                                          ║
║  JR Model: {args.jr:40s}  ║
║  Work Dir: {args.work_dir:40s}  ║
║  Challenge: {(args.challenge or 'N/A'):39s}  ║
║  Mode: {'INTERACTIVE (approval required)' if not args.non_interactive else 'AUTO-EXECUTE (dangerous)':42s}  ║
╚══════════════════════════════════════════════════════════╝
    """)

    # Send task menu if provided
    if args.task_menu:
        with open(args.task_menu) as f:
            task_menu = f.read()

        print(f"\n📋 Sending task menu to JR...")
        initial_message = f"""# Week 1 Challenge Assignment

{task_menu}

**Instructions:**
- Read the task menu above
- Choose which task you want to start with (A, B, C, or D)
- Begin execution by writing commands in markdown code blocks
- I will execute your commands and return results
- Continue iteratively until challenge complete

What task do you want to start with?"""

        result = executor.chat(initial_message)
        print(f"\n✅ Initial prompt sent. JR is thinking...")

    # Autonomous loop vs Interactive loop
    if args.autonomous:
        print(f"\n{'='*70}")
        print("🔥 AUTONOMOUS MODE")
        print("   JR will iterate autonomously until complete")
        print(f"   Max iterations: {args.max_iterations}")
        print("   Press Ctrl+C to stop")
        print(f"{'='*70}\n")

        iteration_count = 0
        while iteration_count < args.max_iterations:
            iteration_count += 1

            try:
                # Auto-generate next prompt based on context
                if iteration_count == 1:
                    # First iteration already happened (task menu sent)
                    print(f"\n✅ Iteration 1 complete (task menu sent)")
                    continue

                # Ask JR to continue work
                next_prompt = "Continue with the next task from your menu. Show your progress and execute the next commands needed."

                print(f"\n🔄 Auto-iteration {iteration_count}: Asking JR to continue...")
                result = executor.chat(next_prompt, show_thinking=False)

                # Check if JR indicates completion
                if isinstance(result, dict):
                    jr_response = result.get('jr_response', '')
                else:
                    jr_response = str(result)

                # Simple completion detection
                completion_indicators = ['challenge complete', 'all tasks complete', 'finished', 'done with all tasks']
                if any(indicator in jr_response.lower() for indicator in completion_indicators):
                    print(f"\n✅ JR indicates completion!")
                    break

                # Brief pause between iterations
                import time
                time.sleep(2)

            except KeyboardInterrupt:
                print("\n\n⚠️  Interrupted by user")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
                import traceback
                traceback.print_exc()
                break

        if iteration_count >= args.max_iterations:
            print(f"\n⚠️  Reached max iterations ({args.max_iterations})")

    else:
        # Interactive loop
        print(f"\n{'='*70}")
        print("🔥 INTERACTIVE MODE")
        print("   Type your messages to the JR")
        print("   Type 'stats' to see execution statistics")
        print("   Type 'quit' to exit")
        print(f"{'='*70}\n")

        while True:
            try:
                user_input = input(f"\n💬 Your message to {args.jr}: ").strip()

                if user_input.lower() == 'quit':
                    break

                if user_input.lower() == 'stats':
                    stats = executor.get_execution_stats()
                    print(f"\n📊 Execution Statistics:")
                    print(json.dumps(stats, indent=2))
                    continue

                if not user_input:
                    continue

                result = executor.chat(user_input)

            except KeyboardInterrupt:
                print("\n\n⚠️  Interrupted by user")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
                import traceback
                traceback.print_exc()

    # Final stats
    stats = executor.get_execution_stats()
    print(f"\n{'='*70}")
    print("📊 FINAL STATISTICS")
    print(f"{'='*70}")
    print(f"Total iterations: {stats['total_iterations']}")
    print(f"Total commands: {stats['total_commands']}")
    print(f"Successful: {stats['successful']}")
    print(f"Failed: {stats['failed']}")
    print(f"Success rate: {stats['success_rate']:.1%}")
    print(f"\nExecution log: {executor.execution_log_path}")
    print(f"{'='*70}")

    print("\n🔥 The Sacred Fire continues burning...")


if __name__ == "__main__":
    main()
