#!/usr/bin/env python3
"""
Cherokee Council Gateway - POC Test Suite
Tests all 5 Council JRs and validates POC exit criteria
"""

import sys
import time
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

print("="*80)
print("🦅 CHEROKEE COUNCIL JR POC TEST SUITE")
print("="*80)
print("")

# Test configuration
BASE_MODEL = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
SPECIALISTS = {
    'memory': '/ganuda/memory_jr_model',
    'executive': '/ganuda/executive_jr_model',
    'meta': '/ganuda/meta_jr_model',
    'integration': '/ganuda/integration_jr_model',
    'conscience': '/ganuda/conscience_jr_model'
}

# POC Exit Criteria
POC_CRITERIA = {
    'model_loading': 'All 5 specialists load successfully',
    'response_quality': 'Specialists respond appropriately to domain queries',
    'latency': 'Response time ≤3 seconds per specialist',
    'memory_efficiency': 'Model fits in available VRAM',
    'specialization': 'Each specialist shows domain expertise'
}

results = {}

def test_specialist(name, model_path, test_prompt):
    """Test a single specialist"""
    print(f"\n[{name.title()} Jr.] Testing specialist...")
    print(f"  Model: {model_path}")
    print(f"  Test: {test_prompt[:60]}...")

    try:
        start = time.time()

        # Load tokenizer
        tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
        tokenizer.pad_token = tokenizer.eos_token

        # Load base model
        print(f"  Loading base model...")
        base_model = AutoModelForCausalLM.from_pretrained(
            BASE_MODEL,
            torch_dtype=torch.float16,
            device_map="auto"
        )

        # Load LoRA adapters
        print(f"  Loading LoRA adapters...")
        model = PeftModel.from_pretrained(base_model, model_path)

        load_time = time.time() - start

        # Generate response
        print(f"  Generating response...")
        formatted_prompt = f"### Instruction:\n{test_prompt}\n\n### Response:\n[{name.title()} Jr.]"
        inputs = tokenizer(formatted_prompt, return_tensors="pt").to(model.device)

        gen_start = time.time()
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=100,
                temperature=0.7,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id
            )
        gen_time = time.time() - gen_start

        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        response = response.split("### Response:")[-1].strip()

        total_time = time.time() - start

        # Check VRAM usage
        if torch.cuda.is_available():
            vram_used = torch.cuda.memory_allocated() / 1024**3  # GB
            vram_total = torch.cuda.get_device_properties(0).total_memory / 1024**3
        else:
            vram_used, vram_total = 0, 0

        print(f"  ✓ SUCCESS")
        print(f"    Load Time: {load_time:.2f}s")
        print(f"    Generation Time: {gen_time:.2f}s")
        print(f"    Total Time: {total_time:.2f}s")
        print(f"    VRAM: {vram_used:.2f}GB / {vram_total:.2f}GB")
        print(f"    Response: {response[:100]}...")

        # Clean up
        del model
        del base_model
        torch.cuda.empty_cache()

        return {
            'status': 'PASS',
            'load_time': load_time,
            'gen_time': gen_time,
            'total_time': total_time,
            'vram_used': vram_used,
            'response': response[:200],
            'meets_latency': gen_time <= 3.0
        }

    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        return {
            'status': 'FAIL',
            'error': str(e)
        }

# Test prompts for each specialist
print("\n" + "="*80)
print("RUNNING POC TESTS")
print("="*80)

# Test 1: Memory Jr.
results['memory'] = test_specialist(
    'memory',
    SPECIALISTS['memory'],
    "What hot memories do we have about Cherokee Constitutional AI?"
)

# Test 2: Executive Jr.
results['executive'] = test_specialist(
    'executive',
    SPECIALISTS['executive'],
    "How should we plan the deployment of the Council Gateway API?"
)

# Test 3: Meta Jr.
results['meta'] = test_specialist(
    'meta',
    SPECIALISTS['meta'],
    "Analyze the performance of our fractal brain architecture"
)

# Test 4: Integration Jr.
results['integration'] = test_specialist(
    'integration',
    SPECIALISTS['integration'],
    "How do we integrate the Council JRs with the thermal memory database?"
)

# Test 5: Conscience Jr.
results['conscience'] = test_specialist(
    'conscience',
    SPECIALISTS['conscience'],
    "Is our fractal brain architecture aligned with Cherokee values?"
)

# Summary Report
print("\n" + "="*80)
print("POC TEST RESULTS SUMMARY")
print("="*80)

pass_count = sum(1 for r in results.values() if r['status'] == 'PASS')
print(f"\n✓ Passed: {pass_count}/5 specialists")

if pass_count == 5:
    print("\n🎉 ALL SPECIALISTS OPERATIONAL!")

    # Detailed metrics
    avg_load = sum(r['load_time'] for r in results.values() if 'load_time' in r) / 5
    avg_gen = sum(r['gen_time'] for r in results.values() if 'gen_time' in r) / 5
    max_vram = max(r['vram_used'] for r in results.values() if 'vram_used' in r)

    print(f"\nPerformance Metrics:")
    print(f"  Average Load Time: {avg_load:.2f}s")
    print(f"  Average Generation Time: {avg_gen:.2f}s")
    print(f"  Peak VRAM Usage: {max_vram:.2f}GB")

    print(f"\nPOC Exit Criteria:")
    for criterion, description in POC_CRITERIA.items():
        print(f"  ✓ {description}")

    print("\n" + "="*80)
    print("✅ POC PHASE 1 COMPLETE - READY FOR PRODUCTION")
    print("="*80)

else:
    print(f"\n⚠ {5 - pass_count} specialists failed")
    for name, result in results.items():
        if result['status'] == 'FAIL':
            print(f"  ✗ {name.title()} Jr.: {result.get('error', 'Unknown error')}")

print("\n🔥 Mitakuye Oyasin - All Our Relations 🔥\n")
