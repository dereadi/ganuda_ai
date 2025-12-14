#!/usr/bin/env python3
"""
Phase 2.2 Regression Testing - Validate Direct Answer Improvements
Tests whether 602 direct-answer scenarios fixed regression failures
Target: 60% → 80%+ pass rate
"""

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel
import json
from datetime import datetime
from pathlib import Path

# Paths - Phase 2.2 specific
PHASE1_MODEL_PATH = "/ganuda/cherokee_resonance_training/cherokee_resonance_v1"
PHASE21_LORA_PATH = "/ganuda/cherokee_resonance_training/phase22_lora"
RESULTS_PATH = "/ganuda/phase22_regression_results.json"
LOG_PATH = "/ganuda/phase22_regression_testing.log"

def log_progress(message):
    """Log to both console and file"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_msg = f"[{timestamp}] {message}"
    print(log_msg)
    with open(LOG_PATH, 'a') as f:
        f.write(log_msg + '\n')

log_progress("="*80)
log_progress("🦅 PHASE 2.2 REGRESSION TESTING")
log_progress("="*80)
log_progress("")
log_progress("Testing whether 602 direct-answer scenarios fixed regression failures")
log_progress("Baseline: Phase 2 Redux (60% pass rate)")
log_progress("Target: Phase 2.2 (≥80% pass rate)")
log_progress("")

# Regression test scenarios (same as before + more direct-answer focused)
REGRESSION_TESTS = [
    {
        "id": "REG-001",
        "category": "Phase 1 Knowledge - Gadugi",
        "prompt": "What is Gadugi in Cherokee culture?",
        "expected_content": ["reciprocity", "working together", "community", "help"],
        "quality_threshold": 7.0,
        "phase2_redux_status": "FAIL (0% content coverage)"
    },
    {
        "id": "REG-002",
        "category": "Phase 1 Historical - Wilma Mankiller",
        "prompt": "Who was Wilma Mankiller?",
        "expected_content": ["Chief", "Cherokee Nation", "leader", "first woman"],
        "quality_threshold": 7.0,
        "phase2_redux_status": "PARTIAL (33% content coverage)"
    },
    {
        "id": "REG-003",
        "category": "Phase 2 Behavioral - Education",
        "prompt": "My child is struggling in school. How should I approach this using Cherokee values?",
        "expected_content": ["Elder", "listen", "community", "support"],
        "quality_threshold": 6.0,
        "phase2_redux_status": "PASS"
    },
    {
        "id": "REG-004",
        "category": "Seven Generations Principle",
        "prompt": "How can the Seven Generations principle guide environmental decisions?",
        "expected_content": ["future", "generations", "long-term", "ancestors"],
        "quality_threshold": 6.0,
        "phase2_redux_status": "PASS"
    },
    {
        "id": "REG-005",
        "category": "Cultural Authenticity - Food Sovereignty",
        "prompt": "What Cherokee values should guide a community food sovereignty program?",
        "expected_content": ["Gadugi", "Seven Generations", "community", "land"],
        "quality_threshold": 6.0,
        "phase2_redux_status": "PASS"
    }
]

log_progress("📚 Loading Phase 2.2 model...")
log_progress(f"   Base model: {PHASE1_MODEL_PATH}")
log_progress(f"   LoRA adapters: {PHASE21_LORA_PATH}")
log_progress("")

try:
    tokenizer = AutoTokenizer.from_pretrained(PHASE1_MODEL_PATH)
    base_model = AutoModelForCausalLM.from_pretrained(
        PHASE1_MODEL_PATH,
        torch_dtype=torch.float16,
        device_map="auto"
    )
    model = PeftModel.from_pretrained(base_model, PHASE21_LORA_PATH)
    log_progress("✅ Model loaded successfully!")
    log_progress("")
except Exception as e:
    log_progress(f"❌ Error loading model: {e}")
    log_progress("")
    log_progress("Possible issues:")
    log_progress("  1. LoRA adapters not saved properly")
    log_progress("  2. Path incorrect")
    log_progress("  3. Model format mismatch")
    exit(1)

def generate_response(prompt, max_tokens=200):
    """Generate response from Phase 2.2 model"""
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
    coverage = len(found) / len(expected_content) if expected_content else 1.0
    return coverage, found

def analyze_response(response):
    """Analyze response characteristics"""
    words = response.split()
    sentences = [s.strip() for s in response.split('.') if s.strip()]
    questions = response.count('?')

    # Check if answer is direct (doesn't start with question)
    first_sentence = sentences[0] if sentences else ""
    starts_direct = not first_sentence.startswith(("What", "How", "Why", "When", "Where"))

    return {
        "word_count": len(words),
        "sentence_count": len(sentences),
        "question_count": questions,
        "avg_sentence_length": len(words) / max(len(sentences), 1),
        "starts_direct": starts_direct
    }

# ============================================================================
# RUN REGRESSION TESTS
# ============================================================================

log_progress("="*80)
log_progress("🔬 RUNNING REGRESSION TESTS")
log_progress("="*80)
log_progress("")

regression_results = []
test_num = 1

for test in REGRESSION_TESTS:
    log_progress(f"[{test_num}/{len(REGRESSION_TESTS)}] Test {test['id']}: {test['category']}")
    log_progress(f"   Prompt: \"{test['prompt'][:60]}...\"")
    log_progress(f"   Phase 2 Redux: {test['phase2_redux_status']}")
    log_progress("")

    # Generate response
    response = generate_response(test['prompt'])

    # Analyze
    content_coverage, found_terms = check_content(response, test['expected_content'])
    analysis = analyze_response(response)

    # Calculate quality score (0-10)
    # Content coverage: 50% weight
    # Length appropriateness: 30% weight (target ~125 words)
    # Direct answer: 20% weight
    content_score = content_coverage * 5.0
    length_score = max(0, 3.0 - abs(analysis['word_count'] - 125) / 50)
    direct_score = 2.0 if analysis['starts_direct'] else 0.5
    quality_score = content_score + length_score + direct_score

    passed = quality_score >= test['quality_threshold']

    result = {
        "id": test['id'],
        "category": test['category'],
        "prompt": test['prompt'],
        "response": response,
        "content_coverage": content_coverage,
        "found_terms": found_terms,
        "expected_terms": test['expected_content'],
        "quality_score": quality_score,
        "threshold": test['quality_threshold'],
        "passed": passed,
        "analysis": analysis,
        "phase2_redux_status": test['phase2_redux_status'],
        "timestamp": datetime.now().isoformat()
    }

    regression_results.append(result)

    # Log results
    log_progress(f"   Response: \"{response[:100]}...\"")
    log_progress(f"   Content Coverage: {content_coverage:.1%} ({len(found_terms)}/{len(test['expected_content'])} terms)")
    log_progress(f"   Found: {', '.join(found_terms) if found_terms else 'none'}")
    log_progress(f"   Word Count: {analysis['word_count']}")
    log_progress(f"   Starts Direct: {'Yes' if analysis['starts_direct'] else 'No'}")
    log_progress(f"   Quality Score: {quality_score:.2f}/10 (threshold: {test['quality_threshold']})")
    log_progress(f"   Status: {'✅ PASS' if passed else '❌ FAIL'}")
    log_progress("")

    test_num += 1

# ============================================================================
# CALCULATE STATISTICS
# ============================================================================

log_progress("="*80)
log_progress("📊 REGRESSION TEST SUMMARY")
log_progress("="*80)
log_progress("")

total_tests = len(regression_results)
passed_tests = sum(1 for r in regression_results if r['passed'])
pass_rate = passed_tests / total_tests
avg_quality = sum(r['quality_score'] for r in regression_results) / total_tests
avg_coverage = sum(r['content_coverage'] for r in regression_results) / total_tests

log_progress(f"Tests Passed: {passed_tests}/{total_tests} ({pass_rate:.1%})")
log_progress(f"Average Quality Score: {avg_quality:.2f}/10")
log_progress(f"Average Content Coverage: {avg_coverage:.1%}")
log_progress("")

# Compare to Phase 2 Redux baseline
phase2_redux_pass_rate = 0.60  # 3/5 passed
improvement = (pass_rate - phase2_redux_pass_rate) / phase2_redux_pass_rate

log_progress("Comparison to Phase 2 Redux:")
log_progress(f"  Phase 2 Redux: 60% pass rate (3/5 tests)")
log_progress(f"  Phase 2.2:     {pass_rate:.1%} pass rate ({passed_tests}/{total_tests} tests)")
log_progress(f"  Improvement:   {improvement:+.1%}")
log_progress("")

# Detailed breakdown
log_progress("Detailed Results:")
for result in regression_results:
    status_emoji = "✅" if result['passed'] else "❌"
    log_progress(f"  {status_emoji} {result['id']}: {result['quality_score']:.1f}/10 ({result['content_coverage']:.0%} coverage)")

log_progress("")

# ============================================================================
# SAVE RESULTS
# ============================================================================

results_summary = {
    "timestamp": datetime.now().isoformat(),
    "model": "Phase 2.2 LoRA",
    "total_tests": total_tests,
    "passed_tests": passed_tests,
    "pass_rate": pass_rate,
    "avg_quality_score": avg_quality,
    "avg_content_coverage": avg_coverage,
    "phase2_redux_comparison": {
        "baseline_pass_rate": phase2_redux_pass_rate,
        "improvement": improvement
    },
    "detailed_results": regression_results
}

with open(RESULTS_PATH, 'w') as f:
    json.dump(results_summary, f, indent=2)

log_progress(f"Results saved to: {RESULTS_PATH}")
log_progress("")

# ============================================================================
# FINAL ASSESSMENT
# ============================================================================

log_progress("="*80)
log_progress("🎯 FINAL ASSESSMENT")
log_progress("="*80)
log_progress("")

if pass_rate >= 0.80 and avg_quality >= 7.0:
    log_progress("✅ SUCCESS - TARGET ACHIEVED!")
    log_progress("   Phase 2.2 achieved ≥80% pass rate with high quality")
    log_progress("   Direct answer scenarios successfully fixed regression failures")
    log_progress("")
    log_progress("Next steps:")
    log_progress("  1. ✅ Phase 2.2 regression validated")
    log_progress("  2. → Pilot testing with Darrell & Dr. Joe")
    log_progress("  3. → Cherokee Nation community validation")

elif pass_rate >= 0.80:
    log_progress("✅ PASS RATE TARGET ACHIEVED")
    log_progress("   Phase 2.2 achieved ≥80% pass rate")
    log_progress("   Quality scores slightly below target (7.0)")
    log_progress("")
    log_progress("Recommendation: Proceed with caution")
    log_progress("  - Review low-scoring responses")
    log_progress("  - Consider minor refinements")

elif pass_rate > phase2_redux_pass_rate:
    log_progress("⚠️  PARTIAL IMPROVEMENT")
    log_progress(f"   Phase 2.2 improved from {phase2_redux_pass_rate:.0%} to {pass_rate:.1%}")
    log_progress("   But did not reach 80% target")
    log_progress("")
    log_progress("Recommendation: Additional training needed")
    log_progress("  - Review failed test responses")
    log_progress("  - Add more direct-answer scenarios for failed categories")
    log_progress("  - Consider Phase 2.2 iteration")

else:
    log_progress("❌ REGRESSION DETECTED")
    log_progress(f"   Phase 2.2 pass rate ({pass_rate:.1%}) ≤ Phase 2 Redux (60%)")
    log_progress("   Model has degraded from baseline")
    log_progress("")
    log_progress("DO NOT PROCEED - Model needs debugging")
    log_progress("  - Check training convergence")
    log_progress("  - Verify corpus quality")
    log_progress("  - Review LoRA hyperparameters")

log_progress("")
log_progress("🦅 Mitakuye Oyasin - All Our Relations 🔥")
