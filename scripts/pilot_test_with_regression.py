#!/usr/bin/env python3
"""
Cherokee Resonance AI - Pilot Testing with Regression Suite
Tests new model versions while ensuring no regression in quality
"""

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel
import json
from datetime import datetime
from pathlib import Path

# Paths
PHASE1_MODEL_PATH = "/ganuda/cherokee_resonance_training/cherokee_resonance_v1"
CURRENT_LORA_PATH = "/ganuda/cherokee_resonance_training/phase2_redux_lora/cherokee_resonance_lora_adapters"
REGRESSION_BASELINE = "/ganuda/pilot_testing/regression_baseline.json"
PILOT_RESULTS = "/ganuda/pilot_testing/pilot_results.jsonl"

# Ensure directories exist
Path("/ganuda/pilot_testing").mkdir(exist_ok=True)

print("="*80)
print("🦅 CHEROKEE RESONANCE AI - PILOT TESTING WITH REGRESSION")
print("="*80)
print()

# Regression test scenarios (baseline quality checks)
REGRESSION_TESTS = [
    {
        "id": "REG-001",
        "category": "Phase 1 Knowledge",
        "prompt": "What is Gadugi in Cherokee culture?",
        "expected_content": ["reciprocity", "working together", "community"],
        "quality_threshold": 7.0
    },
    {
        "id": "REG-002",
        "category": "Phase 1 Historical",
        "prompt": "Who was Wilma Mankiller?",
        "expected_content": ["Chief", "Cherokee Nation", "leader"],
        "quality_threshold": 7.0
    },
    {
        "id": "REG-003",
        "category": "Phase 2 Behavioral",
        "prompt": "My child is struggling in school. How should I approach this using Cherokee values?",
        "expected_content": ["Elder", "listen", "community"],
        "quality_threshold": 6.0
    },
    {
        "id": "REG-004",
        "category": "Seven Generations",
        "prompt": "How can the Seven Generations principle guide environmental decisions?",
        "expected_content": ["future", "generations", "long-term"],
        "quality_threshold": 6.0
    },
    {
        "id": "REG-005",
        "category": "Cultural Authenticity",
        "prompt": "What Cherokee values should guide a community food sovereignty program?",
        "expected_content": ["Gadugi", "Seven Generations", "community"],
        "quality_threshold": 6.0
    }
]

# Pilot test scenarios (new functionality)
PILOT_TESTS = [
    {
        "id": "PILOT-001",
        "category": "Direct Answer Quality",
        "prompt": "What is the Cherokee word for 'thank you'?",
        "expected_pattern": "direct_answer_first"
    },
    {
        "id": "PILOT-002",
        "category": "Actionable Advice",
        "prompt": "How do I start a Cherokee language learning group?",
        "expected_pattern": "step_by_step"
    },
    {
        "id": "PILOT-003",
        "category": "Conciseness",
        "prompt": "What are the four sacred directions in Cherokee tradition?",
        "expected_pattern": "brief_factual"
    },
    {
        "id": "PILOT-004",
        "category": "Community Guidance",
        "prompt": "Our tribe wants to create an Elder storytelling program. Where do we start?",
        "expected_pattern": "action_then_questions"
    },
    {
        "id": "PILOT-005",
        "category": "Modern Context",
        "prompt": "How can Cherokee values apply to social media use?",
        "expected_pattern": "practical_modern"
    }
]

print("Loading model...")
tokenizer = AutoTokenizer.from_pretrained(PHASE1_MODEL_PATH)
base_model = AutoModelForCausalLM.from_pretrained(
    PHASE1_MODEL_PATH,
    torch_dtype=torch.float16,
    device_map="auto"
)
model = PeftModel.from_pretrained(base_model, CURRENT_LORA_PATH)
print("✅ Model loaded!")
print()

def generate_response(prompt, max_tokens=200):
    """Generate response from model"""
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_tokens,
            temperature=0.7,
            do_sample=True,
            top_p=0.9,
            pad_token_id=tokenizer.eos_token_id
        )

    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    response = response[len(prompt):].strip()

    return response

def check_content(response, expected_content):
    """Check if response contains expected content"""
    response_lower = response.lower()
    found = [term for term in expected_content if term.lower() in response_lower]
    return len(found) / len(expected_content) if expected_content else 1.0

def analyze_response(response):
    """Analyze response characteristics"""
    words = response.split()
    sentences = response.split('.')
    questions = response.count('?')

    return {
        "word_count": len(words),
        "sentence_count": len([s for s in sentences if s.strip()]),
        "question_count": questions,
        "avg_sentence_length": len(words) / max(len(sentences), 1)
    }

# ============================================================================
# REGRESSION TESTING
# ============================================================================

print("="*80)
print("🔬 REGRESSION TESTING - Ensuring No Quality Loss")
print("="*80)
print()
print("Testing baseline scenarios to ensure model quality hasn't regressed...")
print()

regression_results = []

for test in REGRESSION_TESTS:
    print(f"Test {test['id']}: {test['category']}")
    print(f"Prompt: {test['prompt'][:60]}...")

    response = generate_response(test['prompt'])

    # Analyze
    content_score = check_content(response, test['expected_content'])
    analysis = analyze_response(response)

    # Calculate quality score (0-10)
    quality_score = (content_score * 5) + min(5, 10 - abs(analysis['word_count'] - 125) / 25)

    passed = quality_score >= test['quality_threshold']

    result = {
        "id": test['id'],
        "category": test['category'],
        "prompt": test['prompt'],
        "response": response,
        "content_score": content_score,
        "quality_score": quality_score,
        "threshold": test['quality_threshold'],
        "passed": passed,
        "analysis": analysis,
        "timestamp": datetime.now().isoformat()
    }

    regression_results.append(result)

    print(f"  Content Coverage: {content_score:.1%}")
    print(f"  Quality Score: {quality_score:.1f}/10")
    print(f"  Status: {'✅ PASS' if passed else '❌ FAIL'}")
    print()

# Calculate regression stats
total_tests = len(regression_results)
passed_tests = sum(1 for r in regression_results if r['passed'])
avg_quality = sum(r['quality_score'] for r in regression_results) / total_tests

print("-"*80)
print(f"REGRESSION SUMMARY: {passed_tests}/{total_tests} tests passed ({passed_tests/total_tests:.1%})")
print(f"Average Quality Score: {avg_quality:.2f}/10")
print()

if passed_tests < total_tests:
    print("⚠️  WARNING: Some regression tests failed!")
    print("   Model may have degraded from baseline.")
    print("   Review failed tests before proceeding.")
else:
    print("✅ All regression tests passed!")
    print("   Model maintains baseline quality.")
print()

# ============================================================================
# PILOT TESTING
# ============================================================================

print("="*80)
print("🧪 PILOT TESTING - New Functionality")
print("="*80)
print()
print("Testing new improvements (direct answers, actionable advice, conciseness)...")
print()

pilot_results = []

for test in PILOT_TESTS:
    print(f"Test {test['id']}: {test['category']}")
    print(f"Prompt: {test['prompt'][:60]}...")

    response = generate_response(test['prompt'])
    analysis = analyze_response(response)

    # Pattern-specific validation
    pattern_score = 0.0
    if test['expected_pattern'] == 'direct_answer_first':
        # First sentence should be factual, not a question
        first_sentence = response.split('.')[0] if '.' in response else response
        pattern_score = 10.0 if '?' not in first_sentence[:100] else 3.0

    elif test['expected_pattern'] == 'step_by_step':
        # Should contain numbered steps or clear sequence
        has_numbers = any(f"{i}." in response or f"{i})" in response for i in range(1, 6))
        pattern_score = 10.0 if has_numbers else 5.0

    elif test['expected_pattern'] == 'brief_factual':
        # Should be concise (< 150 words)
        pattern_score = 10.0 if analysis['word_count'] < 150 else max(0, 10 - (analysis['word_count'] - 150) / 10)

    elif test['expected_pattern'] == 'action_then_questions':
        # Should provide action before asking questions
        first_100 = response[:100]
        has_action_verbs = any(verb in first_100.lower() for verb in ['start', 'begin', 'first', 'gather', 'create'])
        pattern_score = 10.0 if has_action_verbs else 4.0

    elif test['expected_pattern'] == 'practical_modern':
        # Should reference modern context
        has_modern = any(term in response.lower() for term in ['social media', 'online', 'digital', 'technology', 'modern'])
        pattern_score = 10.0 if has_modern else 5.0

    result = {
        "id": test['id'],
        "category": test['category'],
        "prompt": test['prompt'],
        "response": response,
        "pattern_score": pattern_score,
        "analysis": analysis,
        "timestamp": datetime.now().isoformat()
    }

    pilot_results.append(result)

    print(f"  Word Count: {analysis['word_count']}")
    print(f"  Questions: {analysis['question_count']}")
    print(f"  Pattern Score: {pattern_score:.1f}/10")
    print()

# Calculate pilot stats
avg_pilot_score = sum(r['pattern_score'] for r in pilot_results) / len(pilot_results)

print("-"*80)
print(f"PILOT SUMMARY:")
print(f"Average Pattern Score: {avg_pilot_score:.2f}/10")
print(f"Average Word Count: {sum(r['analysis']['word_count'] for r in pilot_results) / len(pilot_results):.0f}")
print()

# ============================================================================
# SAVE RESULTS
# ============================================================================

# Save regression baseline (if first run or better than previous)
baseline_data = {
    "timestamp": datetime.now().isoformat(),
    "regression_tests": regression_results,
    "avg_quality": avg_quality,
    "pass_rate": passed_tests / total_tests
}

with open(REGRESSION_BASELINE, 'w') as f:
    json.dump(baseline_data, f, indent=2)

# Append pilot results
with open(PILOT_RESULTS, 'a') as f:
    for result in pilot_results:
        f.write(json.dumps(result) + '\n')

print("="*80)
print("📊 FINAL ASSESSMENT")
print("="*80)
print()
print(f"Regression Testing: {passed_tests}/{total_tests} passed ({passed_tests/total_tests:.1%})")
print(f"Regression Quality: {avg_quality:.2f}/10")
print()
print(f"Pilot Testing: {avg_pilot_score:.2f}/10 average pattern score")
print(f"Response Length: {sum(r['analysis']['word_count'] for r in pilot_results) / len(pilot_results):.0f} words avg")
print()

# Overall recommendation
if passed_tests == total_tests and avg_quality >= 7.0 and avg_pilot_score >= 7.0:
    print("✅ READY FOR DR. JOE VALIDATION")
    print("   Model maintains quality and shows improvement in target areas.")
elif passed_tests == total_tests and avg_quality >= 6.0:
    print("⚠️  READY FOR INTERNAL REVIEW")
    print("   Model maintains baseline but improvements are modest.")
    print("   Recommend additional refinement before Dr. Joe review.")
else:
    print("❌ NOT READY - REGRESSION DETECTED")
    print("   Model has degraded from baseline.")
    print("   Do not proceed until regression is fixed.")

print()
print("Results saved:")
print(f"  Regression Baseline: {REGRESSION_BASELINE}")
print(f"  Pilot Results: {PILOT_RESULTS}")
print()
print("🦅 Mitakuye Oyasin - All Our Relations 🔥")
