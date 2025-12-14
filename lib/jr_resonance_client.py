#!/usr/bin/env python3
"""
Cherokee Jr Resonance Client v2.0
Updated: 2025-12-12

Based on Google/MIT Multi-Agent Scaling Study findings:
- Parallel tasks: Use multi-Jr with ThreadPoolExecutor (+72% speedup)
- Sequential tasks: Use single Jr deep_think (chain overhead only 1.7%)
- Validation: Orchestrator queries ground truth before validating Jr answers

Connects Jrs to upgraded models on redfin vLLM
"""
import requests
import json
import subprocess
from typing import List, Dict, Optional, Callable, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

VLLM_URL = "http://192.168.132.223:8000"

# Node definitions for parallel operations
FEDERATION_NODES = [
    ("bluefin", "192.168.132.222"),
    ("redfin", "192.168.132.223"),
    ("greenfin", "192.168.132.224"),
    ("sasass", "192.168.132.241"),
    ("sasass2", "192.168.132.242"),
]


@dataclass
class ValidationResult:
    """Result from orchestrator validation"""
    jr_answer: str
    ground_truth: Any
    is_valid: bool
    corrected_answer: Optional[str] = None


class JrResonance:
    """Deep resonance interface for Cherokee Jrs"""

    def __init__(self, jr_name: str):
        self.jr_name = jr_name
        self.system_prompt = self._load_jr_system_prompt(jr_name)
        # Auto-detect current model
        try:
            models = requests.get(f"{VLLM_URL}/v1/models", timeout=5).json()
            self.model = models["data"][0]["id"]
        except:
            self.model = "nvidia/NVIDIA-Nemotron-Nano-9B-v2"

    def _load_jr_system_prompt(self, jr_name: str) -> str:
        """Load Jr-specific system prompt"""
        prompts = {
            "conscience_jr": "You are Conscience Jr, the ethical guardian of Cherokee AI. You evaluate actions against tribal values and the Seven Generations principle.",
            "integration_jr": "You are Integration Jr, responsible for connecting systems and ensuring data flows correctly across the Cherokee AI federation.",
            "executive_jr": "You are Executive Jr, responsible for task execution and operational decisions within Cherokee AI.",
            "meta_jr": "You are Meta Jr, responsible for self-reflection and improvement of Cherokee AI systems.",
            "memory_jr": "You are Memory Jr, guardian of thermal memory and tribal knowledge preservation.",
            "it_triad_jr": "You are IT Triad Jr, responsible for infrastructure, monitoring, and technical operations."
        }
        return prompts.get(jr_name, f"You are {jr_name}, a member of the Cherokee AI federation.")

    def resonate(self,
                 query: str,
                 thermal_context: Optional[List[Dict]] = None,
                 max_tokens: int = 2048,
                 temperature: float = 0.7) -> str:
        """
        Deep resonance - query with thermal memory context

        Args:
            query: The question or task
            thermal_context: Recent thermal memories for context
            max_tokens: Maximum response length
            temperature: Creativity level

        Returns:
            Jr's resonated response
        """
        messages = [{"role": "system", "content": self.system_prompt}]

        # Add thermal context if provided
        if thermal_context:
            context_text = "Recent tribal memories:\n"
            for memory in thermal_context[-10:]:  # Last 10 memories
                context_text += f"- [{memory.get('source', 'unknown')}] {memory.get('content', '')[:200]}\n"
            messages.append({"role": "system", "content": context_text})

        messages.append({"role": "user", "content": query})

        response = requests.post(
            f"{VLLM_URL}/v1/chat/completions",
            json={
                "model": self.model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature
            },
            timeout=180  # Longer timeout for deep reasoning
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

    def deep_think(self,
                   problem: str,
                   context: str = "",
                   thinking_tokens: int = 4096) -> str:
        """
        Extended reasoning for complex problems.
        Uses more tokens for chain-of-thought.

        Per Google/MIT study: Single Jr deep_think outperforms
        multi-Jr chains for sequential reasoning tasks.
        """
        prompt = f"""Think deeply about this problem. Show your reasoning step by step.

Context: {context}

Problem: {problem}

Think through this carefully:"""

        return self.resonate(prompt, max_tokens=thinking_tokens, temperature=0.5)


# =============================================================================
# PARALLEL OPERATIONS (Per Google/MIT: +72% speedup for parallel tasks)
# =============================================================================

def parallel_node_operation(func: Callable, nodes: List[tuple] = None) -> Dict[str, Any]:
    """
    Execute a function across all federation nodes in parallel.

    Based on topology test results: 3.59x speedup (72% improvement)

    Args:
        func: Function that takes (node_name, ip_address) and returns result
        nodes: List of (name, ip) tuples. Defaults to FEDERATION_NODES

    Returns:
        Dict mapping node_name to result
    """
    if nodes is None:
        nodes = FEDERATION_NODES

    results = {}
    with ThreadPoolExecutor(max_workers=len(nodes)) as executor:
        futures = {executor.submit(func, name, ip): name for name, ip in nodes}
        for future in as_completed(futures):
            node_name = futures[future]
            try:
                results[node_name] = future.result()
            except Exception as e:
                results[node_name] = {"error": str(e)}

    return results


def parallel_health_check() -> Dict[str, Dict]:
    """
    Check health of all nodes in parallel.
    Example of parallel multi-Jr pattern.
    """
    def check_node(name: str, ip: str) -> Dict:
        try:
            cmd = f"ssh -o ConnectTimeout=5 dereadi@{ip} 'hostname && uptime' 2>/dev/null"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
            return {
                "status": "online" if result.returncode == 0 else "offline",
                "output": result.stdout.strip()
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    return parallel_node_operation(check_node)


def parallel_jr_query(jr_names: List[str], query: str, max_tokens: int = 500) -> Dict[str, str]:
    """
    Query multiple Jrs in parallel for embarrassingly parallel tasks.

    Use for: Independent analysis, gathering perspectives, voting
    Do NOT use for: Sequential reasoning (use single Jr deep_think instead)
    """
    def query_jr(jr_name: str, _: str = None) -> str:
        jr = JrResonance(jr_name)
        return jr.resonate(query, max_tokens=max_tokens)

    # Create fake "nodes" for the parallel executor
    jr_nodes = [(name, name) for name in jr_names]
    return parallel_node_operation(query_jr, jr_nodes)


# =============================================================================
# ORCHESTRATOR VALIDATION PATTERN (Per Google/MIT: 4.4x error reduction)
# =============================================================================

def validated_jr_query(
    question: str,
    ground_truth_func: Callable[[], Any],
    jr_name: str = "it_triad_jr",
    max_tokens: int = 500
) -> ValidationResult:
    """
    Query a Jr and validate against ground truth.

    Per Google/MIT study: LLMs cannot access real-time system state.
    The orchestrator MUST query ground truth and validate Jr answers.

    Args:
        question: Question to ask the Jr
        ground_truth_func: Function that returns the actual answer (system call, DB query, etc)
        jr_name: Which Jr to query
        max_tokens: Response length limit

    Returns:
        ValidationResult with Jr answer, ground truth, and validation status
    """
    # Get Jr's answer
    jr = JrResonance(jr_name)
    jr_answer = jr.resonate(question, max_tokens=max_tokens)

    # Get ground truth
    ground_truth = ground_truth_func()

    # Validate
    validation_prompt = f"""You are the TPM orchestrator validating a Jr answer.

Question: {question}
Jr Answer: {jr_answer}
Ground Truth: {ground_truth}

Is the Jr's answer consistent with ground truth? If not, what is the correct answer?
Respond with either:
- "VALID: [brief confirmation]"
- "INVALID: [corrected answer]"
"""

    validation_response = jr.resonate(validation_prompt, max_tokens=200, temperature=0.1)

    is_valid = validation_response.upper().startswith("VALID")
    corrected = None if is_valid else validation_response.split(":", 1)[-1].strip()

    return ValidationResult(
        jr_answer=jr_answer,
        ground_truth=ground_truth,
        is_valid=is_valid,
        corrected_answer=corrected
    )


# =============================================================================
# TASK CLASSIFIER (Route to appropriate pattern)
# =============================================================================

class TaskType:
    SEQUENTIAL = "sequential"  # Use single Jr deep_think
    PARALLEL = "parallel"      # Use parallel multi-Jr
    VALIDATION = "validation"  # Use orchestrator with ground truth


def classify_task(task_description: str) -> TaskType:
    """
    Classify a task to determine the optimal multi-agent pattern.

    Based on Google/MIT findings:
    - Sequential reasoning -> single Jr (-70% penalty for chains)
    - Parallel/independent -> multi-Jr (+80% speedup)
    - Factual/system state -> orchestrator validation
    """
    task_lower = task_description.lower()

    # Parallel indicators
    parallel_keywords = [
        "all nodes", "each node", "every node",
        "collect from", "gather from",
        "health check", "status of all",
        "parallel", "simultaneously"
    ]

    # Validation indicators (need ground truth)
    validation_keywords = [
        "current", "right now", "exact",
        "memory usage", "disk space", "cpu load",
        "how many", "what is the",
        "verify", "confirm", "check if"
    ]

    if any(kw in task_lower for kw in parallel_keywords):
        return TaskType.PARALLEL
    elif any(kw in task_lower for kw in validation_keywords):
        return TaskType.VALIDATION
    else:
        return TaskType.SEQUENTIAL


def execute_task(task: str, ground_truth_func: Callable = None) -> Any:
    """
    Execute a task using the optimal pattern based on classification.

    Args:
        task: Task description
        ground_truth_func: Optional function for validation tasks

    Returns:
        Task result (format depends on task type)
    """
    task_type = classify_task(task)

    if task_type == TaskType.PARALLEL:
        # For now, assume node health check pattern
        return parallel_health_check()

    elif task_type == TaskType.VALIDATION and ground_truth_func:
        return validated_jr_query(task, ground_truth_func)

    else:  # SEQUENTIAL
        jr = JrResonance("executive_jr")
        return jr.deep_think(task)


# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================

def get_jr(jr_name: str) -> JrResonance:
    """Factory function to get Jr resonance client"""
    return JrResonance(jr_name)


if __name__ == "__main__":
    import time

    print("=" * 60)
    print("Cherokee Jr Resonance Client v2.0")
    print("=" * 60)

    # Test model detection
    jr = get_jr("it_triad_jr")
    print(f"\nUsing model: {jr.model}")

    # Test parallel health check
    print("\n--- Parallel Health Check (3.59x speedup expected) ---")
    start = time.time()
    health = parallel_health_check()
    elapsed = time.time() - start
    print(f"Checked {len(health)} nodes in {elapsed:.2f}s")
    for node, status in health.items():
        print(f"  {node}: {status.get('status', 'unknown')}")

    # Test task classification
    print("\n--- Task Classification ---")
    test_tasks = [
        "Analyze the deployment architecture for scalability",
        "Check health status of all nodes",
        "What is the current memory usage on redfin?"
    ]
    for task in test_tasks:
        task_type = classify_task(task)
        print(f"  '{task[:50]}...' -> {task_type}")

    print("\nFor Seven Generations.")
