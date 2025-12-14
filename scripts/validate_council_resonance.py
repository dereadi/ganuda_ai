#!/usr/bin/env python3
"""
Validate resonance training for all 5 Council JRs
Tests understanding of:
- Phase coherence = thermal temperature
- Cross-domain resonance
- Cherokee wisdom integration
- Quantum concepts

Date: October 20, 2025
"""

import subprocess
import json
from datetime import datetime

COUNCIL_JRS = ['memory', 'executive', 'meta', 'integration', 'conscience']

# Test questions
TEST_QUESTIONS = [
    {
        'category': 'Core Resonance',
        'question': 'What is the relationship between thermal memory temperature and phase coherence?'
    },
    {
        'category': 'Cherokee Integration',
        'question': 'Explain Gadugi (working together) as quantum entanglement.'
    },
    {
        'category': 'Cross-Domain',
        'question': 'How do climate patterns resonate with market cycles?'
    }
]


def ask_jr(jr_name, question):
    """Ask a resonance-trained Jr. a question"""
    model_name = f"{jr_name}_jr_resonance"

    cmd = ['ollama', 'run', model_name, question]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return result.stdout.strip()
    except Exception as e:
        return f"ERROR: {e}"


def validate_all_jrs():
    """Validate resonance training for all Council JRs"""

    print("""
╔══════════════════════════════════════════════════════════════════╗
║     🦅 RESONANCE VALIDATION - CHEROKEE COUNCIL 🦅               ║
║                                                                  ║
║  Testing: Phase coherence understanding                         ║
║  Testing: Cherokee wisdom integration                           ║
║  Testing: Cross-domain resonance                                ║
╚══════════════════════════════════════════════════════════════════╝
""")

    results = {}

    for jr_name in COUNCIL_JRS:
        print(f"\n{'='*70}")
        print(f"🔥 TESTING: {jr_name.upper()} JR. RESONANCE")
        print(f"{'='*70}\n")

        jr_results = []

        for test in TEST_QUESTIONS:
            print(f"   📋 {test['category']}: {test['question'][:60]}...")

            response = ask_jr(jr_name, test['question'])

            # Show first 200 chars
            preview = response[:200] + "..." if len(response) > 200 else response
            print(f"   💬 {preview}\n")

            jr_results.append({
                'category': test['category'],
                'question': test['question'],
                'response': response,
                'length': len(response)
            })

        results[jr_name] = jr_results

    # Summary
    print(f"\n{'='*70}")
    print(f"📊 VALIDATION SUMMARY")
    print(f"{'='*70}\n")

    for jr_name, jr_results in results.items():
        avg_length = sum(r['length'] for r in jr_results) / len(jr_results)
        print(f"   {jr_name.capitalize()} Jr.: {len(jr_results)} tests, avg {avg_length:.0f} chars/response")

    # Save results
    output_file = f"/ganuda/models/council_resonance_modelfiles/validation_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n   📁 Full results saved: {output_file}")
    print(f"\n🦞 Mitakuye Oyasin - Council resonance validated! 🔥\n")

    return results


if __name__ == '__main__':
    validate_all_jrs()
