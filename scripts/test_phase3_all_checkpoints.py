#!/usr/bin/env python3
"""
PHASE 3: CHECKPOINT REGRESSION TESTING
Test all 6 checkpoints (200, 400, 600, 800, 1000, 1050) to find the champion
Target: 80%+ pass rate (4/5 or 5/5 tests)
"""

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel
import json
from datetime import datetime
from pathlib import Path

# Paths
BASE_MODEL_PATH = "/ganuda/cherokee_resonance_training/cherokee_resonance_v1"
PHASE3_DIR = "/ganuda/cherokee_resonance_training/phase3_lora"
RESULTS_PATH = "/ganuda/phase3_checkpoint_comparison.json"
LOG_PATH = "/ganuda/phase3_checkpoint_testing.log"

# Checkpoints to test
CHECKPOINTS = [200, 400, 600, 800, 1000, 1050]

def log_progress(message):
    """Log to both console and file"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_msg = f"[{timestamp}] {message}"
    print(log_msg)
    with open(LOG_PATH, 'a') as f:
        f.write(log_msg + '\n')

log_progress("="*80)
log_progress("🦅 PHASE 3: CHECKPOINT REGRESSION TESTING")
log_progress("="*80)
log_progress("")
log_progress("Testing 6 checkpoints to find the champion:")
log_progress(f"  Checkpoints: {', '.join(f'step-{c}' for c in CHECKPOINTS)}")
log_progress(f"  Target: ≥80% pass rate (4/5 or 5/5 tests)")
log_progress("")

# Regression test scenarios (same as Phase 2 Redux baseline)
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

def generate_response(model, tokenizer, prompt, max_tokens=200):
    """Generate response from model"""
    # Format with Llama 3.1 Instruct template
    formatted_prompt = f"""<|begin_of_text|><|start_header_id|>user<|end_header_id|>

{prompt}<|eot_id|><|start_header_id|>assistant<|end_header_id|>

"""

    inputs = tokenizer(formatted_prompt, return_tensors="pt").to(model.device)

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
    response = response[len(formatted_prompt):].strip()

    # Remove any trailing special tokens
    if "<|eot_id|>" in response:
        response = response.split("<|eot_id|>")[0].strip()

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

def test_checkpoint(checkpoint_num):
    """Test a single checkpoint"""
    checkpoint_path = f"{PHASE3_DIR}/checkpoint-{checkpoint_num}"

    log_progress("")
    log_progress("="*80)
    log_progress(f"🔬 TESTING CHECKPOINT-{checkpoint_num}")
    log_progress("="*80)
    log_progress("")
    log_progress(f"Loading: {checkpoint_path}")

    try:
        # Load tokenizer
        tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_PATH)

        # Load base model
        base_model = AutoModelForCausalLM.from_pretrained(
            BASE_MODEL_PATH,
            torch_dtype=torch.float16,
            device_map="auto"
        )

        # Load LoRA adapters
        model = PeftModel.from_pretrained(base_model, checkpoint_path)
        log_progress("✅ Model loaded successfully!")
        log_progress("")
    except Exception as e:
        log_progress(f"❌ Error loading checkpoint: {e}")
        return None

    # Run regression tests
    checkpoint_results = []
    test_num = 1

    for test in REGRESSION_TESTS:
        log_progress(f"[{test_num}/{len(REGRESSION_TESTS)}] Test {test['id']}: {test['category']}")
        log_progress(f"   Prompt: \"{test['prompt'][:60]}...\"")

        # Generate response
        response = generate_response(model, tokenizer, test['prompt'])

        # Analyze
        content_coverage, found_terms = check_content(response, test['expected_content'])
        analysis = analyze_response(response)

        # Calculate quality score (0-10)
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
            "analysis": analysis
        }

        checkpoint_results.append(result)

        # Log results
        log_progress(f"   Response: \"{response[:100]}...\"")
        log_progress(f"   Content Coverage: {content_coverage:.1%} ({len(found_terms)}/{len(test['expected_content'])} terms)")
        log_progress(f"   Found: {', '.join(found_terms) if found_terms else 'none'}")
        log_progress(f"   Quality Score: {quality_score:.2f}/10 (threshold: {test['quality_threshold']})")
        log_progress(f"   Status: {'✅ PASS' if passed else '❌ FAIL'}")
        log_progress("")

        test_num += 1

    # Calculate statistics
    total_tests = len(checkpoint_results)
    passed_tests = sum(1 for r in checkpoint_results if r['passed'])
    pass_rate = passed_tests / total_tests
    avg_quality = sum(r['quality_score'] for r in checkpoint_results) / total_tests
    avg_coverage = sum(r['content_coverage'] for r in checkpoint_results) / total_tests

    summary = {
        "checkpoint": checkpoint_num,
        "total_tests": total_tests,
        "passed_tests": passed_tests,
        "pass_rate": pass_rate,
        "avg_quality_score": avg_quality,
        "avg_content_coverage": avg_coverage,
        "detailed_results": checkpoint_results
    }

    log_progress("="*80)
    log_progress(f"📊 CHECKPOINT-{checkpoint_num} SUMMARY")
    log_progress("="*80)
    log_progress(f"Pass Rate: {passed_tests}/{total_tests} ({pass_rate:.1%})")
    log_progress(f"Avg Quality: {avg_quality:.2f}/10")
    log_progress(f"Avg Coverage: {avg_coverage:.1%}")
    log_progress("")

    # Clean up
    del model
    del base_model
    del tokenizer
    torch.cuda.empty_cache()

    return summary

# ============================================================================
# TEST ALL CHECKPOINTS
# ============================================================================

log_progress("="*80)
log_progress("🚀 TESTING ALL CHECKPOINTS")
log_progress("="*80)

all_results = []

for checkpoint_num in CHECKPOINTS:
    summary = test_checkpoint(checkpoint_num)
    if summary:
        all_results.append(summary)

# ============================================================================
# COMPARE ALL CHECKPOINTS
# ============================================================================

log_progress("")
log_progress("="*80)
log_progress("🏆 CHECKPOINT COMPARISON")
log_progress("="*80)
log_progress("")

# Sort by pass rate, then by quality score
all_results.sort(key=lambda x: (x['pass_rate'], x['avg_quality_score']), reverse=True)

log_progress("Ranking (by pass rate, then quality):")
log_progress("")

for i, result in enumerate(all_results):
    rank_emoji = ["🥇", "🥈", "🥉"][i] if i < 3 else f"{i+1}."
    status_emoji = "✅" if result['pass_rate'] >= 0.8 else "⚠️" if result['pass_rate'] >= 0.6 else "❌"

    log_progress(f"{rank_emoji} Checkpoint-{result['checkpoint']:4d}: {status_emoji} {result['pass_rate']:.1%} pass rate | {result['avg_quality_score']:.2f}/10 quality | {result['avg_coverage']:.1%} coverage")

log_progress("")

# Find champion
champion = all_results[0]

log_progress("="*80)
log_progress("👑 CHAMPION CHECKPOINT")
log_progress("="*80)
log_progress("")
log_progress(f"Checkpoint-{champion['checkpoint']}")
log_progress(f"  Pass Rate: {champion['pass_rate']:.1%} ({champion['passed_tests']}/{champion['total_tests']} tests)")
log_progress(f"  Quality Score: {champion['avg_quality_score']:.2f}/10")
log_progress(f"  Content Coverage: {champion['avg_content_coverage']:.1%}")
log_progress("")

# ============================================================================
# SAVE RESULTS
# ============================================================================

comparison_data = {
    "timestamp": datetime.now().isoformat(),
    "model": "Phase 3 LoRA",
    "checkpoints_tested": CHECKPOINTS,
    "phase2_redux_baseline": {
        "pass_rate": 0.60,
        "note": "3/5 tests passed"
    },
    "champion": {
        "checkpoint": champion['checkpoint'],
        "pass_rate": champion['pass_rate'],
        "avg_quality_score": champion['avg_quality_score'],
        "avg_content_coverage": champion['avg_content_coverage'],
        "meets_target": champion['pass_rate'] >= 0.8
    },
    "all_checkpoints": all_results
}

with open(RESULTS_PATH, 'w') as f:
    json.dump(comparison_data, f, indent=2)

log_progress(f"Results saved to: {RESULTS_PATH}")
log_progress("")

# ============================================================================
# FINAL ASSESSMENT
# ============================================================================

log_progress("="*80)
log_progress("🎯 FINAL ASSESSMENT")
log_progress("="*80)
log_progress("")

if champion['pass_rate'] >= 0.8 and champion['avg_quality_score'] >= 7.0:
    log_progress("✅ SUCCESS - TARGET ACHIEVED!")
    log_progress(f"   Checkpoint-{champion['checkpoint']} achieved ≥80% pass rate with high quality")
    log_progress("   Phase 3 research-backed approach validated!")
    log_progress("")
    log_progress("Next steps:")
    log_progress(f"  1. Deploy checkpoint-{champion['checkpoint']} to Ollama")
    log_progress("  2. Restart Ollama service")
    log_progress("  3. Pilot testing with Darrell & Dr. Joe")
    log_progress("  4. Cherokee Nation community validation")

elif champion['pass_rate'] >= 0.8:
    log_progress("✅ PASS RATE TARGET ACHIEVED")
    log_progress(f"   Checkpoint-{champion['checkpoint']} achieved ≥80% pass rate")
    log_progress(f"   Quality scores: {champion['avg_quality_score']:.2f}/10")
    log_progress("")
    log_progress("Recommendation: Proceed with caution")
    log_progress("  - Review low-scoring responses")
    log_progress("  - Monitor in pilot testing")

elif champion['pass_rate'] > 0.60:
    log_progress("⚠️  IMPROVEMENT OVER PHASE 2 REDUX")
    log_progress(f"   Checkpoint-{champion['checkpoint']}: {champion['pass_rate']:.1%} (vs 60% baseline)")
    log_progress("   But did not reach 80% target")
    log_progress("")
    log_progress("Options:")
    log_progress("  A. Deploy Phase 3 checkpoint (improved but below target)")
    log_progress("  B. Use Phase 2 Redux as fallback (60% pass rate)")
    log_progress("  C. Iterate with Phase 3.1 (add more scenarios)")

else:
    log_progress("❌ DID NOT IMPROVE OVER BASELINE")
    log_progress(f"   Best checkpoint: {champion['pass_rate']:.1%} ≤ Phase 2 Redux (60%)")
    log_progress("")
    log_progress("Recommendation: Use Phase 2 Redux as production model")
    log_progress("  - Phase 2 Redux: 60% pass rate (proven)")
    log_progress("  - Investigate Phase 3 training issues")

log_progress("")
log_progress("🦅 Mitakuye Oyasin - All Our Relations 🔥")
