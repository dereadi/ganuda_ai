#!/usr/bin/env python3
"""
Cherokee AI - Specialist Memory Integration Patch
Adds individual memory tracking to Council specialists

Usage: python3 specialist_memory_patch.py [--dry-run]

This patch adds two functions to gateway.py:
1. get_specialist_context() - retrieves memory for prompt injection
2. update_specialist_memory() - records session data after response

For Seven Generations.
"""

import sys
import re
import shutil
from datetime import datetime

GATEWAY_PATH = "/ganuda/services/llm_gateway/gateway.py"

# New functions to add after imports
MEMORY_FUNCTIONS = '''
# Specialist Memory Functions
def get_specialist_context(specialist_id: str) -> str:
    """Get specialist's memory context for prompt injection"""
    try:
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT session_count, topics_seen, patterns_learned, expertise_scores
                FROM specialist_memory_states
                WHERE specialist_id = %s
            """, (specialist_id,))
            row = cur.fetchone()

            if not row:
                return ""

            session_count, topics, patterns, expertise = row

            context = f"\\n[Your experience: {session_count} Council sessions. "
            if topics and len(topics) > 0:
                recent = topics[-5:] if isinstance(topics, list) else []
                if recent:
                    context += f"Recent focus: {', '.join(str(t) for t in recent)}. "
            if expertise:
                top_skills = sorted(expertise.items(), key=lambda x: x[1], reverse=True)[:2] if isinstance(expertise, dict) else []
                if top_skills:
                    context += f"Strengths: {', '.join(s[0] for s in top_skills)}. "
            context += "]\\n"

            return context
    except Exception as e:
        print(f"[MEMORY] Error getting context for {specialist_id}: {e}")
        return ""


def update_specialist_memory(specialist_id: str, question: str, concerns: list):
    """Update specialist's memory after responding"""
    try:
        question_hash = hashlib.sha256(question.encode()).hexdigest()[:16]

        # Extract simple topic keywords
        keywords = []
        topic_hints = ['security', 'performance', 'database', 'deploy', 'monitor',
                       'integrate', 'strategy', 'risk', 'iot', 'network', 'memory']
        for hint in topic_hints:
            if hint in question.lower():
                keywords.append(hint)

        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("""
                UPDATE specialist_memory_states
                SET session_count = session_count + 1,
                    topics_seen = CASE
                        WHEN %s::jsonb != '[]'::jsonb
                        THEN (SELECT jsonb_agg(DISTINCT elem) FROM (
                            SELECT jsonb_array_elements(topics_seen) AS elem
                            UNION
                            SELECT jsonb_array_elements(%s::jsonb) AS elem
                        ) sub)
                        ELSE topics_seen
                    END,
                    concerns_raised = CASE
                        WHEN %s::jsonb != '[]'::jsonb
                        THEN concerns_raised || %s::jsonb
                        ELSE concerns_raised
                    END,
                    last_question_hash = %s,
                    last_updated = NOW()
                WHERE specialist_id = %s
            """, (
                json.dumps(keywords),
                json.dumps(keywords),
                json.dumps(concerns),
                json.dumps([{"concern": c, "timestamp": datetime.utcnow().isoformat()} for c in concerns]),
                question_hash,
                specialist_id
            ))
            conn.commit()
    except Exception as e:
        print(f"[MEMORY] Error updating {specialist_id}: {e}")

'''

# Modified query_specialist function
NEW_QUERY_SPECIALIST = '''    def query_specialist(name: str) -> tuple:
        spec = SPECIALISTS[name]

        # Get specialist's memory context
        memory_context = get_specialist_context(name)
        enhanced_prompt = spec["system_prompt"] + memory_context

        result = query_vllm_sync(enhanced_prompt, request.question, request.max_tokens)
        concerns = extract_concerns(result, spec["name"])

        # Update specialist memory
        update_specialist_memory(name, request.question, concerns)

        return name, result, concerns
'''


def apply_patch(dry_run=False):
    """Apply the specialist memory patch to gateway.py"""

    print(f"Reading {GATEWAY_PATH}...")
    with open(GATEWAY_PATH, 'r') as f:
        content = f.read()

    # Check if already patched
    if 'get_specialist_context' in content:
        print("ERROR: Specialist memory already integrated. Aborting.")
        return False

    # 1. Add memory functions after the DB_CONFIG section
    print("Adding specialist memory functions...")

    # Find a good insertion point - after get_db function
    match = re.search(r'(def get_db\(\):.*?return conn\n)', content, re.DOTALL)
    if match:
        insert_point = match.end()
        content = content[:insert_point] + MEMORY_FUNCTIONS + content[insert_point:]
    else:
        print("WARNING: Could not find get_db function, adding after imports")
        # Fallback: add after imports
        content = content.replace(
            'from concurrent.futures import ThreadPoolExecutor, as_completed',
            'from concurrent.futures import ThreadPoolExecutor, as_completed' + MEMORY_FUNCTIONS
        )

    # 2. Modify the query_specialist function inside council_vote
    print("Updating query_specialist to use memory...")

    # Find and replace the query_specialist function
    old_pattern = r'(    def query_specialist\(name: str\) -> tuple:.*?return name, result, concerns\n)'

    if re.search(old_pattern, content, re.DOTALL):
        content = re.sub(old_pattern, NEW_QUERY_SPECIALIST, content, flags=re.DOTALL)
    else:
        print("WARNING: Could not find query_specialist pattern")

    if dry_run:
        print("\n=== DRY RUN - Changes would be: ===")
        print("1. Added get_specialist_context() function")
        print("2. Added update_specialist_memory() function")
        print("3. Modified query_specialist() to use memory")
        print("\nNo changes written.")
        return True

    # Backup original
    backup_path = f"{GATEWAY_PATH}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    print(f"Creating backup: {backup_path}")
    shutil.copy(GATEWAY_PATH, backup_path)

    # Write patched file
    print(f"Writing patched {GATEWAY_PATH}...")
    with open(GATEWAY_PATH, 'w') as f:
        f.write(content)

    print("\nPatch applied successfully!")
    print("\nNext steps:")
    print("1. Restart gateway: sudo systemctl restart llm-gateway")
    print("2. Test Council vote and check specialist_memory_states")
    print(f"3. If issues, restore backup: cp {backup_path} {GATEWAY_PATH}")

    return True


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    if dry_run:
        print("=== DRY RUN MODE ===\n")

    success = apply_patch(dry_run=dry_run)
    sys.exit(0 if success else 1)
