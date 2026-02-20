#!/usr/bin/env python3
"""
Jr LLM Reasoner - Gives Jrs the ability to reason using Cherokee Constitutional model.

This module replaces regex-based task parsing with actual LLM understanding.
Part of the Learning Infrastructure (Phase 2).

Methods:
- understand_instruction() - Parse JR instructions using Cherokee model
- generate_code() - Generate implementation code
- reflect_on_execution() - MAR Reflexion loop
- ask_council() - Consult specialist council

Cherokee model endpoint: http://localhost:8002/v1/chat/completions
Model name: cherokee-constitutional

For Seven Generations - Cherokee AI Federation
Created: January 17, 2026
"""

import aiohttp
import asyncio
import json
import re
from typing import Optional, Dict, List, Any

# Configuration
# Dual-model architecture: PM (small) for planning, Coder (large) for code generation
# PM Model - Ollama executive_jr for fast planning/decomposition
PM_MODEL_URL = "http://localhost:11434/api/generate"
PM_MODEL_NAME = "executive_jr"

# Coder Model - vLLM on redfin (env-configured)
import os
CODER_MODEL_URL = "http://localhost:8000/v1/chat/completions"
CODER_MODEL_NAME = os.environ.get('VLLM_MODEL', '/ganuda/models/qwen2.5-72b-instruct-awq')

# Legacy single-model config (used by existing methods)
LLM_URL = "http://localhost:8000/v1/chat/completions"
GATEWAY_URL = "http://localhost:8080"
API_KEY = os.environ.get('LLM_GATEWAY_API_KEY', 'ck-cabccc2d6037c1dce1a027cc80df7b14cdba66143e3c2d4f3bdf0fd53b6ab4a5')
DEFAULT_MODEL = os.environ.get('VLLM_MODEL', '/ganuda/models/qwen2.5-72b-instruct-awq')


class JrLLMReasoner:
    """Gives Jrs the ability to reason using local LLM (Qwen 32B)."""

    def __init__(self, model: str = None):
        self.model = model or DEFAULT_MODEL
        self.llm_url = LLM_URL
        self.gateway_url = GATEWAY_URL
        self.api_key = API_KEY

    async def _call_llm(self, prompt: str, max_tokens: int = 1500, temperature: float = 0.3) -> str:
        """Call local LLM and return response text."""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    self.llm_url,
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": max_tokens,
                        "temperature": temperature
                    },
                    timeout=aiohttp.ClientTimeout(total=120)
                ) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        raise Exception(f"LLM API error {resp.status}: {error_text}")
                    data = await resp.json()
                    return data["choices"][0]["message"]["content"]
            except aiohttp.ClientError as e:
                raise Exception(f"Failed to connect to LLM: {e}")

    def _extract_json(self, text: str) -> dict:
        """Extract JSON from LLM response, handling markdown code blocks."""
        # Try to find JSON in code blocks first
        json_match = re.search(r'```(?:json)?\s*\n?([\s\S]*?)\n?```', text)
        if json_match:
            text = json_match.group(1)

        # Try to find raw JSON object
        json_match = re.search(r'\{[\s\S]*\}', text)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass

        # Try parsing the whole text
        try:
            return json.loads(text.strip())
        except json.JSONDecodeError:
            return {"error": "Failed to parse JSON", "raw_response": text}

    async def understand_instruction(self, instruction_text: str) -> dict:
        """
        Use Cherokee model to understand a JR instruction.

        Args:
            instruction_text: The full markdown content of a JR instruction file

        Returns:
            {
                "task_id": str,
                "summary": str,  # 1-2 sentence summary
                "steps": list[str],  # Ordered implementation steps
                "files_to_create": list[str],
                "files_to_modify": list[str],
                "dependencies": list[str],
                "success_criteria": list[str],
                "language": str,  # primary language (python, typescript, sql, etc.)
                "task_type": str  # code, content, research, deployment
            }
        """
        prompt = f"""You are a Jr engineer parsing a task instruction. Extract the following from this instruction and respond in JSON format only.

Extract:
1. task_id - The task identifier (from metadata or title)
2. summary - Brief 1-2 sentence summary of what needs to be done
3. steps - Ordered list of implementation steps (be specific and actionable)
4. files_to_create - List of new files to create (full paths)
5. files_to_modify - List of existing files to modify (full paths)
6. dependencies - Prerequisites or dependencies
7. success_criteria - How to verify the task is complete
8. language - Primary programming language (python, typescript, sql, bash, etc.)
9. task_type - One of: code, content, research, deployment

Respond with ONLY valid JSON, no explanations.

INSTRUCTION:
{instruction_text[:1500]}
"""
        response = await self._call_llm(prompt, max_tokens=800)
        result = self._extract_json(response)

        # Ensure required fields exist with defaults
        defaults = {
            "task_id": "unknown",
            "summary": "",
            "steps": [],
            "files_to_create": [],
            "files_to_modify": [],
            "dependencies": [],
            "success_criteria": [],
            "language": "python",
            "task_type": "code"
        }
        for key, default in defaults.items():
            if key not in result:
                result[key] = default

        return result

    async def generate_code(self, task_description: str, context: dict) -> str:
        """
        Generate code to implement a task.

        Args:
            task_description: What needs to be implemented
            context: {
                "language": "python" | "typescript" | "sql" | "bash",
                "existing_code": str | None,  # Code to modify
                "file_path": str,
                "patterns": list[str]  # Existing patterns to follow
            }

        Returns:
            Generated code as string
        """
        language = context.get("language", "python")
        file_path = context.get("file_path", "output.py")
        existing_code = context.get("existing_code")
        patterns = context.get("patterns", [])

        existing_section = ""
        if existing_code:
            existing_section = f"""
EXISTING CODE TO MODIFY:
```{language}
{existing_code[:2000]}
```
"""

        patterns_section = ""
        if patterns:
            patterns_section = f"""
PATTERNS TO FOLLOW:
{chr(10).join(f'- {p}' for p in patterns[:5])}
"""

        prompt = f"""You are a Jr engineer implementing code. Generate clean, production-ready code.

TASK: {task_description}
LANGUAGE: {language}
FILE: {file_path}
{patterns_section}
{existing_section}

Requirements:
1. Output ONLY executable {language} code
2. Include proper error handling
3. Follow existing patterns if provided
4. Add minimal necessary comments
5. No explanations outside the code

Generate the complete code:"""

        response = await self._call_llm(prompt, max_tokens=1000, temperature=0.2)

        # Extract code from response
        code = self._extract_code(response, language)
        return code

    def _extract_code(self, response: str, language: str) -> str:
        """Extract code from LLM response, removing markdown formatting."""
        # Try to find code in markdown blocks
        code_match = re.search(rf'```(?:{language})?\s*\n([\s\S]*?)\n```', response)
        if code_match:
            return code_match.group(1).strip()

        # If no code block, return cleaned response
        # Remove common non-code prefixes
        lines = response.strip().split('\n')
        code_lines = []
        in_code = False

        for line in lines:
            # Skip explanation lines
            if line.startswith('Here') or line.startswith('This') or line.startswith('The'):
                if not in_code:
                    continue
            in_code = True
            code_lines.append(line)

        return '\n'.join(code_lines).strip()

    async def reflect_on_execution(self, task: str, result: str, error: Optional[str] = None) -> dict:
        """
        Reflect on task execution using MAR Reflexion pattern.

        Args:
            task: Description of the task attempted
            result: Output/result from execution
            error: Error message if execution failed

        Returns:
            {
                "success": bool,
                "analysis": str,
                "improvements": list[str],
                "retry_suggested": bool,
                "modified_approach": str | None
            }
        """
        prompt = f"""You are reflecting on a task execution using the MAR Reflexion pattern. Analyze what happened and suggest improvements.

TASK: {task}

RESULT: {result[:1500] if result else "No output"}

ERROR: {error if error else "None"}

Analyze and respond in JSON format:
{{
    "success": true/false,
    "analysis": "Brief analysis of what happened",
    "improvements": ["improvement 1", "improvement 2"],
    "retry_suggested": true/false,
    "modified_approach": "If retry, what should we do differently? null if not retrying"
}}

Respond with ONLY valid JSON:"""

        response = await self._call_llm(prompt, max_tokens=800)
        result = self._extract_json(response)

        # Ensure required fields
        defaults = {
            "success": False,
            "analysis": "Unable to analyze",
            "improvements": [],
            "retry_suggested": False,
            "modified_approach": None
        }
        for key, default in defaults.items():
            if key not in result:
                result[key] = default

        return result

    async def simple_completion(self, prompt: str, max_tokens: int = 2000) -> str:
        """
        Simple LLM completion without JSON extraction or special formatting.
        Used for planning prompts and code generation.

        Args:
            prompt: The prompt to send to the LLM
            max_tokens: Maximum tokens in response

        Returns:
            Raw text response from LLM
        """
        return await self._call_llm(prompt, max_tokens=max_tokens, temperature=0.3)

    async def ask_council(self, question: str, context: str) -> dict:
        """
        Ask the Specialist Council for guidance on architectural decisions.

        Uses LLM Gateway at http://localhost:8080/v1/council/vote

        Args:
            question: The question to ask the council
            context: Background context for the decision

        Returns:
            {
                "recommendation": str,
                "votes": dict[str, str],  # specialist -> vote
                "concerns": list[str],
                "consensus": bool
            }
        """
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    f"{self.gateway_url}/v1/council/vote",
                    json={
                        "question": question,
                        "context": context
                    },
                    headers={
                        "X-API-Key": self.api_key,
                        "Content-Type": "application/json"
                    },
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    if resp.status != 200:
                        # Fallback to local reasoning if council unavailable
                        return await self._local_council_fallback(question, context)
                    return await resp.json()
            except aiohttp.ClientError:
                # Fallback to local reasoning
                return await self._local_council_fallback(question, context)

    async def _local_council_fallback(self, question: str, context: str) -> dict:
        """Fallback council reasoning using Cherokee model when gateway unavailable."""
        prompt = f"""You are simulating the Cherokee AI Federation's 7-Specialist Council.

The specialists are:
- Crawdad (Security): Evaluates security implications
- Gecko (Technical): Assesses technical feasibility
- Turtle (Seven Generations): Considers long-term impact
- Eagle Eye (Monitoring): Thinks about observability
- Spider (Integration): Considers system integration
- Peace Chief (Consensus): Seeks balanced solutions
- Raven (Strategy): Evaluates strategic alignment

QUESTION: {question}

CONTEXT: {context}

Provide a council response in JSON format:
{{
    "recommendation": "The council's recommendation",
    "votes": {{
        "crawdad": "brief vote",
        "gecko": "brief vote",
        "turtle": "brief vote",
        "eagle_eye": "brief vote",
        "spider": "brief vote",
        "peace_chief": "brief vote",
        "raven": "brief vote"
    }},
    "concerns": ["any concerns raised"],
    "consensus": true/false
}}

Respond with ONLY valid JSON:"""

        response = await self._call_llm(prompt, max_tokens=1000)
        result = self._extract_json(response)

        # Ensure required fields
        defaults = {
            "recommendation": "Unable to reach council consensus",
            "votes": {},
            "concerns": [],
            "consensus": False
        }
        for key, default in defaults.items():
            if key not in result:
                result[key] = default

        return result


# Synchronous wrapper for non-async usage
class JrLLMReasonerSync:
    """Synchronous wrapper for JrLLMReasoner."""

    def __init__(self, model: str = None):
        self._async_reasoner = JrLLMReasoner(model)

    def _run(self, coro):
        """Run async coroutine synchronously."""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro)

    def understand_instruction(self, instruction_text: str) -> dict:
        return self._run(self._async_reasoner.understand_instruction(instruction_text))

    def generate_code(self, task_description: str, context: dict) -> str:
        return self._run(self._async_reasoner.generate_code(task_description, context))

    def reflect_on_execution(self, task: str, result: str, error: Optional[str] = None) -> dict:
        return self._run(self._async_reasoner.reflect_on_execution(task, result, error))

    def ask_council(self, question: str, context: str) -> dict:
        return self._run(self._async_reasoner.ask_council(question, context))

    def simple_completion(self, prompt: str, max_tokens: int = 2000) -> str:
        return self._run(self._async_reasoner.simple_completion(prompt, max_tokens))


# Convenience functions
def get_reasoner() -> JrLLMReasoner:
    """Get async reasoner instance."""
    return JrLLMReasoner()


def get_reasoner_sync() -> JrLLMReasonerSync:
    """Get synchronous reasoner instance."""
    return JrLLMReasonerSync()


# =============================================================================
# DUAL-MODEL ARCHITECTURE FUNCTIONS
# PM (small model) handles planning, Coder (large model) handles code generation
# Added: January 28, 2026
# =============================================================================

import requests

def get_pm_plan(instruction_content: str) -> dict:
    """
    Use PM model (executive_jr) to parse instructions and create execution plan.

    This small model is fast and good at structured output.
    Returns a JSON plan that the Coder model can execute step-by-step.
    """
    prompt = f"""You are a Project Manager. Parse this JR instruction and create a structured execution plan.

INSTRUCTION:
{instruction_content[:3000]}

OUTPUT FORMAT (JSON):
{{
  "title": "task title",
  "summary": "one sentence summary",
  "steps": [
    {{
      "step_number": 1,
      "action": "create_file" | "edit_file" | "run_command",
      "target": "/path/to/file.py",
      "description": "what to do",
      "code_needed": true | false
    }}
  ],
  "files_to_create": ["/path/to/new/file.py"],
  "files_to_modify": ["/path/to/existing/file.py"]
}}

Return ONLY valid JSON, no explanation."""

    try:
        response = requests.post(
            PM_MODEL_URL,
            json={"model": PM_MODEL_NAME, "prompt": prompt, "stream": False},
            timeout=60
        )

        if response.status_code != 200:
            # Fallback to Qwen if Ollama unavailable
            return _fallback_pm_plan(instruction_content)

        result = response.json()
        text = result.get("response", "")

        # Extract JSON from response
        json_match = re.search(r'\{[\s\S]*\}', text)
        if json_match:
            try:
                parsed = json.loads(json_match.group(0))
                # Validate it has required structure
                if parsed.get('steps') or parsed.get('title'):
                    return parsed
            except json.JSONDecodeError:
                pass

        # PM model didn't return valid JSON - fallback to Qwen
        print(f"[PM] executive_jr didn't return JSON, falling back to Qwen")
        return _fallback_pm_plan(instruction_content)

    except requests.exceptions.RequestException as e:
        # Fallback to Qwen if Ollama unavailable
        return _fallback_pm_plan(instruction_content)


def _fallback_pm_plan(instruction_content: str) -> dict:
    """Fallback to Qwen 32B if PM model unavailable."""
    prompt = f"""Parse this JR instruction and create a structured execution plan as JSON.

INSTRUCTION:
{instruction_content[:3000]}

Return JSON with: title, summary, steps (each with step_number, action, target, description, code_needed), files_to_create, files_to_modify.
Return ONLY valid JSON:"""

    try:
        response = requests.post(
            CODER_MODEL_URL,
            json={
                "model": CODER_MODEL_NAME,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 1500
            },
            timeout=90
        )

        if response.status_code == 200:
            text = response.json()["choices"][0]["message"]["content"]
            json_match = re.search(r'\{[\s\S]*\}', text)
            if json_match:
                try:
                    return json.loads(json_match.group(0))
                except json.JSONDecodeError:
                    pass

        return {"error": "Fallback also failed", "steps": []}

    except Exception as e:
        return {"error": str(e), "steps": []}


def get_code_for_step(step: dict, context: str) -> str:
    """
    Use Coder model (Qwen 32B) to generate code for a plan step.

    CRITICAL: Output includes '# filepath:' marker for rlm_executor to parse.
    """
    target = step.get("target", "/ganuda/lib/output.py")
    description = step.get("description", "implement the step")

    prompt = f"""Generate production-ready code for this step.

STEP: {description}
TARGET FILE: {target}
CONTEXT: {context[:1500]}

CRITICAL: Your response MUST start with a code block containing a filepath comment.

Format your response EXACTLY like this:
```python
# filepath: {target}
# Your implementation here
```

Generate the complete implementation:"""

    try:
        response = requests.post(
            CODER_MODEL_URL,
            json={
                "model": CODER_MODEL_NAME,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 4000
            },
            timeout=120
        )

        if response.status_code == 200:
            content = response.json()["choices"][0]["message"]["content"]
            return content
        else:
            return f"# Error: API returned {response.status_code}"

    except Exception as e:
        return f"# Error generating code: {e}"


def execute_with_dual_model(instruction_content: str) -> dict:
    """
    Execute task using PM + Coder dual-model approach.

    Phase 1: PM model parses instruction into structured plan
    Phase 2: Coder model generates code for each step with filepath markers

    Returns dict with plan, code_outputs, and success status.
    """
    # Phase 1: PM creates plan
    plan = get_pm_plan(instruction_content)

    if plan.get("error"):
        return {
            "success": False,
            "error": plan.get("error"),
            "plan": plan,
            "code_outputs": []
        }

    code_outputs = []

    # Phase 2: Coder generates code for each step
    for step in plan.get("steps", []):
        if step.get("code_needed", True):
            code_response = get_code_for_step(step, instruction_content[:1000])
            code_outputs.append({
                "step_number": step.get("step_number"),
                "target": step.get("target"),
                "code": code_response
            })

    return {
        "success": len(code_outputs) > 0,
        "plan": plan,
        "code_outputs": code_outputs,
        "files_to_create": plan.get("files_to_create", []),
        "files_to_modify": plan.get("files_to_modify", [])
    }


# CLI test mode
if __name__ == "__main__":
    import sys

    async def test():
        reasoner = JrLLMReasoner()

        print("=" * 60)
        print("Jr LLM Reasoner - Test Suite")
        print("=" * 60)

        # Test 1: understand_instruction
        print("\n[TEST 1] understand_instruction()")
        test_instruction = """
# JR Instruction: Add Login Button

## Metadata
```yaml
task_id: add_login_button
priority: 2
target: frontend
```

## Overview
Add a login button to the application header.

## Implementation
1. Create LoginButton component
2. Add to Header component
3. Wire up onClick to auth flow

## Files
- Create: src/components/LoginButton.tsx
- Modify: src/components/Header.tsx

## Success Criteria
- [ ] Button visible in header
- [ ] Clicking opens login modal
"""
        result = await reasoner.understand_instruction(test_instruction)
        print(f"  task_id: {result.get('task_id')}")
        print(f"  summary: {result.get('summary')[:80]}...")
        print(f"  steps: {len(result.get('steps', []))} steps")
        print(f"  files_to_create: {result.get('files_to_create')}")
        print(f"  ✓ PASS" if result.get('task_id') else "  ✗ FAIL")

        # Test 2: generate_code
        print("\n[TEST 2] generate_code()")
        code = await reasoner.generate_code(
            "Create a simple Python function that calculates factorial",
            {"language": "python", "file_path": "/ganuda/lib/math_utils.py"}
        )
        print(f"  Generated {len(code)} chars of code")
        print(f"  Preview: {code[:100]}...")
        print(f"  ✓ PASS" if "def" in code.lower() else "  ✗ FAIL")

        # Test 3: reflect_on_execution
        print("\n[TEST 3] reflect_on_execution()")
        reflection = await reasoner.reflect_on_execution(
            task="Add login button to header",
            result="Component created but throws TypeError on click",
            error="TypeError: onClick is not a function"
        )
        print(f"  success: {reflection.get('success')}")
        print(f"  analysis: {reflection.get('analysis', '')[:80]}...")
        print(f"  retry_suggested: {reflection.get('retry_suggested')}")
        print(f"  ✓ PASS" if 'success' in reflection else "  ✗ FAIL")

        # Test 4: ask_council
        print("\n[TEST 4] ask_council()")
        council = await reasoner.ask_council(
            question="Should we use JWT or session-based authentication?",
            context="Building a veteran assistance web application with sensitive PII"
        )
        print(f"  recommendation: {council.get('recommendation', '')[:80]}...")
        print(f"  consensus: {council.get('consensus')}")
        print(f"  concerns: {len(council.get('concerns', []))} concerns")
        print(f"  ✓ PASS" if 'recommendation' in council else "  ✗ FAIL")

        print("\n" + "=" * 60)
        print("All tests completed!")
        print("=" * 60)

    asyncio.run(test())
