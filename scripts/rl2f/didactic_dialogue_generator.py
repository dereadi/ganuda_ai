#!/usr/bin/env python3
"""
RL2F Phase 1: Didactic Dialogue Generator
Generates teacher-student dialogues from council vote outcomes.

Teacher: has ground truth recommendation + specialist concerns
Student: reasons from scratch, teacher guides toward correct answer

Usage:
    python3 didactic_dialogue_generator.py --batch-size 50 --max-dialogues 500
    python3 didactic_dialogue_generator.py --dry-run  # preview without generating

For Seven Generations
"""

import argparse
import json
import os
import sys
import time
import hashlib
import psycopg2
import psycopg2.extras
import requests
from datetime import datetime

# Configuration
VLLM_URL = "http://192.168.132.222:8000/v1/chat/completions"
VLLM_MODEL = "Qwen/Qwen2.5-72B-Instruct-AWQ"
DB_CONFIG = {
    "host": "192.168.132.222",
    "dbname": "zammad_production",
    "user": "claude",
    "password": os.environ.get("CHEROKEE_DB_PASS", "")
}
OUTPUT_DIR = "/ganuda/reports/rl2f_dialogues"
PROMPT_VERSION = "v1.0"

TEACHER_SYSTEM = """You are an expert AI council teacher. You know the correct recommendation and the concerns raised by specialists. Guide the student toward understanding through Socratic questioning. Do NOT reveal the answer directly — ask probing questions that help the student reason correctly.

Ground truth: {recommendation} (confidence: {confidence})
Specialist concerns: {concerns}

After 3-4 exchanges, if the student is on the right track, confirm their reasoning. If they are stuck after 4 exchanges, provide a gentle hint."""

STUDENT_SYSTEM = """You are an AI reasoning student analyzing a council question. Think step by step. Consider multiple perspectives (security, efficiency, cultural values, architecture). Share your reasoning openly. When the teacher asks a question, engage thoughtfully.

You do NOT know the correct answer. Reason from first principles."""


def get_db():
    return psycopg2.connect(**DB_CONFIG, cursor_factory=psycopg2.extras.RealDictCursor)


def fetch_unprocessed_votes(conn, limit=50):
    """Fetch council votes not yet converted to dialogues."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT cv.id, cv.question, cv.consensus, cv.recommendation,
                   cv.confidence, cv.concerns, cv.specialist_count,
                   cv.audit_hash
            FROM council_votes cv
            LEFT JOIN didactic_dialogues dd ON dd.source_vote_id = cv.id
            WHERE dd.id IS NULL
              AND cv.consensus IS NOT NULL
              AND cv.question IS NOT NULL
              AND length(cv.question) > 20
            ORDER BY cv.voted_at DESC
            LIMIT %s
        """, (limit,))
        return cur.fetchall()


def generate_dialogue(vote):
    """Generate a multi-turn teacher-student dialogue from a council vote."""
    question = vote["question"]
    recommendation = vote.get("recommendation", "PROCEED")
    confidence = vote.get("confidence", 0.7)
    concerns_raw = vote.get("concerns", "[]")

    # Parse concerns
    if isinstance(concerns_raw, str):
        try:
            concerns = json.loads(concerns_raw)
        except (json.JSONDecodeError, TypeError):
            concerns = [concerns_raw] if concerns_raw else []
    elif isinstance(concerns_raw, list):
        concerns = concerns_raw
    else:
        concerns = []

    concerns_text = "; ".join(concerns[:5]) if concerns else "None raised"

    teacher_sys = TEACHER_SYSTEM.format(
        recommendation=recommendation,
        confidence=confidence,
        concerns=concerns_text
    )

    # Build dialogue: 4-6 turns
    dialogue_turns = []
    student_messages = [{"role": "system", "content": STUDENT_SYSTEM}]
    teacher_messages = [{"role": "system", "content": teacher_sys}]

    # Turn 1: Student initial analysis
    student_messages.append({
        "role": "user",
        "content": f"Please analyze this question for the tribal council:\n\n{question}"
    })

    for turn_num in range(4):
        # Student responds
        student_resp = call_vllm(student_messages, max_tokens=300, temperature=0.7)
        if not student_resp:
            break

        dialogue_turns.append({
            "turn": turn_num * 2,
            "role": "student",
            "content": student_resp
        })

        student_messages.append({"role": "assistant", "content": student_resp})

        # Teacher guides
        teacher_messages.append({
            "role": "user",
            "content": f"The student said:\n\n{student_resp}\n\nThe original question was: {question}\n\nGuide them toward the correct reasoning. Turn {turn_num + 1}/4."
        })

        teacher_resp = call_vllm(teacher_messages, max_tokens=250, temperature=0.4)
        if not teacher_resp:
            break

        dialogue_turns.append({
            "turn": turn_num * 2 + 1,
            "role": "teacher",
            "content": teacher_resp
        })

        teacher_messages.append({"role": "assistant", "content": teacher_resp})

        # Feed teacher's guidance back to student
        student_messages.append({
            "role": "user",
            "content": teacher_resp
        })

    # Check if student converged to correct answer
    final_student = dialogue_turns[-2]["content"] if len(dialogue_turns) >= 2 else ""
    student_correct = recommendation.lower() in final_student.lower()

    # Check for answer leakage in teacher messages
    teacher_texts = " ".join(t["content"] for t in dialogue_turns if t["role"] == "teacher")
    leakage = f"the answer is {recommendation}".lower() in teacher_texts.lower()

    # Quality score: convergence + no leakage + sufficient turns
    quality = 0.0
    if student_correct:
        quality += 0.5
    if not leakage:
        quality += 0.3
    if len(dialogue_turns) >= 6:
        quality += 0.2

    return {
        "dialogue": dialogue_turns,
        "turns": len(dialogue_turns),
        "student_correct": student_correct,
        "teacher_leakage": leakage,
        "quality_score": round(quality, 2)
    }


def call_vllm(messages, max_tokens=300, temperature=0.7):
    """Call vLLM with retry."""
    for attempt in range(3):
        try:
            resp = requests.post(
                VLLM_URL,
                json={
                    "model": VLLM_MODEL,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature
                },
                timeout=60
            )
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"]
            else:
                print(f"  [vLLM] HTTP {resp.status_code} on attempt {attempt + 1}")
                time.sleep(2)
        except Exception as e:
            print(f"  [vLLM] Error on attempt {attempt + 1}: {e}")
            time.sleep(5)
    return None


def save_dialogue(conn, vote, result):
    """Save generated dialogue to didactic_dialogues table."""
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO didactic_dialogues (
                source_vote_id, source_audit_hash, dialogue, turns,
                student_final_correct, teacher_answer_leakage,
                quality_score, original_question,
                ground_truth_recommendation, ground_truth_confidence,
                concern_count, specialist_count,
                generator_model, generator_temperature,
                generation_prompt_version, generated_at,
                included_in_training, training_batch
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        """, (
            vote["id"],
            vote.get("audit_hash", ""),
            json.dumps(result["dialogue"]),
            result["turns"],
            result["student_correct"],
            result["teacher_leakage"],
            result["quality_score"],
            vote["question"],
            vote.get("recommendation", ""),
            vote.get("confidence", 0),
            len(json.loads(vote.get("concerns", "[]")) if isinstance(vote.get("concerns"), str) else (vote.get("concerns") or [])),
            vote.get("specialist_count", 7),
            VLLM_MODEL,
            0.7,
            PROMPT_VERSION,
            datetime.now(),
            False,
            None
        ))
    conn.commit()


def main():
    parser = argparse.ArgumentParser(description="RL2F Didactic Dialogue Generator")
    parser.add_argument("--batch-size", type=int, default=50, help="Votes to process per batch")
    parser.add_argument("--max-dialogues", type=int, default=500, help="Max dialogues to generate this run")
    parser.add_argument("--dry-run", action="store_true", help="Preview without generating")
    parser.add_argument("--min-quality", type=float, default=0.5, help="Minimum quality score to save")
    args = parser.parse_args()

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    conn = get_db()
    votes = fetch_unprocessed_votes(conn, limit=args.batch_size)

    print(f"[RL2F] Found {len(votes)} unprocessed council votes")

    if args.dry_run:
        for v in votes[:10]:
            print(f"  Vote #{v['id']}: {v['question'][:80]}... -> {v.get('recommendation', '?')}")
        print(f"  ... ({len(votes)} total)")
        conn.commit()  # explicit commit before close
        conn.close()
        return

    generated = 0
    skipped_low_quality = 0
    errors = 0

    for i, vote in enumerate(votes):
        if generated >= args.max_dialogues:
            print(f"[RL2F] Reached max dialogues limit ({args.max_dialogues})")
            break

        print(f"\n[RL2F] [{i+1}/{len(votes)}] Vote #{vote['id']}: {vote['question'][:60]}...")

        try:
            result = generate_dialogue(vote)

            if result["quality_score"] < args.min_quality:
                print(f"  Quality {result['quality_score']} < {args.min_quality} — skipping")
                skipped_low_quality += 1
                continue

            save_dialogue(conn, vote, result)
            generated += 1

            print(f"  Saved: {result['turns']} turns, quality={result['quality_score']}, "
                  f"correct={result['student_correct']}, leakage={result['teacher_leakage']}")

            # Rate limit: ~2s between dialogues to not slam vLLM
            time.sleep(1)

        except Exception as e:
            print(f"  ERROR: {e}")
            errors += 1
            if errors > 10:
                print("[RL2F] Too many errors, aborting")
                break

    # Summary
    print(f"\n{'='*60}")
    print(f"[RL2F] Generation complete")
    print(f"  Generated: {generated}")
    print(f"  Skipped (low quality): {skipped_low_quality}")
    print(f"  Errors: {errors}")

    # Write summary to file
    summary_path = os.path.join(OUTPUT_DIR, f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(summary_path, "w") as f:
        json.dump({
            "generated": generated,
            "skipped_low_quality": skipped_low_quality,
            "errors": errors,
            "timestamp": datetime.now().isoformat(),
            "prompt_version": PROMPT_VERSION,
            "model": VLLM_MODEL
        }, f, indent=2)
    print(f"  Summary: {summary_path}")

    conn.commit()  # explicit commit before close
    conn.close()


if __name__ == "__main__":
    main()