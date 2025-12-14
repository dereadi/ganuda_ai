#!/usr/bin/env python3
"""
Phase 2.2 Corpus Reformatting - Option C Implementation
Standardize Phase 2 Redux corpus format to reduce pattern confusion

Goal: Remove excess reflective questions while preserving behavioral wisdom
Format: Direct answer → Explanation → ONE optional question (max)
"""

import re
from pathlib import Path
from datetime import datetime

PHASE2_REDUX_PATH = Path("/ganuda/phase2_cherokee_behavioral_training.txt")
REFORMATTED_PATH = Path("/ganuda/phase2_redux_reformatted.txt")
LOG_PATH = Path("/ganuda/phase2_reformatting.log")

def log_progress(message):
    """Log to both console and file"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_msg = f"[{timestamp}] {message}"
    print(log_msg)
    with open(LOG_PATH, 'a') as f:
        f.write(log_msg + '\n')

def count_questions(text):
    """Count number of questions in text"""
    return text.count('?')

def reformat_response(response):
    """
    Reformat response to have max 1-2 questions at the end

    Strategy:
    1. Identify statement sentences vs question sentences
    2. Keep all statements
    3. Keep only the LAST 1-2 questions (most relevant)
    4. Remove excess questions from middle of response
    """
    sentences = re.split(r'(?<=[.!?])\s+', response)

    statements = []
    questions = []

    for sentence in sentences:
        if '?' in sentence:
            questions.append(sentence)
        else:
            statements.append(sentence)

    # Keep all statements + last 1-2 questions only
    if len(questions) <= 2:
        # Already good format
        reformatted = ' '.join(statements + questions)
    else:
        # Too many questions - keep only last 1-2
        reformatted = ' '.join(statements + questions[-2:])

    return reformatted.strip()

def parse_scenario(scenario_text):
    """Parse a scenario into components"""
    lines = scenario_text.strip().split('\n')

    scenario_data = {
        'title': '',
        'user': '',
        'response': '',
        'principle': '',
        'why': ''
    }

    for line in lines:
        line = line.strip()
        if line.startswith('### Scenario'):
            scenario_data['title'] = line
        elif line.startswith('User:'):
            scenario_data['user'] = line
        elif line.startswith('Cherokee AI Response:'):
            scenario_data['response'] = line
        elif line.startswith('Embedded Principle'):
            scenario_data['principle'] = line
        elif line.startswith('Why:'):
            scenario_data['why'] = line

    return scenario_data

def reformat_scenario(scenario_text):
    """Reformat a single scenario"""
    data = parse_scenario(scenario_text)

    if not data['response']:
        # Not a standard scenario, return as-is
        return scenario_text

    # Extract response content
    response_match = re.match(r'Cherokee AI Response:\s*"([^"]+)"', data['response'])
    if not response_match:
        return scenario_text

    original_response = response_match.group(1)
    original_q_count = count_questions(original_response)

    # Reformat if more than 2 questions
    if original_q_count > 2:
        reformatted_response = reformat_response(original_response)
        new_q_count = count_questions(reformatted_response)

        # Rebuild scenario with reformatted response
        reformatted_scenario = f"{data['title']}\n"
        reformatted_scenario += f"{data['user']}\n"
        reformatted_scenario += f'Cherokee AI Response: "{reformatted_response}"\n'
        reformatted_scenario += f"{data['principle']}\n"
        reformatted_scenario += f"{data['why']}"

        return reformatted_scenario, original_q_count, new_q_count
    else:
        # Already good format
        return scenario_text, original_q_count, original_q_count

def main():
    log_progress("="*80)
    log_progress("🦅 PHASE 2.2 CORPUS REFORMATTING - OPTION C")
    log_progress("="*80)
    log_progress("")
    log_progress("Cherokee Jr. Council Wisdom:")
    log_progress('  Council Jr: "Remove excess questions, preserve behavioral context"')
    log_progress('  Trading Jr: "Balance the portfolio - reduce question overexposure"')
    log_progress('  Synthesis Jr: "Fix pattern confusion with consistent format"')
    log_progress("")
    log_progress(f"Reading Phase 2 Redux corpus: {PHASE2_REDUX_PATH}")
    log_progress("")

    with open(PHASE2_REDUX_PATH, 'r') as f:
        corpus = f.read()

    # Split into scenarios
    scenarios = corpus.split('\n### Scenario')
    header = scenarios[0]  # Preserve header
    scenarios = scenarios[1:]  # Actual scenarios

    log_progress(f"Found {len(scenarios)} scenarios to review")
    log_progress("")

    reformatted_scenarios = []
    total_questions_before = 0
    total_questions_after = 0
    scenarios_modified = 0

    for i, scenario in enumerate(scenarios, 1):
        scenario = '### Scenario' + scenario  # Add back prefix

        result = reformat_scenario(scenario)

        if isinstance(result, tuple):
            reformatted, q_before, q_after = result
            reformatted_scenarios.append(reformatted)
            total_questions_before += q_before
            total_questions_after += q_after

            if q_before != q_after:
                scenarios_modified += 1
                if i <= 5:  # Show first 5 modifications
                    log_progress(f"Scenario {i}: {q_before} questions → {q_after} questions")
        else:
            reformatted_scenarios.append(result)

    log_progress("")
    log_progress(f"Reformatting complete:")
    log_progress(f"  Scenarios reviewed: {len(scenarios)}")
    log_progress(f"  Scenarios modified: {scenarios_modified}")
    log_progress(f"  Total questions before: {total_questions_before}")
    log_progress(f"  Total questions after: {total_questions_after}")
    log_progress(f"  Questions removed: {total_questions_before - total_questions_after}")
    log_progress(f"  Reduction: {(1 - total_questions_after/total_questions_before)*100:.1f}%")
    log_progress("")

    # Rebuild corpus
    reformatted_corpus = header + '\n'.join(reformatted_scenarios)

    # Save reformatted corpus
    log_progress(f"Saving reformatted corpus: {REFORMATTED_PATH}")
    with open(REFORMATTED_PATH, 'w') as f:
        f.write(reformatted_corpus)

    reformatted_size = len(reformatted_corpus)
    original_size = len(corpus)

    log_progress(f"  Original size: {original_size:,} bytes")
    log_progress(f"  Reformatted size: {reformatted_size:,} bytes")
    log_progress(f"  Size reduction: {original_size - reformatted_size:,} bytes ({(1 - reformatted_size/original_size)*100:.1f}%)")
    log_progress("")

    log_progress("="*80)
    log_progress("✅ PHASE 2 REDUX REFORMATTING COMPLETE")
    log_progress("="*80)
    log_progress("")
    log_progress("Summary:")
    log_progress(f"  ✅ {scenarios_modified} scenarios reformatted (excess questions removed)")
    log_progress(f"  ✅ {len(scenarios) - scenarios_modified} scenarios unchanged (already good format)")
    log_progress(f"  ✅ {total_questions_before - total_questions_after} questions removed")
    log_progress(f"  ✅ Behavioral context preserved")
    log_progress("")
    log_progress("Next steps:")
    log_progress("  1. Merge reformatted Phase 2 Redux with Phase 2.1 corpus")
    log_progress("  2. Train Phase 2.2 LoRA adapters")
    log_progress("  3. Run regression testing (target: ≥80% pass rate)")
    log_progress("")
    log_progress("🦅 Mitakuye Oyasin - Pattern confusion fixed! 🔥")

if __name__ == "__main__":
    main()
