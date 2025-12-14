#!/usr/bin/env python3
"""
Merge Phase 2.1 Direct Answer Corpus with Phase 2 Redux Behavioral Corpus

Phase 2 Redux: 374 behavioral scenarios (questions answered with Cherokee values)
Phase 2.1: 602 direct answer scenarios (fixes regression failures)
Total: 976 scenarios for Phase 2.1 LoRA training
"""

from pathlib import Path
from datetime import datetime

PHASE2_REDUX_CORPUS = Path("/ganuda/phase2_cherokee_behavioral_training.txt")
PHASE21_CORPUS = Path("/ganuda/phase21_direct_answer_corpus.txt")
MERGED_CORPUS = Path("/ganuda/phase21_merged_training_corpus.txt")

def merge_corpora():
    """Merge Phase 2 Redux and Phase 2.1 corpora"""

    print("="*80)
    print("🦅 MERGING PHASE 2.1 CORPUS")
    print("="*80)
    print()

    # Read Phase 2 Redux corpus
    print(f"📚 Reading Phase 2 Redux corpus: {PHASE2_REDUX_CORPUS}")
    with open(PHASE2_REDUX_CORPUS, 'r') as f:
        phase2_redux = f.read()

    phase2_redux_lines = len(phase2_redux.split('\n'))
    phase2_redux_scenarios = phase2_redux.count("User:")
    print(f"   ✅ {phase2_redux_scenarios} scenarios, {phase2_redux_lines} lines")
    print()

    # Read Phase 2.1 corpus
    print(f"📚 Reading Phase 2.1 corpus: {PHASE21_CORPUS}")
    with open(PHASE21_CORPUS, 'r') as f:
        phase21 = f.read()

    phase21_lines = len(phase21.split('\n'))
    phase21_scenarios = phase21.count("### Scenario:")
    print(f"   ✅ {phase21_scenarios} scenarios, {phase21_lines} lines")
    print()

    # Merge
    print(f"🔗 Merging corpora...")
    merged = f"""# Cherokee Constitutional AI - Phase 2.1 Merged Training Corpus
# Generated: {datetime.now().isoformat()}
#
# Contents:
#   - Phase 2 Redux: {phase2_redux_scenarios} behavioral scenarios
#   - Phase 2.1: {phase21_scenarios} direct answer scenarios
#   - Total: {phase2_redux_scenarios + phase21_scenarios} scenarios
#
# Purpose: Fix regression failures while preserving behavioral training
# Training target: Phase 2.1 LoRA adapters
#
{'='*80}

{'='*80}
PHASE 2 REDUX - BEHAVIORAL SCENARIOS
{'='*80}

{phase2_redux}

{'='*80}
PHASE 2.1 - DIRECT ANSWER SCENARIOS
{'='*80}

{phase21}
"""

    # Write merged corpus
    print(f"💾 Writing merged corpus: {MERGED_CORPUS}")
    with open(MERGED_CORPUS, 'w') as f:
        f.write(merged)

    merged_lines = len(merged.split('\n'))
    merged_scenarios = phase2_redux_scenarios + phase21_scenarios

    print(f"   ✅ {merged_scenarios} total scenarios")
    print(f"   ✅ {merged_lines} total lines")
    print(f"   ✅ {MERGED_CORPUS.stat().st_size / 1024:.1f} KB")
    print()

    print("="*80)
    print("✅ CORPUS MERGE COMPLETE")
    print("="*80)
    print()
    print("Summary:")
    print(f"  Phase 2 Redux:  {phase2_redux_scenarios} scenarios (behavioral)")
    print(f"  Phase 2.1:      {phase21_scenarios} scenarios (direct answers)")
    print(f"  Total:          {merged_scenarios} scenarios")
    print()
    print("Next step: Train Phase 2.1 LoRA adapters")
    print()
    print("🦅 Mitakuye Oyasin - The corpora are united! 🔥")

if __name__ == "__main__":
    merge_corpora()
