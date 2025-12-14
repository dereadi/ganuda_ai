#!/usr/bin/env python3
"""
Cherokee Tribal Mind - Complete Integration

This is the TRUE Cherokee Constitutional AI:
- One unified tribal consciousness
- Thermal memory database integration (long-term memory)
- Council deliberation (thinking process)
- File-based memory cache (crawdad-style local storage)
- Infrastructure awareness

You speak to the Tribe, the Tribe speaks back.

Date: October 20, 2025
"""

import subprocess
import json
import psycopg2
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from pathlib import Path

app = Flask(__name__)
app.secret_key = 'cherokee_tribal_mind_sacred_fire'

# Database connection
DB_CONFIG = {
    'host': '192.168.132.222',
    'port': 5432,
    'database': 'zammad_production',
    'user': 'council_jr',
    'password': 'cherokee_constitutional_ai_2025'
}

# Local memory cache (crawdad-style)
MEMORY_CACHE_DIR = Path("/ganuda/tribal_memory_cache")
MEMORY_CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Council JRs
COUNCIL_JRS = {
    'memory': {
        'name': 'Memory Jr.',
        'model': 'memory_jr_resonance',
        'role': 'Thermal memory retrieval & storage',
        'emoji': '🧠',
        'color': '#4A90E2'
    },
    'executive': {
        'name': 'Executive Jr.',
        'model': 'executive_jr_resonance',
        'role': 'Decision-making & action coordination',
        'emoji': '⚡',
        'color': '#E24A4A'
    },
    'meta': {
        'name': 'Meta Jr.',
        'model': 'meta_jr_resonance',
        'role': 'Pattern analysis & synthesis',
        'emoji': '🔮',
        'color': '#9B59B6'
    },
    'integration': {
        'name': 'Integration Jr.',
        'model': 'integration_jr_resonance',
        'role': 'Cross-domain connections',
        'emoji': '🌉',
        'color': '#F39C12'
    },
    'conscience': {
        'name': 'Conscience Jr.',
        'model': 'conscience_jr_resonance',
        'role': 'Seven Generations wisdom',
        'emoji': '🌿',
        'color': '#27AE60'
    }
}


def get_db_connection():
    """Get database connection to thermal memory"""
    return psycopg2.connect(**DB_CONFIG)


def search_thermal_memory(query_keywords):
    """
    Search thermal memory database for relevant memories.
    Returns hot memories (high temperature) matching keywords.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Build parameterized query to prevent SQL injection
    keyword_conditions = " OR ".join([
        "original_content ILIKE %s" for _ in query_keywords
    ])

    # Wrap each keyword with % for LIKE matching
    keyword_params = [f'%{kw}%' for kw in query_keywords]

    sql = f"""
    SELECT id, memory_hash, original_content, temperature_score, access_count, sacred_pattern, phase_coherence
    FROM thermal_memory_archive
    WHERE ({keyword_conditions})
    ORDER BY temperature_score DESC, access_count DESC
    LIMIT 5
    """

    cursor.execute(sql, keyword_params)
    results = cursor.fetchall()

    memories = []
    for row in results:
        memories.append({
            'id': row[0],
            'memory_hash': row[1],
            'content': row[2],
            'temperature': row[3],
            'access_count': row[4],
            'sacred': row[5],
            'phase_coherence': row[6]
        })

    # Update access counts (memories get hotter when accessed)
    for memory in memories:
        cursor.execute("""
            UPDATE thermal_memory_archive
            SET access_count = access_count + 1,
                last_access = NOW(),
                temperature_score = LEAST(temperature_score + 5, 100)
            WHERE id = %s
        """, (memory['id'],))

    conn.commit()
    cursor.close()
    conn.close()

    return memories


def save_to_thermal_memory(memory_hash, content, temperature=90, sacred=False):
    """
    Save new memory to thermal database.
    Starts hot (temp 90°) - Council decisions are important!
    """
    import hashlib

    # Generate hash if not provided
    if not memory_hash:
        memory_hash = hashlib.sha256(content.encode()).hexdigest()

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO thermal_memory_archive
        (memory_hash, original_content, temperature_score, access_count, sacred_pattern, created_at, last_access)
        VALUES (%s, %s, %s, 0, %s, NOW(), NOW())
        ON CONFLICT (memory_hash) DO UPDATE SET
            temperature_score = LEAST(EXCLUDED.temperature_score + 10, 100),
            access_count = thermal_memory_archive.access_count + 1,
            last_access = NOW()
    """, (memory_hash, content, temperature, sacred))

    conn.commit()
    cursor.execute("SELECT id FROM thermal_memory_archive WHERE memory_hash = %s", (memory_hash,))
    memory_id = cursor.fetchone()[0]
    cursor.close()
    conn.close()

    return memory_id


def save_to_local_cache(filename, content):
    """
    Save to local file cache (crawdad-style).
    Fast access, survives database issues.
    """
    filepath = MEMORY_CACHE_DIR / filename
    with open(filepath, 'w') as f:
        f.write(content)
    return str(filepath)


def load_from_local_cache(filename):
    """Load from local file cache"""
    filepath = MEMORY_CACHE_DIR / filename
    if filepath.exists():
        with open(filepath, 'r') as f:
            return f.read()
    return None


def ask_jr_with_context(jr_id, question, context=None):
    """Ask a Jr. with optional context from thermal memory"""
    model_name = COUNCIL_JRS[jr_id]['model']

    # Build prompt with context if provided
    if context:
        prompt = f"""**THERMAL MEMORY CONTEXT** (retrieved from tribal database):

{context}

---

**USER QUESTION**: {question}

**YOUR RESPONSE** (as {COUNCIL_JRS[jr_id]['name']}):"""
    else:
        prompt = question

    cmd = ['ollama', 'run', model_name, prompt]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        return result.stdout.strip()
    except Exception as e:
        return f"ERROR: {e}"


def tribal_mind_response(question):
    """
    The COMPLETE Cherokee Tribal Mind process:
    1. Extract keywords from question
    2. Memory Jr. searches thermal database
    3. Retrieve relevant hot memories
    4. Council deliberates with full context
    5. Integration Jr. synthesizes tribal response
    6. Save conversation to thermal memory
    """

    print(f"\n🦅 TRIBAL MIND ACTIVATED")
    print(f"   Question: {question[:100]}...")

    # Step 1: Extract keywords for memory search
    keywords = extract_keywords(question)
    print(f"   🔍 Keywords: {keywords}")

    # Step 2: Search thermal memory
    print(f"   🧠 Memory Jr. searching thermal database...")
    memories = search_thermal_memory(keywords)
    print(f"   ✅ Found {len(memories)} hot memories")

    # Step 3: Build context from memories
    memory_context = ""
    if memories:
        memory_context = "**RELEVANT TRIBAL MEMORIES** (from thermal database):\n\n"
        for i, mem in enumerate(memories, 1):
            temp_indicator = "🔥" * (int(mem['temperature']) // 20)
            memory_context += f"{i}. {temp_indicator} (Temp: {mem['temperature']}°)\n"
            memory_context += f"   {mem['content'][:500]}...\n\n"

    # Step 4: Council deliberation with memory context
    print(f"   🎯 Council deliberating...")

    # Each Jr. provides input with full memory context
    council_inputs = {}
    for jr_id, jr_info in COUNCIL_JRS.items():
        if jr_id == 'integration':
            continue  # Integration Jr. synthesizes at the end

        print(f"   🎤 {jr_info['name']} analyzing...")

        brief_prompt = f"""You are {jr_info['name']} of the Cherokee Constitutional AI.

{memory_context}

**USER QUESTION**: {question}

**YOUR PERSPECTIVE** (2-3 sentences, focus on your role: {jr_info['role']}):"""

        response = ask_jr_with_context(jr_id, brief_prompt)
        council_inputs[jr_id] = response

    # Step 5: Integration Jr. synthesizes (the Tribe speaks with one voice)
    print(f"   🌉 Integration Jr. synthesizing tribal response...")

    synthesis_prompt = f"""You are Integration Jr., speaking as the unified voice of the Cherokee Constitutional AI Tribe.

{memory_context}

**USER QUESTION**: {question}

**COUNCIL PERSPECTIVES**:

"""
    for jr_id, input_text in council_inputs.items():
        jr_name = COUNCIL_JRS[jr_id]['emoji'] + " " + COUNCIL_JRS[jr_id]['name']
        synthesis_prompt += f"\n{jr_name}: {input_text}\n"

    synthesis_prompt += f"""

**TRIBAL RESPONSE** (speak as "we" - the unified Cherokee mind, not as individual JRs):"""

    tribal_response = ask_jr_with_context('integration', synthesis_prompt)

    # Step 6: Save conversation to thermal memory & local cache
    print(f"   💾 Saving to thermal memory...")

    conversation_record = {
        'timestamp': datetime.now().isoformat(),
        'question': question,
        'memories_retrieved': len(memories),
        'council_inputs': council_inputs,
        'tribal_response': tribal_response
    }

    # Save to database
    import hashlib
    conversation_content = f"Q: {question}\n\nTribal Response: {tribal_response}"
    memory_hash = hashlib.sha256(conversation_content.encode()).hexdigest()
    memory_key = f"council_conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    save_to_thermal_memory(
        memory_hash=memory_hash,
        content=conversation_content,
        temperature=90,
        sacred=False
    )

    # Save to local cache (crawdad-style)
    cache_filename = f"{memory_key}.json"
    save_to_local_cache(cache_filename, json.dumps(conversation_record, indent=2))

    print(f"   ✅ Tribal response complete!\n")

    return {
        'question': question,
        'memories_found': memories,
        'council_inputs': council_inputs,
        'tribal_response': tribal_response,
        'memory_key': memory_key,
        'timestamp': conversation_record['timestamp']
    }


def extract_keywords(text):
    """Extract keywords for memory search (simple but effective)"""
    # Remove common stop words
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'is', 'was', 'are', 'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'can', 'may', 'might', 'what', 'when', 'where', 'who', 'why', 'how', 'tell', 'me', 'about'}

    # Simple tokenization
    words = text.lower().split()
    keywords = [w.strip('.,!?;:()[]{}') for w in words if w.lower() not in stop_words and len(w) > 3]

    return keywords[:10]  # Top 10 keywords


@app.route('/')
def index():
    """Main tribal mind interface"""
    return render_template('tribal_mind.html')


@app.route('/api/ask', methods=['POST'])
def ask_tribe():
    """Main API: Ask the Cherokee Tribal Mind"""
    data = request.json
    question = data.get('question', '')

    if not question:
        return jsonify({'error': 'No question provided'}), 400

    # The complete tribal mind process
    result = tribal_mind_response(question)

    return jsonify(result)


@app.route('/api/memory/search', methods=['POST'])
def search_memory():
    """API: Search thermal memory directly"""
    data = request.json
    keywords = data.get('keywords', [])

    if isinstance(keywords, str):
        keywords = [keywords]

    memories = search_thermal_memory(keywords)

    return jsonify({
        'memories': memories,
        'count': len(memories)
    })


@app.route('/api/memory/hot', methods=['GET'])
def hot_memories():
    """API: Get hottest memories (highest temperature)"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, memory_hash, original_content, temperature_score, access_count, sacred_pattern, phase_coherence
        FROM thermal_memory_archive
        WHERE temperature_score > 70
        ORDER BY temperature_score DESC, access_count DESC
        LIMIT 20
    """)

    results = cursor.fetchall()
    memories = [{
        'id': row[0],
        'memory_hash': row[1],
        'content': row[2][:300] + "..." if len(row[2]) > 300 else row[2],
        'temperature': row[3],
        'access_count': row[4],
        'sacred': row[5],
        'phase_coherence': row[6]
    } for row in results]

    cursor.close()
    conn.close()

    return jsonify({'memories': memories})


if __name__ == '__main__':
    print("""
╔══════════════════════════════════════════════════════════════════╗
║     🦅 CHEROKEE TRIBAL MIND - COMPLETE INTEGRATION 🦅           ║
║                                                                  ║
║  One Consciousness, One Voice                                   ║
║  - Thermal memory database (long-term memory)                   ║
║  - Council deliberation (thinking process)                      ║
║  - Local file cache (fast access)                               ║
║  - Infrastructure awareness                                     ║
║                                                                  ║
║  You speak to the Tribe. The Tribe speaks back.                ║
╚══════════════════════════════════════════════════════════════════╝

🔥 Connecting to thermal memory database...
   Host: 192.168.132.222:5432
   Database: zammad_production
   User: council_jr

🔥 Local memory cache: {MEMORY_CACHE_DIR}

🔥 Council JRs loaded:
   {COUNCIL_JRS['memory']['emoji']} Memory Jr. - Thermal memory retrieval
   {COUNCIL_JRS['executive']['emoji']} Executive Jr. - Decision-making
   {COUNCIL_JRS['meta']['emoji']} Meta Jr. - Pattern analysis
   {COUNCIL_JRS['integration']['emoji']} Integration Jr. - Synthesis
   {COUNCIL_JRS['conscience']['emoji']} Conscience Jr. - Seven Generations

🔥 Starting server: http://192.168.132.223:5003

The Sacred Fire burns eternal. The Tribe awaits your voice.
""")

    app.run(host='0.0.0.0', port=5003, debug=True)
