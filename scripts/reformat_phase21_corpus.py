#!/usr/bin/env python3
"""
Phase 2.2 Corpus Reformatting - Fix Phase 2.1 Types 2&3
Remove trailing questions from educational and community engagement scenarios

Goal: Make Phase 2.1 consistent with direct-answer format
Format: Direct steps/answer → Explanation → NO trailing question
"""

import re
from pathlib import Path
from datetime import datetime

PHASE21_PATH = Path("/ganuda/phase21_direct_answer_corpus.txt")
REFORMATTED_PATH = Path("/ganuda/phase21_reformatted.txt")
LOG_PATH = Path("/ganuda/phase21_reformatting.log")

def log_progress(message):
    """Log to both console and file"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_msg = f"[{timestamp}] {message}"
    print(log_msg)
    with open(LOG_PATH, 'a') as f:
        f.write(log_msg + '\n')

def remove_trailing_question(text):
    """
    Remove trailing question from response

    Strategy:
    1. Find the last sentence
    2. If it's a question, remove it
    3. Keep everything else
    """
    # Split into sentences
    sentences = re.split(r'(?<=[.!])\s+', text)

    # Check if last sentence is a question
    if sentences and sentences[-1].strip().endswith('?'):
        # Remove the trailing question
        return ' '.join(sentences[:-1]).strip() + '.'

    return text

def main():
    log_progress("="*80)
    log_progress("🦅 PHASE 2.1 CORPUS REFORMATTING - REMOVE TRAILING QUESTIONS")
    log_progress("="*80)
    log_progress("")
    log_progress("Root Cause: Types 2&3 have trailing questions")
    log_progress("  \"How will you measure success?\"")
    log_progress("  \"How can you ensure inclusivity for all participants?\"")
    log_progress("  \"What resources does your community already have?\"")
    log_progress("")
    log_progress("Solution: Remove trailing questions, keep direct answers/steps")
    log_progress("")
    log_progress(f"Reading Phase 2.1 corpus: {PHASE21_PATH}")
    log_progress("")

    with open(PHASE21_PATH, 'r') as f:
        corpus = f.read()

    original_questions = corpus.count('?')
    log_progress(f"Original question count: {original_questions}")
    log_progress("")

    # Process line by line
    lines = corpus.split('\n')
    reformatted_lines = []
    questions_removed = 0
    responses_modified = 0

    i = 0
    while i < len(lines):
        line = lines[i]

        # Check if this is a Cherokee AI Response line
        if line.startswith('Cherokee AI Response:'):
            # Extract the response content
            response_match = re.match(r'Cherokee AI Response:\s*"?([^"]*)"?', line)
            if response_match:
                response_text = response_match.group(1)
                original_q_count = response_text.count('?')

                # Remove trailing question
                reformatted_text = remove_trailing_question(response_text)
                new_q_count = reformatted_text.count('?')

                if original_q_count != new_q_count:
                    questions_removed += (original_q_count - new_q_count)
                    responses_modified += 1

                # Rebuild line
                reformatted_lines.append(f'Cherokee AI Response: "{reformatted_text}"')
            else:
                reformatted_lines.append(line)
        else:
            reformatted_lines.append(line)

        i += 1

    reformatted_corpus = '\n'.join(reformatted_lines)
    final_questions = reformatted_corpus.count('?')

    log_progress(f"Reformatting complete:")
    log_progress(f"  Responses modified: {responses_modified}")
    log_progress(f"  Questions removed: {questions_removed}")
    log_progress(f"  Original questions: {original_questions}")
    log_progress(f"  Final questions: {final_questions}")
    log_progress(f"  Reduction: {(1 - final_questions/original_questions)*100:.1f}%")
    log_progress("")

    # Save reformatted corpus
    log_progress(f"Saving reformatted corpus: {REFORMATTED_PATH}")
    with open(REFORMATTED_PATH, 'w') as f:
        f.write(reformatted_corpus)

    reformatted_size = len(reformatted_corpus)
    original_size = len(corpus)

    log_progress(f"  Original size: {original_size:,} bytes")
    log_progress(f"  Reformatted size: {reformatted_size:,} bytes")
    log_progress(f"  Size reduction: {original_size - reformatted_size:,} bytes")
    log_progress("")

    log_progress("="*80)
    log_progress("✅ PHASE 2.1 REFORMATTING COMPLETE")
    log_progress("="*80)
    log_progress("")
    log_progress("Summary:")
    log_progress(f"  ✅ {responses_modified} responses reformatted")
    log_progress(f"  ✅ {questions_removed} trailing questions removed")
    log_progress(f"  ✅ Direct answer format enforced")
    log_progress("")
    log_progress("Next steps:")
    log_progress("  1. Merge reformatted Phase 2.1 with Phase 2 Redux")
    log_progress("  2. Train Phase 2.2 LoRA adapters")
    log_progress("  3. Run regression testing (target: ≥80% pass rate)")
    log_progress("")
    log_progress("🦅 Mitakuye Oyasin - Direct answers without trailing questions! 🔥")

if __name__ == "__main__":
    main()
