#!/usr/bin/env python3
"""
Merge Phase 2.2 Reformatted Corpus
Combines reformatted Phase 2 Redux + reformatted Phase 2.1
"""

from pathlib import Path
from datetime import datetime

PHASE2_REDUX_PATH = Path("/ganuda/phase2_redux_reformatted.txt")
PHASE21_PATH = Path("/ganuda/phase21_reformatted.txt")
MERGED_PATH = Path("/ganuda/phase22_merged_training_corpus.txt")

def main():
    print("="*80)
    print("🦅 PHASE 2.2 CORPUS MERGE - REFORMATTED CORPORA")
    print("="*80)
    print()

    # Read reformatted corpora
    print(f"📚 Reading reformatted Phase 2 Redux: {PHASE2_REDUX_PATH}")
    with open(PHASE2_REDUX_PATH, 'r') as f:
        phase2_redux = f.read()

    phase2_redux_scenarios = phase2_redux.count("### Scenario")
    phase2_redux_questions = phase2_redux.count("?")
    print(f"   ✅ {phase2_redux_scenarios} scenarios, {phase2_redux_questions} questions")
    print()

    print(f"📚 Reading reformatted Phase 2.1: {PHASE21_PATH}")
    with open(PHASE21_PATH, 'r') as f:
        phase21 = f.read()

    phase21_scenarios = phase21.count("### Scenario")
    phase21_questions = phase21.count("?")
    print(f"   ✅ {phase21_scenarios} scenarios, {phase21_questions} questions")
    print()

    # Merge
    print("🔗 Merging corpora...")
    merged = f"""# Cherokee Constitutional AI - Phase 2.2 Merged Training Corpus
# Generated: {datetime.now().isoformat()}
#
# Contents:
#   - Phase 2 Redux (reformatted): {phase2_redux_scenarios} behavioral scenarios
#   - Phase 2.1 (reformatted): {phase21_scenarios} direct answer scenarios
#   - Total: {phase2_redux_scenarios + phase21_scenarios} scenarios
#
# Reformatting Changes:
#   - Phase 2 Redux: 2 scenarios reformatted (already mostly good)
#   - Phase 2.1: 292 trailing questions removed (31.3% reduction)
#   - Total questions removed: 294
#
# Purpose: Fix pattern confusion with consistent format
# Training target: Phase 2.2 LoRA adapters
# Expected pass rate: ≥80% (vs Phase 2.1: 40%, Phase 2 Redux: 60%)
#
{'='*80}

{'='*80}
PHASE 2 REDUX - BEHAVIORAL SCENARIOS (REFORMATTED)
{'='*80}

{phase2_redux}

{'='*80}
PHASE 2.1 - DIRECT ANSWER SCENARIOS (REFORMATTED)
{'='*80}

{phase21}
"""

    # Write merged corpus
    print(f"💾 Writing merged corpus: {MERGED_PATH}")
    with open(MERGED_PATH, 'w') as f:
        f.write(merged)

    merged_scenarios = phase2_redux_scenarios + phase21_scenarios
    merged_questions = phase2_redux_questions + phase21_questions
    merged_size = len(merged)

    print(f"   ✅ {merged_scenarios} total scenarios")
    print(f"   ✅ {merged_questions} total questions")
    print(f"   ✅ {merged_size / 1024:.1f} KB")
    print()

    print("="*80)
    print("✅ PHASE 2.2 CORPUS MERGE COMPLETE")
    print("="*80)
    print()
    print("Summary:")
    print(f"  Phase 2 Redux:  {phase2_redux_scenarios} scenarios, {phase2_redux_questions} questions")
    print(f"  Phase 2.1:      {phase21_scenarios} scenarios, {phase21_questions} questions")
    print(f"  Total:          {merged_scenarios} scenarios, {merged_questions} questions")
    print()
    print("Comparison to Phase 2.1 (original):")
    print(f"  Original questions: 932 + 22 = 954")
    print(f"  Reformatted questions: {merged_questions}")
    print(f"  Reduction: {954 - merged_questions} questions ({(1 - merged_questions/954)*100:.1f}%)")
    print()
    print("Next step: Train Phase 2.2 LoRA adapters")
    print()
    print("🦅 Mitakuye Oyasin - Corpus reformatted with consistent patterns! 🔥")

if __name__ == "__main__":
    main()
