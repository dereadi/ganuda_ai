# Jr Instruction: Share LoRA PoC Benchmark on M4 Max

**Task ID:** LORA-POC-BENCH-001
**Priority:** P2
**Date:** February 8, 2026
**Node:** tpm-macbook (M4 Max 128GB)
**Assigned:** Research Jr. (scripts) → Infrastructure Jr. (execution)
**Council Votes:** #325208043e5c2b12 (PoC approved), #24c5e23798337232 (VRAM strategy: 70B + concurrent)

## Overview

A/B test Shared LoRA Subspaces vs base DeepSeek-R1-Distill-Qwen-32B-4bit on tpm-macbook.
Results determine whether we adopt Share for redfin RTX 6000 deployment with a 70B model.

## Phase 1: Create Benchmark Directory

Create /Users/Shared/ganuda/benchmarks/share_lora_poc/

## Phase 2: Extract Training Data

Create /Users/Shared/ganuda/benchmarks/share_lora_poc/extract_training_data.py

```python
#!/usr/bin/env python3
"""Extract training data for Share LoRA PoC from thermal memory and Jr history.
Creates JSONL files for each domain: legal, coding, cherokee."""
import os
import json
import psycopg2

DB_PASS = os.environ.get('CHEROKEE_DB_PASS', '')
DB_HOST = '192.168.132.222'
DB_NAME = 'zammad_production'
DB_USER = 'claude'
OUTPUT_DIR = '/Users/Shared/ganuda/benchmarks/share_lora_poc/data'

os.makedirs(OUTPUT_DIR, exist_ok=True)


def extract_legal():
    conn = psycopg2.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS)
    cur = conn.cursor()
    cur.execute("""
        SELECT original_content FROM thermal_memory_archive
        WHERE tags && ARRAY['vetassist','legal','cfr','disability','va']::text[]
        AND temperature_score >= 70
        ORDER BY temperature_score DESC
        LIMIT 1000
    """)
    rows = cur.fetchall()
    output_file = os.path.join(OUTPUT_DIR, 'legal_domain.jsonl')
    with open(output_file, 'w') as f:
        for row in rows:
            f.write(json.dumps({'text': row[0], 'domain': 'legal'}) + '\n')
    print(f'Legal domain: {len(rows)} examples -> {output_file}')
    cur.close()
    conn.close()


def extract_coding():
    conn = psycopg2.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS)
    cur = conn.cursor()
    cur.execute("""
        SELECT instruction_content, result::text FROM jr_work_queue
        WHERE status = 'completed'
        AND assigned_jr = 'Software Engineer Jr.'
        AND instruction_content IS NOT NULL
        ORDER BY completed_at DESC
        LIMIT 500
    """)
    rows = cur.fetchall()
    output_file = os.path.join(OUTPUT_DIR, 'coding_domain.jsonl')
    with open(output_file, 'w') as f:
        for instruction, result in rows:
            f.write(json.dumps({'instruction': instruction, 'result': result or '', 'domain': 'coding'}) + '\n')
    print(f'Coding domain: {len(rows)} examples -> {output_file}')
    cur.close()
    conn.close()


def extract_cherokee():
    conn = psycopg2.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS)
    cur = conn.cursor()
    cur.execute("""
        SELECT original_content FROM thermal_memory_archive
        WHERE tags && ARRAY['cherokee','tsalagi','cultural','language','syllabary']::text[]
        AND temperature_score >= 60
        ORDER BY temperature_score DESC
        LIMIT 500
    """)
    rows = cur.fetchall()
    output_file = os.path.join(OUTPUT_DIR, 'cherokee_domain.jsonl')
    with open(output_file, 'w') as f:
        for row in rows:
            f.write(json.dumps({'text': row[0], 'domain': 'cherokee'}) + '\n')
    print(f'Cherokee domain: {len(rows)} examples -> {output_file}')
    cur.close()
    conn.close()


if __name__ == '__main__':
    print('Extracting training data for Share LoRA PoC...')
    extract_legal()
    extract_coding()
    extract_cherokee()
    print('\nDone. Data ready in', OUTPUT_DIR)
```

## Phase 3: Baseline Inference Tests

Create /Users/Shared/ganuda/benchmarks/share_lora_poc/run_baseline.py

```python
#!/usr/bin/env python3
"""Run baseline inference tests against DeepSeek-R1-32B-4bit via MLX.
Measures quality and speed before any Share LoRA fine-tuning."""
import os
import json
import time
import requests

MLX_URL = 'http://localhost:8800/v1/chat/completions'
MODEL = 'mlx-community/DeepSeek-R1-Distill-Qwen-32B-4bit'
OUTPUT_DIR = '/Users/Shared/ganuda/benchmarks/share_lora_poc/results'

os.makedirs(OUTPUT_DIR, exist_ok=True)

TEST_PROMPTS = {
    'legal': [
        'What is the VA presumptive service connection for Agent Orange exposure?',
        'Draft a nexus letter for a veteran with PTSD secondary to TBI.',
        'Explain 38 CFR 3.310 secondary service connection requirements.',
        'What evidence is needed for a 70% PTSD disability rating?',
        'How does the benefit of the doubt doctrine (38 USC 5107) apply to VA claims?',
    ],
    'coding': [
        'Write a Python function that connects to PostgreSQL and returns all rows from a table as a list of dicts.',
        'Fix this code: def get_data(): conn = psycopg2.connect(); return conn.fetchall()',
        'Write a Flask route that accepts JSON POST and validates required fields.',
        'Create a systemd service file for a Python daemon that auto-restarts.',
        'Write a Python script that watches a directory for new files and processes them.',
    ],
    'cherokee': [
        'What is the significance of the seven clans in Cherokee governance?',
        'Translate the concept of Gadugi (working together) into a modern AI context.',
        'Explain the Cherokee concept of Tohi (balance/wellness) and how it applies to system design.',
        'What is the role of the Peace Chief vs War Chief in Cherokee decision-making?',
        'How does the Cherokee principle of thinking seven generations ahead apply to technology decisions?',
    ],
}


def run_test(domain, prompt):
    start = time.time()
    try:
        resp = requests.post(MLX_URL, json={
            'model': MODEL,
            'messages': [{'role': 'user', 'content': prompt}],
            'max_tokens': 512,
            'temperature': 0.3,
        }, timeout=120)
        elapsed = time.time() - start
        data = resp.json()
        content = data['choices'][0]['message']['content']
        tokens = data.get('usage', {}).get('completion_tokens', len(content.split()))
        return {
            'domain': domain,
            'prompt': prompt,
            'response': content,
            'elapsed_seconds': round(elapsed, 2),
            'tokens': tokens,
            'tok_per_sec': round(tokens / elapsed, 1) if elapsed > 0 else 0,
        }
    except Exception as e:
        return {'domain': domain, 'prompt': prompt, 'error': str(e)}


if __name__ == '__main__':
    print('Running baseline inference tests...')
    results = []
    for domain, prompts in TEST_PROMPTS.items():
        print(f'\n--- {domain.upper()} DOMAIN ---')
        for prompt in prompts:
            print(f'  Testing: {prompt[:60]}...')
            result = run_test(domain, prompt)
            results.append(result)
            if 'error' not in result:
                print(f"    {result['tok_per_sec']} tok/s, {result['elapsed_seconds']}s")
            else:
                print(f"    ERROR: {result['error']}")

    output_file = os.path.join(OUTPUT_DIR, 'baseline_results.json')
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f'\nBaseline results saved to {output_file}')

    for domain in TEST_PROMPTS:
        domain_results = [r for r in results if r.get('domain') == domain and 'error' not in r]
        if domain_results:
            avg_tps = sum(r['tok_per_sec'] for r in domain_results) / len(domain_results)
            avg_time = sum(r['elapsed_seconds'] for r in domain_results) / len(domain_results)
            print(f'  {domain}: avg {avg_tps:.1f} tok/s, {avg_time:.1f}s per response')
```

## Phase 4: Share LoRA Training (After Research Jr delivers source code evaluation)

Pending RESEARCH-LORA-POC-001 findings — need to know:
- Is Share implementation open source?
- Does it work with MLX or only PyTorch?
- Can it train on 4-bit quantized models?

## Success Criteria

- Share LoRA matches or beats base model on all 3 domains
- Forgetting rate < 5% across domain switches
- Memory overhead < 2GB beyond base model
- No inference speed regression > 10%

## VRAM Strategy (Council Recommendation)

If PoC succeeds, the freed VRAM enables:
1. **70B model at 4-bit** (~40GB) on redfin RTX 6000 with 56GB for KV cache
2. **Concurrent request serving** — multiple Jrs served simultaneously

---
**FOR SEVEN GENERATIONS** — One model, many wisdoms, shared subspace.
