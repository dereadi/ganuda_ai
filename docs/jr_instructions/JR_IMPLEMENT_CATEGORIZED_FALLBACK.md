# Jr Build Instructions: Categorized Fallback Pattern

**Task ID:** JR-CAT-FALLBACK-001
**Priority:** P2 (High - Reliability Enhancement)
**Date:** 2025-12-26
**Author:** TPM
**Source:** Assembled (John Wang) - Production pattern for model routing

---

## Problem Statement

Current Gateway has simple fallback: if primary model fails, try backup model. But all task types get the same fallback behavior.

**Better approach:** Route fallback by task category to the optimal model for that task type.

---

## Solution: Categorized Fallback

```
Request → [Classify Task Type] → [Route to Optimal Model Chain]

Task Type     | Primary         | Fallback 1    | Fallback 2
--------------|-----------------|---------------|-------------
Summarization | Flash/Haiku     | Nemotron-9B   | -
Reasoning     | O1/Thinking     | Opus          | Nemotron-9B
Code Gen      | Sonnet          | Qwen-Coder    | Nemotron-9B
Conversation  | Nemotron-9B     | Haiku         | -
Research      | Sonnet          | Nemotron-9B   | -
SQL/Data      | Qwen-14B        | Nemotron-9B   | -
```

### Key Principle
- **Classify once, route intelligently**
- **Task-specific model chains** - not just generic fallback
- **Fast/cheap for simple tasks** - don't waste Opus on summarization
- **Strong models for hard tasks** - reasoning needs thinking models

---

## Implementation

### Step 1: Add Task Classifier

In `/ganuda/services/llm_gateway/gateway.py`:

```python
from enum import Enum
from typing import List, Tuple
import re

class TaskType(Enum):
    SUMMARIZATION = "summarization"
    REASONING = "reasoning"
    CODE_GENERATION = "code_generation"
    CONVERSATION = "conversation"
    RESEARCH = "research"
    SQL_DATA = "sql_data"
    CREATIVE = "creative"
    UNKNOWN = "unknown"


def classify_task(prompt: str, messages: list = None) -> TaskType:
    """
    Classify the task type from prompt content.
    Returns the most likely task type for optimal model routing.
    """
    prompt_lower = prompt.lower()

    # Summarization indicators
    if any(kw in prompt_lower for kw in [
        "summarize", "summary", "tldr", "brief", "condense",
        "key points", "main ideas", "in short"
    ]):
        return TaskType.SUMMARIZATION

    # Reasoning indicators
    if any(kw in prompt_lower for kw in [
        "why", "explain why", "reason", "analyze", "logic",
        "step by step", "think through", "deduce", "prove"
    ]):
        return TaskType.REASONING

    # Code generation indicators
    if any(kw in prompt_lower for kw in [
        "write code", "implement", "function", "class", "def ",
        "code", "programming", "script", "algorithm", "debug"
    ]):
        return TaskType.CODE_GENERATION

    # SQL/Data indicators
    if any(kw in prompt_lower for kw in [
        "sql", "query", "database", "select", "insert", "table",
        "postgresql", "mysql", "join", "aggregate"
    ]):
        return TaskType.SQL_DATA

    # Research indicators
    if any(kw in prompt_lower for kw in [
        "research", "find", "search", "investigate", "compare",
        "what is", "how does", "information about"
    ]):
        return TaskType.RESEARCH

    # Creative indicators
    if any(kw in prompt_lower for kw in [
        "write a story", "poem", "creative", "imagine", "fiction",
        "compose", "invent", "brainstorm"
    ]):
        return TaskType.CREATIVE

    # Conversation - short messages, greetings, simple questions
    if len(prompt) < 100 or any(kw in prompt_lower for kw in [
        "hello", "hi ", "hey", "thanks", "thank you", "how are you"
    ]):
        return TaskType.CONVERSATION

    return TaskType.UNKNOWN
```

### Step 2: Define Model Chains

```python
# Model routing configuration
# Each chain is ordered: primary → fallback1 → fallback2
MODEL_CHAINS = {
    TaskType.SUMMARIZATION: [
        "NVIDIA/Nemotron-Nano-9B-v2",  # Fast, good at summarization
    ],
    TaskType.REASONING: [
        "NVIDIA/Nemotron-Nano-9B-v2",  # Our primary
        # In future: add o1, claude-thinking
    ],
    TaskType.CODE_GENERATION: [
        "NVIDIA/Nemotron-Nano-9B-v2",
        # In future: add Qwen-Coder, DeepSeek-Coder
    ],
    TaskType.CONVERSATION: [
        "NVIDIA/Nemotron-Nano-9B-v2",  # Fast for chat
    ],
    TaskType.RESEARCH: [
        "NVIDIA/Nemotron-Nano-9B-v2",
    ],
    TaskType.SQL_DATA: [
        "NVIDIA/Nemotron-Nano-9B-v2",
        # In future: add sqlcoder
    ],
    TaskType.CREATIVE: [
        "NVIDIA/Nemotron-Nano-9B-v2",
    ],
    TaskType.UNKNOWN: [
        "NVIDIA/Nemotron-Nano-9B-v2",  # Default chain
    ],
}

# Model endpoints
MODEL_ENDPOINTS = {
    "NVIDIA/Nemotron-Nano-9B-v2": "http://localhost:8000/v1/chat/completions",
    # Add more as we deploy them
}
```

### Step 3: Create Categorized Fallback Router

```python
import aiohttp
import asyncio
from typing import Optional

class CategorizedFallbackRouter:
    """
    Routes requests to optimal model chain based on task type.
    Implements smart fallback with task-specific chains.
    """

    def __init__(self):
        self.model_chains = MODEL_CHAINS
        self.endpoints = MODEL_ENDPOINTS
        self.timeout = aiohttp.ClientTimeout(total=60)

    async def route(self, prompt: str, messages: list, request_params: dict) -> dict:
        """
        Route request through categorized model chain.
        """
        # 1. Classify the task
        task_type = classify_task(prompt, messages)

        # 2. Get model chain for this task type
        chain = self.model_chains.get(task_type, self.model_chains[TaskType.UNKNOWN])

        # 3. Try each model in chain until success
        last_error = None
        for model in chain:
            try:
                result = await self._call_model(model, messages, request_params)
                result["task_type"] = task_type.value
                result["model_used"] = model
                result["fallback_position"] = chain.index(model)
                return result
            except Exception as e:
                last_error = e
                print(f"[FALLBACK] {model} failed: {e}, trying next...")
                continue

        # All models failed
        return {
            "error": f"All models in chain failed. Last error: {last_error}",
            "task_type": task_type.value,
            "chain_tried": chain
        }

    async def _call_model(self, model: str, messages: list, params: dict) -> dict:
        """Call a specific model endpoint."""
        endpoint = self.endpoints.get(model)
        if not endpoint:
            raise ValueError(f"No endpoint configured for {model}")

        payload = {
            "model": model,
            "messages": messages,
            **params
        }

        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            async with session.post(endpoint, json=payload) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    raise Exception(f"Model returned {resp.status}: {text}")
                return await resp.json()

    def get_chain_for_type(self, task_type: TaskType) -> List[str]:
        """Get the model chain for a task type."""
        return self.model_chains.get(task_type, self.model_chains[TaskType.UNKNOWN])
```

### Step 4: Integrate Into Gateway

Modify the chat completions handler:

```python
# Initialize router
fallback_router = CategorizedFallbackRouter()

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatRequest, api_key: str = Depends(verify_api_key)):
    """Handle chat completions with categorized fallback."""

    prompt = request.messages[-1].content if request.messages else ""
    messages = [{"role": m.role, "content": m.content} for m in request.messages]

    params = {
        "temperature": request.temperature,
        "max_tokens": request.max_tokens,
        "top_p": request.top_p,
    }

    # Route through categorized fallback
    result = await fallback_router.route(prompt, messages, params)

    # Log task classification for learning
    log_task_classification(
        task_type=result.get("task_type"),
        model_used=result.get("model_used"),
        fallback_position=result.get("fallback_position", 0)
    )

    return result
```

### Step 5: Add Classification Learning

Track classification accuracy to improve over time:

```python
def log_task_classification(task_type: str, model_used: str, fallback_position: int):
    """Log task classification for learning."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO task_classification_log (
                task_type, model_used, fallback_position, timestamp
            ) VALUES (%s, %s, %s, NOW())
        """, (task_type, model_used, fallback_position))

        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[CLASSIFY] Logging error: {e}")
```

---

## Schema Addition

```sql
CREATE TABLE IF NOT EXISTS task_classification_log (
    id SERIAL PRIMARY KEY,
    task_type VARCHAR(32),
    model_used VARCHAR(64),
    fallback_position INTEGER DEFAULT 0,
    timestamp TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_task_class_type ON task_classification_log(task_type);
CREATE INDEX idx_task_class_model ON task_classification_log(model_used);
CREATE INDEX idx_task_class_time ON task_classification_log(timestamp);
```

---

## Validation

```bash
# Test summarization routing
curl -X POST http://192.168.132.223:8080/v1/chat/completions \
  -H "Authorization: Bearer YOUR_KEY" \
  -d '{"messages": [{"role": "user", "content": "Summarize the main points of this article..."}]}'

# Check response includes task_type
# Response should show: "task_type": "summarization"

# Test code generation routing
curl -X POST http://192.168.132.223:8080/v1/chat/completions \
  -H "Authorization: Bearer YOUR_KEY" \
  -d '{"messages": [{"role": "user", "content": "Write a Python function to sort a list"}]}'

# Response should show: "task_type": "code_generation"
```

---

## Future Enhancements

When more models are deployed:
1. Add Qwen-Coder for code_generation chain
2. Add o1/claude-thinking for reasoning chain
3. Add sqlcoder for sql_data chain
4. Implement dynamic chain adjustment based on classification_log

---

## Files to Modify

1. `/ganuda/services/llm_gateway/gateway.py` - Add classifier and router

## SQL to Run

1. Create `task_classification_log` table on bluefin

---

*For Seven Generations - Cherokee AI Federation*
*"The wise hunter uses different arrows for different prey"*
