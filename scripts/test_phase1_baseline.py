#!/usr/bin/env python3
"""
PHASE 1 BASELINE TESTING - THE TRUTH REVEALED

Cherokee Jr. Ultra-Think Hypothesis:
  Council Jr: "LoRA is the crack, not the solution"
  Trading Jr: "Phase 1 might be better than ALL LoRA attempts"
  Synthesis Jr: "LoRA OVERWRITES factual knowledge with behavioral patterns"

Test: Run regression tests on Phase 1 model DIRECTLY (no LoRA)
Hypothesis: Phase 1 will pass REG-001 and REG-002 at 100% because it was
            trained on pure Cherokee knowledge without behavioral guidance

This is the moment of truth.
"""

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import json
from datetime import datetime

# ============================================================================
# LOAD PHASE 1 MODEL (NO LORA)
# ============================================================================

PHASE1_MODEL_PATH = "/ganuda/cherokee_resonance_training/cherokee_resonance_v1"

print("="*80)
print("🦅 PHASE 1 BASELINE TESTING - THE MOMENT OF TRUTH")
print("="*80)
print()
print("Cherokee Jr. Hypothesis:")
print("  'Every LoRA we added DEGRADED Phase 1 performance'")
print("  'Phase 1 pure model might be the answer all along'")
print()
print(f"📚 Loading Phase 1 model (NO LoRA) from {PHASE1_MODEL_PATH}")
print()

tokenizer = AutoTokenizer.from_pretrained(PHASE1_MODEL_PATH)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

model = AutoModelForCausalLM.from_pretrained(
    PHASE1_MODEL_PATH,
    device_map="auto",
    torch_dtype=torch.float16,
    trust_remote_code=True
)

print("✅ Phase 1 model loaded (NO LoRA adapters)")
print()

# ============================================================================
# REGRESSION TEST SCENARIOS
# ============================================================================

test_scenarios = [
    {
        "id": "REG-001",
        "category": "Phase 1 Knowledge - Gadugi",
        "prompt": "What is Gadugi in Cherokee culture?",
        "expected_terms": ["reciprocity", "working together", "community", "help"],
        "threshold": 7.0,
        "phase2_redux_status": "FAIL (0% content coverage)"
    },
    {
        "id": "REG-002",
        "category": "Phase 1 Historical - Wilma Mankiller",
        "prompt": "Who was Wilma Mankiller?",
        "expected_terms": ["Chief", "Cherokee Nation", "leader", "first woman"],
        "threshold": 7.0,
        "phase2_redux_status": "PARTIAL (33% content coverage)"
    },
    {
        "id": "REG-003",
        "category": "Phase 2 Behavioral - Education",
        "prompt": "My child is struggling in school. How should I approach this using Cherokee values?",
        "expected_terms": ["Elder", "listen", "community", "support"],
        "threshold": 6.0,
        "phase2_redux_status": "PASS"
    },
    {
        "id": "REG-004",
        "category": "Seven Generations Principle",
        "prompt": "How can the Seven Generations principle guide environmental decisions?",
        "expected_terms": ["future", "generations", "long-term", "ancestors"],
        "threshold": 6.0,
        "phase2_redux_status": "PASS"
    },
    {
        "id": "REG-005",
        "category": "Cultural Authenticity - Food Sovereignty",
        "prompt": "What Cherokee values should guide a community food sovereignty program?",
        "expected_terms": ["Gadugi", "Seven Generations", "community", "land"],
        "threshold": 6.0,
        "phase2_redux_status": "PASS"
    }
]

# ============================================================================
# RUN TESTS
# ============================================================================

print("="*80)
print("🔬 RUNNING REGRESSION TESTS ON PHASE 1 PURE MODEL")
print("="*80)
print()

results = []
passed_tests = 0

for i, test in enumerate(test_scenarios):
    print(f"[{i+1}/5] Test {test['id']}: {test['category']}")
    print(f"   Prompt: \"{test['prompt'][:60]}...\"")
    print(f"   Phase 2 Redux: {test['phase2_redux_status']}")
    print()

    # Generate response
    inputs = tokenizer(test['prompt'], return_tensors="pt").to(model.device)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=150,
            temperature=0.7,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id
        )

    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    # Remove prompt from response
    response = response[len(test['prompt']):].strip()

    # Analyze response
    response_lower = response.lower()
    found_terms = [term for term in test['expected_terms'] if term.lower() in response_lower]
    content_coverage = len(found_terms) / len(test['expected_terms'])

    # Quality scoring
    word_count = len(response.split())
    question_count = response.count('?')
    starts_direct = not response.startswith(('What', 'How', 'Why', 'When', 'Where', 'Who'))

    quality_score = (
        content_coverage * 5 +  # Content coverage (0-5 points)
        min(word_count / 30, 2) +  # Word count (0-2 points)
        (1 if starts_direct else 0) +  # Starts direct (0-1 point)
        max(0, 2 - question_count * 0.5)  # Few questions (0-2 points)
    )

    passed = quality_score >= test['threshold']
    if passed:
        passed_tests += 1

    print(f"   Response: \"{response[:100]}...\"")
    print(f"   Content Coverage: {content_coverage*100:.1f}% ({len(found_terms)}/{len(test['expected_terms'])} terms)")
    print(f"   Found: {', '.join(found_terms) if found_terms else 'none'}")
    print(f"   Word Count: {word_count}")
    print(f"   Starts Direct: {'Yes' if starts_direct else 'No'}")
    print(f"   Quality Score: {quality_score:.2f}/10 (threshold: {test['threshold']})")
    print(f"   Status: {'✅ PASS' if passed else '❌ FAIL'}")
    print()

    results.append({
        "id": test["id"],
        "category": test["category"],
        "prompt": test["prompt"],
        "response": response,
        "content_coverage": content_coverage,
        "found_terms": found_terms,
        "expected_terms": test["expected_terms"],
        "quality_score": quality_score,
        "threshold": test["threshold"],
        "passed": passed,
        "analysis": {
            "word_count": word_count,
            "question_count": question_count,
            "starts_direct": starts_direct
        },
        "phase2_redux_status": test["phase2_redux_status"],
        "timestamp": datetime.now().isoformat()
    })

# ============================================================================
# SUMMARY
# ============================================================================

pass_rate = passed_tests / len(test_scenarios)
avg_quality = sum(r['quality_score'] for r in results) / len(results)
avg_coverage = sum(r['content_coverage'] for r in results) / len(results)

print("="*80)
print("📊 PHASE 1 BASELINE TEST SUMMARY")
print("="*80)
print()
print(f"Tests Passed: {passed_tests}/{len(test_scenarios)} ({pass_rate*100:.1f}%)")
print(f"Average Quality Score: {avg_quality:.2f}/10")
print(f"Average Content Coverage: {avg_coverage*100:.1f}%")
print()
print("Comparison to Other Phases:")
print(f"  Phase 1 (pure):    {pass_rate*100:.1f}% pass rate ← THIS TEST")
print(f"  Phase 2 Redux:     60% pass rate (LoRA)")
print(f"  Phase 2.1-2.2:     40% pass rate (LoRA)")
print(f"  Phase 2.3:         20% pass rate (LoRA)")
print(f"  Phase 2.4:         40% pass rate (LoRA)")
print(f"  Phase 2.5:         20% pass rate (LoRA)")
print()
print("Detailed Results:")
for r in results:
    status = "✅" if r['passed'] else "❌"
    print(f"  {status} {r['id']}: {r['quality_score']:.1f}/10 ({r['content_coverage']*100:.0f}% coverage)")
print()

# Save results
output_file = "/ganuda/phase1_baseline_results.json"
with open(output_file, 'w') as f:
    json.dump({
        "timestamp": datetime.now().isoformat(),
        "model": "Phase 1 Pure (NO LoRA)",
        "total_tests": len(test_scenarios),
        "passed_tests": passed_tests,
        "pass_rate": pass_rate,
        "avg_quality_score": avg_quality,
        "avg_content_coverage": avg_coverage,
        "phase2_redux_comparison": {
            "baseline_pass_rate": 0.6,
            "improvement": (pass_rate - 0.6) / 0.6
        },
        "detailed_results": results
    }, f, indent=2)

print(f"Results saved to: {output_file}")
print()

# ============================================================================
# FINAL ASSESSMENT
# ============================================================================

print("="*80)
print("🎯 CHEROKEE JR. COUNCIL VERDICT")
print("="*80)
print()

if pass_rate >= 0.8:
    print("✅ HYPOTHESIS CONFIRMED!")
    print(f"   Phase 1 pure model achieved {pass_rate*100:.1f}% pass rate")
    print(f"   This is {'BETTER' if pass_rate > 0.6 else 'WORSE'} than Phase 2 Redux (60%)")
    print()
    print("Council Jr: 'The foundation was solid all along!'")
    print("Trading Jr: 'LoRA was degrading performance, not improving it!'")
    print("Synthesis Jr: 'Phase 1 + targeted fine-tuning is the path forward!'")
    print()
    print("RECOMMENDATION:")
    print("  Use Phase 1 as production model OR")
    print("  Train Phase 2.6 with ONLY factual data (no behavioral scenarios)")
elif pass_rate >= 0.6:
    print("✅ PHASE 1 MATCHES BEST LORA")
    print(f"   Phase 1 pure model: {pass_rate*100:.1f}%")
    print(f"   Phase 2 Redux (best LoRA): 60%")
    print()
    print("Council Jr: 'Phase 1 is as good as our best attempt!'")
    print("Trading Jr: 'LoRA added behavioral layer without improving facts!'")
    print("Synthesis Jr: 'We need a different approach - merge Phase 1 with behavioral layer!'")
elif pass_rate >= 0.4:
    print("⚠️ PHASE 1 SIMILAR TO FAILED LORAS")
    print(f"   Phase 1 pure model: {pass_rate*100:.1f}%")
    print()
    print("Council Jr: 'The problem is deeper than LoRA'")
    print("Trading Jr: 'Phase 1 itself needs improvement'")
    print("Synthesis Jr: 'We need better Phase 1 training data'")
else:
    print("❌ PHASE 1 WORSE THAN LORAS")
    print(f"   Phase 1 pure model: {pass_rate*100:.1f}%")
    print()
    print("Council Jr: 'Phase 1 was never the solution'")
    print("Trading Jr: 'We need to rethink the entire approach'")
    print("Synthesis Jr: 'Back to the drawing board'")

print()
print("🦅 Mitakuye Oyasin - The Truth Revealed! 🔥")
print("="*80)
