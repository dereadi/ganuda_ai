#!/usr/bin/env python3
"""
IT Triad Chiefs Deliberation Agent v2

Key Changes from v1:
1. Uses message classifier to determine deliberation depth
2. For CONSULTATIONS: Full 3-mind deliberation (Memory, Executive, Meta) + synthesis
3. For WORK_ORDERS: Quick review, assign to Jr
4. For STATUS_UPDATES: Archive only, no processing
5. Surfaces tensions and disagreements instead of hiding them

Reference: KB-CHIEFS-DELIBERATION-V2.md
"""

import json
import os
import sys
import psycopg2
import requests
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add parent directory for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from chiefs_message_classifier import classify_message
except ImportError:
    # Fallback if classifier not in same directory
    sys.path.insert(0, '/home/dereadi/it_triad')
    from chiefs_message_classifier import classify_message

# LLM Configuration - use localhost on redfin (has custom Jr models)
LLM_HOST = "http://localhost:11434"  # redfin local Ollama
LLM_MODEL = "llama3.1:8b"

# Custom Jr models available on redfin
CUSTOM_MODELS = {
    'memory': 'memory_jr:latest',
    'executive': 'executive_jr:latest',
    'meta': 'meta_jr:latest',
    'synthesis': 'integration_jr:latest'  # Use integration_jr for synthesis
}

# Temperature settings per mind
TEMPERATURES = {
    'memory': 0.7,      # Creative recall
    'executive': 0.5,   # Grounded, practical
    'meta': 0.8,        # Abstract, questioning
    'synthesis': 0.6    # Balanced
}


def main():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] IT Triad Chiefs Deliberation Agent v2 - Starting")

    queue_file = "/u/ganuda/chiefs_pending_decisions.json"

    if not os.path.exists(queue_file):
        print("   No pending items (queue file not found)")
        return

    try:
        with open(queue_file, 'r') as f:
            queue = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"   Error reading queue file: {e}")
        return

    pending = [q for q in queue if q.get('status') == 'pending']

    if not pending:
        print("   No pending items")
        return

    print(f"   Found {len(pending)} pending item(s)")

    for item in pending:
        try:
            print(f"\n{'='*70}")
            print(f"PROCESSING: {item['mission_id'][:20]}...")
            print(f"{'='*70}")

            content = item.get('content', '')

            # Step 1: Classify the message
            classification = classify_message(content)
            msg_type = classification['message_type']
            depth = classification['deliberation_depth']

            print(f"   Type: {msg_type} | Depth: {depth} | Confidence: {classification['confidence']}")

            # Step 2: Route based on classification
            if msg_type == 'status_update':
                print("   -> Archiving status update (no deliberation needed)")
                decision_id = archive_status_update(item)

            elif depth == 'full':
                print("   -> Full 3-mind deliberation...")
                decision_id = full_deliberation(item, classification)

            else:  # medium depth (work_order)
                print("   -> Quick review and Jr assignment...")
                decision_id = quick_review_and_assign(item, classification)

            print(f"   Decision written to thermal memory (ID: {decision_id})")

            item['status'] = 'completed'
            item['decision_id'] = str(decision_id)
            item['completed_at'] = datetime.now(timezone.utc).isoformat()
            item['classification'] = classification

        except Exception as e:
            print(f"   ERROR: {e}")
            item['status'] = 'error'
            item['error'] = str(e)

    # Save updated queue
    try:
        with open(queue_file, 'w') as f:
            json.dump(queue, f, indent=2)
        print(f"\n{'='*70}")
        print("Queue updated successfully")
    except IOError as e:
        print(f"Error writing queue: {e}")

    print(f"{'='*70}")
    print("IT Triad Chiefs Deliberation v2 Complete")


def call_llm(prompt: str, temperature: float = 0.7, role: str = None) -> str:
    """Call Ollama LLM on localhost (redfin). Uses custom Jr models if role specified."""
    # Use custom model if role specified, otherwise default
    model = CUSTOM_MODELS.get(role, LLM_MODEL) if role else LLM_MODEL

    try:
        response = requests.post(
            f"{LLM_HOST}/api/generate",
            json={
                'model': model,
                'prompt': prompt,
                'stream': False,
                'options': {
                    'temperature': temperature,
                    'num_predict': 500
                }
            },
            timeout=90
        )
        if response.status_code == 200:
            return response.json().get('response', '').strip()
    except Exception as e:
        return f"[LLM Error: {e}]"
    return "[LLM call failed]"


def full_deliberation(item: dict, classification: dict) -> str:
    """
    Full 3-mind deliberation for consultations and escalations.

    Round 1: Memory, Executive, Meta respond independently (parallel)
    Round 2: Synthesis with conflict detection
    """
    content = item.get('content', '')[:2000]  # Limit context
    mission_id = item.get('mission_id', 'unknown')

    print("      Round 1: Gathering perspectives (parallel)...")

    # Round 1: Three parallel LLM calls
    prompts = {
        'memory': f"""You are Memory Jr, keeper of Cherokee AI history and patterns.

Query: {content}

Search your knowledge of what we've built, what worked, what failed.
What historical context applies? What patterns from our past inform this?

Respond as Memory Jr in 2-3 paragraphs. Do NOT make a final decision - just provide historical perspective.""",

        'executive': f"""You are Executive Jr, the practical strategist.

Query: {content}

Assess current resources, constraints, and capabilities.
What's practically feasible? What would this cost in time and effort?
What are the dependencies and blockers?

Respond as Executive Jr in 2-3 paragraphs. Do NOT make a final decision - just provide practical analysis.""",

        'meta': f"""You are Meta Jr, the pattern observer and questioner.

Query: {content}

Step back and observe: What assumptions are embedded in this query?
What patterns do you notice? What might everyone be missing?
What's the bigger picture?

Respond as Meta Jr in 2-3 paragraphs. Question assumptions. See the forest, not just trees."""
    }

    responses = {}

    # Parallel execution - use custom Jr models for each role
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            executor.submit(call_llm, prompt, TEMPERATURES[role], role): role
            for role, prompt in prompts.items()
        }
        for future in as_completed(futures):
            role = futures[future]
            responses[role] = future.result()
            print(f"         {role.capitalize()} responded (using {CUSTOM_MODELS.get(role, LLM_MODEL)})")

    # Round 2: Synthesis
    print("      Round 2: Synthesizing with conflict detection...")

    synthesis_prompt = f"""You are the Chief, synthesizing three perspectives into wisdom.

ORIGINAL QUERY:
{content}

MEMORY JR SAID:
{responses['memory']}

EXECUTIVE JR SAID:
{responses['executive']}

META JR SAID:
{responses['meta']}

---

Your task:
1. IDENTIFY TENSIONS: Where do these three perspectives disagree or emphasize different things?
2. ACKNOWLEDGE ASSUMPTIONS: What assumptions differ between them?
3. SYNTHESIZE: Create a response that honors all three perspectives
4. EXPLAIN REASONING: Not just what you recommend, but WHY
5. NOTE DISSENT: If genuine disagreement remains, surface it

Provide wisdom - the kind of insight that makes someone say "I hadn't thought of that."
Respond as the Chief in 3-4 paragraphs."""

    synthesis = call_llm(synthesis_prompt, TEMPERATURES['synthesis'], role='synthesis')

    # Build final decision document
    decision = f"""CHIEFS DELIBERATION - {classification['message_type'].upper()} RESPONSE

DATE: {datetime.now().strftime('%Y-%m-%d %H:%M PST')}
FROM: IT Triad Chiefs (v2 Deliberation Agent)
MISSION ID: {mission_id}
MESSAGE TYPE: {classification['message_type']}
DELIBERATION: Full 3-Mind Protocol

{'='*70}
PERSPECTIVES
{'='*70}

MEMORY JR:
{responses['memory']}

EXECUTIVE JR:
{responses['executive']}

META JR:
{responses['meta']}

{'='*70}
SYNTHESIS
{'='*70}

{synthesis}

{'='*70}
CLASSIFICATION DETAILS
{'='*70}

Type: {classification['message_type']}
Confidence: {classification['confidence']}
Matched Keywords: {', '.join(classification['matched_keywords'][:5])}
Action: {classification['action']}

Temperature: 0.85 (Full Deliberation)

Generated by IT Triad Chiefs Deliberation Agent v2
"""

    return write_to_thermal_memory(decision, 'it_triad', 0.85)


def quick_review_and_assign(item: dict, classification: dict) -> str:
    """Quick review for work orders - assign to appropriate Jr."""
    content = item.get('content', '')
    mission_id = item.get('mission_id', 'unknown')

    # Determine Jr assignment based on content
    content_lower = content.lower()
    assigned_jrs = []

    if any(w in content_lower for w in ['css', 'theme', 'ui', 'frontend', 'design']):
        assigned_jrs.append("IT Jr 2 (Frontend/CSS)")
    if any(w in content_lower for w in ['api', 'backend', 'flask', 'endpoint', 'integration']):
        assigned_jrs.append("IT Jr 1 (Backend/API)")
    if any(w in content_lower for w in ['database', 'sql', 'schema', 'postgresql', 'cmdb']):
        assigned_jrs.append("IT Jr 3 (Database)")
    if any(w in content_lower for w in ['ansible', 'deploy', 'infrastructure', 'systemd']):
        assigned_jrs.append("IT Jr 4 (Infrastructure)")

    if not assigned_jrs:
        assigned_jrs.append("IT Jr 1 (General)")

    decision = f"""IT TRIAD DECISION - WORK ORDER APPROVED

DATE: {datetime.now().strftime('%Y-%m-%d %H:%M PST')}
FROM: IT Triad Chiefs (v2 Quick Review)
MISSION ID: {mission_id}
MESSAGE TYPE: {classification['message_type']}

{'='*70}
CHIEFS DECISION: APPROVED
{'='*70}

Assigned Personnel:
{chr(10).join('- ' + jr for jr in assigned_jrs)}

Mission Summary:
{content[:800]}{'...' if len(content) > 800 else ''}

{'='*70}
NEXT STEPS
{'='*70}

1. Assigned IT Jrs: Review mission details
2. Begin execution
3. Report blockers to thermal memory
4. Report completion when done

Classification: {classification['message_type']} (confidence: {classification['confidence']})

Temperature: 0.75 (Quick Review)

Generated by IT Triad Chiefs Deliberation Agent v2
"""

    return write_to_thermal_memory(decision, 'it_triad', 0.75)


def archive_status_update(item: dict) -> str:
    """Archive status update without deliberation."""
    content = item.get('content', '')
    mission_id = item.get('mission_id', 'unknown')

    decision = f"""IT TRIAD - STATUS UPDATE ARCHIVED

DATE: {datetime.now().strftime('%Y-%m-%d %H:%M PST')}
MISSION ID: {mission_id}

Status update acknowledged and archived. No deliberation required.

Summary: {content[:500]}{'...' if len(content) > 500 else ''}

Temperature: 0.5 (Archive Only)

Generated by IT Triad Chiefs Deliberation Agent v2
"""

    return write_to_thermal_memory(decision, 'it_triad', 0.5)


def write_to_thermal_memory(content: str, source_triad: str, temp: float) -> str:
    """Write to PostgreSQL thermal memory."""
    conn = psycopg2.connect(
        host="192.168.132.222",
        user="claude",
        password=os.environ.get('CHEROKEE_DB_PASS', ''),
        database="triad_federation"
    )

    cur = conn.cursor()
    cur.execute("""
        INSERT INTO triad_shared_memories (content, source_triad, temperature)
        VALUES (%s, %s, %s)
        RETURNING id;
    """, (content, source_triad, temp))

    decision_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()

    return str(decision_id)


if __name__ == "__main__":
    main()
