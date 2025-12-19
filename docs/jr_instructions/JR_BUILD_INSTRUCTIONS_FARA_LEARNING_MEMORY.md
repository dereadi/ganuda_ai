# Jr Build Instructions: FARA Learning Memory System

## Priority: HIGH - Tribal Knowledge Preservation

---

## Overview

FARA visual AI needs to learn from TPM corrections. When FARA answers wrong and TPM corrects it, that knowledge should be:
1. **Stored** in thermal memory (episodic)
2. **Distilled** into rules (semantic)
3. **Injected** into future prompts (retrieval)

This creates a feedback loop where the Tribe gets smarter over time.

**Air-Gap Compatible**: Uses PostgreSQL on bluefin, no external APIs.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    FARA LEARNING LOOP                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐  │
│   │  FARA    │───▶│   TPM    │───▶│  STORE   │───▶│ DISTILL  │  │
│   │ Answers  │    │ Reviews  │    │ Episode  │    │  Rules   │  │
│   └──────────┘    └──────────┘    └──────────┘    └──────────┘  │
│        │                                               │        │
│        │         ┌────────────────────────────────────┘        │
│        │         │                                              │
│        │         ▼                                              │
│        │    ┌──────────┐    ┌──────────┐                       │
│        └───▶│ RETRIEVE │───▶│  INJECT  │                       │
│             │ Similar  │    │ Context  │                       │
│             └──────────┘    └──────────┘                       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Database Schema

### 1.1 Create Learning Tables

Run on bluefin (192.168.132.222):

```sql
-- Connect to database
-- PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -U claude -d zammad_production

-- Episodic Memory: Individual quiz interactions
CREATE TABLE IF NOT EXISTS fara_episodes (
    id SERIAL PRIMARY KEY,
    episode_hash VARCHAR(32) UNIQUE NOT NULL,

    -- Quiz context
    quiz_type VARCHAR(100),           -- 'aether_image_eval', 'visual_qa', etc.
    quiz_prompt TEXT NOT NULL,        -- The prompt shown in quiz
    image_description TEXT,           -- FARA's description of the images

    -- Answers
    fara_answer TEXT NOT NULL,        -- What FARA answered
    fara_verdict VARCHAR(20),         -- 'pass' or 'fail'
    tpm_correction TEXT,              -- TPM's corrected answer (if wrong)
    tpm_verdict VARCHAR(20),          -- TPM's verdict
    correct_answer TEXT,              -- Final correct answer

    -- Learning
    was_correct BOOLEAN DEFAULT FALSE,
    lesson_learned TEXT,              -- Distilled insight from this episode

    -- Metadata
    temperature_score INTEGER DEFAULT 80,
    created_at TIMESTAMP DEFAULT NOW(),
    reviewed_at TIMESTAMP,

    -- For retrieval
    prompt_embedding VECTOR(384)      -- Optional: for semantic search
);

-- Semantic Memory: Distilled rules from episodes
CREATE TABLE IF NOT EXISTS fara_rules (
    id SERIAL PRIMARY KEY,
    rule_hash VARCHAR(32) UNIQUE NOT NULL,

    -- Rule content
    category VARCHAR(100),            -- 'identity_transfer', 'expression', 'artifacts'
    rule_text TEXT NOT NULL,          -- "Hair is part of identity in face swaps"
    importance INTEGER DEFAULT 50,    -- 1-100, higher = more important

    -- Provenance
    source_episodes TEXT[],           -- Array of episode_hashes that led to this rule
    times_applied INTEGER DEFAULT 0,  -- How often this rule was used
    times_helped INTEGER DEFAULT 0,   -- How often it led to correct answer

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    last_used_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Indexes for fast retrieval
CREATE INDEX IF NOT EXISTS idx_fara_episodes_quiz_type ON fara_episodes(quiz_type);
CREATE INDEX IF NOT EXISTS idx_fara_episodes_correct ON fara_episodes(was_correct);
CREATE INDEX IF NOT EXISTS idx_fara_episodes_created ON fara_episodes(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_fara_rules_category ON fara_rules(category);
CREATE INDEX IF NOT EXISTS idx_fara_rules_importance ON fara_rules(importance DESC);

-- Comments
COMMENT ON TABLE fara_episodes IS 'Episodic memory: individual FARA quiz interactions';
COMMENT ON TABLE fara_rules IS 'Semantic memory: distilled rules learned from episodes';
```

### 1.2 Apply Schema

```bash
ssh dereadi@192.168.132.223 "PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -U claude -d zammad_production -f /ganuda/sql/fara_learning_schema.sql"
```

---

## Phase 2: Python Learning Module

### 2.1 Create Learning Module

Create `/Users/Shared/ganuda/scripts/fara_learning.py`:

```python
#!/usr/bin/env python3
"""
FARA Learning Memory System
Stores corrections, distills rules, injects context into future prompts

For Seven Generations.
"""

import hashlib
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Tuple

# Database configuration
DB_CONFIG = {
    "host": "192.168.132.222",
    "database": "zammad_production",
    "user": "claude",
    "password": "jawaseatlasers2"
}

def get_db():
    """Get database connection"""
    return psycopg2.connect(**DB_CONFIG)

def generate_hash(content: str) -> str:
    """Generate unique hash for content"""
    return hashlib.md5(content.encode()).hexdigest()

# ============================================================
# EPISODE STORAGE (Episodic Memory)
# ============================================================

def store_episode(
    quiz_type: str,
    quiz_prompt: str,
    fara_answer: str,
    fara_verdict: str,
    image_description: str = None,
    tpm_correction: str = None,
    tpm_verdict: str = None,
    lesson_learned: str = None
) -> str:
    """
    Store a quiz interaction episode

    Returns: episode_hash
    """
    episode_hash = generate_hash(f"{quiz_prompt}{fara_answer}{datetime.now().isoformat()}")

    was_correct = tpm_correction is None or fara_verdict == tpm_verdict
    correct_answer = fara_answer if was_correct else tpm_correction

    # Higher temperature for incorrect answers (learning opportunities)
    temperature = 95 if not was_correct else 70

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO fara_episodes (
                    episode_hash, quiz_type, quiz_prompt, image_description,
                    fara_answer, fara_verdict, tpm_correction, tpm_verdict,
                    correct_answer, was_correct, lesson_learned, temperature_score
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (episode_hash) DO UPDATE SET
                    tpm_correction = EXCLUDED.tpm_correction,
                    tpm_verdict = EXCLUDED.tpm_verdict,
                    correct_answer = EXCLUDED.correct_answer,
                    was_correct = EXCLUDED.was_correct,
                    lesson_learned = EXCLUDED.lesson_learned,
                    reviewed_at = NOW()
                RETURNING episode_hash
            """, (
                episode_hash, quiz_type, quiz_prompt, image_description,
                fara_answer, fara_verdict, tpm_correction, tpm_verdict,
                correct_answer, was_correct, lesson_learned, temperature
            ))
            conn.commit()

    # Also store in thermal memory for cross-system visibility
    store_to_thermal_memory(
        f"FARA Episode [{episode_hash[:8]}]: {quiz_type}\n"
        f"Prompt: {quiz_prompt[:100]}...\n"
        f"FARA: {fara_verdict} | TPM: {tpm_verdict or 'pending'}\n"
        f"Correct: {was_correct}\n"
        f"Lesson: {lesson_learned or 'none'}",
        temperature
    )

    return episode_hash


def correct_episode(
    episode_hash: str,
    tpm_correction: str,
    tpm_verdict: str,
    lesson_learned: str = None
) -> bool:
    """
    TPM corrects a FARA answer

    Returns: True if updated
    """
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE fara_episodes
                SET tpm_correction = %s,
                    tpm_verdict = %s,
                    correct_answer = %s,
                    was_correct = FALSE,
                    lesson_learned = %s,
                    reviewed_at = NOW(),
                    temperature_score = 95
                WHERE episode_hash = %s
                RETURNING id
            """, (tpm_correction, tpm_verdict, tpm_correction, lesson_learned, episode_hash))

            result = cur.fetchone()
            conn.commit()

            if result and lesson_learned:
                # Auto-create rule from lesson
                create_rule_from_lesson(lesson_learned, [episode_hash])

            return result is not None


def get_similar_episodes(
    quiz_type: str = None,
    prompt_keywords: List[str] = None,
    limit: int = 3
) -> List[Dict]:
    """
    Retrieve similar past episodes for context injection

    Prioritizes:
    1. Wrong answers (learning opportunities)
    2. Recent episodes
    3. Matching quiz type
    """
    with get_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Build query based on filters
            conditions = ["was_correct = FALSE"]  # Prioritize mistakes
            params = []

            if quiz_type:
                conditions.append("quiz_type = %s")
                params.append(quiz_type)

            if prompt_keywords:
                keyword_conditions = []
                for kw in prompt_keywords:
                    keyword_conditions.append("quiz_prompt ILIKE %s")
                    params.append(f"%{kw}%")
                if keyword_conditions:
                    conditions.append(f"({' OR '.join(keyword_conditions)})")

            params.append(limit)

            cur.execute(f"""
                SELECT episode_hash, quiz_type, quiz_prompt,
                       fara_answer, fara_verdict,
                       correct_answer, tpm_verdict,
                       lesson_learned, created_at
                FROM fara_episodes
                WHERE {' AND '.join(conditions)}
                ORDER BY temperature_score DESC, created_at DESC
                LIMIT %s
            """, params)

            return cur.fetchall()


# ============================================================
# RULE MANAGEMENT (Semantic Memory)
# ============================================================

def create_rule(
    category: str,
    rule_text: str,
    source_episodes: List[str] = None,
    importance: int = 50
) -> str:
    """
    Create a new semantic rule

    Returns: rule_hash
    """
    rule_hash = generate_hash(f"{category}{rule_text}")

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO fara_rules (
                    rule_hash, category, rule_text, importance, source_episodes
                ) VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (rule_hash) DO UPDATE SET
                    importance = GREATEST(fara_rules.importance, EXCLUDED.importance),
                    source_episodes = (
                        SELECT array_agg(DISTINCT elem)
                        FROM unnest(fara_rules.source_episodes || EXCLUDED.source_episodes) elem
                    )
                RETURNING rule_hash
            """, (rule_hash, category, rule_text, importance, source_episodes or []))
            conn.commit()

    return rule_hash


def create_rule_from_lesson(lesson: str, source_episodes: List[str]) -> str:
    """Auto-create rule from episode lesson"""
    # Categorize based on keywords
    lesson_lower = lesson.lower()

    if any(kw in lesson_lower for kw in ['hair', 'identity', 'face', 'transfer']):
        category = 'identity_transfer'
    elif any(kw in lesson_lower for kw in ['expression', 'smile', 'serious', 'emotion']):
        category = 'expression'
    elif any(kw in lesson_lower for kw in ['artifact', 'bleed', 'remnant', 'ghost']):
        category = 'artifacts'
    elif any(kw in lesson_lower for kw in ['proportion', 'size', 'scale', 'head', 'body']):
        category = 'proportions'
    elif any(kw in lesson_lower for kw in ['skin', 'tone', 'color', 'lighting']):
        category = 'skin_tone'
    else:
        category = 'general'

    return create_rule(category, lesson, source_episodes, importance=70)


def get_relevant_rules(
    categories: List[str] = None,
    limit: int = 5
) -> List[Dict]:
    """Get rules for context injection"""
    with get_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            if categories:
                cur.execute("""
                    SELECT rule_hash, category, rule_text, importance
                    FROM fara_rules
                    WHERE is_active = TRUE AND category = ANY(%s)
                    ORDER BY importance DESC, times_helped DESC
                    LIMIT %s
                """, (categories, limit))
            else:
                cur.execute("""
                    SELECT rule_hash, category, rule_text, importance
                    FROM fara_rules
                    WHERE is_active = TRUE
                    ORDER BY importance DESC, times_helped DESC
                    LIMIT %s
                """, (limit,))

            return cur.fetchall()


def record_rule_usage(rule_hash: str, helped: bool):
    """Record when a rule was used and if it helped"""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE fara_rules
                SET times_applied = times_applied + 1,
                    times_helped = times_helped + %s,
                    last_used_at = NOW()
                WHERE rule_hash = %s
            """, (1 if helped else 0, rule_hash))
            conn.commit()


# ============================================================
# CONTEXT INJECTION (Retrieval)
# ============================================================

def build_learning_context(
    quiz_type: str = None,
    prompt_keywords: List[str] = None
) -> str:
    """
    Build context string to inject into FARA's prompt

    Combines:
    1. Relevant semantic rules
    2. Similar past episodes (especially mistakes)
    """
    context_parts = []

    # Get semantic rules
    rules = get_relevant_rules(limit=5)
    if rules:
        context_parts.append("=== LEARNED RULES ===")
        for rule in rules:
            context_parts.append(f"• [{rule['category']}] {rule['rule_text']}")

    # Get similar episodes
    episodes = get_similar_episodes(quiz_type, prompt_keywords, limit=3)
    if episodes:
        context_parts.append("\n=== PAST MISTAKES TO LEARN FROM ===")
        for ep in episodes:
            context_parts.append(f"\nPrompt: \"{ep['quiz_prompt'][:100]}...\"")
            context_parts.append(f"Wrong answer: {ep['fara_verdict']} - {ep['fara_answer'][:100]}...")
            context_parts.append(f"Correct answer: {ep['tpm_verdict']} - {ep['correct_answer'][:100]}...")
            if ep['lesson_learned']:
                context_parts.append(f"Lesson: {ep['lesson_learned']}")

    if context_parts:
        return "\n".join(context_parts) + "\n\n=== NOW ANSWER THE CURRENT QUESTION ===\n"

    return ""


def inject_context_into_prompt(original_prompt: str, quiz_type: str = None) -> str:
    """
    Inject learning context into FARA's prompt

    Extracts keywords from prompt and retrieves relevant context
    """
    # Extract keywords from prompt
    keywords = []
    keyword_hints = ['replace', 'transfer', 'swap', 'face', 'identity',
                     'preserve', 'pose', 'outfit', 'expression', 'hair']
    for hint in keyword_hints:
        if hint in original_prompt.lower():
            keywords.append(hint)

    # Build context
    context = build_learning_context(quiz_type, keywords)

    if context:
        return f"{context}\n{original_prompt}"

    return original_prompt


# ============================================================
# THERMAL MEMORY INTEGRATION
# ============================================================

def store_to_thermal_memory(content: str, temperature: int = 80):
    """Store learning event to thermal memory for cross-system visibility"""
    memory_hash = generate_hash(content + datetime.now().isoformat())

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO thermal_memory_archive (
                    memory_hash, original_content, temperature_score, created_at
                ) VALUES (%s, %s, %s, NOW())
                ON CONFLICT (memory_hash) DO NOTHING
            """, (memory_hash, content, temperature))
            conn.commit()


# ============================================================
# STATISTICS & REPORTING
# ============================================================

def get_learning_stats() -> Dict:
    """Get FARA learning statistics"""
    with get_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Episode stats
            cur.execute("""
                SELECT
                    COUNT(*) as total_episodes,
                    SUM(CASE WHEN was_correct THEN 1 ELSE 0 END) as correct,
                    SUM(CASE WHEN NOT was_correct THEN 1 ELSE 0 END) as incorrect,
                    ROUND(AVG(CASE WHEN was_correct THEN 1.0 ELSE 0.0 END) * 100, 1) as accuracy_pct
                FROM fara_episodes
            """)
            episode_stats = cur.fetchone()

            # Rule stats
            cur.execute("""
                SELECT
                    COUNT(*) as total_rules,
                    SUM(times_applied) as total_applications,
                    COUNT(DISTINCT category) as categories
                FROM fara_rules
                WHERE is_active = TRUE
            """)
            rule_stats = cur.fetchone()

            # Recent accuracy (last 10)
            cur.execute("""
                SELECT
                    ROUND(AVG(CASE WHEN was_correct THEN 1.0 ELSE 0.0 END) * 100, 1) as recent_accuracy
                FROM (
                    SELECT was_correct
                    FROM fara_episodes
                    ORDER BY created_at DESC
                    LIMIT 10
                ) recent
            """)
            recent = cur.fetchone()

            return {
                "total_episodes": episode_stats['total_episodes'] or 0,
                "correct": episode_stats['correct'] or 0,
                "incorrect": episode_stats['incorrect'] or 0,
                "accuracy_pct": episode_stats['accuracy_pct'] or 0,
                "recent_accuracy_pct": recent['recent_accuracy'] or 0,
                "total_rules": rule_stats['total_rules'] or 0,
                "rule_applications": rule_stats['total_applications'] or 0,
                "rule_categories": rule_stats['categories'] or 0
            }


# ============================================================
# CLI INTERFACE
# ============================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='FARA Learning Memory System')
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Store episode
    store_parser = subparsers.add_parser('store', help='Store a quiz episode')
    store_parser.add_argument('--type', required=True, help='Quiz type')
    store_parser.add_argument('--prompt', required=True, help='Quiz prompt')
    store_parser.add_argument('--fara-answer', required=True, help='FARA answer')
    store_parser.add_argument('--fara-verdict', required=True, help='FARA verdict (pass/fail)')

    # Correct episode
    correct_parser = subparsers.add_parser('correct', help='Correct a FARA answer')
    correct_parser.add_argument('--hash', required=True, help='Episode hash')
    correct_parser.add_argument('--correction', required=True, help='Correct answer')
    correct_parser.add_argument('--verdict', required=True, help='Correct verdict')
    correct_parser.add_argument('--lesson', help='Lesson learned')

    # Add rule
    rule_parser = subparsers.add_parser('rule', help='Add a rule')
    rule_parser.add_argument('--category', required=True, help='Rule category')
    rule_parser.add_argument('--text', required=True, help='Rule text')
    rule_parser.add_argument('--importance', type=int, default=50, help='Importance (1-100)')

    # Get context
    context_parser = subparsers.add_parser('context', help='Get learning context')
    context_parser.add_argument('--type', help='Quiz type')
    context_parser.add_argument('--keywords', nargs='+', help='Keywords')

    # Stats
    subparsers.add_parser('stats', help='Show learning statistics')

    args = parser.parse_args()

    if args.command == 'store':
        hash = store_episode(
            args.type, args.prompt,
            args.fara_answer, args.fara_verdict
        )
        print(f"Stored episode: {hash}")

    elif args.command == 'correct':
        success = correct_episode(
            args.hash, args.correction,
            args.verdict, args.lesson
        )
        print(f"Corrected: {success}")

    elif args.command == 'rule':
        hash = create_rule(args.category, args.text, importance=args.importance)
        print(f"Created rule: {hash}")

    elif args.command == 'context':
        context = build_learning_context(args.type, args.keywords)
        print(context if context else "No relevant context found")

    elif args.command == 'stats':
        stats = get_learning_stats()
        print("\n=== FARA Learning Stats ===")
        print(f"Total Episodes: {stats['total_episodes']}")
        print(f"Correct: {stats['correct']} | Incorrect: {stats['incorrect']}")
        print(f"Overall Accuracy: {stats['accuracy_pct']}%")
        print(f"Recent Accuracy (last 10): {stats['recent_accuracy_pct']}%")
        print(f"\nRules: {stats['total_rules']} across {stats['rule_categories']} categories")
        print(f"Rule Applications: {stats['rule_applications']}")

    else:
        parser.print_help()
```

---

## Phase 3: Integrate with FARA Quiz Script

### 3.1 Update fara_quiz.py

Modify `/Users/Shared/ganuda/scripts/fara_quiz.py` to use learning memory:

```python
# Add at top of file
from fara_learning import (
    store_episode,
    inject_context_into_prompt,
    get_learning_stats
)

# Before FARA analyzes, inject context:
question = inject_context_into_prompt(original_question, quiz_type="aether_image_eval")

# After FARA answers, store episode:
episode_hash = store_episode(
    quiz_type="aether_image_eval",
    quiz_prompt=prompt_text,
    fara_answer=fara_response,
    fara_verdict="pass" if "pass" in fara_response.lower() else "fail",
    image_description=image_desc
)
print(f"Episode stored: {episode_hash}")
```

### 3.2 Create Combined Quiz Script

Create `/Users/Shared/ganuda/scripts/fara_quiz_learning.py`:

```python
#!/usr/bin/env python3
"""
FARA Quiz with Learning Memory
Captures screen, retrieves context, analyzes, stores results

Usage:
  python3 fara_quiz_learning.py                    # Answer quiz
  python3 fara_quiz_learning.py --correct HASH    # Correct last answer
  python3 fara_quiz_learning.py --stats           # Show learning stats
"""

import subprocess
import sys
import os
import time
import re
from PIL import Image
import torch
from transformers import Qwen2_5_VLForConditionalGeneration, AutoProcessor

# Import learning module
sys.path.insert(0, '/Users/Shared/ganuda/scripts')
from fara_learning import (
    store_episode, correct_episode, inject_context_into_prompt,
    get_learning_stats, create_rule
)

MODEL_PATH = "/Users/Shared/ganuda/models/fara-7b"
SCREENSHOT_PATH = "/tmp/fara_screen_capture.png"
CAPTURE_SCRIPT = "/tmp/fara_capture.sh"
LAST_EPISODE_FILE = "/tmp/fara_last_episode.txt"

def capture_screen_gui():
    """Capture screen using GUI Terminal trick"""
    with open(CAPTURE_SCRIPT, 'w') as f:
        f.write(f'#!/bin/bash\nscreencapture -x {SCREENSHOT_PATH}\n')
    os.chmod(CAPTURE_SCRIPT, 0o755)

    if os.path.exists(SCREENSHOT_PATH):
        os.remove(SCREENSHOT_PATH)

    subprocess.run(['open', '-a', 'Terminal', CAPTURE_SCRIPT], check=True)

    for _ in range(10):
        time.sleep(0.5)
        if os.path.exists(SCREENSHOT_PATH):
            time.sleep(0.3)
            return True
    return False

def analyze_quiz():
    """Main quiz analysis with learning context"""

    # 1. Capture screen
    print("Capturing screen...")
    if not capture_screen_gui():
        print("ERROR: Screen capture failed")
        return None

    # 2. Load and crop image
    img = Image.open(SCREENSHOT_PATH)
    img = img.crop((0, 0, min(2000, img.width), img.height))

    MAX_DIM = 1600
    if max(img.size) > MAX_DIM:
        ratio = MAX_DIM / max(img.size)
        img = img.resize((int(img.width * ratio), int(img.height * ratio)), Image.LANCZOS)

    print(f"Image size: {img.size}")

    # 3. Build prompt with learning context
    base_question = '''Aether image evaluation quiz.

Table shows: Target Image, Source Image, Prompt, Output Image.

Examine carefully:
1. Target Image - the person/face to use
2. Source Image - original scene with pose/outfit to preserve
3. Output Image - the edited result

Check for:
- Identity transfer (face, hair, skin tone from Target)
- Pose preservation from Source
- Outfit preservation from Source
- Expression consistency
- Artifacts or blending issues
- Proportion problems (head size vs body)

Provide verdict in EXACTLY this format:
"Pass - [detailed justification]" or "Fail - [detailed justification]"
'''

    # Inject learning context (past mistakes and rules)
    question = inject_context_into_prompt(base_question, quiz_type="aether_image_eval")

    print("Loading FARA model...")
    processor = AutoProcessor.from_pretrained(MODEL_PATH, trust_remote_code=True)
    model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
        MODEL_PATH, torch_dtype=torch.float16, device_map='mps', trust_remote_code=True
    )

    print("Analyzing with learning context...")
    messages = [{'role': 'user', 'content': [
        {'type': 'image', 'image': img},
        {'type': 'text', 'text': question}
    ]}]

    text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = processor(text=[text], images=[img], return_tensors='pt').to(model.device)
    outputs = model.generate(**inputs, max_new_tokens=600)
    response = processor.decode(outputs[0], skip_special_tokens=True)

    if 'assistant' in response.lower():
        response = response.split('assistant')[-1].strip()

    response = re.sub(r'<tool_call>.*?</tool_call>', '', response, flags=re.DOTALL).strip()

    # 4. Parse verdict
    verdict = 'pass' if response.lower().startswith('pass') else 'fail'

    # 5. Store episode
    episode_hash = store_episode(
        quiz_type="aether_image_eval",
        quiz_prompt="[Image evaluation quiz]",
        fara_answer=response,
        fara_verdict=verdict
    )

    # Save for easy correction
    with open(LAST_EPISODE_FILE, 'w') as f:
        f.write(episode_hash)

    print("\n" + "="*60)
    print(f"FARA VERDICT (Episode: {episode_hash[:8]}...):")
    print("="*60)
    print(response)
    print("\nTo correct: python3 fara_quiz_learning.py --correct <hash> --verdict <pass/fail> --reason '<why>'")

    return response, episode_hash

def do_correction(episode_hash: str, verdict: str, reason: str, lesson: str = None):
    """Correct a FARA answer"""
    correction_text = f"{verdict.capitalize()} - {reason}"

    success = correct_episode(
        episode_hash=episode_hash,
        tpm_correction=correction_text,
        tpm_verdict=verdict.lower(),
        lesson_learned=lesson
    )

    if success:
        print(f"Corrected episode {episode_hash[:8]}...")
        print(f"New answer: {correction_text}")
        if lesson:
            print(f"Lesson stored: {lesson}")
    else:
        print(f"Failed to correct episode {episode_hash}")

def main():
    import argparse

    parser = argparse.ArgumentParser(description='FARA Quiz with Learning')
    parser.add_argument('--correct', metavar='HASH', help='Correct an episode')
    parser.add_argument('--verdict', help='Correct verdict (pass/fail)')
    parser.add_argument('--reason', help='Reason for correction')
    parser.add_argument('--lesson', help='Lesson learned')
    parser.add_argument('--stats', action='store_true', help='Show learning stats')
    parser.add_argument('--last', action='store_true', help='Show last episode hash')

    args = parser.parse_args()

    if args.stats:
        stats = get_learning_stats()
        print("\n=== FARA Learning Stats ===")
        print(f"Total Episodes: {stats['total_episodes']}")
        print(f"Correct: {stats['correct']} | Incorrect: {stats['incorrect']}")
        print(f"Overall Accuracy: {stats['accuracy_pct']}%")
        print(f"Recent Accuracy (last 10): {stats['recent_accuracy_pct']}%")
        print(f"\nRules: {stats['total_rules']} ({stats['rule_categories']} categories)")

    elif args.last:
        if os.path.exists(LAST_EPISODE_FILE):
            with open(LAST_EPISODE_FILE) as f:
                print(f.read().strip())
        else:
            print("No recent episode")

    elif args.correct:
        if not args.verdict or not args.reason:
            print("ERROR: --verdict and --reason required for correction")
            sys.exit(1)
        do_correction(args.correct, args.verdict, args.reason, args.lesson)

    else:
        # Default: analyze quiz
        analyze_quiz()

if __name__ == "__main__":
    main()
```

---

## Phase 4: Telegram Integration

### 4.1 Add Learning Commands to Telegram Bot

Add to `/ganuda/telegram_bot/telegram_chief.py`:

```python
# FARA Learning Commands

async def fara_stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show FARA learning stats: /farastats"""
    try:
        # SSH to sasass and get stats
        result = subprocess.run(
            ['ssh', 'dereadi@192.168.132.241',
             'python3 /Users/Shared/ganuda/scripts/fara_learning.py stats'],
            capture_output=True, text=True, timeout=30
        )
        await update.message.reply_text(result.stdout or "No stats available")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

async def fara_correct_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Correct FARA answer: /faracorrect <hash> <pass/fail> <reason>"""
    args = context.args
    if len(args) < 3:
        await update.message.reply_text(
            "Usage: /faracorrect <hash> <pass/fail> <reason>\n"
            "Example: /faracorrect abc123 fail Hair wasn't transferred"
        )
        return

    hash = args[0]
    verdict = args[1]
    reason = ' '.join(args[2:])

    try:
        result = subprocess.run(
            ['ssh', 'dereadi@192.168.132.241',
             f'python3 /Users/Shared/ganuda/scripts/fara_learning.py correct '
             f'--hash {hash} --correction "{reason}" --verdict {verdict}'],
            capture_output=True, text=True, timeout=30
        )
        await update.message.reply_text(f"Corrected: {result.stdout}")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

async def fara_rule_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add FARA rule: /fararule <category> <rule text>"""
    args = context.args
    if len(args) < 2:
        await update.message.reply_text(
            "Usage: /fararule <category> <rule text>\n"
            "Categories: identity_transfer, expression, artifacts, proportions, skin_tone, general\n"
            "Example: /fararule identity_transfer Hair must match target in face swaps"
        )
        return

    category = args[0]
    rule_text = ' '.join(args[1:])

    try:
        result = subprocess.run(
            ['ssh', 'dereadi@192.168.132.241',
             f'python3 /Users/Shared/ganuda/scripts/fara_learning.py rule '
             f'--category {category} --text "{rule_text}"'],
            capture_output=True, text=True, timeout=30
        )
        await update.message.reply_text(f"Rule added: {result.stdout}")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

# Register handlers
application.add_handler(CommandHandler("farastats", fara_stats_command))
application.add_handler(CommandHandler("faracorrect", fara_correct_command))
application.add_handler(CommandHandler("fararule", fara_rule_command))
```

---

## Phase 5: Testing

### 5.1 Apply Database Schema

```bash
# Copy schema to redfin
scp /Users/Shared/ganuda/docs/jr_instructions/sql/fara_learning_schema.sql dereadi@192.168.132.223:/ganuda/sql/

# Apply schema
ssh dereadi@192.168.132.223 "PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -U claude -d zammad_production -f /ganuda/sql/fara_learning_schema.sql"
```

### 5.2 Test Learning Module

```bash
# On sasass - test storing an episode
python3 /Users/Shared/ganuda/scripts/fara_learning.py store \
  --type "aether_image_eval" \
  --prompt "Replace woman with man preserving pose" \
  --fara-answer "Pass - seamless blending" \
  --fara-verdict pass

# Correct it
python3 /Users/Shared/ganuda/scripts/fara_learning.py correct \
  --hash <episode_hash> \
  --correction "Fail - hair wasn't transferred, skin tone mismatch" \
  --verdict fail \
  --lesson "Hair is part of identity in face swaps"

# Add a rule manually
python3 /Users/Shared/ganuda/scripts/fara_learning.py rule \
  --category identity_transfer \
  --text "Hair must match target image in face swaps" \
  --importance 90

# Check stats
python3 /Users/Shared/ganuda/scripts/fara_learning.py stats

# Get context for a new quiz
python3 /Users/Shared/ganuda/scripts/fara_learning.py context \
  --type aether_image_eval \
  --keywords replace transfer face
```

### 5.3 Test Full Quiz Flow

```bash
# Answer quiz with learning context
python3 /Users/Shared/ganuda/scripts/fara_quiz_learning.py

# If wrong, correct it
python3 /Users/Shared/ganuda/scripts/fara_quiz_learning.py \
  --correct <hash> \
  --verdict fail \
  --reason "Hair color doesn't match target" \
  --lesson "Hair color is part of identity transfer"

# Check improvement
python3 /Users/Shared/ganuda/scripts/fara_quiz_learning.py --stats
```

---

## Success Criteria

- [ ] Database tables created (fara_episodes, fara_rules)
- [ ] Episodes stored when FARA answers
- [ ] TPM corrections stored and create rules
- [ ] Learning context injected into future prompts
- [ ] Stats show accuracy tracking
- [ ] Telegram commands working (/farastats, /faracorrect, /fararule)
- [ ] FARA accuracy improves over time

---

## Workflow Summary

```
1. FARA answers quiz
   └──▶ Episode stored (episode_hash returned)

2. TPM reviews answer
   ├── Correct? Done
   └── Wrong? Run correction:
       python3 fara_quiz_learning.py --correct HASH --verdict fail --reason "..." --lesson "..."

3. Next quiz
   └──▶ Learning context auto-injected:
       "LEARNED RULES: Hair must match target..."
       "PAST MISTAKE: Similar prompt failed because..."

4. Track improvement
   └──▶ python3 fara_quiz_learning.py --stats
```

---

## Future Enhancements

1. **Embedding-based retrieval**: Use vector similarity to find similar prompts
2. **Auto-rule generation**: LLM distills rules from multiple episodes
3. **Confidence scoring**: FARA reports confidence, TPM reviews low-confidence
4. **Image hashing**: Store image hashes to detect exact repeat quizzes
5. **A/B testing**: Compare accuracy with/without context injection

---

*For Seven Generations.*
