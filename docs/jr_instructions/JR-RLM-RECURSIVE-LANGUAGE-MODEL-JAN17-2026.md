# JR Instruction: Integrate Recursive Language Models (RLM)

## Metadata
```yaml
task_id: rlm_integration
priority: 1
assigned_to: IT Triad Jr
target: /ganuda/lib/rlm_executor.py
estimated_effort: high
dependencies:
  - jr_llm_reasoner.py (COMPLETE)
  - vLLM on port 8000 (COMPLETE)
  - Qwen 32B model (COMPLETE)
phase: 4 of 6 (Recursive Task Decomposition)
references:
  - paper: https://arxiv.org/pdf/2512.24601
  - library: https://github.com/alexzhang13/rlm
  - minimal: https://github.com/alexzhang13/rlm-minimal
```

## Overview

Integrate Recursive Language Models (RLM) into the Jr executor system. RLM enables Jrs to recursively decompose complex tasks into subtasks, with the model calling itself as a subroutine. This solves context rot and enables handling of extended reasoning chains.

**Key Insight**: Instead of one-shot task execution, Jrs can now:
1. Decompose "Build authentication system" → subtasks
2. Recursively process each subtask (model calls itself)
3. Execute code in REPL sandbox
4. Condense results back up the tree

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Jr Queue Worker                       │
│  ┌─────────────────────────────────────────────────┐    │
│  │              RLM Executor                        │    │
│  │  ┌─────────────┐    ┌─────────────────────┐    │    │
│  │  │   RLM Core  │───▶│  REPL Environment   │    │    │
│  │  │  (depth=N)  │    │  (Docker sandbox)   │    │    │
│  │  └──────┬──────┘    └─────────────────────┘    │    │
│  │         │                                       │    │
│  │         ▼ recursive sub-call                   │    │
│  │  ┌─────────────┐                               │    │
│  │  │  Sub_RLM    │──▶ vLLM (port 8000)          │    │
│  │  │  (depth=1)  │    Qwen 32B                   │    │
│  │  └─────────────┘                               │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

## Prerequisites

1. **vLLM running on port 8000** - OpenAI-compatible API (DONE)
2. **Docker installed** - For sandboxed REPL execution
3. **Python 3.12** - Required by RLM library

## Installation

### Step 1: Install RLM Library

```bash
cd /ganuda/lib
source /home/dereadi/cherokee_venv/bin/activate

# Install via pip (RLM uses OpenAI client interface)
pip install rlm

# Or from source for latest:
git clone https://github.com/alexzhang13/rlm.git /ganuda/lib/rlm_source
cd /ganuda/lib/rlm_source
pip install -e .
```

### Step 2: Verify Docker for Sandboxing

```bash
# Ensure Docker is running for sandboxed execution
sudo systemctl status docker
docker pull python:3.11-slim
```

## Module: `/ganuda/lib/rlm_executor.py`

```python
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

from typing import Dict, List, Optional, Any
import json

# RLM library imports
try:
    from rlm import RLM
    RLM_AVAILABLE = True
except ImportError:
    RLM_AVAILABLE = False
    print("[WARN] RLM library not installed. Run: pip install rlm")


# Configuration for local vLLM
VLLM_BASE_URL = "http://localhost:8000/v1"
MODEL_NAME = "/ganuda/models/qwen2.5-coder-32b-awq"
MAX_RECURSION_DEPTH = 3  # Prevent runaway recursion


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
        sandbox: str = "docker"  # "local", "docker", "modal"
    ):
        if not RLM_AVAILABLE:
            raise ImportError("RLM library required. Install with: pip install rlm")

        self.model = model
        self.base_url = base_url
        self.max_depth = max_depth
        self.sandbox = sandbox

        # Initialize RLM with vLLM backend
        self.rlm = RLM(
            backend="openai",
            backend_kwargs={
                "model_name": model,
                "base_url": base_url,
                "api_key": "not-needed"  # vLLM doesn't require key
            },
            environment=sandbox,
            environment_kwargs={
                "image": "python:3.11-slim"  # For Docker sandbox
            },
            verbose=True
        )

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

        try:
            # RLM handles recursive decomposition automatically
            response = self.rlm.completion(prompt)

            return {
                "success": True,
                "result": response.response,
                "subtasks_completed": response.metadata.get("recursion_count", 1),
                "artifacts": self._extract_artifacts(response),
                "execution_tree": response.metadata.get("execution_tree", {})
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "subtasks_completed": 0,
                "artifacts": [],
                "execution_tree": {}
            }

    def _build_execution_prompt(self, task: Dict) -> str:
        """Build the RLM execution prompt for a task."""
        return f"""You are a Jr engineer executing a task. You can use Python code to accomplish the task.
You have access to `sub_rlm(prompt)` to recursively decompose complex subtasks.

TASK: {task.get('title', 'Unknown task')}

INSTRUCTIONS:
{task.get('instructions', '')}

FILES TO CREATE: {json.dumps(task.get('files_to_create', []))}
FILES TO MODIFY: {json.dumps(task.get('files_to_modify', []))}

APPROACH:
1. If the task is complex, break it into subtasks using sub_rlm()
2. Execute each subtask, collecting results
3. Combine results into final output
4. Create/modify files as needed using standard Python file I/O

Execute the task now. Output only the final result summary.
"""

    def _extract_artifacts(self, response) -> List[Dict]:
        """Extract file artifacts from RLM execution response."""
        artifacts = []
        # Parse response for created/modified files
        if hasattr(response, 'files_created'):
            for f in response.files_created:
                artifacts.append({
                    "type": "file_created",
                    "path": f.path,
                    "content_hash": f.hash
                })
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
        prompt = f"""Decompose this task into 3-7 specific subtasks.
Return ONLY a JSON array of subtask strings.

TASK: {task_description}

Example output: ["Subtask 1", "Subtask 2", "Subtask 3"]
"""
        response = self.rlm.completion(prompt)

        try:
            return json.loads(response.response)
        except json.JSONDecodeError:
            # Fallback: split by newlines
            return [
                line.strip().lstrip("0123456789.-) ")
                for line in response.response.split("\n")
                if line.strip()
            ]


# Convenience functions
def get_rlm_executor() -> RLMExecutor:
    """Get RLM executor instance with default config."""
    return RLMExecutor()


def execute_with_rlm(task: Dict) -> Dict:
    """Execute a task using RLM (convenience wrapper)."""
    executor = RLMExecutor()
    return executor.execute_task(task)


# CLI test mode
if __name__ == "__main__":
    print("=" * 60)
    print("RLM Executor - Test Suite")
    print("=" * 60)

    if not RLM_AVAILABLE:
        print("ERROR: RLM library not installed")
        print("Run: pip install rlm")
        exit(1)

    executor = RLMExecutor(sandbox="local")  # Use local for testing

    # Test 1: Task decomposition
    print("\n[TEST 1] decompose_only()")
    subtasks = executor.decompose_only(
        "Create a REST API endpoint that validates user input and stores it in PostgreSQL"
    )
    print(f"  Subtasks: {len(subtasks)}")
    for i, st in enumerate(subtasks, 1):
        print(f"    {i}. {st}")

    # Test 2: Simple task execution
    print("\n[TEST 2] execute_task()")
    result = executor.execute_task({
        "task_id": "test_001",
        "title": "Create a Python function that calculates factorial",
        "instructions": "Write a factorial function with proper error handling",
        "files_to_create": ["/tmp/test_factorial.py"],
        "files_to_modify": []
    })
    print(f"  Success: {result['success']}")
    print(f"  Subtasks completed: {result['subtasks_completed']}")
    print(f"  Result preview: {result.get('result', '')[:200]}...")

    print("\n" + "=" * 60)
    print("Tests completed!")
    print("=" * 60)
```

## Integration with Task Executor

Update `/ganuda/jr_executor/task_executor.py` to use RLM for complex tasks:

```python
# Add to imports
try:
    from rlm_executor import RLMExecutor, RLM_AVAILABLE
except ImportError:
    RLM_AVAILABLE = False

class TaskExecutor:
    def __init__(self):
        # ... existing init ...
        self.rlm_executor = RLMExecutor() if RLM_AVAILABLE else None

    def process_queue_task(self, task: Dict) -> Dict:
        # Use RLM for complex multi-file tasks
        if self._is_complex_task(task) and self.rlm_executor:
            return self._execute_with_rlm(task)
        else:
            return self._execute_standard(task)

    def _is_complex_task(self, task: Dict) -> bool:
        """Determine if task warrants RLM recursive execution."""
        files_count = len(task.get('files_to_create', [])) + len(task.get('files_to_modify', []))
        instructions_length = len(task.get('instructions', ''))

        # Use RLM if: many files OR long instructions OR explicit flag
        return (
            files_count > 3 or
            instructions_length > 2000 or
            task.get('use_rlm', False)
        )

    def _execute_with_rlm(self, task: Dict) -> Dict:
        """Execute task using RLM recursive decomposition."""
        print(f"[RLM] Executing complex task with recursive decomposition")
        return self.rlm_executor.execute_task(task)
```

## Systemd Service Update

Update `/ganuda/scripts/systemd/jr-queue-worker.service`:

```ini
[Unit]
Description=Cherokee AI Jr Queue Worker - Phase 4 RLM-enabled
After=network.target vllm.service docker.service
Wants=vllm.service docker.service

[Service]
Type=simple
User=dereadi
Group=dereadi
WorkingDirectory=/ganuda/jr_executor
Environment=PATH=/home/dereadi/cherokee_venv/bin:/usr/bin:/bin
Environment=PYTHONPATH=/ganuda/lib
# Docker socket access for sandboxed RLM execution
SupplementaryGroups=docker
ExecStart=/home/dereadi/cherokee_venv/bin/python jr_queue_worker.py "it_triad_jr"
Restart=always
RestartSec=30
StandardOutput=journal
StandardError=journal
SyslogIdentifier=jr-queue-worker

[Install]
WantedBy=multi-user.target
```

## Testing

### Manual Test

```bash
cd /ganuda/lib
source /home/dereadi/cherokee_venv/bin/activate
python rlm_executor.py
```

### Integration Test

```bash
# Queue a complex task
PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -U claude -d zammad_production -c "
INSERT INTO jr_work_queue (title, instruction_file, priority, status, assigned_jr, use_rlm)
VALUES (
    'RLM Test: Build User Registration Flow',
    '/ganuda/docs/jr_instructions/JR-RLM-RECURSIVE-LANGUAGE-MODEL-JAN17-2026.md',
    1,
    'pending',
    'it_triad_jr',
    true
) RETURNING id, title;
"

# Restart worker and observe
sudo systemctl restart jr-queue-worker
journalctl -u jr-queue-worker -f
```

## Success Criteria

- [ ] RLM library installed in cherokee_venv
- [ ] `/ganuda/lib/rlm_executor.py` created and tested
- [ ] Docker sandbox working for safe code execution
- [ ] Task executor detects complex tasks and routes to RLM
- [ ] Recursive decomposition visible in logs
- [ ] `use_rlm` column added to jr_work_queue table
- [ ] Subtask results properly condensed

## Security Considerations

1. **Docker Sandbox**: All RLM code execution happens in isolated containers
2. **Recursion Limit**: MAX_RECURSION_DEPTH=3 prevents runaway loops
3. **No Network in Sandbox**: Container runs without network access
4. **Read-Only Mounts**: Only specific paths mounted read-only

## Performance Notes

- RLM adds ~2-5 seconds overhead per recursion level
- Complex tasks with 3+ subtasks benefit most
- Simple single-file tasks should skip RLM

---

*Cherokee AI Federation - For the Seven Generations*
*"Jrs that decompose, reason, and execute recursively."*
