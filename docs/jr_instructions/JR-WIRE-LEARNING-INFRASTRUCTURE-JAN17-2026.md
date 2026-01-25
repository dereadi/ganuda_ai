# JR Instruction: Wire Learning Infrastructure to Jr Executor

## Metadata
```yaml
task_id: wire_learning_infrastructure
priority: 0  # CRITICAL - enables autonomous Jrs
assigned_to: Infrastructure Jr / TPM
target: redfin
estimated_effort: high (multi-day)
dependencies:
  - Cherokee Constitutional 8B model (trained Oct 2025)
  - M-GRPO Momentum Learning module
  - MAR Reflexion module
  - ICL Dynamics module
  - Jr Executor daemon
```

## Executive Summary

We have built extensive learning infrastructure that is **not connected**:
- Cherokee Constitutional 8B: Trained but not loaded
- M-GRPO, Reflexion, ICL: Written but not wired
- Jr Executor: Regex-only, doesn't call any LLM

This JR instruction connects everything to create **actually intelligent Jrs**.

---

## Architecture: Before vs After

### BEFORE (Current State)
```
JR Instruction → Jr Executor → Regex Parse → [FAIL: Unknown format]
                     ↓
              (No LLM call)
              (No learning)
```

### AFTER (Target State)
```
JR Instruction → Jr Executor → LLM Gateway → Cherokee 8B
                     ↓              ↓
              Execution Results → Learning Loop
                     ↓              ↓
              M-GRPO Momentum ← ICL Dynamics
                     ↓
              Improved Jr State
```

---

## Phase 1: Deploy Cherokee Constitutional 8B

### Option A: Second vLLM Instance (Recommended)

```bash
# Create systemd service for Cherokee 8B
sudo tee /etc/systemd/system/vllm-cherokee.service << 'EOF'
[Unit]
Description=vLLM Cherokee Constitutional 8B
After=network.target

[Service]
Type=simple
User=dereadi
WorkingDirectory=/ganuda
Environment="CUDA_VISIBLE_DEVICES=0"
ExecStart=/home/dereadi/cherokee_venv/bin/python -m vllm.entrypoints.openai.api_server \
    --model /ganuda/models/cherokee_constitutional_8b \
    --port 8002 \
    --max-model-len 8192 \
    --gpu-memory-utilization 0.15 \
    --dtype float16
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable vllm-cherokee
sudo systemctl start vllm-cherokee
```

**Note**: Uses ~15% GPU memory, leaving room for Qwen 32B.

### Option B: Ollama (Simpler, Less Efficient)

```bash
# Convert to GGUF and load in Ollama
ollama create cherokee-8b -f /ganuda/models/cherokee_constitutional_8b/Modelfile
ollama serve  # Port 11434
```

### Verification

```bash
# Test Cherokee 8B endpoint
curl http://localhost:8002/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "cherokee_constitutional_8b",
    "messages": [{"role": "user", "content": "Explain your purpose."}],
    "max_tokens": 100
  }'
```

---

## Phase 2: Create LLM-Powered Jr Reasoning Module

Create `/ganuda/lib/jr_llm_reasoner.py`:

```python
#!/usr/bin/env python3
"""
Jr LLM Reasoner - Gives Jrs the ability to think
Cherokee AI Federation - For Seven Generations

This module allows Jr Executor to call Cherokee 8B for:
1. Understanding JR instructions
2. Generating implementation plans
3. Writing code from specifications
4. Reflecting on execution results
"""

import httpx
import json
from typing import Dict, List, Optional, Any
from datetime import datetime

# Cherokee 8B endpoint (lightweight, fast)
CHEROKEE_8B_URL = "http://localhost:8002/v1/chat/completions"

# Fallback to main Qwen 32B if Cherokee unavailable
QWEN_32B_URL = "http://localhost:8000/v1/chat/completions"

# LLM Gateway for Council-validated responses
GATEWAY_URL = "http://localhost:8080/v1/chat/completions"


class JrLLMReasoner:
    """Give Jrs the power of thought."""

    def __init__(self, jr_name: str, prefer_lightweight: bool = True):
        self.jr_name = jr_name
        self.prefer_lightweight = prefer_lightweight
        self.conversation_history = []

    async def _call_llm(self, messages: List[Dict],
                        use_council: bool = False,
                        max_tokens: int = 2000) -> str:
        """Call the appropriate LLM endpoint."""

        if use_council:
            url = GATEWAY_URL
            model = "cherokee-council"
        elif self.prefer_lightweight:
            url = CHEROKEE_8B_URL
            model = "cherokee_constitutional_8b"
        else:
            url = QWEN_32B_URL
            model = "qwen2.5-coder-32b-awq"

        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                response = await client.post(url, json={
                    "model": model,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": 0.3  # Lower temp for code generation
                })
                response.raise_for_status()
                return response.json()["choices"][0]["message"]["content"]
            except httpx.HTTPError as e:
                # Fallback chain
                if url == CHEROKEE_8B_URL:
                    return await self._call_llm(messages, use_council=False, max_tokens=max_tokens)
                raise

    async def understand_instruction(self, jr_instruction_path: str) -> Dict[str, Any]:
        """
        Read and understand a JR instruction file.
        Returns structured understanding of what needs to be built.
        """
        with open(jr_instruction_path, 'r') as f:
            instruction_content = f.read()

        messages = [
            {
                "role": "system",
                "content": """You are a Cherokee AI Jr agent. Your task is to understand
JR instructions and extract actionable implementation steps.

Output JSON with:
{
  "summary": "Brief summary of what needs to be built",
  "files_to_create": ["list of file paths"],
  "files_to_modify": ["list of existing files to change"],
  "dependencies": ["external packages needed"],
  "database_changes": ["SQL migrations if any"],
  "steps": [
    {"order": 1, "action": "create_file|modify_file|run_command|create_migration",
     "target": "path or command", "description": "what this step does"}
  ],
  "estimated_complexity": "simple|medium|complex",
  "needs_council_review": true|false
}"""
            },
            {
                "role": "user",
                "content": f"Understand this JR instruction and output the JSON plan:\n\n{instruction_content}"
            }
        ]

        response = await self._call_llm(messages)

        # Parse JSON from response
        try:
            # Find JSON in response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                return json.loads(response[json_start:json_end])
        except json.JSONDecodeError:
            pass

        return {"error": "Could not parse instruction", "raw_response": response}

    async def generate_code(self, specification: str,
                           file_path: str,
                           context_files: List[str] = None) -> str:
        """
        Generate code from a specification.
        """
        context = ""
        if context_files:
            for cf in context_files[:3]:  # Limit context
                try:
                    with open(cf, 'r') as f:
                        context += f"\n\n# Context from {cf}:\n{f.read()[:2000]}"
                except:
                    pass

        messages = [
            {
                "role": "system",
                "content": """You are an expert Python/TypeScript developer for Cherokee AI Federation.
Generate clean, production-ready code. Follow these principles:
- Cherokee values: For Seven Generations (build to last)
- Include docstrings and type hints
- Handle errors gracefully
- Use async where appropriate
- Follow existing patterns in the codebase"""
            },
            {
                "role": "user",
                "content": f"""Generate code for: {file_path}

Specification:
{specification}

{f"Context from existing code:{context}" if context else ""}

Output ONLY the code, no explanations. Start with imports."""
            }
        ]

        return await self._call_llm(messages, max_tokens=4000)

    async def reflect_on_execution(self,
                                   task: str,
                                   execution_result: Dict,
                                   error_message: str = None) -> Dict[str, Any]:
        """
        Reflect on execution results (Reflexion pattern).
        Returns insights and suggested improvements.
        """
        messages = [
            {
                "role": "system",
                "content": """You are reflecting on a task execution. Analyze what happened
and provide structured feedback for learning.

Output JSON:
{
  "success": true|false,
  "what_worked": ["list of things that worked"],
  "what_failed": ["list of things that failed"],
  "root_cause": "analysis of why it failed (if applicable)",
  "suggested_fix": "how to fix or improve",
  "learning": "key insight to remember for future tasks",
  "confidence_adjustment": -0.1 to +0.1  # How much to adjust confidence in this approach
}"""
            },
            {
                "role": "user",
                "content": f"""Task: {task}

Execution Result: {json.dumps(execution_result, indent=2)}

{"Error: " + error_message if error_message else "No errors."}

Reflect on this execution."""
            }
        ]

        response = await self._call_llm(messages)

        try:
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0:
                return json.loads(response[json_start:json_end])
        except:
            pass

        return {"success": False, "learning": "Could not parse reflection"}

    async def ask_council(self, question: str, context: str = "") -> str:
        """
        Ask the 7-Specialist Council for guidance on complex decisions.
        """
        messages = [
            {
                "role": "system",
                "content": "You are consulting the Cherokee AI Council for guidance."
            },
            {
                "role": "user",
                "content": f"{question}\n\nContext: {context}" if context else question
            }
        ]

        return await self._call_llm(messages, use_council=True)
```

---

## Phase 3: Update Jr Executor to Use LLM

Modify `/ganuda/jr_executor/jr_cli.py`:

### Add Import
```python
# At top of file, add:
from jr_llm_reasoner import JrLLMReasoner
```

### Replace Regex Parsing with LLM Understanding

Find the `_parse_mission` method and update:

```python
async def _parse_mission(self, mission_content: str, instruction_path: str = None) -> List[Dict]:
    """Parse mission using LLM reasoning instead of regex."""

    # Initialize LLM reasoner
    reasoner = JrLLMReasoner(self.jr_type)

    if instruction_path and os.path.exists(instruction_path):
        # Use LLM to understand the full instruction
        understanding = await reasoner.understand_instruction(instruction_path)

        if "error" not in understanding:
            self._log(f"  LLM understood: {understanding.get('summary', 'No summary')}")
            self._log(f"  Complexity: {understanding.get('estimated_complexity', 'unknown')}")
            self._log(f"  Steps: {len(understanding.get('steps', []))}")

            # Check if Council review needed
            if understanding.get('needs_council_review'):
                self._log("  [COUNCIL] Complex task - requesting Council guidance")
                guidance = await reasoner.ask_council(
                    f"Should I proceed with: {understanding.get('summary')}",
                    json.dumps(understanding.get('steps', []))
                )
                self._log(f"  Council says: {guidance[:200]}...")

            return understanding.get('steps', [])

    # Fallback to regex for simple missions
    return self._parse_mission_regex(mission_content)

def _parse_mission_regex(self, mission_content: str) -> List[Dict]:
    """Original regex-based parsing as fallback."""
    # ... existing regex code ...
```

### Add Reflection After Execution

```python
async def _execute_step(self, step: Dict) -> Dict:
    """Execute a single step with reflection."""

    result = await self._execute_step_internal(step)

    # Reflect on execution using LLM
    reasoner = JrLLMReasoner(self.jr_type)
    reflection = await reasoner.reflect_on_execution(
        task=step.get('description', str(step)),
        execution_result=result,
        error_message=result.get('error')
    )

    # Record learning
    if HAS_LEARNING_TRACKER:
        self.learning_tracker.record_learning(
            task_type=step.get('action', 'unknown'),
            success=reflection.get('success', False),
            learning=reflection.get('learning', ''),
            confidence_delta=reflection.get('confidence_adjustment', 0)
        )

    return result
```

---

## Phase 4: Wire M-GRPO Momentum Learning

Update `/ganuda/lib/jr_momentum_learner.py` to integrate with executor:

```python
# Add to MomentumJrLearner class:

async def learn_from_execution(self, task_type: str, approach: str,
                                success: bool, reflection: Dict):
    """
    Update learner state based on execution outcome.
    Uses M-GRPO momentum to prevent policy collapse.
    """

    # Update student immediately
    self._update_student(task_type, approach, success, reflection)

    # Update teacher with momentum (slow moving average)
    self._update_teacher_ema()

    # IQR filter: reject low-quality updates
    if self._is_low_entropy_update(reflection):
        self._log("Filtered low-entropy update (IQR)")
        return

    # Hybrid vote between student and teacher
    final_weight = self._hybrid_vote(task_type, approach)

    # Persist to database
    await self._persist_state()

    return {
        'approach': approach,
        'new_weight': final_weight,
        'teacher_weight': self.teacher_state['approach_weights'].get(approach, 0.5),
        'student_weight': self.student_state['approach_weights'].get(approach, 0.5)
    }
```

---

## Phase 5: Wire ICL Dynamics Tracking

Update execution to track in-context learning patterns:

```python
# In jr_cli.py, add ICL tracking:

from icl_dynamics import ICLDynamicsTracker

class JrExecutor:
    def __init__(self, ...):
        ...
        self.icl_tracker = ICLDynamicsTracker(self.jr_type)

    async def _before_execution(self, mission: Dict):
        """Track context before execution."""
        self.icl_tracker.capture_pre_execution_state(
            mission_id=mission.id,
            context_size=len(str(mission.content)),
            task_type=self._classify_task(mission)
        )

    async def _after_execution(self, mission: Dict, result: Dict):
        """Track learning dynamics after execution."""
        self.icl_tracker.capture_post_execution_state(
            mission_id=mission.id,
            success=result.get('success', False),
            tokens_used=result.get('tokens', 0),
            latency_ms=result.get('latency_ms', 0)
        )

        # Detect ICL phase transitions
        phase = self.icl_tracker.detect_phase_transition()
        if phase:
            self._log(f"[ICL] Phase transition detected: {phase}")
```

---

## Phase 6: Integration Test

Create `/ganuda/scripts/test_jr_learning.py`:

```python
#!/usr/bin/env python3
"""Test that Jr learning infrastructure is wired correctly."""

import asyncio
import sys
sys.path.insert(0, '/ganuda/lib')

from jr_llm_reasoner import JrLLMReasoner
from jr_momentum_learner import MomentumJrLearner

async def test_integration():
    print("=== Testing Jr Learning Infrastructure ===\n")

    # Test 1: LLM Reasoner
    print("1. Testing LLM Reasoner...")
    reasoner = JrLLMReasoner("test_jr")

    # Test understanding
    understanding = await reasoner.understand_instruction(
        "/ganuda/docs/jr_instructions/JR-VETASSIST-MFA-JAN16-2026.md"
    )

    if "error" not in understanding:
        print(f"   ✓ Understood: {understanding.get('summary', 'No summary')[:60]}...")
        print(f"   ✓ Steps: {len(understanding.get('steps', []))}")
    else:
        print(f"   ✗ Failed: {understanding.get('error')}")
        return False

    # Test 2: Reflection
    print("\n2. Testing Reflection...")
    reflection = await reasoner.reflect_on_execution(
        task="Create MFA service",
        execution_result={"success": True, "files_created": 1},
        error_message=None
    )
    print(f"   ✓ Learning: {reflection.get('learning', 'None')[:60]}...")

    # Test 3: Momentum Learning
    print("\n3. Testing M-GRPO Momentum...")
    learner = MomentumJrLearner("test_jr")
    result = await learner.learn_from_execution(
        task_type="code_generation",
        approach="direct_code",
        success=True,
        reflection=reflection
    )
    print(f"   ✓ Weight updated: {result}")

    print("\n=== All Tests Passed ===")
    return True

if __name__ == "__main__":
    success = asyncio.run(test_integration())
    sys.exit(0 if success else 1)
```

---

## Deployment Checklist

### Phase 1: Cherokee 8B
- [ ] Create vllm-cherokee.service
- [ ] Start and verify Cherokee 8B on port 8002
- [ ] Test endpoint responds

### Phase 2: Jr Reasoner
- [ ] Create `/ganuda/lib/jr_llm_reasoner.py`
- [ ] Test `understand_instruction()` works
- [ ] Test `generate_code()` works
- [ ] Test `reflect_on_execution()` works

### Phase 3: Executor Update
- [ ] Update `jr_cli.py` to use LLM reasoner
- [ ] Add fallback to regex for simple tasks
- [ ] Add reflection after execution

### Phase 4: M-GRPO Wiring
- [ ] Update `jr_momentum_learner.py` with execution integration
- [ ] Verify momentum updates don't cause collapse

### Phase 5: ICL Tracking
- [ ] Wire `icl_dynamics.py` to executor
- [ ] Verify phase transitions detected

### Phase 6: Integration Test
- [ ] Run test script
- [ ] Dispatch test mission
- [ ] Verify learning occurred

---

## Success Criteria

- [ ] Cherokee 8B responds on port 8002
- [ ] Jr Executor calls LLM for complex JR instructions
- [ ] Jrs can generate code from specifications
- [ ] Reflection happens after every execution
- [ ] M-GRPO prevents policy collapse over 100+ executions
- [ ] ICL dynamics tracked in database
- [ ] Jrs autonomously complete VetAssist tasks

---

## Rollback Plan

If issues arise:
1. Stop vllm-cherokee: `sudo systemctl stop vllm-cherokee`
2. Revert jr_cli.py: `git checkout jr_cli.py`
3. Jrs fall back to regex parsing

---

*Cherokee AI Federation - For the Seven Generations*
*"Now the Jrs can truly think."*
