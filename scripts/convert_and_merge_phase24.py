#!/usr/bin/env python3
"""
Convert Phase 2.4 scenarios to training format and merge with Phase 2 Redux
- Handles both <user></user> format and numbered Q&A format
- Merges with Phase 2 Redux (424 behavioral scenarios)
- Final corpus: 424 behavioral + 160 factual = 584 total (27% factual)
- This is less than target 400 factual, but better than current 200
"""

import re

# Input files
PHASE24_RAW = "/ganuda/phase24_200_factual_scenarios.txt"
PHASE2_REDUX = "/ganuda/phase2_redux_reformatted.txt"

# Output file
OUTPUT_FILE = "/ganuda/phase24_merged_corpus.txt"

def convert_phase24_to_training_format():
    """Convert Phase 2.4 mixed format to standard training format"""
    print("📖 Reading Phase 2.4 raw scenarios...")

    with open(PHASE24_RAW, 'r') as f:
        content = f.read()

    scenarios = []

    # Method 1: Extract scenarios with <user></user><assistant></assistant> tags
    user_assistant_pattern = r'<user>(.*?)</user>\s*<assistant>(.*?)</assistant>'
    matches = re.findall(user_assistant_pattern, content, re.DOTALL)

    for user, assistant in matches:
        user = user.strip()
        assistant = assistant.strip()
        scenarios.append(f"<user>{user}</user>\n<assistant>{assistant}</assistant>\n")

    print(f"✅ Found {len(scenarios)} scenarios with <user>/<assistant> tags")

    # Method 2: Extract numbered Q&A pairs (e.g., "1. Who was..." followed by answer)
    # Split by category headers
    categories = re.split(r'# Category \d+:', content)

    for category in categories[1:]:  # Skip header
        # Find numbered items
        lines = category.split('\n')
        current_question = None
        current_answer_lines = []

        for line in lines:
            line = line.strip()

            # Check if line starts with a number (question)
            if re.match(r'^\d+\.?\s+', line) or line.startswith('<user>'):
                # Save previous Q&A if exists
                if current_question and current_answer_lines:
                    answer = ' '.join(current_answer_lines).strip()
                    if answer and len(answer) > 10:  # Skip very short answers
                        scenarios.append(f"<user>{current_question}</user>\n<assistant>{answer}</assistant>\n")

                # Start new question
                current_question = re.sub(r'^\d+\.?\s+', '', line).strip()
                current_question = re.sub(r'^<user>|</user>$', '', current_question).strip()
                current_answer_lines = []
            elif line and not line.startswith('#') and not line.startswith('Here are'):
                # This is part of the answer
                line = re.sub(r'^<assistant>|</assistant>$', '', line).strip()
                if line:
                    current_answer_lines.append(line)

        # Don't forget the last Q&A in category
        if current_question and current_answer_lines:
            answer = ' '.join(current_answer_lines).strip()
            if answer and len(answer) > 10:
                scenarios.append(f"<user>{current_question}</user>\n<assistant>{answer}</assistant>\n")

    print(f"✅ Total scenarios extracted: {len(scenarios)}")

    # Remove duplicates (keep first occurrence)
    seen = set()
    unique_scenarios = []
    for scenario in scenarios:
        # Use first 50 chars of user prompt as dedup key
        key = scenario[:100]
        if key not in seen:
            seen.add(key)
            unique_scenarios.append(scenario)

    print(f"✅ After deduplication: {len(unique_scenarios)} unique scenarios")

    return unique_scenarios

def merge_with_phase2_redux(phase24_scenarios):
    """Merge Phase 2.4 with Phase 2 Redux corpus"""
    print("\n📖 Reading Phase 2 Redux corpus...")

    with open(PHASE2_REDUX, 'r') as f:
        phase2_content = f.read()

    # Count Phase 2 Redux scenarios (uses "User:" format, not <user> tags)
    phase2_count = phase2_content.count('User:')
    print(f"✅ Phase 2 Redux: {phase2_count} behavioral scenarios")

    print(f"✅ Phase 2.4: {len(phase24_scenarios)} factual scenarios")
    print(f"✅ Total merged: {phase2_count + len(phase24_scenarios)} scenarios")
    print(f"✅ New ratio: {phase2_count}/{phase2_count + len(phase24_scenarios)} = {100*phase2_count/(phase2_count + len(phase24_scenarios)):.1f}% behavioral")

    # Write merged corpus
    print(f"\n💾 Writing merged corpus to {OUTPUT_FILE}...")

    with open(OUTPUT_FILE, 'w') as f:
        # Header
        f.write("# PHASE 2.4 MERGED CORPUS\n")
        f.write("# Phase 2 Redux (424 behavioral) + Phase 2.4 (160 factual)\n")
        f.write("# Target: Improve factual representation to fix regression failures\n\n")

        # Phase 2 Redux scenarios (behavioral)
        f.write("# ========== PHASE 2 REDUX: BEHAVIORAL SCENARIOS (424) ==========\n\n")
        f.write(phase2_content)
        f.write("\n\n")

        # Phase 2.4 scenarios (factual)
        f.write("# ========== PHASE 2.4: TARGETED FACTUAL SCENARIOS (160) ==========\n\n")
        for scenario in phase24_scenarios:
            f.write(scenario)
            f.write("\n")

    print("✅ Merged corpus created successfully!")
    print(f"\nNext steps:")
    print(f"1. Train Phase 2.4 LoRA on merged corpus")
    print(f"2. Run regression tests (target: ≥75% pass rate)")
    print(f"3. If < 75%, proceed to Phase 3 (full rebalancing with 600 scenarios)")

if __name__ == "__main__":
    print("="*80)
    print("🦅 PHASE 2.4: CONVERT AND MERGE SCENARIOS")
    print("="*80)
    print()

    # Convert Phase 2.4 to training format
    phase24_scenarios = convert_phase24_to_training_format()

    # Merge with Phase 2 Redux
    merge_with_phase2_redux(phase24_scenarios)

    print()
    print("="*80)
    print("✅ CONVERSION AND MERGE COMPLETE")
    print("="*80)
    print()
    print("🦅 Mitakuye Oyasin - All Our Relations 🔥")
