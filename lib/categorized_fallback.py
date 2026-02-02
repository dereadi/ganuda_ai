"""
Categorized Fallback Router for Cherokee AI Federation
Implements John Wang's Assembled pattern for task-type routing
"""
from enum import Enum
from typing import List, Dict, Optional
import aiohttp
import asyncio


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


# Model routing configuration
# Each chain is ordered: primary -> fallback1 -> fallback2
# Code tasks route to Qwen2.5-Coder-32B for superior code generation
MODEL_CHAINS: Dict[TaskType, List[str]] = {
    TaskType.SUMMARIZATION: [
        "nvidia/NVIDIA-Nemotron-Nano-9B-v2",
    ],
    TaskType.REASONING: [
        "Qwen/Qwen2.5-Coder-32B-Instruct",  # Coder is strong at reasoning too
        "nvidia/NVIDIA-Nemotron-Nano-9B-v2",
    ],
    TaskType.CODE_GENERATION: [
        "Qwen/Qwen2.5-Coder-32B-Instruct",  # Primary: best coding model
        "nvidia/NVIDIA-Nemotron-Nano-9B-v2",  # Fallback
    ],
    TaskType.CONVERSATION: [
        "nvidia/NVIDIA-Nemotron-Nano-9B-v2",  # Fast for chat
    ],
    TaskType.RESEARCH: [
        "nvidia/NVIDIA-Nemotron-Nano-9B-v2",
    ],
    TaskType.SQL_DATA: [
        "Qwen/Qwen2.5-Coder-32B-Instruct",  # Good at SQL too
        "nvidia/NVIDIA-Nemotron-Nano-9B-v2",
    ],
    TaskType.CREATIVE: [
        "nvidia/NVIDIA-Nemotron-Nano-9B-v2",
    ],
    TaskType.UNKNOWN: [
        "nvidia/NVIDIA-Nemotron-Nano-9B-v2",
    ],
}

# Model endpoints - dual model setup
# Port 8000: Primary model (Qwen or Nemotron depending on systemd config)
# Port 8001: Secondary model (when dual-model is enabled)
#
# To switch to Qwen as primary, update /etc/systemd/system/vllm.service:
#   sudo systemctl stop vllm
#   sudo nano /etc/systemd/system/vllm.service  # change model path to /ganuda/models/qwen2.5-coder-32b
#   sudo systemctl daemon-reload
#   sudo systemctl start vllm
MODEL_ENDPOINTS: Dict[str, str] = {
    "nvidia/NVIDIA-Nemotron-Nano-9B-v2": "http://localhost:8000/v1/chat/completions",
    "Qwen/Qwen2.5-Coder-32B-Instruct": "http://localhost:8000/v1/chat/completions",  # Same port - will use whatever model is loaded
}


class CategorizedFallbackRouter:
    """
    Routes requests to optimal model chain based on task type.
    Implements smart fallback with task-specific chains.
    """

    def __init__(self, model_chains: Dict = None, endpoints: Dict = None):
        self.model_chains = model_chains or MODEL_CHAINS
        self.endpoints = endpoints or MODEL_ENDPOINTS
        self.timeout = aiohttp.ClientTimeout(total=60)

    async def route(self, prompt: str, messages: list, request_params: dict) -> dict:
        """
        Route request through categorized model chain.
        """
        # Classify the task
        task_type = classify_task(prompt, messages)

        # Get model chain for this task type
        chain = self.model_chains.get(task_type, self.model_chains[TaskType.UNKNOWN])

        # Try each model in chain until success
        last_error = None
        for i, model in enumerate(chain):
            try:
                result = await self._call_model(model, messages, request_params)
                # Add routing metadata
                result["task_type"] = task_type.value
                result["model_used"] = model
                result["fallback_position"] = i
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


# Singleton instance for easy use
_router_instance = None

def get_fallback_router() -> CategorizedFallbackRouter:
    """Get singleton router instance."""
    global _router_instance
    if _router_instance is None:
        _router_instance = CategorizedFallbackRouter()
    return _router_instance
