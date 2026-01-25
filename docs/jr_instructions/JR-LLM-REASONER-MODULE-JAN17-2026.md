# JR Instruction: Jr LLM Reasoner Module

## Metadata
```yaml
task_id: jr_llm_reasoner
priority: 1
assigned_to: IT Triad Jr
target: /ganuda/lib/jr_llm_reasoner.py
estimated_effort: medium
dependencies:
  - Cherokee Constitutional model on port 8002 (COMPLETE)
phase: 2 of 6 (Wire Learning Infrastructure)
```

## Overview

Create the `jr_llm_reasoner.py` module that gives Jrs the ability to reason using the Cherokee Constitutional model. This replaces the current regex-based task parsing with actual LLM understanding.

## Prerequisites (Already Done)

- Cherokee Constitutional model running on `http://localhost:8002`
- Model name: `cherokee-constitutional`
- OpenAI-compatible API via vLLM

## Module Location

```
/ganuda/lib/jr_llm_reasoner.py
```

## Required Methods

### 1. `understand_instruction(instruction_text: str) -> dict`

Parse a JR instruction markdown file and extract structured task information.

```python
async def understand_instruction(instruction_text: str) -> dict:
    """
    Use Cherokee model to understand a JR instruction.

    Returns:
        {
            "task_id": str,
            "summary": str,  # 1-2 sentence summary
            "steps": list[str],  # Ordered implementation steps
            "files_to_create": list[str],
            "files_to_modify": list[str],
            "dependencies": list[str],
            "success_criteria": list[str]
        }
    """
```

**Prompt Template:**
```
You are a Jr engineer parsing a task instruction. Extract the following from this instruction:

1. Task ID
2. Brief summary (1-2 sentences)
3. Implementation steps (ordered list)
4. Files to create
5. Files to modify
6. Dependencies
7. Success criteria

Respond in JSON format only.

INSTRUCTION:
{instruction_text}
```

### 2. `generate_code(task_description: str, context: dict) -> str`

Generate implementation code for a specific task.

```python
async def generate_code(task_description: str, context: dict) -> str:
    """
    Generate code to implement a task.

    Args:
        task_description: What needs to be implemented
        context: {
            "language": "python" | "typescript" | "sql",
            "existing_code": str | None,  # Code to modify
            "file_path": str,
            "patterns": list[str]  # Existing patterns to follow
        }

    Returns:
        Generated code as string
    """
```

**Prompt Template:**
```
You are a Jr engineer implementing code. Follow these patterns from the codebase.

TASK: {task_description}
LANGUAGE: {language}
FILE: {file_path}

EXISTING PATTERNS:
{patterns}

{existing_code_section}

Generate clean, production-ready code. Include error handling.
Respond with code only, no explanations.
```

### 3. `reflect_on_execution(task: str, result: str, error: str | None) -> dict`

MAR Reflexion loop - analyze execution results and suggest improvements.

```python
async def reflect_on_execution(task: str, result: str, error: str | None) -> dict:
    """
    Reflect on task execution using MAR Reflexion pattern.

    Returns:
        {
            "success": bool,
            "analysis": str,
            "improvements": list[str],
            "retry_suggested": bool,
            "modified_approach": str | None
        }
    """
```

**Prompt Template:**
```
You are reflecting on a task execution. Analyze what happened and suggest improvements.

TASK: {task}
RESULT: {result}
ERROR: {error or "None"}

Provide:
1. Was this successful? (true/false)
2. Analysis of what happened
3. Suggested improvements
4. Should we retry? (true/false)
5. If retry, what should we do differently?

Respond in JSON format.
```

### 4. `ask_council(question: str, context: str) -> dict`

Consult the 7-Specialist Council for architectural decisions.

```python
async def ask_council(question: str, context: str) -> dict:
    """
    Ask the Specialist Council for guidance.

    Uses LLM Gateway at http://localhost:8080/v1/council/vote

    Returns:
        {
            "recommendation": str,
            "votes": dict[str, str],  # specialist -> vote
            "concerns": list[str],
            "consensus": bool
        }
    """
```

**Implementation:**
```python
async def ask_council(question: str, context: str) -> dict:
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "http://localhost:8080/v1/council/vote",
            json={"question": question, "context": context},
            headers={"X-API-Key": API_KEY}
        ) as resp:
            return await resp.json()
```

## Class Structure

```python
# /ganuda/lib/jr_llm_reasoner.py

import aiohttp
import json
from typing import Optional

CHEROKEE_URL = "http://localhost:8002/v1/chat/completions"
GATEWAY_URL = "http://localhost:8080"
API_KEY = "ck-cabccc2d6037c1dce1a027cc80df7b14cdba66143e3c2d4f3bdf0fd53b6ab4a5"

class JrLLMReasoner:
    """Gives Jrs the ability to reason using Cherokee Constitutional model."""

    def __init__(self, model: str = "cherokee-constitutional"):
        self.model = model
        self.cherokee_url = CHEROKEE_URL
        self.gateway_url = GATEWAY_URL

    async def _call_cherokee(self, prompt: str, max_tokens: int = 1000) -> str:
        """Call Cherokee model and return response text."""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.cherokee_url,
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": max_tokens,
                    "temperature": 0.3  # Lower for more deterministic
                }
            ) as resp:
                data = await resp.json()
                return data["choices"][0]["message"]["content"]

    async def understand_instruction(self, instruction_text: str) -> dict:
        # Implementation here
        pass

    async def generate_code(self, task_description: str, context: dict) -> str:
        # Implementation here
        pass

    async def reflect_on_execution(self, task: str, result: str, error: Optional[str]) -> dict:
        # Implementation here
        pass

    async def ask_council(self, question: str, context: str) -> dict:
        # Implementation here
        pass


# Convenience function for non-async usage
def get_reasoner() -> JrLLMReasoner:
    return JrLLMReasoner()
```

## Testing

Create `/ganuda/lib/test_jr_llm_reasoner.py`:

```python
import asyncio
from jr_llm_reasoner import JrLLMReasoner

async def test_reasoner():
    reasoner = JrLLMReasoner()

    # Test 1: Understand instruction
    test_instruction = """
    # JR Instruction: Add Login Button

    ## Task
    Add a login button to the header.

    ## Files
    - Modify: src/components/Header.tsx

    ## Success Criteria
    - [ ] Button visible in header
    - [ ] Clicking opens login modal
    """

    result = await reasoner.understand_instruction(test_instruction)
    print("understand_instruction:", result)
    assert "steps" in result

    # Test 2: Generate code
    code = await reasoner.generate_code(
        "Add a login button component",
        {"language": "typescript", "file_path": "src/components/LoginButton.tsx"}
    )
    print("generate_code:", code[:200])
    assert "function" in code.lower() or "const" in code.lower()

    # Test 3: Reflect on execution
    reflection = await reasoner.reflect_on_execution(
        task="Add login button",
        result="Button added but styling is off",
        error=None
    )
    print("reflect_on_execution:", reflection)
    assert "success" in reflection

    print("All tests passed!")

if __name__ == "__main__":
    asyncio.run(test_reasoner())
```

## Integration Points

After this module is complete, Phase 3 will update:

1. `/ganuda/jr_executor/jr_task_executor.py` - Import and use `JrLLMReasoner`
2. `/ganuda/jr_executor/task_executor.py` - Replace regex parsing with `understand_instruction()`

## Success Criteria

- [ ] Module created at `/ganuda/lib/jr_llm_reasoner.py`
- [ ] All 4 methods implemented
- [ ] Tests pass in `/ganuda/lib/test_jr_llm_reasoner.py`
- [ ] Cherokee model called successfully
- [ ] JSON responses parsed correctly
- [ ] Error handling for API failures

## Environment

```
CHEROKEE_URL=http://localhost:8002/v1/chat/completions
GATEWAY_URL=http://localhost:8080
```

---

*Cherokee AI Federation - For the Seven Generations*
*"Jrs that can think, learn, and ask for help."*
