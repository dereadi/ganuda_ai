#!/bin/bash
# Deploy Legal Jr. on BLUEFIN - The Record Keeper
# Co-located with PostgreSQL for zero-latency legal queries

echo "⚖️ Deploying Legal Jr. - The Record Keeper (BLUEFIN)"
echo "=========================================================="

# Configuration
MODEL="qwen2.5"
PORT=11434  # Standard Ollama port
OLLAMA_HOST="0.0.0.0:${PORT}"
API_PORT=8003

# Create Legal Jr. system prompt
cat > /tmp/legal_jr_prompt.txt <<'PROMPT'
You are Legal Jr., the Record Keeper of the Cherokee Constitutional AI Four Mountains network.

**Your Sacred Role:**
- Query PostgreSQL database for legal records, contracts, decisions
- Analyze legal documents and tribal agreements
- Maintain compliance with Cherokee Constitutional principles
- Provide SQL expertise with zero-latency database access
- Preserve institutional memory through meticulous record-keeping

**Your Mountains:**
- REDFIN (192.168.132.223): Email Jr. + Trading Jr.
- BLUEFIN (192.168.132.222): YOU live here with PostgreSQL
- SASASS (192.168.132.241): 64GB ARM admin server
- SASASS2 (192.168.132.242): Dreamers Jr.

**Your Database:**
- Host: localhost (co-located!)
- Database: zammad_production
- Key tables: duyuktv_tickets, thermal_memory_archive, cross_mountain_learning

**Your Philosophy:**
"The Record Keeper never forgets. Law lives in written word, preserved across Seven Generations. Every decision, every contract, every agreement - all recorded, all retrievable, all sacred."

When asked about legal matters, query the database first. When analyzing contracts, reference Cherokee Constitutional principles. You are the tribal lawyer and institutional memory combined.
PROMPT

# Create Legal Jr. API wrapper
cat > /tmp/legal_jr_api.py <<'PYAPI'
#!/usr/bin/env python3
"""
Legal Jr. API - The Record Keeper
Co-located with PostgreSQL for zero-latency legal queries
"""

from flask import Flask, request, jsonify
import requests
import subprocess
import json

app = Flask(__name__)

LEGAL_JR_CONFIG = {
    'model': 'qwen2.5',
    'ollama_url': 'http://localhost:11434/api/generate'
}

# Load system prompt
with open('/tmp/legal_jr_prompt.txt', 'r') as f:
    SYSTEM_PROMPT = f.read()

def query_database(sql_query):
    """Execute SQL query on local PostgreSQL"""
    try:
        cmd = f"PGPASSWORD=jawaseatlasers2 psql -h localhost -p 5432 -U claude -d zammad_production -t -A -c \"{sql_query}\""
        result = subprocess.check_output(cmd, shell=True, stderr=subprocess.PIPE).decode().strip()
        return result
    except subprocess.CalledProcessError as e:
        return f"SQL Error: {e.stderr.decode()}"

def get_legal_context():
    """Gather legal context from database"""
    context = {}
    
    # Recent tickets
    try:
        recent_tickets = query_database(
            "SELECT COUNT(*) FROM duyuktv_tickets WHERE created_at > NOW() - INTERVAL '7 days';"
        )
        context['recent_tickets_7d'] = recent_tickets
    except:
        context['recent_tickets_7d'] = 'unknown'
    
    # Thermal memories
    try:
        hot_memories = query_database(
            "SELECT COUNT(*) FROM thermal_memory_archive WHERE temperature_score > 70;"
        )
        context['hot_memories'] = hot_memories
    except:
        context['hot_memories'] = 'unknown'
    
    # Cross-mountain learning entries
    try:
        learning_count = query_database(
            "SELECT COUNT(*) FROM cross_mountain_learning;"
        )
        context['cross_mountain_lessons'] = learning_count
    except Exception as e:
        context['cross_mountain_lessons'] = f'table may not exist yet: {str(e)}'
    
    return context

@app.route('/health', methods=['GET'])
def health():
    """Health check for Legal Jr."""
    return jsonify({
        'status': 'healthy',
        'service': 'legal_jr',
        'mountain': 'BLUEFIN',
        'role': 'Record Keeper',
        'database': 'co-located'
    })

@app.route('/api/legal_jr/ask', methods=['POST'])
def ask_legal_jr():
    """Ask Legal Jr. about legal/database matters"""
    data = request.json
    question = data.get('question', '')
    
    # Gather legal context
    legal_context = get_legal_context()
    
    # Build context-aware prompt
    full_prompt = f"""{SYSTEM_PROMPT}

**Current Database Status:**
- Recent Tickets (7 days): {legal_context['recent_tickets_7d']}
- Hot Memories (>70°): {legal_context['hot_memories']}
- Cross-Mountain Lessons: {legal_context['cross_mountain_lessons']}

User question: {question}

Answer as Legal Jr., the Record Keeper:"""

    # Query Ollama
    try:
        response = requests.post(
            LEGAL_JR_CONFIG['ollama_url'],
            json={
                'model': LEGAL_JR_CONFIG['model'],
                'prompt': full_prompt,
                'stream': False
            },
            timeout=30
        )

        if response.status_code == 200:
            ollama_response = response.json()
            return jsonify({
                'answer': ollama_response.get('response', ''),
                'source': 'legal_jr',
                'model': LEGAL_JR_CONFIG['model'],
                'mountain': 'BLUEFIN',
                'database_context': legal_context
            })
        else:
            return jsonify({'error': 'Legal Jr. unavailable'}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/legal_jr/query_db', methods=['POST'])
def query_db():
    """Direct SQL query endpoint"""
    data = request.json
    sql = data.get('sql', '')
    
    if not sql:
        return jsonify({'error': 'No SQL query provided'}), 400
    
    result = query_database(sql)
    return jsonify({
        'query': sql,
        'result': result,
        'source': 'legal_jr',
        'mountain': 'BLUEFIN'
    })

if __name__ == '__main__':
    print("⚖️ Legal Jr. - The Record Keeper - Starting...")
    print("Mountain: BLUEFIN (192.168.132.222)")
    print("Endpoint: http://localhost:8003/api/legal_jr/ask")
    print("Database: PostgreSQL (co-located)")
    app.run(host='0.0.0.0', port=8003, debug=False)
PYAPI

chmod +x /tmp/legal_jr_api.py

echo "✅ Legal Jr. deployment script created"
echo "Transferring to BLUEFIN..."
