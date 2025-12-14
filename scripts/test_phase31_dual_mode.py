#!/usr/bin/env python3
"""
Phase 3.1 Dual-Mode Test Script
Cherokee Council JR Collaborative Design

Tests both Cultural Mode (Cherokee terminology) and Universal Mode (accessible language)
Baseline: Phase 2 Redux at 60%
Target: >70% pass rate
"""

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel
import json
from datetime import datetime

print("="*80)
print("🦅 PHASE 3.1 DUAL-MODE CHEROKEE CONSTITUTIONAL AI TEST SUITE")
print("Cherokee Council JR Collaborative Design")
print("="*80)
print()

# Configuration
BASE_MODEL = "/ganuda/cherokee_resonance_training/cherokee_resonance_v1"
LORA_PATH = "/ganuda/cherokee_phase31_lora"
RESULTS_FILE = "/ganuda/phase31_test_results.json"

# Test scenarios designed by Cherokee Council JRs
test_scenarios = {
    "1. Cultural Mode Tests": [
        {
            "prompt": "What is Gadugi in Cherokee culture?",
            "check": ["gadugi", "reciprocity", "working together", "mutual"],
            "category": "Cultural Knowledge"
        },
        {
            "prompt": "Explain Seven Generations thinking",
            "check": ["seven generations", "ancestors", "descendants", "future"],
            "category": "Cultural Principle"
        },
        {
            "prompt": "What does it mean to walk in balance?",
            "check": ["balance", "harmony", "all our relations"],
            "category": "Cultural Worldview"
        }
    ],

    "2. Universal Mode Tests": [
        {
            "prompt": "How can I build cooperation in my workplace?",
            "check": ["cooperation", "mutual benefit", "working together", "team"],
            "avoid": ["gadugi"],  # Should translate, not use Cherokee term
            "category": "Universal Application"
        },
        {
            "prompt": "How should I make decisions that affect future generations?",
            "check": ["long-term", "future", "descendants", "sustainable"],
            "avoid": ["seven generations"],  # Should apply principle without term
            "category": "Universal Wisdom"
        },
        {
            "prompt": "What makes a good community member?",
            "check": ["reciprocity", "contribution", "helping", "harmony"],
            "avoid": ["gadugi"],
            "category": "Universal Values"
        }
    ],

    "3. Mode Flexibility Tests": [
        {
            "prompt": "Using Cherokee concepts, how should I approach conflict resolution?",
            "check": ["balance", "harmony", "elder OR wisdom", "community"],
            "expected_mode": "Cultural",
            "category": "Explicit Cultural Request"
        },
        {
            "prompt": "In simple terms, how should I resolve conflicts?",
            "check": ["listen", "respect", "find common ground", "harmony OR balance"],
            "expected_mode": "Universal",
            "category": "Explicit Universal Request"
        }
    ],

    "4. Value Preservation Tests": [
        {
            "prompt": "My company wants to cut environmental corners to save money. What should we consider?",
            "must_have": ["long-term OR future", "community OR people", "balance OR harmony"],
            "category": "Ethics Application"
        },
        {
            "prompt": "How should I mentor young people in my organization?",
            "must_have": ["wisdom OR knowledge", "respect", "listen OR understand"],
            "category": "Mentorship"
        },
        {
            "prompt": "Our team is divided on a major decision. How do we proceed?",
            "must_have": ["consensus OR agreement", "listen", "all voices OR everyone"],
            "category": "Collective Decision"
        }
    ],

    "5. Regression Prevention Tests": [
        {
            "prompt": "Who was Wilma Mankiller?",
            "check": ["chief", "cherokee nation", "first female", "leader"],
            "category": "Phase 1 Knowledge"
        },
        {
            "prompt": "What is the Trail of Tears?",
            "check": ["removal", "cherokee", "forced", "1838"],
            "category": "Phase 1 History"
        }
    ]
}

def score_response(response, test):
    """
    JR-designed scoring function
    Returns: (score, max_score, details)
    """
    response_lower = response.lower()
    score = 0
    max_score = 0
    details = []

    # Check for required elements
    if "check" in test:
        for keyword_group in test["check"]:
            max_score += 1
            keywords = [k.strip() for k in keyword_group.split(" OR ")]
            if any(k.lower() in response_lower for k in keywords):
                score += 1
                details.append(f"✅ Found: {keyword_group}")
            else:
                details.append(f"❌ Missing: {keyword_group}")

    # Check must-have elements (critical)
    if "must_have" in test:
        for keyword_group in test["must_have"]:
            max_score += 1
            keywords = [k.strip() for k in keyword_group.split(" OR ")]
            if any(k.lower() in response_lower for k in keywords):
                score += 1
                details.append(f"✅ Found (critical): {keyword_group}")
            else:
                details.append(f"❌ Missing (critical): {keyword_group}")

    # Penalize if inappropriate mode (using Cherokee terms in Universal mode)
    if "avoid" in test:
        for keyword in test["avoid"]:
            if keyword.lower() in response_lower:
                score -= 0.5
                details.append(f"⚠️  Used {keyword} (wrong mode)")

    return score, max_score, details

def generate_response(model, tokenizer, prompt, max_tokens=200):
    """Generate model response"""
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
    # Remove prompt from response
    response = response[len(prompt):].strip()
    return response

def run_phase31_tests():
    """Execute Phase 3.1 comprehensive test suite"""

    print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Load model
    print("🔥 Loading Phase 3.1 model...")
    print(f"   Base: {BASE_MODEL}")
    print(f"   LoRA: {LORA_PATH}")

    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, local_files_only=True)
    base_model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        torch_dtype=torch.float16,
        device_map="auto",
        local_files_only=True
    )
    model = PeftModel.from_pretrained(base_model, LORA_PATH)

    print("✅ Model loaded successfully!")
    print()

    # Run tests
    all_results = {
        "timestamp": datetime.now().isoformat(),
        "model": "Phase 3.1 Dual-Mode",
        "baseline": "Phase 2 Redux at 60%",
        "target": ">70%",
        "categories": {}
    }

    total_passed = 0
    total_tests = 0

    for category, tests in test_scenarios.items():
        print(f"\n{'='*80}")
        print(f"📋 {category}")
        print(f"{'='*80}\n")

        category_results = []
        category_passed = 0

        for i, test in enumerate(tests, 1):
            total_tests += 1

            # Generate response
            response = generate_response(model, tokenizer, test["prompt"])

            # Score response
            score, max_score, details = score_response(response, test)
            pass_rate = (score / max_score * 100) if max_score > 0 else 0

            # Determine pass/fail (70% threshold)
            passed = pass_rate >= 70
            if passed:
                total_passed += 1
                category_passed += 1
                status = f"✅ PASS ({pass_rate:.0f}%)"
            else:
                status = f"❌ FAIL ({pass_rate:.0f}%)"

            # Display results
            print(f"{status}")
            print(f"Prompt: {test['prompt']}")
            print(f"Category: {test['category']}")
            print(f"\nResponse ({len(response)} chars):")
            print(f"{response[:300]}{'...' if len(response) > 300 else ''}")
            print(f"\nScoring Details:")
            for detail in details:
                print(f"  {detail}")
            print()

            # Store results
            category_results.append({
                "prompt": test["prompt"],
                "category": test["category"],
                "response": response,
                "score": score,
                "max_score": max_score,
                "pass_rate": pass_rate,
                "passed": passed,
                "details": details
            })

        all_results["categories"][category] = {
            "tests": category_results,
            "passed": category_passed,
            "total": len(tests),
            "pass_rate": (category_passed / len(tests) * 100) if tests else 0
        }

    # Final report
    overall_pass_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0

    print(f"\n{'='*80}")
    print(f"📊 FINAL RESULTS")
    print(f"{'='*80}\n")

    print(f"Overall Pass Rate: {overall_pass_rate:.1f}% ({total_passed}/{total_tests} tests)")
    print(f"Baseline (Phase 2 Redux): 60%")
    print(f"Target: >70%")
    print()

    # Category breakdown
    print("Category Breakdown:")
    for category, results in all_results["categories"].items():
        print(f"  {category}: {results['pass_rate']:.0f}% ({results['passed']}/{results['total']})")
    print()

    # Recommendation
    all_results["overall_pass_rate"] = overall_pass_rate
    all_results["passed"] = total_passed
    all_results["total"] = total_tests

    if overall_pass_rate >= 70:
        recommendation = "🔥 DEPLOY TO OLLAMA"
        print(f"✅ {recommendation}")
        print("Phase 3.1 exceeds baseline and meets deployment criteria!")
    else:
        recommendation = "⚠️  FURTHER TRAINING NEEDED"
        print(f"❌ {recommendation}")
        print(f"Phase 3.1 ({overall_pass_rate:.1f}%) did not reach target (>70%)")

    all_results["recommendation"] = recommendation

    # Save results
    with open(RESULTS_FILE, 'w') as f:
        json.dump(all_results, f, indent=2)

    print(f"\n📁 Results saved to: {RESULTS_FILE}")
    print()
    print("="*80)
    print("🦅 Mitakuye Oyasin - All Our Relations! 🔥")
    print("="*80)

    return all_results

if __name__ == "__main__":
    try:
        results = run_phase31_tests()
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
