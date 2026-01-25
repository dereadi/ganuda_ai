import os
from enum import Enum
import anthropic
import requests

class ModelTier(Enum):
    """Enum representing different tiers of models."""
    HAIKU = "haiku"
    LOCAL = "local"
    OPUS = "opus"

SIMPLE_KEYWORDS = ["format", "summarize", "list", "simple", "quick", "template"]
COMPLEX_KEYWORDS = ["architect", "security", "refactor", "multi-file", "critical"]

def classify_task_complexity(task: dict) -> ModelTier:
    """
    Classify the complexity of a task based on its title and instructions.

    Args:
        task (dict): A dictionary containing the task details with 'title' and 'instructions'.

    Returns:
        ModelTier: The tier of the model that should handle the task.
    """
    text = (task.get("title", "") + " " + task.get("instructions", "")).lower()
    if any(kw in text for kw in COMPLEX_KEYWORDS):
        return ModelTier.OPUS
    if sum(1 for kw in SIMPLE_KEYWORDS if kw in text) >= 2:
        return ModelTier.HAIKU
    return ModelTier.LOCAL

def call_haiku(prompt: str) -> str:
    """
    Call the Haiku model with a given prompt.

    Args:
        prompt (str): The input prompt for the model.

    Returns:
        str: The response from the Haiku model.
    """
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    response = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text

def call_local(prompt: str) -> str:
    """
    Call the local model with a given prompt.

    Args:
        prompt (str): The input prompt for the model.

    Returns:
        str: The response from the local model.
    """
    response = requests.post(
        "http://localhost:8000/v1/chat/completions",
        json={
            "model": "/ganuda/models/qwen2.5-coder-32b-awq",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 4096
        },
        timeout=120
    )
    return response.json()["choices"][0]["message"]["content"]

def route_and_call(task: dict, prompt: str) -> tuple:
    """
    Route the task to the appropriate model and call it.

    Args:
        task (dict): A dictionary containing the task details with 'title' and 'instructions'.
        prompt (str): The input prompt for the model.

    Returns:
        tuple: A tuple containing the response from the model and the model tier used.
    """
    tier = classify_task_complexity(task)
    if tier == ModelTier.HAIKU:
        return call_haiku(prompt), tier
    return call_local(prompt), tier