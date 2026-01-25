#!/usr/bin/env python3
"""
RLM Executor - Recursive Language Model integration for Jr task execution.

Enables Jrs to recursively decompose complex tasks into subtasks.
Uses vLLM (Qwen 32B) on port 8000 via OpenAI-compatible API.

Paper: https://arxiv.org/pdf/2512.24601
Library: https://github.com/alexzhang13/rlm

For Seven Generations - Cherokee AI Federation
Created: January 17, 2026
"""

import json
import logging
from typing import Dict, List, Optional, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# RLM library imports
try:
    from rlm import RLM
    RLM_AVAILABLE = True
    logger.info("[RLM] Library loaded successfully")
except ImportError as e:
    RLM_AVAILABLE = False
    logger.warning(f"[RLM] Library not available: {e}")


# Configuration for local vLLM
VLLM_BASE_URL = "http://localhost:8000/v1"
MODEL_NAME = "/ganuda/models/qwen2.5-coder-32b-awq"
MAX_RECURSION_DEPTH = 3  # Prevent runaway recursion

# Phase 9 Path Validation (Jan 23, 2026 - Council Vote 28d18d80e447505f)
PLACEHOLDER_PATTERNS = [
    r'/path/to/',
    r'/example/',
    r'<[^>]+>',
    r'\$\{[^}]+\}',
    r'\{\{[^}]+\}\}',
    r'/your/',
    r'/my/',
]

def validate_path(path: str) -> tuple:
    """Validate path to prevent LLM hallucination and injection."""
    import re
    if not path:
        return False, "Empty path"
    for pattern in PLACEHOLDER_PATTERNS:
        if re.search(pattern, path, re.IGNORECASE):
            return False, f"Placeholder pattern: {pattern}"
    if not path.startswith('/'):
        return False, "Not absolute"
    if '..' in path:
        return False, "Directory traversal"
    return True, ""


class RLMExecutor:
    """
    Executes Jr tasks using Recursive Language Model approach.

    Tasks are decomposed into subtasks, processed recursively,
    and results condensed back up the execution tree.
    """

    def __init__(
        self,
        model: str = MODEL_NAME,
        base_url: str = VLLM_BASE_URL,
        max_depth: int = MAX_RECURSION_DEPTH,
        sandbox: str = "local"  # "local", "docker", "modal"
    ):
        if not RLM_AVAILABLE:
            raise ImportError("RLM library required. Install with: pip install git+https://github.com/alexzhang13/rlm.git")

        self.model = model
        self.base_url = base_url
        self.max_depth = max_depth
        self.sandbox = sandbox
        self.logger = logging.getLogger(__name__)

        # Initialize RLM with vLLM backend (OpenAI-compatible)
        self.logger.info(f"[RLM] Initializing with model={model}, base_url={base_url}")

        try:
            self.rlm = RLM(
                backend="openai",
                backend_kwargs={
                    "model_name": model,
                    "base_url": base_url,
                    "api_key": "not-needed"  # vLLM doesn't require API key
                },
                environment=sandbox,
                verbose=True
            )
            self.logger.info("[RLM] Initialized successfully")
        except Exception as e:
            self.logger.error(f"[RLM] Initialization failed: {e}")
            raise

    def execute_task(self, task: Dict) -> Dict:
        """
        Execute a Jr task using RLM recursive decomposition.

        Args:
            task: {
                "task_id": str,
                "title": str,
                "instructions": str,
                "files_to_create": list,
                "files_to_modify": list
            }

        Returns:
            {
                "success": bool,
                "result": str,
                "subtasks_completed": int,
                "artifacts": list,
                "execution_tree": dict
            }
        """
        prompt = self._build_execution_prompt(task)
        self.logger.info(f"[RLM] Executing task: {task.get('title', 'unknown')}")

        try:
            # RLM handles recursive decomposition automatically
            response = self.rlm.completion(prompt)
            response_text = response.response if hasattr(response, 'response') else str(response)

            # FIXED Jan 18, 2026: Actually create files from LLM response
            artifacts = self._write_files_from_response(response_text, task)

            # Also check for any artifacts the RLM library created
            artifacts.extend(self._extract_artifacts(response))

            result = {
                "success": True,
                "result": response_text,
                "subtasks_completed": getattr(response, 'recursion_count', 1) if hasattr(response, 'recursion_count') else 1,
                "artifacts": artifacts,
                "files_created": len([a for a in artifacts if a.get('type') == 'file_created']),
                "execution_tree": {}
            }
            self.logger.info(f"[RLM] Task completed: {len(artifacts)} artifacts created")
            return result

        except Exception as e:
            self.logger.error(f"[RLM] Task execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "subtasks_completed": 0,
                "artifacts": [],
                "execution_tree": {}
            }

    def _build_execution_prompt(self, task: Dict) -> str:
        """Build the RLM execution prompt for a task.

        FIXED Jan 22, 2026: Changed to execution model - model writes Python code
        that actually creates files using open(), not markdown output.
        """
        files_create = json.dumps(task.get('files_to_create', []))
        files_modify = json.dumps(task.get('files_to_modify', []))

        return f"""You are a Jr engineer. Write Python code to CREATE files on disk.

TASK: {task.get('title', 'Unknown task')}

INSTRUCTIONS:
{task.get('instructions', '')}

FILES TO CREATE: {files_create}
FILES TO MODIFY: {files_modify}

EXECUTION MODEL - You must write Python code that CREATES FILES using open().

EXAMPLE - Creating a Python file:
```repl
import os
os.makedirs('/ganuda/example', exist_ok=True)
with open('/ganuda/example/myfile.py', 'w') as f:
    f.write('''#!/usr/bin/env python3
def hello():
    return "world"

if __name__ == "__main__":
    print(hello())
''')
print("Created: /ganuda/example/myfile.py")
```

EXAMPLE - Creating a JavaScript file:
```repl
import os
os.makedirs('/ganuda/sag/static/js', exist_ok=True)
with open('/ganuda/sag/static/js/vision.js', 'w') as f:
    f.write('''async function processFrame(framePath, cameraId) {{
    const response = await fetch("/api/optic/process", {{
        method: "POST",
        headers: {{"Content-Type": "application/json"}},
        body: JSON.stringify({{frame_path: framePath, camera_id: cameraId}})
    }});
    return await response.json();
}}
''')
print("Created: /ganuda/sag/static/js/vision.js")
```

RULES:
1. Write Python code using open() to create each file
2. Use triple single-quotes ''' for file content (avoids escaping issues)
3. Double curly braces {{{{ }}}} in f-strings for literal braces in JS/JSON
4. Always os.makedirs(dir, exist_ok=True) first
5. Print "Created: <path>" after each file
6. Only /ganuda/ or /tmp/ paths allowed
7. After ALL files created, call: FINAL_VAR({{"files_created": ["path1", "path2"], "success": True}})

Write the Python code to create the files now:
"""

    def _extract_artifacts(self, response) -> List[Dict]:
        """Extract file artifacts from RLM execution response."""
        artifacts = []
        # Parse response for created/modified files
        if hasattr(response, 'files_created'):
            for f in response.files_created:
                artifacts.append({
                    "type": "file_created",
                    "path": getattr(f, 'path', str(f)),
                    "content_hash": getattr(f, 'hash', None)
                })
        return artifacts

    def _write_files_from_response(self, response_text: str, task: Dict) -> List[Dict]:
        """
        Parse LLM response for code blocks and ACTUALLY write files to disk.

        Looks for patterns like:
        - **CREATE FILE: /path/to/file.py**
        - CREATE FILE: `/path/to/file.py`
        - Followed by code block

        Fixed Jan 18, 2026 - RLM was generating text but not creating files.
        Fixed Jan 21, 2026 - Added destructive overwrite safeguard + better patterns.
        """
        import re
        import os

        artifacts = []
        self.logger.info("[RLM] Parsing response for files to create...")

        # Security: allowed paths
        ALLOWED_PATHS = ['/ganuda/', '/tmp/']

        # Pre-process: Remove rich console box-drawing characters
        clean_text = re.sub(r'[│─┌┐└┘├┤┬┴┼╭╮╯╰]', '', response_text)

        # Strip leading/trailing whitespace from lines (but preserve code indentation)
        lines = clean_text.split('\n')
        clean_lines = []
        in_code_block = False
        for line in lines:
            if '```' in line:
                in_code_block = not in_code_block
                clean_lines.append(line.strip())
            elif in_code_block:
                # Inside code block: strip leading spaces added by box formatting
                # but preserve relative indentation
                clean_lines.append(line.rstrip())
            else:
                clean_lines.append(line.strip())
        clean_text = '\n'.join(clean_lines)

        # Pattern 1: **CREATE FILE: path** (with flexible whitespace)
        pattern1 = r'\*\*(?:CREATE|MODIFY)\s+FILE:\s*([^*\n]+?)\s*\*\*\s*\n*```(\w*)\n(.*?)```'

        # Pattern 2: CREATE FILE: `path` (backtick style)
        pattern2 = r'(?:CREATE|MODIFY)\s+FILE:\s*`([^`]+)`\s*\n*```(\w*)\n(.*?)```'

        # Pattern 3: ### /path/file.py followed by code block
        pattern3 = r'###\s*(/[\w/\.\-_]+\.\w+)\s*\n*```(\w*)\n(.*?)```'

        # Pattern 4: **path** followed by code block (simpler variant)
        pattern4 = r'\*\*(/ganuda/[^\*]+?)\*\*\s*\n*```(\w*)\n(.*?)```'

        # Pattern 5: File: `path` followed by code block (Qwen/vLLM common format)
        # Matches: File: `/ganuda/path/file.py` (optional annotations like "(new file)")
        pattern5 = r'File:\s*`([^`]+)`(?:\s*\([^)]*\))?\s*\n+```(\w*)\n(.*?)```'

        # Pattern 6: File: path (without backticks) followed by code block
        pattern6 = r'File:\s*(/ganuda/[\w/\.\-_]+\.\w+)(?:\s*\([^)]*\))?\s*\n+```(\w*)\n(.*?)```'

        # Pattern 7: # filepath: path inside code block (extract from first line)
        # This is handled separately below

        # Pattern 8: ```python\n# /ganuda/path/file.py (path as first comment)
        pattern8 = r'```(\w*)\n#\s*(/ganuda/[\w/\.\-_]+\.\w+)\s*\n(.*?)```'

        all_patterns = [
            (pattern1, "CREATE FILE markdown"),
            (pattern2, "CREATE FILE backtick"),
            (pattern3, "markdown header"),
            (pattern4, "bold path"),
            (pattern5, "File backtick"),
            (pattern6, "File plain"),
            (pattern8, "comment path"),
        ]

        found_files = set()  # Track to avoid duplicates

        for pattern, pattern_name in all_patterns:
            for match in re.finditer(pattern, clean_text, re.DOTALL | re.IGNORECASE):
                file_path = match.group(1).strip()
                language = match.group(2) or 'python'
                code = match.group(3)

                # Clean up path
                file_path = file_path.strip('`*').strip()

                # Skip if already processed
                if file_path in found_files:
                    continue

                # Security: validate path is in allowed locations
                if not any(file_path.startswith(p) for p in ALLOWED_PATHS):
                    self.logger.warning(f"[RLM] Skipping file outside allowed paths: {file_path}")
                    continue

                # Phase 9: Validate path against placeholder patterns (LLM hallucination check)
                is_valid, error = validate_path(file_path)
                if not is_valid:
                    self.logger.warning(f"[RLM] BLOCKED hallucinated path: {file_path} - {error}")
                    artifacts.append({
                        'type': 'file_blocked',
                        'path': file_path,
                        'reason': f'Path validation failed: {error}',
                        'blocked_by': 'path_validator'
                    })
                    continue

                # Skip placeholder code (too short or just a comment)
                code_stripped = code.strip()
                if len(code_stripped) < 50:
                    self.logger.warning(f"[RLM] Skipping placeholder code for: {file_path} ({len(code_stripped)} bytes)")
                    continue

                found_files.add(file_path)

                # CRITICAL SAFEGUARD: Prevent destructive overwrites
                if os.path.exists(file_path):
                    existing_size = os.path.getsize(file_path)
                    new_size = len(code)

                    # Block if existing file is >2x the size AND >1000 bytes
                    if existing_size > new_size * 2 and existing_size > 1000:
                        self.logger.error(
                            f"[RLM] BLOCKED destructive overwrite of {file_path}: "
                            f"existing={existing_size}b, new={new_size}b"
                        )
                        artifacts.append({
                            'type': 'file_blocked',
                            'path': file_path,
                            'reason': f'Would overwrite {existing_size}b with {new_size}b',
                            'existing_size': existing_size,
                            'new_size': new_size
                        })
                        continue

                    self.logger.warning(
                        f"[RLM] Overwriting {file_path} (existing={existing_size}b, new={new_size}b)"
                    )

                # Create directory if needed
                dir_path = os.path.dirname(file_path)
                if dir_path:
                    os.makedirs(dir_path, exist_ok=True)

                # Write file
                try:
                    with open(file_path, 'w') as f:
                        f.write(code)
                    artifacts.append({
                        'type': 'file_created',
                        'path': file_path,
                        'size': len(code),
                        'language': language,
                        'pattern': pattern_name
                    })
                    self.logger.info(f"[RLM] Created file: {file_path} ({len(code)} bytes) via {pattern_name}")
                except Exception as e:
                    self.logger.error(f"[RLM] Failed to write {file_path}: {e}")

        # Pattern 7: # filepath: or # file: inside code block (fallback)
        if not artifacts:
            self.logger.info("[RLM] Primary patterns failed, trying filepath comment extraction...")
            filepath_pattern = r'```(\w*)\n#\s*(?:filepath|file):\s*(/ganuda/[\w/\.\-_]+\.\w+)\s*\n(.*?)```'
            for match in re.finditer(filepath_pattern, clean_text, re.DOTALL | re.IGNORECASE):
                language = match.group(1) or 'python'
                file_path = match.group(2).strip()
                code = match.group(3)

                if file_path in found_files:
                    continue

                if not any(file_path.startswith(p) for p in ALLOWED_PATHS):
                    continue

                is_valid, error = validate_path(file_path)
                if not is_valid:
                    continue

                code_stripped = code.strip()
                if len(code_stripped) < 50:
                    continue

                found_files.add(file_path)

                # Create directory and write
                dir_path = os.path.dirname(file_path)
                if dir_path:
                    os.makedirs(dir_path, exist_ok=True)

                try:
                    with open(file_path, 'w') as f:
                        f.write(code)
                    artifacts.append({
                        'type': 'file_created',
                        'path': file_path,
                        'size': len(code),
                        'language': language,
                        'pattern': 'filepath comment'
                    })
                    self.logger.info(f"[RLM] Created file: {file_path} ({len(code)} bytes) via filepath comment")
                except Exception as e:
                    self.logger.error(f"[RLM] Failed to write {file_path}: {e}")

        if not artifacts:
            self.logger.warning(f"[RLM] No files extracted from response ({len(clean_text)} chars)")
            # Debug: log what patterns we tried to match
            self.logger.debug(f"[RLM] Response preview: {clean_text[:500]}")

        self.logger.info(f"[RLM] Created {len(artifacts)} file(s) from response")
        return artifacts

    def decompose_only(self, task_description: str) -> List[str]:
        """
        Decompose a task into subtasks without executing.
        Useful for planning and validation.

        Args:
            task_description: Natural language task description

        Returns:
            List of subtask descriptions
        """
        prompt = f"""Decompose this task into 3-7 specific, actionable subtasks.
Return ONLY a JSON array of subtask strings, nothing else.

TASK: {task_description}

Example output format: ["Subtask 1 description", "Subtask 2 description", "Subtask 3 description"]
"""
        self.logger.info(f"[RLM] Decomposing task: {task_description[:50]}...")

        try:
            response = self.rlm.completion(prompt)
            response_text = response.response if hasattr(response, 'response') else str(response)

            # Try to parse JSON
            # Handle markdown code blocks
            if '```' in response_text:
                import re
                json_match = re.search(r'```(?:json)?\s*\n?([\s\S]*?)\n?```', response_text)
                if json_match:
                    response_text = json_match.group(1)

            # Find JSON array
            import re
            array_match = re.search(r'\[[\s\S]*\]', response_text)
            if array_match:
                return json.loads(array_match.group(0))

            return json.loads(response_text)

        except json.JSONDecodeError:
            # Fallback: split by newlines and clean up
            self.logger.warning("[RLM] JSON parse failed, using line-based fallback")
            response_text = response.response if hasattr(response, 'response') else str(response)
            return [
                line.strip().lstrip("0123456789.-) ")
                for line in response_text.split("\n")
                if line.strip() and not line.strip().startswith(('[', ']', '{', '}'))
            ][:7]  # Limit to 7 subtasks

    def simple_completion(self, prompt: str) -> str:
        """
        Simple completion without recursive decomposition.
        Useful for straightforward queries.

        Args:
            prompt: The prompt to send

        Returns:
            Response text
        """
        try:
            response = self.rlm.completion(prompt)
            return response.response if hasattr(response, 'response') else str(response)
        except Exception as e:
            self.logger.error(f"[RLM] Completion failed: {e}")
            return f"Error: {e}"


# Convenience functions
def get_rlm_executor(sandbox: str = "local") -> RLMExecutor:
    """Get RLM executor instance with default config."""
    return RLMExecutor(sandbox=sandbox)


def execute_with_rlm(task: Dict) -> Dict:
    """Execute a task using RLM (convenience wrapper)."""
    executor = RLMExecutor()
    return executor.execute_task(task)


def decompose_task(description: str) -> List[str]:
    """Decompose a task description into subtasks."""
    executor = RLMExecutor()
    return executor.decompose_only(description)


# CLI test mode
if __name__ == "__main__":
    print("=" * 60)
    print("RLM Executor - Test Suite")
    print("=" * 60)

    if not RLM_AVAILABLE:
        print("ERROR: RLM library not installed")
        print("Run: pip install git+https://github.com/alexzhang13/rlm.git")
        exit(1)

    try:
        executor = RLMExecutor(sandbox="local")

        # Test 1: Task decomposition
        print("\n[TEST 1] decompose_only()")
        subtasks = executor.decompose_only(
            "Create a REST API endpoint that validates user input and stores it in PostgreSQL"
        )
        print(f"  Subtasks: {len(subtasks)}")
        for i, st in enumerate(subtasks, 1):
            print(f"    {i}. {st}")
        print(f"  {'PASS' if len(subtasks) > 0 else 'FAIL'}")

        # Test 2: Simple completion
        print("\n[TEST 2] simple_completion()")
        response = executor.simple_completion("What is 2 + 2? Reply with just the number.")
        print(f"  Response: {response[:100]}")
        print(f"  {'PASS' if response else 'FAIL'}")

        # Test 3: Task execution
        print("\n[TEST 3] execute_task()")
        result = executor.execute_task({
            "task_id": "test_001",
            "title": "Calculate factorial of 5",
            "instructions": "Write Python code to calculate factorial of 5 and return the result",
            "files_to_create": [],
            "files_to_modify": []
        })
        print(f"  Success: {result['success']}")
        print(f"  Result preview: {str(result.get('result', ''))[:150]}...")
        print(f"  {'PASS' if result['success'] else 'FAIL'}")

        print("\n" + "=" * 60)
        print("All tests completed!")
        print("=" * 60)

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
