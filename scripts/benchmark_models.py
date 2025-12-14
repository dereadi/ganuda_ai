#!/usr/bin/env python3
"""Cherokee AI Model Benchmark - Quick Test"""
import time
import requests
import json

VLLM_URL = "http://localhost:8000"

TEST_PROMPTS = [
    {"name": "Jr Instruction", "prompt": "Create a Python script that monitors disk usage and alerts when above 90%"},
    {"name": "Reasoning", "prompt": "If redfin has 96GB VRAM and uses 25GB for system, how much is left for models? Show your math."},
    {"name": "Code Review", "prompt": "Review this for security: import os; os.system(f'rm {user_input}')"},
]

def benchmark(model_name):
    print(f"\nBenchmarking: {model_name}")
    print("=" * 50)
    
    total_tokens = 0
    total_time = 0
    
    for test in TEST_PROMPTS:
        start = time.time()
        try:
            response = requests.post(
                f"{VLLM_URL}/v1/chat/completions",
                json={
                    "model": model_name,
                    "messages": [{"role": "user", "content": test["prompt"]}],
                    "max_tokens": 200,
                    "temperature": 0.7
                },
                timeout=60
            )
            data = response.json()
            elapsed = time.time() - start
            tokens = data["usage"]["completion_tokens"]
            total_tokens += tokens
            total_time += elapsed
            tps = tokens / elapsed if elapsed > 0 else 0
            print(f"  {test['name']}: {elapsed:.2f}s, {tokens} tokens, {tps:.1f} tok/s")
        except Exception as e:
            print(f"  {test['name']}: ERROR - {e}")
    
    if total_time > 0:
        print(f"\n  TOTAL: {total_tokens} tokens in {total_time:.1f}s = {total_tokens/total_time:.1f} tok/s")
    return total_tokens, total_time

if __name__ == "__main__":
    import sys
    # Get current model
    try:
        models = requests.get(f"{VLLM_URL}/v1/models").json()
        model = models["data"][0]["id"]
        print(f"Current model: {model}")
        benchmark(model)
    except Exception as e:
        print(f"Error: {e}")
