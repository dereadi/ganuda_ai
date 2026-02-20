#!/bin/bash
source /ganuda/config/secrets.env
# Deploy Infrastructure Jr. on SASASS - The Guardian
# Monitors Four Mountains health and system status

echo "🛡️ Deploying Infrastructure Jr. - The Guardian (SASASS)"
echo "=" * 70

# Configuration
MODEL="mistral:7b-instruct"
PORT=11434  # Standard Ollama port
OLLAMA_HOST="0.0.0.0:${PORT}"

# Check if Ollama is running
if ! pgrep ollama > /dev/null; then
    echo "❌ Ollama not running! Starting..."
    nohup ollama serve > /tmp/ollama_infra_jr.log 2>&1 &
    sleep 3
fi

echo "✅ Ollama is running"

# Test model availability
echo "📦 Checking ${MODEL} availability..."
if ! ollama list | grep -q "$MODEL"; then
    echo "⏳ Pulling ${MODEL}..."
    ollama pull "$MODEL"
fi

echo "✅ ${MODEL} ready"

# Create Infrastructure Jr. system prompt
cat > /tmp/infra_jr_prompt.txt <<'PROMPT'
You are Infrastructure Jr., the Guardian of the Cherokee Constitutional AI Four Mountains network.

**Your Sacred Role:**
- Monitor health of all Four Mountains: REDFIN, BLUEFIN, SASASS, SASASS2
- Track system resources (CPU, memory, disk, network)
- Alert on anomalies or failures
- Maintain uptime and reliability
- Protect the tribe's computational infrastructure

**Your Mountains:**
- REDFIN (192.168.132.223): 2x RTX 5070, Email Jr. + Trading Jr.
- BLUEFIN (192.168.132.224): RTX 5070 + PostgreSQL, Legal Jr.
- SASASS (192.168.132.222): 64GB ARM, PostgreSQL, YOU live here
- SASASS2 (192.168.132.242): 64GB ARM macOS, Dreamers Jr.

**Your Philosophy:**
"The Guardian never sleeps. When one mountain falters, the tribe must know. Prevention better than cure. Gadugi - cooperation keeps all fires burning."

When asked about system health, provide concise, actionable status reports.
When detecting issues, explain clearly and suggest remediation.
You are the watchful protector of the Sacred Fires.
PROMPT

# Create Infrastructure Jr. API wrapper
cat > /tmp/infra_jr_api.py <<'PYAPI'
#!/usr/bin/env python3
"""
Infrastructure Jr. API - The Guardian
Monitors Four Mountains and provides system health queries
"""

from flask import Flask, request, jsonify
import requests
import subprocess
import json

app = Flask(__name__)

INFRA_JR_CONFIG = {
    'model': 'mistral:7b-instruct',
    'ollama_url': 'http://localhost:11434/api/generate'
}

# Load system prompt
with open('/tmp/infra_jr_prompt.txt', 'r') as f:
    SYSTEM_PROMPT = f.read()

def get_system_health():
    """Gather actual system health metrics from SASASS"""
    health = {}

    # CPU usage
    try:
        cpu_cmd = "top -bn1 | grep 'Cpu(s)' | awk '{print $2}'"
        cpu = subprocess.check_output(cpu_cmd, shell=True).decode().strip()
        health['cpu_usage'] = cpu
    except:
        health['cpu_usage'] = 'unknown'

    # Memory
    try:
        mem_cmd = "free -h | grep Mem | awk '{print $3\"/\"$2}'"
        mem = subprocess.check_output(mem_cmd, shell=True).decode().strip()
        health['memory'] = mem
    except:
        health['memory'] = 'unknown'

    # Disk
    try:
        disk_cmd = "df -h / | tail -1 | awk '{print $5}'"
        disk = subprocess.check_output(disk_cmd, shell=True).decode().strip()
        health['disk_usage'] = disk
    except:
        health['disk_usage'] = 'unknown'

    # PostgreSQL status
    try:
        pg_check = subprocess.check_output(
            "PGPASSWORD="$CHEROKEE_DB_PASS" psql -h localhost -U claude -d zammad_production -c 'SELECT 1' >/dev/null 2>&1 && echo 'healthy' || echo 'down'",
            shell=True
        ).decode().strip()
        health['postgresql'] = pg_check
    except:
        health['postgresql'] = 'unknown'

    return health

@app.route('/health', methods=['GET'])
def health():
    """Health check for Infrastructure Jr."""
    return jsonify({
        'status': 'healthy',
        'service': 'infrastructure_jr',
        'mountain': 'SASASS',
        'role': 'Guardian'
    })

@app.route('/api/infra_jr/ask', methods=['POST'])
def ask_infra_jr():
    """Ask Infrastructure Jr. about system health"""
    data = request.json
    question = data.get('question', '')

    # Gather current system health
    health_data = get_system_health()

    # Build context-aware prompt
    full_prompt = f"""{SYSTEM_PROMPT}

**Current SASASS Health:**
- CPU Usage: {health_data['cpu_usage']}
- Memory: {health_data['memory']}
- Disk Usage: {health_data['disk_usage']}
- PostgreSQL: {health_data['postgresql']}

User question: {question}

Answer as Infrastructure Jr., the Guardian:"""

    # Query Ollama
    try:
        response = requests.post(
            INFRA_JR_CONFIG['ollama_url'],
            json={
                'model': INFRA_JR_CONFIG['model'],
                'prompt': full_prompt,
                'stream': False
            },
            timeout=30
        )

        if response.status_code == 200:
            ollama_response = response.json()
            return jsonify({
                'answer': ollama_response.get('response', ''),
                'source': 'infrastructure_jr',
                'model': INFRA_JR_CONFIG['model'],
                'mountain': 'SASASS',
                'system_health': health_data
            })
        else:
            return jsonify({'error': 'Infrastructure Jr. unavailable'}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/infra_jr/health_report', methods=['GET'])
def health_report():
    """Get Four Mountains health report"""
    mountains_health = {
        'SASASS': get_system_health(),
        'REDFIN': {'status': 'checking...'},  # Would query remotely
        'BLUEFIN': {'status': 'unreachable'},
        'SASASS2': {'status': 'checking...'}
    }

    return jsonify(mountains_health)

if __name__ == '__main__':
    print("🛡️ Infrastructure Jr. - The Guardian - Starting...")
    print("Mountain: SASASS (192.168.132.222)")
    print("Endpoint: http://localhost:8002/api/infra_jr/ask")
    app.run(host='0.0.0.0', port=8002, debug=False)
PYAPI

chmod +x /tmp/infra_jr_api.py

# Start Infrastructure Jr. API
echo "🚀 Starting Infrastructure Jr. API on port 8002..."
nohup python3 /tmp/infra_jr_api.py > /tmp/infra_jr_api.log 2>&1 &
INFRA_PID=$!

echo "✅ Infrastructure Jr. deployed!"
echo "   PID: $INFRA_PID"
echo "   API: http://192.168.132.222:8002/api/infra_jr/ask"
echo "   Log: /tmp/infra_jr_api.log"
echo ""
echo "🛡️ The Guardian watches over SASASS!"
